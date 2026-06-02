"""Catalogue prose and moment import service routes for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_prose_import as prose_import
from catalogue.catalogue_service_context import CatalogueWriteContext, append_activity_rows, log_event


def prose_import_apply_response(context: CatalogueWriteContext, body: Mapping[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
    preview = prose_import.build_prose_import_preview(context.repo_root, context.source_dir, body)
    if not preview.get("valid"):
        errors = preview.get("errors") if isinstance(preview.get("errors"), list) else []
        raise ValueError("; ".join(str(error) for error in errors) or "prose import preview failed")
    if preview.get("overwrite_required") and not bool(body.get("confirm_overwrite")):
        return HTTPStatus.CONFLICT, {"ok": False, "error": "overwrite confirmation required", "preview": preview}

    result = prose_import.apply_prose_import(
        context.repo_root,
        context.source_dir,
        body,
        allowed_write_roots=context.allowed_write_roots,
        dry_run=context.dry_run,
        preview=preview,
    )
    target = result.target
    payload: dict[str, Any] = {
        "ok": True,
        "target_kind": target.target_kind,
        "target_id": target.target_id,
        "changed": result.changed,
        "staging_path": result.preview.get("staging_path"),
        "target_path": result.preview.get("target_path"),
        "target_exists": result.preview.get("target_exists"),
        "content_sha256": result.preview.get("content_sha256"),
        "warnings": result.preview.get("warnings", []),
    }
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = result.changed
    elif result.changed:
        payload["imported_at_utc"] = activity.utc_now()
    log_event(
        context.repo_root,
        "catalogue_prose_import_apply",
        {
            "target_kind": target.target_kind,
            "target_id": target.target_id,
            "changed": result.changed,
            "dry_run": context.dry_run,
        },
    )
    return HTTPStatus.OK, payload


def moment_import_apply_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    result = prose_import.apply_moment_import(
        context.repo_root,
        context.source_dir,
        body,
        allowed_write_roots=context.allowed_write_roots,
        dry_run=context.dry_run,
    )
    moment_id = result.moment_id
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_IMPORT_MOMENT,
        record_id=moment_id,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "moment_file": result.moment_file,
        "moment_id": moment_id,
        "status": "draft",
        "published": False,
        "preview": result.preview,
        "build": {},
        "steps": [],
        "metadata_path": str(result.preview.get("metadata_path") or ""),
        "target_path": str(result.preview.get("target_path") or ""),
    }
    if activity_context:
        payload["activity_context"] = activity_context
    if context.dry_run:
        payload["dry_run"] = True
    if not context.dry_run:
        payload["completed_at_utc"] = activity.utc_now()
        if activity_context:
            append_activity_rows(
                context.repo_root,
                payload,
                [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=payload["completed_at_utc"],
                        script_purpose_id="import-source-data",
                        status="completed",
                        record_groups=activity.activity_record_groups(moments=[moment_id]),
                        detail_items=[
                            f"Imported draft moment source {moment_id}",
                            f"Wrote body-only moment prose to {context.rel_path(result.target_path)}",
                            f"Saved canonical moment metadata for {moment_id}",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    )
                ],
            )
    return payload
