#!/usr/bin/env python3
"""Focused checks for catalogue media-version promotion."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from catalogue.catalogue_media_version import finalize_catalogue_media_version  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    source = repo / "studio/data/canonical/catalogue"
    write_json(
        source / "works.json",
        {
            "header": {"schema": "catalogue_source_works_v1", "count": 1},
            "works": {
                "00001": {
                    "work_id": "00001",
                    "status": "published",
                    "series_ids": [],
                    "project_folder": "alpha",
                    "project_filename": "alpha.jpg",
                    "media_version": 1,
                    "title": "Alpha",
                }
            },
        },
    )
    write_json(
        source / "series.json",
        {"header": {"schema": "catalogue_source_series_v1", "count": 0}, "series": {}},
    )
    write_json(
        source / "work_details/00001.json",
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
                            "media_version": 1,
                            "title": "Detail",
                        }
                    ],
                }
            ],
        },
    )
    return repo


def successful_build(command, repo_root, env):
    assert "--only" in command
    assert "work-json" in command
    assert "--write" in command
    assert "--refresh-published" not in command
    assert "--skip-source-dimension-refresh" in command
    return 0, "focused build completed", ""


def test_work_upload_advances_confirmed_version(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = finalize_catalogue_media_version(
        repo,
        kind="works",
        item_id="00001",
        advance=True,
        build_runner=successful_build,
    )
    work = json.loads((repo / "studio/data/canonical/catalogue/works.json").read_text())["works"]["00001"]
    assert result.previous_version == 1
    assert result.media_version == 2
    assert result.advanced is True
    assert work["media_version"] == 2


def test_matching_rerun_rebuilds_without_advancing(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = finalize_catalogue_media_version(
        repo,
        kind="work_details",
        item_id="00001-001",
        advance=False,
        build_runner=successful_build,
    )
    payload = json.loads((repo / "studio/data/canonical/catalogue/work_details/00001.json").read_text())
    detail = payload["detail_sections"][0]["details"][0]
    assert result.previous_version == 1
    assert result.media_version == 1
    assert result.advanced is False
    assert detail["media_version"] == 1


def test_detail_upload_advances_only_the_nested_detail_version(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = finalize_catalogue_media_version(
        repo,
        kind="work_details",
        item_id="00001-001",
        advance=True,
        build_runner=successful_build,
    )
    work = json.loads((repo / "studio/data/canonical/catalogue/works.json").read_text())["works"]["00001"]
    payload = json.loads((repo / "studio/data/canonical/catalogue/work_details/00001.json").read_text())
    detail = payload["detail_sections"][0]["details"][0]
    assert result.work_id == "00001"
    assert result.previous_version == 1
    assert result.media_version == 2
    assert detail["media_version"] == 2
    assert work["media_version"] == 1
