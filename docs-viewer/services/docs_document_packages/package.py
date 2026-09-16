#!/usr/bin/env python3
"""Document package generation and returned-package listing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_document_packages.export import (
    build_export,
    parse_doc_ids as parse_export_doc_ids,
)
from docs_document_packages.returned_common import (
    DOCS_REVIEW_CAPABILITY,
    RETURN_IMPORT_CAPABILITY,
)
from docs_document_packages.returned_profiles import (
    supported_docs_review_profile_ids,
    supported_return_import_profile_ids,
)
from docs_document_packages.returned_parser import parse_staged_import
from docs_document_packages import source_context
from docs_document_packages.metadata import list_staged_files_with_metadata
from docs_document_packages.provenance import require_package_stage
import docs_source_model as source_model


def document_selectable_record(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("doc_id") or "").strip()
    title = str(doc.get("title") or doc_id).strip()
    selectable = bool(doc_id)
    issues: list[Dict[str, str]] = []
    record = {
        "id": doc_id,
        "name": title,
        "doc_id": doc_id,
        "title": title,
        "type": "document",
        "meta": doc_id,
        "parent_id": str(doc.get("parent_id") or "").strip(),
        "selectable": selectable,
        "children": [],
        "issues": issues,
        "content_text_length": int(doc.get("content_text_length") or 0),
        "summary": str(doc.get("summary") or ""),
    }
    return record


def selectable_document_records(
    repo_root: Path,
    *,
    stage: str,
    selection_model: str,
    collection: str = "",
) -> Dict[str, Any]:
    normalized_stage = require_package_stage(stage)
    normalized_collection = str(collection or "").strip().lower()
    docs = source_context.load_document_package_source_records(
        repo_root,
        normalized_stage,
        normalized_collection,
    )
    records = [
        document_selectable_record(
            {
                "doc_id": item.doc_id,
                "title": item.title,
                "parent_id": item.parent_id,
                "content_text_length": item.content_text_length,
                "summary": item.summary,
            }
        )
        for item in docs
    ]
    payload: Dict[str, Any] = {
        "ok": True,
        "stage": normalized_stage,
        "selection_model": selection_model,
        "records": records,
        "docs": records,
        "source": {
            "kind": "docs_source",
            "stage": normalized_stage,
        },
    }
    if normalized_collection:
        payload.update({
            "collection": normalized_collection,
            "flat_collection": True,
        })
        payload["source"]["kind"] = "docs_collection_source"
        payload["source"]["collection"] = normalized_collection
    return payload


def build_document_package(
    repo_root: Path,
    *,
    stage: str,
    data_domain: str,
    config_id: str,
    raw_doc_ids: Any,
    select_all: bool,
    missing_summary_only: Any,
    dry_run: bool,
    config_path: str,
    target_format: str,
    content_format: str,
    output_root: Path,
    metadata_root: Path,
    collection: str = "",
) -> Dict[str, Any]:
    normalized_stage = require_package_stage(stage)
    normalized_collection = str(collection or "").strip().lower()
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
        stage=normalized_stage,
        collection=normalized_collection,
        data_domain=data_domain,
        selected_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
        expand_document_tree_descendants=False,
        write=not dry_run,
        config_path=config_path,
        target_format=target_format or None,
        content_format=content_format or None,
        output_root=output_root,
        metadata_root=metadata_root,
    )


def list_returned_document_packages(
    repo_root: Path,
    *,
    stage: str,
    collection: str | None = None,
    required_capability: str = DOCS_REVIEW_CAPABILITY,
    staging_root: Path,
    metadata_root: Path,
) -> Dict[str, Any]:
    """List reviewable packages for a stage or importable packages for one child."""

    if required_capability not in {
        DOCS_REVIEW_CAPABILITY,
        RETURN_IMPORT_CAPABILITY,
    }:
        raise ValueError(
            f"unsupported returned-package capability: {required_capability}"
        )
    normalized_stage = require_package_stage(stage)
    normalized_collection = (
        None
        if collection is None
        else str(collection or "").strip().lower()
    )
    if collection is not None and not normalized_collection:
        raise ValueError("collection is required for exact returned-package listing")
    stage_config = source_context.package_source_stage_config(repo_root, normalized_stage)
    collection_labels = {
        record.collection: record.title
        for record in stage_config.collections
    }

    def add_collection_labels(item: dict[str, Any]) -> dict[str, Any]:
        collection = str(item.get("collection") or "").strip().lower()
        item["stage_label"] = source_model.humanize(normalized_stage)
        item["collection_label"] = (
            collection_labels.get(collection, source_model.humanize(collection))
            if collection
            else ""
        )
        return item

    report = list_staged_files_with_metadata(
        repo_root,
        staging_root=staging_root,
        metadata_root=metadata_root,
    )
    report["stage"] = normalized_stage
    staged_files: list[dict[str, Any]] = []
    unassigned_files: list[dict[str, Any]] = []
    for item in report.get("files", []):
        if not item.get("metadata_ok"):
            unassigned_files.append(item)
            continue
        if str(item.get("data_domain") or "").strip() != "documents":
            continue
        item_stage = str(item.get("stage") or "").strip().lower()
        if not item_stage:
            unassigned_files.append(item)
            continue
        item_collection = str(item.get("collection") or "").strip().lower()
        if (
            item_stage == normalized_stage
            and (
                normalized_collection is None
                or item_collection == normalized_collection
            )
        ):
            staged_files.append(add_collection_labels(item))
    supported_profile_ids = (
        supported_return_import_profile_ids()
        if required_capability == RETURN_IMPORT_CAPABILITY
        else supported_docs_review_profile_ids()
    )
    files: list[dict[str, Any]] = []
    blocked_files: list[dict[str, Any]] = []
    for item in report.get("blocked_files", []):
        if str(item.get("data_domain") or "").strip() != "documents":
            continue
        if item.get("provenance_error"):
            blocked_files.append(item)
            continue
        item_stage = str(item.get("stage") or "").strip().lower()
        if not item_stage:
            unassigned_files.append(item)
            continue
        item_collection = str(item.get("collection") or "").strip().lower()
        if (
            item_stage == normalized_stage
            and (
                normalized_collection is None
                or item_collection == normalized_collection
            )
        ):
            blocked_files.append(add_collection_labels(item))
    for item in staged_files:
        profile_id = str(item.get("profile_id") or "").strip()
        if item.get("supports_docs_review") is not True:
            blocked = dict(item)
            blocked["docs_review_supported"] = False
            blocked["return_import_supported"] = False
            blocked["blocked_reason"] = "export_only_profile"
            blocked_files.append(blocked)
            continue
        if profile_id not in supported_profile_ids:
            blocked = dict(item)
            blocked["docs_review_supported"] = False
            blocked["return_import_supported"] = False
            blocked["blocked_reason"] = (
                "unsupported_import_profile"
                if required_capability == RETURN_IMPORT_CAPABILITY
                else "unsupported_review_profile"
            )
            blocked_files.append(blocked)
            continue
        if (
            required_capability == RETURN_IMPORT_CAPABILITY
            and item.get("supports_return_import") is not True
        ):
            blocked = dict(item)
            blocked["docs_review_supported"] = True
            blocked["return_import_supported"] = False
            blocked["blocked_reason"] = (
                "export_only_collection"
                if str(item.get("collection") or "").strip()
                else "export_only_profile"
            )
            blocked_files.append(blocked)
            continue
        validation = parse_staged_import(
            repo_root=repo_root,
            stage=normalized_stage,
            collection=normalized_collection,
            staged_file=str(item.get("filename") or "").strip(),
            staging_root=staging_root,
            metadata_root=metadata_root,
            required_capability=required_capability,
        )
        if validation.get("ok") is not True:
            blocked = dict(item)
            blocked["docs_review_supported"] = True
            blocked["return_import_supported"] = (
                item.get("supports_return_import") is True
            )
            blocked["blocked_reason"] = "invalid_returned_package"
            blocked_files.append(blocked)
            continue
        counts = validation.get("counts") if isinstance(validation.get("counts"), dict) else {}
        record_count = counts.get("records")
        if not isinstance(record_count, int) or isinstance(record_count, bool) or record_count < 1:
            blocked = dict(item)
            blocked["docs_review_supported"] = True
            blocked["return_import_supported"] = (
                item.get("supports_return_import") is True
            )
            blocked["blocked_reason"] = "invalid_returned_package"
            blocked_files.append(blocked)
            continue
        item["docs_review_supported"] = True
        item["return_import_supported"] = (
            item.get("supports_return_import") is True
        )
        item["document_count"] = record_count
        files.append(item)
    report["files"] = files
    report["blocked_files"] = blocked_files
    report["unassigned_files"] = unassigned_files
    report["required_capability"] = required_capability
    if normalized_collection is not None:
        report["collection"] = normalized_collection
    return report
