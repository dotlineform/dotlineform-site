from __future__ import annotations

from typing import Any, Dict, Mapping

SCHEMAS = {
    "work_search": "studio_catalogue_lookup_work_search_v3",
    "series_search": "studio_catalogue_lookup_series_search_v2",
    "work_record": "studio_catalogue_work_record_v3",
}

WORK_SEARCH_FIELDS = frozenset({"work_id", "title", "year", "year_display", "series_id", "media_version", "image_staged"})
SERIES_SEARCH_FIELDS = frozenset({"series_id", "title"})


def build_work_search_item(work_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    """Project canonical fields for Work search and versioned Series thumbnails."""
    return {
        "work_id": work_id,
        "title": record["title"],
        "year": record["year"],
        "year_display": record["year_display"],
        "series_id": record.get("series_id"),
        "media_version": record.get("media_version"),
        "image_staged": record["image_staged"],
    }


def build_series_search_item(series_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    """Project the saved identity/title consumed by Series authoring controls."""
    return {
        "series_id": series_id,
        "title": record["title"],
    }


def build_work_lookup_payload(works: Mapping[str, Mapping[str, Any]], work_id: str) -> Dict[str, Any]:
    """Build one Work response from the supplied Work map without Series inputs."""
    record = works.get(work_id)
    if not isinstance(record, Mapping):
        raise KeyError(f"work_id not found: {work_id}")

    return {
        "header": {
            "schema": SCHEMAS["work_record"],
        },
        "work": dict(record),
    }


def work_medium_values(works: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Project distinct nonempty authored values from supplied records without reads."""
    return list(dict.fromkeys(record["medium"] for record in works.values() if record.get("medium")))


def build_work_search_payload(works: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    """Project Work search and Medium suggestions from one supplied Work map."""
    items = []
    for work_id, record in works.items():
        items.append(build_work_search_item(work_id, record))
    items.sort(key=lambda item: item["work_id"])
    return {
        "header": {
            "schema": SCHEMAS["work_search"],
            "count": len(items),
        },
        "items": items,
        "medium_values": work_medium_values(works),
    }


def build_series_search_payload(series: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    """Project Series search from one supplied Series map."""
    items = []
    for series_id, record in series.items():
        items.append(build_series_search_item(series_id, record))
    items.sort(key=lambda item: item["series_id"])
    return {
        "header": {
            "schema": SCHEMAS["series_search"],
            "count": len(items),
        },
        "items": items,
    }
