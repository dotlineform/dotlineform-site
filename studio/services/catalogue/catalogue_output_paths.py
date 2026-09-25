"""Resolve Working Catalogue JSON and shared assets in the configured Docs workspace."""

from pathlib import Path
from typing import Mapping

from docs_artifact_locations import ArtifactLocation
from docs_workspace_config import (
    DOTLINEFORM_DOCS_BASE_DIR_ENV, DocsWorkspaceConfig, load_docs_workspace_config,
    location_child, safe_relative_path,
)
from local_env import runtime_env

CATALOGUE_OUTPUT_ROUTE_PREFIX = "/studio/catalogue-output/"


def catalogue_workspace_config(repo_root: Path, *, environ: Mapping[str, str] | None = None) -> DocsWorkspaceConfig:
    """Use the explicit Docs environment binding, independently of Projects sources."""
    env = runtime_env(repo_root=repo_root, environ=environ)
    value = env.get(DOTLINEFORM_DOCS_BASE_DIR_ENV, "").strip()
    if not value:
        raise ValueError(f"{DOTLINEFORM_DOCS_BASE_DIR_ENV} is required")
    return load_docs_workspace_config(repo_root, docs_base_dir=Path(value))


def catalogue_output_workspace(repo_root: Path, *, environ: Mapping[str, str] | None = None) -> ArtifactLocation:
    """Select the configured Working JSON destination; no creation or old-root fallback."""
    return catalogue_workspace_config(repo_root, environ=environ).catalogue.working


def output_path(workspace: ArtifactLocation, relative: str | Path) -> Path:
    """Resolve an owned descendant without traversal or symlinks."""
    return location_child(workspace, safe_relative_path(str(relative), field="Catalogue output")).path


def thumbnail_directory(repo_root: Path, kind: str) -> Path:
    """Return the Work thumbnail destination used by Studio."""
    if kind != "work":
        raise ValueError(f"unsupported Catalogue media kind: {kind}")
    return catalogue_workspace_config(repo_root).assets.work_thumbnails.path
