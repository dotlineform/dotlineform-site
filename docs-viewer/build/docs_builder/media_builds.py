from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

from docs_artifact_locations import (
    ArtifactLocation,
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    normalize_artifact_identity,
)
from docs_mermaid_media import produce_mermaid_svg
from docs_scope_config import DocsScopeConfig

from .common import MEDIA_TOKEN_PATTERN


@dataclass(frozen=True)
class MediaBuildContext:
    scope: str
    build_type: str
    publishes_to: str
    source: ArtifactLocationAdapter
    published: ArtifactLocationAdapter
    write: bool
    requested_published_identities: tuple[str, ...] | None = None


MediaProducer = Callable[[MediaBuildContext], Iterable[str]]
REGISTERED_MEDIA_PRODUCERS: dict[str, MediaProducer] = {"mermaid": produce_mermaid_svg}


def referenced_build_media_identities(
    config: DocsScopeConfig,
    markdown_sources: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    """Collect configured build-media outputs referenced by selected Markdown sources."""

    build_prefixes = {
        build_type: config.published.media[build.publishes_to].reference_prefix.as_posix().strip("/")
        for build_type, build in config.source.build_media.items()
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
    requested_published_identities: Mapping[str, Iterable[str]] | None = None,
) -> list[dict[str, object]]:
    """Run explicitly configured media producers directly into published locations."""

    if not config.source.build_media:
        return []
    if requested_published_identities is not None:
        unknown_build_types = sorted(
            set(requested_published_identities) - set(config.source.build_media)
        )
        if unknown_build_types:
            raise ValueError(
                "Requested Docs media outputs use unconfigured build types: "
                f"{', '.join(unknown_build_types)}"
            )
    available = producers if producers is not None else REGISTERED_MEDIA_PRODUCERS
    target_locations = [
        config.published.media[build.publishes_to].location
        for build in config.source.build_media.values()
    ]
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        target_locations,
        client=client,  # type: ignore[arg-type]
    )
    results: list[dict[str, object]] = []
    for build_type, build in sorted(config.source.build_media.items()):
        producer = available.get(build.producer)
        if producer is None:
            raise RuntimeError(
                f"Docs media producer {build.producer!r} is not registered for {config.scope_id}/{build_type}"
            )
        published_media = config.published.media[build.publishes_to]
        source = artifact_location_adapter(
            repo_root,
            ArtifactLocation(
                provider=config.source.location.provider,
                path=config.source.location.path / build.path,
            ),
        )
        published = artifact_location_adapter(
            repo_root,
            published_media.location,
            served_path_prefix=published_media.served_path_prefix,
            remote_client=remote_client,
        )
        source_inventory = source.list()
        requested = (
            None
            if requested_published_identities is None
            else tuple(
                sorted(
                    {
                        normalize_artifact_identity(identity)
                        for identity in requested_published_identities.get(build_type, ())
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
                    published=published,
                    write=write,
                    requested_published_identities=requested,
                )
            )
        )
        if len(set(output_identities)) != len(output_identities):
            raise RuntimeError(
                f"Docs media producer {build.producer!r} returned duplicate published identities"
            )
        if write:
            missing = [identity for identity in output_identities if published.stat(identity) is None]
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


__all__ = [
    "MediaBuildContext",
    "MediaProducer",
    "REGISTERED_MEDIA_PRODUCERS",
    "referenced_build_media_identities",
    "run_registered_media_builds",
]
