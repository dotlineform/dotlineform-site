#!/usr/bin/env python3
"""Focused checks for target catalogue media section source schema rules."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "studio/services"))

from catalogue.catalogue_source import (  # noqa: E402
    CatalogueSourceRecords,
    next_detail_section_id,
    validate_source_records,
    validate_work_detail_media_section_record,
    validate_work_detail_section_record,
)


def source_records_with_detail(detail_record: dict, section_record: dict | None = None) -> CatalogueSourceRecords:
    section = section_record or {
        "section_id": "00001-1",
        "work_id": "00001",
        "details_subfolder": "details",
        "section_title": "Details",
        "section_order": None,
        "detail_sort": None,
    }
    normalized_detail = dict(detail_record)
    if normalized_detail.get("project_filename") and not normalized_detail.get("media_version"):
        normalized_detail["media_version"] = 1
    return CatalogueSourceRecords(
        works={
            "00001": {
                "work_id": "00001",
                "status": "published",
                "series_ids": [],
                "project_folder": "one",
                "project_filename": "one.jpg",
                "media_version": 1,
                "title": "One",
            }
        },
        work_detail_sections={str(section["section_id"]): section},
        work_details={"00001-001": normalized_detail},
        series={},
    )


def assert_target_detail_schema_accepts_new_fields() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "section_id": "00001-1",
        "project_filename": "detail.jpg",
        "title": "Detail",
    }
    errors = validate_source_records(
        source_records_with_detail(detail),
        require_detail_media_sections=True,
        allow_compat_detail_project_subfolder=False,
    )
    assert not errors, errors


def assert_detail_schema_rejects_retired_detail_section_fields() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "details_subfolder": "details",
        "section_id": "00001-1",
        "section_title": "Details",
        "sort_order": 1,
        "project_filename": "detail.jpg",
        "title": "Detail",
    }
    errors = validate_source_records(source_records_with_detail(detail))
    assert any("details_subfolder is section metadata" in error for error in errors), errors
    assert any("section_title is section metadata" in error for error in errors), errors
    assert any("sort_order is section metadata" in error for error in errors), errors


def assert_target_detail_schema_rejects_compat_subfolder_field() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "project_subfolder": "details",
        "project_filename": "detail.jpg",
        "title": "Detail",
    }
    errors = validate_work_detail_media_section_record("00001-001", detail)
    assert any("project_subfolder is not supported" in error for error in errors), errors
    assert any("missing section_id" in error for error in errors), errors


def assert_target_section_schema_rejects_bad_section_order() -> None:
    section = {
        "section_id": "00001-1",
        "work_id": "00001",
        "section_title": "Details",
        "section_order": "first",
    }
    errors = validate_work_detail_section_record("00001-1", section)
    assert any("section_order must be a whole number" in error for error in errors), errors


def assert_next_detail_section_id_uses_hyphen_suffix() -> None:
    next_id = next_detail_section_id(
        "00001",
        [
            {"work_id": "00001", "section_id": "00001-1"},
            {"work_id": "00001", "section_id": "00001-2"},
            {"work_id": "00002", "section_id": "00002-9"},
        ],
    )
    assert next_id == "00001-3"


def assert_media_version_is_required_for_media_records() -> None:
    records = source_records_with_detail(
        {
            "detail_uid": "00001-001",
            "work_id": "00001",
            "detail_id": "001",
            "section_id": "00001-1",
            "project_filename": "detail.jpg",
            "title": "Detail",
        }
    )
    records.works["00001"].pop("media_version")
    records.work_details["00001-001"].pop("media_version")
    errors = validate_source_records(records)
    assert any("works 00001: media_version is required" in error for error in errors), errors
    assert any("work_details 00001-001: media_version is required" in error for error in errors), errors


def assert_detail_section_id_must_match_section_work() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "section_id": "00002-1",
        "project_filename": "detail.jpg",
        "title": "Detail",
    }
    section = {
        "section_id": "00002-1",
        "work_id": "00002",
        "details_subfolder": "details",
        "section_title": "Details",
    }
    errors = validate_source_records(source_records_with_detail(detail, section))
    assert any("belongs to work_id '00002'" in error for error in errors), errors


def main() -> int:
    assert_target_detail_schema_accepts_new_fields()
    assert_detail_schema_rejects_retired_detail_section_fields()
    assert_target_detail_schema_rejects_compat_subfolder_field()
    assert_target_section_schema_rejects_bad_section_order()
    assert_next_detail_section_id_uses_hyphen_suffix()
    assert_media_version_is_required_for_media_records()
    assert_detail_section_id_must_match_section_work()
    print("catalogue source media section schema checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
