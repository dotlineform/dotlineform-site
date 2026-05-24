#!/usr/bin/env python3
"""Tag-specific Studio activity helpers."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from analytics import tag_routes as routes
from studio_activity import normalize_activity_context_from_contract, studio_activity_entry


SCRIPT_PURPOSE_SAVE_TAG_DATA = "save-tag-data"
STUDIO_ANALYTICS_LOG_REL_PATH = Path("var/studio/logs/studio_analytics_api.log")

ACTIVITY_WRITE_ENDPOINTS = (
    routes.SAVE_TAGS_PATH,
    routes.IMPORT_ASSIGNMENTS_APPLY_PATH,
    routes.IMPORT_REGISTRY_PATH,
    routes.IMPORT_ALIASES_PATH,
    routes.DELETE_ALIAS_PATH,
    routes.MUTATE_ALIAS_APPLY_PATH,
    routes.PROMOTE_ALIAS_APPLY_PATH,
    routes.DEMOTE_TAG_APPLY_PATH,
    routes.MUTATE_TAG_APPLY_PATH,
)

TAG_ACTIVITY_CHANGED_KEYS = (
    "added",
    "overwritten",
    "removed",
    "applied_series",
    "canonical_added",
    "alias_deleted",
    "aliases_rewritten",
    "aliases_removed_empty",
    "aliases_removed_redundant",
    "series_rows_touched",
    "work_rows_touched",
    "series_tag_refs_rewritten",
    "work_tag_refs_rewritten",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tag_activity_status(stats: Mapping[str, Any]) -> str:
    error_count = int(stats.get("invalid_count") or stats.get("missing_count") or 0)
    conflict_count = int(stats.get("conflict_count") or 0)
    if error_count:
        return "failed"
    if conflict_count:
        return "warning"
    return "completed"


def tag_activity_changed(stats: Mapping[str, Any]) -> bool:
    if any(int(stats.get(key) or 0) > 0 for key in TAG_ACTIVITY_CHANGED_KEYS):
        return True
    if stats.get("changed") is True:
        return True
    if stats.get("canonical_changed") or stats.get("description_changed"):
        return True
    return False


def tag_activity_record_groups(
    activity_context: Mapping[str, str],
    record_groups: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    resolved = dict(record_groups or {})
    if "tag_id" in activity_context and not resolved.get("tags"):
        resolved["tags"] = [activity_context["tag_id"]]
    if "alias" in activity_context and not resolved.get("aliases"):
        resolved["aliases"] = [activity_context["alias"]]
    return resolved


def attach_tag_activity(
    *,
    repo_root: str | Path,
    endpoint: str,
    dry_run: bool,
    append_activity: Callable[[Dict[str, Any]], None],
    body: Mapping[str, Any],
    response_payload: Dict[str, Any],
    script_purpose_id: str = SCRIPT_PURPOSE_SAVE_TAG_DATA,
    record_id: str = "",
    record_groups: Optional[Mapping[str, Any]] = None,
    detail_items: Optional[list[str]] = None,
    activity_id_suffix: str = "",
    status: str = "completed",
) -> None:
    raw_context = body.get("activity_context")
    if not raw_context or dry_run:
        return
    try:
        activity_context = normalize_activity_context_from_contract(
            repo_root,
            raw_context,
            endpoint=endpoint,
            record_id=record_id,
        )
        if not activity_context:
            return
        response_payload["activity_context"] = activity_context
        append_activity(
            studio_activity_entry(
                activity_context,
                script_purpose_id=script_purpose_id,
                now_utc=str(response_payload.get("updated_at_utc") or utc_now()),
                status=status,
                record_groups=tag_activity_record_groups(activity_context, record_groups),
                detail_items=detail_items or [str(response_payload.get("summary_text") or "Updated tag data.")],
                source_refs=[{"kind": "log", "path": str(STUDIO_ANALYTICS_LOG_REL_PATH)}],
                activity_id_suffix=activity_id_suffix,
            )
        )
        response_payload["activity_log"] = {"written_count": 1}
    except Exception as exc:  # noqa: BLE001
        response_payload["activity_log"] = {"written_count": 0, "error": str(exc)}
