#!/usr/bin/env python3
"""Tag assignment write handlers for the Studio tag API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tags import tag_assignment_service as tag_assignments
from tags import tag_routes
from tags import tag_source_model as tag_source
from tags import tag_write_transactions as tag_transactions
from studio_tag_api import common


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
