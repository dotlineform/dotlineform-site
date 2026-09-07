#!/usr/bin/env python3
"""Document-owned Concept declarations and private reverse associations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from docs_document_identities import (
    NUMERIC_IDENTITY_PATTERN,
    normalize_document_identity,
    validate_unique_document_identities,
)

CONCEPT_ID_FIELD = "concept_id"
CONCEPT_ASSOCIATIONS_SCHEMA_VERSION = "docs_concept_associations_v1"


def validate_unique_concept_declarations(declarations: Mapping[str, Mapping[str, Any]]) -> None:
    """Require one defining document per nonempty Concept ID in a collection."""

    validate_unique_document_identities(declarations, CONCEPT_ID_FIELD)


def load_concept_definitions(repo_root: Path, *, stage: str = "working") -> list[dict[str, Any]]:
    """Read exact Analysis Concept definitions and their stage-owned document destinations."""

    from docs_document_location import management_collection_viewer_url, management_document_viewer_url
    from docs_scope_config import load_docs_scope_stage
    from docs_source_model import load_document_collection_docs_for_config

    parent = load_docs_scope_stage(repo_root, "analysis", stage)
    collection = next((item for item in parent.sub_scopes if item.sub_scope == "concepts"), None)
    if collection is None:
        raise ValueError(f"Analysis {stage} Concepts collection is not configured")
    documents = load_document_collection_docs_for_config(repo_root, parent, collection)
    declarations = {doc.doc_id: normalize_concept_declaration(doc.front_matter) for doc in documents}
    validate_unique_concept_declarations(declarations)
    collection_url = management_collection_viewer_url(repo_root, "analysis", "concepts", stage=stage)
    return sorted(
        [
            {
                "concept_id": declarations[doc.doc_id][CONCEPT_ID_FIELD],
                "doc_id": doc.doc_id,
                "title": doc.title,
                "group": str(doc.front_matter.get("group") or ""),
                "href": management_document_viewer_url(collection_url, doc.doc_id, sub_scope=True),
            }
            for doc in documents
            if declarations[doc.doc_id]["state"] == "valid"
        ],
        key=lambda record: record[CONCEPT_ID_FIELD],
    )


def normalize_concept_declaration(front_matter: Mapping[str, Any]) -> dict[str, Any]:
    """Read an optional, exact numeric identity without deriving it from a title."""
    return normalize_document_identity(front_matter, CONCEPT_ID_FIELD)


def concept_declaration_generation(
    *,
    scope: str,
    stage: str = "",
    sub_scope: str,
    declarations_by_doc_id: Mapping[str, Mapping[str, Any]],
) -> str:
    source = {
        "scope": scope,
        "stage": stage,
        "sub_scope": sub_scope,
        "documents": [
            {
                "doc_id": doc_id,
                "concept_declaration": declarations_by_doc_id[doc_id],
            }
            for doc_id in sorted(declarations_by_doc_id)
        ],
    }
    encoded = json.dumps(
        source,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_current_public_concept_locations(
    repo_root: Path,
    *,
    scope: str,
    sub_scope: str,
) -> tuple[dict[str, str], ...]:
    """Read optional current public placements without making them identity inputs."""

    from docs_document_location_projection import (
        load_public_exact_document_location_records,
    )
    from docs_scope_config import load_docs_scope_configs, public_documents_path

    config = load_docs_scope_configs(repo_root, scope_ids=[scope]).get(scope)
    if config is None or public_documents_path(config) is None:
        return ()
    try:
        records = load_public_exact_document_location_records(repo_root, config)
    except (OSError, ValueError):
        return ()
    return tuple(
        record
        for record in records
        if record.get("scope_id") == scope and record.get("sub_scope") == sub_scope
    )


def project_concept_associations(
    *,
    scope: str,
    stage: str = "",
    sub_scope: str,
    documents: Sequence[Any],
    declarations_by_doc_id: Mapping[str, Mapping[str, Any]],
    declaration_generation: str,
    management_urls_by_doc_id: Mapping[str, str] | None = None,
    public_location_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Group valid document declarations into a deterministic private product."""

    validate_unique_concept_declarations(declarations_by_doc_id)
    management_urls = management_urls_by_doc_id or {}
    public_by_doc_id: dict[str, list[dict[str, str]]] = {}
    for raw_location in public_location_records:
        if (
            str(raw_location.get("scope_id") or "") != scope
            or str(raw_location.get("sub_scope") or "") != sub_scope
        ):
            continue
        doc_id = str(raw_location.get("doc_id") or "")
        url = str(raw_location.get("url") or "")
        if not doc_id or not url:
            continue
        public_by_doc_id.setdefault(doc_id, []).append(
            {
                "access": "public",
                "url": url,
                "title": str(raw_location.get("document_title") or ""),
                "report_title": str(raw_location.get("report_title") or ""),
            }
        )
    for locations in public_by_doc_id.values():
        locations.sort(
            key=lambda record: (
                record["url"],
                record["title"],
                record["report_title"],
            )
        )

    documents_by_concept: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        doc_id = str(getattr(document, "doc_id", "") or "")
        declaration = declarations_by_doc_id.get(doc_id, {})
        if declaration.get("state") != "valid":
            continue
        concept_id = str(declaration.get("concept_id") or "")
        if NUMERIC_IDENTITY_PATTERN.fullmatch(concept_id) is None:
            raise ValueError(f"valid Concept declaration is invalid for {doc_id!r}")
        locations: list[dict[str, str]] = []
        management_url = str(management_urls.get(doc_id) or "")
        if management_url:
            locations.append(
                {
                    "access": "manage",
                    "url": management_url,
                    "title": str(getattr(document, "title", "") or ""),
                    "report_title": "",
                }
            )
        locations.extend(public_by_doc_id.get(doc_id, ()))
        documents_by_concept.setdefault(concept_id, []).append(
            {
                "target": {
                    "scope": scope,
                    "stage": stage,
                    "sub_scope": sub_scope,
                    "doc_id": doc_id,
                },
                "title": str(getattr(document, "title", "") or ""),
                "locations": locations,
            }
        )

    associations: list[dict[str, Any]] = []
    for concept_id in sorted(documents_by_concept):
        association_documents = sorted(
            documents_by_concept[concept_id],
            key=lambda record: (
                record["target"]["scope"],
                record["target"]["sub_scope"],
                record["target"]["doc_id"],
            ),
        )
        associations.append(
            {
                "concept_id": concept_id,
                "documents": association_documents,
            }
        )

    return {
        "schema_version": CONCEPT_ASSOCIATIONS_SCHEMA_VERSION,
        "scope": scope,
        "stage": stage,
        "sub_scope": sub_scope,
        "declaration_generation": declaration_generation,
        "associations": associations,
    }


__all__ = [
    "CONCEPT_ASSOCIATIONS_SCHEMA_VERSION",
    "CONCEPT_ID_FIELD",
    "load_concept_definitions",
    "validate_unique_concept_declarations",
    "load_current_public_concept_locations",
    "normalize_concept_declaration",
    "project_concept_associations",
    "concept_declaration_generation",
]
