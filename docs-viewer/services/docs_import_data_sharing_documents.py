#!/usr/bin/env python3
"""Data Sharing documents collection orchestration for managed Docs Import."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_import_collection_plan import (
    DocumentsCollectionPlan,
    blocked_collection_plan,
    plan_import_content_collection,
)
from docs_import_data_sharing_package import (
    data_sharing_record_states,
    load_data_sharing_documents_package,
    normalize_data_sharing_record_states,
)
from docs_source_model import load_scope_docs, normalize_scope
from services.paths import marker_path


COLLECTION_SOURCE_FORMAT = "data_sharing_documents"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def plan_data_sharing_documents_collection(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    staging_root: Path,
    workspace_root: Path,
    metadata_root: Path,
) -> DocumentsCollectionPlan:
    """Read and completely plan one trusted package without applying any writes."""

    normalized_scope = normalize_scope(scope)
    package, blockers = load_data_sharing_documents_package(
        repo_root,
        staged_filename=staged_filename,
        staging_root=staging_root,
        metadata_root=metadata_root,
    )
    if package is None:
        return blocked_collection_plan(
            source_format=COLLECTION_SOURCE_FORMAT,
            scope=normalized_scope,
            staged_filename=staged_filename,
            blockers=blockers,
            workspace_root=workspace_root,
        )

    docs = load_scope_docs(repo_root, normalized_scope)
    states, identity_blockers = data_sharing_record_states(package.raw_rows)
    blockers.extend(identity_blockers)
    blockers.extend(
        normalize_data_sharing_record_states(
            package,
            states,
            current_doc_ids={doc.doc_id for doc in docs},
            staged_filename=staged_filename,
        )
    )
    package_projection = {
        "export_id": package.export_id,
        "profile_id": _clean_text(
            package.adapter_metadata.get("profile_id")
            or package.adapter_metadata.get("config_id")
        ),
        "schema_version": _clean_text(package.adapter_metadata.get("schema_version")),
        "source_scope": _clean_text(package.adapter_metadata.get("scope")),
        "content_format": _clean_text(package.adapter_metadata.get("content_format")),
        "staged_path": marker_path(package.path, workspace_root=workspace_root),
        "source_sha256": package.source_sha256,
    }
    return plan_import_content_collection(
        repo_root,
        source_format=COLLECTION_SOURCE_FORMAT,
        scope=normalized_scope,
        staged_filename=staged_filename,
        states=states,
        docs=docs,
        staging_root=staging_root,
        workspace_root=workspace_root,
        package_projection=package_projection,
        blockers=blockers,
    )


__all__ = [
    "COLLECTION_SOURCE_FORMAT",
    "DocumentsCollectionPlan",
    "plan_data_sharing_documents_collection",
]
