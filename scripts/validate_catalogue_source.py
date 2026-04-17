#!/usr/bin/env python3
"""Validate canonical catalogue source JSON files."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source, validate_source_records
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source, validate_source_records

try:
    from display_paths import format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.display_paths import format_display_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate catalogue source JSON files.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Catalogue source JSON directory")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source_dir = Path(args.source_dir).expanduser()
    records = records_from_json_source(source_dir)
    errors = validate_source_records(records)
    print(f"Catalogue source validation: {format_display_path(source_dir, repo_root=repo_root)}")
    for kind, record_map in records.as_maps().items():
        print(f"- {kind}: {len(record_map)} records")

    if not errors:
        print("Validation passed.")
        return 0

    print("Validation failed:")
    for error in errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
