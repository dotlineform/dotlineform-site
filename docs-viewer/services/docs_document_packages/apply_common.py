#!/usr/bin/env python3
"""Common returned document-package apply helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_document_packages.returned_parser import parse_staged_import
import docs_source_model as source_model


def package_records(
    report: Dict[str, Any],
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], list[tuple[int, Dict[str, Any], str]]]:
    record_rows: list[Dict[str, Any]] = []
    skipped: list[Dict[str, Any]] = []
    records: list[tuple[int, Dict[str, Any], str]] = []
    for record in report.get("records", []):
        if not isinstance(record, dict) or not isinstance(record.get("record_index"), int):
            continue
        record_index = int(record["record_index"])
        doc_id = str(record.get("doc_id") or "").strip()
        record_rows.append({"record_index": record_index, "doc_id": doc_id})
        if not doc_id:
            skipped.append({"record_index": record_index, "reason": "missing_doc_id", "message": "package record has no doc_id"})
            continue
        records.append((record_index, record, doc_id))

    return record_rows, skipped, records


def parse_apply_inputs(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    staging_root: Path,
    metadata_root: Path,
) -> tuple[Dict[str, Any], list[source_model.ScopeDoc], list[Dict[str, Any]], list[Dict[str, Any]], list[tuple[int, Dict[str, Any], str]]]:
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
    docs = source_model.load_scope_docs(repo_root, normalized_scope)
    record_rows, skipped, records = package_records(report)
    return report, docs, record_rows, skipped, records
