#!/usr/bin/env python3
"""Focused checks for the Uncataloged Files producer."""

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

from docs_local_links import encode_relative_target  # noqa: E402
from docs_uncataloged_files import (  # noqa: E402
    REPORT_SCHEMA_VERSION,
    UncatalogedFilesPaths,
    UncatalogedFilesProducer,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def work(
    work_id: str,
    folder: str,
    filename: str,
    *,
    subfolder: str = "",
) -> dict[str, object]:
    record: dict[str, object] = {
        "work_id": work_id,
        "title": f"Work {work_id}",
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


def write_detail_section(source_dir: Path) -> None:
    write_json(
        source_dir / "work_details/00001.json",
        {
            "header": {
                "schema": "catalogue_source_work_detail_record_v1",
                "work_id": "00001",
                "section_count": 1,
                "count": 1,
            },
            "work_id": "00001",
            "detail_sections": [
                {
                    "section_id": "00001-1",
                    "details_subfolder": "details",
                    "section_title": "Details",
                    "details": [
                        {
                            "detail_uid": "00001-001",
                            "detail_id": "001",
                            "project_filename": "detail.jpg",
                            "title": "Detail",
                        }
                    ],
                }
            ],
        },
    )


def fixture_paths(tmp_path: Path) -> tuple[UncatalogedFilesPaths, Path, Path]:
    projects_base = tmp_path / "external"
    projects_root = projects_base / "projects"
    source_dir = tmp_path / "studio/data/canonical/catalogue"
    projects_root.mkdir(parents=True)
    return (
        UncatalogedFilesPaths(
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


def test_report_lists_direct_ordinary_uncataloged_files_only(tmp_path: Path) -> None:
    paths, projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(
        source_dir,
        {
            "00001": work("00001", "alpha", "primary.jpg"),
            "00002": work("00002", "alpha", "nested.jpg", subfolder="ink"),
            "00003": work("00003", "alpha", "primary.jpg"),
            "00004": work("00004", "missing", "absent.jpg"),
            "00005": {
                "work_id": "00005",
                "title": "Incomplete",
                "status": "draft",
                "series_ids": [],
                "project_folder": "alpha",
            },
            "00006": work("00006", "alpha", "detail-primary.jpg", subfolder="details"),
            "00007": work("00007", "alpha", "moiré.jpg"),
        },
    )
    write_detail_section(source_dir)

    alpha = projects_root / "alpha"
    ink = alpha / "ink"
    details = alpha / "details"
    unrepresented = projects_root / "unrepresented"
    for directory in (alpha, ink, details, unrepresented):
        directory.mkdir(parents=True, exist_ok=True)
    (alpha / "primary.jpg").write_text("primary", encoding="utf-8")
    (alpha / "notes.pdf").write_text("notes", encoding="utf-8")
    (alpha / "sound.wav").write_text("sound", encoding="utf-8")
    (alpha / "README").write_text("readme", encoding="utf-8")
    (alpha / ".hidden.txt").write_text("hidden", encoding="utf-8")
    (alpha / "named-like-file.docx").mkdir()
    (ink / "nested.jpg").write_text("nested", encoding="utf-8")
    (ink / "working.docx").write_text("working", encoding="utf-8")
    (details / "detail-primary.jpg").write_text("primary detail", encoding="utf-8")
    (details / "working.psd").write_text("excluded detail", encoding="utf-8")
    (unrepresented / "orphan.xlsx").write_text("unrepresented", encoding="utf-8")

    unicode_actual = alpha / "moire\u0301.jpg"
    unicode_expected = alpha / "moiré.jpg"
    create_unicode_alias(unicode_actual, unicode_expected)

    payload = UncatalogedFilesProducer(repo_root=tmp_path, paths=paths).run()

    assert set(payload) == {"report"}
    assert set(payload["report"]) == {"schema_version", "rows"}
    assert payload["report"]["schema_version"] == REPORT_SCHEMA_VERSION
    assert payload["report"]["rows"] == [
        {
            "folder": "alpha",
            "file_name": "notes.pdf",
            "local_target": encode_relative_target("projects/alpha/notes.pdf"),
        },
        {
            "folder": "alpha",
            "file_name": "README",
            "local_target": encode_relative_target("projects/alpha/README"),
        },
        {
            "folder": "alpha",
            "file_name": "sound.wav",
            "local_target": encode_relative_target("projects/alpha/sound.wav"),
        },
        {
            "folder": "alpha/ink",
            "file_name": "working.docx",
            "local_target": encode_relative_target("projects/alpha/ink/working.docx"),
        },
    ]


def test_report_rejects_complete_work_paths_with_parent_traversal(tmp_path: Path) -> None:
    paths, _projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(
        source_dir,
        {
            "00001": work(
                "00001",
                "alpha",
                "outside.jpg",
                subfolder="../outside",
            )
        },
    )

    with pytest.raises(ValueError, match="project_subfolder"):
        UncatalogedFilesProducer(repo_root=tmp_path, paths=paths).run()


def test_report_rejects_a_represented_directory_resolving_outside_root(tmp_path: Path) -> None:
    paths, projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(source_dir, {"00001": work("00001", "linked", "primary.jpg")})
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "primary.jpg").write_text("outside", encoding="utf-8")
    (projects_root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="outside the Projects source root"):
        UncatalogedFilesProducer(repo_root=tmp_path, paths=paths).run()


def test_report_rejects_a_direct_file_resolving_outside_root(tmp_path: Path) -> None:
    paths, projects_root, source_dir = fixture_paths(tmp_path)
    write_catalogue(source_dir, {"00001": work("00001", "alpha", "primary.jpg")})
    alpha = projects_root / "alpha"
    alpha.mkdir()
    (alpha / "primary.jpg").write_text("primary", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (alpha / "linked.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="outside the Projects source root"):
        UncatalogedFilesProducer(repo_root=tmp_path, paths=paths).run()
