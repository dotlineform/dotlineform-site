"""Confine replaceable Catalogue output to its existing external workspace."""

from pathlib import Path
from typing import Mapping

from external_workspace_paths import ExternalWorkspaceRoot, resolve_external_workspace_root, resolve_workspace_path
from local_env import runtime_env

CATALOGUE_OUTPUT_ROUTE_PREFIX = "/studio/catalogue-output/"


def catalogue_output_workspace(repo_root: Path, *, environ: Mapping[str, str] | None = None) -> ExternalWorkspaceRoot:
    """Require the configured workspace; never create a replacement root."""
    return resolve_external_workspace_root(
        "catalogue/generated", environ=environ if environ is not None else runtime_env(repo_root=repo_root),
        require_exists=True,
    )


def output_path(workspace: ExternalWorkspaceRoot, relative: str | Path) -> Path:
    """Resolve an owned path, rejecting symlinks that leave the output root."""
    return resolve_workspace_path(workspace, relative)


def thumbnail_directory(repo_root: Path, kind: str) -> Path:
    """Return the Work or Detail thumbnail destination used by Studio."""
    families = {"work": "works", "work_details": "work_details"}
    if kind not in families:
        raise ValueError(f"unsupported Catalogue media kind: {kind}")
    return output_path(catalogue_output_workspace(repo_root), f"{families[kind]}/thumbs")
