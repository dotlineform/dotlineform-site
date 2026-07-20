#!/usr/bin/env python3
"""Summary apply action for returned document packages."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict

import docs_source_model as source_model
from docs_document_packages.apply_common import parse_apply_inputs
from docs_document_packages.write import DocumentPackageWriteDependencies, relative_path, write_document_updates_with_rebuild

def normalize_summary(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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
    confirmed: bool,
    dry_run: bool,
    staging_root: Path,
    metadata_root: Path,
    subject_label: str,
    dependencies: DocumentPackageWriteDependencies,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    report, docs, record_rows, skipped, records = parse_apply_inputs(
        repo_root,
        scope=normalized_scope,
        staged_filename=staged_filename,
        staging_root=staging_root,
        metadata_root=metadata_root,
    )
    docs_by_id = {doc.doc_id: doc for doc in docs}
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    updates: list[Dict[str, Any]] = []
    rewrite_docs: list[source_model.ScopeDoc] = []
    rewritten_sources: dict[str, str] = {}

    for record_index, record, doc_id in records:
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
                "updated_doc_ids": doc_ids,
            },
            doc_ids=doc_ids,
            dependencies=dependencies,
        )

    payload: Dict[str, Any] = {
        "ok": ok,
        "scope": normalized_scope,
        "staged_filename": staged_filename,
        "operation": "summary_apply",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "input_ok": bool(report.get("ok")),
        "detected_import_type": report.get("detected_import_type", ""),
        "records": record_rows,
        "updates": updates,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "records": len(record_rows),
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
    payload["summary_text"] = f"{action} {len(updates)} {subject_label} summary update(s){suffix}."
    return payload
