#!/usr/bin/env python3
"""Build public document-location records from the accepted Docs Viewer snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, quote, urlsplit

from docs_document_identity import is_immutable_doc_id
from docs_workspace_config import (
    DocsWorkspaceConfig,
    select_workspace_stage,
    public_documents_path,
    public_search_path,
    resolve_workspace_path,
)


DOCUMENT_LOCATION_SCHEMA_VERSION = "docs_document_locations_v2"


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def document_location_projection_path(config: DocsWorkspaceConfig) -> Path:
    """Return the public output path owned beside the configured public search index."""

    search_path = public_search_path(config)
    if search_path is None:
        raise ValueError("Docs workspace has no public search projection")
    return search_path.with_name("document-locations.json")


def canonical_search_document(
    config: DocsWorkspaceConfig,
    raw_document: Any,
    *,
    field: str,
) -> tuple[str, str, str]:
    if not isinstance(raw_document, dict):
        raise ValueError(f"{field} must be an object")

    doc_id = clean_text(raw_document.get("id"))
    title = clean_text(raw_document.get("title"))
    href = clean_text(raw_document.get("href"))
    if not is_immutable_doc_id(doc_id):
        raise ValueError(f"{field}.id must use immutable document identity")
    if not title:
        raise ValueError(f"{field}.title must not be empty")

    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.fragment or parsed.path != config.public_viewer_base_url:
        raise ValueError(f"{field}.href must use the configured canonical viewer route")
    expected_query = [("doc", doc_id)]
    if parse_qsl(parsed.query, keep_blank_values=True) != expected_query:
        raise ValueError(f"{field}.href must contain only the canonical document query")
    return doc_id, title, href


def canonical_collection_url(parent_url: str, doc_id: str) -> str:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("collection doc_id must use immutable document identity")
    return f"{parent_url}&subdoc={quote(doc_id)}"


def collection_manifest_records(payload: Any, *, field: str) -> list[tuple[str, str]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("docs"), list):
        raise ValueError(f"{field}.docs must be an array")
    records: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(payload["docs"]):
        row_field = f"{field}.docs[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{row_field} must be an object")
        doc_id = clean_text(row.get("doc_id"))
        title = clean_text(row.get("title"))
        if not is_immutable_doc_id(doc_id):
            raise ValueError(f"{row_field}.doc_id must use immutable document identity")
        if not title:
            raise ValueError(f"{row_field}.title must not be empty")
        if doc_id in seen:
            raise ValueError(f"{field} contains duplicate doc_id {doc_id!r}")
        seen.add(doc_id)
        records.append((doc_id, title))
    return records


def build_document_location_payload(
    config: DocsWorkspaceConfig,
    *,
    search_payload: Any,
    parent_documents: Mapping[str, Any],
    collection_manifests: Mapping[str, Any],
) -> dict[str, Any]:
    """Project exact public document and report placements for the public workspace.

    Inputs are already-public search, parent-document, and collection manifest
    projections. Source front matter and manage manifests are intentionally
    outside this boundary.
    """

    exact_records = build_exact_document_location_records(
        config,
        search_payload=search_payload,
        parent_documents=parent_documents,
        collection_manifests=collection_manifests,
    )
    return {
        "schema_version": DOCUMENT_LOCATION_SCHEMA_VERSION,
        "records": [
            {
                "url": record["url"],
                "document_title": record["document_title"],
                "report_title": record["report_title"],
            }
            for record in exact_records
        ],
    }


def build_exact_document_location_records(
    config: DocsWorkspaceConfig,
    *,
    search_payload: Any,
    parent_documents: Mapping[str, Any],
    collection_manifests: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Retain exact source identity while projecting current public URLs.

    This is an internal producer seam. The public document-location payload
    intentionally continues to omit source identity.
    """

    if not isinstance(search_payload, dict) or not isinstance(search_payload.get("docs"), list):
        raise ValueError("public search docs must be an array")

    header = search_payload.get("header")
    if (
        not isinstance(header, dict)
        or clean_text(header.get("schema")) != "docs_viewer_search_index_v3"
        or "scope" in header
        or header.get("stage") != "published"
    ):
        raise ValueError("public search must describe the deployed document set")

    configured_collections = {collection.collection for collection in select_workspace_stage(config, "preview").collections}
    manifest_records: dict[str, list[tuple[str, str]]] = {}

    records: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    def append_record(
        *,
        doc_id: str,
        collection: str,
        url: str,
        document_title: str,
        report_title: str = "",
    ) -> None:
        if url in seen_urls:
            raise ValueError(f"duplicate document-location URL: {url}")
        seen_urls.add(url)
        records.append(
            {
                "url": url,
                "collection": collection,
                "doc_id": doc_id,
                "document_title": document_title,
                "report_title": report_title,
            }
        )

    for index, raw_document in enumerate(search_payload["docs"]):
        if isinstance(raw_document, dict) and clean_text(raw_document.get("collection")):
            continue
        doc_id, title, href = canonical_search_document(
            config,
            raw_document,
            field=f"search.docs[{index}]",
        )
        append_record(
            doc_id=doc_id,
            collection="",
            url=href,
            document_title=title,
        )

        parent_payload = parent_documents.get(doc_id)
        if not isinstance(parent_payload, dict):
            raise ValueError(f"public parent payload is missing for search document {doc_id!r}")
        report = parent_payload.get("report")
        if not isinstance(report, dict) or clean_text(report.get("id")) != "docs_collection":
            continue

        collection_id = clean_text(report.get("collection")).lower()
        if collection_id not in configured_collections:
            raise ValueError(
                f"public report {doc_id!r} references unsupported collection "
                f"{collection_id!r}"
            )
        if collection_id not in manifest_records:
            manifest_records[collection_id] = collection_manifest_records(
                collection_manifests.get(collection_id),
                field=f"collections.{collection_id}",
            )
        for child_doc_id, child_title in manifest_records[collection_id]:
            append_record(
                doc_id=child_doc_id,
                collection=collection_id,
                url=canonical_collection_url(href, child_doc_id),
                document_title=child_title,
                report_title=title,
            )

    return records


def load_public_document_location_inputs(
    repo_root: Path,
    config: DocsWorkspaceConfig,
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    """Load the exact currently public inputs shared by location consumers."""

    search_path = public_search_path(config)
    documents_path = public_documents_path(config)
    if search_path is None or documents_path is None:
        raise ValueError("Docs workspace has no public projection")

    resolved_search_path = resolve_workspace_path(repo_root, search_path)
    resolved_documents_path = resolve_workspace_path(repo_root, documents_path)
    search_payload = json.loads(resolved_search_path.read_text(encoding="utf-8"))
    search_doc_ids = {
        clean_text(document.get("id"))
        for document in (
            search_payload.get("docs", [])
            if isinstance(search_payload, dict)
            else []
        )
        if isinstance(document, dict)
        and not clean_text(document.get("collection"))
    }
    parent_documents = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((resolved_documents_path / "by-id").glob("*.json"))
    }
    collection_manifests = {}
    configured_collections = {
        collection.collection: collection for collection in select_workspace_stage(config, "preview").collections
    }
    placed_collection_ids = {
        clean_text(payload["report"].get("collection")).lower()
        for doc_id, payload in parent_documents.items()
        if doc_id in search_doc_ids
        if isinstance(payload, dict)
        and isinstance(payload.get("report"), dict)
        and clean_text(payload["report"].get("id")) == "docs_collection"
    }
    for collection_id in sorted(placed_collection_ids):
        collection = configured_collections.get(collection_id)
        if collection is None:
            raise ValueError(
                f"public report references unsupported collection {collection_id!r}"
            )
        collection_path = public_documents_path(collection)
        if collection_path is None:
            raise ValueError(
                f"collection {collection.collection} has no public projection"
            )
        manifest_path = resolve_workspace_path(repo_root, collection_path) / "manifest.json"
        collection_manifests[collection.collection] = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    return search_payload, parent_documents, collection_manifests


def load_public_document_location_payload(
    repo_root: Path,
    config: DocsWorkspaceConfig,
) -> dict[str, Any]:
    """Build from the currently published site projection without source reads."""

    search_payload, parent_documents, collection_manifests = (
        load_public_document_location_inputs(repo_root, config)
    )

    return build_document_location_payload(
        config,
        search_payload=search_payload,
        parent_documents=parent_documents,
        collection_manifests=collection_manifests,
    )


def load_public_exact_document_location_records(
    repo_root: Path,
    config: DocsWorkspaceConfig,
) -> list[dict[str, str]]:
    """Build exact internal records for the configured public workspace."""

    search_payload, parent_documents, collection_manifests = (
        load_public_document_location_inputs(repo_root, config)
    )
    return build_exact_document_location_records(
        config,
        search_payload=search_payload,
        parent_documents=parent_documents,
        collection_manifests=collection_manifests,
    )


__all__ = [
    "DOCUMENT_LOCATION_SCHEMA_VERSION",
    "build_document_location_payload",
    "build_exact_document_location_records",
    "canonical_search_document",
    "canonical_collection_url",
    "document_location_projection_path",
    "json_bytes",
    "load_public_exact_document_location_records",
    "load_public_document_location_payload",
    "load_public_document_location_inputs",
]
