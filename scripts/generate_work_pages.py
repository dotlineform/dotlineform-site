#!/usr/bin/env python3
"""
Generate Jekyll work pages from an Excel workbook.

Default output: ./works/<ID>.md  (matches your "URLs mirror folder structure" preference)
Supports collections too: use --output-dir _works

Safe by default:
- dry-run unless you pass --write
- will not overwrite unless --force

Example:
  python3 scripts/generate_work_pages.py data/works.xlsx --sheet Works --write
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import openpyxl


def slug_id(raw: Any, width: int = 5) -> str:
    if raw is None:
        raise ValueError("Missing id")
    s = str(raw).strip()
    # Handle numeric IDs like 361.0 from Excel
    s = re.sub(r"\.0$", "", s)
    s = re.sub(r"\D", "", s)  # keep digits only
    if not s:
        raise ValueError(f"Invalid id value: {raw!r}")
    return s.zfill(width)


def parse_date(raw: Any) -> Optional[str]:
    if raw is None or str(raw).strip() == "":
        return None
    if isinstance(raw, dt.datetime):
        return raw.date().isoformat()
    if isinstance(raw, dt.date):
        return raw.isoformat()
    s = str(raw).strip()
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
    s = str(raw).strip()
    if not s:
        return []
    return [item.strip() for item in s.split(sep) if item.strip()]


def yaml_quote(s: str) -> str:
    # Conservative quoting to keep YAML safe
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def to_yaml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        # avoid "361.0"
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
    if isinstance(v, list):
        if not v:
            return "[]"
        return "[" + ", ".join(yaml_quote(str(x)) for x in v) + "]"
    return yaml_quote(str(v))


def build_front_matter(fields: Dict[str, Any]) -> str:
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            continue
        lines.append(f"{k}: {to_yaml_value(v)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", help="Path to Excel workbook (.xlsx)")
    ap.add_argument("--sheet", default=None, help="Sheet name (default: active sheet)")
    ap.add_argument("--output-dir", default="works", help="Output folder (works or _works)")
    ap.add_argument("--id-col", default="id", help="Column header for work id")
    ap.add_argument("--title-col", default="title", help="Column header for title")
    ap.add_argument("--date-col", default="date", help="Column header for date")
    ap.add_argument("--layout", default="theme", help="Default layout if column missing")
    ap.add_argument("--permalink", default="", help="If set, use as permalink pattern, e.g. /works/{id}/")
    ap.add_argument("--assets-base", default="/assets/works", help="Base path for work assets")
    ap.add_argument("--attachments-col", default="attachments", help="Column header for attachments (semicolon-separated)")
    ap.add_argument("--tags-col", default="tags", help="Column header for tags (comma-separated)")
    ap.add_argument("--notes-col", default="notes", help="Column header for notes/body text")
    ap.add_argument("--write", action="store_true", help="Actually write files (otherwise dry-run)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    xlsx_path = Path(args.xlsx).expanduser()
    if not xlsx_path.exists():
        raise SystemExit(f"Workbook not found: {xlsx_path}")

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[args.sheet] if args.sheet else wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise SystemExit("Sheet is empty")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    header_index = {h: i for i, h in enumerate(headers) if h}

    def cell(row: tuple, col_name: str) -> Any:
        i = header_index.get(col_name)
        return None if i is None or i >= len(row) else row[i]

    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0

    for r in rows[1:]:
        raw_id = cell(r, args.id_col)
        raw_title = cell(r, args.title_col)
        if raw_id is None or raw_title is None or str(raw_title).strip() == "":
            skipped += 1
            continue

        wid = slug_id(raw_id)
        title = str(raw_title).strip()

        date_val = parse_date(cell(r, args.date_col)) or dt.date.today().isoformat()

        # Optional fields
        catalogue_date = parse_date(cell(r, "catalogue_date"))
        primary = cell(r, "primary")
        thumb = cell(r, "thumb")
        series = cell(r, "series")
        medium = cell(r, "medium")
        dimensions = cell(r, "dimensions")

        tags = parse_list(cell(r, args.tags_col), sep=",")
        attachments = parse_list(cell(r, args.attachments_col), sep=";")

        # Canonical: attachments stored per-work
        # Example: /assets/works/00361/files/<filename>
        attachment_urls = [
            f"{args.assets_base}/{wid}/files/{fname}" for fname in attachments
        ]

        fm: Dict[str, Any] = {
            "title": title,
            "date": date_val,
            "layout": str(cell(r, "layout")).strip() if cell(r, "layout") else args.layout,
            "work_id": wid,
            # Sorting-only field; your layout should not display it.
            "catalogue_date": catalogue_date,
            "series": str(series).strip() if series else None,
            "medium": str(medium).strip() if medium else None,
            "dimensions": str(dimensions).strip() if dimensions else None,
            "primary": str(primary).strip() if primary else None,
            "thumb": str(thumb).strip() if thumb else None,
            "tags": tags if tags else None,
        }

        if args.permalink:
            fm["permalink"] = args.permalink.format(id=wid)

        body_lines: List[str] = []
        notes = cell(r, args.notes_col)
        if notes and str(notes).strip():
            body_lines.append(str(notes).strip())
            body_lines.append("")

        if attachment_urls:
            body_lines.append("## Supplements")
            for url in attachment_urls:
                fname = url.split("/")[-1]
                body_lines.append(f"- [{fname}]({url})")
            body_lines.append("")

        content = build_front_matter(fm) + "\n".join(body_lines).rstrip() + "\n"

        out_path = out_dir / f"{wid}.md"
        exists = out_path.exists()

        if exists and not args.force:
            print(f"SKIP (exists): {out_path}")
            skipped += 1
            continue

        if args.write:
            out_path.write_text(content, encoding="utf-8")
            print(f"WRITE: {out_path}")
            written += 1
        else:
            print(f"DRY-RUN: would write {out_path} (overwrite={exists})")
            written += 1

    print(f"\nDone. {'Would write' if not args.write else 'Wrote'}: {written}. Skipped: {skipped}.")


if __name__ == "__main__":
    main()