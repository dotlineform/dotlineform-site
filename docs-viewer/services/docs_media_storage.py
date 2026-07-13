#!/usr/bin/env python3
"""Scope-aware Docs Viewer media storage and R2 publication."""

from __future__ import annotations

import datetime as dt
import mimetypes
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Protocol, Sequence

from docs_scope_config import (
    LOCAL_EXTERNAL_SCOPE_TYPE,
    DocsScopeConfig,
    load_docs_scope_configs,
    resolve_external_data_root,
)
from services.paths import configured_workspace_paths
from studio.services.media.publish_media_to_r2 import (
    DEFAULT_ENV_FILES,
    R2Client,
    RemoteObject,
    content_type_for,
    file_md5,
    load_r2_credentials,
)


DOCS_MEDIA_CLASSES = {"files", "img"}
DOCS_MEDIA_ROUTE_PREFIX = "/docs/media/"
SUCCESSFUL_UPLOAD_STATUSES = {"unchanged", "uploaded", "overwritten"}


class DocsRemoteClient(Protocol):
    def head_object(self, key: str) -> RemoteObject | None:
        ...

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        ...


@dataclass(frozen=True)
class DocsMediaFile:
    scope: str
    media_class: str
    filename: str
    local_path: Path
    source_root: Path
    object_key: str
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


def docs_media_object_key(config: DocsScopeConfig, media_class: str, filename: str) -> str:
    normalized_class = validate_media_class(media_class)
    normalized_filename = validate_media_filename(filename)
    prefix = config.media_path_prefix.as_posix().strip("/")
    expected_prefix = f"docs/{config.scope_id}"
    if prefix != expected_prefix:
        raise ValueError(
            f"R2 Docs media scope {config.scope_id!r} must use media_path_prefix {expected_prefix!r}"
        )
    return f"{prefix}/{normalized_class}/{normalized_filename}"


def docs_media_file(
    config: DocsScopeConfig,
    *,
    media_class: str,
    local_path: Path,
    source_root: Path,
    filename: str | None = None,
) -> DocsMediaFile:
    normalized_class = validate_media_class(media_class)
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
        object_key=docs_media_object_key(config, normalized_class, normalized_filename),
        size=resolved_path.stat().st_size,
        md5=file_md5(resolved_path),
    )


def remote_matches(item: DocsMediaFile, remote: RemoteObject) -> bool:
    etag = remote.etag.strip().strip('"').lower()
    return remote.size == item.size and etag == item.md5


def _result(
    item: DocsMediaFile,
    status: str,
    reason: str = "",
) -> DocsMediaPublishResult:
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
    client: DocsRemoteClient,
    write: bool,
    force: bool,
) -> list[DocsMediaPublishResult]:
    """Preflight a complete Docs media set, then publish it without exposing remote keys."""

    if not files:
        return []
    identities = [(item.scope, item.media_class, item.filename) for item in files]
    if len(set(identities)) != len(identities):
        raise ValueError("Docs media publication contains duplicate scope/class/filename identities")

    checked: list[tuple[DocsMediaFile, RemoteObject | None, str]] = []
    preflight_failed = False
    for item in files:
        try:
            remote = client.head_object(item.object_key)
        except Exception:  # pragma: no cover - defensive remote boundary
            checked.append((item, None, "failed"))
            preflight_failed = True
            continue
        if remote is not None and remote_matches(item, remote):
            checked.append((item, remote, "unchanged"))
        elif remote is not None and not force:
            checked.append((item, remote, "blocked_changed"))
            preflight_failed = True
        else:
            checked.append((item, remote, "ready"))

    if preflight_failed:
        results: list[DocsMediaPublishResult] = []
        for item, _remote, status in checked:
            if status == "failed":
                results.append(_result(item, status, "remote comparison failed"))
            elif status == "blocked_changed":
                results.append(_result(item, status, "remote object differs; use a new filename or force the CLI upload"))
            elif status == "unchanged":
                results.append(_result(item, status, "remote bytes already match"))
            else:
                results.append(_result(item, "not_attempted", "complete-set preflight did not pass"))
        return results

    if not write:
        return [
            _result(
                item,
                "unchanged" if status == "unchanged" else "would_overwrite" if remote is not None else "would_upload",
                "remote bytes already match" if status == "unchanged" else "dry-run",
            )
            for item, remote, status in checked
        ]

    results = []
    upload_failed = False
    for item, remote, status in checked:
        if status == "unchanged":
            results.append(_result(item, "unchanged", "remote bytes already match"))
            continue
        if upload_failed:
            results.append(_result(item, "not_attempted", "stopped after a remote upload failure"))
            continue
        try:
            client.put_object(item.object_key, item.local_path, content_type_for(item.local_path))
        except Exception:  # pragma: no cover - defensive remote boundary
            results.append(_result(item, "failed", "remote upload failed"))
            upload_failed = True
            continue
        results.append(_result(item, "overwritten" if remote is not None else "uploaded"))
    return results


def publish_docs_media_files(
    repo_root: Path,
    files: Sequence[DocsMediaFile],
    *,
    write: bool,
    force: bool = False,
    client: DocsRemoteClient | None = None,
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
    if config.scope_type != "public" or config.import_media_storage.storage_mode != "r2_upload":
        raise ValueError(f"Docs media scope {scope!r} is not configured for public R2 publication")
    for item in files:
        expected_key = docs_media_object_key(config, item.media_class, item.filename)
        if item.object_key != expected_key:
            raise ValueError("Docs media object key does not match the configured scope contract")

    remote_client = client
    if remote_client is None:
        selected_env_files = list(env_files) if env_files is not None else [
            repo_root / path for path in DEFAULT_ENV_FILES
        ]
        try:
            credentials = load_r2_credentials(env_files=selected_env_files, environ=environ)
        except SystemExit as exc:
            message = str(exc).removeprefix("Error: ")
            raise RuntimeError(message) from exc
        remote_client = R2Client(credentials)
    return plan_and_publish_docs_media(files, client=remote_client, write=write, force=force)


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
        "action": "upload",
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
    client: DocsRemoteClient | None = None,
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


def external_media_root_for_scope(config: DocsScopeConfig) -> Path:
    if (
        config.scope_type != LOCAL_EXTERNAL_SCOPE_TYPE
        or config.import_media_storage.storage_mode != "external_assets"
    ):
        raise ValueError(f"Docs scope {config.scope_id!r} is not an external-local media scope")
    external_root = resolve_external_data_root().resolve()
    media_root = (external_root / "media" / config.scope_id).resolve()
    if not media_root.is_relative_to(external_root):
        raise ValueError("External Docs media root escapes the configured external workspace")
    return media_root


def repo_media_root_for_scope(repo_root: Path, config: DocsScopeConfig) -> Path:
    if config.scope_type == "public" or config.import_media_storage.storage_mode != "repo_assets":
        raise ValueError(f"Docs scope {config.scope_id!r} is not a local repo-media scope")
    resolved_repo_root = repo_root.resolve()
    media_root = (
        resolved_repo_root / config.import_media_storage.repo_assets_path_prefix
    ).resolve()
    if not media_root.is_relative_to(resolved_repo_root):
        raise ValueError("Repo Docs media root escapes the repository")
    return media_root


def local_media_root_for_scope(repo_root: Path, config: DocsScopeConfig) -> Path:
    if config.import_media_storage.storage_mode == "external_assets":
        return external_media_root_for_scope(config)
    return repo_media_root_for_scope(repo_root, config)


def local_media_route(scope: str, media_class: str, filename: str) -> str:
    normalized_scope = str(scope or "").strip().lower()
    if not normalized_scope or "/" in normalized_scope or "\\" in normalized_scope:
        raise ValueError("Docs media scope must be one safe scope id")
    return f"{DOCS_MEDIA_ROUTE_PREFIX}{normalized_scope}/{validate_media_class(media_class)}/{validate_media_filename(filename)}"


def local_media_path_from_route(repo_root: Path, request_path: str) -> tuple[Path, str]:
    if not request_path.startswith(DOCS_MEDIA_ROUTE_PREFIX):
        raise ValueError("Invalid Docs media route")
    parts = request_path.removeprefix(DOCS_MEDIA_ROUTE_PREFIX).split("/")
    if len(parts) != 3:
        raise ValueError("Invalid Docs media route")
    scope, media_class, filename = parts
    normalized_class = validate_media_class(media_class)
    normalized_filename = validate_media_filename(filename)
    config = load_docs_scope_configs(repo_root).get(scope)
    if config is None:
        raise FileNotFoundError(f"Docs media scope not found: {scope!r}")
    root = local_media_root_for_scope(repo_root, config)
    path = (root / normalized_class / normalized_filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise FileNotFoundError(f"Docs media file not found: {scope}/{normalized_class}/{normalized_filename}")
    return path, normalized_class


def safe_content_type(path: Path) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if content_type in {"text/html", "application/xhtml+xml"}:
        raise ValueError("Interactive HTML is not served through the ordinary Docs media route")
    return content_type


__all__ = [
    "DOCS_MEDIA_CLASSES",
    "DOCS_MEDIA_ROUTE_PREFIX",
    "DocsMediaFile",
    "DocsMediaPublishResult",
    "docs_media_file",
    "docs_media_object_key",
    "docs_publish_report",
    "docs_publish_succeeded",
    "external_media_root_for_scope",
    "local_media_path_from_route",
    "local_media_root_for_scope",
    "local_media_route",
    "plan_and_publish_docs_media",
    "publish_docs_media_files",
    "repo_media_root_for_scope",
    "run_docs_staged_media_publish",
    "safe_content_type",
]
