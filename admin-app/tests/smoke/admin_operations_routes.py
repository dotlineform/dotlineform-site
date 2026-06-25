#!/usr/bin/env python3
"""Smoke-check Admin audits, checks, and activity routes."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "admin-app" / "app" / "server" / "admin_app"
sys.path.insert(0, str(SERVER_DIR))

from admin_app_server import AdminAppServer  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


def start_server() -> tuple[AdminAppServer, str]:
    server = AdminAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def activity_feed() -> dict[str, object]:
    return {
        "ok": True,
        "header": {
            "schema": "admin_activity_log_v1",
            "count": 1,
        },
        "entries": [
            {
                "id": "admin-activity-smoke",
                "activity_id": "admin-activity-smoke",
                "time_utc": "2026-05-15T10:00:00Z",
                "timestamp": "2026-05-15T10:00:00Z",
                "status": "completed",
                "page_label": "Catalogue Work",
                "user_action_label": "Save work",
                "script_purpose_label": "Save catalogue source",
                "detail_items": ["Wrote source JSON", "Updated Admin activity feed"],
                "record_groups": {"works": {"count": 1}},
            }
        ],
    }


def assert_runtime(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/admin/runtime-config.json", timeout=10) as response:
        runtime_config = json.loads(response.read().decode("utf-8"))
    runtime = runtime_config.get("app", {}).get("runtime", {})
    runtime_views = runtime.get("views", [])
    runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
    expected = {
        "admin_audits": "/admin/audits/",
        "admin_checks": "/admin/checks/",
        "admin_activity": "/admin/activity/",
    }
    for route_id, path in expected.items():
        runtime_view = runtime_by_id.get(route_id)
        if not runtime_view or runtime_view.get("path") != path:
            raise AssertionError(f"runtime config missing {route_id}: {runtime_views!r}")
        if runtime_view.get("shell_type") != "html-template":
            raise AssertionError(f"runtime config missing template shell type for {route_id}: {runtime_view!r}")
        if not str(runtime_view.get("template") or "").startswith("/admin/app/frontend/routes/"):
            raise AssertionError(f"runtime config missing route template for {route_id}: {runtime_view!r}")
    if runtime.get("services", {}).get("audits", {}).get("audits") != "/admin/api/audits/audits":
        raise AssertionError("runtime config missing Admin audit API")
    if runtime.get("services", {}).get("checks", {}).get("runs") != "/admin/api/checks/runs":
        raise AssertionError("runtime config missing Admin checks API")
    if runtime.get("services", {}).get("activity", {}).get("feed") != "/admin/api/activity/feed":
        raise AssertionError("runtime config missing Admin activity API")
    if "admin_risk" in runtime_by_id or "risk" in runtime.get("services", {}):
        raise AssertionError(f"runtime config still exposes retired Admin risk route/API: {runtime!r}")


def assert_api_payloads(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/admin/api/audits/audits", timeout=10) as response:
        audits_payload = json.loads(response.read().decode("utf-8"))
    if not audits_payload.get("ok") or not any(
        audit.get("audit_id") == "route-ready-state"
        for audit in audits_payload.get("audits", [])
        if isinstance(audit, dict)
    ):
        raise AssertionError(f"Admin audits API returned unexpected payload: {audits_payload!r}")

    with urllib.request.urlopen(f"{base_url}/admin/api/checks/reports", timeout=10) as response:
        checks_payload = json.loads(response.read().decode("utf-8"))
    if not checks_payload.get("ok") or not any(
        report.get("id") == "files"
        for report in checks_payload.get("reports", [])
        if isinstance(report, dict)
    ):
        raise AssertionError(f"Admin checks API returned unexpected payload: {checks_payload!r}")


def run_browser_smoke(base_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        console_errors: list[str] = []
        page_errors: list[str] = []

        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        page.goto(f"{base_url}/admin/audits/", wait_until="domcontentloaded")
        if page.locator("[data-admin-route-outlet]").count() != 1:
            raise AssertionError("Admin audits did not render the static Admin shell outlet")
        audits_root = page.locator("#studioAuditsRoot")
        wait_for_route_ready(page, "#studioAuditsRoot", "data-admin-ready", "data-admin-busy")
        expect(audits_root).to_have_attribute("data-admin-mode", "summary", timeout=10_000)
        expect(page.locator("[data-run-audit]").first).to_be_enabled(timeout=10_000)

        page.goto(f"{base_url}/admin/checks/", wait_until="domcontentloaded")
        if page.locator("[data-admin-route-outlet]").count() != 1:
            raise AssertionError("Admin checks did not render the static Admin shell outlet")
        checks_root = page.locator("#studioChecksRoot")
        wait_for_route_ready(page, "#studioChecksRoot", "data-admin-ready", "data-admin-busy")
        expect(checks_root).to_have_attribute("data-admin-service", "available", timeout=10_000)
        expect(page.locator("#studioChecksRun")).to_be_enabled(timeout=10_000)
        expect(page.locator("#studioChecksReport")).to_have_value("files")

        page.route(
            "**/admin/api/activity/feed",
            lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(activity_feed())),
        )
        page.goto(f"{base_url}/admin/activity/", wait_until="domcontentloaded")
        if page.locator("[data-admin-route-outlet]").count() != 1:
            raise AssertionError("Admin activity did not render the static Admin shell outlet")
        activity_root = page.locator("#studioActivityRoot")
        wait_for_route_ready(page, "#studioActivityRoot", "data-admin-ready", "data-admin-busy")
        expect(activity_root).to_have_attribute("data-admin-mode", "list", timeout=10_000)
        expect(page.locator("[data-activity-id='admin-activity-smoke']")).to_be_visible(timeout=10_000)

        page.close()
        browser.close()

    if console_errors:
        raise AssertionError(f"console errors: {console_errors}")
    if page_errors:
        raise AssertionError(f"page errors: {page_errors}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        assert_runtime(base_url)
        assert_api_payloads(base_url)
        run_browser_smoke(base_url)
        print(f"Admin operations routes OK: {base_url}/admin/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
