#!/usr/bin/env python3
"""Studio catalogue read route tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from studio_app_server_test_support import catalogue_get_payload, catalogue_post_response, write_repo_marker


@pytest.mark.parametrize("api_path", ["/project-state-report", "/project-state-open-report"])
def test_retired_project_state_routes_are_not_dispatched(api_path: str) -> None:
    with pytest.raises(FileNotFoundError, match="Unknown catalogue API route"):
        catalogue_post_response(Path.cwd(), api_path, {}, dry_run=True)

def test_catalogue_read_route_returns_source_payloads() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (source_dir / "works.json").write_text(
            json.dumps(
                {
                    "catalogue_source_works_version": "catalogue_source_works_v1",
                    "works": {
                        "00001": {
                            "work_id": "00001",
                            "title": "Draft One",
                            "status": "draft",
                            "series_ids": ["001"],
                            "project_folder": "Alpha",
                        },
                        "00002": {
                            "work_id": "00002",
                            "title": "Published A",
                            "status": "published",
                            "series_ids": ["001"],
                            "project_folder": "Beta",
                        },
                        "00003": {
                            "work_id": "00003",
                            "title": "Published B",
                            "status": "published",
                            "series_ids": ["001"],
                            "project_folder": "Alpha",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps(
                {
                    "catalogue_source_series_version": "catalogue_source_series_v1",
                    "series": {
                        "001": {
                            "series_id": "001",
                            "title": "Series",
                            "series_type": "primary",
                            "status": "published",
                            "primary_work_id": "00002",
                            "sort_fields": "title,work_id",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        works_payload = catalogue_get_payload(repo_root, "/read", {"key": ["catalogue_works"]})
        series_payload = catalogue_get_payload(repo_root, "/read", {"key": ["catalogue_series"]})
        exact_series_payload = catalogue_get_payload(
            repo_root,
            "/read",
            {"key": ["catalogue_lookup_series_base"], "record_id": ["001"]},
        )
        exact_work_payload = catalogue_get_payload(
            repo_root,
            "/read",
            {"key": ["catalogue_work_record"], "record_id": ["00002"]},
        )

        assert works_payload["works"]["00001"]["title"] == "Draft One"
        assert series_payload["series"]["001"]["title"] == "Series"
        assert exact_series_payload["header"]["schema"] == "studio_catalogue_lookup_series_record_v2"
        assert exact_series_payload["series"]["series_id"] == "001"
        assert exact_series_payload["ordered_published_work_ids"] == ["00002", "00003"]
        assert exact_series_payload["project_folders"] == ["Alpha", "Beta"]
        assert [row["work_id"] for row in exact_series_payload["member_works"]] == ["00001", "00002", "00003"]
        assert exact_work_payload["work"]["work_id"] == "00002"
        with pytest.raises(KeyError, match="series_id not found: 999"):
            catalogue_get_payload(
                repo_root,
                "/read",
                {"key": ["catalogue_lookup_series_base"], "record_id": ["999"]},
            )
        with pytest.raises(ValueError, match="unsupported catalogue read key"):
            catalogue_get_payload(repo_root, "/read", {"key": ["unknown_key"]})

def test_catalogue_project_media_route_lists_allowed_project_images(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        projects_base = Path(tmp_dir) / "source"
        projects_root = projects_base / "projects"
        alpha = projects_root / "natural"
        nerve = projects_root / "nerve"
        unnatural = projects_root / "unnatural"
        processing_root = projects_base / "processing"
        ink_engine = processing_root / "ink-engine"
        alpha_subfolder = alpha / "install"
        alpha_subfolder.mkdir(parents=True)
        nerve.mkdir(parents=True)
        unnatural.mkdir(parents=True)
        ink_engine.mkdir(parents=True)
        write_repo_marker(repo_root)
        (alpha / "cover.jpg").write_bytes(b"")
        (alpha / "notes.txt").write_text("not image", encoding="utf-8")
        (alpha / ".hidden.jpg").write_bytes(b"")
        (alpha_subfolder / "detail.png").write_bytes(b"")
        (alpha_subfolder / "deep").mkdir()
        (alpha_subfolder / "deep" / "ignored.jpg").write_bytes(b"")
        (nerve / "nerve.webp").write_bytes(b"")
        (ink_engine / "glyph.jpg").write_bytes(b"")
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))

        health_payload = catalogue_get_payload(repo_root, "/health")

        sources_payload = catalogue_get_payload(repo_root, "/project-media", {"mode": ["sources"]})
        folders_payload = catalogue_get_payload(repo_root, "/project-media", {"mode": ["folders"], "q": ["nat"]})
        processing_folders_payload = catalogue_get_payload(
            repo_root,
            "/project-media",
            {"mode": ["folders"], "media_source_id": ["processing"]},
        )
        processing_files_payload = catalogue_get_payload(
            repo_root,
            "/project-media",
            {"mode": ["files"], "media_source_id": ["processing"], "project_folder": ["ink-engine"]},
        )
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

        assert sources_payload["default_media_source_id"] == "projects"
        assert sources_payload["media_source_ids"] == ["projects", "processing"]
        assert folders_payload["ok"] is True
        assert folders_payload["media_source_id"] == "projects"
        assert [item["project_folder"] for item in folders_payload["project_folders"]] == ["natural"]
        assert [item["project_subfolder"] for item in files_payload["subfolders"]] == ["install"]
        assert [item["filename"] for item in files_payload["files"]] == ["cover.jpg"]
        assert [item["filename"] for item in subfolder_payload["files"]] == ["detail.png"]
        assert [item["project_folder"] for item in processing_folders_payload["project_folders"]] == ["ink-engine"]
        assert [item["filename"] for item in processing_files_payload["files"]] == ["glyph.jpg"]
        assert "project-media" in health_payload["routes"]
        assert "project-state-report" not in health_payload["routes"]
        assert "project-state-open-report" not in health_payload["routes"]

        with pytest.raises(ValueError, match="project_subfolder must be a single path segment"):
            catalogue_get_payload(
                repo_root,
                "/project-media",
                {"mode": ["files"], "project_folder": ["natural"], "project_subfolder": ["install/deep"]},
            )
        with pytest.raises(ValueError, match="unknown Work media source identity"):
            catalogue_get_payload(
                repo_root,
                "/project-media",
                {"mode": ["folders"], "media_source_id": ["unknown"]},
            )
