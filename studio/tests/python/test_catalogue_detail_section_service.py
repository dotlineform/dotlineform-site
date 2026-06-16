#!/usr/bin/env python3
"""Verify catalogue work-detail section create service."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio/shared/python"
for candidate in (SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from catalogue.catalogue_build_media import PROJECTS_BASE_DIR_ENV_NAME  # noqa: E402
from catalogue.catalogue_detail_section_service import create_detail_section_payload  # noqa: E402
from catalogue.catalogue_service_context import build_catalogue_write_context  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    source_dir = repo_root / "studio/data/canonical/catalogue"
    projects_base = tmp_path / "projects-base"
    detail_dir = projects_base / "projects/birth/details"
    detail_dir.mkdir(parents=True)
    (detail_dir / "detail-01.jpg").write_bytes(b"image")
    (detail_dir / "detail-02.png").write_bytes(b"image")
    (detail_dir / ".hidden.jpg").write_bytes(b"image")
    (detail_dir / "notes.txt").write_text("not an image", encoding="utf-8")

    write_json(
        source_dir / "works.json",
        {
            "header": {"schema": "catalogue_source_works_v1", "count": 1},
            "works": {
                "00782": {
                    "work_id": "00782",
                    "status": "published",
                    "series_ids": ["009"],
                    "project_folder": "birth",
                    "project_filename": "cover.jpg",
                    "title": "birth of forms",
                    "year": 2026,
                    "year_display": "2026",
                }
            },
        },
    )
    write_json(
        source_dir / "work_details.json",
        {
            "header": {"schema": "catalogue_source_work_details_v2", "section_count": 0, "count": 0},
            "work_detail_sections": {},
            "work_details": {},
        },
    )
    write_json(
        source_dir / "series.json",
        {
            "header": {"schema": "catalogue_source_series_v1", "count": 1},
            "series": {
                "009": {
                    "series_id": "009",
                    "title": "Series",
                    "status": "published",
                    "year": 2026,
                    "year_display": "2026",
                    "primary_work_id": "00782",
                }
            },
        },
    )
    write_json(source_dir / "meta.json", {"header": {"schema": "catalogue_source_meta_v1"}, "meta": {}})
    env_path = repo_root / "var/local/site.env"
    env_path.parent.mkdir(parents=True)
    env_path.write_text(f"{PROJECTS_BASE_DIR_ENV_NAME}={projects_base}\n", encoding="utf-8")
    return repo_root, projects_base


def test_create_detail_section_writes_section_and_records(tmp_path: Path) -> None:
    repo_root, _projects_base = prepare_repo(tmp_path)
    context = build_catalogue_write_context(repo_root)

    payload = create_detail_section_payload(
        context,
        {
            "work_id": "00782",
            "project_folder": "birth",
            "project_subfolder": "details",
            "filenames": ["detail-01.jpg", "detail-02.png"],
        },
    )

    assert payload["ok"] is True
    assert payload["changed"] is True
    assert payload["section_id"] == "00782-1"
    assert payload["created_detail_uids"] == ["00782-001", "00782-002"]
    assert payload["created_count"] == 2

    source = read_json(repo_root / "studio/data/canonical/catalogue/work_details.json")
    assert source["header"]["section_count"] == 1
    assert source["header"]["count"] == 2
    assert source["work_detail_sections"]["00782-1"] == {
        "details_subfolder": "details",
        "section_id": "00782-1",
        "section_title": "details",
        "work_id": "00782",
    }
    first_detail = source["work_details"]["00782-001"]
    assert first_detail["detail_id"] == "001"
    assert first_detail["detail_uid"] == "00782-001"
    assert first_detail["project_filename"] == "detail-01.jpg"
    assert first_detail["section_id"] == "00782-1"
    assert first_detail["title"] == "detail-01"
    assert first_detail["work_id"] == "00782"
    if "width_px" in first_detail:
        assert isinstance(first_detail["width_px"], int)
    if "height_px" in first_detail:
        assert isinstance(first_detail["height_px"], int)
    assert source["work_details"]["00782-002"]["title"] == "detail-02"

    duplicate_payload = create_detail_section_payload(
        context,
        {
            "work_id": "00782",
            "project_folder": "birth",
            "project_subfolder": "details",
            "filenames": ["detail-01.jpg"],
        },
    )
    assert duplicate_payload["ok"] is True
    assert duplicate_payload["changed"] is False
    assert duplicate_payload["reason"] == "section_exists"
    assert duplicate_payload["section_id"] == "00782-1"


def test_create_detail_section_rejects_missing_file(tmp_path: Path) -> None:
    repo_root, _projects_base = prepare_repo(tmp_path)
    context = build_catalogue_write_context(repo_root)

    try:
        create_detail_section_payload(
            context,
            {
                "work_id": "00782",
                "project_folder": "birth",
                "project_subfolder": "details",
                "filenames": ["missing.jpg"],
            },
        )
    except ValueError as exc:
        assert "selected file(s) not found" in str(exc)
        return
    raise AssertionError("expected missing file to be rejected")
