"""Data-oriented fixtures for Studio catalogue tests."""

from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, payload: object, *, sort_keys: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8")


def write_catalogue_source(repo_root: Path):
    """Write two Works and two Series with the current schema-only source serializer."""
    from catalogue.catalogue_source import CatalogueSourceRecords, SOURCE_FILES, payload_for_map

    records = CatalogueSourceRecords(
        works={
            "00001": {"work_id": "00001", "title": "Alpha", "year": 2026, "year_display": "2026", "series_id": "009", "project_folder": "alpha", "project_filename": "cover.jpg", "media_version": 1},
            "00002": {"work_id": "00002", "title": "Beta", "year": 2026, "year_display": "2026"},
        },
        series={
            "009": {"series_id": "009", "title": "First", "year": 2026, "year_display": "2026", "sort_fields": "-title"},
            "010": {"series_id": "010", "title": "Empty", "year": 2026, "year_display": "2026"},
        },
    )
    source_dir = repo_root / "studio/data/canonical/catalogue"
    for kind, record_map in records.as_maps().items():
        write_json(source_dir / SOURCE_FILES[kind], payload_for_map(kind, record_map))
    return source_dir
