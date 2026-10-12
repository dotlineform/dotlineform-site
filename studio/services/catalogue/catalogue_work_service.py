"""Catalogue work create/save service routes for Local Studio."""

from __future__ import annotations

import re
from typing import Any, Mapping

from catalogue import catalogue_source_mutation as source_mutation
from catalogue.catalogue_galleries import (
    MEMBERSHIPS_FILE,
    newly_empty_gallery_ids,
    read_galleries,
    with_work_memberships,
)
from catalogue.catalogue_revisions import record_hash
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    load_works_payload,
    log_event,
    utc_now,
)
from catalogue.catalogue_source import WORK_FIELDS
from catalogue.catalogue_shared_changes import work_shared_changes


def work_create_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    work_update = extract_work_update(body)
    work_id = body.get("work_id")
    if not isinstance(work_id, str) or re.fullmatch(r"[0-9]{5}", work_id) is None:
        raise ValueError("work_id must be exactly five digits")
    works_payload = load_works_payload(context.works_path)
    works = works_payload["works"]
    if work_id in works:
        raise ValueError(f"work_id already exists: {work_id}")

    mutation_plan = source_mutation.plan_work_create(
        works,
        work_id,
        work_update,
    )
    galleries = read_galleries(context.source_dir)
    updated_galleries = with_work_memberships(
        galleries, {work_id: body.get("gallery_ids", [])},
    )
    membership_changed = galleries.works != updated_galleries.works
    changed_fields = mutation_plan.changed_fields + (["gallery_ids"] if membership_changed else [])
    target_path = context.works_path.resolve()
    writes = {target_path: mutation_plan.payload}
    if membership_changed:
        writes[(context.source_dir / MEMBERSHIPS_FILE).resolve()] = updated_galleries.payloads()[MEMBERSHIPS_FILE]
    if not set(writes).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    transactions.execute_source_json_write(
        writes,
        dry_run=context.dry_run,
        repo_root=context.repo_root,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "work_id": work_id,
        "record_hash": record_hash(mutation_plan.updated_record),
        "created": True,
        "changed": True,
        "changed_fields": changed_fields,
        "record": mutation_plan.updated_record,
        "gallery_ids": updated_galleries.works.get(work_id, []),
        "affected_gallery_ids": updated_galleries.works.get(work_id, []),
        "_shared_changes": work_shared_changes(
            works, {**works, work_id: mutation_plan.updated_record}, galleries.works, updated_galleries.works, [work_id],
        ),
    }
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = True
    else:
        payload["saved_at_utc"] = utc_now()

    log_event(
        context.repo_root,
        "catalogue_work_create",
        {
            "work_id": work_id,
            "changed_fields": payload["changed_fields"],
            "dry_run": context.dry_run,
        },
    )
    return payload


def work_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    """Persist UI-authored metadata; the dispatcher owns required media/effects."""
    work_update = extract_work_update(body)
    work_id = body.get("work_id")
    if not isinstance(work_id, str):
        raise ValueError("work_id must identify an existing exact Work")
    works = load_works_payload(context.works_path)["works"]
    current_record = works.get(work_id)
    if not isinstance(current_record, dict):
        raise ValueError(f"work_id not found: {work_id}")
    galleries = read_galleries(context.source_dir)
    updated_galleries = galleries
    if "gallery_ids" in body:
        updated_galleries = with_work_memberships(galleries, {work_id: body["gallery_ids"]})
    plan = source_mutation.plan_work_save(
        works, work_id, current_record, work_update,
    )
    membership_changed = galleries.works != updated_galleries.works
    changed = plan.changed or membership_changed
    changed_fields = plan.changed_fields + (["gallery_ids"] if membership_changed else [])
    writes = {}
    if plan.changed:
        writes[context.works_path.resolve()] = plan.payload
    if membership_changed:
        writes[(context.source_dir / MEMBERSHIPS_FILE).resolve()] = updated_galleries.payloads()[MEMBERSHIPS_FILE]
    if not set(writes).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    if writes:
        transactions.execute_source_json_write(
            writes, dry_run=context.dry_run, repo_root=context.repo_root,
        )
    payload: dict[str, Any] = {
        "ok": True, "work_id": work_id, "changed": changed,
        "changed_fields": changed_fields, "record": plan.updated_record,
        "record_hash": record_hash(plan.updated_record),
        "gallery_ids": sorted(updated_galleries.works.get(work_id, [])),
        "affected_gallery_ids": sorted(set(galleries.works.get(work_id, [])) | set(updated_galleries.works.get(work_id, []))),
        "newly_empty_gallery_ids": newly_empty_gallery_ids(galleries, updated_galleries, [work_id]),
        "_shared_changes": work_shared_changes(
            works, {**works, work_id: plan.updated_record}, galleries.works, updated_galleries.works, [work_id],
        ),
    }
    if context.dry_run:
        payload.update(dry_run=True, would_write=changed)
    elif changed:
        payload["saved_at_utc"] = utc_now()
    log_event(context.repo_root, "catalogue_work_save", {
        "work_id": work_id, "changed": changed,
        "changed_fields": changed_fields, "dry_run": context.dry_run,
    })
    return payload


def extract_work_update(body: Mapping[str, Any]) -> dict[str, Any]:
    if "work" in body or any(field in body for field in WORK_FIELDS if field != "work_id"):
        raise ValueError("Work fields must be supplied in record")
    raw_record = body.get("record")
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in WORK_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work field")
    return dict(raw_record)
