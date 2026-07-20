#!/usr/bin/env python3
"""Studio Activity helpers for Docs Management service actions."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict

import docs_management_routes as routes
from docs_source_model import normalize_scope
from studio_activity import (
    append_studio_activity,
    normalize_activity_context_from_contract,
    studio_activity_entry,
)


DOCS_MANAGEMENT_LOG_REL_PATH = Path("var/docs/logs/docs_management_service.log")
DOCS_ACTIVITY_SOURCE_REFS = [{"kind": "log", "path": str(DOCS_MANAGEMENT_LOG_REL_PATH)}]
DOCUMENT_PACKAGE_PREPARE_PATH = "/docs/packages/prepare"
DOCUMENT_PACKAGE_APPLY_PATH = "/docs/packages/returned/apply"


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
                source_refs=DOCS_ACTIVITY_SOURCE_REFS,
            ),
        )
        payload["activity_log"] = {"written_count": 1}
    except Exception as exc:  # noqa: BLE001
        payload["activity_log"] = {"written_count": 0, "error": str(exc)}


def maybe_attach_broken_links_activity(repo_root: Path, body: Dict[str, Any], payload: Dict[str, Any]) -> None:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    scope = normalize_scope(payload.get("scope") or body.get("scope"))
    total = int(summary.get("total") or 0)
    attach_docs_activity(
        repo_root,
        body,
        payload,
        endpoint=routes.BROKEN_LINKS_PATH,
        script_purpose_id="run-audit",
        record_id=scope,
        record_groups={"docs": [scope]},
        detail_items=[
            f"Ran broken-links audit for {scope} docs.",
            f"Found {total} broken link(s).",
        ],
        status="warning" if total else "completed",
    )


def maybe_attach_docs_export_activity(repo_root: Path, body: Dict[str, Any], payload: Dict[str, Any], dry_run: bool) -> None:
    if dry_run or not payload.get("output_written"):
        return
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    issue_counts = payload.get("issue_counts") if isinstance(payload.get("issue_counts"), dict) else {}
    output_file = str(payload.get("output_file") or "").strip()
    export_id = str(payload.get("export_id") or "").strip()
    exported = int(counts.get("exported") or 0)
    failed = int(counts.get("failed") or 0)
    warnings = int(issue_counts.get("warnings") or 0)
    activity_body = dict(body)
    raw_context = body.get("activity_context")
    if isinstance(raw_context, dict):
        activity_body["activity_context"] = {**raw_context, "export_id": export_id}
    attach_docs_activity(
        repo_root,
        activity_body,
        payload,
        endpoint=DOCUMENT_PACKAGE_PREPARE_PATH,
        script_purpose_id="prepare-share-package",
        record_id=export_id,
        record_groups={"docs": compact_ids(body.get("doc_ids"))},
        detail_items=[
            str(payload.get("summary_text") or f"Exported {exported} document(s).").strip(),
            f"Output file: {output_file}" if output_file else "",
        ],
        status=docs_activity_status(ok=bool(payload.get("ok")), errors=failed, warnings=warnings),
    )


def maybe_attach_import_source_activity(repo_root: Path, body: Dict[str, Any], payload: Dict[str, Any], dry_run: bool) -> None:
    if payload.get("collection") is True:
        if dry_run or payload.get("preview_only"):
            return
        records = payload.get("records") if isinstance(payload.get("records"), list) else []
        applied_doc_ids = [
            str(record.get("doc_id") or "").strip()
            for record in records
            if isinstance(record, dict) and record.get("status") in {"created", "overwritten"}
        ]
        skipped_notes = [
            str(record.get("note") or "").strip()
            for record in records
            if isinstance(record, dict) and record.get("status") == "skipped" and str(record.get("note") or "").strip()
        ]
        counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
        report_path = str(payload.get("report_path") or "").strip()
        attach_docs_activity(
            repo_root,
            body,
            payload,
            endpoint=routes.IMPORT_SOURCE_PATH,
            script_purpose_id="import-source-data",
            record_id=str(body.get("staged_filename") or "").strip(),
            record_groups={
                "docs": compact_ids(applied_doc_ids),
                "files": compact_ids([report_path] if report_path else []),
            },
            detail_items=[
                (
                    f"Collection import {payload.get('outcome') or 'completed'}: "
                    f"{counts.get('created', 0)} created, {counts.get('overwritten', 0)} overwritten, "
                    f"{counts.get('skipped', 0)} skipped, {counts.get('failed', 0)} failed, "
                    f"{counts.get('not_attempted', 0)} not attempted."
                ),
                f"Result report: {report_path}" if report_path else "",
                *[f"Skipped-record note: {note}" for note in skipped_notes],
            ],
            status=(
                "completed" if payload.get("outcome") == "completed"
                else "failed" if payload.get("outcome") == "failed"
                else "warning"
            ),
        )
        return
    if dry_run or payload.get("preview_only"):
        return
    doc_id = str(payload.get("doc_id") or "").strip()
    if not doc_id:
        return
    media_written = payload.get("inline_media_written") if isinstance(payload.get("inline_media_written"), list) else []
    interactive_written = payload.get("interactive_html_written") if isinstance(payload.get("interactive_html_written"), list) else []
    details = [
        str(payload.get("summary_text") or f"Imported docs source {doc_id}.").strip(),
        f"Wrote source file: {payload.get('path')}" if payload.get("path") else "",
        f"Materialized {len(media_written)} inline media file(s)." if media_written else "",
        f"Copied {len(interactive_written)} interactive HTML script file(s)." if interactive_written else "",
    ]
    attach_docs_activity(
        repo_root,
        body,
        payload,
        endpoint=routes.IMPORT_SOURCE_PATH,
        script_purpose_id="import-source-data",
        record_id=str(body.get("staged_filename") or "").strip(),
        record_groups={
            "docs": [doc_id],
            "files": compact_ids(
                [item.get("path") for item in media_written if isinstance(item, dict)]
                + [item.get("target_path") for item in interactive_written if isinstance(item, dict)]
            ),
        },
        detail_items=details,
        status="completed",
    )


def maybe_attach_documents_import_apply_activity(repo_root: Path, body: Dict[str, Any], payload: Dict[str, Any], dry_run: bool) -> None:
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
        endpoint=DOCUMENT_PACKAGE_APPLY_PATH,
        script_purpose_id="update-docs-source",
        record_id=str(body.get("staged_filename") or "").strip(),
        record_groups={"docs": doc_ids},
        detail_items=[
            str(payload.get("summary_text") or "Updated imported docs source data.").strip(),
            f"Updated {len(doc_ids)} source doc(s).",
        ],
        status=docs_activity_status(ok=bool(payload.get("ok")), errors=errors, warnings=warnings),
    )
