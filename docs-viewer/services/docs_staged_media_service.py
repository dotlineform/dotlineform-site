#!/usr/bin/env python3
"""Plan and publish staged media for Docs source-editor insertion."""

from __future__ import annotations

import datetime as dt
import re
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

from docs_artifact_locations import (
    ArtifactLocation,
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
)
from docs_import_common import (
    FILE_MEDIA_STAGED_SUFFIXES,
    RASTER_IMAGE_STAGED_SUFFIXES,
    SVG_STAGED_SUFFIXES,
    humanize,
    slugify,
)
from docs_import_media import build_media_plan
from docs_media_storage import (
    docs_media_file,
    docs_publish_succeeded,
    publish_docs_media_files,
    validate_media_filename,
)
from docs_mermaid_media import produce_mermaid_svg
from docs_scope_config import load_docs_scope_configs
from docs_svg_sanitizer import SanitizedSvg, sanitize_svg_bytes
from services.paths import configured_workspace_paths, marker_path, workspace_status


STAGED_MEDIA_IMAGE = "image"
STAGED_MEDIA_FILE = "file"
STAGED_MEDIA_KINDS = {STAGED_MEDIA_IMAGE, STAGED_MEDIA_FILE}
MERMAID_STAGED_SUFFIXES = {".mmd"}
TOKEN_SAFE_MEDIA_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class PreparedMermaidMedia:
    source_identity: str
    published_identity: str
    source_bytes: bytes
    published_bytes: bytes
    source_adapter: ArtifactLocationAdapter
    published_adapter: ArtifactLocationAdapter
    sanitized: SanitizedSvg
    collision: str
    published_status: str
    source_status: str


def normalize_media_kind(value: Any) -> str:
    kind = str(value or "").strip().lower()
    if kind not in STAGED_MEDIA_KINDS:
        raise ValueError("media_kind must be image or file")
    return kind


def media_suffixes(kind: str) -> set[str]:
    return (
        RASTER_IMAGE_STAGED_SUFFIXES | SVG_STAGED_SUFFIXES | MERMAID_STAGED_SUFFIXES
        if normalize_media_kind(kind) == STAGED_MEDIA_IMAGE
        else FILE_MEDIA_STAGED_SUFFIXES
    )


def validate_media_identity(value: Any) -> str:
    return validate_media_filename(str(value or "").strip())


def published_media_filename(source_path: Path) -> str:
    filename = validate_media_identity(source_path.name)
    if TOKEN_SAFE_MEDIA_FILENAME_PATTERN.fullmatch(filename):
        return filename
    return f"{slugify(source_path.stem)}{source_path.suffix.lower()}"


def normalize_label(value: Any, *, fallback: str) -> str:
    label = " ".join(str(value or "").split()) or fallback
    return label.replace("\\", r"\\").replace("[", r"\[").replace("]", r"\]")


def _resolve_staged_media(staging_root: Path, filename: str, kind: str) -> Path:
    normalized_filename = validate_media_identity(filename)
    root = staging_root.resolve()
    unresolved = root / normalized_filename
    if unresolved.is_symlink():
        raise ValueError("staged media files must not be symlinks")
    source_path = unresolved.resolve()
    if source_path.parent != root or not source_path.is_file():
        raise FileNotFoundError(f"staged media file does not exist: {normalized_filename}")
    if source_path.suffix.lower() not in media_suffixes(kind):
        supported = ", ".join(sorted(media_suffixes(kind)))
        raise ValueError(f"staged {kind} file must use one of these extensions: {supported}")
    return source_path


def list_staged_media_files(repo_root: Path, kind: str) -> dict[str, Any]:
    normalized_kind = normalize_media_kind(kind)
    status = workspace_status(repo_root, required_paths=("import_staging",))
    if not status["available"]:
        return {
            "ok": True,
            "available": False,
            "staging_root": status["root"],
            "message": status["message"],
            "media_kind": normalized_kind,
            "files": [],
        }
    workspace = configured_workspace_paths(repo_root)
    staging_root = workspace.import_staging.resolve()
    suffixes = media_suffixes(normalized_kind)
    files: list[dict[str, Any]] = []
    for path in sorted(staging_root.iterdir(), key=lambda candidate: candidate.name.lower()):
        if (
            not path.is_file()
            or path.is_symlink()
            or path.suffix.lower() not in suffixes
        ):
            continue
        stat = path.stat()
        files.append({
            "filename": path.name,
            "path": marker_path(path, workspace_root=workspace.root),
            "media_kind": normalized_kind,
            "media_format": (
                "mermaid"
                if path.suffix.lower() == ".mmd"
                else "svg"
                if path.suffix.lower() == ".svg"
                else "raster"
                if normalized_kind == STAGED_MEDIA_IMAGE
                else "file"
            ),
            "suggested_label": humanize(path.stem),
            "size_bytes": stat.st_size,
            "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    return {
        "ok": True,
        "available": True,
        "staging_root": marker_path(staging_root, workspace_root=workspace.root),
        "message": "",
        "media_kind": normalized_kind,
        "files": files,
    }


@contextmanager
def _prepared_media_source(
    source_path: Path,
    kind: str,
    media_filename: str,
) -> Iterator[tuple[Path, Path, SanitizedSvg | None]]:
    is_svg = normalize_media_kind(kind) == STAGED_MEDIA_IMAGE and source_path.suffix.lower() == ".svg"
    if not is_svg and media_filename == source_path.name:
        yield source_path, source_path.parent, None
        return
    sanitized = sanitize_svg_bytes(source_path.read_bytes()) if is_svg else None
    with tempfile.TemporaryDirectory(prefix="docs-staged-media-publish-") as temp_dir:
        temp_root = Path(temp_dir).resolve()
        prepared_path = temp_root / media_filename
        if sanitized:
            prepared_path.write_bytes(sanitized.bytes)
        else:
            shutil.copyfile(source_path, prepared_path)
        yield prepared_path, temp_root, sanitized


def _staged_media_contract(repo_root: Path, body: dict[str, Any]) -> tuple[str, str, Path, str, str, str]:
    kind = normalize_media_kind(body.get("media_kind"))
    scope = str(body.get("scope") or "").strip().lower()
    configs = load_docs_scope_configs(repo_root)
    if scope not in configs:
        raise ValueError(f"scope must be one of: {', '.join(sorted(configs))}")
    workspace = configured_workspace_paths(repo_root)
    source_path = _resolve_staged_media(workspace.import_staging, body.get("staged_filename"), kind)
    fallback = humanize(source_path.stem) or ("Image" if kind == STAGED_MEDIA_IMAGE else "File")
    label = normalize_label(body.get("label"), fallback=fallback)
    media_class = (
        "mermaid"
        if kind == STAGED_MEDIA_IMAGE and source_path.suffix.lower() == ".mmd"
        else "svg"
        if kind == STAGED_MEDIA_IMAGE and source_path.suffix.lower() == ".svg"
        else "img"
        if kind == STAGED_MEDIA_IMAGE
        else "files"
    )
    media_filename = published_media_filename(source_path)
    if media_class == "mermaid":
        media_filename = Path(media_filename).with_suffix(".mmd").name
    return scope, kind, source_path, label, media_class, media_filename


def _markdown_token(kind: str, label: str, media_token: str) -> str:
    return f"![{label}]({media_token})" if kind == STAGED_MEDIA_IMAGE else f"[{label}]({media_token})"


def _artifact_status(adapter: ArtifactLocationAdapter, identity: str, data: bytes) -> str:
    existing = adapter.stat(identity)
    if existing is None:
        return "new"
    return "unchanged" if adapter.verify_bytes(identity, data) else "replace"


def _prepared_mermaid_media(
    repo_root: Path,
    scope: str,
    source_path: Path,
    source_filename: str,
) -> PreparedMermaidMedia:
    config = load_docs_scope_configs(repo_root)[scope]
    build = config.source.build_media.get("mermaid")
    if build is None or build.producer != "mermaid" or build.publishes_to != "svg":
        raise ValueError(f"scope {scope!r} does not configure Mermaid source media")
    published_media = config.published.media.get("svg")
    if published_media is None or "mermaid" not in published_media.build_inputs:
        raise ValueError(f"scope {scope!r} does not register Mermaid as an SVG build input")

    source_identity = source_filename
    published_identity = Path(source_filename).with_suffix(".svg").as_posix()
    source_bytes = source_path.read_bytes()
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        [published_media.location],
    )
    source_adapter = artifact_location_adapter(
        repo_root,
        ArtifactLocation(
            provider=config.source.location.provider,
            path=config.source.location.path / build.path,
        ),
    )
    published_adapter = artifact_location_adapter(
        repo_root,
        published_media.location,
        served_path_prefix=published_media.served_path_prefix,
        remote_client=remote_client,
    )

    with tempfile.TemporaryDirectory(prefix="docs-staged-mermaid-render-") as temp_dir:
        temp_root = Path(temp_dir).resolve()
        temporary_source = artifact_location_adapter(
            temp_root,
            ArtifactLocation(provider="repository", path=Path("source")),
        )
        temporary_published = artifact_location_adapter(
            temp_root,
            ArtifactLocation(provider="repository", path=Path("published")),
        )
        temporary_source.replace(source_identity, source_bytes, content_type="text/plain")
        context = SimpleNamespace(
            source=temporary_source,
            published=temporary_published,
            write=True,
            requested_published_identities=(published_identity,),
        )
        outputs = produce_mermaid_svg(context)
        if outputs != (published_identity,):
            raise RuntimeError(f"Mermaid producer did not render {published_identity!r}")
        published_bytes = temporary_published.read(published_identity)

    sanitized = sanitize_svg_bytes(published_bytes)
    source_status = _artifact_status(source_adapter, source_identity, source_bytes)
    published_status = _artifact_status(published_adapter, published_identity, published_bytes)
    statuses = {source_status, published_status}
    collision = "replace" if "replace" in statuses else "unchanged" if statuses == {"unchanged"} else "new"
    return PreparedMermaidMedia(
        source_identity=source_identity,
        published_identity=published_identity,
        source_bytes=source_bytes,
        published_bytes=published_bytes,
        source_adapter=source_adapter,
        published_adapter=published_adapter,
        sanitized=sanitized,
        collision=collision,
        published_status=published_status,
        source_status=source_status,
    )


def _mermaid_preview_payload(
    repo_root: Path,
    scope: str,
    kind: str,
    source_path: Path,
    label: str,
    prepared: PreparedMermaidMedia,
) -> dict[str, Any]:
    plan = build_media_plan(
        scope,
        "svg",
        Path(prepared.published_identity),
        label,
        repo_root=repo_root,
    )
    return {
        "ok": True,
        "scope": scope,
        "media_kind": kind,
        "media_format": "mermaid",
        "staged_filename": source_path.name,
        "source_identity": prepared.source_identity,
        "published_filename": Path(prepared.published_identity).name,
        "label": label,
        "media_identity": plan["media_path"],
        "media_token": plan["media_token"],
        "markdown": _markdown_token(kind, label, plan["media_token"]),
        "collision": prepared.collision,
        "requires_replace_confirmation": prepared.collision == "replace",
        "size_bytes": len(prepared.published_bytes),
        "svg": {
            "title": prepared.sanitized.title,
            "diagnostics": prepared.sanitized.diagnostics(),
        },
    }


def preview_staged_media(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope, kind, source_path, label, media_class, media_filename = _staged_media_contract(repo_root, body)
    if media_class == "mermaid":
        prepared = _prepared_mermaid_media(repo_root, scope, source_path, media_filename)
        return _mermaid_preview_payload(repo_root, scope, kind, source_path, label, prepared)
    config = load_docs_scope_configs(repo_root)[scope]
    with _prepared_media_source(source_path, kind, media_filename) as (prepared_path, source_root, sanitized):
        item = docs_media_file(
            config,
            media_class=media_class,
            local_path=prepared_path,
            source_root=source_root,
            filename=media_filename,
        )
        result = publish_docs_media_files(repo_root, [item], write=False, force=True)[0]
        plan = build_media_plan(scope, media_class, Path(media_filename), label, repo_root=repo_root)
        collision = "unchanged" if result.status == "unchanged" else "replace" if result.status == "would_overwrite" else "new"
        return {
            "ok": True,
            "scope": scope,
            "media_kind": kind,
            "staged_filename": source_path.name,
            "published_filename": media_filename,
            "label": label,
            "media_identity": plan["media_path"],
            "media_token": plan["media_token"],
            "markdown": _markdown_token(kind, label, plan["media_token"]),
            "collision": collision,
            "requires_replace_confirmation": collision == "replace",
            "size_bytes": item.size,
            "svg": {
                "title": sanitized.title,
                "diagnostics": sanitized.diagnostics(),
            } if sanitized else None,
        }


def apply_staged_media(repo_root: Path, body: dict[str, Any], *, write: bool = True) -> dict[str, Any]:
    scope, kind, source_path, label, media_class, media_filename = _staged_media_contract(repo_root, body)
    if media_class == "mermaid":
        prepared = _prepared_mermaid_media(repo_root, scope, source_path, media_filename)
        preview = _mermaid_preview_payload(repo_root, scope, kind, source_path, label, prepared)
        confirm_replace = bool(body.get("confirm_replace"))
        if preview["requires_replace_confirmation"] and not confirm_replace:
            raise ValueError("canonical Mermaid source or published SVG bytes differ; confirm replacement or cancel")
        if write:
            prepared.source_adapter.replace(
                prepared.source_identity,
                prepared.source_bytes,
                content_type="text/plain",
            )
            if not prepared.source_adapter.verify_bytes(prepared.source_identity, prepared.source_bytes):
                raise RuntimeError("Canonical Mermaid source publication verification failed")
            prepared.published_adapter.replace(
                prepared.published_identity,
                prepared.published_bytes,
                content_type="image/svg+xml",
            )
            if not prepared.published_adapter.verify_bytes(prepared.published_identity, prepared.published_bytes):
                raise RuntimeError("Mermaid SVG publication verification failed")
        published_status = (
            "unchanged"
            if prepared.published_status == "unchanged"
            else "overwritten"
            if prepared.published_status == "replace" and write
            else "uploaded"
            if write
            else "would_overwrite"
            if prepared.published_status == "replace"
            else "would_upload"
        )
        return {
            **preview,
            "preview_only": not write,
            "source_publish": {
                "identity": prepared.source_identity,
                "status": prepared.source_status,
                "size": len(prepared.source_bytes),
            },
            "publish": {
                "scope": scope,
                "media_class": "svg",
                "filename": prepared.published_identity,
                "size": len(prepared.published_bytes),
                "status": published_status,
                "reason": "",
            },
            "summary_text": (
                f"Published {source_path.name} and rendered Mermaid SVG."
                if write and prepared.collision != "unchanged"
                else f"Verified {source_path.name} and rendered Mermaid SVG."
                if write
                else f"Prepared Mermaid publication preview for {source_path.name}."
            ),
        }

    preview = preview_staged_media(repo_root, body)
    confirm_replace = bool(body.get("confirm_replace"))
    if preview["requires_replace_confirmation"] and not confirm_replace:
        raise ValueError("published media bytes differ; confirm replacement or cancel")

    config = load_docs_scope_configs(repo_root)[scope]
    with _prepared_media_source(source_path, kind, media_filename) as (prepared_path, source_root, _sanitized):
        item = docs_media_file(
            config,
            media_class=media_class,
            local_path=prepared_path,
            source_root=source_root,
            filename=media_filename,
        )
        results = publish_docs_media_files(
            repo_root,
            [item],
            write=write,
            force=confirm_replace,
        )
    if write and not docs_publish_succeeded(results):
        raise RuntimeError(f"Docs media publication did not complete: {results[0].status}")
    return {
        **preview,
        "preview_only": not write,
        "publish": asdict(results[0]),
        "summary_text": (
            f"Published {source_path.name}."
            if write and results[0].status != "unchanged"
            else f"Verified {source_path.name}."
            if write
            else f"Prepared publication preview for {source_path.name}."
        ),
    }


__all__ = [
    "STAGED_MEDIA_FILE",
    "STAGED_MEDIA_IMAGE",
    "apply_staged_media",
    "list_staged_media_files",
    "normalize_media_kind",
    "published_media_filename",
    "preview_staged_media",
    "validate_media_identity",
]
