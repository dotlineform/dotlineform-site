#!/usr/bin/env python3
"""Current Docs source context for returned document-package review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_document_packages import source_context as docs_source_context
from docs_document_packages.returned_common import issue, normalize_text, scope_title
from docs_scope_config import document_source_path

def load_current_docs_context(repo_root: Path, scope: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    context: dict[str, Any] = {
        "source_loaded": False,
        "source_root": "",
        "doc_count": 0,
        "renderable_count": 0,
        "docs_by_id": {},
        "renderable_ids": [],
    }
    try:
        loaded_context = docs_source_context.load_document_package_source_context(repo_root, scope)
    except (FileNotFoundError, json.JSONDecodeError, ValueError, RuntimeError, OSError) as exc:
        issues.append(issue("warning", "current_source_unreadable", f"current {scope} docs source context could not be read: {exc}"))
        return context, issues

    docs_by_id: dict[str, dict[str, Any]] = {}
    renderable_ids: list[str] = []
    for item in loaded_context.records:
        doc_id = item.doc_id
        docs_by_id[doc_id] = item
        renderable_ids.append(doc_id)
    context.update(
        {
            "source_loaded": True,
            "source_root": document_source_path(loaded_context.scope_config).as_posix(),
            "doc_count": len(docs_by_id),
            "renderable_count": len(set(renderable_ids)),
            "docs_by_id": docs_by_id,
            "renderable_ids": sorted(set(renderable_ids)),
        }
    )
    return context, issues

def current_report_context(current: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_loaded": bool(current.get("source_loaded")),
        "source_root": normalize_text(current.get("source_root")),
        "doc_count": int(current.get("doc_count") or 0),
        "renderable_count": int(current.get("renderable_count") or 0),
    }


def add_current_library_report(
    records: list[dict[str, Any]],
    *,
    current: dict[str, Any],
    scope: str = "library",
) -> list[dict[str, Any]]:
    if not current.get("source_loaded"):
        return []

    issues: list[dict[str, Any]] = []
    docs_by_id = current.get("docs_by_id") if isinstance(current.get("docs_by_id"), dict) else {}
    renderable_ids = set(current.get("renderable_ids") if isinstance(current.get("renderable_ids"), list) else [])

    staged_ids = {
        normalize_text(record.get("doc_id"))
        for record in records
        if normalize_text(record.get("doc_id"))
    }
    for record in records:
        record_index = record.get("record_index") if isinstance(record.get("record_index"), int) else None
        line = record.get("line") if isinstance(record.get("line"), int) else None
        doc_id = normalize_text(record.get("doc_id"))
        parent_id = normalize_text(record.get("parent_id"))
        current_doc = docs_by_id.get(doc_id)
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}

        current_state: dict[str, Any] = {
            "exists": bool(current_doc),
            "viewable": None,
            "source_exists": bool(current_doc),
            "source_renderable": False,
            "current_summary": "",
            "staged_current_summary_matches": None,
            "parent_exists": None,
            "parent_source_exists": None,
            "parent_source_renderable": None,
        }
        if current_doc:
            current_state["viewable"] = current_doc.viewable
            current_state["source_renderable"] = doc_id in renderable_ids
            current_state["current_summary"] = current_doc.summary
            if "current_summary" in metadata:
                current_state["staged_current_summary_matches"] = str(metadata.get("current_summary") or "") == current_doc.summary
        record["current_library"] = current_state

        if not doc_id:
            continue
        if not current_doc:
            issues.append(
                issue(
                    "warning",
                    "unknown_doc_id",
                    f"record doc_id is not in the current {scope_title(scope)} source context: {doc_id}",
                    record_index=record_index,
                    line=line,
                    doc_id=doc_id,
                )
            )
        if current_doc and doc_id not in renderable_ids:
            issues.append(
                issue(
                    "warning",
                    "current_source_unrenderable",
                    f"record exists in the current {scope_title(scope)} source context but could not be rendered: {doc_id}",
                    record_index=record_index,
                    line=line,
                    doc_id=doc_id,
                )
            )

        if parent_id:
            parent_doc = docs_by_id.get(parent_id)
            current_state["parent_exists"] = bool(parent_doc)
            current_state["parent_source_exists"] = bool(parent_doc)
            current_state["parent_source_renderable"] = parent_id in renderable_ids
            if parent_id not in docs_by_id and parent_id not in staged_ids:
                issues.append(
                    issue(
                        "warning",
                        "missing_parent_id",
                        f"parent_id is not in the current {scope_title(scope)} source context or staged records: {parent_id}",
                        record_index=record_index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
            elif parent_doc and parent_id not in renderable_ids:
                issues.append(
                    issue(
                        "warning",
                        "parent_source_unrenderable",
                        f"parent_id points to a current {scope_title(scope)} source context record that could not be rendered: {parent_id}",
                        record_index=record_index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
    return issues
