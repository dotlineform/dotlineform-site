#!/usr/bin/env python3
"""Smoke-check the local Analytics app Tag Groups view."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from analytics_app_server import AnalyticsAppServer  # noqa: E402


def start_server() -> tuple[AnalyticsAppServer, str]:
    server = AnalyticsAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/analytics/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        runtime_routes = runtime_config.get("app", {}).get("runtime", {}).get("routes", {})
        if runtime_config.get("analytics_config_version") != "analytics_config_v1":
            raise AssertionError("runtime config did not include the Analytics config payload")
        if runtime_config.get("app", {}).get("runtime", {}).get("host") != "local-analytics-app":
            raise AssertionError("runtime config did not include local app runtime metadata")
        if runtime_routes.get("runtime_config") != "/analytics/runtime-config.json":
            raise AssertionError(f"unexpected runtime config route metadata: {runtime_routes!r}")
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        tag_groups_view = next((view for view in runtime_views if view.get("id") == "tag_groups"), None)
        if not tag_groups_view or tag_groups_view.get("path") != "/analytics/tag-groups/":
            raise AssertionError(f"runtime config did not include the Tag Groups view: {runtime_views!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            config_requests: list[str] = []
            analytics_requests: list[str] = []
            static_group_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on(
                "request",
                lambda request: config_requests.append(request.url)
                if "/analytics/runtime-config.json" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: analytics_requests.append(request.url)
                if "/analytics/api/tag-groups" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: static_group_requests.append(request.url)
                if "/analytics/data/canonical/tag-groups.json" in request.url
                else None,
            )
            page.goto(f"{base_url}/analytics/tag-groups/", wait_until="domcontentloaded")
            nav_script_count = page.locator('script[src*="analytics-navigation.js"]').count()
            page.wait_for_selector('#tag-groups[data-analytics-ready="true"]', timeout=10000)
            mode = page.locator("#tag-groups").get_attribute("data-analytics-mode")
            record_loaded = page.locator("#tag-groups").get_attribute("data-analytics-record-loaded")
            chips = page.locator(".tagGroups__section .analytics__keyPill").all_text_contents()
            doc_link_count = page.locator(".studioLayout__docLink").count()
            content_text = page.locator('[data-role="content"]').inner_text()
            browser.close()

        expected_groups = {"subject", "domain", "form", "theme"}
        if nav_script_count != 1:
            raise AssertionError(f"expected one navigation script on Analytics route, got {nav_script_count}")
        if mode != "list":
            raise AssertionError(f"expected list mode, got {mode!r}")
        if record_loaded != "true":
            raise AssertionError(f"expected record loaded, got {record_loaded!r}")
        if expected_groups - set(chips):
            raise AssertionError(f"missing expected group chips: {sorted(expected_groups - set(chips))}")
        if doc_link_count:
            raise AssertionError("Tag Groups still renders header doc pill")
        if "No group descriptions available" in content_text:
            raise AssertionError("Tag Groups rendered empty fallback unexpectedly")
        if not config_requests:
            raise AssertionError("Tag Groups did not request the local runtime config endpoint")
        if not analytics_requests:
            raise AssertionError("Tag Groups did not request the local analytics API")
        if static_group_requests:
            raise AssertionError(f"Tag Groups should use the local analytics API instead of static data: {static_group_requests!r}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        print(f"local Analytics Tag Groups OK: {base_url}/analytics/tag-groups/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
