#!/usr/bin/env python3
"""Focused checks for the local Studio app server."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from pathlib import Path
import sys
import tempfile

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_audit_api import audit_get_payload, audit_post_response  # noqa: E402
from studio.app.server.studio.studio_app_config import asset_version, runtime_config, validate_studio_route_registry  # noqa: E402
from studio.app.server.studio.studio_app_server import StudioAppRequestHandler, env_flag, parse_args  # noqa: E402
from studio.app.server.studio.studio_app_views import studio_app_bootstrap_view  # noqa: E402
from studio.app.server.studio import studio_catalogue_api  # noqa: E402
from studio.app.server.studio.studio_catalogue_api import catalogue_get_payload, catalogue_post_response  # noqa: E402
from studio.app.server.studio.studio_risk_api import append_risk_activity, risk_delete_response, risk_get_payload, risk_post_response  # noqa: E402


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
    assert payload["app"]["routes"]["studio_home"]["path"] == "/studio/"
    assert payload["app"]["routes"]["studio_home"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["catalogue_work_editor"]["path"] == "/studio/catalogue-work/?mode=manage"
    assert payload["app"]["routes"]["studio_audits"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["studio_risk"]["path"] == "/studio/risk/?mode=manage"
    assert payload["app"]["routes"]["studio_risk"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["project_state"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["bulk_add_work"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["activity"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["catalogue_field_registry"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["catalogue_status"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["studio_works"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["catalogue_series_editor"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["catalogue_work_editor"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["catalogue_work_detail_editor"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["catalogue_moment_editor"]["shell_type"] == "javascript"
    assert payload["app"]["routes"]["project_state"]["shell_type"] == "javascript"
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
    assert not any(str(view["id"]).startswith("ui_catalogue") for view in runtime["views"])
    assert any(view["id"] == "studio_audits" and view["path"] == "/studio/audits/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "studio_risk" and view["path"] == "/studio/risk/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "project_state" and view["path"] == "/studio/project-state/?mode=manage" for view in runtime["views"])
    assert not any(view["id"] == "thumbnail_quality" for view in runtime["views"])
    assert not any("doc_id" in view for view in runtime["views"])
    assert not any("docId" in view for view in runtime["views"])
    assert any(view["id"] == "bulk_add_work" and view["path"] == "/studio/bulk-add-work/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "activity" and view["path"] == "/studio/activity/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_field_registry" and view["path"] == "/studio/catalogue-field-registry/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_status" and view["path"] == "/studio/catalogue-status/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "studio_works" and view["path"] == "/studio/studio-works/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_series_editor" and view["path"] == "/studio/catalogue-series/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_work_editor" and view["path"] == "/studio/catalogue-work/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_work_detail_editor" and view["path"] == "/studio/catalogue-work-detail/?mode=manage" for view in runtime["views"])
    assert any(view["id"] == "catalogue_moment_editor" and view["path"] == "/studio/catalogue-moment/?mode=manage" for view in runtime["views"])
    assert runtime["navigation"]["primary"] == []
    assert "series_tag_editor" not in runtime["navigation"]["primary"]
    assert "analytics" not in runtime["services"]
    assert "data_sharing" not in runtime["services"]
    assert "docs" not in runtime["services"]
    assert "external_links" not in payload
    assert "catalogue" not in payload
    assert set(runtime["data_paths"]) == {"studio", "ui_text"}
    assert set(runtime["data_paths"]["studio"]) == {
        "catalogue_works",
        "catalogue_work_details",
        "catalogue_series",
        "catalogue_moments",
        "catalogue_lookup_work_search",
        "catalogue_lookup_series_search",
        "catalogue_lookup_work_detail_search",
        "catalogue_lookup_work_base",
        "catalogue_lookup_work_detail_base",
        "catalogue_lookup_series_base",
        "catalogue_field_registry",
    }
    assert "docs_viewer" not in runtime["data_paths"].get("ui_text", {})
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
    assert runtime["services"]["catalogue"]["project_state_open_report"] == "/studio/api/catalogue/project-state-open-report"
    assert runtime["services"]["risk"]["base"] == "/studio/api/risk"
    assert runtime["services"]["risk"]["health"] == "/studio/api/risk/health"
    assert runtime["services"]["risk"]["producers"] == "/studio/api/risk/producers"
    assert runtime["services"]["risk"]["runs"] == "/studio/api/risk/runs"
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
    duplicate_path["app"]["routes"]["project_state"]["path"] = routes["studio_audits"]["path"]
    with pytest.raises(RuntimeError, match="duplicate path"):
        validate_studio_route_registry(REPO_ROOT, duplicate_path)

    missing_script = json.loads(json.dumps(payload))
    missing_script["app"]["routes"]["project_state"].pop("script")
    with pytest.raises(RuntimeError, match="project_state: shell route is missing script"):
        validate_studio_route_registry(REPO_ROOT, missing_script)

    unsupported_shell = json.loads(json.dumps(payload))
    unsupported_shell["app"]["routes"]["project_state"]["shell_type"] = "server"
    with pytest.raises(RuntimeError, match="project_state: unsupported shell_type"):
        validate_studio_route_registry(REPO_ROOT, unsupported_shell)

    unserved_route = json.loads(json.dumps(payload))
    unserved_route["app"]["routes"]["unserved_route"] = {
        "label": "unserved",
        "title": "Unserved",
        "path": "/studio/unserved/?mode=manage",
        "script": "/studio/app/frontend/js/project-state.js",
        "nav": False,
        "shell_type": "javascript",
        "ready_state_route_id": "unserved",
    }
    with pytest.raises(RuntimeError, match="unserved_route: no current Studio route serves this shell route"):
        validate_studio_route_registry(REPO_ROOT, unserved_route)

    duplicated_route_metadata = json.loads(json.dumps(payload))
    duplicated_route_metadata["paths"]["routes"] = {
        "catalogue_field_registry_review": "/studio/catalogue-field-registry/?mode=manage"
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
    assert allowed("/studio/data/generated/activity/index.json") is True
    assert allowed("/studio/data/generated/catalogue-lookup/work-search.json") is True
    assert allowed("/assets/docs/interactive/library/coincidence-salience.html") is False
    assert allowed("/data-sharing/config/adapters.json") is False
    assert allowed("/data-sharing/config/library-export-configs.json") is False
    assert allowed("/assets/works/img/00001.jpg") is True
    assert allowed("/assets/js/work.js") is True
    assert allowed("/studio/data/generated/project-state/report.json") is False

    assert allowed("/assets/studio/js/catalogue-work-editor.js") is False
    assert allowed("/assets/ui-catalogue/js/ui-catalogue-demo.js") is False
    assert allowed("/studio/ui-catalogue/assets/js/ui-catalogue-demo.js") is False
    assert allowed("/ui-catalogue/app/assets/js/ui-catalogue-demo.js") is False
    assert allowed("/admin/ui-catalogue/assets/js/ui-catalogue-demo.js") is False
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


def test_public_jekyll_build_and_studio_server_exclude_data_sharing_config() -> None:
    excludes: set[str] = set()
    in_exclude = False
    for line in (REPO_ROOT / "_config.yml").read_text(encoding="utf-8").splitlines():
        if line == "exclude:":
            in_exclude = True
            continue
        if in_exclude and line and not line.startswith("  "):
            break
        if in_exclude and line.startswith("  - "):
            excludes.add(line.removeprefix("  - ").strip())

    assert "data-sharing/config/" in excludes
    assert "admin-app/" in excludes
    assert StudioAppRequestHandler.is_allowed_static_path(object(), "/data-sharing/config/adapters.json") is False
    assert StudioAppRequestHandler.is_allowed_static_path(object(), "/data-sharing/config/library-export-configs.json") is False


def test_local_studio_shells_load_studio_css_without_public_main_css() -> None:
    html_shells = [
        studio_app_bootstrap_view("test-version"),
    ]

    for shell in html_shells:
        assert "/studio/app/assets/css/studio.css?v=test-version" in shell
        assert "/assets/css/main.css" not in shell
        assert "/studio/ui-catalogue/" not in shell
        assert "/ui-catalogue/app/" not in shell
        assert "/admin/ui-catalogue/assets/" not in shell

def test_local_studio_asset_version_does_not_follow_public_main_css() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        public_css = repo_root / "assets" / "css" / "main.css"
        studio_css = repo_root / "studio" / "app" / "assets" / "css" / "studio.css"
        for path in (public_css, studio_css):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("/* fixture */\n", encoding="utf-8")
        os.utime(studio_css, (200, 200))
        os.utime(public_css, (300, 300))

        assert asset_version(repo_root) == "200"


def test_audit_api_routes_return_registry_and_validate_runs() -> None:
    health_payload = audit_get_payload(REPO_ROOT, "/health")
    audits_payload = audit_get_payload(REPO_ROOT, "/audits")

    assert health_payload["ok"] is True
    assert "studio-ready-state" in health_payload["audits"]
    assert audits_payload["ok"] is True
    assert any(audit["audit_id"] == "studio-ready-state" for audit in audits_payload["audits"])

    with pytest.raises(ValueError, match="allowlisted"):
        audit_post_response(REPO_ROOT, "/audits/run", {"audit_id": "not-allowlisted"})


def test_risk_api_lists_producers_runs_and_reads_summary() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        run_dir = repo_root / "var" / "studio" / "risk" / "runs" / "sample-run"
        run_dir.mkdir(parents=True)
        (run_dir / "manifest.json").write_text(
            json.dumps({"run_id": "sample-run", "app": "docs-viewer", "area": "runtime", "created_at_utc": "2026-05-31T12:00:00Z"}),
            encoding="utf-8",
        )
        (run_dir / "summary.json").write_text(
            json.dumps({"run_id": "sample-run", "app": "docs-viewer", "area": "runtime", "status": "passed", "warnings": [], "evidence": [{"artifact": "summary.json"}]}),
            encoding="utf-8",
        )
        (run_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")

        health = risk_get_payload(repo_root, "/health")
        producers = risk_get_payload(repo_root, "/producers")
        runs = risk_get_payload(repo_root, "/runs")
        summary = risk_get_payload(repo_root, "/runs/sample-run/summary")

    assert health["ok"] is True
    assert health["service"] == "studio_risk_evidence"
    assert any(producer["producer_id"] == "runtime-checks" for producer in producers["producers"])
    assert runs["runs"][0]["run_id"] == "sample-run"
    assert runs["runs"][0]["summary_path"] == "var/studio/risk/runs/sample-run/summary.md"
    assert summary["summary"]["status"] == "passed"
    assert summary["summary_markdown"] == "# Summary\n"


def test_risk_api_validates_run_requests_without_command_passthrough() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        risk_post_response(REPO_ROOT, "/runs", {"app": "bad", "area": "runtime", "dry_run": True})
    with pytest.raises(ValueError, match="safe slug"):
        risk_post_response(REPO_ROOT, "/runs", {"app": "docs-viewer", "area": "../bad", "dry_run": True})
    with pytest.raises(ValueError, match="runtime profile"):
        risk_post_response(REPO_ROOT, "/runs", {"app": "docs-viewer", "area": "runtime", "runtime_profiles": ["not-allowed"], "dry_run": True})

    status, payload = risk_post_response(
        REPO_ROOT,
        "/runs",
        {"app": "docs-viewer", "area": "runtime", "run_id": "risk-api-dry-run", "dry_run": True},
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert "risk_evidence_pack.py" in payload["stdout"] or "Risk evidence pack dry run" in payload["stdout"]


def test_risk_api_deletes_run_snapshots_with_path_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        run_dir = repo_root / "var" / "studio" / "risk" / "runs" / "sample-run"
        run_dir.mkdir(parents=True)
        (run_dir / "summary.json").write_text(
            json.dumps({"run_id": "sample-run", "app": "docs-viewer", "area": "runtime", "status": "passed"}),
            encoding="utf-8",
        )
        (run_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")

        status, payload = risk_delete_response(repo_root, "/runs/sample-run")

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["status"] == "deleted"
        assert payload["run_id"] == "sample-run"
        assert payload["deleted_path"] == "var/studio/risk/runs/sample-run"
        assert not run_dir.exists()

        with pytest.raises(FileNotFoundError, match="does not exist"):
            risk_delete_response(repo_root, "/runs/sample-run")
        with pytest.raises(ValueError, match="safe slug"):
            risk_delete_response(repo_root, "/runs/../bad")


def test_risk_activity_append_uses_contract_context() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        contract_target = repo_root / "studio" / "data" / "config" / "runtime" / "activity-contract.json"
        contract_target.parent.mkdir(parents=True)
        contract_target.write_text(
            (REPO_ROOT / "studio" / "data" / "config" / "runtime" / "activity-contract.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        run_id = "risk-api-activity-test"
        response = {
            "ok": True,
            "status": "passed",
            "app": "docs-viewer",
            "area": "runtime",
            "run_id": run_id,
            "summary_path": f"var/studio/risk/runs/{run_id}/summary.md",
        }

        append_risk_activity(
            repo_root,
            {
                "activity_context": {
                    "page_id": "studio-risk",
                    "action_id": "run-risk-evidence",
                    "route": "/studio/risk/?mode=manage",
                    "control_id": "studioRiskRun",
                    "control_selector": "#studioRiskRun",
                    "correlation_id": f"pytest:{run_id}",
                    "run_id": run_id,
                },
            },
            response,
            "2026-05-31T12:00:00Z",
        )

        activity_path = repo_root / "var" / "studio" / "activity" / "activity_log.json"
        activity_payload = json.loads(activity_path.read_text(encoding="utf-8"))

    assert response["activity_log"]["written_count"] == 1
    assert activity_payload["entries"][0]["page_id"] == "studio-risk"
    assert activity_payload["entries"][0]["script_purpose_id"] == "generate-report"


def test_catalogue_project_state_route_uses_fixture_source(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        projects_base = Path(tmp_dir) / "source"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
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


def test_catalogue_read_route_returns_source_and_activity_payloads() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
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
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
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

        assert status == HTTPStatus.OK
        assert preview_payload["preview"]["summary"]["importable_count"] == 1
        assert preview_payload["preview"]["importable_ids"] == ["00042"]
        assert apply_status == HTTPStatus.OK
        assert apply_payload["dry_run"] is True
        assert apply_payload["would_write"] is True
        assert json.loads((source_dir / "works.json").read_text(encoding="utf-8"))["works"] == {}


def test_catalogue_write_service_routes_are_registered() -> None:
    service_paths = studio_catalogue_api.catalogue_write_service.SERVICE_POST_PATHS
    assert {
        "/bulk-save",
        "/work/create",
        "/work/save",
        "/work-detail/create",
        "/work-detail/save",
        "/series/create",
        "/series/save",
        "/delete-preview",
        "/delete-apply",
        "/publication-preview",
        "/publication-apply",
        "/build-preview",
        "/build-apply",
        "/moment/preview",
        "/moment/save",
        "/prose/import-preview",
        "/prose/import-apply",
        "/moment/import-preview",
        "/moment/import-apply",
    } <= service_paths


def test_catalogue_delete_preview_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {"00042": {"work_id": "00042", "title": "Draft", "status": "draft", "series_ids": []}}}),
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
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
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


def test_catalogue_editor_create_work_detail_dry_run_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        (source_dir / "works.json").write_text(
            json.dumps(
                {
                    "catalogue_source_works_version": "catalogue_source_works_v1",
                    "works": {
                        "00042": {
                            "work_id": "00042",
                            "title": "Published Work",
                            "status": "published",
                            "series_ids": [],
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
        (source_dir / "moments.json").write_text(
            json.dumps({"catalogue_source_moments_version": "catalogue_source_moments_v1", "moments": {}}),
            encoding="utf-8",
        )

        status, payload = catalogue_post_response(
            repo_root,
            "/work-detail/create",
            {
                "work_id": "42",
                "detail_id": "1",
                "record": {
                    "title": "Detail",
                    "section_title": "Details",
                    "status": "draft",
                },
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["detail_uid"] == "00042-001"
        assert payload["work_id"] == "00042"
        assert payload["created"] is True
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert json.loads((source_dir / "work_details.json").read_text(encoding="utf-8"))["work_details"] == {}


def test_catalogue_editor_save_work_dry_run_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
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


def test_catalogue_editor_save_work_detail_dry_run_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        (source_dir / "works.json").write_text(
            json.dumps(
                {
                    "catalogue_source_works_version": "catalogue_source_works_v1",
                    "works": {
                        "00042": {
                            "work_id": "00042",
                            "title": "Published Work",
                            "status": "published",
                            "series_ids": [],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        (source_dir / "work_details.json").write_text(
            json.dumps(
                {
                    "catalogue_source_work_details_version": "catalogue_source_work_details_v1",
                    "work_details": {
                        "00042-001": {
                            "detail_uid": "00042-001",
                            "work_id": "00042",
                            "detail_id": "001",
                            "title": "Original Detail",
                            "section_id": "00042-1",
                            "section_title": "Details",
                            "status": "draft",
                        }
                    },
                }
            ),
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
        registry_target = repo_root / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json"
        registry_target.parent.mkdir(parents=True, exist_ok=True)
        registry_target.write_text((REPO_ROOT / "studio" / "data" / "config" / "catalogue" / "catalogue-field-registry.json").read_text(encoding="utf-8"), encoding="utf-8")

        status, payload = catalogue_post_response(
            repo_root,
            "/work-detail/save",
            {
                "detail_uid": "00042-001",
                "record": {
                    "title": "Updated Detail",
                },
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["detail_uid"] == "00042-001"
        assert payload["work_id"] == "00042"
        assert payload["changed"] is True
        assert payload["changed_fields"] == ["title"]
        assert payload["dry_run"] is True
        assert payload["would_write"] is True
        assert "build_plan" in payload
        assert json.loads((source_dir / "work_details.json").read_text(encoding="utf-8"))["work_details"]["00042-001"]["title"] == "Original Detail"


def test_catalogue_editor_create_series_dry_run_uses_callable_service_route() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
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
        (source_dir / "moments.json").write_text(
            json.dumps({"catalogue_source_moments_version": "catalogue_source_moments_v1", "moments": {}}),
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


if __name__ == "__main__":
    test_runtime_config_exposes_adapter_contract()
    test_static_path_policy_serves_current_studio_allowlists()
    test_local_studio_shells_load_studio_css_without_public_main_css()
    test_local_studio_asset_version_does_not_follow_public_main_css()
    print("studio app server tests OK")
