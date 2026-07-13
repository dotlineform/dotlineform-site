#!/usr/bin/env python3
"""Verify pure catalogue source mutation planners."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from catalogue.catalogue_source import CatalogueSourceRecords  # noqa: E402
from catalogue import catalogue_source_mutation as source_mutation  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_false(value, label: str) -> None:
    if value:
        raise AssertionError(f"{label}: expected falsey value, got {value!r}")


def assert_raises(message: str, callback) -> None:
    try:
        callback()
    except ValueError as exc:
        assert_equal(str(exc), message, "error message")
        return
    raise AssertionError(f"expected ValueError: {message}")


def fixture_records() -> CatalogueSourceRecords:
    return CatalogueSourceRecords(
        works={
            "00001": {
                "work_id": "00001",
                "status": "published",
                "series_ids": ["009"],
                "project_folder": "2026/alpha",
                "project_filename": "alpha.jpg",
                "media_version": 1,
                "title": "Alpha",
                "year": "2026",
                "year_display": "2026",
            },
            "00002": {
                "work_id": "00002",
                "status": "published",
                "series_ids": [],
                "project_folder": "2026/beta",
                "project_filename": "beta.jpg",
                "media_version": 1,
                "title": "Beta",
                "year": "2026",
                "year_display": "2026",
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
                "project_filename": "alpha-detail.jpg",
                "media_version": 1,
                "title": "Alpha detail",
            }
        },
        series={
            "009": {
                "series_id": "009",
                "title": "Series",
                "status": "published",
                "year": "2026",
                "year_display": "2026",
                "primary_work_id": "00001",
            }
        },
    )


def test_work_save_plans_changed_fields_and_payload() -> None:
    records = fixture_records()

    plan = source_mutation.plan_work_save(
        records,
        records.works,
        "00001",
        records.works["00001"],
        {"title": "Alpha Updated"},
    )

    assert_equal(plan.changed_fields, ["title"], "work changed fields")
    assert_false(plan.validation_errors, "work validation errors")
    assert_equal(plan.payload["works"]["00001"]["title"], "Alpha Updated", "work payload")
    assert_equal(records.works["00001"]["title"], "Alpha", "source fixture not mutated")


def test_work_create_defaults_draft_and_series_ids() -> None:
    records = fixture_records()

    plan = source_mutation.plan_work_create(
        records,
        records.works,
        "00003",
        {"work_id": "00003", "title": "Gamma", "year": "2026", "year_display": "2026"},
    )

    assert_equal(plan.updated_record["status"], "draft", "created work status")
    assert_equal(plan.updated_record["series_ids"], [], "created work series ids")
    assert "00003" in plan.payload["works"]
    assert_false(plan.validation_errors, "created work validation errors")
    assert_raises(
        "work title is required",
        lambda: source_mutation.plan_work_create(records, records.works, "00004", {"work_id": "00004"}),
    )

    media_plan = source_mutation.plan_work_create(
        records,
        records.works,
        "00004",
        {
            "work_id": "00004",
            "title": "Delta",
            "year": "2026",
            "year_display": "2026",
            "project_folder": "2026/delta",
            "project_filename": "delta.jpg",
        },
    )
    assert_equal(media_plan.updated_record["media_version"], 1, "created work media version")


def test_detail_update_normalizes_detail_owned_fields() -> None:
    records = fixture_records()

    updated_record = source_mutation.normalize_work_detail_update(
        "00001-001",
        records.work_details["00001-001"],
        {"title": "Alpha detail updated", "project_filename": "updated.jpg"},
    )

    assert_equal(updated_record["title"], "Alpha detail updated", "detail title")
    assert_equal(updated_record["project_filename"], "updated.jpg", "detail filename")
    assert "section_title" not in updated_record
    assert "sort_order" not in updated_record


def test_series_save_plans_member_work_updates() -> None:
    records = fixture_records()

    plan = source_mutation.plan_series_save(
        records,
        records.series,
        records.works,
        "009",
        records.series["009"],
        {"title": "Series Updated"},
        [{"work_id": "00002", "series_ids": ["009"]}],
    )

    assert_equal(plan.changed_fields, ["title"], "series changed fields")
    assert_equal(plan.changed_work_ids, ["00002"], "changed work ids")
    assert_equal(plan.work_records, [{"work_id": "00002", "record": plan.work_updates["00002"]}], "work records")
    assert_equal(plan.works_payload["works"]["00002"]["series_ids"], ["009"], "works payload")
    assert_false(plan.validation_errors, "series save validation errors")


def test_series_create_plans_series_and_optional_work_payload() -> None:
    records = fixture_records()

    plan = source_mutation.plan_series_create(
        records,
        records.series,
        records.works,
        "010",
        {"title": "Draft series", "year": "2026", "year_display": "2026"},
        [],
    )

    assert_equal(plan.updated_record["status"], "draft", "created series status")
    assert_equal(plan.changed_work_ids, [], "created series changed work ids")
    assert_equal(plan.works_payload, None, "created series works payload")
    assert "010" in plan.payload["series"]
    assert_false(plan.validation_errors, "created series validation errors")


def main() -> None:
    test_work_save_plans_changed_fields_and_payload()
    test_work_create_defaults_draft_and_series_ids()
    test_detail_update_normalizes_detail_owned_fields()
    test_series_save_plans_member_work_updates()
    test_series_create_plans_series_and_optional_work_payload()
    print("Catalogue source mutation tests OK")


if __name__ == "__main__":
    main()
