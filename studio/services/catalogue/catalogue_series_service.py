"""Catalogue series create/save service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_source_mutation as source_mutation
from catalogue.catalogue_revisions import record_hash, require_record_revision
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    load_series_payload,
    load_works_payload,
    log_event,
    utc_now,
)
from catalogue.catalogue_source import SERIES_FIELDS, records_from_json_source, slug_id
from catalogue.series_ids import normalize_series_id


def series_create_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_series_id = body.get("series_id")
    series_update = extract_series_update(body)
    if requested_series_id is None:
        requested_series_id = series_update.get("series_id")
    series_id = normalize_series_id(requested_series_id)
    work_updates_request = extract_series_work_updates(body)

    series_payload = load_series_payload(context.series_path)
    series_map = series_payload["series"]
    if isinstance(series_map.get(series_id), dict):
        raise ValueError(f"series_id already exists: {series_id}")

    works_payload = load_works_payload(context.works_path)
    works_map = works_payload["works"]
    mutation_plan = source_mutation.plan_series_create(
        records_from_json_source(context.source_dir),
        series_map,
        works_map,
        series_id,
        series_update,
        work_updates_request,
    )
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    changed_work_ids = mutation_plan.changed_work_ids
    target_payloads: dict[Path, dict[str, Any]] = {
        context.series_path.resolve(): mutation_plan.payload,
    }
    if changed_work_ids and mutation_plan.works_payload is not None:
        target_payloads[context.works_path.resolve()] = mutation_plan.works_payload
    for target_path in target_payloads:
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
    transactions.execute_source_json_write(
        target_payloads,
        dry_run=context.dry_run,
        repo_root=context.repo_root,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "series_id": series_id,
        "record_hash": record_hash(mutation_plan.updated_record),
        "created": True,
        "changed": True,
        "changed_fields": mutation_plan.changed_fields,
        "changed_work_ids": changed_work_ids,
        "record": mutation_plan.updated_record,
        "work_records": mutation_plan.work_records,
    }
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = True
    else:
        payload["saved_at_utc"] = utc_now()

    log_event(
        context.repo_root,
        "catalogue_series_create",
        {
            "series_id": series_id,
            "changed_fields": payload["changed_fields"],
            "changed_work_ids": changed_work_ids,
            "dry_run": context.dry_run,
        },
    )
    return payload


def series_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    """Save a Series and explicit member changes as one canonical transaction."""
    update = extract_series_update(body)
    series_id = normalize_series_id(body.get("series_id") or update.get("series_id"))
    series_map = load_series_payload(context.series_path)["series"]
    current_record = series_map.get(series_id)
    if not isinstance(current_record, dict):
        raise ValueError(f"series_id not found: {series_id}")
    require_record_revision(current_record, body.get("expected_record_hash"))
    works_map = load_works_payload(context.works_path)["works"]
    plan = source_mutation.plan_series_save(
        records_from_json_source(context.source_dir), series_map, works_map,
        series_id, current_record, update, extract_series_work_updates(body),
    )
    if plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(plan.validation_errors[:20]))
    payloads: dict[Path, Any] = {}
    if plan.changed_fields:
        payloads[context.series_path.resolve()] = plan.payload
    if plan.works_payload is not None:
        payloads[context.works_path.resolve()] = plan.works_payload
    if any(path not in context.allowed_write_paths for path in payloads):
        raise ValueError("write target not allowlisted")
    if payloads:
        transactions.execute_source_json_write(payloads, dry_run=context.dry_run, repo_root=context.repo_root)
    payload: dict[str, Any] = {
        "ok": True, "series_id": series_id, "changed": plan.changed,
        "changed_fields": plan.changed_fields, "record": plan.updated_record,
        "record_hash": record_hash(plan.updated_record),
        "changed_work_ids": plan.changed_work_ids, "work_records": plan.work_records,
    }
    if context.dry_run:
        payload.update(dry_run=True, would_write=plan.changed)
    elif plan.changed:
        payload["saved_at_utc"] = utc_now()
    log_event(context.repo_root, "catalogue_series_save", {
        "series_id": series_id, "changed": plan.changed,
        "changed_fields": plan.changed_fields, "changed_work_ids": plan.changed_work_ids,
        "dry_run": context.dry_run,
    })
    return payload


def extract_series_update(body: Mapping[str, Any]) -> dict[str, Any]:
    raw_record = body.get("record", body.get("series"))
    if raw_record is None:
        raw_record = {field: body[field] for field in SERIES_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in SERIES_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one series field")
    return dict(raw_record)


def extract_series_work_updates(body: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_updates = body.get("work_updates") or []
    if raw_updates == []:
        return []
    if not isinstance(raw_updates, list):
        raise ValueError("work_updates must be an array")
    updates: list[dict[str, Any]] = []
    for raw in raw_updates:
        if not isinstance(raw, dict):
            raise ValueError("work_updates entries must be objects")
        unknown = sorted(str(key) for key in raw.keys() if str(key) not in {"work_id", "series_id", "expected_record_hash"})
        if unknown:
            raise ValueError(f"work_updates entry contains unsupported fields: {', '.join(unknown)}")
        if "series_id" not in raw:
            raise ValueError("work_updates entry must include series_id")
        updates.append(
            {
                "work_id": slug_id(raw.get("work_id")),
                "expected_record_hash": raw.get("expected_record_hash"),
                "series_id": normalize_series_id(raw["series_id"]) if raw.get("series_id") else None,
            }
        )
    return updates
