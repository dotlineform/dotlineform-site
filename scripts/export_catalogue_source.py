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
    parser.parse_args()

    print(
        "Deprecated: scripts/export_catalogue_source.py is retired.\n"
        "Canonical catalogue source JSON is now maintained directly in assets/studio/data/catalogue/.\n"
        "Use the Studio workflow, import flow, validation, and comparison tools instead of re-exporting from works.xlsx."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
