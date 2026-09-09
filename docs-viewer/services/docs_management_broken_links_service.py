"""Docs broken-link audit route helpers for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_broken_links import audit_docs_broken_links
from docs_management_document_target import normalize_managed_document_collection_target
from docs_management_context import log_event
from docs_scope_config import load_docs_scope_configs, select_scope_stage


def handle_broken_links(repo_root: Path, body: Dict[str, Any]) -> Dict[str, Any]:
    """Validate report-owned source selection independently of audit destinations."""
    if set(body) - {"scope", "stage", "report_context"}:
        raise ValueError("Unexpected Broken Links request fields")
    context = normalize_managed_document_collection_target(body.get("report_context"))
    selected = normalize_managed_document_collection_target({
        key: body[key] for key in ("scope", "stage") if key in body
    })
    if "sub_scope" in context:
        raise ValueError("Broken Links requires a scope-level report context")
    configs = load_docs_scope_configs(repo_root)
    for target in (context, selected):
        if target["scope"] not in configs:
            raise ValueError("Unknown Broken Links scope")
        select_scope_stage(configs[target["scope"]], target.get("stage"))
    if context["scope"] == "analysis":
        if context.get("stage") != "working" or selected != context:
            raise ValueError("Analysis Broken Links audits Analysis Working only")
    elif selected["scope"] == "analysis":
        raise ValueError("Analysis sources belong to the Analysis Working report")
    scope = selected["scope"]
    stage = selected.get("stage")
    payload = audit_docs_broken_links(repo_root, scope, stage)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    log_event(
        repo_root,
        "docs_broken_links",
        {
            "scope": scope,
            **({"stage": stage} if stage else {}),
            "total": int(summary.get("total") or 0),
        },
    )
    return payload
