"""Catalogue delete service routes for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_delete_plans
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_service import run_catalogue_search_rebuild
from catalogue.catalogue_source import normalize_detail_uid_value, normalize_text, slug_id
from catalogue.catalogue_service_context import CatalogueWriteContext, append_activity_rows, refresh_lookup_payloads
from catalogue.series_ids import normalize_series_id


def delete_preview_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    request = extract_delete_request(body)
    preview = catalogue_delete_plans.build_delete_preview(context.source_dir, request["kind"], request["id"], repo_root=context.repo_root)
    return {
        "ok": True,
        "kind": request["kind"],
        "id": request["id"],
        "preview": preview,
    }


def delete_apply_response(context: CatalogueWriteContext, body: Mapping[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
    request = extract_delete_request(body)
    kind = request["kind"]
    record_id = request["id"]
    preview = catalogue_delete_plans.build_delete_preview(context.source_dir, kind, record_id, repo_root=context.repo_root)
    if preview.get("blocked"):
        return HTTPStatus.BAD_REQUEST, {
            "ok": False,
            "error": "delete preview contains blockers",
            "kind": kind,
            "id": record_id,
            "preview": preview,
        }

    activity_profile = activity.activity_profile_for_delete(kind)
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity_profile,
        record_id=record_id,
    )
    plan = catalogue_delete_plans.build_delete_apply_plan(context.source_dir, context.repo_root, kind, record_id, preview)
    transaction_result = transactions.execute_catalogue_cleanup_transaction(
        repo_root=context.repo_root,
        dry_run=context.dry_run,
        allowed_write_paths=context.allowed_write_paths,
        payloads=plan.payloads,
        cleanup=plan.cleanup,
        rebuild_catalogue_search=lambda repo_root: run_catalogue_search_rebuild(repo_root, write=True),
        refresh_lookup_payloads=lambda: refresh_lookup_payloads(context),
    )
    cleanup_result = transaction_result.payload
    payload: dict[str, Any] = {
        "ok": True,
        "kind": kind,
        "id": record_id,
        "deleted": True,
        "preview": preview,
        "cleanup": cleanup_result,
    }
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = True
    else:
        payload["saved_at_utc"] = activity.utc_now()
    if activity_context:
        payload["activity_context"] = activity_context
    if activity_context and not context.dry_run:
        now_utc = activity.utc_now()
        cleanup_payload = payload.get("cleanup") if isinstance(payload.get("cleanup"), Mapping) else {}
        updated_json_files = cleanup_payload.get("updated_json_files")
        record_groups = activity.activity_record_groups_from_affected(plan.activity_affected)
        append_activity_rows(
            context.repo_root,
            payload,
            activity.catalogue_delete_activity_rows(
                activity_profile,
                activity_context,
                cleanup_payload,
                now_utc=now_utc,
                record_groups=record_groups,
                source_detail_items=[f"Deleted canonical {kind.replace('_', ' ')} source record {record_id}"],
                cleanup_detail_items=[
                    f"Cleaned generated artifacts for deleted {kind.replace('_', ' ')} {record_id}",
                    f"Deleted {cleanup_payload.get('deleted_files', 0)} generated/local file(s)",
                    f"Updated {updated_json_files or 0} generated JSON file(s)",
                ],
            ),
        )
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
