#!/usr/bin/env python3
"""Focused checks for target catalogue media section source schema rules."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from catalogue.catalogue_source import (  # noqa: E402
    CatalogueSourceRecords,
    next_detail_section_id,
    validate_source_records,
    validate_work_detail_media_section_record,
    validate_work_detail_section_metadata_consistency,
)


def source_records_with_detail(detail_record: dict) -> CatalogueSourceRecords:
    return CatalogueSourceRecords(
        works={
            "00001": {
                "work_id": "00001",
                "status": "published",
                "series_ids": [],
                "project_folder": "one",
                "project_filename": "one.jpg",
                "title": "One",
            }
        },
        work_details={"00001-001": detail_record},
        series={},
    )


def assert_target_detail_schema_accepts_new_fields() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "details_subfolder": "details",
        "section_id": "00001-1",
        "section_title": "Details",
        "sort_order": 2,
        "project_filename": "detail.jpg",
        "title": "Detail",
        "status": "draft",
    }
    errors = validate_source_records(
        source_records_with_detail(detail),
        require_detail_media_sections=True,
        allow_legacy_detail_project_subfolder=False,
    )
    assert not errors, errors


def assert_default_validation_keeps_legacy_source_readable() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "project_subfolder": "details",
        "project_filename": "detail.jpg",
        "title": "Detail",
        "status": "draft",
    }
    errors = validate_source_records(source_records_with_detail(detail))
    assert not errors, errors


def assert_target_detail_schema_rejects_legacy_field() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "project_subfolder": "details",
        "project_filename": "detail.jpg",
        "title": "Detail",
        "status": "draft",
    }
    errors = validate_work_detail_media_section_record("00001-001", detail)
    assert any("legacy project_subfolder" in error for error in errors), errors
    assert any("missing section_id" in error for error in errors), errors
    assert any("missing section_title" in error for error in errors), errors


def assert_target_detail_schema_rejects_bad_sort_order() -> None:
    detail = {
        "detail_uid": "00001-001",
        "work_id": "00001",
        "detail_id": "001",
        "section_id": "00001-1",
        "section_title": "Details",
        "sort_order": "first",
        "project_filename": "detail.jpg",
        "title": "Detail",
        "status": "draft",
    }
    errors = validate_work_detail_media_section_record("00001-001", detail)
    assert any("sort_order must be a whole number" in error for error in errors), errors


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


def assert_shared_section_id_requires_consistent_metadata() -> None:
    errors = validate_work_detail_section_metadata_consistency(
        {
            "00001-001": {
                "work_id": "00001",
                "section_id": "00001-1",
                "section_title": "Details",
                "sort_order": 1,
            },
            "00001-002": {
                "work_id": "00001",
                "section_id": "00001-1",
                "section_title": "Pages",
                "sort_order": 1,
            },
            "00001-003": {
                "work_id": "00001",
                "section_id": "00001-2",
                "section_title": "Details",
                "sort_order": 1,
            },
        }
    )
    assert len(errors) == 1, errors
    assert "00001-002" in errors[0], errors
    assert "section metadata conflicts" in errors[0], errors


def main() -> int:
    assert_target_detail_schema_accepts_new_fields()
    assert_default_validation_keeps_legacy_source_readable()
    assert_target_detail_schema_rejects_legacy_field()
    assert_target_detail_schema_rejects_bad_sort_order()
    assert_next_detail_section_id_uses_hyphen_suffix()
    assert_shared_section_id_requires_consistent_metadata()
    print("catalogue source media section schema checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
