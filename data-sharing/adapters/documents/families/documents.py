#!/usr/bin/env python3
"""Temporary Analytics adapter bridge to Docs Viewer document packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from docs_document_packages import service as document_packages

from ..context import (
    DocumentsDataSharingDependencies,
    attach_adapter_context,
    request_selection,
    require_documents_adapter,
    resolve_docs_scope,
)


def direct_body(body: Dict[str, Any], adapter: Any) -> Dict[str, Any]:
    if "record_indices" in body:
        raise ValueError("record_indices is not supported; returned document packages are atomic")
    selection = body.get("selection") if isinstance(body.get("selection"), dict) else {}
    translated = {
        key: value
        for key, value in body.items()
        if key not in document_packages.FORBIDDEN_REQUEST_FIELDS
    }
    translated["scope"] = resolve_docs_scope(
        adapter,
        selection.get("docs_scope"),
        required=False,
    )
    if "config_id" in body:
        translated["profile_id"] = str(body.get("config_id") or "").strip()
    if "file" in body and "staged_filename" not in body:
        translated["staged_filename"] = str(body.get("file") or "").strip()
    if "dry_run" not in translated:
        translated["dry_run"] = False
    return translated


def legacy_payload(payload: Dict[str, Any], adapter: Any) -> Dict[str, Any]:
    report = attach_adapter_context(payload, adapter)
    if isinstance(report.get("source"), dict) and report["source"].get("kind") == "docs_source":
        report["source"] = {
            "kind": "adapter",
            "module": "documents",
            "source": "docs_source_context",
            "scope": report["source"].get("scope", ""),
        }
    if "profile_id" in report and "config_id" not in report:
        report["config_id"] = report["profile_id"]
    if "apply_action" in report and "operation" not in report:
        report["operation"] = report["apply_action"]
    for collection_name in ("files", "blocked_files"):
        for item in report.get(collection_name, []):
            if not isinstance(item, dict):
                continue
            item["data_domain"] = adapter.data_domain
            item["adapter_id"] = adapter.adapter_id
            if "profile_id" in item and "config_id" not in item:
                item["config_id"] = item["profile_id"]
    if "review_records" in report:
        report["selected_records"] = list(report.get("review_records", []))
    if "records" in report and (
        report.get("summary_apply_written") is not None
        or report.get("hierarchy_apply_written") is not None
    ):
        report["selected_records"] = list(report.get("records", []))
    return report


def selectable_records(
    repo_root: Path,
    data_domain: Any,
    selectors: Optional[Dict[str, Any]] = None,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del data_domain, dependencies
    resolved = require_documents_adapter(adapter)
    scope = resolve_docs_scope(resolved, (selectors or {}).get("docs_scope"))
    return legacy_payload(
        document_packages.documents_payload(repo_root, {"scope": [scope]}),
        resolved,
    )


def prepare_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dependencies
    resolved = require_documents_adapter(adapter)
    selection = request_selection(body)
    translated = direct_body(body, resolved)
    translated.update(
        {
            "doc_ids": selection.get("doc_ids", []),
            "select_all": bool(selection.get("select_all")),
            "dry_run": dry_run,
        }
    )
    report = legacy_payload(document_packages.prepare_package(repo_root, translated), resolved)
    if report.get("ok"):
        count = int(report.get("counts", {}).get("exported") or 0)
        noun = "document" if count == 1 else "documents"
        action = "Validated package" if dry_run else "Prepared package"
        suffix = " without writing." if dry_run else "."
        report["summary_text"] = f"{action} {count} {noun} to {report.get('output_file', '')}{suffix}"
    return report


def update_prepare_context(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dependencies
    resolved = require_documents_adapter(adapter)
    translated = direct_body(body, resolved)
    translated["dry_run"] = dry_run
    return legacy_payload(document_packages.update_context(repo_root, translated), resolved)


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dependencies
    resolved = require_documents_adapter(adapter)
    scope_value = data_domain.get("docs_scope") if isinstance(data_domain, dict) else ""
    scope = resolve_docs_scope(resolved, scope_value, required=False)
    return legacy_payload(
        document_packages.returned_payload(repo_root, {"scope": [scope]}),
        resolved,
    )


def review_returned_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dependencies
    if str(body.get("operation") or "review").strip() != "review":
        raise ValueError("operation must be review")
    resolved = require_documents_adapter(adapter)
    translated = direct_body(body, resolved)
    action = str(body.get("review_action") or body.get("action") or "record_review").strip()
    translated["review_action"] = {
        "record_review": "summaries",
        "source_folder": "content",
    }.get(action, action)
    translated["dry_run"] = dry_run
    report = legacy_payload(document_packages.review_returned(repo_root, translated), resolved)
    if report.get("ok"):
        count = len(report.get("selected_records", []))
        noun = "document" if count == 1 else "documents"
        result_action = "Validated" if dry_run else "Generated"
        if action == "record_review":
            report["summary_text"] = (
                f"{result_action} {resolved.label} import review for {count} {noun}."
            )
        elif action not in {"content", "source_folder"}:
            review_label = "hierarchy" if action == "hierarchy" else "summaries"
            report["summary_text"] = (
                f"{result_action} {resolved.label} {review_label} review for {count} {noun}."
            )
    return report


def returned_records(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dry_run, dependencies
    resolved = require_documents_adapter(adapter)
    return legacy_payload(
        document_packages.inspect_returned(repo_root, direct_body(body, resolved)),
        resolved,
    )


def apply_returned_changes(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dependencies
    if str(body.get("operation") or "").strip() != "apply":
        raise ValueError("operation must be apply")
    resolved = require_documents_adapter(adapter)
    translated = direct_body(body, resolved)
    translated["dry_run"] = dry_run
    return legacy_payload(document_packages.apply_returned(repo_root, translated), resolved)
