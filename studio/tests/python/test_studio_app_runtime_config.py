#!/usr/bin/env python3
"""Studio app runtime config tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from studio_app_server_test_support import (
    REPO_ROOT,
    STATIC_PREFIXES,
    STUDIO_SHELL_PATH,
    StudioAppRequestHandler,
    asset_version,
    env_flag,
    parse_args,
    runtime_config,
    studio_shell_route_paths,
    validate_studio_route_registry,
)

def test_studio_bootstrap_exposes_shared_search_list_assets() -> None:
    html = STUDIO_SHELL_PATH.read_text(encoding="utf-8").replace("__STUDIO_ASSET_VERSION__", "test-version")

    assert "/shared/frontend/" in STATIC_PREFIXES
    assert '<link rel="stylesheet" href="/shared/frontend/css/search-list.css?v=test-version">' in html
    assert '<link rel="stylesheet" href="/shared/frontend/css/record-list.css?v=test-version">' in html

def test_runtime_config_exposes_adapter_contract() -> None:
    original_env = {key: os.environ.get(key) for key in ("SITE_HOST", "SITE_PORT", "SITE_PREVIEW_BASE", "PRODUCTION_SITE_BASE")}
    os.environ["SITE_HOST"] = "127.0.0.1"
    os.environ["SITE_PORT"] = "4000"
    os.environ.pop("SITE_PREVIEW_BASE", None)
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
    assert payload["app"]["routes"]["studio_home"]["path"] == "/studio/"
    assert payload["app"]["routes"]["studio_home"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["studio_home"]["template"] == "/studio/app/frontend/routes/studio-home.html"
    assert payload["app"]["routes"]["catalogue_work_editor"]["path"] == "/studio/catalogue-work/"
    assert payload["app"]["routes"]["project_state"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["bulk_add_work"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["catalogue_field_registry"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["catalogue_status"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["studio_works"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["catalogue_series_editor"]["shell_type"] == "html-template"
    assert payload["app"]["routes"]["catalogue_work_editor"]["shell_type"] == "html-template"
    assert "catalogue_moment_editor" not in payload["app"]["routes"]
    assert payload["app"]["routes"]["project_state"]["shell_type"] == "html-template"
    assert not any(route["shell_type"] == "python" for route in payload["app"]["routes"].values())
    assert payload["app"]["routes"]["catalogue_work_editor"]["ready_state_route_id"] == "catalogue-work"
    assert "routes" not in payload["paths"]
    assert "docs" not in payload["app"]["routes"]
    assert any(view["id"] == "studio_home" and view["path"] == "/studio/" for view in runtime["views"])
    assert not any(view["id"] == "docs" for view in runtime["views"])
    assert not any("doc_href" in view for view in runtime["views"])
    assert not any(view["id"] in {"studio_catalogue", "studio_analytics", "data_sharing"} for view in runtime["views"])
    assert not any(view["id"] in {"tag_registry", "tag_aliases", "series_tags", "series_tag_editor"} for view in runtime["views"])
    assert not any(view["id"] in {"data_sharing_prepare", "data_sharing_review"} for view in runtime["views"])
    assert not any(view["id"] in {"studio_audits", "studio_risk", "activity"} for view in runtime["views"])
    assert any(view["id"] == "project_state" and view["path"] == "/studio/project-state/" for view in runtime["views"])
    assert not any(view["id"] == "thumbnail_quality" for view in runtime["views"])
    assert not any("doc_id" in view for view in runtime["views"])
    assert not any("docId" in view for view in runtime["views"])
    assert any(view["id"] == "bulk_add_work" and view["path"] == "/studio/bulk-add-work/" for view in runtime["views"])
    assert any(view["id"] == "catalogue_field_registry" and view["path"] == "/studio/catalogue-field-registry/" for view in runtime["views"])
    assert any(view["id"] == "catalogue_status" and view["path"] == "/studio/catalogue-status/" for view in runtime["views"])
    assert any(view["id"] == "studio_works" and view["path"] == "/studio/studio-works/" for view in runtime["views"])
    assert any(view["id"] == "catalogue_series_editor" and view["path"] == "/studio/catalogue-series/" for view in runtime["views"])
    assert any(view["id"] == "catalogue_work_editor" and view["path"] == "/studio/catalogue-work/" for view in runtime["views"])
    assert not any(view["id"] == "catalogue_moment_editor" or view["path"] == "/studio/catalogue-moment/" for view in runtime["views"])
    assert runtime["navigation"]["primary"] == []
    assert "series_tag_editor" not in runtime["navigation"]["primary"]
    assert "analytics" not in runtime["services"]
    assert "data_sharing" not in runtime["services"]
    assert "docs" not in runtime["services"]
    assert "audits" not in runtime["services"]
    assert "risk" not in runtime["services"]
    assert "external_links" not in payload
    assert "catalogue" not in payload
    assert set(runtime["data_paths"]) == {"studio", "ui_text"}
    assert set(runtime["data_paths"]["studio"]) == {
        "catalogue_works",
        "catalogue_series",
        "catalogue_lookup_work_search",
        "catalogue_lookup_series_search",
        "catalogue_lookup_series_base",
        "catalogue_work_record",
        "catalogue_work_detail_record",
        "catalogue_field_registry",
    }
    assert "docs_viewer" not in runtime["data_paths"].get("ui_text", {})
    assert runtime["services"]["catalogue"]["base"] == "/studio/api/catalogue"
    assert runtime["services"]["catalogue"]["read"] == "/studio/api/catalogue/read"
    assert runtime["services"]["catalogue"]["bulk_save"] == "/studio/api/catalogue/bulk-save"
    assert runtime["services"]["catalogue"]["delete_preview"] == "/studio/api/catalogue/delete-preview"
    assert runtime["services"]["catalogue"]["delete_apply"] == "/studio/api/catalogue/delete-apply"
    assert runtime["services"]["catalogue"]["publication_preview"] == "/studio/api/catalogue/publication-preview"
    assert runtime["services"]["catalogue"]["publication_apply"] == "/studio/api/catalogue/publication-apply"
    assert runtime["services"]["catalogue"]["create_work"] == "/studio/api/catalogue/work/create"
    assert runtime["services"]["catalogue"]["save_work"] == "/studio/api/catalogue/work/save"
    assert runtime["services"]["catalogue"]["import_preview"] == "/studio/api/catalogue/import-preview"
    assert runtime["services"]["catalogue"]["import_apply"] == "/studio/api/catalogue/import-apply"
    assert runtime["services"]["catalogue"]["create_series"] == "/studio/api/catalogue/series/create"
    assert runtime["services"]["catalogue"]["save_series"] == "/studio/api/catalogue/series/save"
    assert runtime["services"]["catalogue"]["build_preview"] == "/studio/api/catalogue/build-preview"
    assert runtime["services"]["catalogue"]["build_apply"] == "/studio/api/catalogue/build-apply"
    assert runtime["services"]["catalogue"]["project_state_report"] == "/studio/api/catalogue/project-state-report"
    assert runtime["services"]["catalogue"]["project_state_open_report"] == "/studio/api/catalogue/project-state-open-report"
    assert "thumbnail_quality_preview" not in runtime["services"]["catalogue"]
    assert "tag_groups" not in runtime["data_paths"]["studio"]
    assert "tag_registry" not in runtime["data_paths"]["studio"]
    assert "tag_aliases" not in runtime["data_paths"]["studio"]
    assert "tag_assignments" not in runtime["data_paths"]["studio"]
    assert "thumbnail_quality_preview" not in runtime["data_paths"]["studio"]
    assert "data_sharing_adapters" not in runtime["data_paths"]["studio"]
    assert "library_export_configs" not in runtime["data_paths"]["studio"]
    assert "catalogue_lookup_meta" not in runtime["data_paths"]["studio"]
    assert "tag_groups" not in runtime["data_paths"]["ui_text"]
    assert runtime["media"]["thumbs"]["works"] == "/assets/works/img"
    assert runtime["pipeline"]["variants"]["thumb"]["suffix"] == "thumb"
    assert runtime["pipeline"]["encoding"]["format"] == "webp"
    assert runtime["pipeline"]["workbooks"]["bulk_import"] == "data/works_bulk_import.xlsx"
    assert runtime["modals"]["event"] == "studio:open-modal"

def test_studio_route_registry_validation_rejects_invalid_routes() -> None:
    payload = runtime_config(REPO_ROOT, "test-version")
    routes = payload["app"]["routes"]

    duplicate_path = json.loads(json.dumps(payload))
    duplicate_path["app"]["routes"]["project_state"]["path"] = routes["bulk_add_work"]["path"]
    with pytest.raises(RuntimeError, match="duplicate path"):
        validate_studio_route_registry(REPO_ROOT, duplicate_path)

    missing_script = json.loads(json.dumps(payload))
    missing_script["app"]["routes"]["project_state"].pop("script")
    with pytest.raises(RuntimeError, match="project_state: shell route is missing script"):
        validate_studio_route_registry(REPO_ROOT, missing_script)

    missing_template = json.loads(json.dumps(payload))
    missing_template["app"]["routes"]["project_state"].pop("template")
    with pytest.raises(RuntimeError, match="project_state: missing required field template"):
        validate_studio_route_registry(REPO_ROOT, missing_template)

    missing_template_path = json.loads(json.dumps(payload))
    missing_template_path["app"]["routes"]["project_state"]["template"] = "/studio/app/frontend/routes/missing.html"
    with pytest.raises(RuntimeError, match="project_state: template does not exist"):
        validate_studio_route_registry(REPO_ROOT, missing_template_path)

    unsupported_shell = json.loads(json.dumps(payload))
    unsupported_shell["app"]["routes"]["project_state"]["shell_type"] = "server"
    with pytest.raises(RuntimeError, match="project_state: unsupported shell_type"):
        validate_studio_route_registry(REPO_ROOT, unsupported_shell)

    external_route = json.loads(json.dumps(payload))
    external_route["app"]["routes"]["external_route"] = {
        "label": "external",
        "title": "External",
        "path": "/external/",
        "template": "/studio/app/frontend/routes/project-state.html",
        "script": "/studio/app/frontend/js/project-state.js",
        "nav": False,
        "shell_type": "html-template",
        "ready_state_route_id": "external",
    }
    with pytest.raises(RuntimeError, match="external_route: shell route path must be under /studio/"):
        validate_studio_route_registry(REPO_ROOT, external_route)

    configured_route = json.loads(json.dumps(payload))
    configured_route["app"]["routes"]["configured_route"] = {
        "label": "configured",
        "title": "Configured",
        "path": "/studio/configured/",
        "template": "/studio/app/frontend/routes/project-state.html",
        "script": "/studio/app/frontend/js/project-state.js",
        "nav": False,
        "shell_type": "html-template",
        "ready_state_route_id": "configured",
    }
    validate_studio_route_registry(REPO_ROOT, configured_route)
    assert "/studio/configured/" in studio_shell_route_paths(REPO_ROOT, configured_route)

    duplicated_route_metadata = json.loads(json.dumps(payload))
    duplicated_route_metadata["paths"]["routes"] = {
        "catalogue_field_registry_review": "/studio/catalogue-field-registry/"
    }
    with pytest.raises(RuntimeError, match="Studio route metadata must live in app.routes"):
        validate_studio_route_registry(REPO_ROOT, duplicated_route_metadata)

def test_access_log_is_opt_in(monkeypatch) -> None:
    monkeypatch.delenv("STUDIO_APP_ACCESS_LOG", raising=False)
    assert env_flag("STUDIO_APP_ACCESS_LOG") is False
    assert parse_args([]).access_log is False

    monkeypatch.setenv("STUDIO_APP_ACCESS_LOG", "1")
    assert env_flag("STUDIO_APP_ACCESS_LOG") is True
    assert parse_args([]).access_log is True
    assert parse_args(["--access-log"]).access_log is True

    monkeypatch.setenv("STUDIO_APP_ACCESS_LOG", "0")
    assert parse_args([]).access_log is False
    assert parse_args(["--access-log"]).access_log is True

def test_static_path_policy_serves_current_studio_allowlists() -> None:
    def allowed(path: str) -> bool:
        return StudioAppRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/studio/app/frontend/js/catalogue-work-editor.js") is True
    assert allowed("/studio/app/assets/css/studio.css") is True
    assert allowed("/shared/frontend/js/search-list.js") is True
    assert allowed("/shared/frontend/css/search-list.css") is True
    assert allowed("/studio/data/generated/activity/index.json") is False
    assert allowed("/studio/data/generated/activity/work-storage-index.json") is True
    assert allowed("/studio/data/generated/catalogue-lookup/work-search.json") is True
    assert allowed("/assets/docs/interactive/library/coincidence-salience.html") is False
    assert allowed("/data-sharing/config/adapters.json") is False
    assert allowed("/data-sharing/adapters/documents/config/prepare-profiles.json") is False
    assert allowed("/assets/works/img/00001.jpg") is True
    assert allowed("/assets/js/work.js") is True
    assert allowed("/var/catalogue/media/works/srcset_images/primary/00008-primary-1600.webp") is True
    assert allowed("/studio/data/generated/project-state/report.json") is False

    assert allowed("/assets/studio/js/catalogue-work-editor.js") is False
    assert allowed("/assets/studio/css/studio.css") is False
    assert allowed("/assets/studio/img/panel-backgrounds/aqua.jpg") is False
    assert allowed("/assets/docs-viewer/js/docs-viewer.js") is False
    assert allowed("/assets/docs-viewer/css/docs-viewer.css") is False
    assert allowed("/assets/docs-viewer/data/docs-viewer-config.json") is False
    assert allowed("/studio/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/static/css/docs-viewer-base.css") is False
    assert allowed("/docs-viewer/config/defaults/docs-viewer-config.json") is False
    assert allowed("/data-sharing/data_sharing/services/registry.py") is False

def test_studio_transport_does_not_publish_data_sharing_defaults() -> None:
    transport_source = (REPO_ROOT / "studio/app/frontend/js/studio-transport.js").read_text(encoding="utf-8")
    assert "/studio/api/data-sharing" not in transport_source

def test_studio_server_excludes_data_sharing_config() -> None:
    assert StudioAppRequestHandler.is_allowed_static_path(object(), "/data-sharing/config/adapters.json") is False
    assert StudioAppRequestHandler.is_allowed_static_path(object(), "/data-sharing/adapters/documents/config/prepare-profiles.json") is False

def test_local_studio_shells_load_studio_css_without_public_main_css() -> None:
    html_shells = [
        STUDIO_SHELL_PATH.read_text(encoding="utf-8").replace("__STUDIO_ASSET_VERSION__", "test-version"),
    ]

    for shell in html_shells:
        assert "/studio/app/assets/css/studio.css?v=test-version" in shell
        assert "/assets/css/main.css" not in shell

def test_local_studio_asset_version_does_not_follow_public_main_css() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        public_css = repo_root / "site" / "assets" / "css" / "main.css"
        studio_css = repo_root / "studio" / "app" / "assets" / "css" / "studio.css"
        for path in (public_css, studio_css):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("/* fixture */\n", encoding="utf-8")
        os.utime(studio_css, (200, 200))
        os.utime(public_css, (300, 300))

        assert asset_version(repo_root) == "200"
