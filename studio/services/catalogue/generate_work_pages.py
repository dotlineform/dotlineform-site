#!/usr/bin/env python3
"""
Generate public catalogue JSON artifacts.

This repo stores public catalogue runtime metadata in generated JSON artifacts.

Series index JSON is written to site/assets/data/series_index.json.
Exact Work JSON files, including nested Work Details, are written to site/assets/works/index/<work_id>.json.
Recent publications JSON is written to site/assets/data/recent_index.json.

- Works: base work metadata (1 row per work)
- Series: series master data (1 row per series_id)
- WorkDetails: additional detail images associated with a work

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
- --series-ids / --series-ids-file: limit series JSON scope
- --projects-base-dir: base path used for work/work_details dimension lookups

Path variables used by the script:
- projects_base_dir = configured external workspace containing the logical Work-media source roots

"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import json

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

from docs_catalogue_document_urls import load_public_catalogue_documents  # noqa: E402

from catalogue import catalogue_cleanup
from catalogue import catalogue_generation_indexes as indexes
from catalogue import catalogue_generation_recent as recent
from catalogue import catalogue_generation_records as records
from catalogue import catalogue_generation_source_updates as source_updates
from tags import tag_source_paths
from catalogue import catalogue_generation_writes as writes
from catalogue.catalogue_generation_common import (
    coerce_int,
    coerce_string,
    compact_json_object,
    is_empty,
    normalize_status,
    normalize_text,
    slug_id,
    parse_date,
)

from display_paths import format_display_path

from script_logging import append_script_log

from catalogue_work_media_sources import resolve_work_media_source_root

from pipeline_config import (
    env_var_name,
    env_var_value,
    load_pipeline_config,
)


from catalogue import catalogue_public_paths as public_paths

from catalogue.catalogue_source import (
    DEFAULT_SOURCE_DIR as DEFAULT_CATALOGUE_SOURCE_DIR,
    ordered_work_detail_sections,
    records_from_json_source,
    validate_source_records,
    write_source_record_payloads,
)

from catalogue.series_ids import normalize_series_id

PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")


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


def log_event(event: str, details: Optional[Dict[str, Any]] = None) -> None:
    try:
        append_script_log(Path(__file__), event=event, details=details or {})
    except Exception:
        # Logging failures must not block generation.
        pass


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
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    return writes.extract_header_scalar_from_json_text(text, key)


def write_index_json_payload(
    *,
    label: str,
    path: Path,
    payload: Dict[str, Any],
    payload_version: str,
    write: bool,
    force: bool,
    display_path: Callable[[Path | str], str],
) -> bool:
    exists = path.exists()
    existing_version = extract_existing_header_scalar(path, "version") if exists else None
    decision = writes.decide_json_payload_write(
        path_exists=exists,
        existing_version=existing_version,
        payload_version=payload_version,
        force=force,
    )
    if not decision.should_write:
        print(f"{label} done. Wrote: 0. Skipped: 1.")
        return False

    if write:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{label} done. Wrote: 1. Skipped: 0. Path: {display_path(path)}")
    else:
        print(f"{label} done. Would write: 1. Skipped: 0. Path: {display_path(path)} (overwrite={exists})")
    return True


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
            "tag_assignments_version": "tag_assignments_v2",
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
        payload["tag_assignments_version"] = "tag_assignments_v2"
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


GENERATE_ARTIFACT_ORDER = (
    "work-json",
    "series-json",
    "series-index-json",
    "recent-index-json",
)


def parse_selected_artifacts(values: List[str]) -> Optional[set[str]]:
    if not values:
        return None
    requested: set[str] = set()
    for raw in values:
        for part in str(raw).split(","):
            item = part.strip().lower()
            if item:
                requested.add(item)
    invalid = sorted(item for item in requested if item not in GENERATE_ARTIFACT_ORDER)
    if invalid:
        raise ValueError(
            "Invalid --only value(s): "
            + ", ".join(invalid)
            + ". Allowed: "
            + ", ".join(GENERATE_ARTIFACT_ORDER)
        )
    return requested


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
    ap.add_argument("--series-json-dir", default=public_paths.SERIES_JSON_DIR.as_posix(), help="Output folder for generated per-series JSON files")
    ap.add_argument("--series-index-json-path", default=public_paths.SERIES_INDEX_JSON_PATH.as_posix(), help="Output path for generated series index JSON")
    ap.add_argument("--works-json-dir", default=public_paths.WORKS_JSON_DIR.as_posix(), help="Output folder for generated exact Work JSON files, including nested Work Details")
    ap.add_argument("--recent-index-json-path", default=public_paths.RECENT_INDEX_JSON_PATH.as_posix(), help="Output path for generated recent publications index JSON")
    ap.add_argument(
        "--projects-base-dir",
        default=env_var_value(PIPELINE_CONFIG, "projects_base_dir"),
        help="Base folder containing the configured Work-media source roots",
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
        "--skip-source-dimension-refresh",
        action="store_true",
        help=argparse.SUPPRESS,
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
        help="Comma-separated series_ids to process for Series JSON/index generation.",
    )
    ap.add_argument(
        "--series-ids-file",
        default="",
        help="Path to series_ids file (one id per line). If set, only these series are processed.",
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help=(
            "Limit run to selected artifacts. Repeat flag and/or pass comma-separated values. "
            "Allowed: work-json,series-json,series-index-json,recent-index-json. "
            "List index JSON artifacts are always rebuilt on every run."
        ),
    )
    args = ap.parse_args()

    if not args.internal_json_source_run:
        print(
            "Unsupported direct entrypoint: studio/services/catalogue/generate_work_pages.py is an internal JSON build engine.\n"
            "Use `./studio/services/catalogue/catalogue_json_build.py --work-id <work_id> [--write]` for scoped runtime rebuilds.\n"
            "Direct generation through this script is disabled."
        )
        return
    try:
        selected_artifacts = parse_selected_artifacts(args.only)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    repo_root = REPO_ROOT
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

    def artifact_enabled(name: str) -> bool:
        if selected_artifacts is None:
            return True
        return name in selected_artifacts

    run_work_json = artifact_enabled("work-json")
    run_series_json = artifact_enabled("series-json")

    needs_projects_base = run_work_json or run_series_json
    if needs_projects_base and normalize_text(args.projects_base_dir) == "":
        raise SystemExit(
            f"Missing projects base directory. Add {PROJECTS_BASE_DIR_ENV_NAME} "
            "to .env.local or pass --projects-base-dir."
        )
    catalogue_documents: Dict[str, Dict[str, List[Dict[str, str]]]] = {
        "work": {},
        "series": {},
    }
    if run_work_json or run_series_json:
        try:
            catalogue_documents = load_public_catalogue_documents(repo_root)
        except (OSError, ValueError) as exc:
            raise SystemExit(
                f"Public Catalogue document URL projection failed: {exc}"
            ) from exc
    series_json_dir = Path(args.series_json_dir).expanduser()
    series_json_dir.mkdir(parents=True, exist_ok=True)

    tag_assignments_path = tag_source_paths.TAG_ASSIGNMENTS_REL_PATH.expanduser()
    tag_assignments_path.parent.mkdir(parents=True, exist_ok=True)
    series_index_json_path = Path(args.series_index_json_path).expanduser()
    series_index_json_path.parent.mkdir(parents=True, exist_ok=True)
    works_json_dir = Path(args.works_json_dir).expanduser()
    works_json_dir.mkdir(parents=True, exist_ok=True)
    recent_index_json_path = Path(args.recent_index_json_path).expanduser()
    recent_index_json_path.parent.mkdir(parents=True, exist_ok=True)
    projects_base_dir = Path(args.projects_base_dir).expanduser() if normalize_text(args.projects_base_dir) != "" else Path(".")

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

    run_work_selection_scope = run_work_json
    run_work_dimension_refresh = run_work_json and not args.skip_source_dimension_refresh

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

    # If caller scopes by series but does not provide an explicit work filter:
    # - when work artifacts are explicitly selected via --only, derive selected work_ids from those series
    # - otherwise skip Work JSON processing by default
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
    source_validation_errors = validate_source_records(source_records)
    if source_validation_errors:
        raise SystemExit("JSON source validation failed: " + "; ".join(source_validation_errors[:20]))

    work_dimensions_updated = 0
    work_project_folder_missing_warned = False
    work_media_source_errors_warned: set[str] = set()
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

            try:
                source_root = resolve_work_media_source_root(
                    PIPELINE_CONFIG,
                    work_record.get("media_source_id"),
                    environ={PROJECTS_BASE_DIR_ENV_NAME: str(projects_base_dir)},
                    require_exists=True,
                )
                source_path_plan = source_updates.plan_work_image_source_path(
                    work_id=wid,
                    project_filename=project_filename,
                    project_folder=work_project_folder_by_id.get(wid),
                    project_subfolder=work_project_subfolder_by_id.get(wid),
                    source_root=source_root,
                    has_project_folder_column=has_project_folder_col,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                warning = str(exc)
                if warning not in work_media_source_errors_warned:
                    print(f"Warning: Work media source is unavailable: {warning}")
                    work_media_source_errors_warned.add(warning)
                source_path_plan = source_updates.SourceImagePathPlan(source_path=None)
            if source_path_plan.warning is not None and not work_project_folder_missing_warned:
                if source_path_plan.warning.code == source_updates.NO_PROJECT_FOLDER_COLUMN:
                    print("Warning: work source records have no project_folder values; cannot persist work image dimensions.")
                else:
                    print("Warning: missing Works.project_folder for one or more works; cannot persist those image dimensions.")
                work_project_folder_missing_warned = True

            src_path = source_path_plan.source_path
            if src_path is not None:
                src_w, src_h = read_image_dims_px(src_path)
                if src_w is not None and src_h is not None:
                    dimension_plan = source_updates.plan_dimension_update(
                        record_kind=source_updates.WORK_RECORD,
                        record_id=wid,
                        current_width_px=width_px,
                        current_height_px=height_px,
                        source_width_px=src_w,
                        source_height_px=src_h,
                    )
                    width_px = dimension_plan.width_px
                    height_px = dimension_plan.height_px
                    if args.write and dimension_plan.updates:
                        update_source_work_record(wid, **dimension_plan.updates)
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

    work_publish_transitions: List[Dict[str, Any]] = []
    if args.write and work_dimensions_updated > 0:
        print(f"Updated work width_px/height_px for {work_dimensions_updated} row(s).")

    # Determine series scope for this run:
    # - If caller explicitly scoped series via --series-ids, honor that.
    # - If caller scoped only works (--work-ids/--work-ids-file), skip Series JSON by default.
    series_json_selected_ids = selected_series_ids
    if explicit_work_filter and selected_series_ids is None:
        if selected_artifacts is None:
            run_series_json = False

    # ----------------------------
    # Series JSON generation
    # ----------------------------
    # Series source required fields:
    # - series_id
    # - title
    # Optional columns:
    # - year_display (preferred display value)
    # - year (numeric; also fallback for display when year_display column absent)

    series_publish_transitions: List[Dict[str, Any]] = []

    if not source_records.series:
        print("No Series JSON to generate (series source records empty).")
    else:
        def is_actionable_series_status(status_value: str) -> bool:
            if status_value == "published" and refresh_published:
                return True
            return False

        series_json_written = 0
        series_json_skipped = 0
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
            if series_json_selected_ids is not None and sid not in series_json_selected_ids:
                continue
            status = normalize_status(series_record.get("status"))
            if is_actionable_series_status(status):
                s_total += 1
        s_processed = 0

        if run_series_json:
            for series_record in source_records.series.values():
                sid_raw = series_record.get("series_id")
                if is_empty(sid_raw):
                    continue
                series_id = normalize_series_id(sid_raw)
                if series_json_selected_ids is not None and series_id not in series_json_selected_ids:
                    continue

                status = normalize_status(series_record.get("status"))
                if not is_actionable_series_status(status):
                    continue

                s_processed += 1
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

                member_works = indexes.build_series_member_work_records(
                    context=series_work_context,
                    series_id=series_id,
                )
                ordered_work_ids = [str(work.get("work_id") or "") for work in member_works]
                try:
                    indexes.require_series_primary_work_id(
                        series_id,
                        series_record,
                        ordered_work_ids=ordered_work_ids,
                    )
                except indexes.CatalogueGenerationIndexError as exc:
                    raise SystemExit(str(exc)) from exc
                published_date = parse_date(series_record.get("published_date"))
                series_output_record = compact_json_object({
                    "series_id": series_id,
                    "status": status,
                    "published_date": published_date,
                    "title": series_title,
                    "sort_fields": ",".join(series_sort_fields_by_series_id.get(series_id, ["work_id"])),
                    "series_type": coerce_string(series_record.get("series_type")),
                    "year": year,
                    "year_display": year_display,
                    "project_folders": series_project_folders_by_id.get(series_id, []),
                })

                public_series_record = records.build_series_json_record(
                    series_output_record,
                    documents=catalogue_documents["series"].get(series_id, []),
                )
                payload = records.build_series_json_payload(
                    series_id=series_id,
                    series_record=public_series_record,
                    member_works=member_works,
                    generated_at_utc=utc_timestamp_now(),
                )
                payload_version = payload["header"]["version"]
                out_json_path = series_json_dir / f"{series_id}.json"
                out_exists = out_json_path.exists()
                existing_payload_version = extract_existing_header_scalar(out_json_path, "version") if out_exists else None
                json_decision = writes.decide_json_payload_write(
                    path_exists=out_exists,
                    existing_version=existing_payload_version,
                    payload_version=payload_version,
                    force=args.force,
                )
                if not json_decision.should_write:
                    series_json_skipped += 1
                else:
                    if args.write:
                        out_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print(f"[Series JSON {s_processed}/{s_total}] WRITE: {display_path(out_json_path)}")
                        series_json_written += 1
                    else:
                        print(f"[Series JSON {s_processed}/{s_total}] DRY-RUN: would write {display_path(out_json_path)} (overwrite={out_exists})")
                        series_json_written += 1

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
            if selected_artifacts is not None and not artifact_enabled("series-json"):
                print("Series JSON skipped: not selected by --only.")
            else:
                print("Series JSON skipped: --work-ids scope active (use --series-ids to include Series JSON rebuild).")
            print("Tag assignments sync skipped: follows series-json selection.")

        if run_series_json:
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

        print(
            f"Series JSON done. {'Would write' if not args.write else 'Wrote'}: "
            f"{series_json_written}. Skipped: {series_json_skipped}."
        )

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
    write_index_json_payload(
        label="Series index JSON",
        path=series_index_json_path,
        payload=series_index_payload,
        payload_version=series_version,
        write=args.write,
        force=args.force,
        display_path=display_path,
    )

    # ----------------------------
    # Work JSON generation, including nested Work Details
    # ----------------------------
    if not source_records.work_details:
        if run_work_json:
            print("No Work Detail records found; Work JSON has no detail sections.")
        else:
            print("Work JSON skipped: not selected by --only.")
    else:
        projects_base_dir = Path(args.projects_base_dir).expanduser()

        # Build known works from source records to validate foreign-key references.
        known_work_ids: set[str] = set()
        for work_record in source_records.works.values():
            wid_raw = work_record.get("work_id")
            if is_empty(wid_raw):
                continue
            known_work_ids.add(slug_id(wid_raw))

        if run_work_json:
            # Build per-work JSON from Works rows (work-driven).
            # Detail sections are sourced from currently published detail rows only.
            encountered_work_ids: List[str] = []
            encountered_work_id_set: set[str] = set()
            detail_records_by_work: Dict[str, Dict[str, Dict[str, Any]]] = {}

            for work_record in source_records.works.values():
                wid_raw = work_record.get("work_id")
                if is_empty(wid_raw):
                    continue
                wid = slug_id(wid_raw)
                if selected_ids is not None and wid not in selected_ids:
                    continue
                status = normalize_status(work_record.get("status"))
                if status != "published":
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

                detail_status = normalize_status(detail_source_record.get("status"))
                if detail_status and detail_status != "published":
                    continue

                did = slug_id(did_raw, width=3)
                detail_record = records.build_canonical_detail_record(
                    wid=wid,
                    did=did,
                    title=coerce_string(detail_source_record.get("title")),
                    width_px=coerce_int(detail_source_record.get("width_px")),
                    height_px=coerce_int(detail_source_record.get("height_px")),
                    media_version=coerce_int(detail_source_record.get("media_version")),
                )
                detail_records_by_work.setdefault(wid, {})[detail_uid] = detail_record

            wj_written = 0
            wj_skipped = 0
            wj_total = len(encountered_work_ids)
            wj_processed = 0
            generated_at_utc = utc_timestamp_now()

            for wid in encountered_work_ids:
                wj_processed += 1
                prefix_wj = f"[Work JSON {wj_processed}/{wj_total}] "

                source_sections = []
                detail_payloads_by_uid = detail_records_by_work.get(wid, {})
                for section in ordered_work_detail_sections(source_records, wid):
                    details = [
                        detail_payloads_by_uid[detail.get("detail_uid")]
                        for detail in section.get("details", [])
                        if isinstance(detail, dict) and detail.get("detail_uid") in detail_payloads_by_uid
                    ]
                    if not details:
                        continue
                    section_payload = dict(section)
                    section_payload["details"] = details
                    source_sections.append(section_payload)
                sections = records.build_sections_from_detail_sections(source_sections)
                details_total = sum(len(s.get("details", [])) for s in sections)
                work_record = records.build_work_json_record(
                    canonical_work_record_by_id.get(wid, {"work_id": wid}),
                    documents=catalogue_documents["work"].get(wid, []),
                )
                payload = records.build_work_json_payload(
                    work_id=wid,
                    work_record=work_record,
                    sections=sections,
                    generated_at_utc=generated_at_utc,
                    count=details_total,
                )
                out_json_path = works_json_dir / f"{wid}.json"
                exists = out_json_path.exists()
                existing_version = extract_existing_header_scalar(out_json_path, "version") if exists else None
                payload_version = payload["header"]["version"]
                json_decision = writes.decide_json_payload_write(
                    path_exists=exists,
                    existing_version=existing_version,
                    payload_version=payload_version,
                    force=args.force,
                )

                if not json_decision.should_write:
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
            print("Work JSON skipped: not selected by --only.")

    published_work_ids = {
        slug_id(work_record.get("work_id"))
        for work_record in source_records.works.values()
        if not is_empty(work_record.get("work_id"))
        and normalize_status(work_record.get("status")) == "published"
    }
    published_series_ids = {
        normalize_series_id(series_record.get("series_id"))
        for series_record in source_records.series.values()
        if not is_empty(series_record.get("series_id"))
        and normalize_status(series_record.get("status")) == "published"
    }
    stale_record_paths: list[Path] = []
    if run_work_json:
        stale_record_paths.extend(
            catalogue_cleanup.collect_stale_work_record_artifacts(works_json_dir, published_work_ids)
        )
    if run_series_json:
        stale_record_paths.extend(
            catalogue_cleanup.collect_stale_series_record_artifacts(series_json_dir, published_series_ids)
        )
    if stale_record_paths:
        if args.write:
            deleted_count = catalogue_cleanup.delete_existing_files(stale_record_paths)
            print(f"Stale public record cleanup: deleted {deleted_count} JSON artifact(s).")
        else:
            print(f"Stale public record cleanup: would delete {len(stale_record_paths)} JSON artifact(s).")
        for stale_path in stale_record_paths:
            print(f"  - {display_path(stale_path)}")
    elif run_work_json or run_series_json:
        print("Stale public record cleanup: no stale JSON artifacts.")

    published_work_ids = {
        work_id
        for work_id, status in work_status_by_id.items()
        if status == "published" and work_id in canonical_work_record_by_id
    }
    recent_entries = recent.build_recent_publication_entries(
        existing_entries=load_recent_entries(recent_index_json_path),
        series_publish_transitions=series_publish_transitions,
        work_publish_transitions=work_publish_transitions,
        series_payload=series_payload,
        series_work_ids_by_id=indexes.ordered_published_work_ids_by_series(series_work_context),
        published_work_ids=published_work_ids,
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
    recent_payload_version = recent_index_payload["header"]["version"]
    write_index_json_payload(
        label="Recent index JSON",
        path=recent_index_json_path,
        payload=recent_index_payload,
        payload_version=recent_payload_version,
        write=args.write,
        force=args.force,
        display_path=display_path,
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
