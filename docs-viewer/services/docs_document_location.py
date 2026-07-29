#!/usr/bin/env python3
"""Resolve canonical Docs Viewer locations from source configuration."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import docs_source_model as source_model
from docs_document_identity import is_immutable_doc_id
from docs_scope_config import (
    document_source_path,
    load_docs_scope_configs,
    resolve_scope_path,
)


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

    parent_root = resolve_scope_path(repo_root, document_source_path(config))
    matching_reports: list[str] = []
    for path in sorted(parent_root.glob("*.md")):
        front_matter, _body = source_model.parse_source(path)
        if (
            front_matter.get("viewer_report") == "docs_subscope"
            and front_matter.get("viewer_report_subscope") == sub_scope_id
        ):
            parent_doc_id = str(front_matter.get("doc_id") or "").strip()
            if not is_immutable_doc_id(parent_doc_id):
                raise ValueError(
                    f"Docs Viewer sub-scope report has invalid doc_id: {path}"
                )
            matching_reports.append(parent_doc_id)
    if len(matching_reports) != 1:
        raise ValueError(
            f"Docs Viewer sub-scope report must resolve exactly once for "
            f"{scope_id}/{sub_scope_id}; found {len(matching_reports)}"
        )

    pairs: list[str] = []
    if config.include_scope_param:
        pairs.append(f"scope={quote(config.scope_id)}")
    pairs.append(f"doc={quote(matching_reports[0])}")
    pairs.append(f"subdoc={quote(normalized_doc_id)}")
    return f"{config.viewer_base_url}?{'&'.join(pairs)}"


__all__ = ["canonical_sub_scope_document_url"]
