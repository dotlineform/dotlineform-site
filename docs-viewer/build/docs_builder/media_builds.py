from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import Path
from typing import Callable, Iterable, Mapping

from docs_artifact_locations import (
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    normalize_artifact_identity,
)
from docs_mermaid_media import produce_mermaid_svg
from docs_media_inventory import source_media_references
from docs_scope_config import DocsScopeConfig, resolve_location_path

from .common import MEDIA_TOKEN_PATTERN


@dataclass(frozen=True)
class MediaBuildContext:
    scope: str
    build_type: str
    publishes_to: str
    source: ArtifactLocationAdapter
    generated: ArtifactLocationAdapter
    write: bool
    requested_generated_identities: tuple[str, ...] | None = None
    replace_existing: bool = True


MediaProducer = Callable[[MediaBuildContext], Iterable[str]]
REGISTERED_MEDIA_PRODUCERS: dict[str, MediaProducer] = {"mermaid": produce_mermaid_svg}
IGNORED_MEDIA_FILENAMES = frozenset({".DS_Store", ".gitkeep"})


def referenced_build_media_identities(
    config: DocsScopeConfig,
    markdown_sources: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    """Collect configured build-media outputs referenced by selected Markdown sources."""

    build_prefixes = {
        build_type: config.media.types[build.publishes_to].reference_prefix.as_posix().strip("/")
        for build_type, build in config.media.build_sources.items()
    }
    requested: dict[str, set[str]] = {build_type: set() for build_type in build_prefixes}
    for markdown in markdown_sources:
        for match in MEDIA_TOKEN_PATTERN.finditer(markdown):
            parts = match.group(1).strip().split()
            media_path = parts[0].lstrip("/") if parts else ""
            for build_type, prefix in build_prefixes.items():
                if not media_path.startswith(f"{prefix}/"):
                    continue
                identity = normalize_artifact_identity(media_path.removeprefix(f"{prefix}/"))
                requested[build_type].add(identity)
    return {
        build_type: tuple(sorted(identities))
        for build_type, identities in sorted(requested.items())
    }


def run_registered_media_builds(
    repo_root: Path,
    config: DocsScopeConfig,
    *,
    write: bool,
    producers: Mapping[str, MediaProducer] | None = None,
    client: object | None = None,
    requested_generated_identities: Mapping[str, Iterable[str]] | None = None,
    replace_existing: bool = True,
) -> list[dict[str, object]]:
    """Run explicitly configured media producers directly into generated locations."""

    if not config.media.build_sources:
        return []
    if requested_generated_identities is not None:
        unknown_build_types = sorted(
            set(requested_generated_identities) - set(config.media.build_sources)
        )
        if unknown_build_types:
            raise ValueError(
                "Requested Docs media outputs use unconfigured build types: "
                f"{', '.join(unknown_build_types)}"
            )
    available = producers if producers is not None else REGISTERED_MEDIA_PRODUCERS
    target_locations = [
        config.media.types[build.publishes_to].generated_location
        for build in config.media.build_sources.values()
    ]
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        target_locations,
        client=client,  # type: ignore[arg-type]
    )
    results: list[dict[str, object]] = []
    for build_type, build in sorted(config.media.build_sources.items()):
        producer = available.get(build.producer)
        if producer is None:
            raise RuntimeError(
                f"Docs media producer {build.producer!r} is not registered for {config.scope_id}/{build_type}"
            )
        generated_media = config.media.types[build.publishes_to]
        source = artifact_location_adapter(
            repo_root,
            build.location,
        )
        generated = artifact_location_adapter(
            repo_root,
            generated_media.generated_location,
            served_path_prefix=generated_media.served_path_prefix,
            remote_client=remote_client,
        )
        source_inventory = source.list()
        requested = (
            None
            if requested_generated_identities is None
            else tuple(
                sorted(
                    {
                        normalize_artifact_identity(identity)
                        for identity in requested_generated_identities.get(build_type, ())
                    }
                )
            )
        )
        output_identities = tuple(
            normalize_artifact_identity(identity)
            for identity in producer(
                MediaBuildContext(
                    scope=config.scope_id,
                    build_type=build_type,
                    publishes_to=build.publishes_to,
                    source=source,
                    generated=generated,
                    write=write,
                    requested_generated_identities=requested,
                    replace_existing=replace_existing,
                )
            )
        )
        if len(set(output_identities)) != len(output_identities):
            raise RuntimeError(
                f"Docs media producer {build.producer!r} returned duplicate published identities"
            )
        if write:
            missing = [identity for identity in output_identities if generated.stat(identity) is None]
            if missing:
                raise RuntimeError(
                    f"Docs media producer {build.producer!r} did not publish: {', '.join(missing)}"
                )
        results.append(
            {
                "build_type": build_type,
                "producer": build.producer,
                "publishes_to": build.publishes_to,
                "source_count": len(source_inventory),
                "output_identities": list(output_identities),
                "write": write,
            }
        )
    return results


def scope_markdown_sources(repo_root: Path, config: DocsScopeConfig) -> tuple[str, ...]:
    roots = [resolve_location_path(repo_root, config.source.location) / config.source.documents_path]
    roots.extend(
        resolve_location_path(repo_root, sub_scope.source.location) / sub_scope.source.documents_path
        for sub_scope in config.sub_scopes
    )
    sources: list[str] = []
    for root in roots:
        sources.extend(path.read_text(encoding="utf-8") for path in sorted(root.glob("*.md")))
    return tuple(sources)


def referenced_media_identities(
    config: DocsScopeConfig,
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


def build_scope_media_snapshot(
    repo_root: Path,
    config: DocsScopeConfig,
    *,
    write: bool,
    producers: Mapping[str, MediaProducer] | None = None,
) -> dict[str, object]:
    """Reconcile the exact referenced source-media set into generated output."""

    markdown_sources = scope_markdown_sources(repo_root, config)
    referenced = referenced_media_identities(config, markdown_sources)
    requested_builds = referenced_build_media_identities(config, markdown_sources)
    producer_builds = run_registered_media_builds(
        repo_root,
        config,
        write=write,
        producers=producers,
        requested_generated_identities=requested_builds,
    )
    produced_by_type: dict[str, set[str]] = {media_type: set() for media_type in config.media.types}
    for result in producer_builds:
        output_type = str(result["publishes_to"])
        produced_by_type[output_type].update(
            normalize_artifact_identity(identity)
            for identity in result["output_identities"]  # type: ignore[union-attr]
        )

    type_results: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    for media_type, media in sorted(config.media.types.items()):
        source = artifact_location_adapter(repo_root, media.source_location)
        generated = artifact_location_adapter(
            repo_root,
            media.generated_location,
            served_path_prefix=media.served_path_prefix,
        )
        produced = produced_by_type[media_type]
        expected: dict[str, bytes | None] = {}
        for identity in referenced[media_type]:
            source_stat = source.stat(identity)
            if identity in produced:
                if source_stat is not None:
                    raise RuntimeError(
                        f"Docs media {config.scope_id}/{media_type}/{identity} has both direct and producer source authority"
                    )
                expected[identity] = None
                continue
            if source_stat is None:
                missing.append(f"docs/{config.scope_id}/{media_type}/{identity}")
                continue
            expected[identity] = source.read(identity)

        existing = {
            item.identity
            for item in generated.list()
            if Path(item.identity).name not in IGNORED_MEDIA_FILENAMES
        }
        stale = sorted(existing - set(expected))
        changed: list[str] = []
        unchanged: list[str] = []
        for identity, data in sorted(expected.items()):
            if data is None:
                if write and generated.stat(identity) is None:
                    raise RuntimeError(
                        f"Docs media producer did not generate {config.scope_id}/{media_type}/{identity}"
                    )
                unchanged.append(identity)
                continue
            if generated.stat(identity) is not None and generated.verify_bytes(identity, data):
                unchanged.append(identity)
                continue
            changed.append(identity)
            if write:
                generated.replace(
                    identity,
                    data,
                    content_type=mimetypes.guess_type(identity)[0] or "application/octet-stream",
                )
                if not generated.verify_bytes(identity, data):
                    raise RuntimeError(
                        f"Docs generated media did not verify: {config.scope_id}/{media_type}/{identity}"
                    )
        if write:
            for identity in stale:
                generated.delete(identity)
        type_results[media_type] = {
            "referenced": len(referenced[media_type]),
            "generated": len(expected),
            "changed": changed,
            "unchanged": unchanged,
            "removed": stale,
        }

    return {
        "scope": config.scope_id,
        "write": write,
        "source_documents": len(markdown_sources),
        "missing_references": sorted(missing),
        "types": type_results,
        "producer_builds": producer_builds,
    }


__all__ = [
    "MediaBuildContext",
    "MediaProducer",
    "REGISTERED_MEDIA_PRODUCERS",
    "build_scope_media_snapshot",
    "referenced_media_identities",
    "referenced_build_media_identities",
    "run_registered_media_builds",
    "scope_markdown_sources",
]
