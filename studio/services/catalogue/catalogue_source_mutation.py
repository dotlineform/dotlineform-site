"""Pure source-record mutation planners for catalogue write paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from catalogue.catalogue_source import (
    MEDIA_VERSION_FIELD,
    SERIES_FIELDS,
    SERIES_TEXT_FIELDS,
    WORK_FIELDS,
    WORK_TEXT_FIELDS,
    normalize_source_record,
    normalize_text,
    is_empty,
    payload_for_map,
    work_resource_entries,
)
from catalogue.series_ids import normalize_series_id
from catalogue.catalogue_revisions import record_hash, require_record_revision


@dataclass(frozen=True)
class SourceRecordPlan:
    baseline_record: Dict[str, Any]
    updated_record: Dict[str, Any]
    changed_fields: list[str]
    payload: Dict[str, Any]

    @property
    def changed(self) -> bool:
        return bool(self.changed_fields)


@dataclass(frozen=True)
class SeriesPlan(SourceRecordPlan):
    validation_errors: list[str]
    changed_work_ids: list[str]
    work_updates: Dict[str, Dict[str, Any]]
    work_records: list[Dict[str, Any]]
    works_payload: Dict[str, Any] | None = None

    @property
    def changed(self) -> bool:
        return bool(self.changed_fields or self.changed_work_ids)


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


def normalize_series_update(
    series_id: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["series_id"] = normalize_series_id(merged.get("series_id") or series_id)
    if merged["series_id"] != series_id:
        raise ValueError("record.series_id must match series_id")
    return normalize_source_record(merged, SERIES_FIELDS, text_fields=SERIES_TEXT_FIELDS)


def validate_series_save_record(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not normalize_text(record.get("title")):
        errors.append("series title is required")
    return errors


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


def _plan_series_work_updates(
    works: Mapping[str, Dict[str, Any]],
    work_updates_request: list[Dict[str, Any]],
) -> tuple[Dict[str, Dict[str, Any]], list[str], list[Dict[str, Any]]]:
    pending_updates: Dict[str, Dict[str, Any]] = {}
    changed_work_ids: list[str] = []
    work_records: list[Dict[str, Any]] = []
    for update in work_updates_request:
        work_id = update["work_id"]
        current_work_record = works.get(work_id)
        if not isinstance(current_work_record, dict):
            raise ValueError(f"work_id not found: {work_id}")
        require_record_revision(current_work_record, update.get("expected_record_hash"))
        updated_work_record = normalize_work_update(work_id, current_work_record, {"series_id": update["series_id"]})
        pending_updates[work_id] = updated_work_record
        if changed_fields(current_work_record, updated_work_record):
            changed_work_ids.append(work_id)

    for work_id in changed_work_ids:
        work_records.append({"work_id": work_id, "record": pending_updates[work_id], "record_hash": record_hash(pending_updates[work_id])})
    return pending_updates, changed_work_ids, work_records


def plan_series_save(
    series: Mapping[str, Dict[str, Any]],
    works: Mapping[str, Dict[str, Any]],
    series_id: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
    work_updates_request: list[Dict[str, Any]],
) -> SeriesPlan:
    """Plan the exact Series/member changes without a canonical family audit."""
    updated_record = normalize_series_update(series_id, current_record, update)
    validation_errors = validate_series_save_record(updated_record)
    pending_work_updates, changed_work_ids, work_records = _plan_series_work_updates(works, work_updates_request)

    updated_series = dict(series)
    updated_series[series_id] = updated_record
    series_payload = payload_for_map("series", updated_series)
    works_payload = None
    if changed_work_ids:
        updated_works = dict(works)
        for work_id in changed_work_ids:
            updated_works[work_id] = pending_work_updates[work_id]
        works_payload = payload_for_map("works", updated_works)

    return SeriesPlan(
        baseline_record=dict(current_record),
        updated_record=updated_record,
        changed_fields=changed_fields(current_record, updated_record),
        validation_errors=validation_errors,
        payload=series_payload,
        changed_work_ids=changed_work_ids,
        work_updates=pending_work_updates,
        work_records=work_records,
        works_payload=works_payload,
    )


def plan_series_create(
    series: Mapping[str, Dict[str, Any]],
    works: Mapping[str, Dict[str, Any]],
    series_id: str,
    update: Mapping[str, Any],
    work_updates_request: list[Dict[str, Any]],
) -> SeriesPlan:
    """Plan the new Series and supplied member changes without a family audit."""
    blank_record = {field: None for field in SERIES_FIELDS}
    blank_record["series_id"] = series_id
    normalized_update = dict(update)
    created_record = normalize_series_update(series_id, blank_record, normalized_update)
    if not str(created_record.get("title") or "").strip():
        raise ValueError("series title is required")

    validation_errors = validate_series_save_record(created_record)
    pending_work_updates, changed_work_ids, work_records = _plan_series_work_updates(works, work_updates_request)

    updated_series = dict(series)
    updated_series[series_id] = created_record
    series_payload = payload_for_map("series", updated_series)
    works_payload = None
    if changed_work_ids:
        updated_works = dict(works)
        for work_id in changed_work_ids:
            updated_works[work_id] = pending_work_updates[work_id]
        works_payload = payload_for_map("works", updated_works)

    return SeriesPlan(
        baseline_record=blank_record,
        updated_record=created_record,
        changed_fields=changed_fields(blank_record, created_record),
        validation_errors=validation_errors,
        payload=series_payload,
        changed_work_ids=changed_work_ids,
        work_updates=pending_work_updates,
        work_records=work_records,
        works_payload=works_payload,
    )
