#!/usr/bin/env python3
"""Verify moment-build invalidation rules."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_invalidation as invalidation  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_empty_moment_change_is_single_record_noop() -> None:
    result = invalidation.moment_build_invalidation_for_fields([])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD, "empty class")
    assert_equal(result["artifacts"], [], "empty artifacts")
    assert_equal(result["fields"], [], "empty fields")
    assert_equal(result["unknown_fields"], [], "empty unknown fields")


def test_unknown_moment_field_forces_full_refresh() -> None:
    result = invalidation.moment_build_invalidation_for_fields(["unknown_moment_field"])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_FULL, "unknown field class")
    assert_equal(result["artifacts"], ["full_lookup_refresh"], "unknown field artifacts")
    assert_equal(result["unknown_fields"], ["unknown_moment_field"], "unknown fields")


def test_moment_title_uses_runtime_index_and_search_artifacts() -> None:
    result = invalidation.moment_build_invalidation_for_fields(["title"])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD, "moment title class")
    assert_equal(result["artifacts"], ["catalogue_search", "moment_record", "moments_index"], "moment title artifacts")


def main() -> None:
    test_empty_moment_change_is_single_record_noop()
    test_unknown_moment_field_forces_full_refresh()
    test_moment_title_uses_runtime_index_and_search_artifacts()
    print("Catalogue invalidation tests OK")


if __name__ == "__main__":
    main()
