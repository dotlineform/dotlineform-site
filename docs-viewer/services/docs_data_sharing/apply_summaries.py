#!/usr/bin/env python3
"""Summary apply action for Docs returned packages."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict

import docs_source_model as source_model
from docs_data_sharing.apply_common import DocumentsApplyIdentity, parse_apply_inputs
from docs_data_sharing.write import DocsDataSharingWriteDependencies, relative_path, write_document_updates_with_rebuild

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

def apply_summary_updates(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    record_indices: Any,
    confirmed: bool,
    dry_run: bool,
    staging_root: Path,
    metadata_root: Path,
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
        metadata_root=metadata_root,
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
    write_result: Dict[str, Any] = {"rebuild": None}
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
        "rebuild": write_result["rebuild"],
        "summary_apply_written": bool(ok and confirmed and updates and not dry_run),
        "requires_confirmation": bool(ok and updates and not confirmed),
    }
    action = "Validated" if not confirmed or dry_run else "Updated"
    suffix = " without writing" if not confirmed or dry_run else ""
    payload["summary_text"] = f"{action} {len(updates)} {identity.adapter_label} summary update(s){suffix}."
    return payload
