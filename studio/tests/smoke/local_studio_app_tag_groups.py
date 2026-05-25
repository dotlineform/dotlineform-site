#!/usr/bin/env python3
"""Smoke-check the local Studio app Tag Groups view."""

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

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        runtime_routes = runtime_config.get("app", {}).get("runtime", {}).get("routes", {})
        if runtime_config.get("studio_config_version") != "studio_config_v1":
            raise AssertionError("runtime config did not include the Studio config payload")
        if runtime_config.get("app", {}).get("runtime", {}).get("host") != "local-studio-app":
            raise AssertionError("runtime config did not include local app runtime metadata")
        if runtime_routes.get("runtime_config") != "/studio/runtime-config.json":
            raise AssertionError(f"unexpected runtime config route metadata: {runtime_routes!r}")
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        tag_groups_view = next((view for view in runtime_views if view.get("id") == "tag_groups"), None)
        if not tag_groups_view or tag_groups_view.get("path") != "/studio/analytics/tag-groups/":
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
                if "/studio/runtime-config.json" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: analytics_requests.append(request.url)
                if "/studio/api/analytics/tag-groups" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: static_group_requests.append(request.url)
                if "/studio/data/canonical/analytics/tag-groups.json" in request.url
                else None,
            )
            page.goto(f"{base_url}/studio/", wait_until="domcontentloaded")
            page.wait_for_selector('[data-studio-navigate="tag_groups"]', timeout=10000)
            docs_home_link = page.locator('.studioLinkList__item[data-studio-navigate="docs"]').get_attribute("href")
            home_link = page.locator('.studioLinkList__item[data-studio-navigate="tag_groups"]').get_attribute("href")
            nav_script_count = page.locator('script[src*="studio-navigation.js"]').count()
            page.locator('.studioLinkList__item[data-studio-navigate="tag_groups"]').click()
            page.wait_for_url("**/studio/analytics/tag-groups/", timeout=10000)
            page.wait_for_selector('#tag-groups[data-studio-ready="true"]', timeout=10000)
            mode = page.locator("#tag-groups").get_attribute("data-studio-mode")
            record_loaded = page.locator("#tag-groups").get_attribute("data-studio-record-loaded")
            chips = page.locator(".tagGroups__section .tagStudio__keyPill").all_text_contents()
            doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
            content_text = page.locator('[data-role="content"]').inner_text()
            browser.close()

        expected_groups = {"subject", "domain", "form", "theme"}
        if not docs_home_link.startswith("http://127.0.0.1:") or not docs_home_link.endswith("/docs/?mode=manage"):
            raise AssertionError(f"unexpected home Docs navigation href: {docs_home_link!r}")
        if home_link != "/studio/analytics/tag-groups/":
            raise AssertionError(f"unexpected home navigation href: {home_link!r}")
        if nav_script_count != 1:
            raise AssertionError(f"expected one navigation script on Studio home, got {nav_script_count}")
        if mode != "list":
            raise AssertionError(f"expected list mode, got {mode!r}")
        if record_loaded != "true":
            raise AssertionError(f"expected record loaded, got {record_loaded!r}")
        if expected_groups - set(chips):
            raise AssertionError(f"missing expected group chips: {sorted(expected_groups - set(chips))}")
        if not doc_link.startswith("http://127.0.0.1:") or not doc_link.endswith("/docs/?scope=studio&doc=tag-groups&mode=manage"):
            raise AssertionError(f"unexpected doc link: {doc_link!r}")
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
        print(f"local Studio Tag Groups OK: {base_url}/studio/analytics/tag-groups/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
