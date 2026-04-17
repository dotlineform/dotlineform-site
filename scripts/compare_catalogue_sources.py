#!/usr/bin/env python3
"""Compare workbook-normalized catalogue source records with JSON source records."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from catalogue_source import (
        DEFAULT_SOURCE_DIR,
        DEFAULT_WORKBOOK_PATH,
        compare_sources,
        records_from_json_source,
        records_from_workbook,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_source import (
        DEFAULT_SOURCE_DIR,
        DEFAULT_WORKBOOK_PATH,
        compare_sources,
        records_from_json_source,
        records_from_workbook,
    )

try:
    from display_paths import format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.display_paths import format_display_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare workbook source with catalogue source JSON.")
    parser.add_argument("xlsx", nargs="?", default=str(DEFAULT_WORKBOOK_PATH), help="Workbook path")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Catalogue source JSON directory")
    parser.add_argument("--max-diffs", type=int, default=25, help="Maximum diff lines to print")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    workbook_path = Path(args.xlsx).expanduser()
    source_dir = Path(args.source_dir).expanduser()
    workbook_records = records_from_workbook(workbook_path)
    json_records = records_from_json_source(source_dir)
    diffs = compare_sources(workbook_records, json_records)

    print("Catalogue source comparison")
    print(f"- workbook: {format_display_path(workbook_path, repo_root=repo_root)}")
    print(f"- source dir: {format_display_path(source_dir, repo_root=repo_root)}")
    for kind, record_map in workbook_records.as_maps().items():
        json_count = len(json_records.as_maps()[kind])
        print(f"- {kind}: workbook={len(record_map)} json={json_count}")

    if not diffs:
        print("Comparison passed.")
        return 0

    print(f"Comparison failed: {len(diffs)} difference(s).")
    for diff in diffs[: max(args.max_diffs, 0)]:
        print(f"- {diff}")
    if len(diffs) > args.max_diffs:
        print(f"- ... {len(diffs) - args.max_diffs} more")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
