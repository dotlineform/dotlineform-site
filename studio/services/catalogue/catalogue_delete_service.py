"""Catalogue delete service routes for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Callable, Mapping, Sequence

from catalogue import catalogue_activity as activity
from catalogue import catalogue_delete_plans
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_service import run_catalogue_search_rebuild
from catalogue.catalogue_source import normalize_detail_uid_value, normalize_text, slug_id
from catalogue.catalogue_service_context import CatalogueWriteContext, append_activity_rows, refresh_lookup_payloads
from catalogue.series_ids import normalize_series_id
from studio.services.media.publish_media_to_r2 import run_catalogue_remote_delete


RemoteDeleteTarget = tuple[str, str]
RemoteDeleteRunner = Callable[..., Mapping[str, object]]


def _publisher_error(error: BaseException) -> ValueError:
    message = str(error).strip()
    if message.startswith("Error:"):
        message = message.removeprefix("Error:").strip()
    return ValueError(message or "R2 media cleanup failed")


def _default_remote_delete_runner(**kwargs: Any) -> Mapping[str, object]:
    try:
        return run_catalogue_remote_delete(**kwargs)
    except SystemExit as error:
        raise _publisher_error(error) from error


def catalogue_delete_remote_media_targets(
    kind: str,
    record_id: str,
    affected: Mapping[str, Any],
) -> list[RemoteDeleteTarget]:
    targets: list[RemoteDeleteTarget] = []
    if kind == "work":
        targets.append(("works", record_id))
    if kind in {"work", "work_detail", "work_detail_section"}:
        targets.extend(
            ("work_details", str(detail_uid))
            for detail_uid in affected.get("work_details") or []
            if str(detail_uid).strip()
        )
    return sorted(set(targets))


def _target_payload(target: RemoteDeleteTarget) -> dict[str, str]:
    return {"kind": target[0], "id": target[1]}


def _remote_cleanup_warning(targets: Sequence[RemoteDeleteTarget]) -> dict[str, Any]:
    return {
        "status": "warning",
        "target_count": len(targets),
        "object_count": len(targets) * 3,
        "deleted": 0,
        "missing": 0,
        "failed": len(targets) * 3,
        "failed_targets": [_target_payload(target) for target in targets],
    }


def _compact_remote_cleanup(
    report: Mapping[str, object],
    targets: Sequence[RemoteDeleteTarget],
) -> dict[str, Any]:
    raw_counts = report.get("counts") if isinstance(report.get("counts"), Mapping) else {}
    counts = {str(key): int(value) for key, value in raw_counts.items() if int(value)}
    failed_targets = {
        (str(item.get("kind") or ""), str(item.get("item_id") or ""))
        for item in report.get("objects") or []
        if isinstance(item, Mapping) and str(item.get("status") or "") not in {"deleted", "missing"}
    }
    unexpected_count = sum(
        count
        for status, count in counts.items()
        if status not in {"deleted", "missing"}
    )
    if unexpected_count and not failed_targets:
        failed_targets = set(targets)
    return {
        "status": "warning" if unexpected_count else "completed",
        "target_count": len(targets),
        "object_count": sum(counts.values()),
        "deleted": counts.get("deleted", 0),
        "missing": counts.get("missing", 0),
        "failed": unexpected_count,
        "failed_targets": [
            _target_payload(target)
            for target in sorted(failed_targets)
            if target[0] and target[1]
        ],
    }


def _delete_remote_media(
    context: CatalogueWriteContext,
    targets: Sequence[RemoteDeleteTarget],
    remote_delete_runner: RemoteDeleteRunner,
) -> dict[str, Any]:
    try:
        report = remote_delete_runner(
            repo_root=context.repo_root,
            targets=list(targets),
            write=True,
        )
    except (Exception, SystemExit):
        return _remote_cleanup_warning(targets)
    return _compact_remote_cleanup(report, targets)


def delete_preview_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    request = extract_delete_request(body)
    preview = catalogue_delete_plans.build_delete_preview(context.source_dir, request["kind"], request["id"], repo_root=context.repo_root)
    return {
        "ok": True,
        "kind": request["kind"],
        "id": request["id"],
        "preview": preview,
    }


def delete_apply_response(
    context: CatalogueWriteContext,
    body: Mapping[str, Any],
    *,
    remote_delete_runner: RemoteDeleteRunner = _default_remote_delete_runner,
) -> tuple[HTTPStatus, dict[str, Any]]:
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
    remote_cleanup = None
    if not context.dry_run:
        remote_targets = catalogue_delete_remote_media_targets(kind, record_id, plan.activity_affected)
        if remote_targets:
            remote_cleanup = _delete_remote_media(context, remote_targets, remote_delete_runner)
            cleanup_result["r2_media"] = remote_cleanup
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
    if remote_cleanup and remote_cleanup["status"] == "warning":
        payload["warning"] = "Catalogue data was deleted, but R2 media cleanup did not complete."
    if activity_context:
        payload["activity_context"] = activity_context
    if activity_context and not context.dry_run:
        now_utc = activity.utc_now()
        cleanup_payload = payload.get("cleanup") if isinstance(payload.get("cleanup"), Mapping) else {}
        updated_json_files = cleanup_payload.get("updated_json_files")
        record_groups = activity.activity_record_groups_from_affected(plan.activity_affected)
        cleanup_detail_items = [
            f"Cleaned generated artifacts for deleted {kind.replace('_', ' ')} {record_id}",
            f"Deleted {cleanup_payload.get('deleted_files', 0)} generated/local file(s)",
            f"Updated {updated_json_files or 0} generated JSON file(s)",
        ]
        if remote_cleanup:
            cleanup_detail_items.append(
                "R2 media cleanup "
                f"{remote_cleanup['status']}: {remote_cleanup['deleted']} deleted, "
                f"{remote_cleanup['missing']} already absent, {remote_cleanup['failed']} failed"
            )
        activity_rows = activity.catalogue_delete_activity_rows(
            activity_profile,
            activity_context,
            cleanup_payload,
            now_utc=now_utc,
            record_groups=record_groups,
            source_detail_items=[f"Deleted canonical {kind.replace('_', ' ')} source record {record_id}"],
            cleanup_detail_items=cleanup_detail_items,
        )
        if remote_cleanup and remote_cleanup["status"] == "warning":
            for row in activity_rows:
                if row.get("script_purpose_id") == "clean-generated-artifacts":
                    row["status"] = "warning"
        append_activity_rows(context.repo_root, payload, activity_rows)
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
