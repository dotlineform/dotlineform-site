"""Catalogue publication service routes for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_publication
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_service import run_build_operation, run_catalogue_search_rebuild
from catalogue.catalogue_moment_service import extract_moment_update
from catalogue.catalogue_service_context import CatalogueWriteContext, append_activity_rows, refresh_lookup_payloads
from catalogue.catalogue_source import normalize_series_ids_value, slug_id
from catalogue.catalogue_work_service import extract_work_update
from catalogue.catalogue_series_service import extract_series_update
from catalogue.series_ids import normalize_series_id


def publication_preview_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    request = extract_publication_request(body)
    preview = catalogue_publication.build_publication_preview(context.source_dir, context.repo_root, request)
    return {"ok": True, "preview": preview}


def publication_apply_response(context: CatalogueWriteContext, body: Mapping[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
    request = extract_publication_request(body)
    preview = catalogue_publication.build_publication_preview(context.source_dir, context.repo_root, request)
    if preview.get("blocked"):
        return HTTPStatus.BAD_REQUEST, {
            "ok": False,
            "error": "publication preview contains blockers",
            "preview": preview,
        }

    kind = str(request["kind"])
    action = str(request["action"])
    record_id = str(request["id"])
    activity_profile = activity.activity_profile_for_publication(kind, action) if action in {"publish", "unpublish"} else None
    activity_context = (
        activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity_profile,
            record_id=record_id,
        )
        if activity_profile is not None
        else {}
    )
    target_record = dict(preview["target_record"])
    changed = bool(preview.get("changed"))
    source_changed = bool(preview.get("source_changed", changed))
    public_update: dict[str, Any] = {"ok": True, "skipped": True}
    public_update_ok = True

    if action == "unpublish":
        cleanup_result = catalogue_publication.apply_publication_unpublish_cleanup(
            repo_root=context.repo_root,
            source_dir=context.source_dir,
            dry_run=context.dry_run,
            allowed_write_paths=context.allowed_write_paths,
            kind=kind,
            record_id=record_id,
            target_record=target_record,
            preview=preview,
            rebuild_catalogue_search=lambda repo_root: run_catalogue_search_rebuild(repo_root, write=True),
            refresh_lookup_payloads=(lambda: refresh_lookup_payloads(context)) if kind != "moment" else None,
        )
        public_update = cleanup_result.payload
    else:
        if source_changed:
            source_payloads = catalogue_publication.publication_source_payloads(context.source_dir, kind, record_id, target_record, preview)
            blocked_paths = [path for path in source_payloads if path not in context.allowed_write_paths]
            if blocked_paths:
                raise ValueError("write target not allowlisted")
            transactions.execute_source_json_write(
                source_payloads,
                dry_run=context.dry_run,
                repo_root=context.repo_root,
            )
            if not context.dry_run and kind != "moment":
                refresh_lookup_payloads(context)
        public_update_ok, public_update = catalogue_publication.run_publication_build_transaction(
            repo_root=context.repo_root,
            source_dir=context.source_dir,
            dry_run=context.dry_run,
            kind=kind,
            record_id=record_id,
            target_record=target_record,
            extra_series_ids=list(request.get("extra_series_ids") or []),
            extra_work_ids=list(request.get("extra_work_ids") or []),
            force=bool(request.get("force")),
            run_build_operation=lambda **kwargs: run_build_operation(context, **kwargs),
        )

    payload: dict[str, Any] = {
        "ok": public_update_ok,
        "status": "completed" if public_update_ok else "public_update_failed",
        "kind": kind,
        "id": record_id,
        "action": action,
        "changed": changed,
        "source_changed": source_changed,
        "changed_fields": preview.get("changed_fields", []),
        "bootstrap_publish_work_ids": preview.get("bootstrap_publish_work_ids", []),
        "record": target_record,
        "preview": preview,
        "source_saved": bool(source_changed and not context.dry_run) or bool(action == "unpublish" and not context.dry_run),
        "public_update": public_update,
    }
    if activity_context:
        payload["activity_context"] = activity_context
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = source_changed or action == "unpublish"
    if not context.dry_run and activity_context and activity_profile is not None:
        now_utc = activity.utc_now()
        record_groups = activity.activity_record_groups_from_affected(preview.get("affected"))
        rows: list[dict[str, Any]] = []
        if payload["source_saved"]:
            rows.extend(
                activity.catalogue_source_write_activity_rows(
                    activity_profile,
                    activity_context,
                    now_utc=now_utc,
                    script_purpose_id="save-canonical-data",
                    record_groups=record_groups,
                    detail_items=[
                        f"{action.replace('_', ' ').title()} {kind.replace('_', ' ')} {record_id}",
                        f"Changed fields: {', '.join(preview.get('changed_fields') or [])}",
                    ],
                )
            )
        if activity_profile.lookup_script_purpose_id and payload["source_saved"]:
            rows.append(
                activity.catalogue_lookup_activity_row(
                    activity_context,
                    now_utc=now_utc,
                    record_groups=record_groups,
                    detail_items=[f"Refreshed catalogue lookup data after {action.replace('_', ' ')} {kind.replace('_', ' ')} {record_id}"],
                )
            )
        if action == "publish":
            rows.extend(
                activity.catalogue_build_studio_activity_rows(
                    activity_profile,
                    activity_context,
                    public_update,
                    published_detail=f"Updated published {kind.replace('_', ' ')} data for {record_id}",
                    search_detail=f"Rebuilt catalogue search for {kind.replace('_', ' ')} {record_id}",
                    fallback_record_groups=record_groups,
                )
            )
        elif action == "unpublish":
            rows.extend(
                activity.catalogue_cleanup_activity_rows(
                    activity_context,
                    public_update,
                    now_utc=now_utc,
                    record_groups=record_groups,
                    detail_items=[
                        f"Cleaned generated artifacts for {kind.replace('_', ' ')} {record_id}",
                        f"Deleted {public_update.get('deleted_files', 0)} generated/local file(s)",
                        f"Updated {public_update.get('updated_json_files', 0)} generated JSON file(s)",
                    ],
                )
            )
        append_activity_rows(context.repo_root, payload, rows)
    return HTTPStatus.OK if public_update_ok else HTTPStatus.INTERNAL_SERVER_ERROR, payload


def extract_publication_request(body: Mapping[str, Any]) -> dict[str, Any]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"work", "series", "moment"}:
        raise ValueError("publication kind must be work, series, or moment")

    action = str(body.get("action") or "").strip().lower().replace("-", "_")
    if action not in {"publish", "unpublish", "save_published"}:
        raise ValueError("publication action must be publish, unpublish, or save_published")

    if kind == "work":
        record_id = slug_id(body.get("work_id") or body.get("id"))
    elif kind == "series":
        record_id = normalize_series_id(body.get("series_id") or body.get("id"))
    else:
        from catalogue.catalogue_service_context import normalize_moment_id_value

        record_id = normalize_moment_id_value(body.get("moment_id") or body.get("id"))

    record_update: dict[str, Any] = {}
    if action == "save_published":
        if kind == "work":
            record_update = extract_work_update(body)
        elif kind == "series":
            record_update = extract_series_update(body)
        else:
            record_update = extract_moment_update(body)

    return {
        "kind": kind,
        "action": action,
        "id": record_id,
        "record_update": record_update,
        "extra_series_ids": normalize_series_ids_value(body.get("extra_series_ids")),
        "extra_work_ids": [slug_id(raw) for raw in body.get("extra_work_ids") or []],
        "force": bool(body.get("force")),
    }
