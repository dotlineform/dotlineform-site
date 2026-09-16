"""Docs broken-link audit route helpers for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_broken_links import audit_docs_broken_links
from docs_management_document_target import normalize_managed_document_collection_target
from docs_management_context import log_event
from docs_workspace_config import load_docs_stage


def handle_broken_links(repo_root: Path, body: Dict[str, Any]) -> Dict[str, Any]:
    """Validate report-owned source selection independently of audit destinations."""
    if set(body) - {"stage", "report_context"}:
        raise ValueError("Unexpected Broken Links request fields")
    context = normalize_managed_document_collection_target(body.get("report_context"))
    selected = normalize_managed_document_collection_target({
        key: body[key] for key in ("stage",) if key in body
    })
    if "sub_scope" in context:
        raise ValueError("Broken Links requires an ordinary report context")
    if context.get("stage") != "working" or selected != context:
        raise ValueError("Broken Links audits Working only")
    stage = selected["stage"]
    load_docs_stage(repo_root, stage)
    payload = audit_docs_broken_links(repo_root, stage=stage)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    log_event(
        repo_root,
        "docs_broken_links",
        {
            "stage": stage,
            "total": int(summary.get("total") or 0),
        },
    )
    return payload
