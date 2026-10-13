from __future__ import annotations

from typing import Any, Dict, Mapping

from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_source import CatalogueSourceRecords, normalize_text, work_resource_entries

SCHEMAS = {
    "work_search": "studio_catalogue_lookup_work_search_v2",
    "series_search": "studio_catalogue_lookup_series_search_v2",
    "work_record": "studio_catalogue_work_record_v3",
}

WORK_SEARCH_FIELDS = frozenset({"work_id", "title", "year_display", "series_id", "media_version", "image_staged"})
SERIES_SEARCH_FIELDS = frozenset({"series_id", "title"})
WORK_SERIES_SUMMARY_FIELDS = frozenset({"title"})


def build_work_search_item(work_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    """Project canonical fields for Work search and versioned Series thumbnails."""
    return {
        "work_id": work_id,
        "record_hash": record_hash(record),
        "title": record["title"],
        "year_display": record["year_display"],
        "series_id": record.get("series_id"),
        "media_version": record.get("media_version"),
        "image_staged": record["image_staged"],
    }


def build_series_search_item(series_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "series_id": series_id,
        "record_hash": record_hash(record),
        "title": record["title"],
    }


def build_work_lookup_payload(records: CatalogueSourceRecords, work_id: str) -> Dict[str, Any]:
    record = records.works.get(work_id)
    if not isinstance(record, Mapping):
        raise KeyError(f"work_id not found: {work_id}")

    series_title_by_id = {
        series_id: normalize_text(series_record.get("title"))
        for series_id, series_record in records.series.items()
    }

    series_summary = [
        {
            "series_id": series_id,
            "title": series_title_by_id[series_id],
        }
        for series_id in ([record["series_id"]] if record.get("series_id") is not None else [])
    ]

    return {
        "header": {
            "schema": SCHEMAS["work_record"],
        },
        "work": dict(record),
        "record_hash": record_hash(record),
        "downloads": list(work_resource_entries(record, "downloads")),
        "links": list(work_resource_entries(record, "links")),
        "series_summary": series_summary,
    }


def build_work_search_payload(records: CatalogueSourceRecords) -> Dict[str, Any]:
    items = []
    for work_id, record in records.works.items():
        items.append(build_work_search_item(work_id, record))
    items.sort(key=lambda item: item["work_id"])
    return {
        "header": {
            "schema": SCHEMAS["work_search"],
            "count": len(items),
        },
        "items": items,
    }


def build_series_search_payload(records: CatalogueSourceRecords) -> Dict[str, Any]:
    items = []
    for series_id, record in records.series.items():
        items.append(build_series_search_item(series_id, record))
    items.sort(key=lambda item: item["series_id"])
    return {
        "header": {
            "schema": SCHEMAS["series_search"],
            "count": len(items),
        },
        "items": items,
    }
