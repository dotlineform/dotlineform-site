#!/usr/bin/env python3
"""Docs Data Sharing returned-package review helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_import import parse_staged_import, render_markdown_previews, scope_title
import docs_source_model as source_model


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def record_issue_map(report: Dict[str, Any]) -> dict[int, list[Dict[str, Any]]]:
    issues_by_record: dict[int, list[Dict[str, Any]]] = {}
    for issue in report.get("issues", []):
        if not isinstance(issue, dict) or not isinstance(issue.get("record_index"), int):
            continue
        issues_by_record.setdefault(int(issue["record_index"]), []).append(issue)
    return issues_by_record


def duplicate_doc_ids(records: list[Dict[str, Any]]) -> set[str]:
    counts: dict[str, int] = {}
    for record in records:
        doc_id = normalize_text(record.get("doc_id"))
        if doc_id:
            counts[doc_id] = counts.get(doc_id, 0) + 1
    return {doc_id for doc_id, count in counts.items() if count > 1}


def ordered_document_records(records: list[Dict[str, Any]]) -> list[tuple[Dict[str, Any], int]]:
    ids = {normalize_text(record.get("doc_id")) for record in records if normalize_text(record.get("doc_id"))}
    children_by_parent: dict[str, list[Dict[str, Any]]] = {}
    for record in records:
        doc_id = normalize_text(record.get("doc_id"))
        parent_id = normalize_text(record.get("parent_id"))
        parent_key = parent_id if parent_id and parent_id != doc_id else ""
        children_by_parent.setdefault(parent_key, []).append(record)

    roots = [
        record
        for record in records
        if not normalize_text(record.get("parent_id"))
        or normalize_text(record.get("parent_id")) not in ids
        or normalize_text(record.get("parent_id")) == normalize_text(record.get("doc_id"))
    ]
    ordered: list[tuple[Dict[str, Any], int]] = []
    rendered: set[int] = set()

    def visit(record: Dict[str, Any], depth: int, active_doc_ids: set[str]) -> None:
        identity = id(record)
        if identity in rendered:
            return
        rendered.add(identity)
        ordered.append((record, depth))
        doc_id = normalize_text(record.get("doc_id"))
        if not doc_id or doc_id in active_doc_ids:
            return
        next_active = set(active_doc_ids)
        next_active.add(doc_id)
        for child in children_by_parent.get(doc_id, []):
            visit(child, depth + 1, next_active)

    for record in roots:
        visit(record, 0, set())
    for record in records:
        visit(record, 0, set())
    return ordered


def review_row_meta(scope: str, record: Dict[str, Any], duplicates: set[str]) -> str:
    doc_id = normalize_text(record.get("doc_id"))
    current_library = record.get("current_library") if isinstance(record.get("current_library"), dict) else {}
    parts = [doc_id or "missing doc_id"]
    if doc_id in duplicates:
        parts.append("duplicate doc_id")
    if current_library.get("exists") is False:
        parts.append(f"not in current {scope_title(scope)}")
    return " · ".join(parts)


def build_review_rows(report: Dict[str, Any], scope: str) -> list[Dict[str, Any]]:
    records = [record for record in report.get("records", []) if isinstance(record, dict)]
    issues_by_record = record_issue_map(report)
    duplicates = duplicate_doc_ids(records)
    rows: list[Dict[str, Any]] = []
    for index, item in enumerate(report.get("preview_files", [])):
        if not isinstance(item, dict) or normalize_text(item.get("kind")) != "relationship_tree":
            continue
        path = normalize_text(item.get("path"))
        rows.append(
            {
                "id": path or f"relationship-tree-{index + 1}",
                "type": "relationship_tree",
                "title": "Relationship tree",
                "meta": f"{int(item.get('record_count') or 0)} records",
                "record_index": None,
                "selectable": False,
                "record_groups": {"files": [path]} if path else {},
                "issues": [],
                "depth": 0,
            }
        )
    for record, depth in ordered_document_records(records):
        record_index = int(record.get("record_index")) if isinstance(record.get("record_index"), int) else len(rows)
        doc_id = normalize_text(record.get("doc_id"))
        rows.append(
            {
                "id": f"{doc_id or 'missing-doc-id'}-record-{record_index + 1}",
                "type": "document",
                "title": normalize_text(record.get("title")) or "missing title",
                "meta": review_row_meta(scope, record, duplicates),
                "record_index": record_index,
                "selectable": True,
                "record_groups": {"documents": [doc_id]} if doc_id else {},
                "issues": issues_by_record.get(record_index, []),
                "depth": depth,
            }
        )
    return rows


def review_returned_document_package(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    dry_run: bool,
    staging_root: Path,
    preview_root: Path,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    if not staged_filename:
        raise ValueError("staged_filename is required")

    report = parse_staged_import(
        repo_root=repo_root,
        scope=normalized_scope,
        staged_file=staged_filename,
        staging_root=staging_root,
    )
    report = render_markdown_previews(
        repo_root=repo_root,
        scope=normalized_scope,
        report=report,
        write=not dry_run,
        preview_root=preview_root,
    )
    report["review_rows"] = build_review_rows(report, normalized_scope)
    return report
