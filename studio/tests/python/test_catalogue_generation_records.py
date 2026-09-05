#!/usr/bin/env python3
"""Verify generated catalogue record projection helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from catalogue import catalogue_generation_records as records  # noqa: E402


def test_work_projection_order_and_coercion() -> None:
    projected = records.build_work_record_projection(
        {
            "artist": "'Artist",
            "title": "  Work 2  ",
            "year": "2024",
            "height_cm": "12.5",
            "width_px": "800",
            "media_version": "2",
        }
    )

    assert list(projected.keys()) == [key for key, _, _ in records.WORKS_SCHEMA]
    assert projected["artist"] == "Artist"
    assert projected["title"] == "Work 2"
    assert projected["year"] == 2024
    assert projected["height_cm"] == 12.5
    assert projected["width_px"] == 800
    assert projected["media_version"] == 2


def test_generated_documents_are_sorted_deduped_and_versioned() -> None:
    document_a = {"url": "/a", "title": "A"}
    document_z = {"url": "/z", "title": "Z"}
    series_document = {"url": "/series", "title": "Series note"}
    work = {"work_id": "00042", "title": "Work", "documents": [document_z, document_a, document_a]}
    series = {"series_id": "009", "title": "Series", "documents": [series_document]}
    with pytest.raises(ValueError, match="documents must be an array"):
        records.normalize_catalogue_documents("/not-an-array")
    with pytest.raises(ValueError, match="conflicting titles"):
        records.normalize_catalogue_documents(
            [document_a, {"url": "/a", "title": "Different"}]
        )

    work_payload = records.build_work_json_payload(
        work_id="00042",
        work_record=work,
        sections=[],
        generated_at_utc="2026-08-09T20:00:00Z",
        count=0,
    )
    assert work_payload["header"]["schema"] == "work_record_v6"
    assert work_payload["work"]["documents"] == [document_a, document_z]
    changed_work_payload = records.build_work_json_payload(
        work_id="00042",
        work_record={**work, "documents": [document_a]},
        sections=[],
        generated_at_utc="2026-08-09T20:00:00Z",
        count=0,
    )
    assert work_payload["header"]["version"] != changed_work_payload["header"]["version"]
    assert "content_html" not in work_payload

    series_payload = records.build_series_json_payload(
        series_id="009",
        series_record=series,
        member_works=[{"work_id": "00001", "title": "Only", "year": 2026, "year_display": "2026"}],
        generated_at_utc="2026-08-09T20:00:00Z",
    )
    assert series_payload["header"]["schema"] == "series_record_v5"
    assert series_payload["header"]["count"] == 1
    assert series_payload["series"]["documents"] == [series_document]
    assert series_payload["member_works"] == [
        {"work_id": "00001", "title": "Only", "year": 2026, "year_display": "2026"}
    ]
    assert "content_html" not in series_payload
    with pytest.raises(ValueError, match="must match exact payload target 010"):
        records.build_series_json_payload(
            series_id="010",
            series_record=series,
            member_works=[],
            generated_at_utc="2026-08-09T20:00:00Z",
        )


def test_detail_record_preserves_exact_identity_and_media() -> None:
    detail_record = records.build_canonical_detail_record(
        "00042",
        "001",
        title="Detail one",
        width_px=None,
        height_px=600,
        media_version=4,
    )
    assert detail_record == {
        "work_id": "00042",
        "detail_id": "001",
        "detail_uid": "00042-001",
        "title": "Detail one",
        "height_px": 600,
        "media_version": 4,
    }
