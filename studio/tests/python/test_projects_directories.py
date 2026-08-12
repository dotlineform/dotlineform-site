"""Focused tests for confined Projects directory navigation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from studio.shared.python.projects_directories import (
    configured_projects_base,
    list_projects_directory,
    projects_path_marker,
    resolve_projects_directory,
)


def test_lists_root_and_nested_directories_with_canonical_markers(tmp_path: Path) -> None:
    projects_base = tmp_path / "Projects"
    nested = projects_base / "projects/architecture"
    (nested / "References").mkdir(parents=True)
    (nested / "assets").mkdir()
    (nested / "notes.md").write_text("# Notes\n", encoding="utf-8")
    environ = {"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)}

    root = list_projects_directory(".", environ=environ)
    listing = list_projects_directory("projects/architecture", environ=environ)

    assert root == {
        "ok": True,
        "current_directory": ".",
        "current_selectable": False,
        "parent_directory": None,
        "directories": [
            {"label": "projects", "source_directory": "projects"},
        ],
    }
    assert listing == {
        "ok": True,
        "current_directory": "projects/architecture",
        "current_selectable": True,
        "parent_directory": "projects",
        "directories": [
            {
                "label": "assets",
                "source_directory": "projects/architecture/assets",
            },
            {
                "label": "References",
                "source_directory": "projects/architecture/References",
            },
        ],
    }
    assert projects_path_marker(nested, configured_projects_base(environ=environ)) == (
        "projects/architecture"
    )


def test_lower_root_is_selectable_and_navigation_cannot_escape_it(tmp_path: Path) -> None:
    projects_base = tmp_path / "Projects"
    (projects_base / "analysis/references/images").mkdir(parents=True)
    (projects_base / "processing").mkdir()
    environ = {"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)}

    root = list_projects_directory(
        "analysis",
        environ=environ,
        lower_root="analysis",
    )
    nested = list_projects_directory(
        "analysis/references",
        environ=environ,
        lower_root="analysis",
    )

    assert root == {
        "ok": True,
        "current_directory": "analysis",
        "current_selectable": True,
        "parent_directory": None,
        "directories": [
            {
                "label": "references",
                "source_directory": "analysis/references",
            },
        ],
    }
    assert nested["parent_directory"] == "analysis"
    with pytest.raises(ValueError, match="configured media source root"):
        resolve_projects_directory(".", environ=environ, lower_root="analysis")
    with pytest.raises(ValueError, match="configured media source root"):
        list_projects_directory("processing", environ=environ, lower_root="analysis")


@pytest.mark.parametrize(
    "marker",
    [
        "",
        " projects",
        "projects ",
        "/projects",
        "projects/",
        "projects//notes",
        "projects/./notes",
        "../notes",
        "projects\\notes",
    ],
)
def test_rejects_noncanonical_directory_markers(tmp_path: Path, marker: str) -> None:
    projects_base = tmp_path / "Projects"
    projects_base.mkdir()

    with pytest.raises(ValueError, match="source_directory"):
        resolve_projects_directory(
            marker,
            environ={"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)},
        )


def test_rejects_missing_files_and_requested_symlink_segments(tmp_path: Path) -> None:
    projects_base = tmp_path / "Projects"
    real = projects_base / "real"
    real.mkdir(parents=True)
    (projects_base / "file.txt").write_text("file\n", encoding="utf-8")
    (projects_base / "linked").symlink_to(real, target_is_directory=True)
    (projects_base / "invalid\\marker").mkdir()
    environ = {"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)}

    with pytest.raises(FileNotFoundError, match="does not exist"):
        resolve_projects_directory("missing", environ=environ)
    with pytest.raises(ValueError, match="identify a directory"):
        resolve_projects_directory("file.txt", environ=environ)
    with pytest.raises(ValueError, match="must not contain symlinks"):
        resolve_projects_directory("linked", environ=environ)

    listing = list_projects_directory(".", environ=environ)
    assert listing["directories"] == [
        {"label": "real", "source_directory": "real"},
    ]


def test_omits_unreadable_child_without_exposing_a_physical_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "Projects"
    visible = projects_base / "visible"
    hidden = projects_base / "hidden"
    visible.mkdir(parents=True)
    hidden.mkdir()
    real_access = os.access

    def fake_access(path: os.PathLike[str] | str, mode: int) -> bool:
        if Path(path) == hidden:
            return False
        return real_access(path, mode)

    monkeypatch.setattr(os, "access", fake_access)

    listing = list_projects_directory(
        ".",
        environ={"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)},
    )

    assert listing["directories"] == [
        {"label": "visible", "source_directory": "visible"},
    ]
    assert str(projects_base) not in repr(listing)
