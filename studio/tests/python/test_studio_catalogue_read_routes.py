#!/usr/bin/env python3
"""Studio catalogue read route tests."""

from __future__ import annotations

import json
import tempfile
from http import HTTPStatus
from pathlib import Path

import pytest

from studio_app_server_test_support import catalogue_get_payload, catalogue_post_response, write_repo_marker

def test_catalogue_project_state_route_uses_fixture_source(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        projects_base = Path(tmp_dir) / "source"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        project_dir = projects_base / "projects" / "alpha"
        source_dir.mkdir(parents=True)
        project_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (project_dir / "one.jpg").write_bytes(b"")
        (project_dir / "extra.jpg").write_bytes(b"")
        (source_dir / "works.json").write_text(
            json.dumps(
                {
                    "catalogue_source_works_version": "catalogue_source_works_v1",
                    "works": {
                        "00001": {
                            "title": "One",
                            "status": "draft",
                            "project_folder": "alpha",
                            "project_filename": "one.jpg",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {}}),
            encoding="utf-8",
        )
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))

        health_payload = catalogue_get_payload(repo_root, "/health")
        status, payload = catalogue_post_response(
            repo_root,
            "/project-state-report",
            {"include_subfolders": False},
            dry_run=True,
        )

        assert health_payload["ok"] is True
        assert "project-media" in health_payload["routes"]
        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["dry_run"] is True
        assert payload["written"] is False
        assert payload["summary"]["source_folder_count"] == 1
        assert payload["summary"]["unrepresented_image_count"] == 1

        write_status, write_payload = catalogue_post_response(
            repo_root,
            "/project-state-report",
            {"include_subfolders": False},
            dry_run=False,
        )
        report_path = repo_root / "var/studio/reports/project-state.md"
        assert write_status == HTTPStatus.OK
        assert write_payload["ok"] is True
        assert write_payload["output_path"] == "var/studio/reports/project-state.md"
        assert report_path.exists()
        assert "published:" not in report_path.read_text(encoding="utf-8")

        open_status, open_payload = catalogue_post_response(
            repo_root,
            "/project-state-open-report",
            {"editor": "vscode"},
            dry_run=True,
        )
        assert open_status == HTTPStatus.OK
        assert open_payload["ok"] is True
        assert open_payload["path"] == "var/studio/reports/project-state.md"
        assert open_payload["editor"] == "vscode"

def test_catalogue_read_route_returns_source_payloads() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {"00001": {"work_id": "00001", "title": "One", "status": "draft"}}}),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {"001": {"series_id": "001", "title": "Series", "status": "draft"}}}),
            encoding="utf-8",
        )

        works_payload = catalogue_get_payload(repo_root, "/read", {"key": ["catalogue_works"]})

        assert works_payload["works"]["00001"]["title"] == "One"
        with pytest.raises(ValueError, match="unsupported catalogue read key"):
            catalogue_get_payload(repo_root, "/read", {"key": ["activity_log"]})

def test_catalogue_project_media_route_lists_allowed_project_images(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        projects_base = Path(tmp_dir) / "source"
        projects_root = projects_base / "projects"
        alpha = projects_root / "natural"
        nerve = projects_root / "nerve"
        unnatural = projects_root / "unnatural"
        alpha_subfolder = alpha / "install"
        alpha_subfolder.mkdir(parents=True)
        nerve.mkdir(parents=True)
        unnatural.mkdir(parents=True)
        write_repo_marker(repo_root)
        (alpha / "cover.jpg").write_bytes(b"")
        (alpha / "notes.txt").write_text("not image", encoding="utf-8")
        (alpha / ".hidden.jpg").write_bytes(b"")
        (alpha_subfolder / "detail.png").write_bytes(b"")
        (alpha_subfolder / "deep").mkdir()
        (alpha_subfolder / "deep" / "ignored.jpg").write_bytes(b"")
        (nerve / "nerve.webp").write_bytes(b"")
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))

        folders_payload = catalogue_get_payload(repo_root, "/project-media", {"mode": ["folders"], "q": ["nat"]})
        files_payload = catalogue_get_payload(
            repo_root,
            "/project-media",
            {"mode": ["files"], "project_folder": ["natural"]},
        )
        subfolder_payload = catalogue_get_payload(
            repo_root,
            "/project-media",
            {"mode": ["files"], "project_folder": ["natural"], "project_subfolder": ["install"]},
        )

        assert folders_payload["ok"] is True
        assert [item["project_folder"] for item in folders_payload["project_folders"]] == ["natural"]
        assert [item["project_subfolder"] for item in files_payload["subfolders"]] == ["install"]
        assert [item["filename"] for item in files_payload["files"]] == ["cover.jpg"]
        assert [item["filename"] for item in subfolder_payload["files"]] == ["detail.png"]

        with pytest.raises(ValueError, match="project_subfolder must be a single path segment"):
            catalogue_get_payload(
                repo_root,
                "/project-media",
                {"mode": ["files"], "project_folder": ["natural"], "project_subfolder": ["install/deep"]},
            )
