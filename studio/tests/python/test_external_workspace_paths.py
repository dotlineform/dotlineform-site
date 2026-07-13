#!/usr/bin/env python3
"""Focused checks for the shared external workspace resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from studio.shared.python.external_workspace_paths import (
    resolve_external_workspace_root,
    resolve_workspace_path,
    workspace_marker_path,
)
from studio.shared.python.catalogue_media_paths import (
    resolve_catalogue_media_request_path,
)


def test_resolver_projects_distinct_domain_roots_from_one_projects_base(tmp_path: Path) -> None:
    projects_base = tmp_path / "projects-base"
    data_sharing = projects_base / "data-sharing"
    data_sharing.mkdir(parents=True)
    environ = {"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)}

    data_workspace = resolve_external_workspace_root("data-sharing", environ=environ, require_exists=True)
    catalogue_workspace = resolve_external_workspace_root("catalogue/media", environ=environ, require_exists=False)
    docs_workspace = resolve_external_workspace_root("docs-viewer", environ=environ, require_exists=False)
    docs_export_workspace = resolve_external_workspace_root("docs-export", environ=environ, require_exists=False)

    assert data_workspace.root == data_sharing.resolve()
    assert data_workspace.marker == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing"
    assert catalogue_workspace.root == (projects_base / "catalogue/media").resolve()
    assert catalogue_workspace.marker == "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media"
    assert docs_workspace.root == (projects_base / "docs-viewer").resolve()
    assert docs_export_workspace.root == (projects_base / "docs-export").resolve()


def test_resolver_confines_child_paths_and_marker_projection(tmp_path: Path) -> None:
    projects_base = tmp_path / "projects-base"
    projects_base.mkdir()
    workspace = resolve_external_workspace_root(
        "catalogue/media",
        environ={"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)},
        require_exists=False,
    )
    image = resolve_workspace_path(workspace, "works/srcset_images/primary/00001-primary-800.webp")

    assert image == (projects_base / "catalogue/media/works/srcset_images/primary/00001-primary-800.webp").resolve()
    assert workspace_marker_path(image, workspace) == (
        "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/works/srcset_images/primary/00001-primary-800.webp"
    )
    with pytest.raises(ValueError, match="safe relative path"):
        resolve_workspace_path(workspace, "../projects/original.jpg")


def test_catalogue_preview_route_maps_to_external_workspace_and_rejects_escape(tmp_path: Path) -> None:
    projects_base = tmp_path / "projects-base"
    projects_base.mkdir()
    workspace = resolve_external_workspace_root(
        "catalogue/media",
        environ={"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)},
        require_exists=False,
    )
    image = resolve_catalogue_media_request_path(
        workspace,
        "/studio/media/catalogue/works/srcset_images/primary/00001-primary-800.webp",
    )

    assert image == (workspace.root / "works/srcset_images/primary/00001-primary-800.webp").resolve()
    with pytest.raises(ValueError, match="invalid catalogue media request path"):
        resolve_catalogue_media_request_path(
            workspace,
            "/studio/media/catalogue/../projects/original.jpg",
        )
