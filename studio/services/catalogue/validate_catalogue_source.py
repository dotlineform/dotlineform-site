#!/usr/bin/env python3
"""Validate canonical catalogue source JSON files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

try:
    from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source, validate_source_records
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source, validate_source_records

try:
    from display_paths import format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from studio.shared.python.display_paths import format_display_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate catalogue source JSON files.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Catalogue source JSON directory")
    parser.add_argument(
        "--target-media-section-schema",
        action="store_true",
        help="Require work-detail media section fields and reject compatibility detail project_subfolder.",
    )
    args = parser.parse_args()

    repo_root = REPO_ROOT
    source_dir = Path(args.source_dir).expanduser()
    records = records_from_json_source(source_dir)
    errors = validate_source_records(
        records,
        require_detail_media_sections=args.target_media_section_schema,
        allow_compat_detail_project_subfolder=not args.target_media_section_schema,
    )
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
