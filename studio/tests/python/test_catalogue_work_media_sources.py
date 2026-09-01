#!/usr/bin/env python3
"""Focused checks for configured Catalogue Work-media source roots."""

from __future__ import annotations

from pathlib import Path

import pytest

from catalogue_work_media_sources import (
    resolve_work_media_path,
    resolve_work_media_source_id,
    resolve_work_media_source_root,
    work_media_source_id_for_storage,
)
from pipeline_config import (
    default_work_media_source_id,
    load_pipeline_config,
    work_media_source_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG = load_pipeline_config(repo_root=REPO_ROOT)


def environment(projects_base: Path) -> dict[str, str]:
    return {"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)}


def test_pipeline_config_owns_two_exact_sources_and_no_retired_scalar() -> None:
    assert "works" not in CONFIG["paths"]["source_roots"]
    assert work_media_source_config(CONFIG) == {
        "default": "projects",
        "roots": {
            "projects": "projects",
            "processing": "processing",
        },
    }
    assert default_work_media_source_id(CONFIG) == "projects"


def test_omission_resolves_to_projects_but_only_processing_is_serialized() -> None:
    assert resolve_work_media_source_id(CONFIG, None) == "projects"
    assert resolve_work_media_source_id(CONFIG, "processing") == "processing"
    assert work_media_source_id_for_storage(CONFIG, "projects") is None
    assert work_media_source_id_for_storage(CONFIG, "processing") == "processing"


@pytest.mark.parametrize("source_id", ["unknown", "../projects", "/projects"])
def test_unknown_or_unsafe_source_identity_is_rejected(source_id: str) -> None:
    with pytest.raises(ValueError, match="unknown Work media source identity"):
        resolve_work_media_source_id(CONFIG, source_id)


def test_processing_source_path_is_confined_to_its_exact_root(tmp_path: Path) -> None:
    processing_root = tmp_path / "processing"
    media_folder = processing_root / "ink-engine"
    media_folder.mkdir(parents=True)
    source_root = resolve_work_media_source_root(
        CONFIG,
        "processing",
        environ=environment(tmp_path),
    )

    assert source_root.root == processing_root
    assert resolve_work_media_path(source_root, "ink-engine", "frame.jpg") == media_folder / "frame.jpg"
    with pytest.raises(ValueError, match="safe relative path"):
        resolve_work_media_path(source_root, "../projects/frame.jpg")


def test_missing_selected_root_is_unavailable_without_default_fallback(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()
    with pytest.raises(ValueError, match="processing"):
        resolve_work_media_source_root(
            CONFIG,
            "processing",
            environ=environment(tmp_path),
        )


def test_source_root_and_nested_path_symlinks_are_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "processing").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="must not contain symlinks"):
        resolve_work_media_source_root(
            CONFIG,
            "processing",
            environ=environment(tmp_path),
        )

    (tmp_path / "processing").unlink()
    processing_root = tmp_path / "processing"
    processing_root.mkdir()
    (processing_root / "ink-engine").symlink_to(outside, target_is_directory=True)
    source_root = resolve_work_media_source_root(
        CONFIG,
        "processing",
        environ=environment(tmp_path),
    )
    with pytest.raises(ValueError, match="must not contain symlinks"):
        resolve_work_media_path(source_root, "ink-engine", "frame.jpg")
