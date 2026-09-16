#!/usr/bin/env python3
"""Stage-aware Docs Viewer media placement and publication."""

from __future__ import annotations

import datetime as dt
import mimetypes
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from docs_artifact_locations import (
    EXTERNAL_LOCAL_PROVIDER,
    REPOSITORY_PROVIDER,
    REPLACE_CAPABILITY,
    STAT_CAPABILITY,
    VERIFY_BYTES_CAPABILITY,
    WRITE_CAPABILITY,
    ArtifactLocationAdapter,
    ArtifactStat,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
)
from docs_workspace_config import (
    MANAGED_MEDIA_TYPES,
    DocsManagedMediaConfig,
    DocsStageConfig,
    DocsCollectionConfig,
    normalize_collection_id,
    load_docs_media_owner,
    managed_media_config,
    require_document_authoring,
)
from docs_document_packages.workspace import configured_workspace_paths
from studio.services.media.publish_media_to_r2 import content_type_for, file_md5


DOCS_MEDIA_CLASSES = set(MANAGED_MEDIA_TYPES)
DOCS_MEDIA_ROUTE_CLASSES = set(MANAGED_MEDIA_TYPES)
DOCS_MEDIA_ROUTE_PREFIX = "/docs/media/"
SUCCESSFUL_UPLOAD_STATUSES = {"unchanged", "uploaded", "overwritten"}


@dataclass(frozen=True)
class DocsMediaFile:
    stage: str
    collection: str
    media_class: str
    filename: str
    local_path: Path
    source_root: Path
    size: int
    md5: str


@dataclass(frozen=True)
class DocsMediaPublishResult:
    stage: str
    collection: str
    media_class: str
    filename: str
    size: int
    status: str
    reason: str = ""


def validate_media_class(value: str) -> str:
    media_class = str(value or "").strip().lower()
    if media_class not in DOCS_MEDIA_CLASSES:
        supported = ", ".join(sorted(DOCS_MEDIA_CLASSES))
        raise ValueError(f"Docs media class must be one of: {supported}")
    return media_class


def validate_route_media_class(value: str) -> str:
    media_class = str(value or "").strip().lower()
    if media_class not in DOCS_MEDIA_ROUTE_CLASSES:
        supported = ", ".join(sorted(DOCS_MEDIA_ROUTE_CLASSES))
        raise ValueError(f"Docs media route class must be one of: {supported}")
    return media_class


def validate_media_filename(value: str) -> str:
    filename = str(value or "").strip()
    if (
        not filename
        or Path(filename).name != filename
        or filename in {".", ".."}
        or "\x00" in filename
        or any(ord(character) < 32 or ord(character) == 127 for character in filename)
    ):
        raise ValueError("Docs media filename must be one safe filename")
    return filename


def docs_media_file(
    config: DocsStageConfig | DocsCollectionConfig,
    *,
    media_class: str,
    local_path: Path,
    source_root: Path,
    filename: str | None = None,
) -> DocsMediaFile:
    normalized_class = validate_media_class(media_class)
    managed_media_config(config, normalized_class)
    normalized_filename = validate_media_filename(filename or local_path.name)
    resolved_root = source_root.resolve()
    resolved_path = local_path.resolve()
    if not resolved_path.is_file() or not resolved_path.is_relative_to(resolved_root):
        raise ValueError(f"Docs media source {normalized_filename!r} is outside its allowlisted root")
    if resolved_path.name != normalized_filename:
        raise ValueError("Docs media source filename does not match the planned filename")
    return DocsMediaFile(
        media_class=normalized_class,
        filename=normalized_filename,
        local_path=resolved_path,
        source_root=resolved_root,
        size=resolved_path.stat().st_size,
        md5=file_md5(resolved_path),
        stage=config.stage,
        collection=getattr(config, "collection", ""),
    )


def artifact_matches(item: DocsMediaFile, stat: ArtifactStat, adapter: ArtifactLocationAdapter) -> bool:
    if stat.size != item.size:
        return False
    etag = stat.etag.strip().strip('"').lower()
    if etag and "-" not in etag:
        return etag == item.md5
    return adapter.verify_bytes(item.filename, item.local_path.read_bytes())


def _result(item: DocsMediaFile, status: str, reason: str = "") -> DocsMediaPublishResult:
    return DocsMediaPublishResult(
        stage=item.stage,
        collection=item.collection,
        media_class=item.media_class,
        filename=item.filename,
        size=item.size,
        status=status,
        reason=reason,
    )


def plan_and_publish_docs_media(
    files: Sequence[DocsMediaFile],
    *,
    adapters: Mapping[str, ArtifactLocationAdapter],
    write: bool,
    force: bool,
) -> list[DocsMediaPublishResult]:
    """Preflight a complete logical media set, then publish through location adapters."""

    if not files:
        return []
    identities = [(item.stage, item.collection, item.media_class, item.filename) for item in files]
    if len(set(identities)) != len(identities):
        raise ValueError("Docs media publication contains duplicate stage/collection/class/filename identities")
    for media_class in {item.media_class for item in files}:
        adapter = adapters.get(media_class)
        if adapter is None:
            raise ValueError(f"Docs media role {media_class!r} has no location adapter")
        adapter.require(
            WRITE_CAPABILITY,
            REPLACE_CAPABILITY,
            STAT_CAPABILITY,
            VERIFY_BYTES_CAPABILITY,
            role=f"media.types.{media_class}",
        )

    checked: list[tuple[DocsMediaFile, ArtifactStat | None, str]] = []
    preflight_failed = False
    for item in files:
        adapter = adapters[item.media_class]
        try:
            existing = adapter.stat(item.filename)
            matches = existing is not None and artifact_matches(item, existing, adapter)
        except Exception:  # pragma: no cover - defensive provider boundary
            checked.append((item, None, "failed"))
            preflight_failed = True
            continue
        if matches:
            checked.append((item, existing, "unchanged"))
        elif existing is not None and not force:
            checked.append((item, existing, "blocked_changed"))
            preflight_failed = True
        else:
            checked.append((item, existing, "ready"))

    if preflight_failed:
        results: list[DocsMediaPublishResult] = []
        for item, _existing, status in checked:
            if status == "failed":
                results.append(_result(item, status, "artifact comparison failed"))
            elif status == "blocked_changed":
                results.append(_result(item, status, "published bytes differ; use a new filename or an explicit force"))
            elif status == "unchanged":
                results.append(_result(item, status, "published bytes already match"))
            else:
                results.append(_result(item, "not_attempted", "complete-set preflight did not pass"))
        return results

    if not write:
        return [
            _result(
                item,
                "unchanged" if status == "unchanged" else "would_overwrite" if existing is not None else "would_upload",
                "published bytes already match" if status == "unchanged" else "dry-run",
            )
            for item, existing, status in checked
        ]

    results: list[DocsMediaPublishResult] = []
    write_failed = False
    for item, existing, status in checked:
        if status == "unchanged":
            results.append(_result(item, "unchanged", "published bytes already match"))
            continue
        if write_failed:
            results.append(_result(item, "not_attempted", "stopped after a publication failure"))
            continue
        adapter = adapters[item.media_class]
        try:
            data = item.local_path.read_bytes()
            adapter.replace(item.filename, data, content_type=content_type_for(item.local_path))
            if not adapter.verify_bytes(item.filename, data):
                raise RuntimeError("published bytes did not verify")
        except Exception:  # pragma: no cover - defensive provider boundary
            results.append(_result(item, "failed", "artifact publication failed"))
            write_failed = True
            continue
        results.append(_result(item, "overwritten" if existing is not None else "uploaded"))
    return results


def media_adapters_for_collection(
    repo_root: Path,
    config: DocsStageConfig | DocsCollectionConfig,
    media_classes: Iterable[str],
    *,
    remote_client: object | None = None,
) -> dict[str, ArtifactLocationAdapter]:
    adapters: dict[str, ArtifactLocationAdapter] = {}
    for media_class in sorted(set(media_classes)):
        media = managed_media_config(config, media_class)
        adapters[media_class] = artifact_location_adapter(
            repo_root,
            media.source_location,
            served_path_prefix=media.served_path_prefix,
            remote_client=remote_client,  # type: ignore[arg-type]
        )
    return adapters


def publish_docs_media_files(
    repo_root: Path,
    files: Sequence[DocsMediaFile],
    *,
    write: bool,
    force: bool = False,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[DocsMediaPublishResult]:
    if not files:
        return []
    targets = {(item.stage, item.collection) for item in files}
    if len(targets) != 1:
        raise ValueError("One Docs media insertion may target only one exact collection")
    stage, collection = next(iter(targets))
    config = load_docs_media_owner(repo_root, stage, collection=collection)
    require_document_authoring(config)

    media_classes = {item.media_class for item in files}
    locations = [managed_media_config(config, media_class).source_location for media_class in media_classes]
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        locations,
        client=client,  # type: ignore[arg-type]
        env_files=env_files,
        environ=environ,
    )
    adapters = media_adapters_for_collection(
        repo_root,
        config,
        media_classes,
        remote_client=remote_client,
    )
    results = plan_and_publish_docs_media(files, adapters=adapters, write=write, force=force)
    if write and docs_publish_succeeded(results):
        for item in files:
            media = managed_media_config(config, item.media_class)
            generated = artifact_location_adapter(repo_root, media.generated_location)
            data = adapters[item.media_class].read(item.filename)
            generated.replace(item.filename, data, content_type=safe_content_type(item.local_path))
            if not generated.verify_bytes(item.filename, data):
                raise RuntimeError("Generated media verification failed after source insertion")
    return results


def docs_publish_succeeded(results: Sequence[DocsMediaPublishResult]) -> bool:
    return bool(results) and all(result.status in SUCCESSFUL_UPLOAD_STATUSES for result in results)


def docs_publish_report(
    *,
    stage: str,
    collection: str = "",
    results: Sequence[DocsMediaPublishResult],
    write: bool,
    force: bool,
) -> dict[str, object]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": "docs",
        "stage": stage,
        "collection": collection,
        "action": "publish",
        "mode": "write" if write else "dry-run",
        "force": force,
        "counts": dict(sorted(counts.items())),
        "objects": [asdict(result) for result in results],
    }


def run_docs_staged_media_publish(
    repo_root: Path,
    *,
    stage: str,
    collection: str = "",
    media_class: str,
    staged_filename: str,
    write: bool,
    force: bool,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    normalized_filename = validate_media_filename(staged_filename)
    config = load_docs_media_owner(repo_root, stage, collection=collection)
    workspace = configured_workspace_paths(repo_root)
    source_path = (workspace.import_staging / normalized_filename).resolve()
    item = docs_media_file(
        config,
        media_class=media_class,
        local_path=source_path,
        source_root=workspace.import_staging,
        filename=normalized_filename,
    )
    results = publish_docs_media_files(
        repo_root,
        [item],
        write=write,
        force=force,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    return docs_publish_report(stage=config.stage, collection=collection, results=results, write=write, force=force)


def local_media_config(config: DocsStageConfig | DocsCollectionConfig, media_class: str) -> DocsManagedMediaConfig:
    media = managed_media_config(config, validate_media_class(media_class))
    if media.generated_location.provider not in {REPOSITORY_PROVIDER, EXTERNAL_LOCAL_PROVIDER}:
        raise ValueError(
            f"Docs stage {config.stage!r} media role {media_class!r} is not locally served"
        )
    return media


def local_media_route(stage: str, media_class: str, filename: str, *, collection: str = "") -> str:
    if stage not in {"working", "pre-publish"}:
        raise ValueError("Docs media route requires an explicit stage")
    child = f"collections/{normalize_collection_id(collection, field='collection')}/" if collection else ""
    return f"{DOCS_MEDIA_ROUTE_PREFIX}{stage}/{child}{validate_route_media_class(media_class)}/{validate_media_filename(filename)}"


def local_media_path_from_route(repo_root: Path, request_path: str) -> tuple[Path, str]:
    if not request_path.startswith(DOCS_MEDIA_ROUTE_PREFIX):
        raise ValueError("Invalid Docs media route")
    parts = request_path.removeprefix(DOCS_MEDIA_ROUTE_PREFIX).split("/")
    stage = parts.pop(0) if parts else None
    collection = ""
    if parts and parts[0] == "collections":
        if len(parts) != 4:
            raise ValueError("Invalid Docs child media route")
        _, collection, *parts = parts
    if len(parts) != 2:
        raise ValueError("Invalid Docs media route")
    media_class, filename = parts
    normalized_class = validate_route_media_class(media_class)
    normalized_filename = validate_media_filename(filename)
    config = load_docs_media_owner(repo_root, stage, collection=collection)
    media = local_media_config(config, normalized_class)
    adapter = artifact_location_adapter(repo_root, media.generated_location, served_path_prefix=media.served_path_prefix)
    path = adapter.resolve(normalized_filename)  # type: ignore[attr-defined]
    if not path.is_file():
        raise FileNotFoundError(f"Docs media file not found: {stage}/{normalized_class}/{normalized_filename}")
    return path, normalized_class


def safe_content_type(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


__all__ = [
    "DOCS_MEDIA_CLASSES",
    "DOCS_MEDIA_ROUTE_PREFIX",
    "DOCS_MEDIA_ROUTE_CLASSES",
    "DocsMediaFile",
    "DocsMediaPublishResult",
    "artifact_matches",
    "docs_media_file",
    "docs_publish_report",
    "docs_publish_succeeded",
    "local_media_config",
    "local_media_path_from_route",
    "local_media_route",
    "media_adapters_for_collection",
    "plan_and_publish_docs_media",
    "publish_docs_media_files",
    "run_docs_staged_media_publish",
    "safe_content_type",
]
