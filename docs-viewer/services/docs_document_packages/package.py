#!/usr/bin/env python3
"""Document package generation and returned-package listing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_document_packages.export import build_selected_export
from docs_document_packages.returned_common import (
    DOCS_REVIEW_CAPABILITY,
    RETURN_IMPORT_CAPABILITY,
)
from docs_document_packages.returned_profiles import (
    supported_docs_review_profile_ids,
    supported_return_import_profile_ids,
)
from docs_document_packages.returned_parser import parse_staged_import
from docs_document_packages.metadata import list_staged_files_with_metadata
import docs_source_model as source_model
from docs_workspace_config import load_docs_working_config
from docs_management_document_target import ManagedDocumentCollection


def build_document_package(
    repo_root: Path, *, owner: ManagedDocumentCollection, config_id: str,
    doc_ids: list[str], dry_run: bool, target_format: str, content_format: str,
    output_root: Path, metadata_root: Path,
) -> Dict[str, Any]:
    """Produce exactly the application's selected records through the shared exporter."""
    return build_selected_export(
        repo_root=repo_root, owner=owner, config_id=config_id, doc_ids=doc_ids,
        write=not dry_run, target_format=target_format, content_format=content_format,
        output_root=output_root, metadata_root=metadata_root,
    )


def list_returned_document_packages(
    repo_root: Path,
    *,
    collection: str | None = None,
    required_capability: str = DOCS_REVIEW_CAPABILITY,
    staging_root: Path,
    metadata_root: Path,
) -> Dict[str, Any]:
    """List reviewable packages or importable packages for one collection."""

    if required_capability not in {
        DOCS_REVIEW_CAPABILITY,
        RETURN_IMPORT_CAPABILITY,
    }:
        raise ValueError(
            f"unsupported returned-package capability: {required_capability}"
        )
    normalized_collection = (
        None
        if collection is None
        else str(collection or "").strip().lower()
    )
    if collection is not None and not normalized_collection:
        raise ValueError("collection is required for exact returned-package listing")
    workspace_config = load_docs_working_config(repo_root)
    collection_labels = {
        record.collection: record.title
        for record in workspace_config.collections
    }

    def add_collection_labels(item: dict[str, Any]) -> dict[str, Any]:
        collection = str(item.get("collection") or "").strip().lower()
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
    staged_files: list[dict[str, Any]] = []
    unassigned_files: list[dict[str, Any]] = []
    for item in report.get("files", []):
        if not item.get("metadata_ok"):
            unassigned_files.append(item)
            continue
        if str(item.get("data_domain") or "").strip() != "documents":
            continue
        item_collection = str(item.get("collection") or "").strip().lower()
        if normalized_collection is None or item_collection == normalized_collection:
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
        item_collection = str(item.get("collection") or "").strip().lower()
        if normalized_collection is None or item_collection == normalized_collection:
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
