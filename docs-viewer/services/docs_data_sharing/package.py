#!/usr/bin/env python3
"""Docs Data Sharing package generation and returned-package listing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_export import (
    build_export,
    parse_doc_ids as parse_export_doc_ids,
    update_external_context_config,
)
from docs_import import supported_return_import_profile_ids
from docs_data_sharing import source_metadata
from services.returned_metadata import list_staged_files_with_metadata
import docs_source_model as source_model


def document_selectable_record(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("doc_id") or "").strip()
    title = str(doc.get("title") or doc_id).strip()
    viewable = doc.get("viewable") is not False
    published = doc.get("published") is not False
    selectable = bool(doc_id and published and viewable)
    issues: list[Dict[str, str]] = []
    if not published:
        issues.append({"level": "warning", "message": "Document is not published."})
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
        "published": published,
        "viewable": viewable,
        "selectable": selectable,
        "children": [],
        "issues": issues,
        "content_text_length": int(doc.get("content_text_length") or 0),
        "summary": str(doc.get("summary") or ""),
    }


def selectable_document_records(repo_root: Path, *, scope: str, selection_model: str) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    docs = source_metadata.load_data_sharing_docs_source_records(repo_root, normalized_scope)
    records = [
        document_selectable_record(
            {
                "doc_id": item.doc_id,
                "title": item.title,
                "parent_id": item.parent_id,
                "published": item.published,
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
            "kind": "adapter",
            "module": "documents",
            "source": "docs_source_metadata",
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
    dry_run: bool,
    config_path: str,
    target_format: str,
    output_root: Path,
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

    return build_export(
        repo_root=repo_root,
        config_id=config_id,
        scope=normalized_scope,
        data_domain=data_domain,
        selected_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
        write=not dry_run,
        config_path=config_path,
        target_format=target_format or None,
        output_root=output_root,
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


def list_returned_document_packages(repo_root: Path, *, scope: str, staging_root: Path) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    report = list_staged_files_with_metadata(repo_root, staging_root=staging_root)
    report["scope"] = normalized_scope
    staged_files = [
        item
        for item in report.get("files", [])
        if not item.get("metadata_ok")
        or (
            str(item.get("data_domain") or "").strip() == "documents"
            and (
                not str(item.get("scope") or "").strip()
                or str(item.get("scope") or "").strip() == normalized_scope
            )
        )
    ]
    importable_profile_ids = supported_return_import_profile_ids()
    files: list[dict[str, Any]] = []
    blocked_files: list[dict[str, Any]] = [
        item
        for item in report.get("blocked_files", [])
        if (
            str(item.get("data_domain") or "").strip() == "documents"
            and (
                not str(item.get("scope") or "").strip()
                or str(item.get("scope") or "").strip() == normalized_scope
            )
        )
    ]
    for item in staged_files:
        if not item.get("metadata_ok"):
            files.append(item)
            continue
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
    return report
