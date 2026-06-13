"""Moment-build invalidation helpers."""

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

# Canonical build invalidation registry for moment-source fields.
# Moments are part of the catalogue surface, but their current derived artifacts are
# `site/assets/moments/index/<moment_id>.json`, `site/assets/data/moments_index.json`, and
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


def moment_build_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, MOMENT_BUILD_INVALIDATION_REGISTRY)
