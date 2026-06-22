#!/usr/bin/env python3
"""Verify catalogue lookup refresh execution helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from catalogue.catalogue_field_registry import field_aware_build_plan, load_catalogue_field_registry  # noqa: E402
from catalogue.catalogue_source import CatalogueSourceRecords, write_source_record_payloads  # noqa: E402
from catalogue import catalogue_lookup_refresh as lookup_refresh  # noqa: E402


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
                "provenance": "Before",
            },
            "00002": {
                "work_id": "00002",
                "title": "Beta",
                "year_display": "2026",
                "status": "published",
                "series_ids": ["009"],
            },
        },
        work_detail_sections={
            "00001-1": {
                "section_id": "00001-1",
                "work_id": "00001",
                "details_subfolder": "details",
                "section_title": "Details",
                "section_order": 1,
                "detail_sort": None,
            }
        },
        work_details={
            "00001-001": {
                "detail_uid": "00001-001",
                "work_id": "00001",
                "detail_id": "001",
                "section_id": "00001-1",
                "title": "Alpha detail",
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
    source_dir = repo_root / "studio/data/canonical/catalogue"
    lookup_dir = repo_root / "studio/data/generated/catalogue-lookup"
    records = write_fixture_source(source_dir)
    return repo_root, source_dir, lookup_dir, records


def lookup_plan_for(
    records: CatalogueSourceRecords,
    *,
    record_family: str,
    changed_fields: list[str],
    current_record: dict,
    updated_record: dict,
) -> dict:
    build_plan = field_aware_build_plan(
        load_catalogue_field_registry(REPO_ROOT),
        record_family=record_family,
        operation="metadata_update",
        changed_field_names=changed_fields,
        context={
            "source_records": records,
            "current_record": current_record,
            "updated_record": updated_record,
        },
    )
    return lookup_refresh.derive_lookup_refresh_plan(
        record_family=record_family,
        changed_field_names=changed_fields,
        build_plan=build_plan,
    )


def test_full_refresh_reports_all_lookup_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, _records = fixture_paths(tmp)

        result = lookup_refresh.full_lookup_refresh(source_dir, lookup_dir, repo_root)

    assert_equal(result["mode"], "full", "full mode")
    assert_equal(result["artifacts"], ["full_lookup_refresh"], "full artifacts")
    assert_equal(result["written_count"], 3, "full written count")
    assert "studio/data/generated/catalogue-lookup/meta.json" not in result["written_paths"]
    assert "studio/data/generated/catalogue-lookup/work_search.json" in result["written_paths"]
    assert "studio/data/generated/catalogue-lookup/series/009.json" in result["written_paths"]


def test_work_single_record_refresh_reports_work_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        current_record = records.works["00001"]
        updated_record = dict(current_record, provenance="After")
        lookup_plan = lookup_plan_for(
            records,
            record_family="work",
            changed_fields=["provenance"],
            current_record=current_record,
            updated_record=updated_record,
        )

        result = lookup_refresh.work_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            work_id="00001",
            current_record=current_record,
            updated_record=updated_record,
            lookup_plan=lookup_plan,
        )

    assert_equal(result["mode"], "none", "work single mode")
    assert_equal(result["artifacts"], [], "work single artifacts")
    assert_equal(result["written_count"], 0, "work single written count")
    assert_equal(result["written_paths"], [], "work single paths")
    assert_equal(result["invalidation_class"], lookup_refresh.LOOKUP_REFRESH_NONE, "work single class")


def test_work_project_subfolder_refresh_is_single_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        current_record = records.works["00001"]
        updated_record = dict(current_record, project_folder="alpha", project_subfolder="ink", project_filename="alpha.jpg")
        lookup_plan = lookup_plan_for(
            records,
            record_family="work",
            changed_fields=["project_subfolder"],
            current_record=current_record,
            updated_record=updated_record,
        )

        result = lookup_refresh.work_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            work_id="00001",
            current_record=current_record,
            updated_record=updated_record,
            lookup_plan=lookup_plan,
        )

    assert_equal(lookup_plan["unknown_fields"], [], "project_subfolder unknown fields")
    assert_equal(result["mode"], "none", "project_subfolder mode")
    assert_equal(result["artifacts"], [], "project_subfolder artifacts")
    assert_equal(result["written_count"], 0, "project_subfolder written count")


def test_unknown_registry_field_uses_full_lookup_fallback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _repo_root, _source_dir, _lookup_dir, records = fixture_paths(tmp)
        current_record = records.works["00001"]
        lookup_plan = lookup_plan_for(
            records,
            record_family="work",
            changed_fields=["unknown_work_field"],
            current_record=current_record,
            updated_record=dict(current_record, unknown_work_field="value"),
        )

    assert_equal(lookup_plan["mode"], "full", "unknown field mode")
    assert_equal(lookup_plan["artifacts"], ["full_lookup_refresh"], "unknown field artifacts")
    assert_equal(lookup_plan["unknown_fields"], ["unknown_work_field"], "unknown field list")


def test_work_targeted_refresh_reports_related_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        current_record = records.works["00001"]
        updated_record = dict(current_record, title="Alpha Updated")
        lookup_plan = lookup_plan_for(
            records,
            record_family="work",
            changed_fields=["title"],
            current_record=current_record,
            updated_record=updated_record,
        )

        result = lookup_refresh.work_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            work_id="00001",
            current_record=current_record,
            updated_record=updated_record,
            lookup_plan=lookup_plan,
        )

    assert_equal(result["mode"], "targeted-multi-record", "work targeted mode")
    assert_equal(
        result["artifacts"],
        ["related_series_records", "work_search"],
        "work targeted artifacts",
    )
    assert_equal(result["written_count"], 2, "work targeted written count")
    assert "studio/data/generated/catalogue-lookup/series/009.json" in result["written_paths"]


def test_detail_targeted_refresh_reports_detail_and_parent_work() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        updated_record = dict(records.work_details["00001-001"], title="Alpha detail updated")
        lookup_plan = lookup_plan_for(
            records,
            record_family="work_detail",
            changed_fields=["title"],
            current_record=records.work_details["00001-001"],
            updated_record=updated_record,
        )

        result = lookup_refresh.detail_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            detail_uid="00001-001",
            updated_record=updated_record,
            lookup_plan=lookup_plan,
        )

    assert_equal(result["mode"], "none", "detail targeted mode")
    assert_equal(result["artifacts"], [], "detail targeted artifacts")
    assert_equal(result["written_count"], 0, "detail targeted written count")
    assert_equal(result["written_paths"], [], "detail targeted paths")


def test_series_targeted_refresh_reports_series_search_and_member_works() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root, source_dir, lookup_dir, records = fixture_paths(tmp)
        lookup_plan = lookup_plan_for(
            records,
            record_family="series",
            changed_fields=["title"],
            current_record=records.series["009"],
            updated_record=dict(records.series["009"], title="Series Updated"),
        )

        result = lookup_refresh.series_change_lookup_refresh(
            source_dir,
            lookup_dir,
            repo_root,
            series_id="009",
            lookup_plan=lookup_plan,
        )

    assert_equal(result["mode"], "targeted-multi-record", "series targeted mode")
    assert_equal(
        result["artifacts"],
        ["series_record", "series_search"],
        "series targeted artifacts",
    )
    assert_equal(result["written_count"], 2, "series targeted written count")
    assert "studio/data/generated/catalogue-lookup/series/009.json" in result["written_paths"]


def main() -> None:
    test_full_refresh_reports_all_lookup_artifacts()
    test_work_single_record_refresh_reports_work_record()
    test_work_project_subfolder_refresh_is_single_record()
    test_unknown_registry_field_uses_full_lookup_fallback()
    test_work_targeted_refresh_reports_related_artifacts()
    test_detail_targeted_refresh_reports_detail_and_parent_work()
    test_series_targeted_refresh_reports_series_search_and_member_works()
    print("Catalogue lookup refresh tests OK")


if __name__ == "__main__":
    main()
