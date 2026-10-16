from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from docs_artifact_locations import (
    artifact_location_adapter,
    normalize_artifact_identity,
)
from docs_media_inventory import source_media_references
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig, resolve_location_path


def collection_markdown_sources(repo_root: Path, config: DocsStageConfig | DocsCollectionConfig) -> tuple[str, ...]:
    """Read only the documents belonging to this media owner."""
    roots = [resolve_location_path(repo_root, config.source.location) / config.source.documents_path]
    sources: list[str] = []
    for root in roots:
        sources.extend(path.read_text(encoding="utf-8") for path in sorted(root.glob("*.md")))
    return tuple(sources)


def referenced_media_identities(
    config: DocsStageConfig | DocsCollectionConfig,
    markdown_sources: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    identities: dict[str, set[str]] = {media_type: set() for media_type in config.media.types}
    for source in markdown_sources:
        for reference in source_media_references(config, source, doc_id=""):
            identities[reference.media_type].add(normalize_artifact_identity(reference.identity))
    return {
        media_type: tuple(sorted(values))
        for media_type, values in sorted(identities.items())
    }


def build_collection_media_snapshot(
    repo_root: Path,
    config: DocsStageConfig | DocsCollectionConfig,
    *,
    write: bool,
    markdown_sources: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Check referenced ready files during explicit media maintenance."""

    markdown_sources = collection_markdown_sources(repo_root, config) if markdown_sources is None else tuple(markdown_sources)
    referenced = referenced_media_identities(config, markdown_sources)
    type_results: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    asset_references = set()
    for media_type, media in sorted(config.media.types.items()):
        assets = artifact_location_adapter(repo_root, media.asset_location)
        available = []
        for identity in referenced[media_type]:
            if assets.stat(identity) is None:
                missing.append(f"{media.reference_prefix.as_posix()}/{identity}")
                continue
            available.append(identity)
            relative = media.asset_location.path.relative_to(config.media.asset_root.path) / identity
            asset_references.add(relative.as_posix())
        type_results[media_type] = {
            "referenced": len(referenced[media_type]), "available": len(available),
            "identities": available,
        }

    if write and missing:
        raise FileNotFoundError("Required shared document media is unavailable: " + ", ".join(sorted(missing)))

    return {
        "stage": config.stage,
        "write": write,
        "source_documents": len(markdown_sources),
        "missing_references": sorted(missing),
        "asset_references": sorted(asset_references),
        "types": type_results,
    }


__all__ = [
    "build_collection_media_snapshot",
    "referenced_media_identities",
    "collection_markdown_sources",
]
