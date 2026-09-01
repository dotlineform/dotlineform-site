#!/usr/bin/env python3
"""Resolve configured Work-media roots and confined source paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import stat
from typing import Any, Mapping

try:
    from .external_workspace_paths import (
        PROJECTS_BASE_DIR_MARKER,
        path_is_relative_to,
        resolve_external_workspace_root,
    )
    from .pipeline_config import (
        default_work_media_source_id,
        work_media_source_ids,
        work_media_source_root_subdir,
    )
except ImportError:  # pragma: no cover - direct sys.path import fallback
    from external_workspace_paths import (
        PROJECTS_BASE_DIR_MARKER,
        path_is_relative_to,
        resolve_external_workspace_root,
    )
    from pipeline_config import (
        default_work_media_source_id,
        work_media_source_ids,
        work_media_source_root_subdir,
    )


@dataclass(frozen=True)
class WorkMediaSourceRoot:
    """One exact configured source identity resolved below the Projects base."""

    source_id: str
    projects_base: Path
    root_subdir: Path
    root: Path
    marker: str


def resolve_work_media_source_id(config: Mapping[str, Any], value: Any = None) -> str:
    """Apply the configured default and reject every unknown explicit identity."""

    source_id = str(value or "").strip()
    if not source_id:
        return default_work_media_source_id(config)
    if source_id not in work_media_source_ids(config):
        raise ValueError(f"unknown Work media source identity: {source_id}")
    return source_id


def work_media_source_id_for_storage(config: Mapping[str, Any], value: Any = None) -> str | None:
    """Return only non-default source identities for canonical serialization."""

    source_id = resolve_work_media_source_id(config, value)
    return None if source_id == default_work_media_source_id(config) else source_id


def _reject_symlink_segments(projects_base: Path, subdir: Path, *, require_exists: bool) -> None:
    current = projects_base
    for segment in subdir.parts:
        current = current / segment
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            if require_exists:
                raise ValueError(
                    f"Work media source root does not exist: {PROJECTS_BASE_DIR_MARKER}/{subdir.as_posix()}"
                ) from None
            return
        except OSError as exc:
            raise ValueError("Work media source root could not be inspected safely") from exc
        if stat.S_ISLNK(current_stat.st_mode):
            raise ValueError("Work media source root must not contain symlinks")
        if not stat.S_ISDIR(current_stat.st_mode):
            raise ValueError("Work media source root must be a directory")


def resolve_work_media_source_root(
    config: Mapping[str, Any],
    value: Any = None,
    *,
    environ: Mapping[str, str] | None = None,
    require_exists: bool = True,
) -> WorkMediaSourceRoot:
    """Resolve one configured source root without a repository or default-root fallback."""

    source_id = resolve_work_media_source_id(config, value)
    root_subdir = work_media_source_root_subdir(config, source_id)
    workspace = resolve_external_workspace_root(
        root_subdir,
        environ=environ,
        require_exists=require_exists,
        require_readable=True,
        require_writable=False,
    )
    _reject_symlink_segments(workspace.projects_base, root_subdir, require_exists=require_exists)
    return WorkMediaSourceRoot(
        source_id=source_id,
        projects_base=workspace.projects_base,
        root_subdir=root_subdir,
        root=workspace.root,
        marker=workspace.marker,
    )


def _safe_relative_path(parts: tuple[Any, ...]) -> Path:
    text_parts: list[str] = []
    for value in parts:
        text = str(value or "").strip()
        if text:
            if "\\" in text or any(ord(character) < 32 or ord(character) == 127 for character in text):
                raise ValueError("Work media path must be a canonical relative POSIX path")
            text_parts.append(text)
    relative = Path(*text_parts)
    if (
        not relative.parts
        or relative.is_absolute()
        or ".." in relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValueError("Work media path must be a safe relative path")
    return relative


def resolve_work_media_path(
    source_root: WorkMediaSourceRoot,
    *relative_parts: Any,
    require_exists: bool = False,
) -> Path:
    """Resolve a source-relative path and reject symlinks at every access."""

    _reject_symlink_segments(source_root.projects_base, source_root.root_subdir, require_exists=True)
    relative = _safe_relative_path(relative_parts)
    current = source_root.root
    missing = False
    for index, segment in enumerate(relative.parts):
        current = current / segment
        if missing:
            continue
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            missing = True
            if require_exists:
                raise FileNotFoundError(f"Work media path does not exist: {source_root.marker}/{relative.as_posix()}") from None
            continue
        except OSError as exc:
            raise ValueError("Work media path could not be inspected safely") from exc
        if stat.S_ISLNK(current_stat.st_mode):
            raise ValueError("Work media path must not contain symlinks")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(current_stat.st_mode):
            raise ValueError("Work media path parent must be a directory")

    resolved = current.resolve(strict=False)
    if not path_is_relative_to(resolved, source_root.root):
        raise ValueError(f"Work media path resolves outside {source_root.marker}")
    return resolved


def work_media_display_path(path: Path, source_root: WorkMediaSourceRoot) -> str:
    """Return a machine-independent path below DOTLINEFORM_PROJECTS_BASE_DIR."""

    resolved = path.resolve(strict=False)
    if not path_is_relative_to(resolved, source_root.root):
        raise ValueError(f"Work media path is outside {source_root.marker}")
    relative = resolved.relative_to(source_root.root)
    suffix = "" if str(relative) == "." else f"/{relative.as_posix()}"
    return f"{source_root.root_subdir.as_posix()}{suffix}"
