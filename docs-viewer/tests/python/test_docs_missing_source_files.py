#!/usr/bin/env python3
"""Focused checks for the Missing Source Files producer."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unicodedata

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer/services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from docs_missing_source_files import (  # noqa: E402
    REPORT_SCHEMA_VERSION,
    MissingSourceFilesPaths,
    MissingSourceFilesProducer,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def work(
    work_id: str,
    title: str,
    folder: str,
    filename: str,
    *,
    subfolder: str = "",
) -> dict[str, object]:
    record: dict[str, object] = {
        "work_id": work_id,
        "title": title,
        "status": "published",
        "series_ids": [],
        "project_folder": folder,
        "project_filename": filename,
    }
    if subfolder:
        record["project_subfolder"] = subfolder
    return record


def write_catalogue(source_dir: Path, works: dict[str, dict[str, object]]) -> None:
    write_json(source_dir / "works.json", {"works": works})
    write_json(source_dir / "series.json", {"series": {}})
    (source_dir / "work_details").mkdir(parents=True, exist_ok=True)


def fixture_paths(tmp_path: Path) -> tuple[MissingSourceFilesPaths, Path, Path]:
    projects_base = tmp_path / "external"
    projects_root = projects_base / "projects"
    source_dir = tmp_path / "studio/data/canonical/catalogue"
    projects_root.mkdir(parents=True)
    return (
        MissingSourceFilesPaths(
            projects_base_dir=projects_base,
            catalogue_source_dir=source_dir,
        ),
        projects_root,
        source_dir,
    )


def create_unicode_alias(actual: Path, expected: Path) -> None:
    actual.write_text("same file", encoding="utf-8")
    if not expected.exists():
        os.link(actual, expected)
    assert actual.name != expected.name
    assert unicodedata.normalize("NFC", actual.name) == unicodedata.normalize("NFC", expected.name)
    assert os.path.samefile(actual, expected)


def test_report_checks_each_complete_work_path_as_a_file(tmp_path: Path) -> None:
    paths, projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(
        source_dir,
        {
            "00001": work("00001", "Present", "alpha", "primary.jpg"),
            "00002": work("00002", "Nested present", "wa", "ink.jpg", subfolder="ink"),
            "00003": work("00003", "Missing", "alpha", "missing.jpg"),
            "00004": work("00004", "Nested missing", "wa", "missing.jpg", subfolder="ink"),
            "00005": {
                "work_id": "00005",
                "title": "Incomplete",
                "status": "draft",
                "series_ids": [],
                "project_folder": "alpha",
            },
            "00006": work("00006", "Directory is not a file", "alpha", "directory.jpg"),
            "00007": work("00007", "Unicode present", "alpha", "moiré.jpg"),
            "00008": work("00008", "Same missing path", "alpha", "missing.jpg"),
        },
    )
    alpha = projects_root / "alpha"
    ink = projects_root / "wa/ink"
    alpha.mkdir()
    ink.mkdir(parents=True)
    (alpha / "primary.jpg").write_text("present", encoding="utf-8")
    (ink / "ink.jpg").write_text("nested", encoding="utf-8")
    (alpha / "directory.jpg").mkdir()
    create_unicode_alias(alpha / "moire\u0301.jpg", alpha / "moiré.jpg")

    payload = MissingSourceFilesProducer(repo_root=tmp_path, paths=paths).run()

    assert set(payload) == {"report"}
    assert set(payload["report"]) == {"schema_version", "rows"}
    assert payload["report"]["schema_version"] == REPORT_SCHEMA_VERSION
    assert payload["report"]["rows"] == [
        {
            "work_id": "00003",
            "work_title": "Missing",
            "expected_source_path": "alpha/missing.jpg",
        },
        {
            "work_id": "00004",
            "work_title": "Nested missing",
            "expected_source_path": "wa/ink/missing.jpg",
        },
        {
            "work_id": "00006",
            "work_title": "Directory is not a file",
            "expected_source_path": "alpha/directory.jpg",
        },
        {
            "work_id": "00008",
            "work_title": "Same missing path",
            "expected_source_path": "alpha/missing.jpg",
        },
    ]


@pytest.mark.parametrize(
    ("folder", "subfolder", "filename", "field"),
    [
        ("../outside", "", "missing.jpg", "project_folder"),
        ("alpha", "../outside", "missing.jpg", "project_subfolder"),
        ("alpha", "", "../missing.jpg", "project_filename"),
    ],
)
def test_report_rejects_parent_traversal(
    tmp_path: Path,
    folder: str,
    subfolder: str,
    filename: str,
    field: str,
) -> None:
    paths, _projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(
        source_dir,
        {"00001": work("00001", "Traversal", folder, filename, subfolder=subfolder)},
    )

    with pytest.raises(ValueError, match=field):
        MissingSourceFilesProducer(repo_root=tmp_path, paths=paths).run()


def test_report_rejects_a_source_path_resolving_outside_root(tmp_path: Path) -> None:
    paths, projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(
        source_dir,
        {
            "00001": work("00001", "Outside", "linked", "missing.jpg"),
        },
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    (projects_root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="outside the Projects source root"):
        MissingSourceFilesProducer(repo_root=tmp_path, paths=paths).run()


def test_report_rejects_a_source_file_resolving_outside_root(tmp_path: Path) -> None:
    paths, projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(
        source_dir,
        {
            "00001": work("00001", "Outside", "alpha", "linked.jpg"),
        },
    )
    alpha = projects_root / "alpha"
    alpha.mkdir()
    outside = tmp_path / "outside.jpg"
    outside.write_text("outside", encoding="utf-8")
    (alpha / "linked.jpg").symlink_to(outside)

    with pytest.raises(ValueError, match="outside the Projects source root"):
        MissingSourceFilesProducer(repo_root=tmp_path, paths=paths).run()
