#!/usr/bin/env python3
"""Provider-independent inventory of registered Docs Viewer media roles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Iterable, Mapping

from docs_artifact_locations import (
    ArtifactLocation,
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
)
from docs_scope_config import DocsScopeConfig, resolve_location_path


MEDIA_REFERENCE_PATTERN = re.compile(r"\[\[(?:media|html-media):(?P<path>[^\]\s]+)(?:[^\]]*)\]\]")
DOC_ID_PATTERN = re.compile(r"(?m)^doc_id:\s*[\"']?(?P<doc_id>[^\"'\s]+)")


@dataclass(frozen=True)
class DocsMediaReference:
    doc_id: str
    media_type: str
    identity: str
    logical_path: str


@dataclass(frozen=True)
class DocsMediaInventoryItem:
    scope: str
    media_type: str
    identity: str
    role: str
    provider: str
    size: int
    etag: str
    served_path: str
    producer: str
    publishes_to: str
    document_ids: tuple[str, ...]


@dataclass(frozen=True)
class DocsMediaInventory:
    scope: str
    items: tuple[DocsMediaInventoryItem, ...]
    missing_references: tuple[DocsMediaReference, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "items": [asdict(item) for item in self.items],
            "missing_references": [asdict(reference) for reference in self.missing_references],
        }


def document_media_references(repo_root: Path, config: DocsScopeConfig) -> tuple[DocsMediaReference, ...]:
    source_root = resolve_location_path(repo_root, config.source.location)
    documents_root = source_root / config.source.documents_path
    references: list[DocsMediaReference] = []
    for path in sorted(documents_root.glob("*.md")):
        source = path.read_text(encoding="utf-8")
        doc_match = DOC_ID_PATTERN.search(source)
        doc_id = doc_match.group("doc_id") if doc_match else path.stem
        found: set[tuple[str, str, str]] = set()
        for match in MEDIA_REFERENCE_PATTERN.finditer(source):
            logical_path = match.group("path").lstrip("/")
            parts = Path(logical_path).parts
            if len(parts) < 4 or parts[:2] != ("docs", config.scope_id):
                continue
            media_type = parts[2]
            if media_type not in config.published.media:
                continue
            found.add((media_type, Path(*parts[3:]).as_posix(), logical_path))
        for media_type, media in config.published.media.items():
            for prefix in (media.reference_prefix.as_posix(), media.served_path_prefix):
                normalized_prefix = prefix.rstrip("/")
                pattern = re.compile(rf"{re.escape(normalized_prefix)}/(?P<identity>[^\s)\]\"'<>]+)")
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
        references.extend(
            DocsMediaReference(
                doc_id=doc_id,
                media_type=media_type,
                identity=identity,
                logical_path=logical_path,
            )
            for media_type, identity, logical_path in sorted(found)
        )
    return tuple(references)


def _location_adapters(
    repo_root: Path,
    config: DocsScopeConfig,
    *,
    client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> tuple[dict[str, ArtifactLocationAdapter], dict[str, ArtifactLocationAdapter]]:
    published_locations = [media.location for media in config.published.media.values()]
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
            media.location,
            served_path_prefix=media.served_path_prefix,
            remote_client=remote_client,
        )
        for media_type, media in config.published.media.items()
    }
    build_source = {
        build_type: artifact_location_adapter(
            repo_root,
            ArtifactLocation(
                provider=config.source.location.provider,
                path=config.source.location.path / build.path,
            ),
        )
        for build_type, build in config.source.build_media.items()
    }
    return published, build_source


def inventory_scope_media(
    repo_root: Path,
    config: DocsScopeConfig,
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> DocsMediaInventory:
    """List every owned object and associate, but do not require, document references."""

    references = document_media_references(repo_root, config)
    references_by_identity: dict[tuple[str, str], set[str]] = {}
    for reference in references:
        references_by_identity.setdefault((reference.media_type, reference.identity), set()).add(reference.doc_id)
    published_adapters, build_adapters = _location_adapters(
        repo_root,
        config,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    items: list[DocsMediaInventoryItem] = []
    published_identities: set[tuple[str, str]] = set()
    for media_type, adapter in sorted(published_adapters.items()):
        media = config.published.media[media_type]
        for artifact in adapter.list():
            if Path(artifact.identity).name == ".gitkeep":
                continue
            published_identities.add((media_type, artifact.identity))
            items.append(
                DocsMediaInventoryItem(
                    scope=config.scope_id,
                    media_type=media_type,
                    identity=artifact.identity,
                    role="published",
                    provider=media.location.provider,
                    size=artifact.size,
                    etag=artifact.etag,
                    served_path=adapter.served_reference(artifact.identity),
                    producer="",
                    publishes_to="",
                    document_ids=tuple(sorted(references_by_identity.get((media_type, artifact.identity), set()))),
                )
            )
    for build_type, adapter in sorted(build_adapters.items()):
        build = config.source.build_media[build_type]
        for artifact in adapter.list():
            if Path(artifact.identity).name == ".gitkeep":
                continue
            items.append(
                DocsMediaInventoryItem(
                    scope=config.scope_id,
                    media_type=build_type,
                    identity=artifact.identity,
                    role="source",
                    provider=config.source.location.provider,
                    size=artifact.size,
                    etag=artifact.etag,
                    served_path="",
                    producer=build.producer,
                    publishes_to=build.publishes_to,
                    document_ids=(),
                )
            )
    missing = tuple(
        reference
        for reference in references
        if (reference.media_type, reference.identity) not in published_identities
    )
    return DocsMediaInventory(
        scope=config.scope_id,
        items=tuple(sorted(items, key=lambda item: (item.role, item.media_type, item.identity))),
        missing_references=missing,
    )


__all__ = [
    "DocsMediaInventory",
    "DocsMediaInventoryItem",
    "DocsMediaReference",
    "document_media_references",
    "inventory_scope_media",
]
