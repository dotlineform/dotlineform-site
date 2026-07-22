#!/usr/bin/env python3
"""Returned document-package review helpers."""

from __future__ import annotations

from typing import Any, Dict

from docs_document_packages.returned_common import scope_title
from docs_document_packages.returned_parser import parse_staged_import
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


def document_record_depth(record: Dict[str, Any], by_doc_id: dict[str, Dict[str, Any]], active_doc_ids: set[str] | None = None) -> int:
    doc_id = normalize_text(record.get("doc_id"))
    parent_id = normalize_text(record.get("parent_id"))
    if not doc_id or not parent_id or parent_id == doc_id:
        return 0
    active = set(active_doc_ids or set())
    if doc_id in active:
        return 0
    parent = by_doc_id.get(parent_id)
    if parent is None:
        return 0
    active.add(doc_id)
    return document_record_depth(parent, by_doc_id, active) + 1


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
    by_doc_id = {
        normalize_text(record.get("doc_id")): record
        for record in records
        if normalize_text(record.get("doc_id"))
    }
    for record in records:
        record_index = int(record.get("record_index")) if isinstance(record.get("record_index"), int) else len(rows)
        doc_id = normalize_text(record.get("doc_id"))
        rows.append(
            {
                "id": f"{doc_id or 'missing-doc-id'}-record-{record_index + 1}",
                "type": "document",
                "title": normalize_text(record.get("title")) or "missing title",
                "meta": review_row_meta(scope, record, duplicates),
                "record_index": record_index,
                "record_groups": {"documents": [doc_id]} if doc_id else {},
                "issues": issues_by_record.get(record_index, []),
                "depth": document_record_depth(record, by_doc_id),
            }
        )
    return rows


def parse_returned_document_records(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    staging_root: Path,
    metadata_root: Path,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    if not staged_filename:
        raise ValueError("staged_filename is required")

    report = parse_staged_import(
        repo_root=repo_root,
        scope=normalized_scope,
        staged_file=staged_filename,
        staging_root=staging_root,
        metadata_root=metadata_root,
    )
    report["review_rows"] = build_review_rows(report, normalized_scope)
    return report
