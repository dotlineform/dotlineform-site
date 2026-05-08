"""Catalogue lookup and moment-build invalidation rules."""

from __future__ import annotations

from typing import Any, Dict, Mapping


LOOKUP_INVALIDATION_SINGLE_RECORD = "single-record"
LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD = "targeted-multi-record"
LOOKUP_INVALIDATION_FULL = "full"

LOOKUP_INVALIDATION_PRIORITY = {
    LOOKUP_INVALIDATION_SINGLE_RECORD: 0,
    LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD: 1,
    LOOKUP_INVALIDATION_FULL: 2,
}

# Canonical invalidation registry for work-source fields.
# This is the source of truth for Task 1 and stays in code for now.
# A later task can externalize it to JSON/config once the dependency model stabilizes.
WORK_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "project_folder": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "project_filename": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "year": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "medium_type": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "medium_caption": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "duration": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "height_cm": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "width_cm": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "depth_cm": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "storage_location": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "notes": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "provenance": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "artist": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "downloads": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "links": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": [
            "work_record",
            "work_search",
            "related_series_records",
            "related_work_detail_records",
        ],
    },
    "year_display": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_record", "work_search", "related_series_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_record", "work_search", "related_series_records"],
    },
    "series_ids": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_record", "work_search", "related_series_records"],
    },
}

# Canonical invalidation registry for work-detail source fields.
# Derived artifacts come from `assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`,
# `assets/studio/data/catalogue_lookup/work_detail_search.json`, and the focused
# work lookup record where detail sections are embedded.
DETAIL_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "project_filename": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "height_px": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "width_px": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "details_subfolder": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "related_work_records"],
    },
    "section_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "related_work_records"],
    },
    "section_title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "related_work_records"],
    },
    "sort_order": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "related_work_records"],
    },
    "detail_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "work_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "detail_uid": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
}

# Canonical invalidation registry for series source fields.
# Derived artifacts come from `assets/studio/data/catalogue_lookup/series/<series_id>.json`,
# `assets/studio/data/catalogue_lookup/series_search.json`, and work lookup records where
# `series_summary` embeds the current series title.
SERIES_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "year": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "year_display": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "series_type": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "notes": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "sort_fields": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search", "related_work_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search"],
    },
    "primary_work_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search"],
    },
    "series_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search", "related_work_records"],
    },
}

# Canonical build invalidation registry for moment-source fields.
# Moments are part of the catalogue surface, but their current derived artifacts are
# `assets/moments/index/<moment_id>.json`, `assets/data/moments_index.json`, and
# catalogue search entries built from `moments_index.json`, not Studio catalogue lookup payloads.
MOMENT_BUILD_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "status": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "image_alt": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "source_image_file": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["moment_record", "moments_index", "catalogue_search"],
    },
    "date": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["moment_record", "moments_index", "catalogue_search"],
    },
    "date_display": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["moment_record", "moments_index", "catalogue_search"],
    },
}

LOOKUP_INVALIDATION_FULL_FALLBACK_OPERATIONS = {
    "catalogue.bulk_save",
    "catalogue.delete_apply",
    "catalogue.import_apply",
    "catalogue.work_create",
    "catalogue.work_detail_create",
    "catalogue.series_create",
    "catalogue.moment_save",
}


def lookup_invalidation_for_fields(
    changed_field_names: list[str],
    registry: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    changed = sorted({str(name).strip() for name in changed_field_names if str(name).strip()})
    if not changed:
        return {
            "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
            "artifacts": [],
            "fields": [],
            "unknown_fields": [],
        }

    invalidation_class = LOOKUP_INVALIDATION_SINGLE_RECORD
    artifacts: set[str] = set()
    unknown_fields: list[str] = []

    for field_name in changed:
        entry = registry.get(field_name)
        if not entry:
            unknown_fields.append(field_name)
            invalidation_class = LOOKUP_INVALIDATION_FULL
            continue
        entry_class = str(entry.get("class") or LOOKUP_INVALIDATION_FULL)
        if LOOKUP_INVALIDATION_PRIORITY.get(entry_class, LOOKUP_INVALIDATION_PRIORITY[LOOKUP_INVALIDATION_FULL]) > LOOKUP_INVALIDATION_PRIORITY[invalidation_class]:
            invalidation_class = entry_class
        for artifact in entry.get("artifacts") or []:
            artifacts.add(str(artifact))

    if unknown_fields:
        artifacts.add("full_lookup_refresh")

    return {
        "class": invalidation_class,
        "artifacts": sorted(artifacts),
        "fields": changed,
        "unknown_fields": unknown_fields,
    }


def work_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, WORK_LOOKUP_INVALIDATION_REGISTRY)


def detail_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, DETAIL_LOOKUP_INVALIDATION_REGISTRY)


def series_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, SERIES_LOOKUP_INVALIDATION_REGISTRY)


def moment_build_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, MOMENT_BUILD_INVALIDATION_REGISTRY)
