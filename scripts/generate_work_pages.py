#!/usr/bin/env python3
"""
Generate Jekyll work/moment pages from an Excel workbook.

This repo stores works as a Jekyll collection in `_works/`. The generator writes one Markdown
file per work (e.g. `_works/00286.md`) with YAML front matter populated from these worksheets.
It can also emit a parallel print collection (e.g. `_works_print/00286.md`) for PDF rendering.

Series JSON index files are written to assets/series/index/<series_id>.json (one per series_id in the Series sheet).
Work-details JSON index files are written to assets/works/index/<work_id>.json (one per work_id with published details).

- Works: base work metadata (1 row per work)
- Series: series master data (1 row per series_id)
- WorkDetails: additional detail images associated with a work
- Moments: standalone moment entries

YAML typing rules enforced by this script (so Excel cells do NOT need quoting):
- Numbers are emitted unquoted for: year, height_cm, width_cm, depth_cm
- Booleans are emitted unquoted for: has_primary_2400
- Everything else is emitted as a quoted string (including fields like year_display)
- Empty cells become YAML null

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
Usage:
    python3 scripts/generate_work_pages.py --work-ids 00001,00002 --write
    python3 scripts/generate_work_pages.py --work-ids-file tmp/work_ids.txt --write
    python3 scripts/generate_work_pages.py --series-ids curve-poems,dots --write
    python3 scripts/generate_work_pages.py --moment-ids blue-sky,compiled --write

Common flags:
- --write: persist generated files + workbook status/date updates
- --force: regenerate even when checksum/hash matches existing output
- --work-ids / --work-ids-file: limit work/work_details generation scope
- --series-ids / --series-ids-file: limit series page/JSON scope
- --moment-ids / --moment-ids-file: limit moments generation scope
- --moments-sheet: worksheet name for moments (default: Moments)
- --moments-output-dir / --moments-prose-dir: moment page/prose destinations
- --projects-base-dir: base path used for dimension lookups in WorkDetails/Moments

Path variables used by the script:
- projects_root = [projects-base-dir]/projects (work + work_details source image lookup)
- moments_root = [projects-base-dir]/moments (moment source image lookup)

"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import hashlib
import json

import openpyxl


# ----------------------------
# Helpers (ID/date/YAML parsing)
# ----------------------------
# These functions exist to normalise common Excel quirks (e.g. numeric IDs like 361.0)
# and to keep YAML output safe/consistent.
def slug_id(raw: Any, width: int = 5) -> str:
    if raw is None:
        raise ValueError("Missing id")
    s = normalize_text(raw)
    # Handle numeric IDs like 361.0 from Excel
    s = re.sub(r"\.0$", "", s)
    # NOTE: This strips ALL non-digits. If your IDs ever include prefixes/suffixes, change this logic.
    s = re.sub(r"\D", "", s)  # keep digits only
    if not s:
        raise ValueError(f"Invalid id value: {raw!r}")
    return s.zfill(width)


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


def parse_date(raw: Any) -> Optional[str]:
    if raw is None or str(raw).strip() == "":
        return None
    if isinstance(raw, dt.datetime):
        return raw.date().isoformat()
    if isinstance(raw, dt.date):
        return raw.isoformat()
    s = normalize_text(raw)
    # NOTE: Prefer real Excel date cells or ISO strings in the workbook; anything else may pass through unchanged.
    # Accept YYYY-M-D and normalise to YYYY-MM-DD if possible
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, mo, d = map(int, m.groups())
        return dt.date(y, mo, d).isoformat()
    # Last resort: leave as-is (but you should fix upstream)
    return s


def parse_list(raw: Any, sep: str = ",") -> List[str]:
    if raw is None:
        return []
    s = normalize_text(raw)
    if not s:
        return []
    return [item.strip() for item in s.split(sep) if item.strip()]


def normalize_status(value: Any) -> str:
    if value is None:
        return ""
    return normalize_text(value).lower()


def normalize_text(value: Any) -> str:
    """Normalize Excel text by trimming and stripping a leading apostrophe prefix."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def yaml_quote(s: str) -> str:
    """Quote a string safely for YAML."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


NUMERIC_KEYS = {"year", "height_cm", "width_cm", "depth_cm", "width_px", "height_px"}
BOOLEAN_KEYS = {"has_primary_2400"}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def coerce_numeric(value: Any) -> Optional[float]:
    """Best-effort numeric coercion for dimension fields; returns None if not parseable."""
    if is_empty(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def coerce_int(value: Any) -> Optional[int]:
    """Best-effort integer coercion for year; returns None if not parseable."""
    if is_empty(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    try:
        return int(str(value).strip())
    except Exception:
        return None


def coerce_string(value: Any) -> Optional[str]:
    """Coerce any non-empty value to a trimmed string (for quoted YAML output)."""
    if is_empty(value):
        return None
    s = normalize_text(value)
    return s if s != "" else None


def coerce_presence_bool(value: Any) -> bool:
    """Map Excel presence to bool: empty -> False, non-empty -> True."""
    return not is_empty(value)


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


# ----------------------------
# Canonical schema (Works sheet)
# ----------------------------
# Define the Works->front matter mapping once so adding a new field is a one-line change.
# Each entry is: (front_matter_key, excel_column_name, coercer)
# Coercers should return the Python type we want before YAML emission:
# - strings (quoted), ints/floats (unquoted for configured numeric keys), or None (-> null)
WORKS_SCHEMA: List[tuple[str, str, Any]] = [
    ("artist", "artist", coerce_string),
    ("title", "title", coerce_string),
    ("year", "year", coerce_int),
    ("year_display", "year_display", coerce_string),
    ("series_id", "series_id", coerce_string),
    ("medium_type", "medium_type", coerce_string),
    ("medium_caption", "medium_caption", coerce_string),
    ("duration", "duration", coerce_string),
    ("vimeo_url", "vimeo_url", coerce_string),
    ("youtube_url", "youtube_url", coerce_string),
    ("bandcamp_url", "bandcamp_url", coerce_string),
    ("height_cm", "height_cm", coerce_numeric),
    ("width_cm", "width_cm", coerce_numeric),
    ("depth_cm", "depth_cm", coerce_numeric),
    ("download", "download", coerce_string),
    ("has_primary_2400", "has_primary_2400", coerce_presence_bool),
    # tags handled separately (csv list)
    # checksum is always computed, not sourced from Excel
]


def build_works_front_matter(works_row: tuple, works_hi: Dict[str, int]) -> Dict[str, Any]:
    """Build the scalar portion of Works front matter (excluding work_id, tags, images, attachments)."""
    fm: Dict[str, Any] = {}
    for fm_key, col_name, coercer in WORKS_SCHEMA:
        raw = works_row[works_hi[col_name]] if col_name in works_hi else None
        fm[fm_key] = coercer(raw)
    return fm


# ----------------------------
# Checksum helpers
# ----------------------------

def compute_work_checksum(front_matter: Dict[str, Any]) -> str:
    """Compute a deterministic checksum for a work from its front matter (excluding checksum itself)."""
    payload = dict(front_matter)
    payload.pop("checksum", None)

    # Canonical JSON for hashing (sorted keys ensures deterministic output)
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    h = hashlib.blake2b(canonical, digest_size=16)
    return h.hexdigest()


def extract_existing_checksum(path: Path) -> Optional[str]:
    """Extract `checksum` from the YAML front matter of an existing work page."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    # Only inspect the first YAML front matter block
    if not text.startswith("---"):
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    fm_text = parts[1]
    for line in fm_text.splitlines():
        if not line.startswith("checksum:"):
            continue
        _, raw = line.split(":", 1)
        raw = raw.strip()
        if raw == "null" or raw == "":
            return None
        if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
            return raw[1:-1]
        return raw

    return None

# ----------------------------
# Series JSON helpers
# ----------------------------

def compute_series_hash(series_id: str, work_ids: List[str]) -> str:
    """Compute deterministic hash for a series JSON payload."""
    payload = {"series_id": series_id, "work_ids": list(work_ids)}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.blake2b(canonical, digest_size=16).hexdigest()


def compute_work_details_hash(work_id: str, sections: List[Dict[str, Any]]) -> str:
    """Compute deterministic hash for a work-details JSON payload."""
    payload = {"work_id": work_id, "sections": sections}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.blake2b(canonical, digest_size=16).hexdigest()


def extract_existing_series_hash(path: Path) -> Optional[str]:
    """Extract header.hash from an existing series JSON file."""
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    header = obj.get("header") if isinstance(obj, dict) else None
    if not isinstance(header, dict):
        return None
    hv = header.get("hash")
    if hv is None:
        return None
    s = str(hv).strip()
    return s or None


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

# ----------------------------
# Main program
# ----------------------------
# High-level flow:
# 1) Parse CLI args (column mapping + output options)
# 2) Load workbook + sheets
# 3) Build header->index maps from row 1 of each sheet
# 4) Iterate Works rows -> build front matter + body -> write one file per work
def main() -> None:
    # CLI arguments define how we map Excel columns to front matter fields, and where output files go.
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", nargs="?", default="data/works.xlsx", help="Path to Excel workbook (.xlsx)")

    # Worksheet names
    ap.add_argument("--works-sheet", default="Works", help="Worksheet name for base work metadata")
    ap.add_argument("--series-sheet", default="Series", help="Worksheet name for series master data")
    ap.add_argument("--work-details-sheet", default="WorkDetails", help="Worksheet name for work detail metadata")
    ap.add_argument("--moments-sheet", default="Moments", help="Worksheet name for moment metadata")

    # Output
    ap.add_argument("--output-dir", default="_works", help="Output folder for generated work pages")
    ap.add_argument("--print-output-dir", default="_works_print", help="Output folder for generated print work pages")
    ap.add_argument("--work-prose-dir", default="_includes/work_prose", help="Folder for optional manual work prose includes")
    ap.add_argument("--series-output-dir", default="_series", help="Output folder for generated series pages")
    ap.add_argument("--series-prose-dir", default="_includes/series_prose", help="Folder for manual series prose includes")
    ap.add_argument("--series-json-dir", default="assets/series/index", help="Output folder for generated per-series JSON index files")
    ap.add_argument("--work-details-output-dir", default="_work_details", help="Output folder for generated work detail pages")
    ap.add_argument("--works-json-dir", default="assets/works/index", help="Output folder for generated per-work detail JSON index files")
    ap.add_argument("--works-files-dir", default="assets/works/files", help="Output folder for copied work download files")
    ap.add_argument("--moments-output-dir", default="_moments", help="Output folder for generated moment pages")
    ap.add_argument("--moments-prose-dir", default="_includes/moments_prose", help="Folder for manual moment prose includes")
    ap.add_argument(
        "--projects-base-dir",
        default="/Users/dlf/Library/CloudStorage/OneDrive-Personal/dotlineform",
        help="Base folder containing the projects directory used to resolve WorkDetails source images",
    )

    # Write controls
    ap.add_argument("--write", action="store_true", help="Actually write files (otherwise dry-run)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    ap.add_argument(
        "--work-ids",
        default="",
        help="Comma-separated work_ids to process (e.g. 00001,00002). If set, only these IDs are processed.",
    )
    ap.add_argument(
        "--work-ids-file",
        default="",
        help="Path to work_ids file (one id per line). If set, only these IDs are processed.",
    )
    ap.add_argument(
        "--series-ids",
        default="",
        help="Comma-separated series_ids to process for series page/JSON generation.",
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
    args = ap.parse_args()

    # Resolve the workbook path and fail fast if it is missing.
    xlsx_path = Path(args.xlsx).expanduser()
    if not xlsx_path.exists():
        raise SystemExit(f"Workbook not found: {xlsx_path}")

    # `data_only=True` reads the last-calculated values of formula cells.
    # If your sheet relies on formulas that haven't been calculated/saved, values may be None.
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)

    if args.works_sheet not in wb.sheetnames:
        raise SystemExit(f"Sheet not found in workbook: {args.works_sheet}")
    works_ws = wb[args.works_sheet]

    def read_sheet_rows(sheet_name: str) -> List[tuple]:
        if sheet_name not in wb.sheetnames:
            raise SystemExit(f"Sheet not found in workbook: {sheet_name}")
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        return rows

    def build_header_index(rows: List[tuple]) -> Dict[str, int]:
        if not rows:
            return {}
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        hi: Dict[str, int] = {}
        for i, h in enumerate(headers):
            if not h:
                continue
            # Preserve original header and also store a lowercase alias for case-insensitive lookups.
            hi[h] = i
            hi[h.lower()] = i
        return hi

    def cell(row: tuple, header_index: Dict[str, int], col_name: str) -> Any:
        i = header_index.get(col_name)
        return None if i is None or i >= len(row) else row[i]

    def first_present_col(header_index: Dict[str, int], names: List[str]) -> Optional[str]:
        for n in names:
            if n in header_index:
                return n
        return None

    # Output directory:
    # - Use `works` for a normal pages folder.
    # - Use `_works` if you're using a Jekyll collection.
    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    print_out_dir = Path(args.print_output_dir).expanduser()
    print_out_dir.mkdir(parents=True, exist_ok=True)

    work_prose_dir = Path(args.work_prose_dir).expanduser()
    work_prose_dir.mkdir(parents=True, exist_ok=True)

    series_out_dir = Path(args.series_output_dir).expanduser()
    series_out_dir.mkdir(parents=True, exist_ok=True)

    series_prose_dir = Path(args.series_prose_dir).expanduser()
    series_prose_dir.mkdir(parents=True, exist_ok=True)

    series_json_dir = Path(args.series_json_dir).expanduser()
    series_json_dir.mkdir(parents=True, exist_ok=True)
    work_details_out_dir = Path(args.work_details_output_dir).expanduser()
    work_details_out_dir.mkdir(parents=True, exist_ok=True)
    works_json_dir = Path(args.works_json_dir).expanduser()
    works_json_dir.mkdir(parents=True, exist_ok=True)
    works_files_dir = Path(args.works_files_dir).expanduser()
    works_files_dir.mkdir(parents=True, exist_ok=True)
    moments_out_dir = Path(args.moments_output_dir).expanduser()
    moments_out_dir.mkdir(parents=True, exist_ok=True)
    moments_prose_dir = Path(args.moments_prose_dir).expanduser()
    moments_prose_dir.mkdir(parents=True, exist_ok=True)
    projects_base_dir = Path(args.projects_base_dir).expanduser()
    projects_root = projects_base_dir / "projects"

    # Load all worksheets up-front.
    works_rows = read_sheet_rows(args.works_sheet)
    series_rows = read_sheet_rows(args.series_sheet)
    work_details_rows = read_sheet_rows(args.work_details_sheet) if args.work_details_sheet in wb.sheetnames else []
    moments_rows = read_sheet_rows(args.moments_sheet)
    series_ws = wb[args.series_sheet]
    work_details_ws = wb[args.work_details_sheet] if args.work_details_sheet in wb.sheetnames else None
    moments_ws = wb[args.moments_sheet]

    if not works_rows:
        raise SystemExit(f"Works sheet '{args.works_sheet}' is empty")

    works_hi = build_header_index(works_rows)
    series_hi = build_header_index(series_rows) if series_rows else {}
    work_details_hi = build_header_index(work_details_rows) if work_details_rows else {}
    moments_hi = build_header_index(moments_rows) if moments_rows else {}

    if "status" not in works_hi:
        raise SystemExit("Works sheet missing required column: status")
    if work_details_rows and "status" not in work_details_hi:
        raise SystemExit("WorkDetails sheet missing required column: status")
    if moments_rows and "status" not in moments_hi:
        raise SystemExit("Moments sheet missing required column: status")

    # Pre-index series titles by series_id
    series_title_by_id: Dict[str, str] = {}
    for r in series_rows[1:] if len(series_rows) > 1 else []:
        sid_raw = cell(r, series_hi, "series_id")
        if is_empty(sid_raw):
            continue
        sid = str(sid_raw).strip()
        title_raw = cell(r, series_hi, "title")
        title = coerce_string(title_raw)
        if title is None:
            continue
        series_title_by_id[sid] = title

    # Pre-index project folder by work_id (for WorkDetails source image lookup).
    work_project_folder_by_id: Dict[str, str] = {}
    has_project_folder_col = "project_folder" in works_hi
    if has_project_folder_col:
        for wr in works_rows[1:]:
            wid_raw = cell(wr, works_hi, "work_id")
            pf_raw = cell(wr, works_hi, "project_folder")
            if is_empty(wid_raw) or is_empty(pf_raw):
                continue
            work_project_folder_by_id[slug_id(wid_raw)] = normalize_text(pf_raw)

    written = 0
    skipped = 0
    print_written = 0
    print_skipped = 0
    downloads_copied = 0
    downloads_missing = 0
    def is_actionable_status(status_value: str) -> bool:
        if status_value == "draft":
            return True
        if status_value == "published" and args.force:
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
        selected_ids = {slug_id(w.strip()) for w in args.work_ids.split(",") if w.strip()}

    selected_series_ids = None
    if args.series_ids_file:
        sids_path = Path(args.series_ids_file).expanduser()
        if not sids_path.exists():
            raise SystemExit(f"series_ids file not found: {sids_path}")
        selected_series_ids = {
            require_slug_safe("series_id", line.strip())
            for line in sids_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    elif args.series_ids:
        selected_series_ids = {
            require_slug_safe("series_id", sid.strip())
            for sid in args.series_ids.split(",")
            if sid.strip()
        }

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

    # If caller scopes by series but does not provide an explicit work filter,
    # skip work-page processing by default.
    if selected_series_ids is not None and not explicit_work_filter:
        selected_ids = set()
    # If caller scopes by work/series and does not provide an explicit moments filter,
    # skip moments generation by default.
    run_moments = True
    if (explicit_work_filter or selected_series_ids is not None) and not explicit_moment_filter:
        run_moments = False

    total = 0
    for r in works_rows[1:]:
        raw_work_id = cell(r, works_hi, "work_id")
        if is_empty(raw_work_id):
            continue
        wid = slug_id(raw_work_id)
        if selected_ids is not None and wid not in selected_ids:
            continue
        status = normalize_status(cell(r, works_hi, "status"))
        if is_actionable_status(status):
            total += 1

    processed = 0
    status_updated = 0
    published_date_updated = 0
    published_date_idx = works_hi.get("published_date")
    published_date_missing_warned = False
    today = dt.date.today()

    # Iterate each Works row and emit one Markdown file per work.
    for r, row_cells in zip(works_rows[1:], works_ws.iter_rows(min_row=2), strict=False):
        status = normalize_status(cell(r, works_hi, "status"))
        raw_work_id = cell(r, works_hi, "work_id")
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
        # Tags: comma-separated in Excel
        tags = parse_list(cell(r, works_hi, "tags"), sep=",")

        # Fields in stable order (matches your canonical front matter schema)
        fm: Dict[str, Any] = {"work_id": wid}
        fm.update(build_works_front_matter(r, works_hi))
        # Normalise download to a filename (basename only) for front matter/link text.
        download_rel = coerce_string(cell(r, works_hi, "download")) if "download" in works_hi else None
        if download_rel is not None:
            fm["download"] = Path(download_rel).name

        # Series title lookup (Works.series_id -> series_id; Series.series_title -> series_title)
        sid = fm.get("series_id")
        if isinstance(sid, str) and sid.strip() != "":
            fm["series_title"] = series_title_by_id.get(sid.strip())
        else:
            fm["series_title"] = None

        # Reorder for clarity: ensure series_title immediately follows series_id in YAML
        if "series_id" in fm and "series_title" in fm:
            _st = fm.get("series_title")
            fm_ordered: Dict[str, Any] = {}
            for k, v in fm.items():
                if k == "series_title":
                    continue  # will be inserted right after series_id
                fm_ordered[k] = v
                if k == "series_id":
                    fm_ordered["series_title"] = _st
            fm = fm_ordered

        fm["tags"] = tags

        # Stable series ordering: oldest first, then work_id within year.
        year_val = fm.get("year")
        if isinstance(year_val, int):
            sort_year = f"{year_val:04d}"
        else:
            sort_year = "9999"
        fm["series_sort"] = f"{sort_year}-{wid}"

        # Compute checksum from the canonical Excel-derived record and write it into front matter.
        checksum = compute_work_checksum(fm)
        fm["checksum"] = checksum

        prose_path = work_prose_dir / f"{wid}.md"
        work_body = ""
        if prose_path.exists():
            work_body = f"{{% include work_prose/{wid}.md %}}\n"

        content = build_front_matter(fm) + "\n" + work_body

        out_path = out_dir / f"{wid}.md"
        print_path = print_out_dir / f"{wid}.md"
        works_print_idx = works_hi.get("works_print")
        works_print_value = None
        if works_print_idx is not None and works_print_idx < len(r):
            works_print_value = r[works_print_idx]
        works_print = normalize_status(works_print_value) == "yes"

        def write_page(path: Path, label: str) -> bool:
            exists = path.exists()
            existing_checksum = extract_existing_checksum(path) if exists else None
            if (existing_checksum is not None) and (existing_checksum == checksum) and (not args.force):
                print(f"{prefix}SKIP ({label}; checksum match): {path}")
                return False
            if args.write:
                path.write_text(content, encoding="utf-8")
                print(f"{prefix}WRITE ({label}): {path}")
            else:
                print(f"{prefix}DRY-RUN: would write {path} (overwrite={exists})")
            return True

        if write_page(out_path, "work"):
            written += 1
            if args.write:
                status_idx = works_hi["status"]
                status_was = normalize_status(row_cells[status_idx].value)
                if status_was != "published":
                    row_cells[status_idx].value = "published"
                    status_updated += 1
                if (status_was != "published") or args.force:
                    if published_date_idx is not None:
                        row_cells[published_date_idx].value = today
                        published_date_updated += 1
                    elif not published_date_missing_warned:
                        print("Warning: Works sheet missing published_date column; skipping date updates.")
                        published_date_missing_warned = True
        else:
            skipped += 1

        if works_print:
            if write_page(print_path, "print"):
                print_written += 1
            else:
                print_skipped += 1

        if download_rel is not None:
            project_folder = work_project_folder_by_id.get(wid)
            if Path(download_rel).is_absolute():
                download_src = Path(download_rel)
            elif project_folder:
                download_src = projects_root / project_folder / download_rel
            else:
                download_src = None

            download_name = Path(download_rel).name
            download_dest = works_files_dir / f"{wid}-{download_name}"

            if download_src is None:
                print(f"{prefix}Warning: cannot resolve download source for {wid} ({download_rel})")
                downloads_missing += 1
            elif not download_src.exists():
                print(f"{prefix}Warning: missing download source: {download_src}")
                downloads_missing += 1
            else:
                if args.write:
                    download_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(download_src, download_dest)
                    print(f"{prefix}COPY download: {download_src} -> {download_dest}")
                    downloads_copied += 1
                else:
                    print(f"{prefix}DRY-RUN: would copy download {download_src} -> {download_dest}")
                    downloads_copied += 1

    if args.write and status_updated > 0:
        wb.save(xlsx_path)
        print(f"Updated status to 'published' for {status_updated} row(s).")
        if published_date_updated > 0:
            print(f"Set published_date for {published_date_updated} row(s).")

    print(
        f"\nDone. {'Would write' if not args.write else 'Wrote'}: {written} works, {print_written} print."
        f" Skipped: {skipped} works, {print_skipped} print."
    )
    print(
        f"Downloads {'to copy' if not args.write else 'copied'}: {downloads_copied}."
        f" Missing/unresolved: {downloads_missing}."
    )
    print(f"Workbook: {xlsx_path}")
    if args.write:
        print("Note: if the workbook is open in Excel, close and reopen it to see changes.")

    # Determine series scope for this run:
    # - If caller explicitly scoped series via --series-ids, honor that for both pages and JSON.
    # - If caller scoped only works (--work-ids/--work-ids-file), skip series pages by default,
    #   but still regenerate series JSON for affected series IDs so work prev/next nav stays fresh.
    run_series_pages = True
    series_page_selected_ids = selected_series_ids
    series_json_selected_ids = selected_series_ids
    if explicit_work_filter and selected_series_ids is None:
        run_series_pages = False
        affected_series_ids: set[str] = set()
        for wr in works_rows[1:]:
            wid_raw = cell(wr, works_hi, "work_id")
            if is_empty(wid_raw):
                continue
            wid = slug_id(wid_raw)
            if selected_ids is None or wid not in selected_ids:
                continue
            sid_raw = cell(wr, works_hi, "series_id")
            if is_empty(sid_raw):
                continue
            sid = normalize_text(sid_raw)
            if is_slug_safe(sid):
                affected_series_ids.add(sid)
        series_json_selected_ids = affected_series_ids

    # ----------------------------
    # Series page generation (Series)
    # ----------------------------
    # Series worksheet required columns:
    # - series_id (slug-safe)
    # - title
    # Optional columns:
    # - year_display (preferred display value)
    # - year (numeric; also fallback for display when year_display column absent)

    if not series_rows or len(series_rows) < 2:
        print("No series pages to generate (Series sheet empty).")
    else:
        def is_actionable_series_status(status_value: str) -> bool:
            if status_value == "draft":
                return True
            if status_value == "published" and args.force:
                return True
            return False

        series_written = 0
        series_skipped = 0
        series_status_updated = 0
        series_published_date_updated = 0
        series_published_date_idx = series_hi.get("published_date")
        series_published_date_missing_warned = False
        s_total = 0
        for sr in series_rows[1:]:
            sid_raw = cell(sr, series_hi, "series_id")
            if is_empty(sid_raw):
                continue
            sid = require_slug_safe("series_id", sid_raw)
            if series_page_selected_ids is not None and sid not in series_page_selected_ids:
                continue
            status = normalize_status(cell(sr, series_hi, "status"))
            if is_actionable_series_status(status):
                s_total += 1
        s_processed = 0

        if run_series_pages:
            for sr, sr_cells in zip(series_rows[1:], series_ws.iter_rows(min_row=2), strict=False):
                sid_raw = cell(sr, series_hi, "series_id")
                if is_empty(sid_raw):
                    series_skipped += 1
                    continue
                series_id = require_slug_safe("series_id", sid_raw)
                if series_page_selected_ids is not None and series_id not in series_page_selected_ids:
                    series_skipped += 1
                    continue

                status = normalize_status(cell(sr, series_hi, "status"))
                if not is_actionable_series_status(status):
                    series_skipped += 1
                    continue

                s_processed += 1
                prefix_s = f"[series {s_processed}/{s_total}] "

                title_raw = cell(sr, series_hi, "title")
                series_title = coerce_string(title_raw) or series_id

                # Numeric year (optional)
                year = coerce_int(cell(sr, series_hi, "year")) if "year" in series_hi else None

                # year_display handling:
                # - If Series sheet has a year_display column, use it (may be null).
                # - If it does NOT have year_display, fall back to numeric year rendered as text
                year_display: Optional[str]
                if "year_display" in series_hi:
                    year_display = coerce_string(cell(sr, series_hi, "year_display"))
                else:
                    # Fall back to numeric year rendered as text
                    year_display = str(year) if year is not None else None

                sfm: Dict[str, Any] = {
                    "series_id": series_id,
                    "title": series_title,
                    "year": year,
                    "year_display": year_display,
                    "layout": "series",
                }

                s_checksum = compute_work_checksum(sfm)
                sfm["checksum"] = s_checksum

                body = f"{{% include series_prose/{series_id}.md %}}\n"
                series_content = build_front_matter(sfm) + "\n" + body

                series_path = series_out_dir / f"{series_id}.md"
                existing_text = None
                if series_path.exists():
                    try:
                        existing_text = series_path.read_text(encoding="utf-8")
                    except Exception:
                        existing_text = None

                needs_write = (existing_text != series_content)
                if (not needs_write) and (not args.force):
                    print(f"{prefix_s}SKIP (no change): {series_path}")
                    series_skipped += 1
                else:
                    if args.write:
                        series_path.write_text(series_content, encoding="utf-8")
                        print(f"{prefix_s}WRITE: {series_path}")
                        series_written += 1
                        status_idx = series_hi.get("status")
                        if status_idx is not None:
                            status_was = normalize_status(sr_cells[status_idx].value)
                            if status_was != "published":
                                sr_cells[status_idx].value = "published"
                                series_status_updated += 1
                            if (status_was != "published") or args.force:
                                if series_published_date_idx is not None:
                                    sr_cells[series_published_date_idx].value = today
                                    series_published_date_updated += 1
                                elif not series_published_date_missing_warned:
                                    print("Warning: Series sheet missing published_date column; skipping date updates.")
                                    series_published_date_missing_warned = True
                    else:
                        print(f"{prefix_s}DRY-RUN: would write {series_path} (overwrite={series_path.exists()})")
                        series_written += 1

                # Ensure prose include exists (create placeholder if missing; never overwrite)
                prose_path = series_prose_dir / f"{series_id}.md"
                if not prose_path.exists():
                    placeholder = (
                        f"<!-- series prose: {series_title} ({series_id}) -->\n"
                        "<!-- Replace this placeholder with the series' prose. -->\n"
                    )
                    if args.write:
                        prose_path.write_text(placeholder, encoding="utf-8")
                        print(f"{prefix_s}WRITE prose placeholder: {prose_path}")
                    else:
                        print(f"{prefix_s}DRY-RUN: would create prose placeholder {prose_path}")
        else:
            print("Series pages skipped: --work-ids scope active (use --series-ids to include series page rebuild).")

        if args.write and (series_status_updated > 0 or series_published_date_updated > 0):
            wb.save(xlsx_path)
            if series_status_updated > 0:
                print(f"Updated series status to 'published' for {series_status_updated} row(s).")
            if series_published_date_updated > 0:
                print(f"Set series published_date for {series_published_date_updated} row(s).")
        print(f"Series pages done. {'Would write' if not args.write else 'Wrote'}: {series_written}. Skipped: {series_skipped}.")

        # ----------------------------
        # Series JSON generation (Series + Works)
        # ----------------------------
        # Writes one JSON file per series_id listed in the Series sheet:
        #   assets/series/index/<series_id>.json
        # JSON structure:
        # {
        #   "header": {"series_id": "...", "count": N, "hash": "..."},
        #   "work_ids": ["00286", "00361", ...]
        # }

        sj_written = 0
        sj_skipped = 0
        sj_total = 0
        for sr, sr_cells in zip(series_rows[1:], series_ws.iter_rows(min_row=2), strict=False):
            sid_raw = cell(sr, series_hi, "series_id")
            if is_empty(sid_raw):
                continue
            sid = require_slug_safe("series_id", sid_raw)
            if series_json_selected_ids is not None and sid not in series_json_selected_ids:
                continue
            status_idx = series_hi.get("status")
            status_val = sr_cells[status_idx].value if status_idx is not None else cell(sr, series_hi, "status")
            status = normalize_status(status_val)
            if status != "draft":
                sj_total += 1
        sj_processed = 0

        # Build published work_id lists by series_id (from Works sheet, after any status updates)
        work_ids_by_series: Dict[str, List[str]] = {}
        status_idx = works_hi.get("status")
        for wr, wr_cells in zip(works_rows[1:], works_ws.iter_rows(min_row=2), strict=False):
            status_val = wr_cells[status_idx].value if status_idx is not None else cell(wr, works_hi, "status")
            if normalize_status(status_val) != "published":
                continue

            sid_raw = cell(wr, works_hi, "series_id")
            if is_empty(sid_raw):
                continue
            sid = require_slug_safe("series_id", sid_raw)

            wid_raw = cell(wr, works_hi, "work_id")
            if is_empty(wid_raw):
                continue
            wid = slug_id(wid_raw)

            work_ids_by_series.setdefault(sid, []).append(wid)

        # Ensure deterministic ordering (alpha) for each series' work_ids
        for sid in list(work_ids_by_series.keys()):
            work_ids_by_series[sid] = sorted(work_ids_by_series[sid])

        for sr, sr_cells in zip(series_rows[1:], series_ws.iter_rows(min_row=2), strict=False):
            sid_raw = cell(sr, series_hi, "series_id")
            if is_empty(sid_raw):
                sj_skipped += 1
                continue
            series_id = require_slug_safe("series_id", sid_raw)
            if series_json_selected_ids is not None and series_id not in series_json_selected_ids:
                sj_skipped += 1
                continue
            status_idx = series_hi.get("status")
            status_val = sr_cells[status_idx].value if status_idx is not None else cell(sr, series_hi, "status")
            status = normalize_status(status_val)
            if status == "draft":
                sj_skipped += 1
                continue

            sj_processed += 1
            prefix_j = f"[seriesjson {sj_processed}/{sj_total}] "

            work_ids = work_ids_by_series.get(series_id, [])
            series_hash = compute_series_hash(series_id, work_ids)

            payload = {
                "header": {
                    "series_id": series_id,
                    "count": len(work_ids),
                    "hash": series_hash,
                },
                "work_ids": work_ids,
            }

            out_json_path = series_json_dir / f"{series_id}.json"
            exists = out_json_path.exists()

            existing_hash = extract_existing_series_hash(out_json_path) if exists else None
            if (existing_hash is not None) and (existing_hash == series_hash) and (not args.force):
                sj_skipped += 1
                continue

            if args.write:
                out_json_path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(f"{prefix_j}WRITE: {out_json_path}")
                sj_written += 1
            else:
                print(f"{prefix_j}DRY-RUN: would write {out_json_path} (overwrite={exists})")
                sj_written += 1

        print(
            f"Series JSON done. {'Would write' if not args.write else 'Wrote'}: {sj_written}. Skipped: {sj_skipped}."
        )

    # ----------------------------
    # Work detail page generation + per-work detail JSON (WorkDetails)
    # ----------------------------
    if not work_details_rows or len(work_details_rows) < 2 or work_details_ws is None:
        print("No work detail pages to generate (WorkDetails sheet empty or missing).")
    else:
        required_details = ["work_id", "detail_id", "title", "status", "project_subfolder", "project_filename", "has_primary_2400"]
        missing_details = [c for c in required_details if c not in work_details_hi]
        if missing_details:
            raise SystemExit(f"WorkDetails sheet missing required columns: {', '.join(missing_details)}")

        projects_base_dir = Path(args.projects_base_dir).expanduser()
        projects_root = projects_base_dir / "projects"

        # Ensure width/height columns exist when writing so dimensions persist in the sheet.
        width_px_idx = work_details_hi.get("width_px")
        height_px_idx = work_details_hi.get("height_px")
        if args.write:
            if width_px_idx is None:
                width_px_idx = work_details_ws.max_column
                work_details_ws.cell(row=1, column=width_px_idx + 1, value="width_px")
                work_details_hi["width_px"] = width_px_idx
            if height_px_idx is None:
                height_px_idx = work_details_ws.max_column
                work_details_ws.cell(row=1, column=height_px_idx + 1, value="height_px")
                work_details_hi["height_px"] = height_px_idx

        # Build known works from the Works sheet to validate foreign-key references.
        known_work_ids: set[str] = set()
        for wr in works_rows[1:]:
            wid_raw = cell(wr, works_hi, "work_id")
            if is_empty(wid_raw):
                continue
            known_work_ids.add(slug_id(wid_raw))

        def is_actionable_detail_status(status_value: str) -> bool:
            if status_value == "draft":
                return True
            if status_value == "published" and args.force:
                return True
            return False

        details_written = 0
        details_skipped = 0
        details_status_updated = 0
        details_published_date_updated = 0
        details_dimensions_updated = 0
        details_published_date_idx = work_details_hi.get("published_date")
        details_published_date_missing_warned = False
        project_folder_missing_warned = False
        details_total = 0

        for dr in work_details_rows[1:]:
            wid_raw = cell(dr, work_details_hi, "work_id")
            if is_empty(wid_raw):
                continue
            wid = slug_id(wid_raw)
            if selected_ids is not None and wid not in selected_ids:
                continue
            status = normalize_status(cell(dr, work_details_hi, "status"))
            if is_actionable_detail_status(status):
                details_total += 1

        details_processed = 0
        for dr, dr_cells in zip(work_details_rows[1:], work_details_ws.iter_rows(min_row=2), strict=False):
            wid_raw = cell(dr, work_details_hi, "work_id")
            did_raw = cell(dr, work_details_hi, "detail_id")
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

            status = normalize_status(cell(dr, work_details_hi, "status"))
            if not is_actionable_detail_status(status):
                details_skipped += 1
                continue

            details_processed += 1
            prefix_d = f"[details {details_processed}/{details_total}] "

            did = slug_id(did_raw, width=3)
            detail_uid = f"{wid}-{did}"
            title = coerce_string(cell(dr, work_details_hi, "title"))
            has_primary_2400 = coerce_presence_bool(cell(dr, work_details_hi, "has_primary_2400"))
            project_subfolder = coerce_string(cell(dr, work_details_hi, "project_subfolder"))
            project_filename = coerce_string(cell(dr, work_details_hi, "project_filename"))
            width_px = coerce_int(cell(dr, work_details_hi, "width_px")) if "width_px" in work_details_hi else None
            height_px = coerce_int(cell(dr, work_details_hi, "height_px")) if "height_px" in work_details_hi else None

            # Resolve source image and persist dimensions back to WorkDetails for stable future rebuilds.
            project_folder = work_project_folder_by_id.get(wid)
            src_path: Optional[Path] = None
            if project_folder and project_filename:
                src_path = projects_root / project_folder
                if project_subfolder:
                    src_path = src_path / project_subfolder
                src_path = src_path / project_filename
            elif not project_folder_missing_warned:
                if not has_project_folder_col:
                    print("Warning: Works sheet has no project_folder column; cannot persist WorkDetails image dimensions.")
                else:
                    print("Warning: missing Works.project_folder for one or more WorkDetails rows; cannot persist those image dimensions.")
                project_folder_missing_warned = True

            if src_path is not None:
                src_w, src_h = read_image_dims_px(src_path)
                if src_w is not None and src_h is not None:
                    width_px = src_w
                    height_px = src_h
                    if args.write and width_px_idx is not None and height_px_idx is not None:
                        prev_w = dr_cells[width_px_idx].value if width_px_idx < len(dr_cells) else None
                        prev_h = dr_cells[height_px_idx].value if height_px_idx < len(dr_cells) else None
                        if prev_w != src_w or prev_h != src_h:
                            dr_cells[width_px_idx].value = src_w
                            dr_cells[height_px_idx].value = src_h
                            details_dimensions_updated += 1
                else:
                    print(f"Warning: could not read dimensions for detail source image: {src_path}")
            elif project_filename:
                print(f"Warning: could not resolve detail source image path for {detail_uid} ({project_filename})")

            dfm: Dict[str, Any] = {
                "work_id": wid,
                "detail_id": did,
                "detail_uid": detail_uid,
                "title": title,
                "project_subfolder": project_subfolder,
                "width_px": width_px,
                "height_px": height_px,
                "has_primary_2400": has_primary_2400,
                "layout": "work_details",
            }
            d_checksum = compute_work_checksum(dfm)
            dfm["checksum"] = d_checksum

            d_content = build_front_matter(dfm)
            d_path = work_details_out_dir / f"{detail_uid}.md"
            d_exists = d_path.exists()
            existing_checksum = extract_existing_checksum(d_path) if d_exists else None

            if (existing_checksum is not None) and (existing_checksum == d_checksum) and (not args.force):
                details_skipped += 1
                continue

            if args.write:
                d_path.write_text(d_content, encoding="utf-8")
                print(f"{prefix_d}WRITE: {d_path}")
                details_written += 1

                status_idx = work_details_hi.get("status")
                if status_idx is not None:
                    status_was = normalize_status(dr_cells[status_idx].value)
                    if status_was != "published":
                        dr_cells[status_idx].value = "published"
                        details_status_updated += 1
                    if (status_was != "published") or args.force:
                        if details_published_date_idx is not None:
                            dr_cells[details_published_date_idx].value = today
                            details_published_date_updated += 1
                        elif not details_published_date_missing_warned:
                            print("Warning: WorkDetails sheet missing published_date column; skipping date updates.")
                            details_published_date_missing_warned = True
            else:
                print(f"{prefix_d}DRY-RUN: would write {d_path} (overwrite={d_exists})")
                details_written += 1

        if args.write and (details_status_updated > 0 or details_published_date_updated > 0 or details_dimensions_updated > 0):
            wb.save(xlsx_path)
            if details_status_updated > 0:
                print(f"Updated work detail status to 'published' for {details_status_updated} row(s).")
            if details_published_date_updated > 0:
                print(f"Set work detail published_date for {details_published_date_updated} row(s).")
            if details_dimensions_updated > 0:
                print(f"Updated work detail width_px/height_px for {details_dimensions_updated} row(s).")

        print(
            f"Work detail pages done. {'Would write' if not args.write else 'Wrote'}: {details_written}. Skipped: {details_skipped}."
        )

        # Build per-work detail JSON from currently published detail rows only.
        # Keep worksheet order for both section order and detail order.
        encountered_work_ids: List[str] = []
        encountered_work_id_set: set[str] = set()
        sections_by_work: Dict[str, List[Dict[str, Any]]] = {}
        section_index_by_work: Dict[str, Dict[str, int]] = {}
        detail_status_idx = work_details_hi.get("status")

        for dr, dr_cells in zip(work_details_rows[1:], work_details_ws.iter_rows(min_row=2), strict=False):
            wid_raw = cell(dr, work_details_hi, "work_id")
            did_raw = cell(dr, work_details_hi, "detail_id")
            if is_empty(wid_raw) or is_empty(did_raw):
                continue

            wid = slug_id(wid_raw)
            if selected_ids is not None and wid not in selected_ids:
                continue
            if wid not in known_work_ids:
                continue

            if wid not in encountered_work_id_set:
                encountered_work_ids.append(wid)
                encountered_work_id_set.add(wid)

            status_val = dr_cells[detail_status_idx].value if detail_status_idx is not None else cell(dr, work_details_hi, "status")
            if normalize_status(status_val) != "published":
                continue

            did = slug_id(did_raw, width=3)
            detail_uid = f"{wid}-{did}"
            project_subfolder = coerce_string(cell(dr, work_details_hi, "project_subfolder")) or ""

            if wid not in sections_by_work:
                sections_by_work[wid] = []
                section_index_by_work[wid] = {}

            if project_subfolder not in section_index_by_work[wid]:
                section_index_by_work[wid][project_subfolder] = len(sections_by_work[wid])
                sections_by_work[wid].append(
                    {
                        "project_subfolder": project_subfolder,
                        "details": [],
                    }
                )

            section_idx = section_index_by_work[wid][project_subfolder]
            sections_by_work[wid][section_idx]["details"].append(
                {
                    "detail_id": did,
                    "detail_uid": detail_uid,
                    "title": coerce_string(cell(dr, work_details_hi, "title")),
                    "has_primary_2400": coerce_presence_bool(cell(dr, work_details_hi, "has_primary_2400")),
                }
            )

        wj_written = 0
        wj_skipped = 0
        wj_total = len(encountered_work_ids)
        wj_processed = 0

        for wid in encountered_work_ids:
            wj_processed += 1
            prefix_wj = f"[workjson {wj_processed}/{wj_total}] "

            sections = sections_by_work.get(wid, [])
            payload = {
                "header": {
                    "work_id": wid,
                    "count": sum(len(s.get("details", [])) for s in sections),
                    "hash": compute_work_details_hash(wid, sections),
                },
                "sections": sections,
            }
            out_json_path = works_json_dir / f"{wid}.json"
            exists = out_json_path.exists()
            existing_hash = extract_existing_series_hash(out_json_path) if exists else None
            payload_hash = payload["header"]["hash"]

            if (existing_hash is not None) and (existing_hash == payload_hash) and (not args.force):
                wj_skipped += 1
                continue

            if args.write:
                out_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"{prefix_wj}WRITE: {out_json_path}")
                wj_written += 1
            else:
                print(f"{prefix_wj}DRY-RUN: would write {out_json_path} (overwrite={exists})")
                wj_written += 1

        print(
            f"Work detail JSON done. {'Would write' if not args.write else 'Wrote'}: {wj_written}. Skipped: {wj_skipped}."
        )

    # ----------------------------
    # Moment page generation (Moments)
    # ----------------------------
    # Required columns:
    # - moment_id, title, status, published_date, date, date_display,
    #   moment_folder, moment_filename, width_px, height_px
    # Optional columns:
    # - moment_id / slug / id (preferred filename stem)
    # - date, date_display
    # - image_file/image_filename/project_filename
    # - image_alt
    # - width_px, height_px
    # - project_folder, project_subfolder, project_filename, work_id (for source image resolution)
    if not run_moments:
        print("Moment pages skipped: scoped run without --moment-ids/--moment-ids-file.")
    elif not moments_rows or len(moments_rows) < 2 or moments_ws is None:
        print("No moment pages to generate (Moments sheet empty or missing).")
    else:
        required_moments = [
            "moment_id",
            "title",
            "status",
            "published_date",
            "date",
            "date_display",
            "moment_folder",
            "moment_filename",
            "width_px",
            "height_px",
        ]
        missing_moments = [c for c in required_moments if c not in moments_hi]
        if missing_moments:
            raise SystemExit(f"Moments sheet missing required columns: {', '.join(missing_moments)}")

        title_col = "title"
        moment_id_col = "moment_id"
        date_col = "date"
        date_display_col = "date_display"
        image_file_col = first_present_col(
            moments_hi,
            ["image_file", "image_filename", "images_file", "images_filename", "hero_file", "file", "moment_filename"],
        )
        image_alt_col = first_present_col(moments_hi, ["image_alt", "alt"])
        project_folder_col = first_present_col(moments_hi, ["moment_folder", "project_folder"])
        project_subfolder_col = first_present_col(moments_hi, ["project_subfolder"])
        project_filename_col = first_present_col(moments_hi, ["moment_filename", "project_filename"])
        moment_work_id_col = first_present_col(moments_hi, ["work_id"])

        moments_published_date_idx = moments_hi.get("published_date")
        moments_width_px_idx = moments_hi.get("width_px")
        moments_height_px_idx = moments_hi.get("height_px")
        if args.write:
            if moments_width_px_idx is None:
                moments_width_px_idx = moments_ws.max_column
                moments_ws.cell(row=1, column=moments_width_px_idx + 1, value="width_px")
                moments_hi["width_px"] = moments_width_px_idx
            if moments_height_px_idx is None:
                moments_height_px_idx = moments_ws.max_column
                moments_ws.cell(row=1, column=moments_height_px_idx + 1, value="height_px")
                moments_hi["height_px"] = moments_height_px_idx

        projects_base_dir = Path(args.projects_base_dir).expanduser()
        moments_root = projects_base_dir / "moments"

        def is_actionable_moment_status(status_value: str) -> bool:
            if status_value == "draft":
                return True
            if status_value == "published" and args.force:
                return True
            return False

        moments_total = 0
        for mr in moments_rows[1:]:
            mid_raw = cell(mr, moments_hi, "moment_id")
            if is_empty(mid_raw):
                continue
            mid = normalize_text(mid_raw).lower()
            if selected_moment_ids is not None and mid not in selected_moment_ids:
                continue
            status = normalize_status(cell(mr, moments_hi, "status"))
            if is_actionable_moment_status(status):
                moments_total += 1

        moments_written = 0
        moments_skipped = 0
        moments_status_updated = 0
        moments_published_date_updated = 0
        moments_dimensions_updated = 0
        moments_published_date_missing_warned = False
        moments_processed = 0

        for mr, mr_cells in zip(moments_rows[1:], moments_ws.iter_rows(min_row=2), strict=False):
            mid_raw = cell(mr, moments_hi, "moment_id")
            if is_empty(mid_raw):
                moments_skipped += 1
                continue
            mid = normalize_text(mid_raw).lower()
            if selected_moment_ids is not None and mid not in selected_moment_ids:
                moments_skipped += 1
                continue
            status = normalize_status(cell(mr, moments_hi, "status"))
            if not is_actionable_moment_status(status):
                moments_skipped += 1
                continue

            moments_processed += 1
            prefix_m = f"[moments {moments_processed}/{moments_total}] "

            title = coerce_string(cell(mr, moments_hi, title_col)) if title_col else None
            moment_id_raw = coerce_string(cell(mr, moments_hi, moment_id_col)) if moment_id_col else None
            if moment_id_raw:
                moment_id = moment_id_raw.strip().lower()
                if not is_slug_safe(moment_id):
                    raise SystemExit(f"Moments.moment_id must be slug-safe; got: {moment_id_raw!r}")
            else:
                raise SystemExit("Moments.moment_id is required")

            if not moment_id:
                print(f"{prefix_m}SKIP: missing slug/id and title")
                moments_skipped += 1
                continue

            date_value = parse_date(cell(mr, moments_hi, date_col)) if date_col else None
            date_display = coerce_string(cell(mr, moments_hi, date_display_col)) if date_display_col else None
            width_px = coerce_int(cell(mr, moments_hi, "width_px")) if "width_px" in moments_hi else None
            height_px = coerce_int(cell(mr, moments_hi, "height_px")) if "height_px" in moments_hi else None

            project_filename = coerce_string(cell(mr, moments_hi, project_filename_col)) if project_filename_col else None
            image_file = coerce_string(cell(mr, moments_hi, image_file_col)) if image_file_col else None
            image_alt = coerce_string(cell(mr, moments_hi, image_alt_col)) if image_alt_col else None
            # Srcset derivatives are keyed by moment_id because copy_draft_media_files.py
            # renames source images to <moment_id>.<ext> before derivative generation.
            if image_file is None and project_filename is not None:
                image_file = f"{moment_id}.webp"
            if image_file is not None and image_alt is None:
                image_alt = title or moment_id

            # Resolve source image for dimensions when possible.
            project_folder = coerce_string(cell(mr, moments_hi, project_folder_col)) if project_folder_col else None
            project_subfolder = coerce_string(cell(mr, moments_hi, project_subfolder_col)) if project_subfolder_col else None
            if project_folder is None and moment_work_id_col is not None:
                moment_work_id_raw = cell(mr, moments_hi, moment_work_id_col)
                if not is_empty(moment_work_id_raw):
                    project_folder = work_project_folder_by_id.get(slug_id(moment_work_id_raw))

            src_path: Optional[Path] = None
            source_filename = project_filename or image_file
            if project_folder and source_filename:
                src_path = moments_root / project_folder
                if project_subfolder:
                    src_path = src_path / project_subfolder
                src_path = src_path / source_filename
            elif project_subfolder and source_filename:
                # Fallback for rows that store a path rooted at moments/.
                src_path = moments_root / project_subfolder / source_filename

            if src_path is not None:
                src_w, src_h = read_image_dims_px(src_path)
                if src_w is not None and src_h is not None:
                    width_px = src_w
                    height_px = src_h
                    if args.write and moments_width_px_idx is not None and moments_height_px_idx is not None:
                        prev_w = mr_cells[moments_width_px_idx].value if moments_width_px_idx < len(mr_cells) else None
                        prev_h = mr_cells[moments_height_px_idx].value if moments_height_px_idx < len(mr_cells) else None
                        if prev_w != src_w or prev_h != src_h:
                            mr_cells[moments_width_px_idx].value = src_w
                            mr_cells[moments_height_px_idx].value = src_h
                            moments_dimensions_updated += 1

            images_list: List[Dict[str, Any]] = []
            if image_file is not None:
                images_list.append(
                    {
                        "file": image_file,
                        "alt": image_alt,
                    }
                )

            mfm: Dict[str, Any] = {
                "moment_id": moment_id,
                "title": title or moment_id,
                "date": date_value,
                "date_display": date_display,
                "images": images_list,
                "width_px": width_px,
                "height_px": height_px,
                "layout": "moment",
            }
            m_checksum = compute_work_checksum(mfm)
            mfm["checksum"] = m_checksum

            prose_path = moments_prose_dir / f"{moment_id}.md"
            if not prose_path.exists():
                placeholder = (
                    f"<!-- moment prose: {title or moment_id} ({moment_id}) -->\n"
                    "<!-- Replace this placeholder with the moment text. -->\n"
                )
                if args.write:
                    prose_path.write_text(placeholder, encoding="utf-8")
                    print(f"{prefix_m}WRITE prose placeholder: {prose_path}")
                else:
                    print(f"{prefix_m}DRY-RUN: would create prose placeholder {prose_path}")

            m_content = build_front_matter(mfm) + "\n" + f"{{% include moments_prose/{moment_id}.md %}}\n"
            m_path = moments_out_dir / f"{moment_id}.md"
            m_exists = m_path.exists()
            existing_checksum = extract_existing_checksum(m_path) if m_exists else None

            if (existing_checksum is not None) and (existing_checksum == m_checksum) and (not args.force):
                moments_skipped += 1
                continue

            if args.write:
                m_path.write_text(m_content, encoding="utf-8")
                print(f"{prefix_m}WRITE: {m_path}")
                moments_written += 1

                status_idx = moments_hi.get("status")
                if status_idx is not None:
                    status_was = normalize_status(mr_cells[status_idx].value)
                    if status_was != "published":
                        mr_cells[status_idx].value = "published"
                        moments_status_updated += 1
                    if (status_was != "published") or args.force:
                        if moments_published_date_idx is not None:
                            mr_cells[moments_published_date_idx].value = today
                            moments_published_date_updated += 1
                        elif not moments_published_date_missing_warned:
                            print("Warning: Moments sheet missing published_date column; skipping date updates.")
                            moments_published_date_missing_warned = True
            else:
                print(f"{prefix_m}DRY-RUN: would write {m_path} (overwrite={m_exists})")
                moments_written += 1

        if args.write and (moments_status_updated > 0 or moments_published_date_updated > 0 or moments_dimensions_updated > 0):
            wb.save(xlsx_path)
            if moments_status_updated > 0:
                print(f"Updated moment status to 'published' for {moments_status_updated} row(s).")
            if moments_published_date_updated > 0:
                print(f"Set moment published_date for {moments_published_date_updated} row(s).")
            if moments_dimensions_updated > 0:
                print(f"Updated moment width_px/height_px for {moments_dimensions_updated} row(s).")

        print(
            f"Moment pages done. {'Would write' if not args.write else 'Wrote'}: {moments_written}. Skipped: {moments_skipped}."
        )

if __name__ == "__main__":
    main()
