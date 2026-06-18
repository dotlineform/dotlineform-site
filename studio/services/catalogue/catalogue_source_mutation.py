"""Pure source-record mutation planners for catalogue write paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from catalogue.catalogue_source import (
    DETAIL_FIELDS,
    DETAIL_TEXT_FIELDS,
    SERIES_FIELDS,
    SERIES_TEXT_FIELDS,
    WORK_FIELDS,
    WORK_TEXT_FIELDS,
    CatalogueSourceRecords,
    normalize_source_record,
    normalize_status,
    normalize_series_ids_value,
    normalize_text,
    payload_for_map,
    slug_id,
    sort_record_map,
    validate_source_records,
)
from catalogue.series_ids import normalize_series_id


@dataclass(frozen=True)
class SourceRecordPlan:
    baseline_record: Dict[str, Any]
    updated_record: Dict[str, Any]
    changed_fields: list[str]
    validation_errors: list[str]
    payload: Dict[str, Any]

    @property
    def changed(self) -> bool:
        return bool(self.changed_fields)


@dataclass(frozen=True)
class SeriesPlan(SourceRecordPlan):
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
    merged["work_id"] = slug_id(merged.get("work_id") or work_id)
    if merged["work_id"] != work_id:
        raise ValueError("record.work_id must match work_id")

    if "status" in update:
        merged["status"] = normalize_status(update.get("status")) or None
    if "series_ids" in update:
        merged["series_ids"] = normalize_series_ids_value(update.get("series_ids"))

    return normalize_source_record(merged, WORK_FIELDS, text_fields=WORK_TEXT_FIELDS)


def normalize_work_detail_update(
    detail_uid: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["detail_uid"] = str(merged.get("detail_uid") or detail_uid).strip()
    if merged["detail_uid"] != detail_uid:
        raise ValueError("record.detail_uid must match detail_uid")

    work_id = slug_id(merged.get("work_id"))
    detail_id = slug_id(merged.get("detail_id"), width=3)
    normalized_uid = f"{work_id}-{detail_id}"
    if normalized_uid != detail_uid:
        raise ValueError("record.work_id/detail_id do not match detail_uid")

    merged["work_id"] = work_id
    merged["detail_id"] = detail_id
    merged["detail_uid"] = normalized_uid
    return normalize_source_record(merged, DETAIL_FIELDS, text_fields=DETAIL_TEXT_FIELDS)


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
    if "status" in update:
        merged["status"] = normalize_status(update.get("status")) or None
    if "primary_work_id" in update:
        primary_work_id = update.get("primary_work_id")
        merged["primary_work_id"] = slug_id(primary_work_id) if primary_work_id not in {None, ""} else None
    return normalize_source_record(merged, SERIES_FIELDS, text_fields=SERIES_TEXT_FIELDS)


def validate_series_save_record(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not normalize_text(record.get("year")):
        errors.append("series year is required")
    else:
        try:
            int(normalize_text(record.get("year")))
        except ValueError:
            errors.append("series year must be a whole number")
    if not normalize_text(record.get("year_display")):
        errors.append("series year_display is required")
    return errors


def changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return [field for field in sorted(set(before.keys()) | set(after.keys())) if before.get(field) != after.get(field)]


def validate_work_records(
    source_records: CatalogueSourceRecords,
    work_id: str,
    work_record: Dict[str, Any],
) -> list[str]:
    works = dict(source_records.works)
    works[work_id] = work_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(works),
        work_detail_sections=source_records.work_detail_sections,
        work_details=source_records.work_details,
        series=source_records.series,
    )
    return validate_source_records(normalized_records)


def validate_series_records(
    source_records: CatalogueSourceRecords,
    series_id: str,
    series_record: Dict[str, Any],
    work_updates: Mapping[str, Dict[str, Any]],
) -> list[str]:
    works = dict(source_records.works)
    series = dict(source_records.series)
    series[series_id] = series_record
    for work_id, work_record in work_updates.items():
        works[work_id] = work_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(works),
        work_detail_sections=source_records.work_detail_sections,
        work_details=source_records.work_details,
        series=sort_record_map(series),
    )
    return validate_source_records(normalized_records)


def plan_work_save(
    source_records: CatalogueSourceRecords,
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
        validation_errors=validate_work_records(source_records, work_id, updated_record),
        payload=payload_for_map("works", updated_works),
    )


def plan_work_create(
    source_records: CatalogueSourceRecords,
    works: Mapping[str, Dict[str, Any]],
    work_id: str,
    update: Mapping[str, Any],
) -> SourceRecordPlan:
    blank_record = {field: None for field in WORK_FIELDS}
    blank_record["work_id"] = work_id
    normalized_update = dict(update)
    if not normalize_status(normalized_update.get("status")):
        normalized_update["status"] = "draft"
    if "series_ids" not in normalized_update:
        normalized_update["series_ids"] = []
    created_record = normalize_work_update(work_id, blank_record, normalized_update)
    if not str(created_record.get("title") or "").strip():
        raise ValueError("work title is required")
    updated_works = dict(works)
    updated_works[work_id] = created_record
    return SourceRecordPlan(
        baseline_record=blank_record,
        updated_record=created_record,
        changed_fields=changed_fields(blank_record, created_record),
        validation_errors=validate_work_records(source_records, work_id, created_record),
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
        updated_work_record = normalize_work_update(work_id, current_work_record, {"series_ids": update["series_ids"]})
        pending_updates[work_id] = updated_work_record
        if changed_fields(current_work_record, updated_work_record):
            changed_work_ids.append(work_id)

    for work_id in changed_work_ids:
        work_records.append({"work_id": work_id, "record": pending_updates[work_id]})
    return pending_updates, changed_work_ids, work_records


def plan_series_save(
    source_records: CatalogueSourceRecords,
    series: Mapping[str, Dict[str, Any]],
    works: Mapping[str, Dict[str, Any]],
    series_id: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
    work_updates_request: list[Dict[str, Any]],
) -> SeriesPlan:
    updated_record = normalize_series_update(series_id, current_record, update)
    save_validation_errors = validate_series_save_record(updated_record)
    pending_work_updates, changed_work_ids, work_records = _plan_series_work_updates(works, work_updates_request)
    validation_errors = (
        save_validation_errors
        if save_validation_errors
        else validate_series_records(source_records, series_id, updated_record, pending_work_updates)
    )

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
    source_records: CatalogueSourceRecords,
    series: Mapping[str, Dict[str, Any]],
    works: Mapping[str, Dict[str, Any]],
    series_id: str,
    update: Mapping[str, Any],
    work_updates_request: list[Dict[str, Any]],
) -> SeriesPlan:
    blank_record = {field: None for field in SERIES_FIELDS}
    blank_record["series_id"] = series_id
    normalized_update = dict(update)
    if not normalize_status(normalized_update.get("status")):
        normalized_update["status"] = "draft"
    created_record = normalize_series_update(series_id, blank_record, normalized_update)
    if not str(created_record.get("title") or "").strip():
        raise ValueError("series title is required")

    save_validation_errors = validate_series_save_record(created_record)
    pending_work_updates, changed_work_ids, work_records = _plan_series_work_updates(works, work_updates_request)
    validation_errors = (
        save_validation_errors
        if save_validation_errors
        else validate_series_records(source_records, series_id, created_record, pending_work_updates)
    )

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
