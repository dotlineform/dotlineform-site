#!/usr/bin/env python3
"""Source text and summary helpers for staged Docs source imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_scope_config import DOCS_SCOPE_CONFIGS, resolve_external_data_root


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


def viewer_url_for(scope: str, doc_id: str) -> str:
    normalized_scope = scope if scope in DOCS_SCOPE_CONFIGS else next(iter(DOCS_SCOPE_CONFIGS))
    return f"/docs/?scope={normalized_scope}&doc={doc_id}"


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
