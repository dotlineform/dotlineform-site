#!/usr/bin/env python3
"""
Generate Jekyll work/moment pages and JSON artifacts.

This repo stores works as a Jekyll collection in `_works/`. The generator writes metadata-free
Markdown route anchors (e.g. `_works/00286.md`) while runtime catalogue metadata lives in
generated JSON artifacts.

Series index JSON is written to assets/data/series_index.json.
Work-details JSON index files are written to assets/works/index/<work_id>.json (work-driven; one per selected work).
Lightweight works index JSON is written to assets/data/works_index.json (object keyed by work_id).
Recent publications JSON is written to assets/data/recent_index.json.
Studio-only work storage index JSON is written to assets/studio/data/work_storage_index.json (object keyed by work_id).
Moment JSON index files are written to assets/moments/index/<moment_id>.json (one per selected moment).
Lightweight moments index JSON is written to assets/data/moments_index.json (object keyed by moment_id).

- Works: base work metadata (1 row per work)
- Series: series master data (1 row per series_id)
- WorkDetails: additional detail images associated with a work
- Moments: standalone moment entries sourced from catalogue moment metadata JSON plus repo-local body Markdown

YAML typing rules enforced by this script:
- Numbers are emitted unquoted for: year, height_cm, width_cm, depth_cm
- Everything else is emitted as a quoted string (including fields like year_display)
- Empty values become YAML null

Safe by default:
- dry-run unless you pass --write
- will not overwrite unless --force
- status gating (Works/Series):
  - draft -> process (candidate to publish)
  - published -> skip unless --force
  - unknown -> skip
  - when writing with --write: set status=published; set published_date=today if status changed or --force

specify work_ids to process with --work-ids (comma-separated list)
  - Only those IDs are processed; others are skipped early.
  - Status filtering still applies to the selected IDs unless you also pass --force.
This script is an internal JSON-build engine used by `catalogue_json_build.py`.
It is not a user-facing command.

Common flags:
- --write: persist generated files + canonical source status/date updates
- --force: regenerate even when generated output would otherwise match existing files
- --work-ids / --work-ids-file: limit work/work_details generation scope
- --series-ids / --series-ids-file: limit series page/JSON scope
- --moment-ids / --moment-ids-file: limit moments generation scope
- --moments-output-dir: moment page destination
- --moments-json-dir: moment JSON output destination
- --moments-index-json-path: moments index JSON output destination
- --projects-base-dir: base path used for work/work_details dimension lookups and moment source-image lookup

Path variables used by the script:
- projects_root = [projects-base-dir]/projects (work + work_details source lookup)
- moment prose root = _docs_catalogue/moments
- moments_images_root = [projects-base-dir]/moments/images (moment source image lookup)

"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import json
import sys

try:
    import catalogue_generation_indexes as indexes
    import catalogue_generation_recent as recent
    import catalogue_generation_records as records
    from catalogue_generation_common import (
        coerce_int,
        coerce_numeric,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        is_empty,
        normalize_status,
        normalize_text,
        slug_id,
        parse_date,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts import catalogue_generation_indexes as indexes
    from scripts import catalogue_generation_recent as recent
    from scripts import catalogue_generation_records as records
    from scripts.catalogue_generation_common import (
        coerce_int,
        coerce_numeric,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        is_empty,
        normalize_status,
        normalize_text,
        slug_id,
        parse_date,
    )

try:
    from display_paths import format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.display_paths import format_display_path

try:
    from script_logging import append_script_log
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.script_logging import append_script_log

try:
    from pipeline_config import (
        env_var_name,
        env_var_value,
        load_pipeline_config,
        source_moments_images_subdir,
        source_works_root_subdir,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.pipeline_config import (
        env_var_name,
        env_var_value,
        load_pipeline_config,
        source_moments_images_subdir,
        source_works_root_subdir,
    )


try:
    from catalogue_source import (
        DEFAULT_SOURCE_DIR as DEFAULT_CATALOGUE_SOURCE_DIR,
        build_detail_section_resolution_by_uid,
        records_from_json_source,
        validate_source_records,
        write_source_record_payloads,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_source import (
        DEFAULT_SOURCE_DIR as DEFAULT_CATALOGUE_SOURCE_DIR,
        build_detail_section_resolution_by_uid,
        records_from_json_source,
        validate_source_records,
        write_source_record_payloads,
    )

try:
    from series_ids import normalize_series_id
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.series_ids import normalize_series_id

try:
    from moment_sources import CATALOGUE_MOMENT_PROSE_REL_DIR, build_moment_metadata_source_index
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.moment_sources import CATALOGUE_MOMENT_PROSE_REL_DIR, build_moment_metadata_source_index


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")
CATALOGUE_PROSE_SOURCE_REL_DIR = Path("_docs_catalogue")


# ----------------------------
# Helpers (ID/date/YAML parsing)
# ----------------------------
# These functions normalise source values and keep YAML output safe/consistent.
def is_slug_safe(s: str) -> bool:
    return bool(re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", s))


def require_slug_safe(label: str, raw: Any) -> str:
    """Validate that `raw` is a slug-safe id and return it as a string."""
    if raw is None:
        raise ValueError(f"Missing {label}")
    s = normalize_text(raw)
    if not s:
        raise ValueError(f"Missing {label}")
    if not is_slug_safe(s):
        raise ValueError(f"{label} is not slug-safe: {s!r}")
    return s


def parse_work_id_selection(raw: str) -> set[str]:
    """
    Parse comma-separated work-id selectors supporting individual IDs and ranges.
    Examples:
      "66,74" -> {"00066", "00074"}
      "66-74,38-40,12" -> {"00012", "00038", ..., "00074"}
    """
    selected: set[str] = set()
    for token in (part.strip() for part in str(raw).split(",") if part.strip()):
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", token)
        if m:
            start = int(m.group(1))
            end = int(m.group(2))
            if start > end:
                start, end = end, start
            for n in range(start, end + 1):
                selected.add(slug_id(n))
        else:
            selected.add(slug_id(token))
    return selected


def slug_anchor(value: Any) -> str:
    """
    Create a stable lowercase slug for anchor/query ids.
    Mirrors the client-side slug behavior used in work detail section ids.
    """
    s = normalize_text(value).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def yaml_quote(s: str) -> str:
    """Quote a string safely for YAML."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


NUMERIC_KEYS = {"year", "height_cm", "width_cm", "depth_cm", "width_px", "height_px"}
BOOLEAN_KEYS = set()


def log_event(event: str, details: Optional[Dict[str, Any]] = None) -> None:
    try:
        append_script_log(Path(__file__), event=event, details=details or {})
    except Exception:
        # Logging failures must not block generation.
        pass


def dump_scalar(key: str, value: Any) -> str:
    """Dump a scalar YAML key/value with typing rules."""
    if value is None:
        if key in BOOLEAN_KEYS:
            return f"{key}: false"
        return f"{key}: null"

    if key in BOOLEAN_KEYS:
        return f"{key}: {'true' if bool(value) else 'false'}"

    if key in NUMERIC_KEYS:
        # year is an int; dimensions are floats but we render ints without .0
        if key == "year":
            iv = coerce_int(value)
            return f"{key}: {iv}" if iv is not None else f"{key}: null"
        fv = coerce_numeric(value)
        if fv is None:
            return f"{key}: null"
        if fv.is_integer():
            return f"{key}: {int(fv)}"
        return f"{key}: {fv}"

    # Everything else is a quoted string
    sv = coerce_string(value)
    return f"{key}: {yaml_quote(sv)}" if sv is not None else f"{key}: null"


def dump_list_of_strings(key: str, values: List[str]) -> List[str]:
    lines: List[str] = [f"{key}:"]
    for v in values:
        lines.append(f"  - {yaml_quote(str(v))}")
    return lines


def dump_list_of_dicts(key: str, items: List[Dict[str, Any]], field_order: Optional[List[str]] = None) -> List[str]:
    """Dump a YAML list of dicts with stable key ordering."""
    lines: List[str] = [f"{key}:"]
    for item in items:
        # First line for each item
        lines.append("  -")
        keys = field_order if field_order else list(item.keys())
        for k in keys:
            if k not in item:
                continue
            # All nested fields here are strings by design; emit as quoted string or null
            sv = coerce_string(item.get(k))
            if sv is None:
                lines.append(f"    {k}: null")
            else:
                lines.append(f"    {k}: {yaml_quote(sv)}")
    return lines



def build_front_matter(fields: Dict[str, Any]) -> str:
    """Build YAML front matter in block style (supports lists of dicts)."""
    # Policy: we intentionally emit explicit empty values to keep the front matter schema stable.
    # - Empty/blank scalars become `key: null`
    # - Empty lists become `key: []`
    # This makes diffs, validation, and layout logic simpler and easier to test.
    lines: List[str] = ["---"]

    for k, v in fields.items():
        if isinstance(v, list):
            if not v:
                # Emit empty list explicitly (rare; keeps schema predictable)
                lines.append(f"{k}: []")
                continue

            # Detect list of dicts vs list of strings
            if all(isinstance(x, dict) for x in v):
                lines.extend(dump_list_of_dicts(k, v))
            else:
                # List of scalars -> strings
                lines.extend(dump_list_of_strings(k, [str(x) for x in v if not is_empty(x)]))
            continue

        # Scalars
        lines.append(dump_scalar(k, v))

    lines.append("---")
    return "\n".join(lines) + "\n"


def build_route_stub_content() -> str:
    """Build a metadata-free Jekyll collection route anchor."""
    return build_front_matter({})


def build_download_entry(filename: Any, label: Any) -> Dict[str, str]:
    filename_value = coerce_string(filename)
    label_value = coerce_string(label)
    if filename_value is None:
        raise ValueError("Missing filename")
    if label_value is None:
        raise ValueError("Missing label")
    source_name = Path(filename_value).name
    stem = Path(source_name).stem
    suffix = "".join(Path(source_name).suffixes)
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._")
    safe_stem = re.sub(r"-{2,}", "-", safe_stem)
    if safe_stem == "":
        safe_stem = "file"
    return {
        "source_filename": source_name,
        "filename": f"{safe_stem}{suffix}",
        "label": label_value,
    }


def build_link_entry(url: Any, label: Any) -> Dict[str, str]:
    url_value = coerce_string(url)
    label_value = coerce_string(label)
    if url_value is None:
        raise ValueError("Missing URL")
    if label_value is None:
        raise ValueError("Missing label")
    return {
        "url": url_value,
        "label": label_value,
    }

def load_recent_entries(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    entries_raw = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries_raw, list):
        return []
    entries: List[Dict[str, Any]] = []
    for raw in entries_raw:
        normalized = recent.normalize_recent_entry(raw)
        if normalized is not None:
            entries.append(normalized)
    return entries


def extract_existing_header_scalar(path: Path, key: str) -> Optional[str]:
    """Extract header.<key> from an existing JSON payload."""
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    header = obj.get("header")
    if not isinstance(header, dict):
        return None
    hv = header.get(key)
    if hv is None:
        return None
    s = str(hv).strip()
    return s or None


def render_markdown_with_jekyll(markdown_path: Path) -> str:
    """Render a markdown file to HTML using the repo's local Jekyll stack."""
    renderer_script = Path(__file__).resolve().with_name("render_markdown_with_jekyll.rb")
    if not renderer_script.exists():
        raise SystemExit(f"Markdown renderer helper not found: {renderer_script}")

    bundle_path = shutil.which("bundle")
    if bundle_path is None:
        raise SystemExit("Bundler not found in PATH; ensure the local Jekyll toolchain is available before generating moment JSON.")

    proc = subprocess.run(
        [bundle_path, "exec", "ruby", str(renderer_script), str(markdown_path.resolve())],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise SystemExit(f"Failed to render markdown with Jekyll: {markdown_path}\n{detail}")
    return proc.stdout


def parse_sips_pixel_dims(output: str) -> tuple[Optional[int], Optional[int]]:
    width = None
    height = None
    for line in output.splitlines():
        m_w = re.search(r"pixelWidth:\s*([0-9]+)", line)
        if m_w:
            width = int(m_w.group(1))
        m_h = re.search(r"pixelHeight:\s*([0-9]+)", line)
        if m_h:
            height = int(m_h.group(1))
    return width, height


def read_image_dims_px(path: Path) -> tuple[Optional[int], Optional[int]]:
    """Read pixel dimensions from an image file using macOS `sips` when available."""
    if not path.exists():
        return None, None
    if shutil.which("sips") is None:
        return None, None
    proc = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None, None
    return parse_sips_pixel_dims(proc.stdout)


def utc_timestamp_now() -> str:
    """Return current UTC timestamp formatted as YYYY-MM-DDTHH:MM:SSZ."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_tag_assignments_payload(path: Path) -> Dict[str, Any]:
    """
    Load tag assignments JSON payload.
    If file is missing, return a default payload shape.
    """
    if not path.exists():
        return {
            "tag_assignments_version": "tag_assignments_v1",
            "updated_at_utc": utc_timestamp_now(),
            "series": {},
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to parse tag assignments JSON: {path} ({exc})")

    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid tag assignments payload (expected object): {path}")

    if not isinstance(payload.get("series"), dict):
        payload["series"] = {}
    if not coerce_string(payload.get("tag_assignments_version")):
        payload["tag_assignments_version"] = "tag_assignments_v1"
    if not coerce_string(payload.get("updated_at_utc")):
        payload["updated_at_utc"] = utc_timestamp_now()
    for series_id, row in list(payload["series"].items()):
        if not isinstance(row, dict):
            payload["series"][series_id] = {
                "tags": [],
                "works": {},
                "updated_at_utc": utc_timestamp_now(),
            }
            continue
        if not isinstance(row.get("tags"), list):
            row["tags"] = []
        if "works" not in row or not isinstance(row.get("works"), dict):
            row["works"] = {}
    return payload


def load_tag_registry_payload(path: Path) -> Dict[str, Any]:
    """Load tag registry JSON payload or return a default shape when missing."""
    if not path.exists():
        return {
            "tag_registry_version": "tag_registry_v1",
            "updated_at_utc": utc_timestamp_now(),
            "tags": [],
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to parse tag registry JSON: {path} ({exc})")

    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid tag registry payload (expected object): {path}")

    if not isinstance(payload.get("tags"), list):
        payload["tags"] = []
    if not coerce_string(payload.get("tag_registry_version")):
        payload["tag_registry_version"] = "tag_registry_v1"
    if not coerce_string(payload.get("updated_at_utc")):
        payload["updated_at_utc"] = utc_timestamp_now()
    return payload


# ----------------------------
# Main program
# ----------------------------
# High-level flow:
# 1) Parse CLI args (scope + output options)
# 2) Load canonical source JSON
# 3) Build generated artifacts from canonical source records
# 4) Persist mutable source fields directly against canonical source records
def main() -> None:
    # CLI arguments define the internal JSON-source run and where output files go.
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source-dir",
        default=str(DEFAULT_CATALOGUE_SOURCE_DIR),
        help="Canonical catalogue source JSON directory.",
    )
    ap.add_argument(
        "--internal-json-source-run",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    # Output
    ap.add_argument("--output-dir", default="_works", help="Output folder for generated work pages")
    ap.add_argument("--series-output-dir", default="_series", help="Output folder for generated series pages")
    ap.add_argument("--series-json-dir", default="assets/series/index", help="Output folder for generated per-series JSON files")
    ap.add_argument("--series-index-json-path", default="assets/data/series_index.json", help="Output path for generated series index JSON")
    ap.add_argument("--work-details-output-dir", default="_work_details", help="Output folder for generated work detail pages")
    ap.add_argument("--works-json-dir", default="assets/works/index", help="Output folder for generated per-work detail JSON index files")
    ap.add_argument("--works-index-json-path", default="assets/data/works_index.json", help="Output path for generated lightweight works index JSON")
    ap.add_argument("--recent-index-json-path", default="assets/data/recent_index.json", help="Output path for generated recent publications index JSON")
    ap.add_argument("--work-storage-index-json-path", default="assets/studio/data/work_storage_index.json", help="Output path for generated Studio-only work storage index JSON")
    ap.add_argument("--moments-output-dir", default="_moments", help="Output folder for generated moment pages")
    ap.add_argument("--moments-json-dir", default="assets/moments/index", help="Output folder for generated per-moment JSON index files")
    ap.add_argument("--moments-index-json-path", default="assets/data/moments_index.json", help="Output path for generated lightweight moments index JSON")
    ap.add_argument(
        "--projects-base-dir",
        default=env_var_value(PIPELINE_CONFIG, "projects_base_dir"),
        help="Base folder containing the projects directory used to resolve source media files",
    )

    # Write controls
    ap.add_argument("--write", action="store_true", help="Actually write files (otherwise dry-run)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    ap.add_argument(
        "--refresh-published",
        action="store_true",
        help="Process selected published records without forcing unchanged writes",
    )
    ap.add_argument(
        "--work-ids",
        default="",
        help=(
            "Comma-separated work_ids/ranges to process "
            "(e.g. 00001,00002 or 66-74,38-40). If set, only these IDs are processed."
        ),
    )
    ap.add_argument(
        "--work-ids-file",
        default="",
        help="Path to work_ids file (one id per line). If set, only these IDs are processed.",
    )
    ap.add_argument(
        "--series-ids",
        default="",
        help="Comma-separated series_ids to process for series page/index generation.",
    )
    ap.add_argument(
        "--series-ids-file",
        default="",
        help="Path to series_ids file (one id per line). If set, only these series are processed.",
    )
    ap.add_argument(
        "--moment-ids",
        default="",
        help="Comma-separated moment_ids to process.",
    )
    ap.add_argument(
        "--moment-ids-file",
        default="",
        help="Path to moment_ids file (one id per line). If set, only these moments are processed.",
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help=(
            "Limit run to selected artifacts. Repeat flag and/or pass comma-separated values. "
            "Allowed: work-pages,series-pages,series-index-json,work-details-pages,work-json,works-index-json,recent-index-json,moments,moments-index-json. "
            "Aggregate index JSON artifacts are always rebuilt on every run."
        ),
    )
    args = ap.parse_args()

    if not args.internal_json_source_run:
        print(
            "Deprecated direct entrypoint: scripts/generate_work_pages.py is now an internal JSON build engine.\n"
            "Use `python3 ./scripts/catalogue_json_build.py --work-id <work_id> [--write]` for scoped runtime rebuilds.\n"
            "Direct generation through this script is retired."
        )
        return

    repo_root = Path(__file__).resolve().parents[1]
    catalogue_prose_source_root = repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR
    projects_base_dir_display = Path(args.projects_base_dir).expanduser() if normalize_text(args.projects_base_dir) else None

    def display_path(path: Path | str) -> str:
        return format_display_path(
            path,
            repo_root=repo_root,
            projects_base_dir=projects_base_dir_display,
        )

    def display_projects_path(path: Path | str) -> str:
        return format_display_path(
            path,
            repo_root=repo_root,
            projects_base_dir=projects_base_dir_display,
        )

    json_source_dir = Path(args.source_dir).expanduser()
    source_records = records_from_json_source(json_source_dir)
    print(f"Catalogue source: JSON {display_path(json_source_dir)}")

    log_event(
        "generate_start",
        {
            "argv": sys.argv[1:],
            "write": bool(args.write),
            "force": bool(args.force),
            "refresh_published": bool(args.refresh_published),
            "source": "json",
        },
    )
    refresh_published = bool(args.refresh_published or args.force)

    valid_artifacts = {
        "work-pages",
        "series-pages",
        "series-index-json",
        "work-details-pages",
        "work-json",
        "works-index-json",
        "recent-index-json",
        "moments",
        "moments-index-json",
    }
    selected_artifacts: Optional[set[str]] = None
    if args.only:
        requested: set[str] = set()
        for raw in args.only:
            for part in str(raw).split(","):
                item = part.strip().lower()
                if item:
                    requested.add(item)
        invalid = sorted(item for item in requested if item not in valid_artifacts)
        if invalid:
            raise SystemExit(
                "Invalid --only value(s): "
                + ", ".join(invalid)
                + ". Allowed: "
                + ", ".join(sorted(valid_artifacts))
            )
        selected_artifacts = requested

    def artifact_enabled(name: str) -> bool:
        if selected_artifacts is None:
            return True
        return name in selected_artifacts

    run_work_pages = artifact_enabled("work-pages")
    run_series_pages = artifact_enabled("series-pages")
    run_series_index_json = True
    run_work_details_pages = artifact_enabled("work-details-pages")
    run_work_json = artifact_enabled("work-json") or run_work_pages
    run_works_index_json = True
    run_moments_artifact = artifact_enabled("moments")
    run_moments_index_json = True
    run_studio_series_pages = False  # retired: use /studio/analytics/series-tag-editor/?series=<id>

    needs_projects_base = run_work_details_pages or run_work_json or run_series_pages or run_moments_artifact or run_moments_index_json
    if needs_projects_base and normalize_text(args.projects_base_dir) == "":
        raise SystemExit(
            f"Missing projects base directory. Add {PROJECTS_BASE_DIR_ENV_NAME} "
            "to var/local/site.env or pass --projects-base-dir."
        )
    # Output directory:
    # - Use `works` for a normal pages folder.
    # - Use `_works` if you're using a Jekyll collection.
    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    series_out_dir = Path(args.series_output_dir).expanduser()
    series_out_dir.mkdir(parents=True, exist_ok=True)
    series_json_dir = Path(args.series_json_dir).expanduser()
    series_json_dir.mkdir(parents=True, exist_ok=True)
    studio_series_out_dir: Optional[Path] = None
    if run_studio_series_pages:
        studio_series_out_dir = Path("_studio_series").expanduser()
        studio_series_out_dir.mkdir(parents=True, exist_ok=True)

    tag_assignments_path = Path("assets/studio/data/tag_assignments.json").expanduser()
    tag_assignments_path.parent.mkdir(parents=True, exist_ok=True)
    series_index_json_path = Path(args.series_index_json_path).expanduser()
    series_index_json_path.parent.mkdir(parents=True, exist_ok=True)
    work_details_out_dir = Path(args.work_details_output_dir).expanduser()
    work_details_out_dir.mkdir(parents=True, exist_ok=True)
    works_json_dir = Path(args.works_json_dir).expanduser()
    works_json_dir.mkdir(parents=True, exist_ok=True)
    works_index_json_path = Path(args.works_index_json_path).expanduser()
    works_index_json_path.parent.mkdir(parents=True, exist_ok=True)
    recent_index_json_path = Path(args.recent_index_json_path).expanduser()
    recent_index_json_path.parent.mkdir(parents=True, exist_ok=True)
    work_storage_index_json_path = Path(args.work_storage_index_json_path).expanduser()
    work_storage_index_json_path.parent.mkdir(parents=True, exist_ok=True)
    moments_out_dir = Path(args.moments_output_dir).expanduser()
    moments_out_dir.mkdir(parents=True, exist_ok=True)
    moments_json_dir = Path(args.moments_json_dir).expanduser()
    moments_json_dir.mkdir(parents=True, exist_ok=True)
    moments_index_json_path = Path(args.moments_index_json_path).expanduser()
    moments_index_json_path.parent.mkdir(parents=True, exist_ok=True)
    projects_base_dir = Path(args.projects_base_dir).expanduser() if normalize_text(args.projects_base_dir) != "" else Path(".")
    projects_root = projects_base_dir / source_works_root_subdir(PIPELINE_CONFIG)

    def validate_source_records_for_writeback() -> None:
        validation_errors = validate_source_records(source_records)
        if validation_errors:
            raise SystemExit("JSON source write-back validation failed: " + "; ".join(validation_errors[:20]))

    def update_source_work_record(work_id: str, **updates: Any) -> None:
        record = source_records.works.get(work_id)
        if not isinstance(record, dict):
            return
        for key, value in updates.items():
            record[key] = value

    def update_source_detail_record(detail_uid: str, **updates: Any) -> None:
        record = source_records.work_details.get(detail_uid)
        if not isinstance(record, dict):
            return
        for key, value in updates.items():
            record[key] = value

    try:
        series_work_context = indexes.build_series_work_index_context(
            series_records=source_records.series,
            work_records=source_records.works,
        )
    except indexes.CatalogueGenerationIndexError as exc:
        raise SystemExit(str(exc)) from exc
    series_title_by_id = series_work_context.series_title_by_id
    series_status_by_id = series_work_context.series_status_by_id
    series_project_folders_by_id = series_work_context.series_project_folders_by_id
    work_meta_by_id = series_work_context.work_meta_by_id
    work_status_by_id = series_work_context.work_status_by_id
    work_ids_by_series_all = series_work_context.work_ids_by_series_all
    series_sort_by_series_id = series_work_context.series_sort_by_series_id
    series_sort_fields_by_series_id = series_work_context.series_sort_fields_by_series_id

    # Pre-index project folder by work_id for source media and dimension lookups.
    work_project_folder_by_id: Dict[str, str] = {}
    work_project_subfolder_by_id: Dict[str, str] = {}
    has_project_folder_col = any("project_folder" in work_record for work_record in source_records.works.values())
    for work_record in source_records.works.values():
        wid_raw = work_record.get("work_id")
        pf_raw = work_record.get("project_folder")
        if is_empty(wid_raw) or is_empty(pf_raw):
            continue
        wid = slug_id(wid_raw)
        work_project_folder_by_id[wid] = normalize_text(pf_raw)
        work_project_subfolder_by_id[wid] = normalize_text(work_record.get("project_subfolder"))

    def resolve_work_prose_source_path(wid: str) -> Path:
        return catalogue_prose_source_root / "works" / f"{wid}.md"

    def resolve_series_prose_source_path(series_id: str) -> Path:
        return catalogue_prose_source_root / "series" / f"{series_id}.md"

    written = 0
    skipped = 0
    run_work_processing = run_work_pages
    run_work_selection_scope = run_work_processing or run_work_json
    run_work_dimension_refresh = run_work_json

    def is_actionable_status(status_value: str) -> bool:
        if status_value == "draft":
            return True
        if status_value == "published" and refresh_published:
            return True
        return False

    # Optional filtering: allow a specific list of work_ids (from file or comma-separated arg).
    selected_ids = None
    explicit_work_filter = bool(args.work_ids_file or args.work_ids)
    if args.work_ids_file:
        ids_path = Path(args.work_ids_file).expanduser()
        if not ids_path.exists():
            raise SystemExit(f"work_ids file not found: {ids_path}")
        selected_ids = {slug_id(line.strip()) for line in ids_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    elif args.work_ids:
        selected_ids = parse_work_id_selection(args.work_ids)

    selected_series_ids = None
    if args.series_ids_file:
        sids_path = Path(args.series_ids_file).expanduser()
        if not sids_path.exists():
            raise SystemExit(f"series_ids file not found: {sids_path}")
        try:
            selected_series_ids = {
                normalize_series_id(line.strip())
                for line in sids_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            }
        except ValueError as exc:
            raise SystemExit(f"Invalid series_ids file value: {exc}") from exc
    elif args.series_ids:
        try:
            selected_series_ids = {
                normalize_series_id(sid.strip())
                for sid in args.series_ids.split(",")
                if sid.strip()
            }
        except ValueError as exc:
            raise SystemExit(f"Invalid --series-ids value: {exc}") from exc

    selected_moment_ids = None
    if args.moment_ids_file:
        mids_path = Path(args.moment_ids_file).expanduser()
        if not mids_path.exists():
            raise SystemExit(f"moment_ids file not found: {mids_path}")
        selected_moment_ids = {
            require_slug_safe("moment_id", normalize_text(line).lower())
            for line in mids_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    elif args.moment_ids:
        selected_moment_ids = {
            require_slug_safe("moment_id", normalize_text(mid).lower())
            for mid in args.moment_ids.split(",")
            if mid.strip()
        }
    explicit_moment_filter = bool(args.moment_ids_file or args.moment_ids)
    # If caller scopes by series but does not provide an explicit work filter:
    # - when work artifacts are explicitly selected via --only, derive selected work_ids from those series
    # - otherwise skip work-page processing by default (backward compatible behavior)
    if selected_series_ids is not None and not explicit_work_filter:
        if selected_artifacts is not None and run_work_selection_scope:
            selected_ids = set()
            for work_record in source_records.works.values():
                raw_work_id = work_record.get("work_id")
                if is_empty(raw_work_id):
                    continue
                wid = slug_id(raw_work_id)
                series_ids = records.parse_work_record_series_ids(work_record)
                if any(sid in selected_series_ids for sid in series_ids):
                    selected_ids.add(wid)
        else:
            selected_ids = set()
    # If caller scopes by work/series and does not provide an explicit moments filter,
    # skip moments generation by default (unless moments was explicitly selected via --only).
    run_moments = run_moments_artifact
    if (
        selected_artifacts is None
        and (explicit_work_filter or selected_series_ids is not None)
        and not explicit_moment_filter
    ):
        run_moments = False
        run_moments_index_json = False

    source_validation_errors = validate_source_records(source_records)
    if source_validation_errors:
        raise SystemExit("JSON source validation failed: " + "; ".join(source_validation_errors[:20]))

    work_dimensions_updated = 0
    work_project_folder_missing_warned = False
    if run_work_dimension_refresh:
        for work_record in source_records.works.values():
            raw_work_id = work_record.get("work_id")
            if is_empty(raw_work_id):
                continue
            wid = slug_id(raw_work_id)
            if selected_ids is not None and wid not in selected_ids:
                continue
            status = normalize_status(work_record.get("status"))
            if status not in {"draft", "published"}:
                continue

            width_px = coerce_int(work_record.get("width_px"))
            height_px = coerce_int(work_record.get("height_px"))
            project_filename = coerce_string(work_record.get("project_filename"))

            src_path: Optional[Path] = None
            if project_filename:
                if Path(project_filename).is_absolute():
                    src_path = Path(project_filename)
                else:
                    project_folder = work_project_folder_by_id.get(wid)
                    if project_folder:
                        src_path = projects_root / project_folder
                        project_subfolder = work_project_subfolder_by_id.get(wid)
                        if project_subfolder:
                            src_path = src_path / project_subfolder
                        src_path = src_path / project_filename
                    elif not work_project_folder_missing_warned:
                        if not has_project_folder_col:
                            print("Warning: work source records have no project_folder values; cannot persist work image dimensions.")
                        else:
                            print("Warning: missing Works.project_folder for one or more works; cannot persist those image dimensions.")
                        work_project_folder_missing_warned = True

            if src_path is not None:
                src_w, src_h = read_image_dims_px(src_path)
                if src_w is not None and src_h is not None:
                    prev_w = width_px
                    prev_h = height_px
                    width_px = src_w
                    height_px = src_h
                    if args.write and (prev_w != src_w or prev_h != src_h):
                        update_source_work_record(wid, width_px=src_w, height_px=src_h)
                        work_dimensions_updated += 1
                else:
                    print(f"Warning: could not read dimensions for work primary source image: {display_projects_path(src_path)}")
            elif project_filename:
                print(f"Warning: could not resolve work primary source image path for {wid} ({project_filename})")

            meta = work_meta_by_id.get(wid)
            if meta is not None:
                meta["width_px"] = width_px
                meta["height_px"] = height_px

    canonical_work_record_by_id: Dict[str, Dict[str, Any]] = {}
    for wid in sorted(work_meta_by_id.keys()):
        record = records.build_canonical_work_record(
            wid,
            work_meta_by_id=work_meta_by_id,
            source_work_record=source_records.works.get(wid, {}),
            series_title_by_id=series_title_by_id,
            series_sort_by_series_id=series_sort_by_series_id,
        )
        if record is not None:
            canonical_work_record_by_id[wid] = record

    total = 0
    if run_work_processing:
        for work_record in source_records.works.values():
            raw_work_id = work_record.get("work_id")
            if is_empty(raw_work_id):
                continue
            wid = slug_id(raw_work_id)
            if selected_ids is not None and wid not in selected_ids:
                continue
            status = normalize_status(work_record.get("status"))
            if is_actionable_status(status):
                total += 1

    processed = 0
    status_updated = 0
    published_date_updated = 0
    today = dt.date.today()
    work_publish_transitions: List[Dict[str, Any]] = []

    # Iterate each Works row and emit one Markdown file per work.
    if run_work_processing:
        for work_record in source_records.works.values():
            status = normalize_status(work_record.get("status"))
            raw_work_id = work_record.get("work_id")
            if is_empty(raw_work_id):
                skipped += 1
                continue
            wid = slug_id(raw_work_id)

            if selected_ids is not None and wid not in selected_ids:
                skipped += 1
                continue

            if not is_actionable_status(status):
                skipped += 1
                continue

            processed += 1
            prefix = f"[{processed}/{total}] "
            if run_work_pages:
                canonical_work_fm = records.build_canonical_work_record(
                    wid,
                    work_meta_by_id=work_meta_by_id,
                    source_work_record=source_records.works.get(wid, {}),
                    series_title_by_id=series_title_by_id,
                    series_sort_by_series_id=series_sort_by_series_id,
                )
                if canonical_work_fm is None:
                    skipped += 1
                    continue
                work_page_content = build_route_stub_content()
                out_path = out_dir / f"{wid}.md"

                def write_page(path: Path, label: str, page_content: str) -> bool:
                    exists = path.exists()
                    if exists and not args.force:
                        print(f"{prefix}SKIP ({label}; route exists): {display_path(path)}")
                        return False
                    if args.write:
                        path.write_text(page_content, encoding="utf-8")
                        print(f"{prefix}WRITE ({label}): {display_path(path)}")
                    else:
                        print(f"{prefix}DRY-RUN: would write {display_path(path)} (overwrite={exists})")
                    return True

                if write_page(out_path, "work", work_page_content):
                    written += 1
                    if args.write:
                        status_was = normalize_status(work_record.get("status"))
                        if status_was != "published":
                            update_source_work_record(wid, status="published")
                            status_updated += 1
                        if status_was != "published":
                            update_source_work_record(wid, published_date=today.isoformat())
                            published_date_updated += 1
                        if status_was != "published":
                            work_meta = work_meta_by_id.get(wid, {})
                            series_ids = work_meta.get("series_ids") if isinstance(work_meta, dict) else []
                            primary_series_id = series_ids[0] if isinstance(series_ids, list) and series_ids else ""
                            work_publish_transitions.append({
                                "work_id": wid,
                                "title": coerce_string(work_meta.get("title")) if isinstance(work_meta, dict) else None,
                                "primary_series_id": primary_series_id,
                                "series_title": series_title_by_id.get(primary_series_id) if primary_series_id else None,
                                "published_date": today.isoformat(),
                            })
                else:
                    skipped += 1

    if args.write and (
        status_updated > 0
        or work_dimensions_updated > 0
    ):
        if status_updated > 0:
            print(f"Updated status to 'published' for {status_updated} row(s).")
        if published_date_updated > 0:
            print(f"Set published_date for {published_date_updated} row(s).")
        if work_dimensions_updated > 0:
            print(f"Updated work width_px/height_px for {work_dimensions_updated} row(s).")
    if run_work_processing:
        print(
            f"\nDone. {'Would write' if not args.write else 'Wrote'}: "
            f"{written} works. Skipped: {skipped} works."
        )
        print(f"Catalogue source: {display_path(json_source_dir)}")
        if args.write:
            print("Canonical source write-back runs after generation completes.")
    else:
        print("Work pages skipped: not selected by --only.")

    # Determine series scope for this run:
    # - If caller explicitly scoped series via --series-ids, honor that.
    # - If caller scoped only works (--work-ids/--work-ids-file), skip series pages by default.
    series_page_selected_ids = selected_series_ids
    if explicit_work_filter and selected_series_ids is None:
        if selected_artifacts is None:
            run_series_pages = False

    # ----------------------------
    # Series page generation (Series)
    # ----------------------------
    # Series source required fields:
    # - series_id
    # - title
    # Optional columns:
    # - year_display (preferred display value)
    # - year (numeric; also fallback for display when year_display column absent)

    series_publish_transitions: List[Dict[str, Any]] = []

    if not source_records.series:
        print("No series pages to generate (series source records empty).")
    else:
        def is_actionable_series_status(status_value: str) -> bool:
            if status_value == "published" and refresh_published:
                return True
            return False

        series_written = 0
        series_skipped = 0
        series_json_written = 0
        series_json_skipped = 0
        series_status_updated = 0
        series_published_date_updated = 0
        studio_series_written = 0
        studio_series_skipped = 0
        tag_assignments_payload = load_tag_assignments_payload(tag_assignments_path)
        tag_assignments_series = tag_assignments_payload.get("series", {})
        tag_assignments_changed = False
        tag_assignments_added = 0
        s_total = 0
        for series_record in source_records.series.values():
            sid_raw = series_record.get("series_id")
            if is_empty(sid_raw):
                continue
            sid = normalize_series_id(sid_raw)
            if series_page_selected_ids is not None and sid not in series_page_selected_ids:
                continue
            status = normalize_status(series_record.get("status"))
            if is_actionable_series_status(status):
                s_total += 1
        s_processed = 0

        if run_series_pages:
            for series_record in source_records.series.values():
                sid_raw = series_record.get("series_id")
                if is_empty(sid_raw):
                    series_skipped += 1
                    continue
                series_id = normalize_series_id(sid_raw)
                if series_page_selected_ids is not None and series_id not in series_page_selected_ids:
                    series_skipped += 1
                    continue

                status = normalize_status(series_record.get("status"))
                if not is_actionable_series_status(status):
                    series_skipped += 1
                    continue

                s_processed += 1
                prefix_s = f"[series {s_processed}/{s_total}] "

                title_raw = series_record.get("title")
                series_title = coerce_string(title_raw) or series_id

                # Numeric year (optional)
                year = coerce_int(series_record.get("year"))

                # year_display handling:
                # - If source has a year_display value, use it.
                # - Otherwise fall back to numeric year rendered as text.
                year_display: Optional[str]
                year_display = coerce_string(series_record.get("year_display"))
                if year_display is None:
                    year_display = str(year) if year is not None else None

                series_work_ids_sorted = sorted(
                    work_id for work_id in work_ids_by_series_all.get(series_id, [])
                    if work_status_by_id.get(work_id) == "published"
                )
                try:
                    primary_work_id = indexes.require_series_primary_work_id(
                        series_id,
                        series_record,
                        ordered_work_ids=series_work_ids_sorted,
                    )
                except indexes.CatalogueGenerationIndexError as exc:
                    raise SystemExit(str(exc)) from exc
                published_date = parse_date(series_record.get("published_date"))
                series_output_record = compact_json_object({
                    "series_id": series_id,
                    "layout": "series",
                    "status": status,
                    "published_date": published_date,
                    "title": series_title,
                    "sort_fields": ",".join(series_sort_fields_by_series_id.get(series_id, ["work_id"])),
                    "series_type": coerce_string(series_record.get("series_type")),
                    "year": year,
                    "year_display": year_display,
                    "notes": coerce_string(series_record.get("notes")),
                    "project_folders": series_project_folders_by_id.get(series_id, []),
                })

                public_series_record = records.build_series_json_record(series_output_record)
                source_prose_path = resolve_series_prose_source_path(series_id)
                content_html: Optional[str] = None
                if source_prose_path.exists():
                    content_html = render_markdown_with_jekyll(source_prose_path)

                payload_version = compute_payload_version(
                    compact_json_object({
                        "series": public_series_record,
                        "content_html": content_html,
                        "work_count": len(series_work_ids_sorted),
                    })
                )
                series_content = build_route_stub_content()

                series_path = series_out_dir / f"{series_id}.md"
                series_exists = series_path.exists()
                if series_exists and not args.force:
                    print(f"{prefix_s}SKIP (route exists): {display_path(series_path)}")
                    series_skipped += 1
                else:
                    if args.write:
                        series_path.write_text(series_content, encoding="utf-8")
                        print(f"{prefix_s}WRITE: {display_path(series_path)}")
                        series_written += 1
                    else:
                        print(f"{prefix_s}DRY-RUN: would write {display_path(series_path)} (overwrite={series_exists})")
                        series_written += 1

                payload = compact_json_object({
                    "header": {
                        "schema": "series_record_v1",
                        "version": payload_version,
                        "generated_at_utc": utc_timestamp_now(),
                        "series_id": series_id,
                        "count": len(series_work_ids_sorted),
                    },
                    "series": public_series_record,
                    "content_html": content_html,
                })
                out_json_path = series_json_dir / f"{series_id}.json"
                out_exists = out_json_path.exists()
                existing_payload_version = extract_existing_header_scalar(out_json_path, "version") if out_exists else None
                if (existing_payload_version is not None) and (existing_payload_version == payload_version) and (not args.force):
                    series_json_skipped += 1
                else:
                    if args.write:
                        out_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print(f"[Series JSON {s_processed}/{s_total}] WRITE: {display_path(out_json_path)}")
                        series_json_written += 1
                    else:
                        print(f"[Series JSON {s_processed}/{s_total}] DRY-RUN: would write {display_path(out_json_path)} (overwrite={out_exists})")
                        series_json_written += 1

                if run_studio_series_pages:
                    if studio_series_out_dir is None:
                        raise RuntimeError("studio_series_out_dir is not initialized")
                    tsm: Dict[str, Any] = {
                        "layout": "studio_series",
                        "series_id": series_id,
                        "title": series_title,
                        "sort_fields": ",".join(series_sort_fields_by_series_id.get(series_id, ["work_id"])),
                        "year": year,
                        "year_display": year_display,
                        "project_folders": series_project_folders_by_id.get(series_id, []),
                        "notes": coerce_string(series_record.get("notes")),
                        "primary_work_id": primary_work_id,
                    }
                    studio_series_content = build_front_matter(tsm) + "\n"
                    studio_series_path = studio_series_out_dir / f"{series_id}.md"

                    existing_studio_series_text = None
                    if studio_series_path.exists():
                        try:
                            existing_studio_series_text = studio_series_path.read_text(encoding="utf-8")
                        except Exception:
                            existing_studio_series_text = None

                    studio_series_needs_write = (existing_studio_series_text != studio_series_content)
                    prefix_ts = f"[studio-series {s_processed}/{s_total}] "
                    if (not studio_series_needs_write) and (not args.force):
                        print(f"{prefix_ts}SKIP (no change): {studio_series_path}")
                        studio_series_skipped += 1
                    else:
                        if args.write:
                            studio_series_path.write_text(studio_series_content, encoding="utf-8")
                            print(f"{prefix_ts}WRITE: {display_path(studio_series_path)}")
                            studio_series_written += 1
                        else:
                            print(f"{prefix_ts}DRY-RUN: would write {display_path(studio_series_path)} (overwrite={studio_series_path.exists()})")
                            studio_series_written += 1

                if series_id not in tag_assignments_series:
                    tag_assignments_series[series_id] = {
                        "tags": [],
                        "works": {},
                        "updated_at_utc": utc_timestamp_now(),
                    }
                    tag_assignments_changed = True
                    tag_assignments_added += 1
                else:
                    assignment_row = tag_assignments_series.get(series_id)
                    if not isinstance(assignment_row, dict):
                        tag_assignments_series[series_id] = {
                            "tags": [],
                            "works": {},
                            "updated_at_utc": utc_timestamp_now(),
                        }
                        tag_assignments_changed = True
                    else:
                        if not isinstance(assignment_row.get("tags"), list):
                            assignment_row["tags"] = []
                            tag_assignments_changed = True
                        if "works" not in assignment_row or not isinstance(assignment_row.get("works"), dict):
                            assignment_row["works"] = {}
                            tag_assignments_changed = True
        else:
            if selected_artifacts is not None and not artifact_enabled("series-pages"):
                print("Series pages skipped: not selected by --only.")
            else:
                print("Series pages skipped: --work-ids scope active (use --series-ids to include series page rebuild).")
            print("Studio series pages retired: skipped.")
            print("Tag assignments sync skipped: follows series-pages selection.")

        if run_series_pages:
            if tag_assignments_changed:
                tag_assignments_payload["series"] = tag_assignments_series
                tag_assignments_payload["updated_at_utc"] = utc_timestamp_now()
                tag_assignments_text = json.dumps(tag_assignments_payload, indent=2, ensure_ascii=False) + "\n"
                if args.write:
                    tag_assignments_path.write_text(tag_assignments_text, encoding="utf-8")
                    print(
                        f"Tag assignments sync: WRITE {display_path(tag_assignments_path)} "
                        f"(added missing entries: {tag_assignments_added})."
                    )
                else:
                    print(
                        f"Tag assignments sync: DRY-RUN would write {display_path(tag_assignments_path)} "
                        f"(added missing entries: {tag_assignments_added})."
                    )
            else:
                print("Tag assignments sync: no missing series entries.")

        if args.write and (series_status_updated > 0 or series_published_date_updated > 0):
            if series_status_updated > 0:
                print(f"Updated series status to 'published' for {series_status_updated} row(s).")
            if series_published_date_updated > 0:
                print(f"Set series published_date for {series_published_date_updated} row(s).")
        print(f"Series pages done. {'Would write' if not args.write else 'Wrote'}: {series_written}. Skipped: {series_skipped}.")
        print(
            f"Series JSON done. {'Would write' if not args.write else 'Wrote'}: "
            f"{series_json_written}. Skipped: {series_json_skipped}."
        )
        if run_studio_series_pages:
            print(
                f"Studio series pages done. {'Would write' if not args.write else 'Wrote'}: "
                f"{studio_series_written}. Skipped: {studio_series_skipped}."
            )
        else:
            print("Studio series pages retired: skipped.")

    try:
        series_index_payload = indexes.build_series_index_payload(
            series_records=source_records.series,
            context=series_work_context,
            generated_at_utc=utc_timestamp_now(),
        )
    except indexes.CatalogueGenerationIndexError as exc:
        raise SystemExit(str(exc)) from exc
    series_payload: Dict[str, Dict[str, Any]] = series_index_payload.get("series", {})
    series_version = series_index_payload["header"]["version"]

    exists = series_index_json_path.exists()
    existing_version = extract_existing_header_scalar(series_index_json_path, "version") if exists else None
    if (existing_version is not None) and (existing_version == series_version) and (not args.force):
        print("Series index JSON done. Wrote: 0. Skipped: 1.")
    else:
        if args.write:
            series_index_json_path.write_text(
                json.dumps(series_index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Series index JSON done. Wrote: 1. Skipped: 0. Path: {display_path(series_index_json_path)}")
        else:
            print(
                "Series index JSON done. Would write: 1. Skipped: 0. "
                f"Path: {display_path(series_index_json_path)} (overwrite={exists})"
            )

    # ----------------------------
    # Work detail page generation + per-work detail JSON (WorkDetails)
    # ----------------------------
    if not source_records.work_details:
        if run_work_details_pages or run_work_json or run_works_index_json:
            print("No work detail pages/JSON/index rows found (work detail source records empty or missing).")
        else:
            print("Work detail pages/JSON skipped: not selected by --only.")
    else:
        projects_base_dir = Path(args.projects_base_dir).expanduser()
        projects_root = projects_base_dir / source_works_root_subdir(PIPELINE_CONFIG)

        # Build known works from source records to validate foreign-key references.
        known_work_ids: set[str] = set()
        for work_record in source_records.works.values():
            wid_raw = work_record.get("work_id")
            if is_empty(wid_raw):
                continue
            known_work_ids.add(slug_id(wid_raw))

        def is_actionable_detail_status(status_value: str) -> bool:
            if status_value == "draft":
                return True
            if status_value == "published" and refresh_published:
                return True
            return False

        if run_work_details_pages:
            details_written = 0
            details_skipped = 0
            details_status_updated = 0
            details_published_date_updated = 0
            details_dimensions_updated = 0
            project_folder_missing_warned = False
            details_total = 0

            for detail_source_record in source_records.work_details.values():
                wid_raw = detail_source_record.get("work_id")
                if is_empty(wid_raw):
                    continue
                wid = slug_id(wid_raw)
                if selected_ids is not None and wid not in selected_ids:
                    continue
                status = normalize_status(detail_source_record.get("status"))
                if is_actionable_detail_status(status):
                    details_total += 1

            details_processed = 0
            for detail_source_record in source_records.work_details.values():
                wid_raw = detail_source_record.get("work_id")
                did_raw = detail_source_record.get("detail_id")
                if is_empty(wid_raw) or is_empty(did_raw):
                    details_skipped += 1
                    continue

                wid = slug_id(wid_raw)
                if selected_ids is not None and wid not in selected_ids:
                    details_skipped += 1
                    continue

                if wid not in known_work_ids:
                    print(f"Warning: skipping work detail for unknown work_id {wid}: detail_id={did_raw}")
                    details_skipped += 1
                    continue

                status = normalize_status(detail_source_record.get("status"))
                if not is_actionable_detail_status(status):
                    details_skipped += 1
                    continue

                details_processed += 1
                prefix_d = f"[details {details_processed}/{details_total}] "

                did = slug_id(did_raw, width=3)
                detail_uid = f"{wid}-{did}"
                details_subfolder = coerce_string(
                    detail_source_record.get("details_subfolder") or detail_source_record.get("project_subfolder")
                )
                project_filename = coerce_string(detail_source_record.get("project_filename"))
                width_px = coerce_int(detail_source_record.get("width_px"))
                height_px = coerce_int(detail_source_record.get("height_px"))

                # Resolve source image and persist dimensions back to WorkDetails for stable future rebuilds.
                project_folder = work_project_folder_by_id.get(wid)
                src_path: Optional[Path] = None
                if project_folder and project_filename:
                    src_path = projects_root / project_folder
                    if details_subfolder:
                        src_path = src_path / details_subfolder
                    src_path = src_path / project_filename
                elif not project_folder_missing_warned:
                    if not has_project_folder_col:
                        print("Warning: work source records have no project_folder values; cannot persist work detail image dimensions.")
                    else:
                        print("Warning: missing work project_folder for one or more work detail records; cannot persist those image dimensions.")
                    project_folder_missing_warned = True

                if src_path is not None:
                    src_w, src_h = read_image_dims_px(src_path)
                    if src_w is not None and src_h is not None:
                        prev_w = width_px
                        prev_h = height_px
                        width_px = src_w
                        height_px = src_h
                        if args.write and (prev_w != src_w or prev_h != src_h):
                            update_source_detail_record(detail_uid, width_px=src_w, height_px=src_h)
                            details_dimensions_updated += 1
                    else:
                        print(f"Warning: could not read dimensions for detail source image: {display_projects_path(src_path)}")
                elif project_filename:
                    print(f"Warning: could not resolve detail source image path for {detail_uid} ({project_filename})")

                d_content = build_route_stub_content()
                d_path = work_details_out_dir / f"{detail_uid}.md"
                d_exists = d_path.exists()
                if d_exists and not args.force:
                    details_skipped += 1
                    continue

                if args.write:
                    d_path.write_text(d_content, encoding="utf-8")
                    print(f"{prefix_d}WRITE: {display_path(d_path)}")
                    details_written += 1

                    status_was = normalize_status(detail_source_record.get("status"))
                    if status_was != "published":
                        update_source_detail_record(detail_uid, status="published")
                        details_status_updated += 1
                        update_source_detail_record(detail_uid, published_date=today.isoformat())
                        details_published_date_updated += 1
                else:
                    print(f"{prefix_d}DRY-RUN: would write {display_path(d_path)} (overwrite={d_exists})")
                    details_written += 1

            if args.write and (details_status_updated > 0 or details_published_date_updated > 0 or details_dimensions_updated > 0):
                if details_status_updated > 0:
                    print(f"Updated work detail status to 'published' for {details_status_updated} row(s).")
                if details_published_date_updated > 0:
                    print(f"Set work detail published_date for {details_published_date_updated} row(s).")
                if details_dimensions_updated > 0:
                    print(f"Updated work detail width_px/height_px for {details_dimensions_updated} row(s).")

            print(
                f"Work detail pages done. {'Would write' if not args.write else 'Wrote'}: {details_written}. Skipped: {details_skipped}."
            )
        else:
            print("Work detail pages skipped: not selected by --only.")

        if run_work_json:
            # Build per-work JSON from Works rows (work-driven).
            # Detail sections are sourced from currently published detail rows only.
            encountered_work_ids: List[str] = []
            encountered_work_id_set: set[str] = set()
            detail_records_by_work: Dict[str, List[Dict[str, Any]]] = {}
            section_resolution_by_uid = build_detail_section_resolution_by_uid(source_records.work_details)

            for work_record in source_records.works.values():
                wid_raw = work_record.get("work_id")
                if is_empty(wid_raw):
                    continue
                wid = slug_id(wid_raw)
                if selected_ids is not None and wid not in selected_ids:
                    continue
                status = normalize_status(work_record.get("status"))
                if status not in {"draft", "published"}:
                    continue
                if wid not in canonical_work_record_by_id:
                    continue
                if wid not in encountered_work_id_set:
                    encountered_work_ids.append(wid)
                    encountered_work_id_set.add(wid)

            for detail_uid, detail_source_record in source_records.work_details.items():
                wid_raw = detail_source_record.get("work_id")
                did_raw = detail_source_record.get("detail_id")
                if is_empty(wid_raw) or is_empty(did_raw):
                    continue

                wid = slug_id(wid_raw)
                if wid not in encountered_work_id_set:
                    continue

                if normalize_status(detail_source_record.get("status")) != "published":
                    continue

                did = slug_id(did_raw, width=3)
                section_resolution = section_resolution_by_uid.get(detail_uid, {})
                detail_record = records.build_canonical_detail_record(
                    wid=wid,
                    did=did,
                    title=coerce_string(detail_source_record.get("title")),
                    section_id=coerce_string(section_resolution.get("section_id")),
                    section_title=coerce_string(section_resolution.get("section_title")),
                    sort_order=coerce_int(section_resolution.get("sort_order")),
                    width_px=coerce_int(detail_source_record.get("width_px")),
                    height_px=coerce_int(detail_source_record.get("height_px")),
                )
                detail_records_by_work.setdefault(wid, []).append(detail_record)

            wj_written = 0
            wj_skipped = 0
            wj_total = len(encountered_work_ids)
            wj_processed = 0
            generated_at_utc = utc_timestamp_now()

            for wid in encountered_work_ids:
                wj_processed += 1
                prefix_wj = f"[Work JSON {wj_processed}/{wj_total}] "

                source_prose_path = resolve_work_prose_source_path(wid)

                sections = records.build_sections_from_detail_records(detail_records_by_work.get(wid, []))
                details_total = sum(len(s.get("details", [])) for s in sections)
                work_record = records.build_work_json_record(canonical_work_record_by_id.get(wid, {"work_id": wid}))
                content_html: Optional[str] = None
                if source_prose_path.exists():
                    content_html = render_markdown_with_jekyll(source_prose_path)
                payload_version = compute_payload_version(compact_json_object({"work": work_record, "sections": sections, "content_html": content_html}))

                payload = compact_json_object({
                    "header": {
                        "schema": "work_record_v3",
                        "version": payload_version,
                        "generated_at_utc": generated_at_utc,
                        "work_id": wid,
                        "count": details_total,
                    },
                    "work": work_record,
                    "sections": sections,
                    "content_html": content_html,
                })
                out_json_path = works_json_dir / f"{wid}.json"
                exists = out_json_path.exists()
                existing_version = extract_existing_header_scalar(out_json_path, "version") if exists else None
                payload_version = payload["header"]["version"]

                if (existing_version is not None) and (existing_version == payload_version) and (not args.force):
                    wj_skipped += 1
                    continue

                if args.write:
                    out_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"{prefix_wj}WRITE: {display_path(out_json_path)}")
                    wj_written += 1
                else:
                    print(f"{prefix_wj}DRY-RUN: would write {display_path(out_json_path)} (overwrite={exists})")
                    wj_written += 1

            print(
                f"Work JSON done. {'Would write' if not args.write else 'Wrote'}: {wj_written}. Skipped: {wj_skipped}."
            )
        else:
            print("Work detail JSON skipped: not selected by --only.")

    works_payload = indexes.build_works_index_records(
        work_records=source_records.works,
        canonical_work_record_by_id=canonical_work_record_by_id,
    )
    work_storage_payload = indexes.build_work_storage_index_records(
        works=works_payload,
        canonical_work_record_by_id=canonical_work_record_by_id,
    )

    payload = indexes.build_works_index_payload(
        works=works_payload,
        generated_at_utc=utc_timestamp_now(),
    )
    payload_version = payload["header"]["version"]
    exists = works_index_json_path.exists()
    existing_version = extract_existing_header_scalar(works_index_json_path, "version") if exists else None
    if (existing_version is not None) and (existing_version == payload_version) and (not args.force):
        print("Works index JSON done. Wrote: 0. Skipped: 1.")
    else:
        if args.write:
            works_index_json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Works index JSON done. Wrote: 1. Skipped: 0. Path: {display_path(works_index_json_path)}")
        else:
            print(
                "Works index JSON done. Would write: 1. Skipped: 0. "
                f"Path: {display_path(works_index_json_path)} (overwrite={exists})"
            )

    recent_entries = recent.build_recent_publication_entries(
        existing_entries=load_recent_entries(recent_index_json_path),
        series_publish_transitions=series_publish_transitions,
        work_publish_transitions=work_publish_transitions,
        series_payload=series_payload,
        works_payload=works_payload,
        work_meta_by_id=work_meta_by_id,
        work_status_by_id=work_status_by_id,
        series_status_by_id=series_status_by_id,
        series_sort_by_series_id=series_sort_by_series_id,
        series_title_by_id=series_title_by_id,
        recorded_at_utc=utc_timestamp_now(),
    )
    recent_index_payload = recent.build_recent_index_payload(
        entries=recent_entries,
        generated_at_utc=utc_timestamp_now(),
    )
    recent_exists = recent_index_json_path.exists()
    recent_existing_version = extract_existing_header_scalar(recent_index_json_path, "version") if recent_exists else None
    recent_payload_version = recent_index_payload["header"]["version"]
    if (recent_existing_version is not None) and (recent_existing_version == recent_payload_version) and (not args.force):
        print("Recent index JSON done. Wrote: 0. Skipped: 1.")
    else:
        if args.write:
            recent_index_json_path.write_text(
                json.dumps(recent_index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Recent index JSON done. Wrote: 1. Skipped: 0. Path: {display_path(recent_index_json_path)}")
        else:
            print(
                "Recent index JSON done. Would write: 1. Skipped: 0. "
                f"Path: {display_path(recent_index_json_path)} (overwrite={recent_exists})"
            )

    work_storage_payload_out = indexes.build_work_storage_index_payload(
        works=work_storage_payload,
        generated_at_utc=utc_timestamp_now(),
    )
    work_storage_payload_version = work_storage_payload_out["header"]["version"]
    work_storage_exists = work_storage_index_json_path.exists()
    existing_work_storage_version = extract_existing_header_scalar(work_storage_index_json_path, "version") if work_storage_exists else None
    if (existing_work_storage_version is not None) and (existing_work_storage_version == work_storage_payload_version) and (not args.force):
        print("Work storage index JSON done. Wrote: 0. Skipped: 1.")
    else:
        if args.write:
            work_storage_index_json_path.write_text(
                json.dumps(work_storage_payload_out, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Work storage index JSON done. Wrote: 1. Skipped: 0. Path: {display_path(work_storage_index_json_path)}")
        else:
            print(
                "Work storage index JSON done. Would write: 1. Skipped: 0. "
                f"Path: {display_path(work_storage_index_json_path)} (overwrite={work_storage_exists})"
            )

    # ----------------------------
    # Moment page + JSON generation (Moments)
    # ----------------------------
    # Required columns:
    # - moment_id, title, status, published_date, date, date_display,
    #   width_px, height_px
    # Optional columns:
    # - moment_id / slug / id (preferred filename stem)
    # - date, date_display
    # - image_file/image_filename/project_filename
    # - image_alt
    # - width_px, height_px
    # - project_folder, project_subfolder, project_filename, work_id (for source image resolution)
    moment_source_records: List[Dict[str, Any]] = []
    projects_base_dir = Path(args.projects_base_dir).expanduser()
    moments_images_root = projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG)
    moments_prose_root = repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR
    source_moment_index = build_moment_metadata_source_index(
        json_source_dir,
        repo_root=repo_root,
        moments_images_root=moments_images_root,
    )
    if not run_moments and not run_moments_index_json:
        if selected_artifacts is not None and not run_moments_artifact and not run_moments_index_json:
            print("Moment pages/JSON skipped: not selected by --only.")
        else:
            print("Moment pages/JSON skipped: scoped run without --moment-ids/--moment-ids-file.")
    elif not source_moment_index:
        print("No moment artifacts to generate (no moment metadata records found).")
    else:
        def collect_moment_source_records() -> List[Dict[str, Any]]:
            records: List[Dict[str, Any]] = []
            for moment_id in sorted(source_moment_index.keys()):
                source_record = source_moment_index[moment_id]
                records.append({
                    "moment_id": moment_id,
                    "title": coerce_string(source_record.get("title")) or moment_id,
                    "status": normalize_status(source_record.get("status")),
                    "published_date": parse_date(source_record.get("published_date")),
                    "date": parse_date(source_record.get("date")),
                    "date_display": coerce_string(source_record.get("date_display")),
                    "width_px": None,
                    "height_px": None,
                    "image_file": f"{moment_id}.jpg",
                    "source_image_file": coerce_string(source_record.get("source_image_file")) or f"{moment_id}.jpg",
                    "image_alt": coerce_string(source_record.get("image_alt")),
                    "source_prose_path": Path(coerce_string(source_record.get("source_prose_path")) or (moments_prose_root / f"{moment_id}.md")),
                    "source_image_path": moments_images_root / ((coerce_string(source_record.get("source_image_file")) or f"{moment_id}.jpg")),
                })
            return records

        moment_source_records = collect_moment_source_records()

        def is_actionable_moment_status(status_value: str) -> bool:
            if status_value == "draft":
                return True
            if status_value == "published" and refresh_published:
                return True
            return False

        moments_pages_total = 0
        moments_json_total = 0
        for moment_entry in moment_source_records:
            mid = str(moment_entry.get("moment_id") or "").strip().lower()
            if not mid:
                continue
            if selected_moment_ids is not None and mid not in selected_moment_ids:
                continue
            status = normalize_status(moment_entry.get("status"))
            if run_moments and is_actionable_moment_status(status):
                moments_pages_total += 1
                moments_json_total += 1

        moments_pages_written = 0
        moments_pages_skipped = 0
        moments_json_written = 0
        moments_json_skipped = 0
        moment_json_generated_at_utc = utc_timestamp_now()
        moments_processed = 0

        for moment_entry in moment_source_records:
            moment_id = str(moment_entry.get("moment_id") or "").strip().lower()
            if not moment_id:
                if run_moments:
                    moments_pages_skipped += 1
                    moments_json_skipped += 1
                continue
            mid = moment_id
            if selected_moment_ids is not None and mid not in selected_moment_ids:
                if run_moments:
                    moments_pages_skipped += 1
                    moments_json_skipped += 1
                continue
            status = normalize_status(moment_entry.get("status"))
            moment_actionable = run_moments and is_actionable_moment_status(status)
            if not moment_actionable and run_moments:
                moments_pages_skipped += 1
                moments_json_skipped += 1
            if not moment_actionable:
                continue

            if not is_slug_safe(moment_id):
                raise SystemExit(f"Moment source filename must be slug-safe; got: {moment_id!r}")

            moments_processed += 1
            prefix_m = f"[moment {moment_id}] "
            print(f"[moment {moments_processed}/{moments_pages_total}] {moment_id}", flush=True)

            title = coerce_string(moment_entry.get("title")) or moment_id
            date_value = parse_date(moment_entry.get("date"))
            date_display = coerce_string(moment_entry.get("date_display"))
            width_px = coerce_int(moment_entry.get("width_px"))
            height_px = coerce_int(moment_entry.get("height_px"))

            default_moment_filename = f"{moment_id}.jpg"
            image_file = coerce_string(moment_entry.get("image_file")) or default_moment_filename
            source_image_file = coerce_string(moment_entry.get("source_image_file")) or default_moment_filename
            image_alt = coerce_string(moment_entry.get("image_alt"))

            # Resolve source image for dimensions when possible.
            src_path: Optional[Path] = None
            source_filename = source_image_file
            if source_filename:
                source_image_path_value = coerce_string(moment_entry.get("source_image_path"))
                src_path = Path(source_image_path_value) if source_image_path_value else (moments_images_root / source_filename)

            source_image_exists = bool(src_path is not None and src_path.exists())

            if src_path is not None:
                src_w, src_h = read_image_dims_px(src_path)
                if src_w is not None and src_h is not None:
                    width_px = src_w
                    height_px = src_h

            images_list: List[Dict[str, Any]] = []
            if image_file is not None and image_alt is None:
                image_alt = title or moment_id
            if image_file is not None and source_image_exists:
                images_list.append(
                    {
                        "file": image_file,
                        "alt": image_alt,
                    }
                )

            moment_record: Dict[str, Any] = {
                "moment_id": moment_id,
                "title": title or moment_id,
                "date": date_value,
                "date_display": date_display,
                "images": images_list,
                "width_px": width_px,
                "height_px": height_px,
                "layout": "moment",
            }
            source_prose_path_value = coerce_string(moment_entry.get("source_prose_path"))
            source_prose_path = Path(source_prose_path_value) if source_prose_path_value else (moments_prose_root / f"{moment_id}.md")
            if not source_prose_path.exists():
                print(f"{prefix_m}WARNING: missing source prose {display_projects_path(source_prose_path)}; skipping moment.")
                if moment_actionable:
                    moments_pages_skipped += 1
                    moments_json_skipped += 1
                continue

            if moment_actionable:
                m_content = build_route_stub_content()
                m_path = moments_out_dir / f"{moment_id}.md"
                m_exists = m_path.exists()

                if m_exists and not args.force:
                    moments_pages_skipped += 1
                else:
                    if args.write:
                        m_path.write_text(m_content, encoding="utf-8")
                        print(f"{prefix_m}WRITE: {display_path(m_path)}")
                        moments_pages_written += 1
                    else:
                        print(f"{prefix_m}DRY-RUN: would write {display_path(m_path)} (overwrite={m_exists})")
                        moments_pages_written += 1

                content_html = render_markdown_with_jekyll(source_prose_path)
                moment_json_record = records.build_moment_json_record(moment_record)
                payload_version = compute_payload_version(compact_json_object({"moment": moment_json_record, "content_html": content_html}))
                payload = compact_json_object({
                    "header": {
                        "schema": "moment_record_v1",
                        "version": payload_version,
                        "generated_at_utc": moment_json_generated_at_utc,
                        "moment_id": moment_id,
                    },
                    "moment": moment_json_record,
                    "content_html": content_html,
                })
                out_json_path = moments_json_dir / f"{moment_id}.json"
                exists = out_json_path.exists()
                existing_version = extract_existing_header_scalar(out_json_path, "version") if exists else None
                payload_version = payload["header"]["version"]

                if (existing_version is not None) and (existing_version == payload_version) and (not args.force):
                    moments_json_skipped += 1
                else:
                    if args.write:
                        out_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print(f"{prefix_m}WRITE moment JSON: {display_path(out_json_path)}")
                        moments_json_written += 1
                    else:
                        print(f"{prefix_m}DRY-RUN: would write moment JSON {display_path(out_json_path)} (overwrite={exists})")
                        moments_json_written += 1

        if run_moments:
            print(
                f"Moment pages done. {'Would write' if not args.write else 'Wrote'}: {moments_pages_written}. Skipped: {moments_pages_skipped}."
            )
            print(
                f"Moment JSON done. {'Would write' if not args.write else 'Wrote'}: {moments_json_written}. Skipped: {moments_json_skipped}."
            )

    moments_payload: Dict[str, Dict[str, Any]] = {}
    projects_base_dir = Path(args.projects_base_dir).expanduser()
    moments_images_root = projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG)

    for moment_entry in moment_source_records:
        moment_id = str(moment_entry.get("moment_id") or "").strip().lower()
        if not moment_id:
            continue

        status = normalize_status(moment_entry.get("status"))
        if status not in {"draft", "published"}:
            continue

        if not is_slug_safe(moment_id):
            raise SystemExit(f"Moment source filename must be slug-safe; got: {moment_id!r}")

        title = coerce_string(moment_entry.get("title")) or moment_id
        date_value = parse_date(moment_entry.get("date"))
        date_display = coerce_string(moment_entry.get("date_display"))
        width_px = coerce_int(moment_entry.get("width_px"))
        height_px = coerce_int(moment_entry.get("height_px"))
        image_file = coerce_string(moment_entry.get("image_file")) or f"{moment_id}.jpg"
        source_image_file = coerce_string(moment_entry.get("source_image_file")) or f"{moment_id}.jpg"
        image_alt = coerce_string(moment_entry.get("image_alt"))

        src_path: Optional[Path] = None
        source_filename = source_image_file
        if source_filename:
            source_image_path_value = coerce_string(moment_entry.get("source_image_path"))
            src_path = Path(source_image_path_value) if source_image_path_value else (moments_images_root / source_filename)

        source_image_exists = bool(src_path is not None and src_path.exists())

        if src_path is not None:
            src_w, src_h = read_image_dims_px(src_path)
            if src_w is not None and src_h is not None:
                width_px = src_w
                height_px = src_h

        images_list: List[Dict[str, Any]] = []
        if image_file is not None and image_alt is None:
            image_alt = title or moment_id
        if image_file is not None and source_image_exists:
            images_list.append(
                {
                    "file": image_file,
                    "alt": image_alt,
                }
            )

        source_prose_path_value = coerce_string(moment_entry.get("source_prose_path"))
        source_prose_path = Path(source_prose_path_value) if source_prose_path_value else (moments_prose_root / f"{moment_id}.md")
        if not source_prose_path.exists():
            print(f"[moment {moment_id}] WARNING: missing source prose {display_projects_path(source_prose_path)}; skipping moments index.")
            continue

        moment_record = {
            "moment_id": moment_id,
            "title": title,
            "date": date_value,
            "date_display": date_display,
            "images": images_list,
            "width_px": width_px,
            "height_px": height_px,
        }
        moments_payload[moment_id] = records.build_moment_index_record(moment_record)

    version_payload = compact_json_object({
        "schema": "moments_index_v1",
        "moments": moments_payload,
    })
    version = compute_payload_version(version_payload)
    payload = compact_json_object({
        "header": {
            "schema": "moments_index_v1",
            "version": version,
            "generated_at_utc": utc_timestamp_now(),
            "count": len(moments_payload),
        },
        "moments": moments_payload,
    })
    payload_version = payload["header"]["version"]
    exists = moments_index_json_path.exists()
    existing_version = extract_existing_header_scalar(moments_index_json_path, "version") if exists else None
    if (existing_version is not None) and (existing_version == payload_version) and (not args.force):
        print("Moments index JSON done. Wrote: 0. Skipped: 1.")
    else:
        if args.write:
            moments_index_json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Moments index JSON done. Wrote: 1. Skipped: 0. Path: {display_path(moments_index_json_path)}")
        else:
            print(
                "Moments index JSON done. Would write: 1. Skipped: 0. "
                f"Path: {display_path(moments_index_json_path)} (overwrite={exists})"
            )

    if args.write:
        validate_source_records_for_writeback()
        synced_paths = write_source_record_payloads(json_source_dir, source_records)
        print("Catalogue source JSON write-back done.")
        for synced_path in synced_paths:
            print(f"  - {display_path(synced_path)}")

    log_event(
        "generate_complete",
        {
            "write": bool(args.write),
            "force": bool(args.force),
            "refresh_published": bool(args.refresh_published),
            "source": "json",
        },
    )

if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        log_event("generate_exit", {"status": "system_exit", "code": code})
        raise
    except Exception as exc:  # noqa: BLE001
        log_event("generate_exit", {"status": "error", "error": str(exc)})
        raise
