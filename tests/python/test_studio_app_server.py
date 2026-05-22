#!/usr/bin/env python3
"""Focused checks for the local Studio app server."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.studio import studio_docs_api  # noqa: E402
from scripts.studio.studio_analytics_api import analytics_get_payload, analytics_post_response  # noqa: E402
from scripts.studio.studio_app_config import runtime_config  # noqa: E402


def test_runtime_config_exposes_adapter_contract() -> None:
    payload = runtime_config(REPO_ROOT, "test-version")
    runtime = payload["app"]["runtime"]

    assert runtime["host"] == "local-studio-app"
    assert runtime["asset_version"] == "test-version"
    assert runtime["routes"]["runtime_config"] == "/studio/runtime-config.json"
    assert runtime["services"]["analytics"]["tag_groups"] == "/studio/api/analytics/tag-groups"
    assert runtime["services"]["analytics"]["tag_registry"] == "/studio/api/analytics/tag-registry"
    assert runtime["services"]["analytics"]["tag_aliases"] == "/studio/api/analytics/tag-aliases"
    assert runtime["services"]["analytics"]["tag_assignments"] == "/studio/api/analytics/tag-assignments"
    assert runtime["services"]["analytics"]["save_tags"] == "/studio/api/analytics/save-tags"
    assert runtime["services"]["analytics"]["import_tag_assignments_preview"] == "/studio/api/analytics/import-tag-assignments-preview"
    assert runtime["services"]["analytics"]["import_tag_assignments"] == "/studio/api/analytics/import-tag-assignments"
    assert runtime["services"]["analytics"]["import_tag_registry"] == "/studio/api/analytics/import-tag-registry"
    assert runtime["services"]["analytics"]["mutate_tag_preview"] == "/studio/api/analytics/mutate-tag-preview"
    assert runtime["services"]["analytics"]["mutate_tag"] == "/studio/api/analytics/mutate-tag"
    assert runtime["services"]["docs"]["base"] == "/studio/api/docs"
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
    test_docs_capabilities_report_scopes_and_management_api()
    test_docs_generated_read_routes_return_existing_payloads()
    test_docs_management_settings_and_dry_run_mutation_routes()
    test_docs_api_post_rejects_disallowed_origin()
    print("studio app server tests OK")
