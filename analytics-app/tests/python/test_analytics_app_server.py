#!/usr/bin/env python3
"""Focused checks for the local Analytics app server."""

from __future__ import annotations

from http import HTTPStatus
import json
from pathlib import Path
import sys
import tempfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (REPO_ROOT, ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from analytics_api import analytics_get_payload, analytics_post_response  # noqa: E402
from analytics_app_config import analytics_shell_route_paths, load_analytics_config, runtime_config, validate_analytics_route_registry  # noqa: E402
from analytics_app_server import AnalyticsAppRequestHandler  # noqa: E402


def test_runtime_config_exposes_analytics_routes_and_services() -> None:
    payload = runtime_config(REPO_ROOT, "test-version")
    runtime = payload["app"]["runtime"]

    assert runtime["host"] == "local-analytics-app"
    assert runtime["asset_version"] == "test-version"
    assert runtime["routes"]["runtime_config"] == "/analytics/runtime-config.json"
    assert runtime["sites"]["public_preview"]["base"] == "http://127.0.0.1:4000"
    assert runtime["sites"]["production"]["base"] == "https://dotlineform.com"
    assert runtime["navigation"]["primary"] == []
    assert "routes" not in payload["paths"]
    assert payload["app"]["routes"]["analytics_home"]["path"] == "/analytics/"
    assert payload["app"]["routes"]["analytics_home"]["template"] == "/analytics/app/frontend/routes/analytics-home.html"
    assert payload["app"]["routes"]["analytics_home"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["tag_registry"]["path"] == "/analytics/tag-registry/"
    assert payload["app"]["routes"]["tag_registry"]["template"] == "/analytics/app/frontend/routes/tag-registry.html"
    assert payload["app"]["routes"]["tag_registry"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["data_sharing_prepare"]["path"] == "/analytics/data-sharing/prepare/"
    assert payload["app"]["routes"]["data_sharing_prepare"]["template"] == "/analytics/app/frontend/routes/data-sharing-prepare.html"
    assert any(view["id"] == "analytics_home" and view["path"] == "/analytics/" for view in runtime["views"])
    assert any(view["id"] == "tag_registry" and view["path"] == "/analytics/tag-registry/" for view in runtime["views"])
    assert any(view["id"] == "tag_aliases" and view["path"] == "/analytics/tag-aliases/" for view in runtime["views"])
    assert any(view["id"] == "series_tags" and view["path"] == "/analytics/series-tags/" for view in runtime["views"])
    assert any(view["id"] == "series_tag_editor" and view["path"] == "/analytics/series-tag-editor/" for view in runtime["views"])
    assert any(view["id"] == "data_sharing_prepare" and view["path"] == "/analytics/data-sharing/prepare/" for view in runtime["views"])
    assert any(view["id"] == "data_sharing_review" and view["path"] == "/analytics/data-sharing/review/" for view in runtime["views"])
    assert "external_links" not in payload

    analytics = runtime["services"]["analytics"]
    assert analytics["base"] == "/analytics/api"
    assert analytics["health"] == "/analytics/api/health"
    assert analytics["tag_groups"] == "/analytics/api/tag-groups"
    assert analytics["tag_registry"] == "/analytics/api/tag-registry"
    assert analytics["tag_aliases"] == "/analytics/api/tag-aliases"
    assert analytics["tag_assignments"] == "/analytics/api/tag-assignments"
    assert analytics["save_tags"] == "/analytics/api/save-tags"
    assert analytics["import_tag_assignments"] == "/analytics/api/import-tag-assignments"
    assert analytics["import_tag_registry"] == "/analytics/api/import-tag-registry"
    assert analytics["import_tag_aliases"] == "/analytics/api/import-tag-aliases"
    assert analytics["mutate_tag"] == "/analytics/api/mutate-tag"
    assert analytics["promote_tag_alias"] == "/analytics/api/promote-tag-alias"

    data_sharing = runtime["services"]["data_sharing"]
    assert data_sharing == {
        "base": "/analytics/api/data-sharing",
        "health": "/analytics/api/data-sharing/health",
        "config": "/analytics/api/data-sharing/config",
        "selectable_records": "/analytics/api/data-sharing/selectable-records",
        "returned_packages": "/analytics/api/data-sharing/returned-packages",
        "returned_records": "/analytics/api/data-sharing/returned-records",
        "prepare": "/analytics/api/data-sharing/prepare",
        "review": "/analytics/api/data-sharing/review",
        "apply": "/analytics/api/data-sharing/apply",
        "context": "/analytics/api/data-sharing/context",
    }

    assert "analytics" not in runtime["data_paths"]
    assert runtime["data_paths"]["site"]["series_index"] == "/assets/data/series_index.json"
    assert runtime["data_paths"]["site"]["works_index"] == "/assets/data/works_index.json"
    assert "ui_text" not in runtime["data_paths"]
    assert runtime["series_tag_editor"]["series_index_url"] == "/assets/data/series_index.json"
    assert runtime["series_tag_editor"]["analytics_tag_editor_module_url"] == "/analytics/app/frontend/js/analytics-tag-editor.js"
    assert runtime["modals"]["event"] == "analytics:open-modal"
    assert payload["analysis"]["groups"]["ordered"] == ["subject", "domain", "form", "theme"]
    assert "deprecated_statuses" not in payload["analysis"]["rag"]
    assert payload["analysis"]["rag"]["completeness"]["group_coverage_denominator"] == 4
    assert "if_deprecated_tags_gt" not in payload["analysis"]["rag"]["rules"]["amber"]
    assert payload["analysis"]["rag"]["rules"]["amber"]["if_missing_all_groups"] == ["form", "theme"]


def test_analytics_route_registry_rejects_paths_routes_duplicates() -> None:
    payload = load_analytics_config(REPO_ROOT)
    paths = payload.setdefault("paths", {})
    assert isinstance(paths, dict)
    paths["routes"] = {"tag_registry": "/analytics/tag-registry/"}

    with pytest.raises(RuntimeError, match="Analytics route metadata must live in app.routes"):
        validate_analytics_route_registry(REPO_ROOT, payload)


def test_analytics_shell_route_paths_are_config_driven() -> None:
    paths = analytics_shell_route_paths(REPO_ROOT)

    assert paths["/analytics/"] == "analytics_home"
    assert paths["/analytics/tag-groups/"] == "tag_groups"
    assert paths["/analytics/tag-registry/"] == "tag_registry"
    assert paths["/analytics/tag-aliases/"] == "tag_aliases"
    assert paths["/analytics/series-tags/"] == "series_tags"
    assert paths["/analytics/series-tag-editor/"] == "series_tag_editor"
    assert paths["/analytics/data-sharing/prepare/"] == "data_sharing_prepare"
    assert paths["/analytics/data-sharing/review/"] == "data_sharing_review"


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


def test_static_path_policy_serves_analytics_paths_and_shared_data_sharing_config() -> None:
    def allowed(path: str) -> bool:
        return AnalyticsAppRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/analytics/app/frontend/js/tag-registry.js") is True
    assert allowed("/analytics/app/frontend/routes/tag-registry.html") is True
    assert allowed("/analytics/app/frontend/config/analytics-config.json") is True
    assert allowed("/analytics/app/assets/css/analytics.css") is True
    assert allowed("/apple-touch-icon-precomposed.png") is True
    assert allowed("/shared/frontend/js/selectable-list.js") is True
    assert allowed("/shared/frontend/css/selectable-list.css") is True
    assert allowed("/data-sharing/config/adapters.json") is False
    assert allowed("/data-sharing/adapters/documents/config/prepare-profiles.json") is False
    assert allowed("/shared/python/markdown_renderer.py") is False
    assert allowed("/analytics/data/canonical/tag-registry.json") is True
    assert allowed("/docs-viewer/generated/docs/studio/index.json") is False

    retired_tag_path = "/studio/data/canonical" + "/analytics/tag-registry.json"
    assert allowed(retired_tag_path) is False
    assert allowed("/studio/app/frontend/js/tag-registry.js") is False
    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/data-sharing/data_sharing/services/registry.py") is False


def test_analytics_save_tags_dry_run_route_uses_assignment_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        assignments_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-assignments.json"
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
        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["series_id"] == "series-a"
        assert payload["tag_count"] == 1
        assert payload["dry_run"] is True
        assert payload["would_write"]["tags"] == [{"tag_id": "subject:trees", "w_manual": 0.9}]
        assert "subject:trees" not in persisted


def test_analytics_import_tag_assignments_dry_run_routes_use_assignment_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        assignments_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-assignments.json"
        series_index_path = repo_root / "site" / "assets" / "data" / "series_index.json"
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
        assert preview_status == HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["applicable_count"] == 1
        assert apply_status == HTTPStatus.OK
        assert apply_payload["ok"] is True
        assert apply_payload["applied_series"] == 1
        assert apply_payload["dry_run"] is True
        assert apply_payload["would_write"]["applied_series"] == 1
        assert "theme:growth" not in persisted


def test_analytics_tag_registry_dry_run_routes_use_registry_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-registry.json"
        aliases_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-aliases.json"
        assignments_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-assignments.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [{"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Old trees"}]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"woodland": {"description": "Woodland", "tags": ["subject:trees"]}}
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {"series-a": {"tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]}}
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
                        {"tag_id": "theme:growth", "group": "theme", "label": "growth", "description": "Growth"}
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
            {"action": "delete", "tag_id": "subject:trees", "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )

        persisted = registry_path.read_text(encoding="utf-8")
        assert import_status == HTTPStatus.OK
        assert import_payload["ok"] is True
        assert import_payload["added"] == 1
        assert import_payload["dry_run"] is True
        assert preview_status == HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["preview"] is True
        assert preview_payload["action"] == "delete"
        assert preview_payload["series_tag_refs_rewritten"] == 1
        assert "theme:growth" not in persisted


def test_analytics_tag_alias_dry_run_routes_use_alias_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        aliases_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-aliases.json"
        registry_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-registry.json"
        aliases_path.parent.mkdir(parents=True)
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"foliage": {"description": "Old foliage", "tags": ["subject:trees"]}}
}
""",
            encoding="utf-8",
        )
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [
    {"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Trees"},
    {"tag_id": "theme:growth", "group": "theme", "label": "growth", "description": "Growth"}
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
                "import_aliases": {"aliases": {"growth": {"description": "Growth", "tags": ["theme:growth"]}}},
                "import_filename": "aliases.json",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        delete_status, delete_payload = analytics_post_response(
            repo_root,
            "/delete-tag-alias",
            {"alias": "foliage", "client_time_utc": "2026-05-22T00:00:00Z"},
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
        assert import_status == HTTPStatus.OK
        assert import_payload["ok"] is True
        assert import_payload["added"] == 1
        assert import_payload["dry_run"] is True
        assert delete_status == HTTPStatus.OK
        assert delete_payload["ok"] is True
        assert delete_payload["alias"] == "foliage"
        assert delete_payload["dry_run"] is True
        assert preview_status == HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["preview"] is True
        assert preview_payload["renamed"] is True
        assert "canopy" not in persisted


def test_analytics_promotion_demotion_dry_run_routes_use_promotion_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-registry.json"
        aliases_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-aliases.json"
        assignments_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-assignments.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [
    {"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Trees"},
    {"tag_id": "theme:growth", "group": "theme", "label": "growth", "description": "Growth"}
  ]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"foliage": {"description": "Foliage", "tags": ["subject:trees"]}}
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {"series-a": {"tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]}}
}
""",
            encoding="utf-8",
        )

        promote_status, promote_payload = analytics_post_response(
            repo_root,
            "/promote-tag-alias-preview",
            {"alias": "foliage", "group": "theme", "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )
        demote_status, demote_payload = analytics_post_response(
            repo_root,
            "/demote-tag-preview",
            {"tag_id": "subject:trees", "alias_targets": ["theme:growth"], "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )

        registry_persisted = registry_path.read_text(encoding="utf-8")
        aliases_persisted = json.loads(aliases_path.read_text(encoding="utf-8"))
        assert promote_status == HTTPStatus.OK
        assert promote_payload["ok"] is True
        assert promote_payload["preview"] is True
        assert promote_payload["new_tag_id"] == "theme:foliage"
        assert demote_status == HTTPStatus.OK
        assert demote_payload["ok"] is True
        assert demote_payload["preview"] is True
        assert demote_payload["alias_key"] == "trees"
        assert demote_payload["series_tag_refs_rewritten"] == 1
        assert "theme:foliage" not in registry_persisted
        assert "trees" not in aliases_persisted["aliases"]
