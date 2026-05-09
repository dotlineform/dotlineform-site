#!/usr/bin/env python3
"""Verify generated catalogue index builders."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import catalogue_generation_indexes as indexes  # noqa: E402


def sample_series_records() -> dict[str, dict[str, object]]:
    return {
        "009": {
            "series_id": "009",
            "status": "published",
            "title": "Numbered Works",
            "sort_fields": "title",
            "primary_work_id": "2",
            "published_date": "2026-5-1",
        },
        "010": {
            "series_id": "010",
            "status": "published",
            "title": "Year Works",
            "sort_fields": "-year,title",
            "primary_work_id": "4",
        },
        "011": {
            "series_id": "011",
            "status": "draft",
            "title": "Draft Series",
            "primary_work_id": "5",
        },
    }


def sample_work_records() -> dict[str, dict[str, object]]:
    return {
        "00001": {
            "work_id": "1",
            "status": "published",
            "title": "Work 10",
            "year": "2021",
            "series_ids": "009",
            "project_folder": "Beta",
        },
        "00002": {
            "work_id": "2",
            "status": "published",
            "title": "Work 2",
            "year": "2022",
            "series_ids": "009, 010",
            "project_folder": "alpha",
        },
        "00003": {
            "work_id": "3",
            "status": "draft",
            "title": "Work 1",
            "year": "2023",
            "series_ids": "009",
            "project_folder": "Beta",
        },
        "00004": {
            "work_id": "4",
            "status": "published",
            "title": "Work 20",
            "year": "2024",
            "series_ids": "010",
            "project_folder": "Gamma",
        },
        "00005": {
            "work_id": "5",
            "status": "published",
            "title": "Draft Series Work",
            "year": "2020",
            "series_ids": "011",
        },
    }


def test_series_context_sorts_title_aliases_and_numeric_values() -> None:
    context = indexes.build_series_work_index_context(
        series_records=sample_series_records(),
        work_records=sample_work_records(),
    )

    assert context.series_title_by_id["009"] == "Numbered Works"
    assert context.series_status_by_id["011"] == "draft"
    assert context.series_project_folders_by_id["009"] == ["alpha", "Beta"]
    assert context.series_sort_fields_by_series_id["009"] == ["title", "work_id"]
    assert context.series_sort_fields_by_series_id["010"] == ["-year", "title", "work_id"]
    assert context.series_sort_by_series_id["009"] == {
        "00003": "001-00003",
        "00002": "002-00002",
        "00001": "003-00001",
    }
    assert context.series_sort_by_series_id["010"] == {
        "00004": "001-00004",
        "00002": "002-00002",
    }


def test_series_index_payload_is_published_only_and_validates_primary_work() -> None:
    context = indexes.build_series_work_index_context(
        series_records=sample_series_records(),
        work_records=sample_work_records(),
    )
    payload = indexes.build_series_index_payload(
        series_records=sample_series_records(),
        context=context,
        generated_at_utc="2026-05-09T12:00:00Z",
    )

    assert payload["header"]["schema"] == "series_index_v2"
    assert payload["header"]["generated_at_utc"] == "2026-05-09T12:00:00Z"
    assert payload["header"]["count"] == 2
    assert list(payload["series"].keys()) == ["009", "010"]
    assert payload["series"]["009"]["works"] == ["00002", "00001"]
    assert payload["series"]["009"]["primary_work_id"] == "00002"
    assert payload["series"]["009"]["published_date"] == "2026-05-01"
    assert payload["series"]["010"]["works"] == ["00004", "00002"]
    assert "011" not in payload["series"]

    broken_records = sample_series_records()
    broken_records["009"] = dict(broken_records["009"], primary_work_id="3")
    broken_context = indexes.build_series_work_index_context(
        series_records=broken_records,
        work_records=sample_work_records(),
    )
    try:
        indexes.build_series_index_payload(
            series_records=broken_records,
            context=broken_context,
            generated_at_utc="2026-05-09T12:00:00Z",
        )
    except indexes.CatalogueGenerationIndexError as exc:
        assert "primary_work_id '00003' is not in its works list" in str(exc)
    else:
        raise AssertionError("expected primary-work validation failure")

    missing_records = sample_series_records()
    missing_records["009"] = {key: value for key, value in missing_records["009"].items() if key != "primary_work_id"}
    missing_context = indexes.build_series_work_index_context(
        series_records=missing_records,
        work_records=sample_work_records(),
    )
    try:
        indexes.build_series_index_payload(
            series_records=missing_records,
            context=missing_context,
            generated_at_utc="2026-05-09T12:00:00Z",
        )
    except indexes.CatalogueGenerationIndexError as exc:
        assert "missing primary_work_id" in str(exc)
    else:
        raise AssertionError("expected missing primary-work validation failure")


def test_works_and_storage_index_payloads() -> None:
    work_records = {
        "00001": {"work_id": "1", "status": "published"},
        "00002": {"work_id": "2", "status": "draft"},
        "00003": {"work_id": "3", "status": "archived"},
        "00004": {"work_id": "4", "status": "published"},
    }
    canonical = {
        "00001": {
            "work_id": "00001",
            "title": "Stored Work",
            "year": 2024,
            "series_ids": ["009"],
            "storage": "Shelf A",
        },
        "00002": {
            "work_id": "00002",
            "title": "Draft Work",
            "year_display": "ongoing",
            "series_ids": [],
            "storage": "",
        },
        "00003": {
            "work_id": "00003",
            "title": "Archived Work",
            "year": 2020,
            "series_ids": ["010"],
            "storage": "Shelf Z",
        },
    }

    works = indexes.build_works_index_records(
        work_records=work_records,
        canonical_work_record_by_id=canonical,
    )
    assert works == {
        "00001": {
            "work_id": "00001",
            "title": "Stored Work",
            "year": 2024,
            "year_display": "2024",
            "series_ids": ["009"],
        },
        "00002": {
            "work_id": "00002",
            "title": "Draft Work",
            "year_display": "ongoing",
            "series_ids": [],
        },
    }

    works_payload = indexes.build_works_index_payload(
        works=works,
        generated_at_utc="2026-05-09T12:30:00Z",
    )
    assert works_payload["header"]["schema"] == "works_index_v4"
    assert works_payload["header"]["count"] == 2
    assert works_payload["works"] == works

    storage = indexes.build_work_storage_index_records(
        works=works,
        canonical_work_record_by_id=canonical,
    )
    assert storage == {"00001": {"storage": "Shelf A"}}

    storage_payload = indexes.build_work_storage_index_payload(
        works=storage,
        generated_at_utc="2026-05-09T12:30:00Z",
    )
    assert storage_payload["header"]["schema"] == "work_storage_index_v1"
    assert storage_payload["header"]["count"] == 1
    assert storage_payload["works"] == storage


def main() -> None:
    test_series_context_sorts_title_aliases_and_numeric_values()
    test_series_index_payload_is_published_only_and_validates_primary_work()
    test_works_and_storage_index_payloads()
    print("Catalogue generation index tests OK")


if __name__ == "__main__":
    main()
