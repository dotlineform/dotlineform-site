#!/usr/bin/env python3
"""Resolve canonical Docs Viewer locations from source configuration."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from urllib.parse import quote

import docs_source_model as source_model
from docs_document_identity import is_immutable_doc_id
from docs_scope_config import (
    DocsScopeConfig,
    DocsSubScopeConfig,
    load_docs_scope_configs,
)


def sub_scope_report_placement(
    repo_root: Path,
    scope_id: str,
    sub_scope_id: str,
    *,
    eligible_parent_doc_ids: Collection[str] | None = None,
    require_public: bool = False,
) -> tuple[DocsScopeConfig, DocsSubScopeConfig, str]:
    """Resolve one configured child collection to its exact eligible report host."""

    configs = load_docs_scope_configs(repo_root, scope_ids=[scope_id])
    config = configs.get(scope_id)
    if config is None:
        raise ValueError(f"unknown Docs Viewer scope: {scope_id}")
    matching_sub_scopes = [
        sub_scope
        for sub_scope in config.sub_scopes
        if sub_scope.sub_scope == sub_scope_id
    ]
    if len(matching_sub_scopes) != 1:
        raise ValueError(
            f"Docs Viewer sub-scope must resolve exactly once: "
            f"{scope_id}/{sub_scope_id}"
        )
    sub_scope = matching_sub_scopes[0]
    eligible_ids = (
        {str(doc_id or "").strip() for doc_id in eligible_parent_doc_ids}
        if eligible_parent_doc_ids is not None
        else None
    )

    matching_reports: list[str] = []
    for document in source_model.load_scope_docs_for_config(repo_root, config):
        report = document.report
        if (
            report is not None
            and report.id == "docs_subscope"
            and report.sub_scope == sub_scope_id
            and (eligible_ids is None or document.doc_id in eligible_ids)
            and (not require_public or report.access == "public")
        ):
            parent_doc_id = document.doc_id
            if not is_immutable_doc_id(parent_doc_id):
                raise ValueError(
                    f"Docs Viewer sub-scope report has invalid doc_id: {document.path}"
                )
            matching_reports.append(parent_doc_id)
    if len(matching_reports) != 1:
        raise ValueError(
            f"Docs Viewer sub-scope report must resolve exactly once for "
            f"{scope_id}/{sub_scope_id}; found {len(matching_reports)}"
        )
    return config, sub_scope, matching_reports[0]


def canonical_sub_scope_document_url(
    repo_root: Path,
    scope_id: str,
    sub_scope_id: str,
    doc_id: str,
) -> str:
    """Return the configured canonical URL for one sub-scope document."""

    normalized_doc_id = str(doc_id or "").strip()
    if not is_immutable_doc_id(normalized_doc_id):
        raise ValueError("doc_id must use immutable document identity")

    config, _sub_scope, parent_doc_id = sub_scope_report_placement(
        repo_root,
        scope_id,
        sub_scope_id,
    )

    pairs: list[str] = []
    if config.include_scope_param:
        pairs.append(f"scope={quote(config.scope_id)}")
    pairs.append(f"doc={quote(parent_doc_id)}")
    pairs.append(f"subdoc={quote(normalized_doc_id)}")
    return f"{config.viewer_base_url}?{'&'.join(pairs)}"


def management_collection_viewer_url(
    repo_root: Path,
    scope_id: str,
    sub_scope_id: str = "",
) -> str:
    """Return the exact local Manage URL for one configured collection."""

    normalized_scope = str(scope_id or "").strip().lower()
    normalized_sub_scope = str(sub_scope_id or "").strip().lower()
    configs = load_docs_scope_configs(repo_root, scope_ids=[normalized_scope])
    if normalized_scope not in configs:
        raise ValueError(f"unknown Docs Viewer scope: {normalized_scope}")
    url = f"/docs/?scope={quote(normalized_scope)}"
    if not normalized_sub_scope:
        return url
    _config, _sub_scope, parent_doc_id = sub_scope_report_placement(
        repo_root,
        normalized_scope,
        normalized_sub_scope,
    )
    return f"{url}&doc={quote(parent_doc_id)}"


def management_document_viewer_url(
    collection_url: str,
    doc_id: str,
    *,
    sub_scope: bool,
) -> str:
    """Extend a prevalidated collection URL with one exact document identity."""

    normalized_doc_id = str(doc_id or "").strip()
    if not is_immutable_doc_id(normalized_doc_id):
        raise ValueError("doc_id must use immutable document identity")
    separator = "&" if "?" in collection_url else "?"
    key = "subdoc" if sub_scope else "doc"
    return f"{collection_url}{separator}{key}={quote(normalized_doc_id)}"


__all__ = [
    "canonical_sub_scope_document_url",
    "management_collection_viewer_url",
    "management_document_viewer_url",
    "sub_scope_report_placement",
]
