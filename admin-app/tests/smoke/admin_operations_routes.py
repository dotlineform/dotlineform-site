#!/usr/bin/env python3
"""Smoke-check Admin audits, risk, and activity routes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
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


DELETE_FIXTURE_RUN_ID = "admin-risk-route-smoke-delete-snapshot"


def start_server() -> tuple[AdminAppServer, str]:
    server = AdminAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def write_delete_fixture() -> Path:
    run_dir = REPO_ROOT / "var" / "admin" / "risk" / "runs" / DELETE_FIXTURE_RUN_ID
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    created_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": DELETE_FIXTURE_RUN_ID, "app": "docs-viewer", "area": "runtime", "created_at_utc": created_at}),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps({"run_id": DELETE_FIXTURE_RUN_ID, "app": "docs-viewer", "area": "runtime", "status": "passed", "warnings": [], "evidence": []}),
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text("# Smoke delete snapshot\n", encoding="utf-8")
    return run_dir


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
        "admin_risk": "/admin/risk/",
        "admin_activity": "/admin/activity/",
    }
    for route_id, path in expected.items():
        runtime_view = runtime_by_id.get(route_id)
        if not runtime_view or runtime_view.get("path") != path:
            raise AssertionError(f"runtime config missing {route_id}: {runtime_views!r}")
    if runtime.get("services", {}).get("audits", {}).get("audits") != "/admin/api/audits/audits":
        raise AssertionError("runtime config missing Admin audit API")
    if runtime.get("services", {}).get("risk", {}).get("runs") != "/admin/api/risk/runs":
        raise AssertionError("runtime config missing Admin risk API")
    if runtime.get("services", {}).get("activity", {}).get("feed") != "/admin/api/activity/feed":
        raise AssertionError("runtime config missing Admin activity API")


def assert_api_payloads(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/admin/api/audits/audits", timeout=10) as response:
        audits_payload = json.loads(response.read().decode("utf-8"))
    if not audits_payload.get("ok") or not any(
        audit.get("audit_id") == "studio-ready-state"
        for audit in audits_payload.get("audits", [])
        if isinstance(audit, dict)
    ):
        raise AssertionError(f"Admin audits API returned unexpected payload: {audits_payload!r}")

    with urllib.request.urlopen(f"{base_url}/admin/api/risk/producers", timeout=10) as response:
        producers_payload = json.loads(response.read().decode("utf-8"))
    if not producers_payload.get("ok") or not any(
        producer.get("producer_id") == "runtime-checks"
        for producer in producers_payload.get("producers", [])
        if isinstance(producer, dict)
    ):
        raise AssertionError(f"Admin risk API returned unexpected payload: {producers_payload!r}")


def run_browser_smoke(base_url: str, delete_fixture_run_dir: Path) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        console_errors: list[str] = []
        page_errors: list[str] = []

        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        page.goto(f"{base_url}/admin/audits/", wait_until="domcontentloaded")
        audits_root = page.locator("#studioAuditsRoot")
        expect(audits_root).to_be_visible(timeout=10_000)
        expect(audits_root).to_have_attribute("data-admin-ready", "true", timeout=10_000)
        expect(audits_root).to_have_attribute("data-admin-mode", "summary", timeout=10_000)
        expect(page.locator("[data-run-audit]").first).to_be_enabled(timeout=10_000)

        page.goto(f"{base_url}/admin/risk/", wait_until="domcontentloaded")
        risk_root = page.locator("#studioRiskRoot")
        expect(risk_root).to_be_visible(timeout=10_000)
        expect(risk_root).to_have_attribute("data-admin-ready", "true", timeout=10_000)
        expect(risk_root).to_have_attribute("data-admin-service", "available", timeout=10_000)
        expect(page.locator("#studioRiskRun")).to_be_enabled(timeout=10_000)
        expect(page.locator("#studioRiskApp")).to_have_value("docs-viewer")
        delete_button = page.locator(f'[data-risk-run-delete="{DELETE_FIXTURE_RUN_ID}"]')
        expect(delete_button).to_be_visible(timeout=10_000)
        page.once("dialog", lambda dialog: dialog.accept())
        delete_button.click()
        expect(page.locator("#studioRiskStatus")).to_contain_text("deleted", timeout=10_000)
        if delete_fixture_run_dir.exists():
            raise AssertionError(f"delete fixture still exists: {delete_fixture_run_dir}")
        page.locator("#studioRiskDryRun").check()
        page.locator("#studioRiskRunId").fill("admin-risk-route-smoke-dry-run")
        page.locator("#studioRiskRun").click()
        expect(page.locator("#studioRiskStatus")).to_contain_text("completed", timeout=10_000)
        page.route(
            "**/admin/api/risk/runs",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "ok": False,
                        "status": "failed",
                        "run_id": "admin-risk-route-smoke-failed-run",
                        "dry_run": True,
                    }
                ),
            )
            if route.request.method == "POST"
            else route.continue_(),
        )
        page.locator("#studioRiskRunId").fill("admin-risk-route-smoke-failed-run")
        page.locator("#studioRiskRun").click()
        expect(page.locator("#studioRiskStatus")).to_contain_text("Risk evidence run failed.", timeout=10_000)

        page.route(
            "**/admin/api/activity/feed",
            lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(activity_feed())),
        )
        page.goto(f"{base_url}/admin/activity/", wait_until="domcontentloaded")
        activity_root = page.locator("#studioActivityRoot")
        expect(activity_root).to_be_visible(timeout=10_000)
        expect(activity_root).to_have_attribute("data-admin-ready", "true", timeout=10_000)
        expect(activity_root).to_have_attribute("data-admin-mode", "list", timeout=10_000)
        expect(page.locator("[data-activity-id='admin-activity-smoke']")).to_be_visible(timeout=10_000)
        page.locator("[data-activity-id='admin-activity-smoke']").click()
        expect(page.locator("[data-role='admin-modal']")).to_be_visible(timeout=10_000)
        modal_body = page.locator("[data-role='admin-modal'] .tagStudioModal__label").all_inner_texts()
        if modal_body != ["Wrote source JSON", "Updated Admin activity feed"]:
            raise AssertionError(f"unexpected activity modal body: {modal_body!r}")

        page.close()
        browser.close()

    if console_errors:
        raise AssertionError(f"console errors: {console_errors}")
    if page_errors:
        raise AssertionError(f"page errors: {page_errors}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    delete_fixture_run_dir = write_delete_fixture()
    server, base_url = start_server()
    try:
        assert_runtime(base_url)
        assert_api_payloads(base_url)
        run_browser_smoke(base_url, delete_fixture_run_dir)
        print(f"Admin operations routes OK: {base_url}/admin/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
