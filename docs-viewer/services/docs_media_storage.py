#!/usr/bin/env python3
"""Scope-aware Docs Viewer media placement and publication."""

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
from docs_scope_config import (
    PUBLISHED_MEDIA_TYPES,
    DocsPublishedMediaConfig,
    DocsScopeConfig,
    load_docs_scope_configs,
    published_media_config,
    resolve_location_path,
)
from services.paths import configured_workspace_paths
from studio.services.media.publish_media_to_r2 import content_type_for, file_md5


DOCS_MEDIA_CLASSES = set(PUBLISHED_MEDIA_TYPES)
DOCS_MEDIA_ROUTE_CLASSES = {"files", "img", "svg"}
DOCS_MEDIA_ROUTE_PREFIX = "/docs/media/"
SUCCESSFUL_UPLOAD_STATUSES = {"unchanged", "uploaded", "overwritten"}


@dataclass(frozen=True)
class DocsMediaFile:
    scope: str
    media_class: str
    filename: str
    local_path: Path
    source_root: Path
    size: int
    md5: str


@dataclass(frozen=True)
class DocsMediaPublishResult:
    scope: str
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
    config: DocsScopeConfig,
    *,
    media_class: str,
    local_path: Path,
    source_root: Path,
    filename: str | None = None,
) -> DocsMediaFile:
    normalized_class = validate_media_class(media_class)
    published_media_config(config, normalized_class)
    normalized_filename = validate_media_filename(filename or local_path.name)
    resolved_root = source_root.resolve()
    resolved_path = local_path.resolve()
    if not resolved_path.is_file() or not resolved_path.is_relative_to(resolved_root):
        raise ValueError(f"Docs media source {normalized_filename!r} is outside its allowlisted root")
    if resolved_path.name != normalized_filename:
        raise ValueError("Docs media source filename does not match the planned filename")
    return DocsMediaFile(
        scope=config.scope_id,
        media_class=normalized_class,
        filename=normalized_filename,
        local_path=resolved_path,
        source_root=resolved_root,
        size=resolved_path.stat().st_size,
        md5=file_md5(resolved_path),
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
        scope=item.scope,
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
    identities = [(item.scope, item.media_class, item.filename) for item in files]
    if len(set(identities)) != len(identities):
        raise ValueError("Docs media publication contains duplicate scope/class/filename identities")
    for media_class in {item.media_class for item in files}:
        adapter = adapters.get(media_class)
        if adapter is None:
            raise ValueError(f"Docs media role {media_class!r} has no location adapter")
        adapter.require(
            WRITE_CAPABILITY,
            REPLACE_CAPABILITY,
            STAT_CAPABILITY,
            VERIFY_BYTES_CAPABILITY,
            role=f"published.media.{media_class}",
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


def media_adapters_for_scope(
    repo_root: Path,
    config: DocsScopeConfig,
    media_classes: Iterable[str],
    *,
    remote_client: object | None = None,
) -> dict[str, ArtifactLocationAdapter]:
    adapters: dict[str, ArtifactLocationAdapter] = {}
    for media_class in sorted(set(media_classes)):
        media = published_media_config(config, media_class)
        adapters[media_class] = artifact_location_adapter(
            repo_root,
            media.location,
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
    scope_ids = {item.scope for item in files}
    if len(scope_ids) != 1:
        raise ValueError("One Docs media publication may target only one exact scope")
    scope = next(iter(scope_ids))
    config = load_docs_scope_configs(repo_root).get(scope)
    if config is None:
        raise ValueError(f"Unknown Docs media scope: {scope!r}")

    media_classes = {item.media_class for item in files}
    locations = [published_media_config(config, media_class).location for media_class in media_classes]
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        locations,
        client=client,  # type: ignore[arg-type]
        env_files=env_files,
        environ=environ,
    )
    adapters = media_adapters_for_scope(
        repo_root,
        config,
        media_classes,
        remote_client=remote_client,
    )
    return plan_and_publish_docs_media(files, adapters=adapters, write=write, force=force)


def docs_publish_succeeded(results: Sequence[DocsMediaPublishResult]) -> bool:
    return bool(results) and all(result.status in SUCCESSFUL_UPLOAD_STATUSES for result in results)


def docs_publish_report(
    *,
    scope: str,
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
        "docs_scope": scope,
        "action": "publish",
        "mode": "write" if write else "dry-run",
        "force": force,
        "counts": dict(sorted(counts.items())),
        "objects": [asdict(result) for result in results],
    }


def run_docs_staged_media_publish(
    repo_root: Path,
    *,
    scope: str,
    media_class: str,
    staged_filename: str,
    write: bool,
    force: bool,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    normalized_filename = validate_media_filename(staged_filename)
    configs = load_docs_scope_configs(repo_root)
    config = configs.get(str(scope or "").strip().lower())
    if config is None:
        raise ValueError(f"Unknown Docs media scope: {scope!r}")
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
    return docs_publish_report(scope=config.scope_id, results=results, write=write, force=force)


def local_media_config(config: DocsScopeConfig, media_class: str) -> DocsPublishedMediaConfig:
    media = published_media_config(config, validate_media_class(media_class))
    if media.location.provider not in {REPOSITORY_PROVIDER, EXTERNAL_LOCAL_PROVIDER}:
        raise ValueError(
            f"Docs scope {config.scope_id!r} media role {media_class!r} is not locally served"
        )
    return media


def ensure_configured_scope_owned_media_directories(
    repo_root: Path,
    configs: Mapping[str, DocsScopeConfig] | None = None,
) -> dict[str, tuple[Path, ...]]:
    configured_scopes = configs if configs is not None else load_docs_scope_configs(repo_root)
    materialized: dict[str, tuple[Path, ...]] = {}
    for scope_id, config in configured_scopes.items():
        directories: list[Path] = []
        for media in config.published.media.values():
            if media.location.provider not in {REPOSITORY_PROVIDER, EXTERNAL_LOCAL_PROVIDER}:
                continue
            media_root = resolve_location_path(repo_root, media.location)
            unresolved_root = (
                repo_root.resolve() / media.location.path
                if media.location.provider == REPOSITORY_PROVIDER
                else media.location.path
            )
            if unresolved_root.is_symlink():
                raise ValueError(f"Configured Docs media directory must not be a symlink: {unresolved_root}")
            if unresolved_root.exists() and not unresolved_root.is_dir():
                raise NotADirectoryError(f"Configured Docs media directory is not a directory: {unresolved_root}")
            media_root.mkdir(parents=True, exist_ok=True)
            if media.location.provider == REPOSITORY_PROVIDER:
                marker = media_root / ".gitkeep"
                if marker.is_symlink() or (marker.exists() and not marker.is_file()):
                    raise ValueError(f"Configured Docs media marker must be a regular file: {marker}")
                if not any(media_root.iterdir()):
                    marker.touch()
            directories.append(media_root)
        if directories:
            materialized[scope_id] = tuple(sorted(directories))
    return materialized


def local_media_route(scope: str, media_class: str, filename: str) -> str:
    normalized_scope = str(scope or "").strip().lower()
    if not normalized_scope or "/" in normalized_scope or "\\" in normalized_scope:
        raise ValueError("Docs media scope must be one safe scope id")
    return (
        f"{DOCS_MEDIA_ROUTE_PREFIX}{normalized_scope}/"
        f"{validate_route_media_class(media_class)}/{validate_media_filename(filename)}"
    )


def local_media_path_from_route(repo_root: Path, request_path: str) -> tuple[Path, str]:
    if not request_path.startswith(DOCS_MEDIA_ROUTE_PREFIX):
        raise ValueError("Invalid Docs media route")
    parts = request_path.removeprefix(DOCS_MEDIA_ROUTE_PREFIX).split("/")
    if len(parts) != 3:
        raise ValueError("Invalid Docs media route")
    scope, media_class, filename = parts
    normalized_class = validate_route_media_class(media_class)
    normalized_filename = validate_media_filename(filename)
    config = load_docs_scope_configs(repo_root).get(scope)
    if config is None:
        raise FileNotFoundError(f"Docs media scope not found: {scope!r}")
    media = local_media_config(config, normalized_class)
    adapter = artifact_location_adapter(repo_root, media.location, served_path_prefix=media.served_path_prefix)
    path = adapter.resolve(normalized_filename)  # type: ignore[attr-defined]
    if not path.is_file():
        raise FileNotFoundError(f"Docs media file not found: {scope}/{normalized_class}/{normalized_filename}")
    return path, normalized_class


def safe_content_type(path: Path) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if content_type in {"text/html", "application/xhtml+xml"}:
        raise ValueError("HTML media is not served through the ordinary Docs media route")
    return content_type


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
    "ensure_configured_scope_owned_media_directories",
    "local_media_config",
    "local_media_path_from_route",
    "local_media_route",
    "media_adapters_for_scope",
    "plan_and_publish_docs_media",
    "publish_docs_media_files",
    "run_docs_staged_media_publish",
    "safe_content_type",
]
