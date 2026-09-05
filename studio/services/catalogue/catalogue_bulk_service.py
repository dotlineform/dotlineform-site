"""Catalogue bulk-save service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_source_mutation as source_mutation
from catalogue.catalogue_revisions import record_hash, require_record_revision
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    load_work_details_payload,
    load_works_payload,
    log_event,
    refresh_lookup_payloads,
    utc_now,
)
from catalogue.catalogue_source import (
    CatalogueSourceRecords,
    normalize_detail_uid_value,
    payload_for_map,
    records_from_json_source,
    slug_id,
    sort_record_map,
    validate_source_records,
    validate_work_detail_media_section_record,
    work_details_payload_for_maps,
)


BULK_WORK_EDITABLE_FIELDS = {
    "series_id",
    "project_folder",
    "project_subfolder",
    "project_filename",
    "title",
    "year",
    "year_display",
    "medium_type",
    "medium_caption",
    "duration",
    "height_cm",
    "width_cm",
    "depth_cm",
    "storage_location",
    "provenance",
    "artist",
}

BULK_DETAIL_EDITABLE_FIELDS = {
    "project_filename",
    "title",
}


def bulk_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    request = extract_bulk_save_request(body)
    kind = request["kind"]
    selected_ids: list[str] = request["ids"]
    set_fields: dict[str, Any] = request["set_fields"]

    source_records = records_from_json_source(context.source_dir)
    changed_record_payloads: list[dict[str, Any]] = []
    changed_ids: list[str] = []
    changed_field_names: set[str] = set()
    affected_work_ids: list[str] = []
    affected_series_ids: set[str] = set()

    if kind == "works":
        works_payload = load_works_payload(context.works_path)
        works_map = works_payload["works"]
        pending_updates: dict[str, dict[str, Any]] = {}
        for work_id in selected_ids:
            current_record = works_map.get(work_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"work_id not found: {work_id}")
            require_record_revision(current_record, (body.get("expected_record_hashes") or {}).get(work_id))
            update = dict(set_fields)
            pending_updates[work_id] = source_mutation.normalize_work_update(work_id, current_record, update)

        validation_errors = validate_bulk_records(context.source_dir, work_updates=pending_updates)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        updated_works = dict(works_map)
        for work_id in selected_ids:
            current_record = works_map[work_id]
            updated_record = pending_updates[work_id]
            fields_changed = source_mutation.changed_fields(current_record, updated_record)
            if not fields_changed:
                continue
            changed_ids.append(work_id)
            changed_field_names.update(fields_changed)
            changed_record_payloads.append({"work_id": work_id, "record": updated_record, "record_hash": record_hash(updated_record)})
            affected_work_ids.append(work_id)
            affected_series_ids.update(
                str(record["series_id"]) for record in (current_record, updated_record) if record.get("series_id")
            )
            updated_works[work_id] = updated_record

        changed = bool(changed_ids)
        if changed:
            target_path = context.works_path.resolve()
            if target_path not in context.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            transactions.execute_source_json_write(
                {target_path: payload_for_map("works", updated_works)},
                dry_run=context.dry_run,
                repo_root=context.repo_root,
            )

        payload: dict[str, Any] = {
            "ok": True,
            "kind": kind,
            "selected_ids": selected_ids,
            "selected_count": len(selected_ids),
            "changed": changed,
            "changed_ids": changed_ids,
            "changed_count": len(changed_ids),
            "changed_fields": sorted(changed_field_names),
            "records": changed_record_payloads,
            "affected_work_ids": affected_work_ids,
            "affected_series_ids": sorted(affected_series_ids),
        }
        _finish_bulk_payload(
            context,
            payload,
            kind=kind,
            selected_ids=selected_ids,
            changed=changed,
            changed_ids=changed_ids,
            changed_field_names=changed_field_names,
        )
        return payload

    details_payload = load_work_details_payload(context.work_details_path)
    detail_map = details_payload["work_details"]
    pending_updates: dict[str, dict[str, Any]] = {}
    for detail_uid in selected_ids:
        current_record = detail_map.get(detail_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"detail_uid not found: {detail_uid}")
        require_record_revision(current_record, (body.get("expected_record_hashes") or {}).get(detail_uid))
        updated_record = source_mutation.normalize_work_detail_update(detail_uid, current_record, set_fields)
        work_id = str(updated_record.get("work_id") or "")
        if work_id not in source_records.works:
            raise ValueError(f"parent work_id not found: {work_id}")
        pending_updates[detail_uid] = updated_record

    validation_errors = validate_bulk_records(context.source_dir, detail_updates=pending_updates)
    if validation_errors:
        raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

    updated_details = dict(detail_map)
    for detail_uid in selected_ids:
        current_record = detail_map[detail_uid]
        updated_record = pending_updates[detail_uid]
        fields_changed = source_mutation.changed_fields(current_record, updated_record)
        if not fields_changed:
            continue
        changed_ids.append(detail_uid)
        changed_field_names.update(fields_changed)
        changed_record_payloads.append({"detail_uid": detail_uid, "record": updated_record, "record_hash": record_hash(updated_record)})
        work_id = str(updated_record.get("work_id") or "")
        affected_work_ids.append(work_id)
        updated_details[detail_uid] = updated_record

    changed = bool(changed_ids)
    if changed:
        target_path = context.work_details_path.resolve()
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        transactions.execute_source_json_write(
            {
                target_path: work_details_payload_for_maps(
                    source_records.work_detail_sections,
                    updated_details,
                )
            },
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )

    payload = {
        "ok": True,
        "kind": kind,
        "selected_ids": selected_ids,
        "selected_count": len(selected_ids),
        "changed": changed,
        "changed_ids": changed_ids,
        "changed_count": len(changed_ids),
        "changed_fields": sorted(changed_field_names),
        "records": changed_record_payloads,
        "affected_work_ids": sorted(set(affected_work_ids)),
        "affected_series_ids": [],
    }
    _finish_bulk_payload(
        context,
        payload,
        kind=kind,
        selected_ids=selected_ids,
        changed=changed,
        changed_ids=changed_ids,
        changed_field_names=changed_field_names,
    )
    return payload


def _finish_bulk_payload(
    context: CatalogueWriteContext,
    payload: dict[str, Any],
    *,
    kind: str,
    selected_ids: list[str],
    changed: bool,
    changed_ids: list[str],
    changed_field_names: set[str],
) -> None:
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = changed
    elif changed:
        payload["saved_at_utc"] = utc_now()

    log_event(
        context.repo_root,
        "catalogue_bulk_save",
        {
            "kind": kind,
            "selected_count": len(selected_ids),
            "changed_count": len(changed_ids),
            "changed_fields": sorted(changed_field_names),
            "dry_run": context.dry_run,
        },
    )
    if changed and not context.dry_run:
        payload["lookup_refresh"] = refresh_lookup_payloads(context)


def extract_bulk_save_request(body: Mapping[str, Any]) -> dict[str, Any]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"works", "work_details"}:
        raise ValueError("bulk save kind must be works or work_details")

    raw_ids = body.get("ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("bulk save ids must be a non-empty array")

    ids: list[str] = []
    seen_ids: set[str] = set()
    for raw in raw_ids:
        record_id = slug_id(raw) if kind == "works" else normalize_detail_uid_value(raw)
        if record_id in seen_ids:
            continue
        seen_ids.add(record_id)
        ids.append(record_id)
    if not ids:
        raise ValueError("bulk save ids must include at least one valid id")

    raw_set_fields = body.get("set_fields") or {}
    if not isinstance(raw_set_fields, dict):
        raise ValueError("set_fields must be an object")
    allowed_fields = BULK_WORK_EDITABLE_FIELDS if kind == "works" else BULK_DETAIL_EDITABLE_FIELDS
    unknown_fields = sorted(str(key) for key in raw_set_fields.keys() if str(key) not in allowed_fields)
    if unknown_fields:
        raise ValueError(f"bulk save contains unsupported fields: {', '.join(unknown_fields)}")
    set_fields = {str(key): raw_set_fields[key] for key in raw_set_fields.keys()}

    if "series_operation" in body:
        raise ValueError("Use set_fields.series_id to assign or clear one Series")

    return {
        "kind": kind,
        "ids": ids,
        "set_fields": set_fields,
    }


def validate_bulk_records(
    source_dir: Path,
    *,
    work_updates: Mapping[str, dict[str, Any]] | None = None,
    detail_updates: Mapping[str, dict[str, Any]] | None = None,
) -> list[str]:
    errors: list[str] = []
    source_records = records_from_json_source(source_dir)
    if work_updates:
        for work_id, work_record in work_updates.items():
            source_records.works[work_id] = work_record
    if detail_updates:
        for detail_uid, detail_record in detail_updates.items():
            errors.extend(validate_work_detail_media_section_record(detail_uid, detail_record))
            source_records.work_details[detail_uid] = detail_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_detail_sections=source_records.work_detail_sections,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
    )
    errors.extend(validate_source_records(normalized_records))
    return sorted(dict.fromkeys(errors))
