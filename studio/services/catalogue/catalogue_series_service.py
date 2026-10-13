"""Catalogue series create/save service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_source_mutation as source_mutation
from catalogue.catalogue_revisions import record_hash
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    load_series_payload,
    load_works_payload,
    log_event,
    utc_now,
)
from catalogue.catalogue_source import CatalogueSourceRecords
from catalogue.series_ids import normalize_series_id
from catalogue.catalogue_report_inputs import SERIES_PATH
from catalogue.catalogue_shared_changes import (
    empty_shared_changes, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT,
    WORK_DOCUMENT_COVERAGE_MANIFEST,
)


def series_create_payload(
    context: CatalogueWriteContext, body: Mapping[str, Any],
) -> tuple[dict[str, Any], CatalogueSourceRecords, CatalogueSourceRecords]:
    """Create one empty definition without reading Works or Galleries."""
    series_id, series_update = extract_series_request(body)
    series_map = load_series_payload(context.series_path)["series"]
    if series_id in series_map:
        raise ValueError(f"series_id already exists: {series_id}")
    mutation_plan = source_mutation.plan_series_create(series_map, series_id, series_update)
    shared = {
        **empty_shared_changes(), "current_series": [series_id],
        "shared_outputs": sorted([RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, WORK_DOCUMENT_COVERAGE_MANIFEST, SERIES_PATH]),
    }
    target_payloads: dict[Path, dict[str, Any]] = {
        context.series_path.resolve(): mutation_plan.payload,
    }
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
        "record": mutation_plan.updated_record,
        "_shared_changes": shared,
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
            "dry_run": context.dry_run,
        },
    )
    previous = CatalogueSourceRecords(works={}, series=series_map)
    current = CatalogueSourceRecords(works={}, series=mutation_plan.payload["series"])
    return payload, previous, current


def series_save_payload(
    context: CatalogueWriteContext, body: Mapping[str, Any],
) -> tuple[dict[str, Any], CatalogueSourceRecords, CatalogueSourceRecords]:
    """Save the exact definition and carry its known members into completion."""
    series_id, update = extract_series_request(body)
    series_map = load_series_payload(context.series_path)["series"]
    current_record = series_map.get(series_id)
    if not isinstance(current_record, dict):
        raise ValueError(f"series_id not found: {series_id}")
    plan = source_mutation.plan_series_save(series_map, series_id, current_record, update)
    works_map = load_works_payload(context.works_path)["works"] if plan.changed else {}
    shared = empty_shared_changes()
    if plan.changed_fields:
        outputs = {RELATIONSHIP_REPORT}
        if "title" in plan.changed_fields:
            outputs.update({WORK_DOCUMENT_COVERAGE_MANIFEST, SERIES_PATH})
        shared.update(current_series=[series_id], shared_outputs=sorted(outputs))
    payloads: dict[Path, Any] = {}
    if plan.changed_fields:
        payloads[context.series_path.resolve()] = plan.payload
    if any(path not in context.allowed_write_paths for path in payloads):
        raise ValueError("write target not allowlisted")
    if payloads:
        transactions.execute_source_json_write(payloads, dry_run=context.dry_run, repo_root=context.repo_root)
    payload: dict[str, Any] = {
        "ok": True, "series_id": series_id, "changed": plan.changed,
        "changed_fields": plan.changed_fields, "record": plan.updated_record,
        "record_hash": record_hash(plan.updated_record),
        "_shared_changes": shared,
        "affected_work_ids": sorted(
            wid for wid, record in works_map.items() if record.get("series_id") == series_id
        ),
    }
    if context.dry_run:
        payload.update(dry_run=True, would_write=plan.changed)
    elif plan.changed:
        payload["saved_at_utc"] = utc_now()
    log_event(context.repo_root, "catalogue_series_save", {
        "series_id": series_id, "changed": plan.changed,
        "changed_fields": plan.changed_fields,
        "dry_run": context.dry_run,
    })
    previous = CatalogueSourceRecords(works=works_map, series=series_map)
    current = CatalogueSourceRecords(works=works_map, series=plan.payload["series"])
    return payload, previous, current


def extract_series_request(body: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """Accept only the UI's exact identity and title-only request envelope."""
    if set(body) != {"series_id", "record"}:
        raise ValueError("Series Create/Save requires series_id and record")
    series_id = body["series_id"]
    if not isinstance(series_id, str) or normalize_series_id(series_id) != series_id:
        raise ValueError("series_id must be an exact Series identity")
    record = body["record"]
    if not isinstance(record, dict) or set(record) != {"title"}:
        raise ValueError("record must be an object containing only title")
    return series_id, record
