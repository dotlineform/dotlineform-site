#!/usr/bin/env python3
"""Export derived Studio catalogue lookup payloads from canonical source JSON."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from catalogue_lookup import DEFAULT_LOOKUP_DIR, build_and_write_catalogue_lookup
    from catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_lookup import DEFAULT_LOOKUP_DIR, build_and_write_catalogue_lookup  # type: ignore
    from scripts.catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source  # type: ignore


def main() -> int:
    parser = argparse.ArgumentParser(description="Export derived Studio catalogue lookup JSON from canonical source.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Canonical source JSON directory")
    parser.add_argument("--lookup-dir", default=str(DEFAULT_LOOKUP_DIR), help="Derived lookup output directory")
    parser.add_argument("--write", action="store_true", help="Write lookup JSON files")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser()
    lookup_dir = Path(args.lookup_dir).expanduser()
    records = records_from_json_source(source_dir)

    print("Catalogue lookup export")
    print(f"- source dir: {source_dir}")
    print(f"- lookup dir: {lookup_dir}")
    print(f"- works: {len(records.works)}")
    print(f"- work_details: {len(records.work_details)}")
    print(f"- series: {len(records.series)}")

    if not args.write:
        print("DRY-RUN: pass --write to write lookup JSON files.")
        return 0

    written = build_and_write_catalogue_lookup(source_dir, lookup_dir)
    print(f"WRITE: {len(written)} lookup files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
