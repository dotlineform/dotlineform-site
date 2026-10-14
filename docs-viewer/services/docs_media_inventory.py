#!/usr/bin/env python3
"""Registered Docs media references and local filename inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping

from docs_artifact_locations import list_filesystem_artifact_identities
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig
from docs_document_images import document_thumbnail_filename, has_document_thumbnail
from docs_source_model import parse_source_text

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.semantic_tokens import SemanticTokenOccurrence, parse_semantic_tokens  # noqa: E402


MEDIA_REFERENCE_PATTERN = re.compile(r"\[\[(?:media|html-media):(?P<path>[^\]\s]+)(?:[^\]]*)\]\]")


@dataclass(frozen=True)
class DocsMediaReference:
    doc_id: str
    media_type: str
    identity: str
    logical_path: str


@dataclass(frozen=True)
class DocsMediaFile:
    collection: str
    media_type: str
    identity: str
    role: str


def source_media_references(
    config: DocsStageConfig | DocsCollectionConfig,
    source: str,
    *,
    doc_id: str,
    document_collection: str | None = None,
) -> tuple[DocsMediaReference, ...]:
    """Return configured, source-collection-owned media references from one document."""

    metadata, body = parse_source_text(source)
    return parsed_source_media_references(
        config, source, metadata=metadata,
        semantic_tokens=parse_semantic_tokens(body, registry=None),
        doc_id=doc_id, document_collection=document_collection,
    )


def parsed_source_media_references(
    config: DocsStageConfig | DocsCollectionConfig,
    source: str,
    *,
    metadata: Mapping[str, Any],
    semantic_tokens: Iterable[SemanticTokenOccurrence],
    doc_id: str,
    document_collection: str | None = None,
    exclude_media_types: frozenset[str] = frozenset(),
) -> tuple[DocsMediaReference, ...]:
    """Extract references using supplied metadata and completed token parsing."""

    found: set[tuple[str, str, str]] = set()
    owner_collection = getattr(config, "collection", "")
    media_types = {
        media_type: media for media_type, media in config.media.types.items()
        if media_type not in exclude_media_types
    }
    for token in semantic_tokens:
        if token.family != "image":
            continue
        for media_type, media in media_types.items():
            prefix = media.reference_prefix.as_posix() + "/"
            if media_type in {"img", "svg"} and token.media_path.startswith(prefix):
                found.add((media_type, token.media_path.removeprefix(prefix), token.media_path))
    if "thumbs" in media_types and (document_collection is None or document_collection == owner_collection):
        if has_document_thumbnail(metadata, collection=owner_collection):
            identity = document_thumbnail_filename(doc_id or metadata.get("doc_id", ""), collection=owner_collection)
            media = media_types["thumbs"]
            found.add(("thumbs", identity, f"{media.reference_prefix.as_posix()}/{identity}"))
    # New token fields and inactive examples must not leak into legacy path scans.
    legacy_source = re.sub(r"\[\[image:.*?\]\]", "", source, flags=re.DOTALL)
    for match in MEDIA_REFERENCE_PATTERN.finditer(legacy_source):
        logical_path = match.group("path").lstrip("/")
        for media_type, media in media_types.items():
            prefix = media.reference_prefix.as_posix() + "/"
            if logical_path.startswith(prefix):
                found.add((media_type, logical_path.removeprefix(prefix), logical_path))
    for media_type, media in media_types.items():
        for prefix in (media.reference_prefix.as_posix(), media.served_path_prefix):
            normalized_prefix = prefix.rstrip("/")
            pattern = re.compile(
                rf"{re.escape(normalized_prefix)}/"
                rf"(?P<identity>[^\s)\]\"'<>?#]+)"
            )
            for match in pattern.finditer(legacy_source):
                identity = match.group("identity").rstrip(".,;:")
                if identity:
                    found.add(
                        (
                            media_type,
                            identity,
                            f"{media.reference_prefix.as_posix()}/{identity}",
                        )
                    )
    return tuple(
        DocsMediaReference(
            doc_id=doc_id,
            media_type=media_type,
            identity=identity,
            logical_path=logical_path,
        )
        for media_type, identity, logical_path in sorted(found)
    )


def list_collection_media(
    repo_root: Path,
    config: DocsStageConfig | DocsCollectionConfig,
    *,
    exclude_media_types: frozenset[str] = frozenset(),
) -> tuple[DocsMediaFile, ...]:
    """List configured ready media and build sources without reading or joining documents.

    Callers may omit selected ready-media families without listing them.
    Storage placeholders are omitted. Display exclusions and ordering belong to
    consumers; no source bodies, paths or credentials enter the returned records.
    """
    published = {
        media_type: media.asset_location for media_type, media in config.media.types.items()
        if media_type not in exclude_media_types
    }
    build_sources = {build_type: build.location for build_type, build in config.media.build_sources.items()}
    items: list[DocsMediaFile] = []
    for role, locations in (("source", published), ("build-source", build_sources)):
        for media_type, location in locations.items():
            for identity in list_filesystem_artifact_identities(repo_root, location):
                if Path(identity).name == ".gitkeep":
                    continue
                items.append(DocsMediaFile(
                    collection=getattr(config, "collection", ""),
                    media_type=media_type,
                    identity=identity,
                    role=role,
                ))
    return tuple(items)


__all__ = [
    "DocsMediaFile",
    "DocsMediaReference",
    "list_collection_media",
    "parsed_source_media_references",
    "source_media_references",
]
