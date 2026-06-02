"""Catalogue bulk-save service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_source_mutation as source_mutation
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_service import run_build_targets
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    extract_apply_build,
    load_work_details_payload,
    load_works_payload,
    log_event,
    refresh_lookup_payloads,
)
from catalogue.catalogue_source import (
    CatalogueSourceRecords,
    normalize_detail_uid_value,
    normalize_series_ids_value,
    normalize_status,
    payload_for_map,
    records_from_json_source,
    slug_id,
    sort_record_map,
    validate_source_records,
    validate_work_detail_media_section_record,
    validate_work_detail_section_metadata_consistency,
)


BULK_WORK_EDITABLE_FIELDS = {
    "status",
    "published_date",
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
    "details_subfolder",
    "section_title",
    "sort_order",
    "project_filename",
    "title",
    "status",
}


def bulk_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    apply_build = extract_apply_build(body)
    request = extract_bulk_save_request(body)
    kind = request["kind"]
    selected_ids: list[str] = request["ids"]
    set_fields: dict[str, Any] = request["set_fields"]
    series_operation = request["series_operation"]

    source_records = records_from_json_source(context.source_dir)
    changed_record_payloads: list[dict[str, Any]] = []
    changed_ids: list[str] = []
    changed_field_names: set[str] = set()
    build_targets: list[dict[str, Any]] = []
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
            update = dict(set_fields)
            if series_operation is not None:
                update["series_ids"] = apply_work_bulk_series_operation(
                    normalize_series_ids_value(current_record.get("series_ids")),
                    series_operation,
                )
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
            changed_record_payloads.append({"work_id": work_id, "record": updated_record})
            previous_series_ids = normalize_series_ids_value(current_record.get("series_ids"))
            next_series_ids = normalize_series_ids_value(updated_record.get("series_ids"))
            extra_series_ids = [series_id for series_id in previous_series_ids if series_id not in next_series_ids]
            if normalize_status(updated_record.get("status")) == "published":
                build_targets.append({"work_id": work_id, "extra_series_ids": extra_series_ids})
            affected_work_ids.append(work_id)
            affected_series_ids.update(previous_series_ids)
            affected_series_ids.update(next_series_ids)
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
            "build_targets": build_targets,
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
        payload["build_requested"] = bool(apply_build and changed and build_targets)
        if apply_build and changed and build_targets:
            payload["build"] = run_build_targets(context, payload["build_targets"])
        return payload

    details_payload = load_work_details_payload(context.work_details_path)
    detail_map = details_payload["work_details"]
    pending_updates: dict[str, dict[str, Any]] = {}
    for detail_uid in selected_ids:
        current_record = detail_map.get(detail_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"detail_uid not found: {detail_uid}")
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
        changed_record_payloads.append({"detail_uid": detail_uid, "record": updated_record})
        work_id = str(updated_record.get("work_id") or "")
        affected_work_ids.append(work_id)
        build_targets.append({"work_id": work_id, "extra_series_ids": []})
        updated_details[detail_uid] = updated_record

    changed = bool(changed_ids)
    if changed:
        target_path = context.work_details_path.resolve()
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        transactions.execute_source_json_write(
            {target_path: payload_for_map("work_details", updated_details)},
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
        "build_targets": [{"work_id": work_id, "extra_series_ids": []} for work_id in sorted(set(affected_work_ids))],
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
    payload["build_requested"] = bool(apply_build and changed)
    if apply_build and changed:
        payload["build"] = run_build_targets(context, payload["build_targets"])
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
        payload["saved_at_utc"] = activity.utc_now()

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
        refresh_lookup_payloads(context)


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

    raw_series_operation = body.get("series_operation")
    if kind != "works" and raw_series_operation not in (None, "", {}):
        raise ValueError("series_operation is only supported for works bulk save")

    series_operation = None
    if kind == "works" and raw_series_operation is not None:
        if not isinstance(raw_series_operation, dict):
            raise ValueError("series_operation must be an object")
        mode = str(raw_series_operation.get("mode") or "").strip().lower()
        if mode not in {"replace", "add_remove"}:
            raise ValueError("series_operation.mode must be replace or add_remove")
        operation: dict[str, Any] = {"mode": mode}
        if mode == "replace":
            operation["series_ids"] = normalize_series_ids_value(raw_series_operation.get("series_ids"))
        else:
            operation["add_series_ids"] = normalize_series_ids_value(raw_series_operation.get("add_series_ids"))
            operation["remove_series_ids"] = normalize_series_ids_value(raw_series_operation.get("remove_series_ids"))
        series_operation = operation

    return {
        "kind": kind,
        "ids": ids,
        "set_fields": set_fields,
        "series_operation": series_operation,
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
        errors.extend(validate_work_detail_section_metadata_consistency(source_records.work_details))
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
    )
    errors.extend(validate_source_records(normalized_records))
    return sorted(dict.fromkeys(errors))


def apply_work_bulk_series_operation(current_series_ids: list[str], operation: Mapping[str, Any] | None) -> list[str]:
    if not operation:
        return current_series_ids
    mode = str(operation.get("mode") or "").strip().lower()
    if mode == "replace":
        return normalize_series_ids_value(operation.get("series_ids"))
    if mode != "add_remove":
        raise ValueError("unsupported series bulk operation")

    add_series_ids = normalize_series_ids_value(operation.get("add_series_ids"))
    remove_series_ids = set(normalize_series_ids_value(operation.get("remove_series_ids")))
    next_series_ids = [series_id for series_id in current_series_ids if series_id not in remove_series_ids]
    seen = set(next_series_ids)
    for series_id in add_series_ids:
        if series_id in seen:
            continue
        seen.add(series_id)
        next_series_ids.append(series_id)
    return next_series_ids
