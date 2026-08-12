"""Read-only directory navigation below the configured Projects base."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Any, Mapping

from studio.shared.python.external_workspace_paths import (
    PROJECTS_BASE_DIR_ENV,
    path_is_relative_to,
)


PROJECTS_ROOT_MARKER = "."


@dataclass(frozen=True)
class ProjectsDirectory:
    projects_base: Path
    path: Path
    marker: str


def configured_projects_base(
    *,
    environ: Mapping[str, str] | None = None,
) -> Path:
    values = os.environ if environ is None else environ
    base_text = str(values.get(PROJECTS_BASE_DIR_ENV) or "").strip()
    if not base_text:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} is required for Projects directory access")
    base_path = Path(base_text).expanduser()
    if not base_path.is_absolute() or ".." in base_path.parts:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} must identify an absolute directory")
    try:
        projects_base = base_path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} must identify an existing directory") from exc
    if not projects_base.is_dir():
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} must identify an existing directory")
    if not os.access(projects_base, os.R_OK | os.X_OK):
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} must identify a readable directory")
    return projects_base


def normalize_projects_directory_marker(value: Any) -> str:
    raw_marker = str(value or "")
    marker = raw_marker.strip()
    if marker != raw_marker:
        raise ValueError("source_directory must not contain surrounding whitespace")
    if marker == PROJECTS_ROOT_MARKER:
        return marker
    if not marker or marker.startswith("/") or marker.endswith("/") or "\\" in marker:
        raise ValueError("source_directory must be a canonical Projects-relative POSIX directory")
    parts = marker.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ValueError("source_directory must be a canonical Projects-relative POSIX directory")
    if any(any(ord(character) < 32 or ord(character) == 127 for character in part) for part in parts):
        raise ValueError("source_directory must not contain control characters")
    return "/".join(parts)


def projects_path_marker(path: Path, projects_base: Path) -> str:
    root = projects_base.resolve()
    resolved = path.resolve()
    if resolved == root:
        return PROJECTS_ROOT_MARKER
    if not path_is_relative_to(resolved, root):
        raise ValueError("Projects path resolves outside the configured Projects base")
    return resolved.relative_to(root).as_posix()


def _normalized_lower_root(value: Any | None) -> str | None:
    return None if value is None else normalize_projects_directory_marker(value)


def _marker_is_within(marker: str, lower_root: str) -> bool:
    return (
        lower_root == PROJECTS_ROOT_MARKER
        or marker == lower_root
        or marker.startswith(f"{lower_root}/")
    )


def resolve_projects_directory(
    marker: Any,
    *,
    environ: Mapping[str, str] | None = None,
    lower_root: Any | None = None,
) -> ProjectsDirectory:
    normalized = normalize_projects_directory_marker(marker)
    normalized_lower_root = _normalized_lower_root(lower_root)
    if normalized_lower_root is not None and not _marker_is_within(
        normalized,
        normalized_lower_root,
    ):
        raise ValueError("source_directory must remain within the configured media source root")
    base = configured_projects_base(environ=environ)
    current = base
    if normalized != PROJECTS_ROOT_MARKER:
        for segment in normalized.split("/"):
            candidate = current / segment
            try:
                candidate_stat = candidate.lstat()
            except FileNotFoundError as exc:
                raise FileNotFoundError("source_directory does not exist") from exc
            except OSError as exc:
                raise ValueError("source_directory could not be inspected safely") from exc
            if stat.S_ISLNK(candidate_stat.st_mode):
                raise ValueError("source_directory must not contain symlinks")
            if not stat.S_ISDIR(candidate_stat.st_mode):
                raise ValueError("source_directory must identify a directory")
            current = candidate
    resolved = current.resolve()
    if not path_is_relative_to(resolved, base):
        raise ValueError("source_directory resolves outside the configured Projects base")
    if not os.access(resolved, os.R_OK | os.X_OK):
        raise ValueError("source_directory must identify a readable directory")
    return ProjectsDirectory(
        projects_base=base,
        path=resolved,
        marker=projects_path_marker(resolved, base),
    )


def _listed_child(child: Path, projects_base: Path) -> dict[str, str] | None:
    try:
        child_stat = child.lstat()
        if stat.S_ISLNK(child_stat.st_mode) or not stat.S_ISDIR(child_stat.st_mode):
            return None
        if not os.access(child, os.R_OK | os.X_OK):
            return None
        marker = normalize_projects_directory_marker(
            projects_path_marker(child, projects_base),
        )
    except (OSError, ValueError):
        return None
    return {
        "label": child.name,
        "source_directory": marker,
    }


def list_projects_directory(
    marker: Any,
    *,
    environ: Mapping[str, str] | None = None,
    lower_root: Any | None = None,
) -> dict[str, object]:
    normalized_lower_root = _normalized_lower_root(lower_root)
    current = resolve_projects_directory(
        marker,
        environ=environ,
        lower_root=normalized_lower_root,
    )
    try:
        children = sorted(
            current.path.iterdir(),
            key=lambda path: (path.name.casefold(), path.name),
        )
    except OSError as exc:
        raise ValueError("source_directory could not be listed safely") from exc
    directories = [
        record
        for child in children
        if (record := _listed_child(child, current.projects_base)) is not None
    ]
    if current.marker == PROJECTS_ROOT_MARKER or current.marker == normalized_lower_root:
        parent_directory = None
    else:
        parent = Path(current.marker).parent.as_posix()
        parent_directory = PROJECTS_ROOT_MARKER if parent == PROJECTS_ROOT_MARKER else parent
    return {
        "ok": True,
        "current_directory": current.marker,
        "current_selectable": (
            current.marker != PROJECTS_ROOT_MARKER
            or normalized_lower_root == current.marker
        ),
        "parent_directory": parent_directory,
        "directories": directories,
    }


__all__ = [
    "PROJECTS_ROOT_MARKER",
    "ProjectsDirectory",
    "configured_projects_base",
    "list_projects_directory",
    "normalize_projects_directory_marker",
    "projects_path_marker",
    "resolve_projects_directory",
]
