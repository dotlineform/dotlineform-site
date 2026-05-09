#!/usr/bin/env python3
"""Verify generated catalogue record projection helpers."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_generation_records as records  # noqa: E402


def test_work_projection_order_and_coercion() -> None:
    projected = records.build_work_record_projection(
        {
            "artist": "'Artist",
            "title": "  Work 2  ",
            "year": "2024",
            "storage_location": "",
            "height_cm": "12.5",
            "width_px": "800",
        }
    )

    assert list(projected.keys()) == [key for key, _, _ in records.WORKS_SCHEMA]
    assert projected["artist"] == "Artist"
    assert projected["title"] == "Work 2"
    assert projected["year"] == 2024
    assert projected["storage"] is None
    assert projected["height_cm"] == 12.5
    assert projected["width_px"] == 800


def test_work_series_ids_are_normalized_and_deduped() -> None:
    assert records.parse_work_record_series_ids({"series_ids": "9, 009, legacy-series, bad id"}) == [
        "009",
        "legacy-series",
    ]
    assert records.parse_work_record_series_ids({"series_ids": [9, "009", "010"]}) == ["009", "010"]


def test_canonical_work_record_orders_fields_and_prunes_public_record() -> None:
    meta = records.build_work_record_projection(
        {
            "title": "Controlled Field",
            "year": "2026",
            "year_display": "",
            "storage_location": "Rack A",
        }
    )
    meta.update(
        {
            "work_id": "00042",
            "series_ids": ["009", "010"],
            "series_id": "009",
            "series_title": "Old title",
            "title_sort": "controlled field",
        }
    )

    canonical = records.build_canonical_work_record(
        "00042",
        work_meta_by_id={"00042": meta},
        source_work_record={"links": [{"url": "https://example.test", "label": "Example"}], "downloads": []},
        series_title_by_id={"009": "Primary Series"},
        series_sort_by_series_id={"009": {"00042": "001-00042"}},
    )

    assert canonical is not None
    assert list(canonical.keys())[:8] == [
        "work_id",
        "title",
        "year",
        "year_display",
        "series_id",
        "series_ids",
        "series_title",
        "series_sort",
    ]
    assert canonical["series_title"] == "Primary Series"
    assert canonical["series_sort"] == "001-00042"
    assert canonical["links"] == [{"url": "https://example.test", "label": "Example"}]
    assert "checksum" in canonical

    public_record = records.build_work_json_record(canonical)
    assert "series_id" not in public_record
    assert "series_title" not in public_record
    assert "series_sort" not in public_record
    assert "title_sort" not in public_record
    assert "checksum" not in public_record
    assert "year_display" not in public_record
    assert public_record["series_ids"] == ["009", "010"]


def test_public_series_and_moment_records_prune_internal_fields() -> None:
    series = records.build_series_json_record(
        {
            "series_id": "009",
            "layout": "series",
            "checksum": "abc",
            "title": "Series",
            "works": ["00001"],
            "primary_work_id": "00001",
            "notes": None,
        }
    )
    assert series == {"series_id": "009", "title": "Series"}

    moment = records.build_moment_json_record(
        {
            "moment_id": "blue-room",
            "layout": "moment",
            "checksum": "abc",
            "title": "Blue Room",
            "images": [],
            "height_px": None,
        }
    )
    assert moment == {"moment_id": "blue-room", "title": "Blue Room", "images": []}

    assert records.build_moment_index_record({"moment_id": "blue-room", "title": "Blue Room", "images": []}) == {
        "moment_id": "blue-room",
        "title": "Blue Room",
    }
    assert records.build_moment_index_record({"moment_id": "blue-room", "title": "Blue Room", "images": [{}]}) == {
        "moment_id": "blue-room",
        "title": "Blue Room",
        "thumb_id": "blue-room",
    }


def test_detail_record_grouping_is_deterministic() -> None:
    detail_record = records.build_canonical_detail_record(
        "00042",
        "001",
        title="Detail one",
        section_id="b",
        section_title="B section",
        sort_order=2,
        width_px=None,
        height_px=600,
    )
    assert detail_record == {
        "work_id": "00042",
        "detail_id": "001",
        "detail_uid": "00042-001",
        "title": "Detail one",
        "section_id": "b",
        "section_title": "B section",
        "sort_order": 2,
        "height_px": 600,
    }

    sections = records.build_sections_from_detail_records(
        [
            {"detail_id": "002", "title": "Second", "section_id": "b", "section_title": "B section", "sort_order": 2},
            {"detail_id": "001", "title": "First", "section_id": "b", "section_title": "B section", "sort_order": 2},
            {"detail_id": "003", "title": "Fallback", "project_subfolder": "Details"},
            {"detail_id": "004", "title": "First section", "section_id": "a", "section_title": "A section", "sort_order": 1},
        ]
    )

    assert [section["section_id"] for section in sections] == ["a", "b", "Details"]
    assert [detail["detail_id"] for detail in sections[1]["details"]] == ["001", "002"]
    assert "section_id" not in sections[1]["details"][0]
    assert "sort_order" not in sections[1]["details"][0]


def main() -> None:
    test_work_projection_order_and_coercion()
    test_work_series_ids_are_normalized_and_deduped()
    test_canonical_work_record_orders_fields_and_prunes_public_record()
    test_public_series_and_moment_records_prune_internal_fields()
    test_detail_record_grouping_is_deterministic()
    print("Catalogue generation record tests OK")


if __name__ == "__main__":
    main()
