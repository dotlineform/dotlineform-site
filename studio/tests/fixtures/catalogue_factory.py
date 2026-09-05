"""Data-oriented fixtures for Studio catalogue tests."""

from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, payload: object, *, sort_keys: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_catalogue_source(repo_root: Path):
    """Two Works, two Series and one exact Detail aggregate for service tests."""
    from catalogue.catalogue_source import CatalogueSourceRecords, write_source_record_payloads

    records = CatalogueSourceRecords(
        works={
            "00001": {"work_id": "00001", "title": "Alpha", "year": 2026, "year_display": "2026", "series_id": "009", "project_folder": "alpha", "project_filename": "cover.jpg", "media_version": 1},
            "00002": {"work_id": "00002", "title": "Beta", "year": 2026, "year_display": "2026"},
        },
        series={
            "009": {"series_id": "009", "title": "First", "year": 2026, "year_display": "2026", "sort_fields": "-title"},
            "010": {"series_id": "010", "title": "Empty", "year": 2026, "year_display": "2026"},
        },
        work_detail_sections={"00001-1": {"section_id": "00001-1", "work_id": "00001", "section_title": "Details", "details_subfolder": "details"}},
        work_details={"00001-001": {"detail_uid": "00001-001", "detail_id": "001", "work_id": "00001", "section_id": "00001-1", "project_filename": "detail.jpg", "media_version": 1, "title": "Detail"}},
    )
    source_dir = repo_root / "studio/data/canonical/catalogue"
    write_source_record_payloads(source_dir, records)
    return source_dir
