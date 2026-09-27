"""Docs broken-link audit route helpers for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_broken_links import audit_docs_broken_links
from docs_management_document_target import normalize_managed_document_collection_target
from docs_management_context import log_event


def handle_broken_links(repo_root: Path, body: Dict[str, Any]) -> Dict[str, Any]:
    """Validate report-owned source selection independently of audit destinations."""
    if set(body) - { "report_context"}:
        raise ValueError("Unexpected Broken Links request fields")
    context = normalize_managed_document_collection_target(body.get("report_context"))
    if context:
        raise ValueError("Broken Links requires an ordinary report context")
    payload = audit_docs_broken_links(repo_root)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    log_event(
        repo_root,
        "docs_broken_links",
        {
            "total": int(summary.get("total") or 0),
        },
    )
    return payload
