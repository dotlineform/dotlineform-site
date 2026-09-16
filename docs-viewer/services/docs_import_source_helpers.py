#!/usr/bin/env python3
"""Source text and summary helpers for staged Docs source imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlencode

from docs_workspace_config import resolve_external_data_root
from docs_management_document_target import normalize_managed_document_target


def relative_path(repo_root: Path, path: Path) -> str:
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        pass
    try:
        return resolved_path.relative_to(resolve_external_data_root().resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("source path is outside the repo and external Docs Viewer root") from exc


def viewer_url_for(doc_id: str, *, stage: str) -> str:
    """Link to the exact imported ordinary document without a scope fallback."""
    target = normalize_managed_document_target({"stage": stage, "doc_id": doc_id})
    return "/docs/?" + urlencode({"stage": target["stage"], "doc": target["doc_id"]})


def import_summary_text(
    operation: str,
    doc_id: str,
    staged_filename: str,
    interactive_html_written: list[Dict[str, Any]],
) -> str:
    action = "Created" if operation == "create" else "Overwrote"
    summary = f"{action} {doc_id} from {staged_filename}."
    if interactive_html_written:
        count = len(interactive_html_written)
        suffix = "" if count == 1 else "s"
        summary += f" Copied {count} interactive HTML script file{suffix}."
    return summary


def interactive_html_overwrite_summary(plans: list[Dict[str, Any]]) -> str:
    if len(plans) == 1:
        return f"Interactive HTML asset overwrite required for {plans[0]['target_path']}."
    return f"Interactive HTML asset overwrite required for {len(plans)} script files."
