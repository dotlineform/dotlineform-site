from __future__ import annotations

from typing import Any, Dict, Mapping

from catalogue import catalogue_generation_indexes as generation_indexes
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_source import CatalogueSourceRecords, normalize_text

SCHEMAS = {
    "work_search": "studio_catalogue_lookup_work_search_v2",
    "series_search": "studio_catalogue_lookup_series_search_v2",
    "work_record": "studio_catalogue_work_record_v3",
    "series_record": "studio_catalogue_lookup_series_record_v3",
}

WORK_SEARCH_FIELDS = frozenset({"work_id", "title", "year_display", "series_id", "media_version"})
SERIES_MEMBER_WORK_FIELDS = frozenset({
    "work_id",
    "title",
    "year",
    "year_display",
    "series_id",
    "project_folder",
})
SERIES_SEARCH_FIELDS = frozenset({"series_id", "title"})
WORK_SERIES_SUMMARY_FIELDS = frozenset({"title"})


def normalize_optional_int(value: Any) -> int | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def build_work_search_item(work_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    """Project canonical fields for Work search and versioned Series thumbnails."""
    return {
        "work_id": work_id,
        "record_hash": record_hash(record),
        "title": normalize_text(record.get("title")),
        "year_display": normalize_text(record.get("year_display")),
        "series_id": normalize_text(record.get("series_id")) or None,
        "media_version": record.get("media_version"),
    }


def build_series_member_work_item(work_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "work_id": work_id,
        "record_hash": record_hash(record),
        "title": normalize_text(record.get("title")),
        "year": normalize_optional_int(record.get("year")),
        "year_display": normalize_text(record.get("year_display")),
        "series_id": normalize_text(record.get("series_id")) or None,
        "project_folder": normalize_text(record.get("project_folder")),
    }


def build_series_search_item(series_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "series_id": series_id,
        "record_hash": record_hash(record),
        "title": normalize_text(record.get("title")),
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
            "title": series_title_by_id.get(series_id, ""),
        }
        for series_id in ([record["series_id"]] if record.get("series_id") else [])
    ]

    return {
        "header": {
            "schema": SCHEMAS["work_record"],
        },
        "work": dict(record),
        "record_hash": record_hash(record),
        "downloads": list(record.get("downloads", [])) if isinstance(record.get("downloads"), list) else [],
        "links": list(record.get("links", [])) if isinstance(record.get("links"), list) else [],
        "series_summary": series_summary,
    }


def build_series_lookup_payload(
    records: CatalogueSourceRecords,
    series_id: str,
    *,
    context: generation_indexes.SeriesWorkIndexContext | None = None,
) -> Dict[str, Any]:
    record = records.series.get(series_id)
    if not isinstance(record, Mapping):
        raise KeyError(f"series_id not found: {series_id}")

    series_context = context or generation_indexes.build_series_work_index_context(
        series_records=records.series,
        work_records=records.works,
    )
    ordered_work_ids = generation_indexes.ordered_work_ids_by_series(series_context).get(
        series_id,
        [],
    )

    members = []
    for work_id, work_record in records.works.items():
        if work_record.get("series_id") != series_id:
            continue
        members.append(build_series_member_work_item(work_id, work_record))
    members.sort(key=lambda item: item["work_id"])

    return {
        "header": {
            "schema": SCHEMAS["series_record"],
        },
        "series": dict(record),
        "record_hash": record_hash(record),
        "member_works": members,
        "ordered_work_ids": ordered_work_ids,
        "project_folders": list(series_context.series_project_folders_by_id.get(series_id, [])),
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
