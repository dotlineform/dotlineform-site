#!/usr/bin/env python3
"""Verify catalogue work-detail section create service."""

from __future__ import annotations

import sys
from pathlib import Path

from catalogue_factory import read_json, write_json


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio/shared/python"
for candidate in (SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from catalogue.catalogue_build_media import PROJECTS_BASE_DIR_ENV_NAME  # noqa: E402
from catalogue import catalogue_detail_section_service as detail_section_service  # noqa: E402
from catalogue.catalogue_service_context import build_catalogue_write_context  # noqa: E402
from catalogue.catalogue_source import load_json_file, write_work_detail_payloads  # noqa: E402


def write_work_details_source(repo_root: Path, payload: dict) -> Path:
    source_dir = repo_root / "studio/data/canonical/catalogue"
    write_work_detail_payloads(
        source_dir,
        payload.get("work_detail_sections") or {},
        payload.get("work_details") or {},
    )
    return source_dir / "work_details"


def read_work_details_source(repo_root: Path) -> dict:
    return load_json_file(repo_root / "studio/data/canonical/catalogue/work_details")


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
                    "media_version": 1,
                    "title": "birth of forms",
                    "year": 2026,
                    "year_display": "2026",
                }
            },
        },
    )
    (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
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
    env_path = repo_root / ".env.local"
    env_path.write_text(f"{PROJECTS_BASE_DIR_ENV_NAME}={projects_base}\n", encoding="utf-8")
    return repo_root, projects_base


def stub_lookup_refresh(monkeypatch) -> None:
    monkeypatch.setattr(detail_section_service, "refresh_lookup_payloads", lambda _context: {})


def test_create_detail_section_writes_section_and_records(tmp_path: Path, monkeypatch) -> None:
    repo_root, _projects_base = prepare_repo(tmp_path)
    context = build_catalogue_write_context(repo_root)
    build_calls: list[dict[str, object]] = []

    def fake_build_operation(_context, **kwargs):
        build_calls.append(dict(kwargs))
        return True, {
            "completed_at_utc": "2026-01-01T00:00:00Z",
            "media": {"generated": {"work_details": [kwargs["detail_uid"]]}},
        }

    monkeypatch.setattr(detail_section_service, "run_build_operation", fake_build_operation)
    stub_lookup_refresh(monkeypatch)

    payload = detail_section_service.create_detail_section_payload(
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
    assert payload["build_requested"] is True
    assert payload["build"]["ok"] is True
    assert [call["detail_uid"] for call in build_calls] == ["00782-001", "00782-002"]

    source = read_work_details_source(repo_root)
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
    assert first_detail["media_version"] == 1
    assert first_detail["section_id"] == "00782-1"
    assert first_detail["title"] == "detail-01"
    assert first_detail["work_id"] == "00782"
    if "width_px" in first_detail:
        assert isinstance(first_detail["width_px"], int)
    if "height_px" in first_detail:
        assert isinstance(first_detail["height_px"], int)
    assert source["work_details"]["00782-002"]["title"] == "detail-02"

    duplicate_payload = detail_section_service.create_detail_section_payload(
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
        detail_section_service.create_detail_section_payload(
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


def test_save_detail_section_updates_title_sort_and_compact_order(tmp_path: Path, monkeypatch) -> None:
    repo_root, _projects_base = prepare_repo(tmp_path)
    write_work_details_source(
        repo_root,
        {
            "header": {"schema": "catalogue_source_work_details_v2", "section_count": 3, "count": 3},
            "work_detail_sections": {
                "00782-1": {
                    "section_id": "00782-1",
                    "work_id": "00782",
                    "details_subfolder": "alpha",
                    "section_title": "alpha",
                    "section_order": 1,
                },
                "00782-2": {
                    "section_id": "00782-2",
                    "work_id": "00782",
                    "details_subfolder": "beta",
                    "section_title": "beta",
                    "section_order": 2,
                },
                "00782-3": {
                    "section_id": "00782-3",
                    "work_id": "00782",
                    "details_subfolder": "gamma",
                    "section_title": "gamma",
                    "section_order": 3,
                },
            },
            "work_details": {
                "00782-001": {
                    "detail_uid": "00782-001",
                    "work_id": "00782",
                    "detail_id": "001",
                    "section_id": "00782-1",
                    "project_filename": "alpha.jpg",
                    "media_version": 1,
                    "title": "Alpha",
                },
                "00782-002": {
                    "detail_uid": "00782-002",
                    "work_id": "00782",
                    "detail_id": "002",
                    "section_id": "00782-2",
                    "project_filename": "beta.jpg",
                    "media_version": 1,
                    "title": "Beta",
                },
                "00782-003": {
                    "detail_uid": "00782-003",
                    "work_id": "00782",
                    "detail_id": "003",
                    "section_id": "00782-3",
                    "project_filename": "gamma.jpg",
                    "media_version": 1,
                    "title": "Gamma",
                },
            },
        },
    )
    before_details = read_work_details_source(repo_root)["work_details"]
    build_calls: list[dict[str, object]] = []

    def fake_build_operation(_context, **kwargs):
        build_calls.append(dict(kwargs))
        return True, {"completed_at_utc": "2026-01-01T00:00:00Z"}

    monkeypatch.setattr(detail_section_service, "run_build_operation", fake_build_operation)
    stub_lookup_refresh(monkeypatch)

    payload = detail_section_service.save_detail_section_payload(
        build_catalogue_write_context(repo_root),
        {
            "work_id": "00782",
            "section_id": "00782-1",
            "section_title": "omega",
            "section_position": 3,
            "detail_sort": "title",
        },
    )

    assert payload["ok"] is True
    assert payload["changed"] is True
    assert payload["section"]["section_title"] == "omega"
    assert payload["section"]["detail_sort"] == "title"
    assert payload["build_requested"] is True
    assert [call["detail_uid"] for call in build_calls] == [""]

    source = read_work_details_source(repo_root)
    sections = source["work_detail_sections"]
    assert sections["00782-2"]["section_order"] == 1
    assert sections["00782-3"]["section_order"] == 2
    assert sections["00782-1"]["section_order"] == 3
    assert sections["00782-1"]["section_title"] == "omega"
    assert sections["00782-1"]["detail_sort"] == "title"
    assert source["work_details"] == before_details


def test_save_detail_section_single_section_omits_default_sort_and_keeps_details(tmp_path: Path, monkeypatch) -> None:
    repo_root, _projects_base = prepare_repo(tmp_path)
    write_work_details_source(
        repo_root,
        {
            "header": {"schema": "catalogue_source_work_details_v2", "section_count": 1, "count": 1},
            "work_detail_sections": {
                "00782-1": {
                    "section_id": "00782-1",
                    "work_id": "00782",
                    "details_subfolder": "details",
                    "section_title": "details",
                    "detail_sort": "title",
                },
            },
            "work_details": {
                "00782-001": {
                    "detail_uid": "00782-001",
                    "work_id": "00782",
                    "detail_id": "001",
                    "section_id": "00782-1",
                    "project_filename": "detail-001.jpg",
                    "media_version": 1,
                    "title": "Detail",
                },
            },
        },
    )
    before_details = read_work_details_source(repo_root)["work_details"]
    build_calls: list[dict[str, object]] = []

    def fake_build_operation(_context, **kwargs):
        build_calls.append(dict(kwargs))
        return True, {"completed_at_utc": "2026-01-01T00:00:00Z"}

    monkeypatch.setattr(detail_section_service, "run_build_operation", fake_build_operation)
    stub_lookup_refresh(monkeypatch)

    payload = detail_section_service.save_detail_section_payload(
        build_catalogue_write_context(repo_root),
        {
            "work_id": "00782",
            "section_id": "00782-1",
            "section_title": "details updated",
            "section_position": 1,
            "detail_sort": "detail_id",
        },
    )

    assert payload["ok"] is True
    assert payload["changed"] is True
    assert [call["detail_uid"] for call in build_calls] == [""]

    source = read_work_details_source(repo_root)
    section = source["work_detail_sections"]["00782-1"]
    assert section == {
        "details_subfolder": "details",
        "section_id": "00782-1",
        "section_title": "details updated",
        "work_id": "00782",
    }
    assert source["work_details"] == before_details


def test_save_detail_section_noop_does_not_rebuild(tmp_path: Path, monkeypatch) -> None:
    repo_root, _projects_base = prepare_repo(tmp_path)
    source_payload = {
        "header": {"schema": "catalogue_source_work_details_v2", "section_count": 1, "count": 1},
        "work_detail_sections": {
            "00782-1": {
                "section_id": "00782-1",
                "work_id": "00782",
                "details_subfolder": "details",
                "section_title": "details",
                "detail_sort": "title",
            },
        },
        "work_details": {
            "00782-001": {
                "detail_uid": "00782-001",
                "work_id": "00782",
                "detail_id": "001",
                "section_id": "00782-1",
                "project_filename": "detail-001.jpg",
                "media_version": 1,
                "title": "Detail",
            },
        },
    }
    write_work_details_source(repo_root, source_payload)
    build_calls: list[dict[str, object]] = []

    def fake_build_operation(_context, **kwargs):
        build_calls.append(dict(kwargs))
        return True, {"completed_at_utc": "2026-01-01T00:00:00Z"}

    monkeypatch.setattr(detail_section_service, "run_build_operation", fake_build_operation)

    payload = detail_section_service.save_detail_section_payload(
        build_catalogue_write_context(repo_root),
        {
            "work_id": "00782",
            "section_id": "00782-1",
            "section_title": "details",
            "section_position": 1,
            "detail_sort": "title",
        },
    )

    assert payload["ok"] is True
    assert payload["changed"] is False
    assert "build_requested" not in payload
    assert build_calls == []
    assert read_work_details_source(repo_root)["work_detail_sections"] == source_payload["work_detail_sections"]
    assert read_work_details_source(repo_root)["work_details"] == source_payload["work_details"]
