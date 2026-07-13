"""R2 media preview/apply routes for the Local Studio catalogue editor."""

from __future__ import annotations

import hashlib
import json
from http import HTTPStatus
from typing import Any, Callable, Mapping

from catalogue import catalogue_activity as activity
from catalogue.catalogue_service_context import CatalogueWriteContext, append_activity_rows, load_works_payload
from catalogue.catalogue_source import normalize_optional_int, normalize_status, slug_id
from studio.services.media.publish_media_to_r2 import run_catalogue_upload


PublisherRunner = Callable[..., Mapping[str, object]]


def _publisher_error(error: BaseException) -> ValueError:
    message = str(error).strip()
    if message.startswith("Error:"):
        message = message.removeprefix("Error:").strip()
    return ValueError(message or "R2 media publisher failed")


def _default_publisher_runner(**kwargs: Any) -> Mapping[str, object]:
    try:
        return run_catalogue_upload(**kwargs)
    except SystemExit as error:
        raise _publisher_error(error) from error


def _work_request(context: CatalogueWriteContext, body: Mapping[str, Any]) -> tuple[str, dict[str, Any], int]:
    work_id = slug_id(body.get("work_id") or body.get("id"))
    works = load_works_payload(context.works_path)["works"]
    record = works.get(work_id)
    if not isinstance(record, dict):
        raise ValueError(f"work_id not found: {work_id}")
    if normalize_status(record.get("status")) != "published":
        raise ValueError("work media can be published only for a published work")
    if not str(record.get("project_filename") or "").strip():
        raise ValueError("project_filename is required before publishing work media")
    current_version = normalize_optional_int(record.get("media_version"))
    if current_version is None or current_version < 1:
        raise ValueError("media_version must be a positive whole number before publishing work media")
    requested_version = normalize_optional_int(body.get("expected_media_version"))
    if requested_version is None or requested_version < 1:
        raise ValueError("expected_media_version must be a positive whole number")
    return work_id, dict(record), current_version


def _safe_object_reason(status: str, reason: str) -> str:
    if status == "blocked_partial":
        return reason
    if status == "blocked_changed":
        return "remote object differs"
    if status == "failed":
        if reason.startswith("remote check failed"):
            return "remote check failed"
        if reason.startswith("upload failed"):
            return "upload failed"
        return "publisher operation failed"
    if status in {"would_upload", "would_overwrite"}:
        return "dry-run"
    if status == "unchanged":
        return "remote object matches local file"
    return ""


def _safe_media_version_reason(status: str, reason: str) -> str:
    if status == "failed":
        return "media-version finalization failed"
    if status == "not_promoted":
        return "complete successful primary variant set is required"
    if status in {"promoted", "current"}:
        return reason
    return ""


def _compact_report(report: Mapping[str, object]) -> dict[str, Any]:
    raw_counts = report.get("counts") if isinstance(report.get("counts"), Mapping) else {}
    counts = {str(key): int(value) for key, value in raw_counts.items() if int(value)}
    objects = []
    for item in report.get("objects") or []:
        if not isinstance(item, Mapping):
            continue
        status = str(item.get("status") or "")
        objects.append(
            {
                "width": int(item.get("width") or 0),
                "status": status,
                "reason": _safe_object_reason(status, str(item.get("reason") or "")),
            }
        )
    missing_variants = []
    for item in report.get("missing_variants") or []:
        if not isinstance(item, Mapping):
            continue
        missing_variants.append(
            {
                "missing_widths": [int(value) for value in item.get("missing_widths") or []],
                "present_widths": [int(value) for value in item.get("present_widths") or []],
            }
        )
    media_versions = []
    for item in report.get("media_versions") or []:
        if not isinstance(item, Mapping):
            continue
        status = str(item.get("status") or "")
        media_versions.append(
            {
                "status": status,
                "previous_version": item.get("previous_version"),
                "media_version": item.get("media_version"),
                "advanced": bool(item.get("advanced")),
                "reason": _safe_media_version_reason(status, str(item.get("reason") or "")),
            }
        )

    requires_force = counts.get("would_overwrite", 0) > 0
    blocking_count = sum(
        count
        for status, count in counts.items()
        if status == "failed" or status.startswith("blocked")
    )
    blocking_count += sum(1 for item in media_versions if item["status"] in {"failed", "not_promoted"})
    upload_count = counts.get("would_upload", 0) + counts.get("uploaded", 0)
    overwrite_count = counts.get("would_overwrite", 0) + counts.get("overwritten", 0)
    current_count = counts.get("unchanged", 0)
    parts = []
    if upload_count:
        parts.append(f"{upload_count} new")
    if overwrite_count:
        parts.append(f"{overwrite_count} replacement")
    if current_count:
        parts.append(f"{current_count} current")
    summary = "R2 primary variants: " + (", ".join(parts) if parts else "none") + "."
    if missing_variants:
        missing = sorted({width for item in missing_variants for width in item["missing_widths"]})
        summary += f" Missing local widths: {', '.join(str(width) for width in missing)}."
    if requires_force:
        summary += " Confirmation will overwrite changed remote objects."
    if blocking_count:
        summary += " Publishing is blocked until the reported failures are resolved."

    return {
        "blocked": blocking_count > 0,
        "requires_force": requires_force,
        "summary": summary,
        "counts": counts,
        "missing_variants": missing_variants,
        "objects": objects,
        "media_versions": media_versions,
    }


def _preview_fingerprint(report: Mapping[str, object], *, work_id: str, media_version: int) -> str:
    objects = []
    for item in report.get("objects") or []:
        if not isinstance(item, Mapping):
            continue
        objects.append(
            {
                "width": int(item.get("width") or 0),
                "size": int(item.get("size") or 0),
                "md5": str(item.get("md5") or ""),
                "status": str(item.get("status") or ""),
                "remote_size": item.get("remote_size"),
                "remote_etag": str(item.get("remote_etag") or ""),
            }
        )
    missing = []
    for item in report.get("missing_variants") or []:
        if not isinstance(item, Mapping):
            continue
        missing.append(
            {
                "missing_widths": sorted(int(value) for value in item.get("missing_widths") or []),
                "present_widths": sorted(int(value) for value in item.get("present_widths") or []),
            }
        )
    payload = {
        "schema": "catalogue_media_publish_preview_v1",
        "work_id": work_id,
        "media_version": media_version,
        "objects": sorted(objects, key=lambda item: item["width"]),
        "missing_variants": missing,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _run(
    context: CatalogueWriteContext,
    *,
    work_id: str,
    write: bool,
    force: bool,
    publisher_runner: PublisherRunner,
) -> Mapping[str, object]:
    try:
        return publisher_runner(
            repo_root=context.repo_root,
            kind="works",
            item_id=work_id,
            write=write,
            force=force,
            changed_only=False,
            allow_partial=False,
        )
    except SystemExit as error:
        raise _publisher_error(error) from error


def media_publish_preview_response(
    context: CatalogueWriteContext,
    body: Mapping[str, Any],
    *,
    publisher_runner: PublisherRunner = _default_publisher_runner,
) -> tuple[HTTPStatus, dict[str, Any]]:
    work_id, _record, current_version = _work_request(context, body)
    requested_version = normalize_optional_int(body.get("expected_media_version"))
    if requested_version != current_version:
        return HTTPStatus.CONFLICT, {
            "ok": False,
            "error": "confirmed media version changed since this page loaded",
            "work_id": work_id,
            "media_version": current_version,
        }
    report = _run(
        context,
        work_id=work_id,
        write=False,
        force=True,
        publisher_runner=publisher_runner,
    )
    preview = _compact_report(report)
    preview["preview_fingerprint"] = _preview_fingerprint(
        report,
        work_id=work_id,
        media_version=current_version,
    )
    return HTTPStatus.OK, {
        "ok": True,
        "work_id": work_id,
        "media_version": current_version,
        "preview": preview,
    }


def media_publish_apply_response(
    context: CatalogueWriteContext,
    body: Mapping[str, Any],
    *,
    publisher_runner: PublisherRunner = _default_publisher_runner,
) -> tuple[HTTPStatus, dict[str, Any]]:
    work_id, _record, current_version = _work_request(context, body)
    requested_version = normalize_optional_int(body.get("expected_media_version"))
    if requested_version != current_version:
        return HTTPStatus.CONFLICT, {
            "ok": False,
            "error": "confirmed media version changed since preview; refresh and try again",
            "work_id": work_id,
            "media_version": current_version,
        }
    force = bool(body.get("force"))
    if force and body.get("confirm_overwrite") is not True:
        raise ValueError("confirm_overwrite must be true before replacing remote media")
    requested_fingerprint = str(body.get("preview_fingerprint") or "").strip()
    if len(requested_fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in requested_fingerprint):
        raise ValueError("preview_fingerprint must be the value returned by media publish preview")
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_PUBLISH_WORK_MEDIA,
        record_id=work_id,
    )
    current_preview_report = _run(
        context,
        work_id=work_id,
        write=False,
        force=True,
        publisher_runner=publisher_runner,
    )
    current_preview = _compact_report(current_preview_report)
    if current_preview["blocked"]:
        return HTTPStatus.BAD_REQUEST, {
            "ok": False,
            "error": "R2 media publishing preview is now blocked",
            "work_id": work_id,
            "media_version": current_version,
            "preview": current_preview,
        }
    current_fingerprint = _preview_fingerprint(
        current_preview_report,
        work_id=work_id,
        media_version=current_version,
    )
    if requested_fingerprint != current_fingerprint or force != bool(current_preview["requires_force"]):
        return HTTPStatus.CONFLICT, {
            "ok": False,
            "error": "local or remote media changed since preview; review the new plan before publishing",
            "work_id": work_id,
            "media_version": current_version,
        }
    report = _run(
        context,
        work_id=work_id,
        write=not context.dry_run,
        force=force,
        publisher_runner=publisher_runner,
    )
    result = _compact_report(report)
    if result["blocked"]:
        return HTTPStatus.BAD_GATEWAY, {
            "ok": False,
            "error": "R2 media publishing did not complete",
            "work_id": work_id,
            "media_version": current_version,
            "result": result,
        }

    record = load_works_payload(context.works_path)["works"].get(work_id)
    if not isinstance(record, dict):
        raise ValueError(f"work_id not found after media publishing: {work_id}")
    confirmed_version = normalize_optional_int(record.get("media_version")) or current_version
    payload: dict[str, Any] = {
        "ok": True,
        "status": "dry_run" if context.dry_run else "completed",
        "work_id": work_id,
        "previous_media_version": current_version,
        "media_version": confirmed_version,
        "record": dict(record),
        "result": result,
    }
    if context.dry_run:
        payload["dry_run"] = True
        return HTTPStatus.OK, payload
    if activity_context:
        payload["activity_context"] = activity_context
        append_activity_rows(
            context.repo_root,
            payload,
            [
                activity.studio_activity_entry(
                    activity_context,
                    now_utc=activity.utc_now(),
                    script_purpose_id="publish-media-to-r2",
                    status="completed",
                    record_groups=activity.activity_record_groups(works=[work_id]),
                    detail_items=[
                        result["summary"],
                        f"Confirmed work media version {confirmed_version}",
                    ],
                    source_refs=activity.catalogue_log_source_ref(),
                )
            ],
        )
    return HTTPStatus.OK, payload
