#!/usr/bin/env python3
"""Verify retired catalogue notes fields are no longer accepted as source fields."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue.catalogue_series_service import extract_series_update  # noqa: E402
from catalogue.catalogue_source import SERIES_FIELDS, WORK_FIELDS  # noqa: E402
from catalogue.catalogue_work_service import extract_work_update  # noqa: E402


def assert_rejects_notes(label: str, func) -> None:
    try:
        func({"record": {"notes": "retired"}})
    except ValueError as exc:
        assert "unsupported fields: notes" in str(exc), label
    else:
        raise AssertionError(f"{label}: expected retired notes field to be rejected")


def test_notes_is_not_a_source_field() -> None:
    assert "notes" not in WORK_FIELDS
    assert "notes" not in SERIES_FIELDS


def test_work_and_series_updates_reject_notes() -> None:
    assert_rejects_notes("work update", extract_work_update)
    assert_rejects_notes("series update", extract_series_update)


def main() -> None:
    test_notes_is_not_a_source_field()
    test_work_and_series_updates_reject_notes()
    print("Catalogue retired notes field tests OK")


if __name__ == "__main__":
    main()
