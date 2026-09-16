#!/usr/bin/env python3
"""Resolve canonical Docs Viewer locations from source configuration."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from urllib.parse import quote

from docs_document_identity import is_immutable_doc_id
from docs_workspace_config import (
    DocsStageConfig,
    DocsCollectionConfig,
    load_docs_stage,
    require_selected_stage,
)


def collection_report_placement(
    repo_root: Path,
    collection_id: str,
    *,
    eligible_parent_doc_ids: Collection[str] | None = None,
    stage: str,
) -> tuple[DocsStageConfig, DocsCollectionConfig, str]:
    """Read the configured host ID without loading or validating its document.

    Callers may restrict placement to an already selected set of document IDs.
    """

    config = load_docs_stage(repo_root, stage)
    matching_collections = [
        collection
        for collection in config.collections
        if collection.collection == collection_id
    ]
    if len(matching_collections) != 1:
        raise ValueError(
            f"Docs Viewer collection must resolve exactly once: "
            f"{stage}/{collection_id}"
        )
    collection = matching_collections[0]
    eligible_ids = (
        {str(doc_id or "").strip() for doc_id in eligible_parent_doc_ids}
        if eligible_parent_doc_ids is not None
        else None
    )

    host_id = collection.report_host_doc_id
    if eligible_ids is not None and host_id not in eligible_ids:
        raise ValueError(
            f"Docs Viewer configured collection report is outside the selected documents: "
            f"{stage}/{collection_id} ({host_id})"
        )
    return config, collection, host_id


def canonical_document_viewer_url(config: DocsStageConfig, doc_id: str, *, subdoc_id: str = "") -> str:
    """Build an ordinary location from explicit document/host identity, without a workflow stage."""
    require_selected_stage(config)
    if not is_immutable_doc_id(doc_id) or (subdoc_id and not is_immutable_doc_id(subdoc_id)):
        raise ValueError("doc_id and subdoc_id must use immutable document identity")
    pairs = [f"doc={quote(doc_id)}"]
    if subdoc_id:
        pairs.append(f"subdoc={quote(subdoc_id)}")
    return f"/docs/?{'&'.join(pairs)}"


def canonical_collection_document_url(
    repo_root: Path,
    collection_id: str,
    doc_id: str,
    *,
    stage: str,
) -> str:
    """Resolve the exact stage's report host, returning a stage-free document URL."""

    normalized_doc_id = str(doc_id or "").strip()
    if not is_immutable_doc_id(normalized_doc_id):
        raise ValueError("doc_id must use immutable document identity")

    config, _collection, parent_doc_id = collection_report_placement(
        repo_root,
        collection_id,
        stage=stage,
    )

    return canonical_document_viewer_url(config, parent_doc_id, subdoc_id=normalized_doc_id)


def management_collection_viewer_url(
    repo_root: Path,
    collection_id: str = "",
    *,
    stage: str,
) -> str:
    """Return the exact local Manage URL for one configured collection."""

    normalized_collection = str(collection_id or "").strip().lower()
    config = load_docs_stage(repo_root, stage)
    url = f"/docs/?stage={quote(config.stage)}"
    if not normalized_collection:
        return url
    _config, _collection, parent_doc_id = collection_report_placement(
        repo_root,
        normalized_collection,
        stage=config.stage,
    )
    return f"{url}&doc={quote(parent_doc_id)}"


def management_document_viewer_url(
    collection_url: str,
    doc_id: str,
    *,
    collection: bool,
) -> str:
    """Extend a prevalidated collection URL with one exact document identity."""

    normalized_doc_id = str(doc_id or "").strip()
    if not is_immutable_doc_id(normalized_doc_id):
        raise ValueError("doc_id must use immutable document identity")
    separator = "&" if "?" in collection_url else "?"
    key = "subdoc" if collection else "doc"
    return f"{collection_url}{separator}{key}={quote(normalized_doc_id)}"


__all__ = [
    "canonical_document_viewer_url",
    "canonical_collection_document_url",
    "management_collection_viewer_url",
    "management_document_viewer_url",
    "collection_report_placement",
]
