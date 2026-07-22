#!/usr/bin/env python3
"""Document package generation and returned-package listing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_document_packages.export import (
    build_export,
    parse_doc_ids as parse_export_doc_ids,
)
from docs_document_packages.export_config import update_external_context_config
from docs_document_packages.returned_profiles import supported_return_import_profile_ids
from docs_document_packages import source_context
from docs_document_packages.metadata import list_staged_files_with_metadata
import docs_source_model as source_model


def document_selectable_record(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("doc_id") or "").strip()
    title = str(doc.get("title") or doc_id).strip()
    viewable = doc.get("viewable") is not False
    selectable = bool(doc_id)
    issues: list[Dict[str, str]] = []
    if not viewable:
        issues.append({"level": "warning", "message": "Document is not viewable."})
    return {
        "id": doc_id,
        "name": title,
        "doc_id": doc_id,
        "title": title,
        "type": "document",
        "meta": doc_id,
        "parent_id": str(doc.get("parent_id") or "").strip(),
        "viewable": viewable,
        "selectable": selectable,
        "children": [],
        "issues": issues,
        "content_text_length": int(doc.get("content_text_length") or 0),
        "summary": str(doc.get("summary") or ""),
    }


def selectable_document_records(repo_root: Path, *, scope: str, selection_model: str) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    docs = source_context.load_document_package_source_records(repo_root, normalized_scope)
    records = [
        document_selectable_record(
            {
                "doc_id": item.doc_id,
                "title": item.title,
                "parent_id": item.parent_id,
                "viewable": item.viewable,
                "content_text_length": item.content_text_length,
                "summary": item.summary,
            }
        )
        for item in docs
    ]
    return {
        "ok": True,
        "scope": normalized_scope,
        "selection_model": selection_model,
        "records": records,
        "docs": records,
        "source": {
            "kind": "docs_source",
            "scope": normalized_scope,
        },
    }


def build_document_package(
    repo_root: Path,
    *,
    scope: str,
    data_domain: str,
    config_id: str,
    raw_doc_ids: Any,
    select_all: bool,
    missing_summary_only: Any,
    include_non_viewable: Any,
    dry_run: bool,
    config_path: str,
    target_format: str,
    content_format: str,
    output_root: Path,
    metadata_root: Path,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    if not config_id:
        raise ValueError("config_id is required")
    if raw_doc_ids is None:
        raw_doc_ids = []
    if not isinstance(raw_doc_ids, list):
        raise ValueError("doc_ids must be a list")
    doc_ids = parse_export_doc_ids([str(doc_id or "") for doc_id in raw_doc_ids])
    if missing_summary_only is not None and not isinstance(missing_summary_only, bool):
        raise ValueError("missing_summary_only must be true, false, or null")
    if include_non_viewable is not None and not isinstance(include_non_viewable, bool):
        raise ValueError("include_non_viewable must be true, false, or null")

    return build_export(
        repo_root=repo_root,
        config_id=config_id,
        scope=normalized_scope,
        data_domain=data_domain,
        selected_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
        include_non_viewable=include_non_viewable,
        expand_document_tree_descendants=False,
        write=not dry_run,
        config_path=config_path,
        target_format=target_format or None,
        content_format=content_format or None,
        output_root=output_root,
        metadata_root=metadata_root,
    )


def update_document_prepare_context(
    repo_root: Path,
    *,
    config_id: str,
    external_context: Any,
    config_path: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    if not config_id:
        raise ValueError("config_id is required")
    report = update_external_context_config(
        repo_root,
        config_id=config_id,
        external_context=external_context,
        config_path=config_path,
        write=not dry_run,
    )
    report["summary_text"] = "Validated context." if dry_run else "Saved context."
    return report


def list_returned_document_packages(
    repo_root: Path,
    *,
    scope: str,
    staging_root: Path,
    metadata_root: Path,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    report = list_staged_files_with_metadata(
        repo_root,
        staging_root=staging_root,
        metadata_root=metadata_root,
    )
    report["scope"] = normalized_scope
    staged_files: list[dict[str, Any]] = []
    unassigned_files: list[dict[str, Any]] = []
    for item in report.get("files", []):
        if not item.get("metadata_ok"):
            unassigned_files.append(item)
            continue
        if str(item.get("data_domain") or "").strip() != "documents":
            continue
        item_scope = str(item.get("scope") or "").strip().lower()
        if not item_scope:
            unassigned_files.append(item)
            continue
        if item_scope == normalized_scope:
            staged_files.append(item)
    importable_profile_ids = supported_return_import_profile_ids()
    files: list[dict[str, Any]] = []
    blocked_files: list[dict[str, Any]] = []
    for item in report.get("blocked_files", []):
        if str(item.get("data_domain") or "").strip() != "documents":
            continue
        item_scope = str(item.get("scope") or "").strip().lower()
        if not item_scope:
            unassigned_files.append(item)
            continue
        if item_scope == normalized_scope:
            blocked_files.append(item)
    for item in staged_files:
        profile_id = str(item.get("profile_id") or "").strip()
        if item.get("supports_return_import") is False:
            blocked = dict(item)
            blocked["return_import_supported"] = False
            blocked["blocked_reason"] = "export_only_profile"
            blocked_files.append(blocked)
            continue
        if profile_id not in importable_profile_ids:
            blocked = dict(item)
            blocked["return_import_supported"] = False
            blocked["blocked_reason"] = "unsupported_import_profile"
            blocked_files.append(blocked)
            continue
        item["return_import_supported"] = True
        files.append(item)
    report["files"] = files
    report["blocked_files"] = blocked_files
    report["unassigned_files"] = unassigned_files
    return report
