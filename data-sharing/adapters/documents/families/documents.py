#!/usr/bin/env python3
"""Document record family for the Documents Data Sharing adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from docs_data_sharing.apply_common import DocumentsApplyIdentity
from docs_data_sharing.apply_hierarchy import apply_hierarchy_updates
from docs_data_sharing.apply_summaries import apply_summary_updates
from docs_data_sharing.package import (
    build_document_package,
    list_returned_document_packages,
    selectable_document_records,
    update_document_prepare_context,
)
from docs_data_sharing.review import review_returned_document_package
from docs_data_sharing.review import parse_returned_document_records

from ..context import (
    DocumentsDataSharingDependencies,
    attach_adapter_context,
    request_selection,
    require_documents_adapter,
    resolve_docs_scope,
    selection_model,
)


def selectable_records(
    repo_root: Path,
    data_domain: Any,
    selectors: Optional[Dict[str, Any]] = None,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del data_domain, dependencies
    adapter = require_documents_adapter(adapter)
    docs_scope = resolve_docs_scope(adapter, (selectors or {}).get("docs_scope"))
    report = selectable_document_records(
        repo_root,
        scope=docs_scope,
        selection_model=selection_model(adapter),
    )
    return attach_adapter_context(report, adapter)


def prepare_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_documents_adapter(adapter)
    selection = request_selection(body)
    docs_scope = resolve_docs_scope(adapter, selection.get("docs_scope"))
    config_id = str(body.get("config_id") or "").strip()
    target_format = str(body.get("target_format") or "").strip()
    report = build_document_package(
        repo_root,
        scope=docs_scope,
        data_domain=adapter.data_domain,
        config_id=config_id,
        raw_doc_ids=selection.get("doc_ids", []),
        select_all=bool(selection.get("select_all")),
        missing_summary_only=selection.get("missing_summary_only"),
        dry_run=dry_run,
        config_path=adapter.config_path("sharing_profiles_path").as_posix(),
        target_format=target_format,
        output_root=adapter.path("outbound_package_root"),
    )
    report = attach_adapter_context(report, adapter)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-export",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "docs_scope": report.get("scope", docs_scope),
                "config_id": config_id,
                "dry_run": dry_run,
                "target_format": report.get("target_format", ""),
                "output_written": bool(report.get("output_written")),
                "selected": int(report.get("counts", {}).get("selected") or 0),
                "exported": int(report.get("counts", {}).get("exported") or 0),
                "skipped": int(report.get("counts", {}).get("skipped") or 0),
                "failed": int(report.get("counts", {}).get("failed") or 0),
                "truncated": int(report.get("counts", {}).get("truncated") or 0),
                "errors": int(report.get("issue_counts", {}).get("errors") or 0),
                "warnings": int(report.get("issue_counts", {}).get("warnings") or 0),
            },
        )
    if report.get("ok"):
        action = "Validated package" if dry_run else "Prepared package"
        suffix = " without writing." if dry_run else "."
        exported_count = int(report.get("counts", {}).get("exported") or 0)
        document_word = "document" if exported_count == 1 else "documents"
        report["summary_text"] = (
            f"{action} {exported_count} {document_word} "
            f"to {report.get('output_file', '')}{suffix}"
        )
    return report


def update_prepare_context(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_documents_adapter(adapter)
    config_id = str(body.get("config_id") or "").strip()
    report = update_document_prepare_context(
        repo_root,
        config_id=config_id,
        external_context=body.get("external_context"),
        config_path=adapter.config_path("sharing_profiles_path").as_posix(),
        dry_run=dry_run,
    )
    report = attach_adapter_context(report, adapter)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-export-context",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "config_id": config_id,
                "dry_run": dry_run,
                "output_written": bool(report.get("output_written")),
            },
        )
    return report


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_documents_adapter(adapter)
    docs_scope = resolve_docs_scope(
        adapter,
        data_domain.get("docs_scope") if isinstance(data_domain, dict) else "",
        required=False,
    )
    report = list_returned_document_packages(
        repo_root,
        scope=docs_scope,
        staging_root=adapter.path("returned_package_staging_root"),
    )
    report = attach_adapter_context(report, adapter)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-import-files",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "docs_scope": report.get("scope", docs_scope),
                "count": len(report.get("files", [])),
            },
        )
    return report


def review_returned_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "review").strip()
    if operation != "review":
        raise ValueError("operation must be review")
    adapter = require_documents_adapter(adapter)
    selection = body.get("selection") if isinstance(body.get("selection"), dict) else {}
    scope = resolve_docs_scope(adapter, selection.get("docs_scope"), required=False)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    record_indices = body.get("record_indices", [])
    report = review_returned_document_package(
        repo_root,
        scope=scope,
        staged_filename=staged_filename,
        dry_run=dry_run,
        staging_root=adapter.path("returned_package_staging_root"),
        preview_root=adapter.path("review_output_root"),
        data_domain=adapter.data_domain,
        record_indices=record_indices,
    )
    report = attach_adapter_context(report, adapter)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-import-review",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "scope": scope,
                "staged_filename": staged_filename,
                "dry_run": dry_run,
                "detected_import_type": str(report.get("detected_import_type") or ""),
                "records": int(report.get("counts", {}).get("records") or 0),
                "parsed_records": int(report.get("counts", {}).get("parsed_records") or 0),
                "malformed_records": int(report.get("counts", {}).get("malformed_records") or 0),
                "errors": int(report.get("counts", {}).get("errors") or 0),
                "warnings": int(report.get("counts", {}).get("warnings") or 0),
                "review_rows": len(report.get("review_rows", [])),
                "selected_records": len(report.get("selected_records", [])),
                "review_written": bool(report.get("review_written")),
                "review_file": str(report.get("review_file") or ""),
            },
        )
    if report.get("ok"):
        action = "Validated" if dry_run else "Generated"
        row_count = len(report.get("selected_records", []))
        row_label = "document" if row_count == 1 else "documents"
        report["summary_text"] = (
            f"{action} {adapter.label} import review for {row_count} selected {row_label}."
        )
    return report


def returned_records(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dry_run
    adapter = require_documents_adapter(adapter)
    selection = body.get("selection") if isinstance(body.get("selection"), dict) else {}
    scope = resolve_docs_scope(adapter, selection.get("docs_scope"), required=False)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    report = parse_returned_document_records(
        repo_root,
        scope=scope,
        staged_filename=staged_filename,
        staging_root=adapter.path("returned_package_staging_root"),
    )
    report = attach_adapter_context(report, adapter)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-import-records",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "scope": scope,
                "staged_filename": staged_filename,
                "detected_import_type": str(report.get("detected_import_type") or ""),
                "records": int(report.get("counts", {}).get("records") or 0),
                "review_rows": len(report.get("review_rows", [])),
                "errors": int(report.get("counts", {}).get("errors") or 0),
                "warnings": int(report.get("counts", {}).get("warnings") or 0),
            },
        )
    if report.get("ok"):
        row_count = len(report.get("review_rows", []))
        row_label = "row" if row_count == 1 else "rows"
        report["summary_text"] = f"Loaded {row_count} {adapter.label} import review {row_label}."
    return report


def apply_returned_changes(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "").strip()
    if operation != "apply":
        raise ValueError("operation must be apply")
    apply_action = str(body.get("apply_action") or "").strip()
    if apply_action not in {"summary_apply", "hierarchy_apply"}:
        raise ValueError("apply_action must be summary_apply or hierarchy_apply")
    if dependencies is None:
        raise ValueError("documents apply requires service dependencies")
    adapter = require_documents_adapter(adapter)
    selection = body.get("selection") if isinstance(body.get("selection"), dict) else {}
    scope = resolve_docs_scope(adapter, selection.get("docs_scope"), required=False)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    confirmed = bool(body.get("confirm"))
    identity = DocumentsApplyIdentity(
        data_domain=adapter.data_domain,
        adapter_id=adapter.adapter_id,
        adapter_label=adapter.label,
    )
    common_args = {
        "scope": scope,
        "staged_filename": staged_filename,
        "record_indices": body.get("record_indices", []),
        "confirmed": confirmed,
        "dry_run": dry_run,
        "staging_root": adapter.path("returned_package_staging_root"),
        "identity": identity,
        "dependencies": dependencies.write_dependencies(),
    }
    if apply_action == "summary_apply":
        payload = apply_summary_updates(repo_root, **common_args)
        log_event_name = "docs-import-summary-apply"
        log_details = {
            "updates": len(payload.get("updates", [])),
            "skipped": len(payload.get("skipped", [])),
            "errors": int(payload.get("counts", {}).get("errors") or 0),
            "written": bool(payload.get("summary_apply_written")),
        }
    else:
        payload = apply_hierarchy_updates(repo_root, **common_args)
        log_event_name = "docs-import-hierarchy-apply"
        log_details = {
            "changed": len(payload.get("updates", [])),
            "unchanged": len(payload.get("unchanged", [])),
            "skipped": len(payload.get("skipped", [])),
            "warnings": len(payload.get("warnings", [])),
            "errors": int(payload.get("counts", {}).get("errors") or 0),
            "written": bool(payload.get("hierarchy_apply_written")),
        }

    dependencies.log_event(
        repo_root,
        log_event_name,
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "confirmed": confirmed,
            **log_details,
        },
    )
    return payload
