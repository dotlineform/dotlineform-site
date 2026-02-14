#!/usr/bin/env python3
"""
Generate Jekyll work pages from an Excel workbook.

This repo stores works as a Jekyll collection in `_works/`. The generator writes one Markdown
file per work (e.g. `_works/00286.md`) with YAML front matter populated from these worksheets.
It can also emit a parallel print collection (e.g. `_works_print/00286.md`) for PDF rendering.

Series JSON index files are written to assets/series/index/<series_id>.json (one per series_id in the Series sheet).

- Works: base work metadata (1 row per work)
- Series: series master data (1 row per series_id)

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

"""

from __future__ import annotations

import argparse
import datetime as dt
import re
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


NUMERIC_KEYS = {"year", "height_cm", "width_cm", "depth_cm"}
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

    # Output
    ap.add_argument("--output-dir", default="_works", help="Output folder for generated work pages")
    ap.add_argument("--print-output-dir", default="_works_print", help="Output folder for generated print work pages")
    ap.add_argument("--work-prose-dir", default="_includes/work_prose", help="Folder for optional manual work prose includes")
    ap.add_argument("--series-output-dir", default="_series", help="Output folder for generated series pages")
    ap.add_argument("--series-prose-dir", default="_includes/series_prose", help="Folder for manual series prose includes")
    ap.add_argument("--series-json-dir", default="assets/series/index", help="Output folder for generated per-series JSON index files")

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

    # Load all worksheets up-front.
    works_rows = read_sheet_rows(args.works_sheet)
    series_rows = read_sheet_rows(args.series_sheet)
    series_ws = wb[args.series_sheet]

    if not works_rows:
        raise SystemExit(f"Works sheet '{args.works_sheet}' is empty")

    works_hi = build_header_index(works_rows)
    series_hi = build_header_index(series_rows) if series_rows else {}

    if "status" not in works_hi:
        raise SystemExit("Works sheet missing required column: status")

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

    written = 0
    skipped = 0
    print_written = 0
    print_skipped = 0
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

    # If caller scopes by series but does not provide an explicit work filter,
    # skip work-page processing by default.
    if selected_series_ids is not None and not explicit_work_filter:
        selected_ids = set()

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

    if args.write and status_updated > 0:
        wb.save(xlsx_path)
        print(f"Updated status to 'published' for {status_updated} row(s).")
        if published_date_updated > 0:
            print(f"Set published_date for {published_date_updated} row(s).")

    print(
        f"\nDone. {'Would write' if not args.write else 'Wrote'}: {written} works, {print_written} print."
        f" Skipped: {skipped} works, {print_skipped} print."
    )
    print(f"Workbook: {xlsx_path}")
    if args.write:
        print("Note: if the workbook is open in Excel, close and reopen it to see changes.")

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
            if selected_series_ids is not None and sid not in selected_series_ids:
                continue
            status = normalize_status(cell(sr, series_hi, "status"))
            if is_actionable_series_status(status):
                s_total += 1
        s_processed = 0

        for sr, sr_cells in zip(series_rows[1:], series_ws.iter_rows(min_row=2), strict=False):
            sid_raw = cell(sr, series_hi, "series_id")
            if is_empty(sid_raw):
                series_skipped += 1
                continue
            series_id = require_slug_safe("series_id", sid_raw)
            if selected_series_ids is not None and series_id not in selected_series_ids:
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
            if selected_series_ids is not None and sid not in selected_series_ids:
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
            if selected_series_ids is not None and series_id not in selected_series_ids:
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

if __name__ == "__main__":
    main()
