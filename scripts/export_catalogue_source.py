#!/usr/bin/env python3
"""Export catalogue source JSON from the current workbook.

Safe by default: prints the export plan unless --write is passed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from catalogue_source import (
        DEFAULT_SOURCE_DIR,
        DEFAULT_WORKBOOK_PATH,
        payloads_from_records,
        records_from_workbook,
        write_payloads,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_source import (
        DEFAULT_SOURCE_DIR,
        DEFAULT_WORKBOOK_PATH,
        payloads_from_records,
        records_from_workbook,
        write_payloads,
    )

try:
    from display_paths import format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.display_paths import format_display_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export canonical catalogue source JSON from data/works.xlsx.")
    parser.add_argument("xlsx", nargs="?", default=str(DEFAULT_WORKBOOK_PATH), help="Workbook path")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Output source JSON directory")
    parser.add_argument("--write", action="store_true", help="Write JSON files")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    workbook_path = Path(args.xlsx).expanduser()
    source_dir = Path(args.source_dir).expanduser()
    records = records_from_workbook(workbook_path)
    payloads = payloads_from_records(records, workbook_path=workbook_path)

    print("Catalogue source export")
    print(f"- workbook: {format_display_path(workbook_path, repo_root=repo_root)}")
    print(f"- source dir: {format_display_path(source_dir, repo_root=repo_root)}")
    for kind, record_map in records.as_maps().items():
        print(f"- {kind}: {len(record_map)} records")

    if not args.write:
        print("DRY-RUN: pass --write to write source JSON files.")
        return 0

    written = write_payloads(source_dir, payloads)
    for path in written:
        print(f"WRITE: {format_display_path(path, repo_root=repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
