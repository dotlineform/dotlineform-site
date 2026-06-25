#!/usr/bin/env python3
"""Smoke-check the local Admin Testing route ready-state boundary."""

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


ROOT_SELECTOR = "#adminTestingRoot"


def start_server() -> tuple[AdminAppServer, str]:
    server = AdminAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def read_json_url(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_runtime(base_url: str) -> None:
    runtime_config = read_json_url(f"{base_url}/admin/runtime-config.json")
    runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
    runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
    runtime_view = runtime_by_id.get("admin_testing")
    if not runtime_view or runtime_view.get("path") != "/admin/testing/":
        raise AssertionError(f"runtime config missing admin_testing: {runtime_views!r}")
    if runtime_view.get("shell_type") != "html-template":
        raise AssertionError(f"runtime config missing template shell type for admin_testing: {runtime_view!r}")
    if runtime_view.get("template") != "/admin/app/frontend/routes/admin-testing.html":
        raise AssertionError(f"runtime config missing Admin Testing template: {runtime_view!r}")
    services = runtime_config.get("app", {}).get("runtime", {}).get("services", {})
    if services.get("testing", {}).get("runs") != "/admin/api/testing/runs":
        raise AssertionError(f"runtime config missing Admin Testing runs API: {services!r}")


def assert_success_route(page, base_url: str) -> None:
    page.goto(f"{base_url}/admin/testing/", wait_until="domcontentloaded")
    if page.locator("[data-admin-route-outlet]").count() != 1:
        raise AssertionError("Admin Testing did not render the static Admin shell outlet")
    root = page.locator(ROOT_SELECTOR)
    wait_for_route_ready(page, ROOT_SELECTOR, "data-admin-ready", "data-admin-busy")
    expect(root).to_have_attribute("data-admin-route", "admin-testing", timeout=10_000)
    expect(root).to_have_attribute("data-admin-mode", "list", timeout=10_000)
    expect(root).to_have_attribute("data-admin-service", "available", timeout=10_000)
    expect(root).to_have_attribute("data-admin-record-loaded", "true", timeout=10_000)
    expect(page.locator("#adminTestingStatus")).to_have_attribute("data-state", "success", timeout=10_000)
    expect(page.locator("#adminTestingStatus")).to_contain_text("Admin test runs:", timeout=10_000)


def assert_unavailable_route(page, base_url: str) -> None:
    page.route(
        "**/admin/api/testing/runs",
        lambda route: route.fulfill(status=503, content_type="application/json", body='{"ok": false}'),
    )
    page.goto(f"{base_url}/admin/testing/", wait_until="domcontentloaded")
    root = page.locator(ROOT_SELECTOR)
    wait_for_route_ready(page, ROOT_SELECTOR, "data-admin-ready", "data-admin-busy")
    expect(root).to_have_attribute("data-admin-mode", "unavailable", timeout=10_000)
    expect(root).to_have_attribute("data-admin-service", "unavailable", timeout=10_000)
    expect(root).to_have_attribute("data-admin-record-loaded", "false", timeout=10_000)
    expect(page.locator("#adminTestingStatus")).to_have_attribute("data-state", "error", timeout=10_000)
    expect(page.locator("#adminTestingStatus")).to_contain_text("testing API returned 503", timeout=10_000)


def run_browser_smoke(base_url: str) -> None:
    def collect_console_error(message) -> None:
        text = message.text
        if "Failed to load resource" in text and "503" in text:
            return
        console_errors.append(text)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        console_errors: list[str] = []
        page_errors: list[str] = []

        success_page = browser.new_page(viewport={"width": 1280, "height": 900})
        success_page.on("console", lambda message: collect_console_error(message) if message.type == "error" else None)
        success_page.on("pageerror", lambda error: page_errors.append(str(error)))
        assert_success_route(success_page, base_url)
        success_page.close()

        unavailable_page = browser.new_page(viewport={"width": 1280, "height": 900})
        unavailable_page.on("console", lambda message: collect_console_error(message) if message.type == "error" else None)
        unavailable_page.on("pageerror", lambda error: page_errors.append(str(error)))
        assert_unavailable_route(unavailable_page, base_url)
        unavailable_page.close()

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
        run_browser_smoke(base_url)
        print(f"Admin Testing route OK: {base_url}/admin/testing/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
