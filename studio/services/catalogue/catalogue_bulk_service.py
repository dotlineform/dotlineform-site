"""Catalogue bulk-save service routes for Local Studio."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue import catalogue_source_mutation as source_mutation
from catalogue.catalogue_revisions import record_hash
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_galleries import (
    MEMBERSHIPS_FILE,
    newly_empty_gallery_ids,
    read_galleries,
    with_work_memberships,
)
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    load_works_payload,
    log_event,
    utc_now,
)
from catalogue.catalogue_source import payload_for_map
from catalogue.catalogue_shared_changes import work_shared_changes


BULK_WORK_EDITABLE_FIELDS = {
    "series_id",
    "project_folder",
    "project_subfolder",
    "project_filename",
    "title",
    "year",
    "year_display",
    "medium",
    "duration",
    "height_cm",
    "width_cm",
    "depth_cm",
    "storage_location",
}


def bulk_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    """Persist the UI's selected metadata/memberships in one transaction."""
    request = extract_bulk_save_request(body)
    kind = request["kind"]
    selected_ids: list[str] = request["ids"]
    set_fields: dict[str, Any] = request["set_fields"]

    record_payloads: list[dict[str, Any]] = []
    changed_ids: list[str] = []
    changed_field_names: set[str] = set()
    affected_work_ids: list[str] = []
    affected_series_ids: set[str] = set()

    works_payload = load_works_payload(context.works_path)
    works_map = works_payload["works"]
    galleries = read_galleries(context.source_dir)
    updated_galleries = galleries
    if "gallery_ids" in body:
        updated_galleries = with_work_memberships(
            galleries, dict.fromkeys(selected_ids, body["gallery_ids"]),
        )
    pending_updates: dict[str, dict[str, Any]] = {}
    for work_id in selected_ids:
        current_record = works_map.get(work_id)
        if not isinstance(current_record, dict):
            raise ValueError(f"work_id not found: {work_id}")
        pending_updates[work_id] = (
            source_mutation.normalize_work_update(work_id, current_record, set_fields)
            if set_fields else dict(current_record)
        )

    updated_works = dict(works_map)
    metadata_changed = False
    affected_gallery_ids: set[str] = set()
    for work_id in selected_ids:
        current_record = works_map[work_id]
        updated_record = pending_updates[work_id]
        fields_changed = source_mutation.changed_fields(current_record, updated_record)
        metadata_changed = metadata_changed or bool(fields_changed)
        previous_ids = galleries.works.get(work_id, [])
        gallery_ids = updated_galleries.works.get(work_id, [])
        if sorted(previous_ids) != sorted(gallery_ids):
            fields_changed.append("gallery_ids")
            affected_gallery_ids.update(previous_ids)
            affected_gallery_ids.update(gallery_ids)
        record_payloads.append({
            "work_id": work_id, "record": updated_record,
            "record_hash": record_hash(updated_record), "gallery_ids": sorted(gallery_ids),
        })
        if not fields_changed:
            continue
        changed_ids.append(work_id)
        changed_field_names.update(fields_changed)
        affected_work_ids.append(work_id)
        affected_series_ids.update(
            str(record["series_id"]) for record in (current_record, updated_record) if record.get("series_id")
        )
        updated_works[work_id] = updated_record

    changed = bool(changed_ids)
    writes = {}
    if metadata_changed:
        writes[context.works_path.resolve()] = payload_for_map("works", updated_works)
    if galleries.works != updated_galleries.works:
        writes[(context.source_dir / MEMBERSHIPS_FILE).resolve()] = updated_galleries.payloads()[MEMBERSHIPS_FILE]
    if not set(writes).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    if writes:
        transactions.execute_source_json_write(
            writes,
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
        "records": record_payloads,
        "affected_work_ids": affected_work_ids,
        "affected_series_ids": sorted(affected_series_ids),
        "affected_gallery_ids": sorted(affected_gallery_ids),
        "newly_empty_gallery_ids": newly_empty_gallery_ids(galleries, updated_galleries, selected_ids),
        "_shared_changes": work_shared_changes(
            works_map, updated_works, galleries.works, updated_galleries.works, changed_ids,
        ),
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


def extract_bulk_save_request(body: Mapping[str, Any]) -> dict[str, Any]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind != "works":
        raise ValueError("bulk save kind must be works")

    raw_ids = body.get("ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("bulk save ids must be a non-empty array")

    if any(not isinstance(work_id, str) for work_id in raw_ids):
        raise ValueError("bulk save ids must be exact Work ID strings")

    raw_set_fields = body.get("set_fields") or {}
    if not isinstance(raw_set_fields, dict):
        raise ValueError("set_fields must be an object")
    allowed_fields = BULK_WORK_EDITABLE_FIELDS
    unknown_fields = sorted(str(key) for key in raw_set_fields.keys() if str(key) not in allowed_fields)
    if unknown_fields:
        raise ValueError(f"bulk save contains unsupported fields: {', '.join(unknown_fields)}")
    set_fields = {str(key): raw_set_fields[key] for key in raw_set_fields.keys()}

    if "series_operation" in body:
        raise ValueError("Use set_fields.series_id to assign or clear one Series")

    return {
        "kind": kind,
        "ids": raw_ids,
        "set_fields": set_fields,
    }
