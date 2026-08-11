#!/usr/bin/env python3
"""Resolve current document-owned Tag declarations for Studio guards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import docs_document_location as document_location
from docs_document_identity import is_immutable_doc_id
import docs_source_model as source_model
from docs_scope_config import (
    load_docs_scope_configs,
    published_documents_path,
    resolve_scope_path,
)
from docs_tag_documents import (
    TAG_ASSOCIATIONS_SCHEMA_VERSION,
    TAG_ID_PATTERN,
    normalize_tag_declaration,
)


ANALYSIS_TAGS_SCOPE = "analysis"
ANALYSIS_TAGS_SUB_SCOPE = "tags"


def _analysis_tags_config(repo_root: Path) -> tuple[Any, Any]:
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
    return parent_config, matching[0]


def load_tag_document_association_payload(repo_root: Path) -> dict[str, Any]:
    """Load and validate the private deterministic Tag association product."""

    _parent_config, tags_config = _analysis_tags_config(repo_root)
    path = (
        resolve_scope_path(repo_root, published_documents_path(tags_config))
        / "tag-associations.json"
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Tag document associations are unavailable") from error
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != TAG_ASSOCIATIONS_SCHEMA_VERSION
        or payload.get("scope") != ANALYSIS_TAGS_SCOPE
        or payload.get("sub_scope") != ANALYSIS_TAGS_SUB_SCOPE
        or not isinstance(payload.get("declaration_generation"), str)
        or not isinstance(payload.get("associations"), list)
    ):
        raise ValueError("Tag document associations are invalid")

    previous_tag_id = ""
    for association in payload["associations"]:
        if not isinstance(association, dict):
            raise ValueError("Tag document association must be an object")
        tag_id = str(association.get("tag_id") or "")
        documents = association.get("documents")
        if (
            TAG_ID_PATTERN.fullmatch(tag_id) is None
            or tag_id <= previous_tag_id
            or not isinstance(documents, list)
        ):
            raise ValueError("Tag document associations are not canonical")
        previous_tag_id = tag_id
        previous_target: tuple[str, str, str] | None = None
        for document in documents:
            target = document.get("target") if isinstance(document, dict) else None
            locations = document.get("locations") if isinstance(document, dict) else None
            if not isinstance(target, dict) or not isinstance(locations, list):
                raise ValueError("Tag association document is invalid")
            target_key = (
                str(target.get("scope") or ""),
                str(target.get("sub_scope") or ""),
                str(target.get("doc_id") or ""),
            )
            if (
                target_key[0] != ANALYSIS_TAGS_SCOPE
                or target_key[1] != ANALYSIS_TAGS_SUB_SCOPE
                or not is_immutable_doc_id(target_key[2])
                or (previous_target is not None and target_key <= previous_target)
            ):
                raise ValueError("Tag association document target is invalid")
            previous_target = target_key
    return payload


def current_tag_document_associations(
    repo_root: Path,
    tag_id: str,
) -> list[dict[str, Any]]:
    """Return sorted exact current source documents declaring one Tag."""

    requested = normalize_tag_declaration({"tag_id": tag_id})
    if requested["state"] != "valid":
        raise ValueError("tag_id must be one exact canonical tag id")

    parent_config, tags_config = _analysis_tags_config(repo_root)
    documents = source_model.load_document_collection_docs_for_config(
        repo_root,
        parent_config,
        tags_config,
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


__all__ = [
    "current_tag_document_associations",
    "load_tag_document_association_payload",
]
