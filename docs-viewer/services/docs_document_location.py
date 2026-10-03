#!/usr/bin/env python3
"""Resolve canonical Docs Viewer locations from source configuration."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from urllib.parse import quote, parse_qsl, urlencode, urlsplit, urlunsplit

from docs_document_identity import is_document_id
from docs_workspace_config import (
    DocsStageConfig,
    DocsCollectionConfig,
    load_docs_working_config,
)


def collection_report_placement(
    repo_root: Path,
    collection_id: str,
    *,
    eligible_parent_doc_ids: Collection[str] | None = None,
) -> tuple[DocsStageConfig, DocsCollectionConfig, str]:
    """Read the configured host ID without loading or validating its document.

    Callers may restrict placement to an already selected set of document IDs.
    """

    config = load_docs_working_config(repo_root)
    matching_collections = [
        collection
        for collection in config.collections
        if collection.collection == collection_id
    ]
    if len(matching_collections) != 1:
        raise ValueError(
            f"Docs Viewer collection must resolve exactly once: "
            f"{collection_id}"
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
            f"{collection_id} ({host_id})"
        )
    return config, collection, host_id


def canonical_document_viewer_url(doc_id: str, *, collection: str = "") -> str:
    """Address the exact storage owner and document, independently of its browse host."""
    if not is_document_id(doc_id, collection=collection):
        raise ValueError("doc_id must use immutable document identity")
    pairs = ([f"collection={quote(collection)}"] if collection else []) + [f"doc={quote(doc_id)}"]
    return f"/docs/?{'&'.join(pairs)}"


def canonical_collection_document_url(
    repo_root: Path,
    collection_id: str,
    doc_id: str,
) -> str:
    """Validate the configured collection and address its exact document."""

    normalized_doc_id = str(doc_id or "").strip()
    if not is_document_id(normalized_doc_id, collection=collection_id):
        raise ValueError("doc_id must use immutable document identity")

    collection_report_placement(
        repo_root,
        collection_id,
    )

    return canonical_document_viewer_url(normalized_doc_id, collection=collection_id)


def management_collection_viewer_url(
    repo_root: Path,
    collection_id: str = "",
) -> str:
    """Return the exact local Manage URL for one configured collection."""

    normalized_collection = str(collection_id or "").strip().lower()
    url = "/docs/"
    if not normalized_collection:
        return url
    _config, _collection, parent_doc_id = collection_report_placement(
        repo_root,
        normalized_collection,
    )
    return f"{url}?doc={quote(parent_doc_id)}"


def management_document_viewer_url(
    collection_url: str,
    doc_id: str,
    *,
    collection: bool,
    collection_id: str = "",
) -> str:
    """Extend a prevalidated collection URL with one exact document identity."""

    normalized_doc_id = str(doc_id or "").strip()
    if not is_document_id(normalized_doc_id, collection=collection_id):
        raise ValueError("doc_id must use immutable document identity")
    if collection and not collection_id:
        raise ValueError("Named document navigation requires its exact collection")
    location = urlsplit(collection_url)
    pairs = [(key, value) for key, value in parse_qsl(location.query) if key not in {"doc", "collection"}]
    if collection:
        pairs.append(("collection", collection_id))
    pairs.append(("doc", normalized_doc_id))
    return urlunsplit((location.scheme, location.netloc, location.path, urlencode(pairs), location.fragment))


__all__ = [
    "canonical_document_viewer_url",
    "canonical_collection_document_url",
    "management_collection_viewer_url",
    "management_document_viewer_url",
    "collection_report_placement",
]
