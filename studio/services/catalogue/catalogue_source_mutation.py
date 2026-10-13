"""Pure source-record mutation planners for catalogue write paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from catalogue.catalogue_source import (
    MEDIA_VERSION_FIELD,
    WORK_FIELDS,
    WORK_TEXT_FIELDS,
    normalize_source_record,
    is_empty,
    payload_for_map,
    work_resource_entries,
)


@dataclass(frozen=True)
class SourceRecordPlan:
    baseline_record: Dict[str, Any]
    updated_record: Dict[str, Any]
    changed_fields: list[str]
    payload: Dict[str, Any]

    @property
    def changed(self) -> bool:
        return bool(self.changed_fields)


def normalize_work_update(work_id: str, current_record: Mapping[str, Any], update: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    # Operational location flags remain server-owned across metadata edits.
    merged["image_staged"] = current_record.get("image_staged", False)
    if merged["image_staged"] is None:
        merged["image_staged"] = False
    prior_downloads = {item["filename"]: item for item in work_resource_entries(current_record, "downloads")}
    merged["downloads"] = [
        {**item, "staged": prior_downloads.get(item["filename"], {}).get("staged", False)}
        for item in work_resource_entries(merged, "downloads")
    ]
    if "work_id" in update and update["work_id"] != work_id:
        raise ValueError("record.work_id must match work_id")
    merged["work_id"] = work_id

    if not is_empty(merged.get("project_filename")) and is_empty(merged.get(MEDIA_VERSION_FIELD)):
        merged[MEDIA_VERSION_FIELD] = 1

    return normalize_source_record(merged, WORK_FIELDS, text_fields=WORK_TEXT_FIELDS)


def changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return [field for field in sorted(set(before.keys()) | set(after.keys())) if before.get(field) != after.get(field)]


def plan_work_save(
    works: Mapping[str, Dict[str, Any]],
    work_id: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> SourceRecordPlan:
    updated_record = normalize_work_update(work_id, current_record, update)
    fields_changed = changed_fields(current_record, updated_record)
    updated_works = dict(works)
    updated_works[work_id] = updated_record
    return SourceRecordPlan(
        baseline_record=dict(current_record),
        updated_record=updated_record,
        changed_fields=fields_changed,
        payload=payload_for_map("works", updated_works),
    )


def plan_work_create(
    works: Mapping[str, Dict[str, Any]],
    work_id: str,
    update: Mapping[str, Any],
) -> SourceRecordPlan:
    blank_record = {field: None for field in WORK_FIELDS if field not in {"downloads", "links"}}
    blank_record["work_id"] = work_id
    normalized_update = dict(update)
    created_record = normalize_work_update(work_id, blank_record, normalized_update)
    updated_works = dict(works)
    updated_works[work_id] = created_record
    return SourceRecordPlan(
        baseline_record=blank_record,
        updated_record=created_record,
        changed_fields=changed_fields(blank_record, created_record),
        payload=payload_for_map("works", updated_works),
    )


def plan_series_save(
    series: Mapping[str, Dict[str, Any]],
    series_id: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> SourceRecordPlan:
    """Plan a title-only definition write from UI-authored values."""
    updated_record = {"series_id": series_id, "title": update["title"]}
    updated_series = dict(series)
    updated_series[series_id] = updated_record
    return SourceRecordPlan(
        baseline_record=dict(current_record),
        updated_record=updated_record,
        changed_fields=changed_fields(current_record, updated_record),
        payload=payload_for_map("series", updated_series),
    )


def plan_series_create(
    series: Mapping[str, Dict[str, Any]],
    series_id: str,
    update: Mapping[str, Any],
) -> SourceRecordPlan:
    """Create an empty Series; Work assignment belongs to Work Save."""
    return plan_series_save(series, series_id, {"series_id": series_id, "title": None}, update)
