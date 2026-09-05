"""Catalogue delete service routes for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Mapping

from catalogue import catalogue_delete_plans
from catalogue.catalogue_revisions import require_record_revision
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_source import normalize_detail_uid_value, normalize_text, slug_id
from catalogue.catalogue_service_context import CatalogueWriteContext, utc_now
from catalogue.series_ids import normalize_series_id


def delete_preview_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    request = extract_delete_request(body)
    preview = catalogue_delete_plans.build_delete_preview(context.source_dir, request["kind"], request["id"])
    return {
        "ok": True,
        "kind": request["kind"],
        "id": request["id"],
        "preview": preview,
    }


def delete_apply_response(
    context: CatalogueWriteContext, body: Mapping[str, Any],
) -> tuple[HTTPStatus, dict[str, Any]]:
    """Delete canonical records; the dispatcher reconciles their output afterward."""
    request = extract_delete_request(body)
    kind, record_id = request["kind"], request["id"]
    preview = catalogue_delete_plans.build_delete_preview(context.source_dir, kind, record_id)
    require_record_revision(preview["record"], body.get("expected_record_hash"))
    if preview["blocked"]:
        return HTTPStatus.BAD_REQUEST, {"ok": False, "error": "delete preview contains blockers", "preview": preview}
    plan = catalogue_delete_plans.build_delete_apply_plan(context.source_dir, kind, record_id)
    if any(path not in context.allowed_write_paths for path in plan.payloads):
        raise ValueError("write target not allowlisted")
    transactions.execute_source_json_write(plan.payloads, dry_run=context.dry_run, repo_root=context.repo_root)
    payload: dict[str, Any] = {
        "ok": True, "kind": kind, "id": record_id, "deleted": True,
        "preview": preview, "affected": plan.affected,
    }
    if context.dry_run:
        payload.update(dry_run=True, would_write=True)
    else:
        payload["saved_at_utc"] = utc_now()
    return HTTPStatus.OK, payload


def extract_delete_request(body: Mapping[str, Any]) -> dict[str, str]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"work", "work_detail", "work_detail_section", "series"}:
        raise ValueError("delete kind must be work, work_detail, work_detail_section, or series")
    if kind == "work":
        record_id = slug_id(body.get("work_id") or body.get("id"))
    elif kind == "work_detail":
        record_id = normalize_detail_uid_value(body.get("detail_uid") or body.get("id"))
    elif kind == "work_detail_section":
        record_id = normalize_text(body.get("section_id") or body.get("id"))
        if not record_id:
            raise ValueError("section_id is required")
    elif kind == "series":
        record_id = normalize_series_id(body.get("series_id") or body.get("id"))
    return {
        "kind": kind,
        "id": record_id,
    }
