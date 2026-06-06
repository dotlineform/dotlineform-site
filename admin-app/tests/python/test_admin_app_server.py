#!/usr/bin/env python3
"""Focused checks for the local Admin app server."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_SERVER_DIR = REPO_ROOT / "admin-app" / "app" / "server"
ADMIN_PACKAGE_DIR = ADMIN_SERVER_DIR / "admin_app"
for path in (REPO_ROOT, ADMIN_SERVER_DIR, ADMIN_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from admin_activity_api import activity_get_payload  # noqa: E402
from admin_app_config import load_admin_config, runtime_config, validate_admin_route_registry  # noqa: E402
from admin_app_server import AdminAppRequestHandler, env_flag, parse_args  # noqa: E402
from admin_app_views import admin_activity_view, admin_audits_view, admin_home_view, admin_risk_view, admin_testing_view  # noqa: E402
from admin_testing_api import testing_get_payload as admin_testing_get_payload  # noqa: E402


def test_runtime_config_exposes_admin_home_and_planned_routes() -> None:
    payload = runtime_config(REPO_ROOT, "test-version")
    runtime = payload["app"]["runtime"]

    assert runtime["host"] == "local-admin-app"
    assert runtime["asset_version"] == "test-version"
    assert runtime["routes"]["home"] == "/admin/"
    assert runtime["routes"]["runtime_config"] == "/admin/runtime-config.json"
    assert payload["app"]["routes"]["admin_home"]["path"] == "/admin/"
    assert payload["app"]["routes"]["admin_audits"]["path"] == "/admin/audits/"
    assert payload["app"]["routes"]["admin_audits"]["script"] == "/admin/app/frontend/js/admin-audits.js"
    assert payload["app"]["routes"]["admin_risk"]["path"] == "/admin/risk/"
    assert payload["app"]["routes"]["admin_risk"]["script"] == "/admin/app/frontend/js/admin-risk.js"
    assert payload["app"]["routes"]["admin_activity"]["path"] == "/admin/activity/"
    assert payload["app"]["routes"]["admin_activity"]["script"] == "/admin/app/frontend/js/admin-activity.js"
    assert payload["app"]["routes"]["admin_testing"]["path"] == "/admin/testing/"
    assert payload["app"]["routes"]["admin_testing"]["script"] == "/admin/app/frontend/js/admin-testing.js"
    assert payload["app"]["routes"]["admin_ui_catalogue"]["path"] == "/admin/ui-catalogue/"
    assert any(view["id"] == "admin_home" and view["path"] == "/admin/" for view in runtime["views"])
    assert runtime["data_paths"]["ui_text"]["admin_home"] == "/admin/app/frontend/config/ui-text/admin-home.json"
    assert runtime["services"]["audits"]["run"] == "/admin/api/audits/audits/run"
    assert runtime["services"]["risk"]["runs"] == "/admin/api/risk/runs"
    assert runtime["services"]["testing"]["runs"] == "/admin/api/testing/runs"
    assert runtime["services"]["activity"]["feed"] == "/admin/api/activity/feed"
    assert runtime["data_paths"]["activity"]["feed"] == "var/admin/activity/activity_log.json"
    assert runtime["data_paths"]["risk"]["runs"] == "var/admin/risk/runs"
    assert runtime["data_paths"]["testing"]["runs"] == "var/admin/test-runs"


def test_admin_route_registry_validates_home_script() -> None:
    payload = load_admin_config(REPO_ROOT)
    validate_admin_route_registry(REPO_ROOT, payload)

    payload["app"]["routes"]["admin_home"]["script"] = "/admin/app/frontend/js/missing.js"
    try:
        validate_admin_route_registry(REPO_ROOT, payload)
    except RuntimeError as error:
        assert "script does not exist" in str(error)
    else:  # pragma: no cover
        raise AssertionError("missing Admin home script was not rejected")


def test_static_path_policy_serves_only_admin_app_assets() -> None:
    def allowed(path: str) -> bool:
        return AdminAppRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/admin/app/assets/css/admin.css") is True
    assert allowed("/admin/app/frontend/js/admin-home.js") is True
    assert allowed("/admin/app/frontend/js/admin-theme.js") is True
    assert allowed("/admin/app/frontend/js/admin-audits.js") is True
    assert allowed("/admin/app/frontend/js/admin-risk.js") is True
    assert allowed("/admin/app/frontend/js/admin-activity.js") is True
    assert allowed("/admin/app/frontend/js/admin-testing.js") is True
    assert allowed("/admin/app/frontend/config/admin-config.json") is True
    assert allowed("/admin/app/frontend/config/ui-text/admin-home.json") is True

    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/analytics/app/assets/css/analytics.css") is False
    assert allowed("/ui-catalogue/app/assets/css/ui-catalogue-demo.css") is False
    assert allowed("/docs-viewer/generated/docs/studio/index.json") is False


def test_admin_home_renders_visible_navigation() -> None:
    html = admin_home_view("test-version", REPO_ROOT)

    assert "dotlineform admin" in html
    assert 'href="/admin/audits/"' in html
    assert 'href="/admin/risk/"' in html
    assert 'href="/admin/activity/"' in html
    assert 'href="/admin/testing/"' in html
    assert 'href="/admin/ui-catalogue/"' in html
    assert 'class="studioHomeLinks__pill"' in html
    assert "Admin home links" in html
    assert "data-admin-theme-toggle" in html
    assert "/admin/app/assets/css/admin.css?v=test-version" in html
    assert "/admin/app/frontend/js/admin-theme.js?v=test-version" in html
    assert "/admin/app/frontend/js/admin-home.js?v=test-version" in html
    assert 'data-admin-ready="false"' in html


def test_admin_route_views_render_admin_owned_shells() -> None:
    audits_html = admin_audits_view("test-version")
    risk_html = admin_risk_view("test-version")
    activity_html = admin_activity_view("test-version")
    testing_html = admin_testing_view("test-version")

    assert "/admin/app/frontend/js/admin-audits.js?v=test-version" in audits_html
    assert 'data-admin-route="admin-audits"' in audits_html
    assert "/admin/app/frontend/js/admin-risk.js?v=test-version" in risk_html
    assert 'data-admin-route="admin-risk"' in risk_html
    assert "/admin/app/frontend/js/admin-activity.js?v=test-version" in activity_html
    assert 'data-admin-route="admin-activity"' in activity_html
    assert "/admin/app/frontend/js/admin-testing.js?v=test-version" in testing_html
    assert 'data-admin-route="admin-testing"' in testing_html
    for html in (audits_html, risk_html, activity_html, testing_html):
        assert 'meta name="dlf-admin-config-url" content="/admin/runtime-config.json"' in html
        assert "data-admin-theme-toggle" in html
        assert "/admin/app/frontend/js/admin-theme.js?v=test-version" in html


def test_admin_activity_api_returns_empty_admin_feed(tmp_path) -> None:
    payload = activity_get_payload(tmp_path, "/feed")

    assert payload["ok"] is True
    assert payload["header"]["schema"] == "admin_activity_log_v1"
    assert payload["entries"] == []


def test_admin_testing_api_reads_admin_run_summaries(tmp_path) -> None:
    run_dir = tmp_path / "var" / "admin" / "test-runs" / "sample-run"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        '{"profiles":["quick"],"status":"passed","run_dir":"var/admin/test-runs/sample-run","results":[]}\n',
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text("# Check Run Summary\n", encoding="utf-8")

    payload = admin_testing_get_payload(tmp_path, "/runs")

    assert payload["ok"] is True
    assert payload["runs_root"] == "var/admin/test-runs"
    assert payload["runs"][0]["run_id"] == "sample-run"
    assert payload["runs"][0]["profiles"] == ["quick"]
    assert payload["runs"][0]["summary_path"] == "var/admin/test-runs/sample-run/summary.md"


def test_access_log_is_opt_in(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_APP_ACCESS_LOG", raising=False)
    assert env_flag("ADMIN_APP_ACCESS_LOG") is False
    assert parse_args([]).access_log is False

    monkeypatch.setenv("ADMIN_APP_ACCESS_LOG", "1")
    assert env_flag("ADMIN_APP_ACCESS_LOG") is True
    assert parse_args([]).access_log is True
    assert parse_args(["--access-log"]).access_log is True

    monkeypatch.setenv("ADMIN_APP_ACCESS_LOG", "0")
    assert parse_args([]).access_log is False
    assert parse_args(["--access-log"]).access_log is True
