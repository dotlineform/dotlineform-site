#!/usr/bin/env python3
"""Tag assignment write handlers for the Analytics app API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tag_services import tag_activity
from tag_services import tag_assignment_service as tag_assignments
from tag_services import tag_routes
from tag_services import tag_source_model as tag_source
from tag_services import tag_write_transactions as tag_transactions
from tag_write_api import common


def save_tags_response(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, object]:
    assignments_path = (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve()
    allowed_write_paths = {assignments_path}

    series_id = body.get("series_id")
    work_id = body.get("work_id")
    keep_work = body.get("keep_work")
    tags = body.get("tags")

    now_utc = common.utc_now()
    payload = tag_source.load_assignments(assignments_path)
    updated_payload, response_payload, would_write = tag_assignments.plan_assignment_save(
        payload,
        series_id,
        work_id,
        keep_work,
        tags,
        now_utc,
    )
    deleted = bool(response_payload.get("deleted"))
    normalized_series_id = str(response_payload.get("series_id") or "")
    normalized_work_id = response_payload.get("work_id")
    normalized_keep_work = response_payload.get("keep_work")

    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = would_write
    else:
        if assignments_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(assignments_path, updated_payload)

    common.log_event(
        repo_root,
        "save_tags",
        {
            "series_id": normalized_series_id,
            "work_id": normalized_work_id,
            "keep_work": normalized_keep_work,
            "tag_count": response_payload["tag_count"],
            "deleted": deleted,
            "dry_run": dry_run,
        },
    )
    common.attach_tag_activity(
        repo_root=repo_root,
        endpoint=tag_routes.SAVE_TAGS_PATH,
        dry_run=dry_run,
        body=body,
        response_payload=response_payload,
        record_id=normalized_series_id,
        record_groups={
            "series": [normalized_series_id],
            "works": [normalized_work_id] if normalized_work_id else [],
        },
        detail_items=[
            f"Saved tag assignments for series {normalized_series_id}.",
            f"Updated work {normalized_work_id}." if normalized_work_id else "",
            f"Tag count: {response_payload['tag_count']}.",
        ],
        activity_id_suffix=f"work:{normalized_work_id}" if normalized_work_id else f"series:{normalized_series_id}",
    )
    return response_payload


def import_tag_assignments_response(
    repo_root: Path,
    body: dict[str, Any],
    *,
    preview: bool,
    dry_run: bool = False,
) -> dict[str, object]:
    assignments_path = (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve()
    series_index_path = (repo_root / tag_source.SERIES_INDEX_REL_PATH).resolve()
    allowed_write_paths = {assignments_path}

    import_assignments = tag_source.sanitize_import_assignments_session(body.get("import_assignments"))
    import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))
    resolutions = sanitize_import_resolutions(body.get("resolutions"))

    now_utc = common.utc_now()
    existing_payload = tag_source.load_assignments(assignments_path)
    series_index_payload = tag_source.load_series_index(series_index_path)
    preview_payload = tag_assignments.preview_assignment_import(
        existing_payload,
        import_assignments,
        series_index_payload,
    )
    response_payload = tag_assignments.build_assignment_import_preview_response(
        preview_payload,
        import_filename,
        now_utc,
    )

    if preview:
        common.log_event(
            repo_root,
            "import_tag_assignments_preview",
            {
                "staged_series_count": preview_payload["staged_series_count"],
                "applicable_count": preview_payload["applicable_count"],
                "conflict_count": preview_payload["conflict_count"],
                "invalid_count": preview_payload["invalid_count"],
                "missing_count": preview_payload["missing_count"],
                "dry_run": dry_run,
            },
        )
        return response_payload

    updated_payload, apply_stats = tag_assignments.apply_assignment_import(
        existing_payload,
        import_assignments,
        preview_payload,
        resolutions,
        now_utc,
    )
    response_payload = tag_assignments.build_assignment_import_apply_response(response_payload, apply_stats)
    apply_summary_text = str(response_payload.get("summary_text") or "")

    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **apply_stats,
        }
    else:
        if assignments_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(assignments_path, updated_payload)

    common.log_event(
        repo_root,
        "import_tag_assignments",
        {
            **apply_stats,
            "dry_run": dry_run,
        },
    )
    if tag_activity.tag_activity_changed(apply_stats):
        common.attach_tag_activity(
            repo_root=repo_root,
            endpoint=tag_routes.IMPORT_ASSIGNMENTS_APPLY_PATH,
            dry_run=dry_run,
            body=body,
            response_payload=response_payload,
            detail_items=[
                apply_summary_text,
                f"Applied series: {apply_stats.get('applied_series')}; skipped: {apply_stats.get('skipped_series')}.",
            ],
            status=tag_activity.tag_activity_status(apply_stats),
        )
    return response_payload


def sanitize_import_resolutions(raw_resolutions: object) -> dict[str, str]:
    resolutions: dict[str, str] = {}
    if raw_resolutions is None:
        return resolutions
    if not isinstance(raw_resolutions, dict):
        raise ValueError("resolutions must be an object")
    for raw_series_id, raw_resolution in raw_resolutions.items():
        series_id = str(raw_series_id or "").strip().lower()
        if not series_id:
            continue
        resolution = str(raw_resolution or "").strip().lower()
        if resolution not in {"overwrite", "skip"}:
            raise ValueError(f"resolutions[{series_id}] must be overwrite or skip")
        resolutions[series_id] = resolution
    return resolutions
