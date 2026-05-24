#!/usr/bin/env python3
"""Verify pure catalogue source mutation planners."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

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
                "title": "Beta",
                "year": "2026",
                "year_display": "2026",
            },
        },
        work_details={
            "00001-001": {
                "detail_uid": "00001-001",
                "work_id": "00001",
                "detail_id": "001",
                "section_id": "00001-1",
                "section_title": "Details",
                "sort_order": 1,
                "project_filename": "alpha-detail.jpg",
                "title": "Alpha detail",
                "status": "published",
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


def test_detail_save_preserves_read_only_section_id() -> None:
    records = fixture_records()

    plan = source_mutation.plan_work_detail_save(
        records,
        records.work_details,
        "00001-001",
        records.work_details["00001-001"],
        {"title": "Alpha detail updated"},
    )

    assert_equal(plan.work_id, "00001", "detail work id")
    assert_equal(plan.changed_fields, ["title"], "detail changed fields")
    assert_false(plan.validation_errors, "detail validation errors")
    assert_raises(
        "record.section_id is read-only",
        lambda: source_mutation.plan_work_detail_save(
            records,
            records.work_details,
            "00001-001",
            records.work_details["00001-001"],
            {"section_id": "00001-2"},
        ),
    )


def test_detail_create_generates_section_id() -> None:
    records = fixture_records()

    plan = source_mutation.plan_work_detail_create(
        records,
        records.work_details,
        "00001-002",
        "00001",
        "002",
        {"title": "Second detail", "section_title": "More details", "project_filename": "second.jpg"},
    )

    assert_equal(plan.updated_record["status"], "draft", "created detail status")
    assert_equal(plan.updated_record["section_id"], "00001-2", "created detail section id")
    assert_equal(plan.payload["work_details"]["00001-002"]["title"], "Second detail", "detail payload")
    assert_false(plan.validation_errors, "created detail validation errors")


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


def test_moment_save_normalizes_and_validates_metadata() -> None:
    moments = {
        "spring-note": {
            "moment_id": "spring-note",
            "title": "Spring note",
            "status": "draft",
            "date": "2026-03-01",
            "date_display": "March 2026",
            "image_alt": "Spring note",
        }
    }

    plan = source_mutation.plan_moment_save(
        moments,
        "spring-note",
        moments["spring-note"],
        {"status": "published", "published_date": "2026-03-02"},
    )

    assert_equal(plan.changed_fields, ["published_date", "status"], "moment changed fields")
    assert_equal(plan.payload["moments"]["spring-note"]["published_date"], "2026-03-02", "moment payload")
    assert_false(plan.validation_errors, "moment validation errors")


def main() -> None:
    test_work_save_plans_changed_fields_and_payload()
    test_work_create_defaults_draft_and_series_ids()
    test_detail_save_preserves_read_only_section_id()
    test_detail_create_generates_section_id()
    test_series_save_plans_member_work_updates()
    test_series_create_plans_series_and_optional_work_payload()
    test_moment_save_normalizes_and_validates_metadata()
    print("Catalogue source mutation tests OK")


if __name__ == "__main__":
    main()
