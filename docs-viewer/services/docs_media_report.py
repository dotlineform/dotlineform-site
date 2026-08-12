#!/usr/bin/env python3
"""Build exact live-file rows for the local Docs Media report."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

import docs_document_location as document_location
import docs_source_model as source_model
from docs_local_links import encode_relative_target
from docs_media_inventory import (
    DocsMediaReference,
    inventory_scope_media,
    source_media_references,
)
from docs_scope_config import DocsScopeConfig


REPORT_SCHEMA_VERSION = "docs_media_report_v1"


def _document_references(
    repo_root: Path,
    config: DocsScopeConfig,
) -> tuple[
    tuple[DocsMediaReference, ...],
    dict[tuple[str, str], dict[tuple[str, str, str], dict[str, object]]],
]:
    references: list[DocsMediaReference] = []
    documents_by_media: dict[
        tuple[str, str],
        dict[tuple[str, str, str], dict[str, object]],
    ] = {}
    collections = (
        ("", config),
        *((sub_scope.sub_scope, sub_scope) for sub_scope in config.sub_scopes),
    )
    for sub_scope, collection_config in collections:
        collection_url = document_location.management_collection_viewer_url(
            repo_root,
            config.scope_id,
            sub_scope,
        )
        for document in source_model.load_document_collection_docs_for_config(
            repo_root,
            config,
            collection_config,
        ):
            target_key = (config.scope_id, sub_scope, document.doc_id)
            target = {
                "scope": config.scope_id,
                "sub_scope": sub_scope,
                "doc_id": document.doc_id,
            }
            presentation = {
                "target": target,
                "title": document.title,
                "href": document_location.management_document_viewer_url(
                    collection_url,
                    document.doc_id,
                    sub_scope=bool(sub_scope),
                ),
            }
            for reference in source_media_references(
                config,
                document.source_text,
                doc_id=document.doc_id,
            ):
                references.append(reference)
                documents_by_media.setdefault(
                    (reference.media_type, reference.identity),
                    {},
                )[target_key] = presentation
    return tuple(references), documents_by_media


def _local_target(scope: str, role: str, media_type: str, identity: str) -> str:
    parts = ["docs-viewer", "media", scope]
    if role == "source":
        parts.append("build-source")
    elif role != "published":
        raise ValueError(f"unsupported Docs media inventory role: {role}")
    parts.extend((media_type, identity))
    return encode_relative_target(PurePosixPath(*parts).as_posix())


def build_docs_media_report(
    repo_root: Path,
    config: DocsScopeConfig,
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Return one exact row per live ready-media or build-source object."""

    references, documents_by_media = _document_references(repo_root, config)
    inventory = inventory_scope_media(
        repo_root,
        config,
        references=references,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    rows: list[dict[str, Any]] = []
    for item in inventory.items:
        documents = list(
            documents_by_media.get((item.media_type, item.identity), {}).values()
        )
        documents.sort(
            key=lambda document: (
                str(document["title"]).casefold(),
                str(document["title"]),
                str(document["href"]),
            )
        )
        rows.append(
            {
                "scope": item.scope,
                "media_type": item.media_type,
                "identity": item.identity,
                "local_target": _local_target(
                    item.scope,
                    item.role,
                    item.media_type,
                    item.identity,
                ),
                "documents": documents,
            }
        )
    rows.sort(
        key=lambda row: (
            str(row["media_type"]).casefold(),
            str(row["media_type"]),
            str(row["identity"]).casefold(),
            str(row["identity"]),
        )
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "scope": config.scope_id,
        "rows": rows,
    }


__all__ = ["REPORT_SCHEMA_VERSION", "build_docs_media_report"]
