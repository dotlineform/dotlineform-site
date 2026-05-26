#!/usr/bin/env python3
"""Docs Data Sharing returned-package apply planning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict

from docs_import import parse_staged_import
import docs_source_model as source_model
from docs_data_sharing.write import DocsDataSharingWriteDependencies, relative_path, write_document_updates_with_rebuild


@dataclass(frozen=True)
class DocumentsApplyIdentity:
    data_domain: str
    adapter_id: str
    adapter_label: str


def normalize_summary(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def selected_record_indices(value: Any) -> list[int]:
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


def summary_from_record(record: Dict[str, Any]) -> tuple[str, bool]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if "summary" not in metadata:
        return "", False
    return normalize_summary(metadata.get("summary")), True


def imported_parent_id(record: Dict[str, Any]) -> str:
    return str(record.get("parent_id") or "").strip()


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
) -> tuple[Dict[str, Any], list[source_model.ScopeDoc], list[int], list[Dict[str, Any]], list[Dict[str, Any]], list[tuple[int, Dict[str, Any], str]]]:
    normalized_scope = source_model.normalize_scope(scope)
    if not staged_filename:
        raise ValueError("staged_filename is required")
    selected_indices = selected_record_indices(record_indices)
    if not selected_indices:
        raise ValueError("record_indices must include at least one selected record")
    report = parse_staged_import(
        repo_root=repo_root,
        scope=normalized_scope,
        staged_file=staged_filename,
        staging_root=staging_root,
    )
    docs = source_model.load_scope_docs(repo_root, normalized_scope)
    selected_rows, skipped, selected = selected_records(report, selected_indices)
    return report, docs, selected_indices, selected_rows, skipped, selected


def apply_summary_updates(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    record_indices: Any,
    confirmed: bool,
    dry_run: bool,
    staging_root: Path,
    identity: DocumentsApplyIdentity,
    dependencies: DocsDataSharingWriteDependencies,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    report, docs, selected_indices, selected_rows, skipped, selected = parse_apply_inputs(
        repo_root,
        scope=normalized_scope,
        staged_filename=staged_filename,
        record_indices=record_indices,
        staging_root=staging_root,
    )
    docs_by_id = {doc.doc_id: doc for doc in docs}
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    updates: list[Dict[str, Any]] = []
    rewrite_docs: list[source_model.ScopeDoc] = []
    rewritten_sources: dict[str, str] = {}

    for record_index, record, doc_id in selected:
        target = docs_by_id.get(doc_id)
        if target is None:
            errors.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_target_doc", "message": f"target Library source doc does not exist: {doc_id}"})
            continue
        summary, has_summary = summary_from_record(record)
        if not has_summary or not summary:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_summary", "message": "selected record has no proposed summary"})
            continue
        current_summary = normalize_summary(target.front_matter.get("summary"))
        if summary == current_summary:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "unchanged", "message": "proposed summary matches current source summary"})
            continue

        rewritten_sources[doc_id] = source_model.rewrite_doc_source(target, {"summary": summary})
        rewrite_docs.append(target)
        updates.append(
            {
                "record_index": record_index,
                "doc_id": doc_id,
                "path": relative_path(repo_root, target.path),
                "from_summary": current_summary,
                "to_summary": summary,
            }
        )

    warning_count = len(warnings) + len(skipped)
    error_count = len(errors)
    ok = bool(report.get("ok")) and error_count == 0
    write_result: Dict[str, Any] = {"backup_dir": "", "rebuild": None}
    if ok and confirmed and updates and not dry_run:
        doc_ids = [item["doc_id"] for item in updates]
        write_result = write_document_updates_with_rebuild(
            repo_root,
            scope=normalized_scope,
            operation="documents-summary-apply",
            suppression_reason="docs-import-summary-apply",
            docs=rewrite_docs,
            rewritten_sources=rewritten_sources,
            metadata={
                "staged_filename": staged_filename,
                "record_indices": selected_indices,
                "updated_doc_ids": doc_ids,
            },
            doc_ids=doc_ids,
            dependencies=dependencies,
        )

    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": identity.data_domain,
        "adapter_id": identity.adapter_id,
        "scope": normalized_scope,
        "staged_filename": staged_filename,
        "operation": "summary_apply",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "input_ok": bool(report.get("ok")),
        "detected_import_type": report.get("detected_import_type", ""),
        "selected_records": selected_rows,
        "updates": updates,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "selected": len(selected_indices),
            "updates": len(updates),
            "skipped": len(skipped),
            "errors": error_count,
            "warnings": warning_count,
        },
        "backup_dir": write_result["backup_dir"],
        "rebuild": write_result["rebuild"],
        "summary_apply_written": bool(ok and confirmed and updates and not dry_run),
        "requires_confirmation": bool(ok and updates and not confirmed),
    }
    action = "Validated" if not confirmed or dry_run else "Updated"
    suffix = " without writing" if not confirmed or dry_run else ""
    payload["summary_text"] = f"{action} {len(updates)} {identity.adapter_label} summary update(s){suffix}."
    return payload


def apply_hierarchy_updates(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    record_indices: Any,
    confirmed: bool,
    dry_run: bool,
    staging_root: Path,
    identity: DocumentsApplyIdentity,
    dependencies: DocsDataSharingWriteDependencies,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    report, docs, selected_indices, selected_rows, skipped, selected = parse_apply_inputs(
        repo_root,
        scope=normalized_scope,
        staged_filename=staged_filename,
        record_indices=record_indices,
        staging_root=staging_root,
    )
    docs_by_id = {doc.doc_id: doc for doc in docs}
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    updates: list[Dict[str, Any]] = []
    unchanged: list[Dict[str, Any]] = []
    rewrite_docs: list[source_model.ScopeDoc] = []
    rewritten_sources: dict[str, str] = {}

    for record_index, record, doc_id in selected:
        target = docs_by_id.get(doc_id)
        if target is None:
            errors.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_target_doc", "message": f"target Library source doc does not exist: {doc_id}"})
            continue
        parent_id = imported_parent_id(record)
        if parent_id == doc_id:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "self_parent_id", "message": "selected record parent_id points to itself"})
            continue
        if parent_id and parent_id not in docs_by_id:
            warnings.append({"record_index": record_index, "doc_id": doc_id, "parent_id": parent_id, "reason": "unknown_parent_id", "message": f"parent_id is not a current Library source doc and will render at root level: {parent_id}"})
        if parent_id == target.parent_id:
            unchanged.append({"record_index": record_index, "doc_id": doc_id, "parent_id": parent_id, "message": "proposed parent_id matches current source parent_id"})
            continue

        rewritten_sources[doc_id] = source_model.rewrite_doc_source(target, {"parent_id": parent_id})
        rewrite_docs.append(target)
        updates.append(
            {
                "record_index": record_index,
                "doc_id": doc_id,
                "path": relative_path(repo_root, target.path),
                "from_parent_id": target.parent_id,
                "to_parent_id": parent_id,
                "sort_order": target.sort_order,
            }
        )

    warning_count = len(warnings) + len(skipped)
    error_count = len(errors)
    ok = bool(report.get("ok")) and error_count == 0
    write_result: Dict[str, Any] = {"backup_dir": "", "rebuild": None}
    if ok and confirmed and updates and not dry_run:
        doc_ids = [item["doc_id"] for item in updates]
        write_result = write_document_updates_with_rebuild(
            repo_root,
            scope=normalized_scope,
            operation="documents-hierarchy-apply",
            suppression_reason="docs-import-hierarchy-apply",
            docs=rewrite_docs,
            rewritten_sources=rewritten_sources,
            metadata={
                "staged_filename": staged_filename,
                "record_indices": selected_indices,
                "updated_doc_ids": doc_ids,
            },
            doc_ids=doc_ids,
            dependencies=dependencies,
        )

    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": identity.data_domain,
        "adapter_id": identity.adapter_id,
        "scope": normalized_scope,
        "staged_filename": staged_filename,
        "operation": "hierarchy_apply",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "input_ok": bool(report.get("ok")),
        "detected_import_type": report.get("detected_import_type", ""),
        "selected_records": selected_rows,
        "updates": updates,
        "unchanged": unchanged,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "selected": len(selected_indices),
            "changed": len(updates),
            "updates": len(updates),
            "unchanged": len(unchanged),
            "skipped": len(skipped),
            "errors": error_count,
            "warnings": warning_count,
        },
        "backup_dir": write_result["backup_dir"],
        "rebuild": write_result["rebuild"],
        "hierarchy_apply_written": bool(ok and confirmed and updates and not dry_run),
        "requires_confirmation": bool(ok and updates and not confirmed),
    }
    action = "Validated" if not confirmed or dry_run else "Updated"
    suffix = " without writing" if not confirmed or dry_run else ""
    payload["summary_text"] = f"{action} {len(updates)} {identity.adapter_label} hierarchy change(s){suffix}."
    return payload
