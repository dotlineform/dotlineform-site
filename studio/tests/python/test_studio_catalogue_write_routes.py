#!/usr/bin/env python3
"""Studio catalogue write route tests."""

from __future__ import annotations

import json
import tempfile
from http import HTTPStatus
from pathlib import Path

from studio_app_server_test_support import REPO_ROOT, catalogue_post_response, studio_catalogue_api, write_repo_marker

def test_catalogue_write_service_routes_are_registered() -> None:
    service_paths = studio_catalogue_api.catalogue_write_service.SERVICE_POST_PATHS
    assert {
        "/bulk-save",
        "/work/create",
        "/work/save",
        "/series/create",
        "/series/save",
        "/delete-preview",
        "/delete-apply",
        "/publication-preview",
        "/publication-apply",
        "/build-preview",
        "/build-apply",
    } <= service_paths

def test_catalogue_delete_preview_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {"00042": {"work_id": "00042", "title": "Draft", "status": "draft", "series_ids": []}}}),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {}}),
            encoding="utf-8",
        )

        status, payload = catalogue_post_response(repo_root, "/delete-preview", {"kind": "work", "id": "42"})

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["kind"] == "work"
        assert payload["id"] == "00042"
        assert payload["preview"]["record"]["work_id"] == "00042"

def test_catalogue_bulk_save_work_dry_run_uses_callable_service_route() -> None:
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
                        "00042": {
                            "work_id": "00042",
                            "title": "Original",
                            "status": "draft",
                            "series_ids": [],
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

        status, payload = catalogue_post_response(
            repo_root,
            "/bulk-save",
            {
                "kind": "works",
                "ids": ["42"],
                "set_fields": {"title": "Bulk Updated"},
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["kind"] == "works"
        assert payload["changed"] is True
        assert payload["changed_ids"] == ["00042"]
        assert payload["records"][0]["record"]["title"] == "Bulk Updated"
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert json.loads((source_dir / "works.json").read_text(encoding="utf-8"))["works"]["00042"]["title"] == "Original"

def test_catalogue_editor_create_work_dry_run_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {}}),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {}}),
            encoding="utf-8",
        )
        registry_target = repo_root / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json"
        registry_target.parent.mkdir(parents=True, exist_ok=True)
        registry_target.write_text((REPO_ROOT / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json").read_text(encoding="utf-8"), encoding="utf-8")

        status, payload = catalogue_post_response(
            repo_root,
            "/work/create",
            {
                "work_id": "42",
                "record": {
                    "title": "Draft Work",
                    "status": "draft",
                    "series_ids": [],
                },
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["work_id"] == "00042"
        assert payload["created"] is True
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert json.loads((source_dir / "works.json").read_text(encoding="utf-8"))["works"] == {}

def test_catalogue_editor_save_work_dry_run_uses_callable_service_route() -> None:
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
                        "00042": {
                            "work_id": "00042",
                            "title": "Original",
                            "status": "draft",
                            "series_ids": [],
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
        registry_target = repo_root / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json"
        registry_target.parent.mkdir(parents=True, exist_ok=True)
        registry_target.write_text((REPO_ROOT / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json").read_text(encoding="utf-8"), encoding="utf-8")

        status, payload = catalogue_post_response(
            repo_root,
            "/work/save",
            {
                "work_id": "42",
                "record": {
                    "title": "Updated",
                },
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["work_id"] == "00042"
        assert payload["changed"] is True
        assert payload["changed_fields"] == ["title"]
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert "build_plan" in payload
        assert json.loads((source_dir / "works.json").read_text(encoding="utf-8"))["works"]["00042"]["title"] == "Original"

def test_catalogue_editor_create_series_dry_run_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {}}),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {}}),
            encoding="utf-8",
        )

        status, payload = catalogue_post_response(
            repo_root,
            "/series/create",
            {
                "series_id": "9",
                "record": {
                    "title": "Draft Series",
                    "status": "draft",
                    "year": "2026",
                    "year_display": "2026",
                },
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["series_id"] == "009"
        assert payload["created"] is True
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert json.loads((source_dir / "series.json").read_text(encoding="utf-8"))["series"] == {}

def test_catalogue_editor_save_series_dry_run_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {}}),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps(
                {
                    "catalogue_source_series_version": "catalogue_source_series_v1",
                    "series": {
                        "009": {
                            "series_id": "009",
                            "title": "Original Series",
                            "status": "draft",
                            "year": "2026",
                            "year_display": "2026",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        registry_target = repo_root / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json"
        registry_target.parent.mkdir(parents=True, exist_ok=True)
        registry_target.write_text((REPO_ROOT / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json").read_text(encoding="utf-8"), encoding="utf-8")

        status, payload = catalogue_post_response(
            repo_root,
            "/series/save",
            {
                "series_id": "9",
                "record": {
                    "title": "Updated Series",
                },
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["series_id"] == "009"
        assert payload["changed"] is True
        assert payload["changed_fields"] == ["title"]
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert "build_plan" in payload
        assert json.loads((source_dir / "series.json").read_text(encoding="utf-8"))["series"]["009"]["title"] == "Original Series"
