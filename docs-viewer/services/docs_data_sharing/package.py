#!/usr/bin/env python3
"""Docs Data Sharing package generation and returned-package listing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_export import build_export, parse_doc_ids as parse_export_doc_ids
import docs_generated_reads
from docs_import import list_staged_import_files
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
    index_payload = docs_generated_reads.read_generated_docs_index(repo_root, normalized_scope)
    docs = index_payload.get("docs")
    if not isinstance(docs, list):
        raise RuntimeError(f"generated docs index for {normalized_scope} is missing docs")
    records = [document_selectable_record(item) for item in docs if isinstance(item, dict)]
    return {
        "ok": True,
        "scope": normalized_scope,
        "selection_model": selection_model,
        "records": records,
        "docs": records,
        "source": {
            "kind": "adapter",
            "module": "documents",
            "source": "generated_docs_index",
            "scope": normalized_scope,
        },
    }


def build_document_package(
    repo_root: Path,
    *,
    scope: str,
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
        selected_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
        write=not dry_run,
        config_path=config_path,
        target_format=target_format or None,
        output_root=output_root,
    )


def list_returned_document_packages(repo_root: Path, *, scope: str, staging_root: Path) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    return {
        "ok": True,
        "scope": normalized_scope,
        "staging_root": staging_root.as_posix(),
        "files": list_staged_import_files(repo_root, normalized_scope, staging_root=staging_root),
    }
