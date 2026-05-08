#!/usr/bin/env python3
"""Verify catalogue lookup refresh execution helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue_source import CatalogueSourceRecords, write_source_record_payloads  # noqa: E402
import catalogue_invalidation as invalidation  # noqa: E402
import catalogue_lookup_refresh as lookup_refresh  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def write_fixture_source(source_dir: Path) -> CatalogueSourceRecords:
    records = CatalogueSourceRecords(
        works={
            "00001": {
                "work_id": "00001",
                "title": "Alpha",
                "year_display": "2026",
                "status": "published",
                "series_ids": ["009"],
                "notes": "Before",
            },
            "00002": {
                "work_id": "00002",
                "title": "Beta",
                "year_display": "2026",
                "status": "published",
                "series_ids": ["009"],
            },
        },
        work_details={
            "00001-001": {
                "detail_uid": "00001-001",
                "work_id": "00001",
                "detail_id": "001",
                "title": "Alpha detail",
                "sort_order": 1,
                "status": "published",
            }
        },
        series={
            "009": {
                "series_id": "009",
                "title": "Series",
                "status": "published",
                "primary_work_id": "00001",
            }
        },
    )
    write_source_record_payloads(source_dir, records)
    return records


def fixture_paths(tmp: str) -> tuple[Path, Path, Path, CatalogueSourceRecords]:
    repo_root = Path(tmp)
    source_dir = repo_root / "assets/studio/data/catalogue"
    lookup_dir = repo_root / "assets/studio/data/catalogue_lookup"
    records = write_fixture_source(source_dir)
    return repo_root, source_dir, lookup_dir, records


def test_full_refresh_reports_all_lookup_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, _records = fixture_paths(tmp)

        result = lookup_refresh.full_lookup_refresh(source_dir, lookup_dir, repo_root)

    assert_equal(result["mode"], "full", "full mode")
    assert_equal(result["artifacts"], ["full_lookup_refresh"], "full artifacts")
    assert_equal(result["written_count"], 8, "full written count")
    assert "assets/studio/data/catalogue_lookup/work_search.json" in result["written_paths"]
    assert "assets/studio/data/catalogue_lookup/works/00001.json" in result["written_paths"]


def test_work_single_record_refresh_reports_work_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        current_record = records.works["00001"]
        updated_record = dict(current_record, notes="After")
        invalidation_result = invalidation.work_lookup_invalidation_for_fields(["notes"])

        result = lookup_refresh.work_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            work_id="00001",
            fields_changed=["notes"],
            current_record=current_record,
            updated_record=updated_record,
            invalidation_result=invalidation_result,
            locked_single_record_fields={"notes"},
        )

    assert_equal(result["mode"], "single-record", "work single mode")
    assert_equal(result["artifacts"], ["work_record"], "work single artifacts")
    assert_equal(result["written_count"], 1, "work single written count")
    assert_equal(
        result["written_paths"],
        ["assets/studio/data/catalogue_lookup/works/00001.json"],
        "work single paths",
    )
    assert_equal(result["invalidation_class"], invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD, "work single class")


def test_work_targeted_refresh_reports_related_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        current_record = records.works["00001"]
        updated_record = dict(current_record, title="Alpha Updated")
        invalidation_result = invalidation.work_lookup_invalidation_for_fields(["title"])

        result = lookup_refresh.work_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            work_id="00001",
            fields_changed=["title"],
            current_record=current_record,
            updated_record=updated_record,
            invalidation_result=invalidation_result,
            locked_single_record_fields=set(),
        )

    assert_equal(result["mode"], "targeted-multi-record", "work targeted mode")
    assert_equal(
        result["artifacts"],
        ["related_series_records", "related_work_detail_records", "work_record", "work_search"],
        "work targeted artifacts",
    )
    assert_equal(result["written_count"], 4, "work targeted written count")
    assert "assets/studio/data/catalogue_lookup/series/009.json" in result["written_paths"]
    assert "assets/studio/data/catalogue_lookup/work_details/00001-001.json" in result["written_paths"]


def test_detail_targeted_refresh_reports_detail_and_parent_work() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        updated_record = dict(records.work_details["00001-001"], sort_order=2)
        invalidation_result = invalidation.detail_lookup_invalidation_for_fields(["sort_order"])

        result = lookup_refresh.detail_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            detail_uid="00001-001",
            updated_record=updated_record,
            invalidation_result=invalidation_result,
        )

    assert_equal(result["mode"], "targeted-multi-record", "detail targeted mode")
    assert_equal(result["artifacts"], ["related_work_records", "work_detail_record"], "detail targeted artifacts")
    assert_equal(result["written_count"], 2, "detail targeted written count")
    assert "assets/studio/data/catalogue_lookup/work_details/00001-001.json" in result["written_paths"]
    assert "assets/studio/data/catalogue_lookup/works/00001.json" in result["written_paths"]


def test_series_targeted_refresh_reports_series_search_and_member_works() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, _records = fixture_paths(tmp)
        invalidation_result = invalidation.series_lookup_invalidation_for_fields(["title"])

        result = lookup_refresh.series_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            series_id="009",
            invalidation_result=invalidation_result,
        )

    assert_equal(result["mode"], "targeted-multi-record", "series targeted mode")
    assert_equal(
        result["artifacts"],
        ["related_work_records", "series_record", "series_search"],
        "series targeted artifacts",
    )
    assert_equal(result["written_count"], 4, "series targeted written count")
    assert "assets/studio/data/catalogue_lookup/series/009.json" in result["written_paths"]
    assert "assets/studio/data/catalogue_lookup/works/00001.json" in result["written_paths"]
    assert "assets/studio/data/catalogue_lookup/works/00002.json" in result["written_paths"]


def main() -> None:
    test_full_refresh_reports_all_lookup_artifacts()
    test_work_single_record_refresh_reports_work_record()
    test_work_targeted_refresh_reports_related_artifacts()
    test_detail_targeted_refresh_reports_detail_and_parent_work()
    test_series_targeted_refresh_reports_series_search_and_member_works()
    print("Catalogue lookup refresh tests OK")


if __name__ == "__main__":
    main()
