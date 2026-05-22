"""Docs broken-link audit route helpers for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_broken_links import audit_docs_broken_links
import docs_source_model as source_model
from docs_management_context import log_event


def handle_broken_links(repo_root: Path, body: Dict[str, Any]) -> Dict[str, Any]:
    scope = source_model.normalize_scope(body.get("scope"))
    payload = audit_docs_broken_links(repo_root, scope)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    log_event(
        repo_root,
        "docs_broken_links",
        {
            "scope": scope,
            "total": int(summary.get("total") or 0),
            "not_found": int(summary.get("not_found") or 0),
        },
    )
    return payload
