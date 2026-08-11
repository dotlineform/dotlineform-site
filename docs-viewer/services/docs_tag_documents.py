#!/usr/bin/env python3
"""Document-owned Tag declarations and private reverse associations."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

TAG_ID_FIELD = "tag_id"
TAG_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")
TAG_ASSOCIATIONS_SCHEMA_VERSION = "docs_tag_associations_v1"


def normalize_tag_declaration(front_matter: Mapping[str, Any]) -> dict[str, Any]:
    """Project one non-blocking state from exact document front matter."""

    if TAG_ID_FIELD not in front_matter:
        return {"state": "none", "tag_id": ""}
    raw_value = front_matter[TAG_ID_FIELD]
    if (
        not isinstance(raw_value, str)
        or not raw_value
        or raw_value != raw_value.strip()
        or TAG_ID_PATTERN.fullmatch(raw_value) is None
    ):
        return {
            "state": "malformed",
            "tag_id": "",
            "evidence": raw_value,
        }
    return {"state": "valid", "tag_id": raw_value}


def tag_declaration_generation(
    *,
    scope: str,
    sub_scope: str,
    declarations_by_doc_id: Mapping[str, Mapping[str, Any]],
) -> str:
    source = {
        "scope": scope,
        "sub_scope": sub_scope,
        "documents": [
            {
                "doc_id": doc_id,
                "tag_declaration": declarations_by_doc_id[doc_id],
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


def load_current_public_tag_locations(
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


def project_tag_associations(
    *,
    scope: str,
    sub_scope: str,
    documents: Sequence[Any],
    declarations_by_doc_id: Mapping[str, Mapping[str, Any]],
    declaration_generation: str,
    management_urls_by_doc_id: Mapping[str, str] | None = None,
    public_location_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Group valid document declarations into a deterministic private product."""

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

    documents_by_tag: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        doc_id = str(getattr(document, "doc_id", "") or "")
        declaration = declarations_by_doc_id.get(doc_id, {})
        if declaration.get("state") != "valid":
            continue
        tag_id = str(declaration.get("tag_id") or "")
        if TAG_ID_PATTERN.fullmatch(tag_id) is None:
            raise ValueError(f"valid Tag declaration is invalid for {doc_id!r}")
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
        documents_by_tag.setdefault(tag_id, []).append(
            {
                "target": {
                    "scope": scope,
                    "sub_scope": sub_scope,
                    "doc_id": doc_id,
                },
                "title": str(getattr(document, "title", "") or ""),
                "locations": locations,
            }
        )

    associations: list[dict[str, Any]] = []
    for tag_id in sorted(documents_by_tag):
        association_documents = sorted(
            documents_by_tag[tag_id],
            key=lambda record: (
                record["target"]["scope"],
                record["target"]["sub_scope"],
                record["target"]["doc_id"],
            ),
        )
        associations.append(
            {
                "tag_id": tag_id,
                "documents": association_documents,
            }
        )

    return {
        "schema_version": TAG_ASSOCIATIONS_SCHEMA_VERSION,
        "scope": scope,
        "sub_scope": sub_scope,
        "declaration_generation": declaration_generation,
        "associations": associations,
    }


__all__ = [
    "TAG_ASSOCIATIONS_SCHEMA_VERSION",
    "TAG_ID_FIELD",
    "TAG_ID_PATTERN",
    "load_current_public_tag_locations",
    "normalize_tag_declaration",
    "project_tag_associations",
    "tag_declaration_generation",
]
