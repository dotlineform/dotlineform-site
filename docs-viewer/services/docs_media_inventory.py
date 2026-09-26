#!/usr/bin/env python3
"""Provider-independent inventory of registered Docs Viewer media roles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Mapping

from docs_artifact_locations import (
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    local_artifact_path,
)
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig


MEDIA_REFERENCE_PATTERN = re.compile(r"\[\[(?:media|html-media):(?P<path>[^\]\s]+)(?:[^\]]*)\]\]")


@dataclass(frozen=True)
class DocsMediaReference:
    doc_id: str
    media_type: str
    identity: str
    logical_path: str


@dataclass(frozen=True)
class DocsMediaFile:
    stage: str
    collection: str
    media_type: str
    identity: str
    role: str


def source_media_references(
    config: DocsStageConfig | DocsCollectionConfig,
    source: str,
    *,
    doc_id: str,
) -> tuple[DocsMediaReference, ...]:
    """Return configured, source-collection-owned media references from one document."""

    found: set[tuple[str, str, str]] = set()
    for match in MEDIA_REFERENCE_PATTERN.finditer(source):
        logical_path = match.group("path").lstrip("/")
        for media_type, media in config.media.types.items():
            prefix = media.reference_prefix.as_posix() + "/"
            if logical_path.startswith(prefix):
                found.add((media_type, logical_path.removeprefix(prefix), logical_path))
    for media_type, media in config.media.types.items():
        for prefix in (media.reference_prefix.as_posix(), media.served_path_prefix):
            normalized_prefix = prefix.rstrip("/")
            pattern = re.compile(
                rf"{re.escape(normalized_prefix)}/"
                rf"(?P<identity>[^\s)\]\"'<>?#]+)"
            )
            for match in pattern.finditer(source):
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


def _location_adapters(
    repo_root: Path,
    config: DocsStageConfig | DocsCollectionConfig,
    *,
    client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> tuple[dict[str, ArtifactLocationAdapter], dict[str, ArtifactLocationAdapter]]:
    published_locations = [media.asset_location for media in config.media.types.values()]
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        published_locations,
        client=client,  # type: ignore[arg-type]
        env_files=env_files,
        environ=environ,
    )
    published = {
        media_type: artifact_location_adapter(
            repo_root,
            media.asset_location,
            served_path_prefix=media.served_path_prefix,
            remote_client=remote_client,
        )
        for media_type, media in config.media.types.items()
    }
    build_source = {
        build_type: artifact_location_adapter(
            repo_root,
            build.location,
        )
        for build_type, build in config.media.build_sources.items()
    }
    return published, build_source


def list_collection_media(
    repo_root: Path,
    config: DocsStageConfig | DocsCollectionConfig,
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[DocsMediaFile, ...]:
    """List configured ready media and build sources without reading or joining documents.

    Storage placeholders are omitted. Display exclusions and ordering belong to
    consumers; no source bodies, paths or credentials enter the returned records.
    """
    published_adapters, build_adapters = _location_adapters(
        repo_root,
        config,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    items: list[DocsMediaFile] = []
    for role, adapters in (("source", published_adapters), ("build-source", build_adapters)):
        for media_type, adapter in adapters.items():
            for artifact in adapter.list():
                if Path(artifact.identity).name == ".gitkeep":
                    continue
                # Preserve local confinement without issuing remote per-file metadata requests.
                local_path = local_artifact_path(repo_root, adapter.location, artifact.identity)
                if local_path is not None and not local_path.is_file():
                    raise FileNotFoundError("Docs media file disappeared during inventory")
                items.append(DocsMediaFile(
                    stage=config.stage,
                    collection=getattr(config, "collection", ""),
                    media_type=media_type,
                    identity=artifact.identity,
                    role=role,
                ))
    return tuple(items)


__all__ = [
    "DocsMediaFile",
    "DocsMediaReference",
    "list_collection_media",
    "source_media_references",
]
