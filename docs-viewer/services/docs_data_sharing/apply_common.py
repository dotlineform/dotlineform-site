#!/usr/bin/env python3
"""Common returned-package apply helpers for Docs Data Sharing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from docs_returned_import_parser import parse_staged_import
import docs_source_model as source_model


@dataclass(frozen=True)
class DocumentsApplyIdentity:
    data_domain: str
    adapter_id: str
    adapter_label: str

def all_record_indices(records: list[Dict[str, Any]]) -> list[int]:
    return [
        int(record.get("record_index"))
        for record in records
        if isinstance(record, dict) and isinstance(record.get("record_index"), int)
    ]


def selected_record_indices(value: Any, records: list[Dict[str, Any]]) -> list[int]:
    if value is None:
        return all_record_indices(records)
    if not isinstance(value, list):
        raise ValueError("record_indices must be a list")
    selected: list[int] = []
    seen: set[int] = set()
    for item in value:
        if isinstance(item, bool):
            raise ValueError("record_indices must contain integers")
        try:
            index = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError("record_indices must contain integers") from exc
        if index < 0:
            raise ValueError("record_indices must contain zero or positive integers")
        if index not in seen:
            selected.append(index)
            seen.add(index)
    return selected

def selected_records(
    report: Dict[str, Any],
    selected_indices: list[int],
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], list[tuple[int, Dict[str, Any], str]]]:
    records_by_index = {
        int(record.get("record_index")): record
        for record in report.get("records", [])
        if isinstance(record, dict) and isinstance(record.get("record_index"), int)
    }
    selected_rows: list[Dict[str, Any]] = []
    skipped: list[Dict[str, Any]] = []
    selected: list[tuple[int, Dict[str, Any], str]] = []
    seen_doc_ids: set[str] = set()

    for record_index in selected_indices:
        record = records_by_index.get(record_index)
        if not record:
            skipped.append({"record_index": record_index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        doc_id = str(record.get("doc_id") or "").strip()
        selected_rows.append({"record_index": record_index, "doc_id": doc_id})
        if not doc_id:
            skipped.append({"record_index": record_index, "reason": "missing_doc_id", "message": "selected record has no doc_id"})
            continue
        if doc_id in seen_doc_ids:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "duplicate_doc_id", "message": "selected doc_id was already planned"})
            continue
        seen_doc_ids.add(doc_id)
        selected.append((record_index, record, doc_id))

    return selected_rows, skipped, selected


def parse_apply_inputs(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    record_indices: Any,
    staging_root: Path,
    metadata_root: Path,
) -> tuple[Dict[str, Any], list[source_model.ScopeDoc], list[int], list[Dict[str, Any]], list[Dict[str, Any]], list[tuple[int, Dict[str, Any], str]]]:
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
    records = [record for record in report.get("records", []) if isinstance(record, dict)]
    selected_indices = selected_record_indices(record_indices, records)
    if not selected_indices and report.get("ok"):
        raise ValueError("record_indices must include at least one selected record")
    docs = source_model.load_scope_docs(repo_root, normalized_scope)
    selected_rows, skipped, selected = selected_records(report, selected_indices)
    return report, docs, selected_indices, selected_rows, skipped, selected
