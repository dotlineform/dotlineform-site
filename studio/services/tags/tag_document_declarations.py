#!/usr/bin/env python3
"""Resolve current document-owned Tag declarations for Studio guards."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import docs_document_location as document_location
import docs_source_model as source_model
from docs_scope_config import load_docs_scope_configs
from docs_tag_documents import normalize_tag_declaration


ANALYSIS_TAGS_SCOPE = "analysis"
ANALYSIS_TAGS_SUB_SCOPE = "tags"


def current_tag_document_associations(
    repo_root: Path,
    tag_id: str,
) -> list[dict[str, Any]]:
    """Return sorted exact current source documents declaring one Tag."""

    requested = normalize_tag_declaration({"tag_id": tag_id})
    if requested["state"] != "valid":
        raise ValueError("tag_id must be one exact canonical tag id")

    configs = load_docs_scope_configs(repo_root, scope_ids=[ANALYSIS_TAGS_SCOPE])
    parent_config = configs.get(ANALYSIS_TAGS_SCOPE)
    if parent_config is None:
        raise ValueError("Analysis Docs Viewer scope is not configured")
    matching = [
        candidate
        for candidate in parent_config.sub_scopes
        if candidate.sub_scope == ANALYSIS_TAGS_SUB_SCOPE
    ]
    if len(matching) != 1:
        raise ValueError("Analysis Tags document collection is not configured")
    documents = source_model.load_document_collection_docs_for_config(
        repo_root,
        parent_config,
        matching[0],
    )
    collection_url = document_location.management_collection_viewer_url(
        repo_root,
        ANALYSIS_TAGS_SCOPE,
        ANALYSIS_TAGS_SUB_SCOPE,
    )
    associations: list[dict[str, Any]] = []
    for document in documents:
        declaration = normalize_tag_declaration(document.front_matter)
        if (
            declaration["state"] != "valid"
            or declaration["tag_id"] != tag_id
        ):
            continue
        associations.append(
            {
                "target": {
                    "scope": ANALYSIS_TAGS_SCOPE,
                    "sub_scope": ANALYSIS_TAGS_SUB_SCOPE,
                    "doc_id": document.doc_id,
                },
                "title": document.title,
                "url": document_location.management_document_viewer_url(
                    collection_url,
                    document.doc_id,
                    sub_scope=True,
                ),
            }
        )
    associations.sort(
        key=lambda record: (
            record["target"]["scope"],
            record["target"]["sub_scope"],
            record["target"]["doc_id"],
        )
    )
    return associations


__all__ = ["current_tag_document_associations"]
