#!/usr/bin/env python3
"""Shared resolver for fixed workspaces below DOTLINEFORM_PROJECTS_BASE_DIR."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"
PROJECTS_BASE_DIR_MARKER = f"${PROJECTS_BASE_DIR_ENV}"


@dataclass(frozen=True)
class ExternalWorkspaceRoot:
    projects_base: Path
    root: Path
    marker: str


def path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def safe_workspace_subdir(value: str | Path) -> Path:
    subdir = Path(value)
    if not subdir.parts or subdir.is_absolute() or ".." in subdir.parts:
        raise ValueError("external workspace subdirectory must be a safe relative path")
    return subdir


def workspace_marker(value: str | Path) -> str:
    return f"{PROJECTS_BASE_DIR_MARKER}/{safe_workspace_subdir(value).as_posix()}"


def resolve_external_workspace_root(
    workspace_subdir: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
    require_exists: bool,
    require_readable: bool = True,
    require_writable: bool = True,
) -> ExternalWorkspaceRoot:
    values = os.environ if environ is None else environ
    base_text = str(values.get(PROJECTS_BASE_DIR_ENV) or "").strip()
    if not base_text:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} is required for external workspace access")
    base_path = Path(base_text).expanduser()
    if not base_path.is_absolute() or ".." in base_path.parts:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} must be an absolute path without parent segments")
    projects_base = base_path.resolve()
    if not projects_base.is_dir():
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} does not exist or is not a directory: {projects_base}")

    subdir = safe_workspace_subdir(workspace_subdir)
    root = (projects_base / subdir).resolve()
    if not path_is_relative_to(root, projects_base):
        raise ValueError(f"external workspace resolves outside {PROJECTS_BASE_DIR_MARKER}")
    if require_exists and not root.exists():
        raise ValueError(f"external workspace does not exist: {workspace_marker(subdir)}")
    if root.exists() and not root.is_dir():
        raise ValueError(f"external workspace must be a directory: {workspace_marker(subdir)}")

    access_target = root if root.exists() else projects_base
    required_access = 0
    if require_readable:
        required_access |= os.R_OK
    if require_writable:
        required_access |= os.W_OK
    if required_access and not os.access(access_target, required_access):
        raise ValueError(f"external workspace must be readable and writable: {workspace_marker(subdir)}")
    return ExternalWorkspaceRoot(
        projects_base=projects_base,
        root=root,
        marker=workspace_marker(subdir),
    )


def resolve_workspace_path(workspace: ExternalWorkspaceRoot, relative: str | Path) -> Path:
    relative_path = safe_workspace_subdir(relative)
    resolved = (workspace.root / relative_path).resolve()
    if not path_is_relative_to(resolved, workspace.root):
        raise ValueError(f"external workspace path resolves outside {workspace.marker}")
    return resolved


def workspace_marker_path(path: Path, workspace: ExternalWorkspaceRoot) -> str:
    resolved = path.resolve()
    if resolved == workspace.root:
        return workspace.marker
    if not path_is_relative_to(resolved, workspace.root):
        raise ValueError(f"external workspace path is outside {workspace.marker}: {path.name}")
    return f"{workspace.marker}/{resolved.relative_to(workspace.root).as_posix()}"
