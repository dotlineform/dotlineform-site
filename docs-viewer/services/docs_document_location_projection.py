#!/usr/bin/env python3
"""Build public document-location records from publishable Docs Viewer data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, quote, urlsplit

from docs_document_identity import is_immutable_doc_id
from docs_scope_config import (
    DocsScopeConfig,
    public_documents_path,
    public_search_path,
    resolve_scope_path,
)


DOCUMENT_LOCATION_SCHEMA_VERSION = "docs_document_locations_v1"
SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS = ("analysis",)


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def document_location_projection_path(config: DocsScopeConfig) -> Path:
    """Return the public output path owned beside one scope's search index."""

    search_path = public_search_path(config)
    if search_path is None:
        raise ValueError(f"scope {config.scope_id!r} has no public search projection")
    return search_path.with_name("document-locations.json")


def canonical_search_entry(
    config: DocsScopeConfig,
    raw_entry: Any,
    *,
    field: str,
) -> tuple[str, str, str]:
    if not isinstance(raw_entry, dict):
        raise ValueError(f"{field} must be an object")
    if clean_text(raw_entry.get("kind")) != "doc":
        raise ValueError(f"{field}.kind must be doc")

    doc_id = clean_text(raw_entry.get("id"))
    title = clean_text(raw_entry.get("title"))
    href = clean_text(raw_entry.get("href"))
    if not is_immutable_doc_id(doc_id):
        raise ValueError(f"{field}.id must use immutable document identity")
    if not title:
        raise ValueError(f"{field}.title must not be empty")

    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.fragment or parsed.path != config.viewer_base_url:
        raise ValueError(f"{field}.href must use the configured canonical viewer route")
    expected_query = (
        [("scope", config.scope_id), ("doc", doc_id)]
        if config.include_scope_param
        else [("doc", doc_id)]
    )
    if parse_qsl(parsed.query, keep_blank_values=True) != expected_query:
        raise ValueError(f"{field}.href must contain only the canonical document query")
    return doc_id, title, href


def canonical_sub_scope_url(parent_url: str, doc_id: str) -> str:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("sub-scope doc_id must use immutable document identity")
    return f"{parent_url}&subdoc={quote(doc_id)}"


def sub_scope_manifest_records(payload: Any, *, field: str) -> list[tuple[str, str]]:
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
    config: DocsScopeConfig,
    *,
    search_payload: Any,
    parent_documents: Mapping[str, Any],
    sub_scope_manifests: Mapping[str, Any],
) -> dict[str, Any]:
    """Project exact public document and report placements for one scope.

    Inputs are already-public search, parent-document, and sub-scope manifest
    projections. Source front matter and manage manifests are intentionally
    outside this boundary.
    """

    if config.scope_id not in SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS:
        raise ValueError(f"unsupported document-location scope: {config.scope_id}")
    exact_records = build_exact_document_location_records(
        config,
        search_payload=search_payload,
        parent_documents=parent_documents,
        sub_scope_manifests=sub_scope_manifests,
    )
    return {
        "schema_version": DOCUMENT_LOCATION_SCHEMA_VERSION,
        "scope_id": config.scope_id,
        "records": [
            {
                "url": record["url"],
                "scope_id": record["scope_id"],
                "document_title": record["document_title"],
                "report_title": record["report_title"],
            }
            for record in exact_records
        ],
    }


def build_exact_document_location_records(
    config: DocsScopeConfig,
    *,
    search_payload: Any,
    parent_documents: Mapping[str, Any],
    sub_scope_manifests: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Retain exact source identity while projecting current public URLs.

    This is an internal producer seam. The public document-location payload
    intentionally continues to omit source identity.
    """

    if not isinstance(search_payload, dict) or not isinstance(search_payload.get("entries"), list):
        raise ValueError("public search entries must be an array")

    header = search_payload.get("header")
    if not isinstance(header, dict) or clean_text(header.get("scope")) != config.scope_id:
        raise ValueError("public search header scope does not match the requested scope")

    configured_sub_scopes = {sub_scope.sub_scope for sub_scope in config.sub_scopes}
    manifest_records: dict[str, list[tuple[str, str]]] = {}

    records: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    def append_record(
        *,
        doc_id: str,
        sub_scope: str,
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
                "scope_id": config.scope_id,
                "sub_scope": sub_scope,
                "doc_id": doc_id,
                "document_title": document_title,
                "report_title": report_title,
            }
        )

    for index, raw_entry in enumerate(search_payload["entries"]):
        doc_id, title, href = canonical_search_entry(
            config,
            raw_entry,
            field=f"search.entries[{index}]",
        )
        append_record(
            doc_id=doc_id,
            sub_scope="",
            url=href,
            document_title=title,
        )

        parent_payload = parent_documents.get(doc_id)
        if not isinstance(parent_payload, dict):
            raise ValueError(f"public parent payload is missing for search document {doc_id!r}")
        report = parent_payload.get("report")
        if not isinstance(report, dict) or clean_text(report.get("id")) != "docs_subscope":
            continue
        if clean_text(report.get("access")) != "public":
            continue

        sub_scope_id = clean_text(report.get("sub_scope")).lower()
        if sub_scope_id not in configured_sub_scopes:
            raise ValueError(
                f"public report {doc_id!r} references unsupported sub-scope "
                f"{sub_scope_id!r}"
            )
        if sub_scope_id not in manifest_records:
            manifest_records[sub_scope_id] = sub_scope_manifest_records(
                sub_scope_manifests.get(sub_scope_id),
                field=f"sub_scopes.{sub_scope_id}",
            )
        for child_doc_id, child_title in manifest_records[sub_scope_id]:
            append_record(
                doc_id=child_doc_id,
                sub_scope=sub_scope_id,
                url=canonical_sub_scope_url(href, child_doc_id),
                document_title=child_title,
                report_title=title,
            )

    return records


def load_public_document_location_inputs(
    repo_root: Path,
    config: DocsScopeConfig,
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    """Load the exact currently public inputs shared by location consumers."""

    search_path = public_search_path(config)
    documents_path = public_documents_path(config)
    if search_path is None or documents_path is None:
        raise ValueError(f"scope {config.scope_id!r} has no public projection")

    resolved_search_path = resolve_scope_path(repo_root, search_path)
    resolved_documents_path = resolve_scope_path(repo_root, documents_path)
    search_payload = json.loads(resolved_search_path.read_text(encoding="utf-8"))
    search_doc_ids = {
        clean_text(entry.get("id"))
        for entry in (
            search_payload.get("entries", [])
            if isinstance(search_payload, dict)
            else []
        )
        if isinstance(entry, dict)
    }
    parent_documents = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((resolved_documents_path / "by-id").glob("*.json"))
    }
    sub_scope_manifests = {}
    configured_sub_scopes = {
        sub_scope.sub_scope: sub_scope for sub_scope in config.sub_scopes
    }
    placed_sub_scope_ids = {
        clean_text(payload["report"].get("sub_scope")).lower()
        for doc_id, payload in parent_documents.items()
        if doc_id in search_doc_ids
        if isinstance(payload, dict)
        and isinstance(payload.get("report"), dict)
        and clean_text(payload["report"].get("id")) == "docs_subscope"
        and clean_text(payload["report"].get("access")) == "public"
    }
    for sub_scope_id in sorted(placed_sub_scope_ids):
        sub_scope = configured_sub_scopes.get(sub_scope_id)
        if sub_scope is None:
            raise ValueError(
                f"public report references unsupported sub-scope {sub_scope_id!r}"
            )
        sub_scope_path = public_documents_path(sub_scope)
        if sub_scope_path is None:
            raise ValueError(
                f"sub-scope {config.scope_id}/{sub_scope.sub_scope} has no public projection"
            )
        manifest_path = resolve_scope_path(repo_root, sub_scope_path) / "manifest.json"
        sub_scope_manifests[sub_scope.sub_scope] = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    return search_payload, parent_documents, sub_scope_manifests


def load_public_document_location_payload(
    repo_root: Path,
    config: DocsScopeConfig,
) -> dict[str, Any]:
    """Build from the currently published site projection without source reads."""

    search_payload, parent_documents, sub_scope_manifests = (
        load_public_document_location_inputs(repo_root, config)
    )

    return build_document_location_payload(
        config,
        search_payload=search_payload,
        parent_documents=parent_documents,
        sub_scope_manifests=sub_scope_manifests,
    )


def load_public_exact_document_location_records(
    repo_root: Path,
    config: DocsScopeConfig,
) -> list[dict[str, str]]:
    """Build exact internal records for any configured public scope."""

    search_payload, parent_documents, sub_scope_manifests = (
        load_public_document_location_inputs(repo_root, config)
    )
    return build_exact_document_location_records(
        config,
        search_payload=search_payload,
        parent_documents=parent_documents,
        sub_scope_manifests=sub_scope_manifests,
    )


__all__ = [
    "DOCUMENT_LOCATION_SCHEMA_VERSION",
    "SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS",
    "build_document_location_payload",
    "build_exact_document_location_records",
    "canonical_search_entry",
    "canonical_sub_scope_url",
    "document_location_projection_path",
    "json_bytes",
    "load_public_exact_document_location_records",
    "load_public_document_location_payload",
    "load_public_document_location_inputs",
]
