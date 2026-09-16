#!/usr/bin/env python3
"""Build exact live-file rows for the local Docs Media report."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping

import docs_document_location as document_location
import docs_source_model as source_model
from docs_artifact_locations import local_artifact_path
from docs_media_inventory import (
    DocsMediaReference,
    inventory_collection_media,
    source_media_references,
)
from docs_workspace_config import DocsStageConfig, DocsSubScopeConfig, load_docs_media_owner


REPORT_SCHEMA_VERSION = "docs_media_report_v4"


def _document_references(
    repo_root: Path,
    config: DocsStageConfig,
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
        documents = source_model.load_document_collection_docs_for_config(
            repo_root, config, collection_config,
        )
        if not documents:
            continue
        collection_url = document_location.management_collection_viewer_url(
            repo_root,
            sub_scope,
            stage=config.stage,
        )
        for document in documents:
            target_key = (config.stage, sub_scope, document.doc_id)
            target = {
                "stage": config.stage,
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


def _source_path(
    repo_root: Path, config: DocsStageConfig | DocsSubScopeConfig,
    role: str, media_type: str, identity: str,
) -> Path:
    if role == "build-source":
        media = config.media.build_sources.get(media_type)
        location = media.location if media is not None else None
    elif role == "source":
        media = config.media.types.get(media_type)
        location = media.source_location if media is not None else None
    else:
        raise ValueError(f"unsupported Docs media inventory role: {role}")
    if location is None:
        raise ValueError("Docs media type is not configured for this collection and role")
    path = local_artifact_path(repo_root, location, identity)
    if path is None or not path.is_file():
        raise FileNotFoundError("Docs media source file is unavailable")
    return path


def open_media_source(
    repo_root: Path, body: dict[str, Any], *, dry_run: bool = False,
) -> dict[str, object]:
    """Reveal one exact configured Docs media file without accepting a filesystem path."""
    if set(body) != {"stage", "sub_scope", "role", "media_type", "identity"} or any(
        not isinstance(value, str) or value != value.strip() or (not value and key != "sub_scope")
        for key, value in body.items()
    ):
        raise ValueError("Docs media requires an exact stage, sub-scope, role, media type and identity")
    config = load_docs_media_owner(repo_root, body["stage"], body["sub_scope"])
    path = _source_path(repo_root, config, body["role"], body["media_type"], body["identity"])
    if sys.platform != "darwin":
        raise ValueError("Open in Finder is unavailable on this platform")
    if not dry_run:
        result = subprocess.run(["open", "-R", str(path)], cwd=repo_root, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError("Docs media source could not be revealed in Finder")
    return {"ok": True, **body, "dry_run": dry_run,
            "summary_text": "Docs media source validated." if dry_run else "Docs media source revealed in Finder."}


def build_docs_media_report(
    repo_root: Path,
    config: DocsStageConfig,
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Read one selected stage; retain configured file locations and document targets."""

    references, documents_by_media = _document_references(repo_root, config)
    inventory = inventory_collection_media(
        repo_root,
        config,
        references=references,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    rows: list[dict[str, Any]] = []
    for item in inventory.items:
        _source_path(repo_root, config, item.role, item.media_type, item.identity)
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
                "stage": item.stage,
                "sub_scope": item.sub_scope,
                "media_type": item.media_type,
                "identity": item.identity,
                "role": item.role,
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
        "stage": config.stage,
        "rows": rows,
    }


__all__ = ["REPORT_SCHEMA_VERSION", "build_docs_media_report", "open_media_source"]
