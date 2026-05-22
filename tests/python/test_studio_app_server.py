#!/usr/bin/env python3
"""Focused checks for the local Studio app server."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.studio import studio_docs_api  # noqa: E402
from scripts.studio.studio_analytics_api import analytics_get_payload, analytics_post_response  # noqa: E402
from scripts.studio.studio_audit_api import audit_get_payload, audit_post_response  # noqa: E402
from scripts.studio.studio_app_config import runtime_config  # noqa: E402
from scripts.studio.studio_catalogue_api import catalogue_get_payload, catalogue_post_response  # noqa: E402


def test_runtime_config_exposes_adapter_contract() -> None:
    original_env = {key: os.environ.get(key) for key in ("JEKYLL_HOST", "JEKYLL_PORT", "PUBLIC_SITE_PREVIEW_BASE", "PRODUCTION_SITE_BASE")}
    os.environ["JEKYLL_HOST"] = "127.0.0.1"
    os.environ["JEKYLL_PORT"] = "4000"
    os.environ.pop("PUBLIC_SITE_PREVIEW_BASE", None)
    os.environ.pop("PRODUCTION_SITE_BASE", None)
    try:
        payload = runtime_config(REPO_ROOT, "test-version")
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    runtime = payload["app"]["runtime"]

    assert runtime["host"] == "local-studio-app"
    assert runtime["asset_version"] == "test-version"
    assert runtime["routes"]["runtime_config"] == "/studio/runtime-config.json"
    assert runtime["sites"]["public_preview"]["base"] == "http://127.0.0.1:4000"
    assert runtime["sites"]["production"]["base"] == "https://dotlineform.com"
    assert any(view["id"] == "studio_catalogue" and view["path"] == "/studio/catalogue/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "studio_analytics" and view["path"] == "/studio/analytics/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "tag_registry" and view["path"] == "/studio/analytics/tag-registry/" for view in runtime["views"])
    assert any(view["id"] == "tag_aliases" and view["path"] == "/studio/analytics/tag-aliases/" for view in runtime["views"])
    assert any(view["id"] == "series_tags" and view["path"] == "/studio/analytics/series-tags/" for view in runtime["views"])
    assert any(view["id"] == "series_tag_editor" and view["path"] == "/studio/analytics/series-tag-editor/" for view in runtime["views"])
    assert any(view["id"] == "studio_audits" and view["path"] == "/studio/audits/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "project_state" and view["path"] == "/studio/project-state/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "thumbnail_quality" and view["path"] == "/studio/thumbnail-quality/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "bulk_add_work" and view["path"] == "/studio/bulk-add-work/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "activity" and view["path"] == "/studio/activity/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_field_registry" and view["path"] == "/studio/catalogue-field-registry/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_status" and view["path"] == "/studio/catalogue-status/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "studio_works" and view["path"] == "/studio/studio-works/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_series_editor" and view["path"] == "/studio/catalogue-series/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_work_editor" and view["path"] == "/studio/catalogue-work/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_work_detail_editor" and view["path"] == "/studio/catalogue-work-detail/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_moment_editor" and view["path"] == "/studio/catalogue-moment/?mode=manage" for view in runtime["views"])
    assert "series_tag_editor" not in runtime["navigation"]["primary"]
    assert runtime["services"]["analytics"]["tag_groups"] == "/studio/api/analytics/tag-groups"
    assert runtime["services"]["analytics"]["tag_registry"] == "/studio/api/analytics/tag-registry"
    assert runtime["services"]["analytics"]["tag_aliases"] == "/studio/api/analytics/tag-aliases"
    assert runtime["services"]["analytics"]["tag_assignments"] == "/studio/api/analytics/tag-assignments"
    assert runtime["services"]["analytics"]["delete_tag_alias"] == "/studio/api/analytics/delete-tag-alias"
    assert runtime["services"]["analytics"]["demote_tag_preview"] == "/studio/api/analytics/demote-tag-preview"
    assert runtime["services"]["analytics"]["demote_tag"] == "/studio/api/analytics/demote-tag"
    assert runtime["services"]["analytics"]["save_tags"] == "/studio/api/analytics/save-tags"
    assert runtime["services"]["analytics"]["import_tag_assignments_preview"] == "/studio/api/analytics/import-tag-assignments-preview"
    assert runtime["services"]["analytics"]["import_tag_assignments"] == "/studio/api/analytics/import-tag-assignments"
    assert runtime["services"]["analytics"]["import_tag_aliases"] == "/studio/api/analytics/import-tag-aliases"
    assert runtime["services"]["analytics"]["import_tag_registry"] == "/studio/api/analytics/import-tag-registry"
    assert runtime["services"]["analytics"]["mutate_tag_alias_preview"] == "/studio/api/analytics/mutate-tag-alias-preview"
    assert runtime["services"]["analytics"]["mutate_tag_alias"] == "/studio/api/analytics/mutate-tag-alias"
    assert runtime["services"]["analytics"]["mutate_tag_preview"] == "/studio/api/analytics/mutate-tag-preview"
    assert runtime["services"]["analytics"]["mutate_tag"] == "/studio/api/analytics/mutate-tag"
    assert runtime["services"]["analytics"]["promote_tag_alias_preview"] == "/studio/api/analytics/promote-tag-alias-preview"
    assert runtime["services"]["analytics"]["promote_tag_alias"] == "/studio/api/analytics/promote-tag-alias"
    assert runtime["services"]["docs"]["base"] == "/studio/api/docs"
    assert runtime["services"]["audits"]["base"] == "/studio/api/audits"
    assert runtime["services"]["audits"]["audits"] == "/studio/api/audits/audits"
    assert runtime["services"]["audits"]["run"] == "/studio/api/audits/audits/run"
    assert runtime["services"]["catalogue"]["base"] == "/studio/api/catalogue"
    assert runtime["services"]["catalogue"]["read"] == "/studio/api/catalogue/read"
    assert runtime["services"]["catalogue"]["bulk_save"] == "/studio/api/catalogue/bulk-save"
    assert runtime["services"]["catalogue"]["delete_preview"] == "/studio/api/catalogue/delete-preview"
    assert runtime["services"]["catalogue"]["delete_apply"] == "/studio/api/catalogue/delete-apply"
    assert runtime["services"]["catalogue"]["publication_preview"] == "/studio/api/catalogue/publication-preview"
    assert runtime["services"]["catalogue"]["publication_apply"] == "/studio/api/catalogue/publication-apply"
    assert runtime["services"]["catalogue"]["create_work"] == "/studio/api/catalogue/work/create"
    assert runtime["services"]["catalogue"]["save_work"] == "/studio/api/catalogue/work/save"
    assert runtime["services"]["catalogue"]["create_work_detail"] == "/studio/api/catalogue/work-detail/create"
    assert runtime["services"]["catalogue"]["save_work_detail"] == "/studio/api/catalogue/work-detail/save"
    assert runtime["services"]["catalogue"]["import_preview"] == "/studio/api/catalogue/import-preview"
    assert runtime["services"]["catalogue"]["import_apply"] == "/studio/api/catalogue/import-apply"
    assert runtime["services"]["catalogue"]["create_series"] == "/studio/api/catalogue/series/create"
    assert runtime["services"]["catalogue"]["save_series"] == "/studio/api/catalogue/series/save"
    assert runtime["services"]["catalogue"]["build_preview"] == "/studio/api/catalogue/build-preview"
    assert runtime["services"]["catalogue"]["build_apply"] == "/studio/api/catalogue/build-apply"
    assert runtime["services"]["catalogue"]["prose_import_preview"] == "/studio/api/catalogue/prose/import-preview"
    assert runtime["services"]["catalogue"]["prose_import_apply"] == "/studio/api/catalogue/prose/import-apply"
    assert runtime["services"]["catalogue"]["moment_import_preview"] == "/studio/api/catalogue/moment/import-preview"
    assert runtime["services"]["catalogue"]["moment_import_apply"] == "/studio/api/catalogue/moment/import-apply"
    assert runtime["services"]["catalogue"]["moment_preview"] == "/studio/api/catalogue/moment/preview"
    assert runtime["services"]["catalogue"]["save_moment"] == "/studio/api/catalogue/moment/save"
    assert runtime["services"]["catalogue"]["project_state_report"] == "/studio/api/catalogue/project-state-report"
    assert runtime["services"]["catalogue"]["thumbnail_quality_preview"] == "/studio/api/catalogue/thumbnail-quality-preview"
    assert "tag_groups" not in runtime["data_paths"]["studio"]
    assert "tag_registry" not in runtime["data_paths"]["studio"]
    assert "tag_aliases" not in runtime["data_paths"]["studio"]
    assert "tag_assignments" not in runtime["data_paths"]["studio"]
    assert runtime["data_paths"]["ui_text"]["tag_groups"] == "/assets/studio/data/ui_text/tag-groups.json"
    assert runtime["media"]["thumbs"]["works"] == "/assets/works/img"
    assert runtime["pipeline"]["variants"]["thumb"]["suffix"] == "thumb"
    assert runtime["state"]["return_context_storage_key"] == "dlf.studio.returnContext"
    assert runtime["modals"]["event"] == "studio:open-modal"
    assert any(view["id"] == "docs" and view["path"] == "/docs/?mode=manage" for view in runtime["views"])


def test_analytics_tag_groups_route_returns_existing_payload() -> None:
    groups_payload = analytics_get_payload(REPO_ROOT, "/tag-groups")
    registry_payload = analytics_get_payload(REPO_ROOT, "/tag-registry")
    aliases_payload = analytics_get_payload(REPO_ROOT, "/tag-aliases")
    assignments_payload = analytics_get_payload(REPO_ROOT, "/tag-assignments")

    assert groups_payload["ok"] is True
    assert groups_payload["tag_groups_version"] == "tag_groups_v1"
    assert {group["group_id"] for group in groups_payload["groups"]} >= {"subject", "domain", "form", "theme"}
    assert registry_payload["ok"] is True
    assert registry_payload["tag_registry_version"] == "tag_registry_v1"
    assert any(tag["tag_id"] == "subject:flower" for tag in registry_payload["tags"])
    assert aliases_payload["ok"] is True
    assert aliases_payload["tag_aliases_version"] == "tag_aliases_v1"
    assert "floral" in aliases_payload["aliases"]
    assert assignments_payload["ok"] is True
    assert assignments_payload["tag_assignments_version"] == "tag_assignments_v1"
    assert "001" in assignments_payload["series"]


def test_audit_api_routes_return_registry_and_validate_runs() -> None:
    health_payload = audit_get_payload(REPO_ROOT, "/health")
    audits_payload = audit_get_payload(REPO_ROOT, "/audits")

    assert health_payload["ok"] is True
    assert "studio-ready-state" in health_payload["audits"]
    assert audits_payload["ok"] is True
    assert any(audit["audit_id"] == "studio-ready-state" for audit in audits_payload["audits"])

    with pytest.raises(ValueError, match="allowlisted"):
        audit_post_response(REPO_ROOT, "/audits/run", {"audit_id": "not-allowlisted"})


def test_catalogue_project_state_route_uses_fixture_source(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        projects_base = Path(tmp_dir) / "source"
        source_dir = repo_root / "assets" / "studio" / "data" / "catalogue"
        project_dir = projects_base / "projects" / "alpha"
        source_dir.mkdir(parents=True)
        project_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
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
        (source_dir / "work_details.json").write_text(
            json.dumps({"catalogue_source_work_details_version": "catalogue_source_work_details_v1", "work_details": {}}),
            encoding="utf-8",
        )
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
        assert status == studio_docs_api.HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["dry_run"] is True
        assert payload["written"] is False
        assert payload["summary"]["source_folder_count"] == 1
        assert payload["summary"]["unrepresented_image_count"] == 1


def test_catalogue_thumbnail_quality_route_uses_fixture_source(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        projects_base = Path(tmp_dir) / "source"
        source_dir = projects_base / "thumbnail-quality-preview"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").parent.mkdir(parents=True, exist_ok=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        (source_dir / "sample.jpg").write_bytes(b"")
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))

        status, payload = catalogue_post_response(
            repo_root,
            "/thumbnail-quality-preview",
            {},
            dry_run=True,
        )

        assert status == studio_docs_api.HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["dry_run"] is True
        assert payload["source_count"] == 1
        assert payload["data_path"] == "assets/studio/data/thumbnail_quality_preview.json"
        assert payload["rows"][0]["source_name"] == "sample.jpg"
        assert payload["rows"][0]["baseline"]["path"].endswith("-current.webp")


def test_catalogue_read_route_returns_source_and_activity_payloads() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "assets" / "studio" / "data" / "catalogue"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {"00001": {"work_id": "00001", "title": "One", "status": "draft"}}}),
            encoding="utf-8",
        )
        (source_dir / "work_details.json").write_text(
            json.dumps({"catalogue_source_work_details_version": "catalogue_source_work_details_v1", "work_details": {}}),
            encoding="utf-8",
        )
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {"001": {"series_id": "001", "title": "Series", "status": "draft"}}}),
            encoding="utf-8",
        )
        (source_dir / "moments.json").write_text(
            json.dumps({"catalogue_source_moments_version": "catalogue_source_moments_v1", "moments": {}}),
            encoding="utf-8",
        )

        works_payload = catalogue_get_payload(repo_root, "/read", {"key": ["catalogue_works"]})
        activity_payload = catalogue_get_payload(repo_root, "/read", {"key": ["activity_log"]})

        assert works_payload["works"]["00001"]["title"] == "One"
        assert activity_payload["header"]["schema"] == "studio_activity_log_v1"
        assert activity_payload["entries"] == []


def test_catalogue_import_preview_and_apply_dry_run_use_fixture_workbook() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "assets" / "studio" / "data" / "catalogue"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {}}),
            encoding="utf-8",
        )
        (source_dir / "work_details.json").write_text(
            json.dumps({"catalogue_source_work_details_version": "catalogue_source_work_details_v1", "work_details": {}}),
            encoding="utf-8",
        )
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {"001": {"series_id": "001", "title": "Series", "status": "published", "primary_work_id": "00042"}}}),
            encoding="utf-8",
        )
        workbook_path = repo_root / "data" / "works_bulk_import.xlsx"
        workbook_path.parent.mkdir(parents=True)
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Works"
        sheet.append(["work_id", "series_ids", "title"])
        sheet.append(["42", "001", "Imported Work"])
        workbook.save(workbook_path)

        status, preview_payload = catalogue_post_response(repo_root, "/import-preview", {"mode": "works"}, dry_run=True)
        apply_status, apply_payload = catalogue_post_response(repo_root, "/import-apply", {"mode": "works"}, dry_run=True)

        assert status == studio_docs_api.HTTPStatus.OK
        assert preview_payload["preview"]["summary"]["importable_count"] == 1
        assert preview_payload["preview"]["importable_ids"] == ["00042"]
        assert apply_status == studio_docs_api.HTTPStatus.OK
        assert apply_payload["dry_run"] is True
        assert apply_payload["would_write"] is True
        assert json.loads((source_dir / "works.json").read_text(encoding="utf-8"))["works"] == {}


def test_catalogue_editor_create_work_dry_run_uses_in_process_write_handler() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "assets" / "studio" / "data" / "catalogue"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {}}),
            encoding="utf-8",
        )
        (source_dir / "work_details.json").write_text(
            json.dumps({"catalogue_source_work_details_version": "catalogue_source_work_details_v1", "work_details": {}}),
            encoding="utf-8",
        )
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {}}),
            encoding="utf-8",
        )
        (source_dir / "moments.json").write_text(
            json.dumps({"catalogue_source_moments_version": "catalogue_source_moments_v1", "moments": {}}),
            encoding="utf-8",
        )
        registry_target = repo_root / "assets" / "studio" / "data" / "catalogue_field_registry.json"
        registry_target.write_text((REPO_ROOT / "assets" / "studio" / "data" / "catalogue_field_registry.json").read_text(encoding="utf-8"), encoding="utf-8")

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

        assert status == studio_docs_api.HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["work_id"] == "00042"
        assert payload["created"] is True
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert json.loads((source_dir / "works.json").read_text(encoding="utf-8"))["works"] == {}


def test_analytics_save_tags_dry_run_route_uses_assignment_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        assignments_path = repo_root / "assets" / "studio" / "data" / "tag_assignments.json"
        assignments_path.parent.mkdir(parents=True)
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {}
}
""",
            encoding="utf-8",
        )

        status, payload = analytics_post_response(
            repo_root,
            "/save-tags",
            {
                "series_id": "series-a",
                "tags": [{"tag_id": "subject:trees", "w_manual": 0.9}],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        persisted = assignments_path.read_text(encoding="utf-8")
        assert status == studio_docs_api.HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["series_id"] == "series-a"
        assert payload["tag_count"] == 1
        assert payload["dry_run"] is True
        assert payload["would_write"]["tags"] == [{"tag_id": "subject:trees", "w_manual": 0.9}]
        assert "subject:trees" not in persisted


def test_analytics_import_tag_assignments_dry_run_routes_use_assignment_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        assignments_path = repo_root / "assets" / "studio" / "data" / "tag_assignments.json"
        series_index_path = repo_root / "assets" / "data" / "series_index.json"
        assignments_path.parent.mkdir(parents=True)
        series_index_path.parent.mkdir(parents=True)
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {
    "series-a": {
      "tags": []
    }
  }
}
""",
            encoding="utf-8",
        )
        series_index_path.write_text(
            """{
  "series": {
    "series-a": {
      "works": []
    }
  }
}
""",
            encoding="utf-8",
        )
        import_assignments = {
            "version": "tag_assignments_export_v1",
            "series": {
                "series-a": {
                    "base_row_snapshot": {"tags": []},
                    "staged_row": {"tags": [{"tag_id": "theme:growth", "w_manual": 0.6}]},
                }
            },
        }

        preview_status, preview_payload = analytics_post_response(
            repo_root,
            "/import-tag-assignments-preview",
            {
                "import_assignments": import_assignments,
                "import_filename": "import.json",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        apply_status, apply_payload = analytics_post_response(
            repo_root,
            "/import-tag-assignments",
            {
                "import_assignments": import_assignments,
                "import_filename": "import.json",
                "resolutions": {},
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        persisted = assignments_path.read_text(encoding="utf-8")
        assert preview_status == studio_docs_api.HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["applicable_count"] == 1
        assert apply_status == studio_docs_api.HTTPStatus.OK
        assert apply_payload["ok"] is True
        assert apply_payload["applied_series"] == 1
        assert apply_payload["dry_run"] is True
        assert apply_payload["would_write"]["applied_series"] == 1
        assert "theme:growth" not in persisted


def test_analytics_tag_registry_dry_run_routes_use_registry_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "assets" / "studio" / "data" / "tag_registry.json"
        aliases_path = repo_root / "assets" / "studio" / "data" / "tag_aliases.json"
        assignments_path = repo_root / "assets" / "studio" / "data" / "tag_assignments.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {
    "allowed_groups": ["subject", "theme"]
  },
  "tags": [
    {
      "tag_id": "subject:trees",
      "group": "subject",
      "label": "trees",
      "status": "active",
      "description": "Old trees"
    }
  ]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {
    "woodland": {
      "description": "Woodland",
      "tags": ["subject:trees"]
    }
  }
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {
    "series-a": {
      "tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]
    }
  }
}
""",
            encoding="utf-8",
        )

        import_status, import_payload = analytics_post_response(
            repo_root,
            "/import-tag-registry",
            {
                "mode": "add",
                "import_registry": {
                    "tags": [
                        {
                            "tag_id": "theme:growth",
                            "group": "theme",
                            "label": "growth",
                            "status": "active",
                            "description": "Growth",
                        }
                    ]
                },
                "import_filename": "registry.json",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        preview_status, preview_payload = analytics_post_response(
            repo_root,
            "/mutate-tag-preview",
            {
                "action": "delete",
                "tag_id": "subject:trees",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        persisted = registry_path.read_text(encoding="utf-8")
        assert import_status == studio_docs_api.HTTPStatus.OK
        assert import_payload["ok"] is True
        assert import_payload["added"] == 1
        assert import_payload["dry_run"] is True
        assert preview_status == studio_docs_api.HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["preview"] is True
        assert preview_payload["action"] == "delete"
        assert preview_payload["series_tag_refs_rewritten"] == 1
        assert "theme:growth" not in persisted


def test_analytics_tag_alias_dry_run_routes_use_alias_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        aliases_path = repo_root / "assets" / "studio" / "data" / "tag_aliases.json"
        registry_path = repo_root / "assets" / "studio" / "data" / "tag_registry.json"
        aliases_path.parent.mkdir(parents=True)
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {
    "foliage": {
      "description": "Old foliage",
      "tags": ["subject:trees"]
    }
  }
}
""",
            encoding="utf-8",
        )
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {
    "allowed_groups": ["subject", "theme"]
  },
  "tags": [
    {
      "tag_id": "subject:trees",
      "group": "subject",
      "label": "trees",
      "status": "active",
      "description": "Trees"
    },
    {
      "tag_id": "theme:growth",
      "group": "theme",
      "label": "growth",
      "status": "active",
      "description": "Growth"
    }
  ]
}
""",
            encoding="utf-8",
        )

        import_status, import_payload = analytics_post_response(
            repo_root,
            "/import-tag-aliases",
            {
                "mode": "add",
                "import_aliases": {
                    "aliases": {
                        "growth": {
                            "description": "Growth",
                            "tags": ["theme:growth"],
                        }
                    }
                },
                "import_filename": "aliases.json",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        delete_status, delete_payload = analytics_post_response(
            repo_root,
            "/delete-tag-alias",
            {
                "alias": "foliage",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        preview_status, preview_payload = analytics_post_response(
            repo_root,
            "/mutate-tag-alias-preview",
            {
                "alias": "foliage",
                "new_alias": "canopy",
                "description": "Canopy",
                "tags": ["subject:trees", "theme:growth"],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        persisted = aliases_path.read_text(encoding="utf-8")
        assert import_status == studio_docs_api.HTTPStatus.OK
        assert import_payload["ok"] is True
        assert import_payload["added"] == 1
        assert import_payload["dry_run"] is True
        assert delete_status == studio_docs_api.HTTPStatus.OK
        assert delete_payload["ok"] is True
        assert delete_payload["alias"] == "foliage"
        assert delete_payload["dry_run"] is True
        assert preview_status == studio_docs_api.HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["preview"] is True
        assert preview_payload["renamed"] is True
        assert "canopy" not in persisted


def test_analytics_promotion_demotion_dry_run_routes_use_promotion_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "assets" / "studio" / "data" / "tag_registry.json"
        aliases_path = repo_root / "assets" / "studio" / "data" / "tag_aliases.json"
        assignments_path = repo_root / "assets" / "studio" / "data" / "tag_assignments.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {
    "allowed_groups": ["subject", "theme"]
  },
  "tags": [
    {
      "tag_id": "subject:trees",
      "group": "subject",
      "label": "trees",
      "status": "active",
      "description": "Trees"
    },
    {
      "tag_id": "theme:growth",
      "group": "theme",
      "label": "growth",
      "status": "active",
      "description": "Growth"
    }
  ]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {
    "foliage": {
      "description": "Foliage",
      "tags": ["subject:trees"]
    }
  }
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {
    "series-a": {
      "tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]
    }
  }
}
""",
            encoding="utf-8",
        )

        promote_status, promote_payload = analytics_post_response(
            repo_root,
            "/promote-tag-alias-preview",
            {
                "alias": "foliage",
                "group": "theme",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        demote_status, demote_payload = analytics_post_response(
            repo_root,
            "/demote-tag-preview",
            {
                "tag_id": "subject:trees",
                "alias_targets": ["theme:growth"],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        registry_persisted = registry_path.read_text(encoding="utf-8")
        aliases_persisted = json.loads(aliases_path.read_text(encoding="utf-8"))
        assert promote_status == studio_docs_api.HTTPStatus.OK
        assert promote_payload["ok"] is True
        assert promote_payload["preview"] is True
        assert promote_payload["new_tag_id"] == "theme:foliage"
        assert demote_status == studio_docs_api.HTTPStatus.OK
        assert demote_payload["ok"] is True
        assert demote_payload["preview"] is True
        assert demote_payload["alias_key"] == "trees"
        assert demote_payload["series_tag_refs_rewritten"] == 1
        assert "theme:foliage" not in registry_persisted
        assert "trees" not in aliases_persisted["aliases"]


def test_docs_capabilities_report_scopes_and_management_api() -> None:
    payload = studio_docs_api.docs_capabilities_payload(REPO_ROOT)
    capabilities = payload["capabilities"]
    studio = capabilities["scopes"]["studio"]

    assert payload["ok"] is True
    assert studio["available"] is True
    assert studio["root"] == "_docs"
    assert capabilities["docs_management"] is True
    assert capabilities["generated_data_reads"] is True
    assert capabilities["html_import"] is True
    assert capabilities["source_config_settings_reads"] is True
    assert capabilities["scope_lifecycle"]["create_apply"] is True
    assert studio["generated_data_reads"] is True
    assert studio["generated_search_reads"] is True


def test_docs_generated_read_routes_return_existing_payloads() -> None:
    params = {"scope": ["studio"]}
    index_payload = studio_docs_api.docs_generated_read_payload(
        REPO_ROOT,
        "/docs/generated/index",
        params,
    )
    search_payload = studio_docs_api.docs_generated_read_payload(
        REPO_ROOT,
        "/docs/generated/search",
        params,
    )
    doc_payload = studio_docs_api.docs_generated_read_payload(
        REPO_ROOT,
        "/docs/generated/payload",
        {"scope": ["studio"], "doc_id": ["docs-viewer"]},
    )

    assert any(doc["doc_id"] == "docs-viewer" for doc in index_payload["docs"])
    assert "entries" in search_payload
    assert doc_payload["doc_id"] == "docs-viewer"


def test_docs_management_settings_and_dry_run_mutation_routes() -> None:
    settings_payload = studio_docs_api.docs_management_get_payload(
        REPO_ROOT,
        "/docs/source-config-settings",
        {"scope": ["studio"]},
    )
    preview_status, preview_payload = studio_docs_api.docs_management_post_response(
        REPO_ROOT,
        "/docs/delete-preview",
        {"scope": "studio", "doc_id": "docs-viewer"},
        dry_run=True,
    )

    assert settings_payload["ok"] is True
    assert any(scope["scope_id"] == "studio" for scope in settings_payload["scopes"])
    assert preview_status == studio_docs_api.HTTPStatus.OK
    assert preview_payload["ok"] is True
    assert preview_payload["doc_id"] == "docs-viewer"
    assert "blockers" in preview_payload


def test_docs_api_post_rejects_disallowed_origin() -> None:
    assert studio_docs_api.docs_allowed_origin(REPO_ROOT, "http://127.0.0.1:8765") == "http://127.0.0.1:8765"
    assert studio_docs_api.docs_allowed_origin(REPO_ROOT, "https://example.com") == ""


if __name__ == "__main__":
    test_runtime_config_exposes_adapter_contract()
    test_analytics_tag_groups_route_returns_existing_payload()
    test_analytics_save_tags_dry_run_route_uses_assignment_contract()
    test_analytics_import_tag_assignments_dry_run_routes_use_assignment_contract()
    test_analytics_tag_registry_dry_run_routes_use_registry_contract()
    test_analytics_tag_alias_dry_run_routes_use_alias_contract()
    test_analytics_promotion_demotion_dry_run_routes_use_promotion_contract()
    test_docs_capabilities_report_scopes_and_management_api()
    test_docs_generated_read_routes_return_existing_payloads()
    test_docs_management_settings_and_dry_run_mutation_routes()
    test_docs_api_post_rejects_disallowed_origin()
    print("studio app server tests OK")
