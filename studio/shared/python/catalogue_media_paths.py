#!/usr/bin/env python3
"""Resolve the external catalogue-media workspace and local preview URLs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

try:
    from .external_workspace_paths import (
        ExternalWorkspaceRoot,
        resolve_external_workspace_root,
        resolve_workspace_path,
    )
    from .local_env import runtime_env
    from .pipeline_config import load_pipeline_config, media_root_subdir
except ImportError:  # pragma: no cover - direct sys.path import fallback
    from external_workspace_paths import (
        ExternalWorkspaceRoot,
        resolve_external_workspace_root,
        resolve_workspace_path,
    )
    from local_env import runtime_env
    from pipeline_config import load_pipeline_config, media_root_subdir


CATALOGUE_MEDIA_ROUTE_PREFIX = "/studio/media/catalogue/"


def configured_catalogue_media_workspace(
    repo_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
    config: Mapping[str, Any] | None = None,
) -> ExternalWorkspaceRoot:
    """Resolve the media root using the operation's loaded policy when supplied."""
    config = load_pipeline_config(repo_root=repo_root) if config is None else config
    values = dict(environ) if environ is not None else runtime_env(repo_root=repo_root)
    return resolve_external_workspace_root(
        media_root_subdir(config),
        environ=values,
        require_exists=False,
    )


def configured_catalogue_media_root(
    repo_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
    config: Mapping[str, Any] | None = None,
) -> Path:
    """Return the checked root without rereading an explicitly supplied policy."""
    return configured_catalogue_media_workspace(repo_root, environ=environ, config=config).root


def resolve_catalogue_media_request_path(workspace: ExternalWorkspaceRoot, request_path: str) -> Path:
    if not request_path.startswith(CATALOGUE_MEDIA_ROUTE_PREFIX):
        raise ValueError("request is outside the catalogue media route")
    relative_text = request_path.removeprefix(CATALOGUE_MEDIA_ROUTE_PREFIX)
    relative = Path(relative_text)
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ValueError("invalid catalogue media request path")
    return resolve_workspace_path(workspace, relative)
