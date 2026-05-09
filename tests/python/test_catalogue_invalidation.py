#!/usr/bin/env python3
"""Verify catalogue lookup and moment-build invalidation rules."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_invalidation as invalidation  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_empty_change_is_single_record_noop() -> None:
    result = invalidation.work_lookup_invalidation_for_fields([])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD, "empty class")
    assert_equal(result["artifacts"], [], "empty artifacts")
    assert_equal(result["fields"], [], "empty fields")
    assert_equal(result["unknown_fields"], [], "empty unknown fields")


def test_work_title_uses_targeted_multi_record_artifacts() -> None:
    result = invalidation.work_lookup_invalidation_for_fields(["title"])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD, "work title class")
    assert_equal(
        result["artifacts"],
        ["related_series_records", "related_work_detail_records", "work_record", "work_search"],
        "work title artifacts",
    )


def test_unknown_field_forces_full_refresh() -> None:
    result = invalidation.series_lookup_invalidation_for_fields(["unknown_series_field"])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_FULL, "unknown field class")
    assert_equal(result["artifacts"], ["full_lookup_refresh"], "unknown field artifacts")
    assert_equal(result["unknown_fields"], ["unknown_series_field"], "unknown fields")


def test_detail_sort_order_uses_related_work_records() -> None:
    result = invalidation.detail_lookup_invalidation_for_fields(["sort_order"])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD, "detail sort class")
    assert_equal(result["artifacts"], ["related_work_records", "work_detail_record"], "detail sort artifacts")


def test_moment_title_uses_runtime_index_and_search_artifacts() -> None:
    result = invalidation.moment_build_invalidation_for_fields(["title"])
    assert_equal(result["class"], invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD, "moment title class")
    assert_equal(result["artifacts"], ["catalogue_search", "moment_record", "moments_index"], "moment title artifacts")


def main() -> None:
    test_empty_change_is_single_record_noop()
    test_work_title_uses_targeted_multi_record_artifacts()
    test_unknown_field_forces_full_refresh()
    test_detail_sort_order_uses_related_work_records()
    test_moment_title_uses_runtime_index_and_search_artifacts()
    print("Catalogue invalidation tests OK")


if __name__ == "__main__":
    main()
