"""Catalogue work create/save service routes for Local Studio."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue import catalogue_source_mutation as source_mutation
from catalogue.catalogue_revisions import record_hash, require_record_revision
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    load_works_payload,
    log_event,
    refresh_lookup_payloads,
    refresh_lookup_payloads_for_work_change,
    utc_now,
)
from catalogue.catalogue_source import WORK_FIELDS, records_from_json_source, slug_id


def work_create_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_work_id = body.get("work_id")
    work_update = extract_work_update(body)
    if requested_work_id is None:
        requested_work_id = work_update.get("work_id")
    work_id = slug_id(requested_work_id)
    works_payload = load_works_payload(context.works_path)
    works = works_payload["works"]
    if isinstance(works.get(work_id), dict):
        raise ValueError(f"work_id already exists: {work_id}")

    mutation_plan = source_mutation.plan_work_create(
        records_from_json_source(context.source_dir),
        works,
        work_id,
        work_update,
    )
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    target_path = context.works_path.resolve()
    if target_path not in context.allowed_write_paths:
        raise ValueError("write target not allowlisted")
    transactions.execute_source_json_write(
        {target_path: mutation_plan.payload},
        dry_run=context.dry_run,
        repo_root=context.repo_root,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "work_id": work_id,
        "record_hash": record_hash(mutation_plan.updated_record),
        "created": True,
        "changed": True,
        "changed_fields": mutation_plan.changed_fields,
        "record": mutation_plan.updated_record,
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
    if not context.dry_run:
        refresh_result = refresh_lookup_payloads(context)
        payload["lookup_refresh"] = refresh_result
    return payload


def work_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    """Save canonical metadata and refresh Studio reads without publishing output."""
    work_update = extract_work_update(body)
    work_id = slug_id(body.get("work_id") or work_update.get("work_id"))
    works = load_works_payload(context.works_path)["works"]
    current_record = works.get(work_id)
    if not isinstance(current_record, dict):
        raise ValueError(f"work_id not found: {work_id}")
    require_record_revision(current_record, body.get("expected_record_hash"))
    plan = source_mutation.plan_work_save(
        records_from_json_source(context.source_dir), works, work_id, current_record, work_update,
    )
    if plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(plan.validation_errors[:20]))
    if plan.changed:
        target_path = context.works_path.resolve()
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        transactions.execute_source_json_write(
            {target_path: plan.payload}, dry_run=context.dry_run, repo_root=context.repo_root,
        )
    payload: dict[str, Any] = {
        "ok": True, "work_id": work_id, "changed": plan.changed,
        "changed_fields": plan.changed_fields, "record": plan.updated_record,
        "record_hash": record_hash(plan.updated_record),
    }
    if context.dry_run:
        payload.update(dry_run=True, would_write=plan.changed)
    elif plan.changed:
        payload["saved_at_utc"] = utc_now()
        payload["lookup_refresh"] = refresh_lookup_payloads_for_work_change(
            context, work_id, current_record, plan.updated_record, plan.changed_fields,
        )
    log_event(context.repo_root, "catalogue_work_save", {
        "work_id": work_id, "changed": plan.changed,
        "changed_fields": plan.changed_fields, "dry_run": context.dry_run,
    })
    return payload


def extract_work_update(body: Mapping[str, Any]) -> dict[str, Any]:
    raw_record = body.get("record", body.get("work"))
    if raw_record is None:
        raw_record = {field: body[field] for field in WORK_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in WORK_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work field")
    return dict(raw_record)
