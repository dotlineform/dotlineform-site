#!/usr/bin/env python3
"""Document Data Sharing activity helpers."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict

from studio_activity import (
    append_studio_activity,
    normalize_activity_context_from_contract,
    studio_activity_entry,
)


DATA_SHARING_LOG_REL_PATH = Path("var/analytics/logs/analytics_data_sharing_api.log")
DATA_SHARING_ACTIVITY_SOURCE_REFS = [{"kind": "log", "path": str(DATA_SHARING_LOG_REL_PATH)}]
DATA_SHARING_PREPARE_PATH = "/prepare"
DATA_SHARING_APPLY_PATH = "/apply"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compact_ids(values: Any, limit: int = 12) -> list[str]:
    if not isinstance(values, list):
        return []
    ids = [str(value or "").strip() for value in values if str(value or "").strip()]
    return ids[:limit]


def docs_activity_status(*, ok: bool = True, errors: int = 0, warnings: int = 0) -> str:
    if not ok or errors > 0:
        return "failed"
    if warnings > 0:
        return "warning"
    return "completed"


def attach_docs_activity(
    repo_root: Path,
    body: Dict[str, Any],
    payload: Dict[str, Any],
    *,
    endpoint: str,
    script_purpose_id: str,
    record_id: str,
    record_groups: Dict[str, Any],
    detail_items: list[str],
    status: str = "completed",
) -> None:
    raw_context = body.get("activity_context")
    if not raw_context:
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
        payload["activity_context"] = activity_context
        append_studio_activity(
            repo_root,
            studio_activity_entry(
                activity_context,
                script_purpose_id=script_purpose_id,
                now_utc=utc_now(),
                status=status,
                record_groups=record_groups,
                detail_items=detail_items,
                source_refs=DATA_SHARING_ACTIVITY_SOURCE_REFS,
            ),
        )
        payload["activity_log"] = {"written_count": 1}
    except Exception as exc:  # noqa: BLE001
        payload["activity_log"] = {"written_count": 0, "error": str(exc)}


def maybe_attach_docs_export_activity(repo_root: Path, body: Dict[str, Any], payload: Dict[str, Any], dry_run: bool) -> None:
    if dry_run or not payload.get("output_written"):
        return
    if str(payload.get("adapter_id") or "").strip() not in {"", "documents"}:
        return
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    issue_counts = payload.get("issue_counts") if isinstance(payload.get("issue_counts"), dict) else {}
    output_file = str(payload.get("output_file") or "").strip()
    exported = int(counts.get("exported") or 0)
    failed = int(counts.get("failed") or 0)
    warnings = int(issue_counts.get("warnings") or 0)
    attach_docs_activity(
        repo_root,
        body,
        payload,
        endpoint=DATA_SHARING_PREPARE_PATH,
        script_purpose_id="prepare-share-package",
        record_id=(
            f"{payload.get('data_domain') or body.get('data_domain')}:"
            f"{payload.get('config_id') or body.get('config_id')}"
        ),
        record_groups={"docs": compact_ids(body.get("doc_ids"))},
        detail_items=[
            str(payload.get("summary_text") or f"Exported {exported} document(s).").strip(),
            f"Output file: {output_file}" if output_file else "",
        ],
        status=docs_activity_status(ok=bool(payload.get("ok")), errors=failed, warnings=warnings),
    )


def maybe_attach_documents_import_apply_activity(
    repo_root: Path,
    body: Dict[str, Any],
    payload: Dict[str, Any],
    dry_run: bool,
) -> None:
    if dry_run or not body.get("confirm"):
        return
    if not (payload.get("summary_apply_written") or payload.get("hierarchy_apply_written")):
        return
    updates = payload.get("updates") if isinstance(payload.get("updates"), list) else []
    doc_ids = [str(item.get("doc_id") or "").strip() for item in updates if isinstance(item, dict)]
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    errors = int(counts.get("errors") or 0)
    warnings = int(counts.get("warnings") or 0)
    attach_docs_activity(
        repo_root,
        body,
        payload,
        endpoint=DATA_SHARING_APPLY_PATH,
        script_purpose_id="update-docs-source",
        record_id=str(body.get("staged_filename") or "").strip(),
        record_groups={"docs": doc_ids},
        detail_items=[
            str(payload.get("summary_text") or "Updated imported docs source data.").strip(),
            f"Updated {len(doc_ids)} source doc(s).",
            f"Backup: {payload.get('backup_dir')}" if payload.get("backup_dir") else "",
        ],
        status=docs_activity_status(ok=bool(payload.get("ok")), errors=errors, warnings=warnings),
    )


__all__ = [
    "DATA_SHARING_ACTIVITY_SOURCE_REFS",
    "DATA_SHARING_LOG_REL_PATH",
    "attach_docs_activity",
    "compact_ids",
    "docs_activity_status",
    "maybe_attach_docs_export_activity",
    "maybe_attach_documents_import_apply_activity",
]
