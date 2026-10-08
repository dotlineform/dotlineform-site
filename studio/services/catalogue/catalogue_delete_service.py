"""Delete selected Work identities or one empty Series through Local Studio."""

from __future__ import annotations

from http import HTTPStatus
import re
from typing import Any, Mapping

from catalogue.catalogue_delete_plans import build_delete_apply_plan
from catalogue.catalogue_output_service import complete_saved_catalogue_edit
from catalogue.catalogue_revisions import require_record_revision
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_service_context import CatalogueWriteContext, utc_now
from catalogue.series_ids import normalize_series_id


def delete_apply_response(
    context: CatalogueWriteContext, body: Mapping[str, Any],
) -> tuple[HTTPStatus, dict[str, Any]]:
    """Delete one or many Works by exact ID; complete the saved result without rereads.

    Series deletion retains its existing revision and empty-membership rules.
    Required local completion can fail after canonical deletion; report that
    saved outcome through the shared completion owner without restoring records.
    """
    kind, record_ids = extract_delete_request(body)
    plan = build_delete_apply_plan(context.source_dir, kind, record_ids)
    if kind == "series":
        require_record_revision(plan.previous.series[record_ids[0]], body.get("expected_record_hash"))
    if not set(plan.payloads).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    transactions.execute_source_json_write(plan.payloads, dry_run=context.dry_run, repo_root=context.repo_root)
    identity = {"ids": record_ids} if kind == "works" else {"id": record_ids[0]}
    payload: dict[str, Any] = {
        "ok": True, "kind": kind, **identity, "deleted": True, "affected": plan.affected,
    }
    if context.dry_run:
        payload.update(dry_run=True, would_write=True)
    else:
        payload["saved_at_utc"] = utc_now()
    complete_saved_catalogue_edit(context, payload, plan.previous, current_records=plan.current)
    return HTTPStatus.OK, payload


def extract_delete_request(body: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Require distinct exact Work IDs, or an exact Series ID and its existing revision field."""
    kind = body.get("kind")
    if kind == "works":
        allowed = {"kind", "ids"}
        raw_ids = body.get("ids")
        if not isinstance(raw_ids, list) or not raw_ids:
            raise ValueError("delete ids must be a non-empty array of exact Work IDs")
        if any(not isinstance(wid, str) or not re.fullmatch(r"[0-9]{5}", wid) for wid in raw_ids):
            raise ValueError("delete ids must contain exact five-digit Work IDs")
        if len(raw_ids) != len(set(raw_ids)):
            raise ValueError("delete ids must be distinct")
        record_ids = sorted(raw_ids)
    elif kind == "series":
        allowed = {"kind", "series_id", "expected_record_hash"}
        series_id = body.get("series_id")
        if not isinstance(series_id, str) or normalize_series_id(series_id) != series_id:
            raise ValueError("delete series_id must be an exact Series ID")
        record_ids = [series_id]
    else:
        raise ValueError("delete kind must be works or series")
    unknown = sorted(str(key) for key in body if key not in allowed)
    if unknown:
        raise ValueError("delete contains unsupported fields: " + ", ".join(unknown))
    return kind, record_ids
