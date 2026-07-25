#!/usr/bin/env python3
"""Smoke-check the local Studio Tag Groups view."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402
from local_studio_tag_server import start_studio_tag_server, stop_studio_tag_server  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_studio_tag_server(REPO_ROOT)
    try:
        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        runtime_routes = runtime_config.get("app", {}).get("runtime", {}).get("routes", {})
        if runtime_config.get("studio_config_version") != "studio_config_v1":
            raise AssertionError("runtime config did not include the Studio config payload")
        if runtime_config.get("app", {}).get("runtime", {}).get("host") != "local-studio-app":
            raise AssertionError("runtime config did not include Studio runtime metadata")
        if runtime_routes.get("runtime_config") != "/studio/runtime-config.json":
            raise AssertionError(f"unexpected runtime config route metadata: {runtime_routes!r}")
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        tag_groups_route = next((view for view in runtime_views if view.get("id") == "tag_groups"), None)
        if not tag_groups_route or tag_groups_route.get("path") != "/studio/tag-groups/":
            raise AssertionError(f"runtime config did not include the Tag Groups view: {runtime_views!r}")
        if tag_groups_route.get("shell_type") != "html-template":
            raise AssertionError(f"runtime config missing template shell type for tag_groups: {tag_groups_route!r}")
        if tag_groups_route.get("template") != "/studio/app/frontend/routes/tag-groups.html":
            raise AssertionError(f"runtime config missing tag_groups template: {tag_groups_route!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            config_requests: list[str] = []
            tag_api_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on(
                "request",
                lambda request: config_requests.append(request.url)
                if "/studio/runtime-config.json" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: tag_api_requests.append(request.url)
                if "/studio/api/tags/tag-groups" in request.url
                else None,
            )
            page.goto(f"{base_url}/studio/tag-groups/", wait_until="domcontentloaded")
            if page.locator("#studioApp").count() != 1:
                raise AssertionError("tag groups route did not render through the Studio shell")
            nav_script_count = page.locator('script[src*="studio-app.js"]').count()
            wait_for_route_ready(page, "#tag-groups", "data-studio-ready", "data-studio-busy")
            mode = page.locator("#tag-groups").get_attribute("data-studio-mode")
            record_loaded = page.locator("#tag-groups").get_attribute("data-studio-record-loaded")
            chips = page.locator(".tagGroups__section .studioUi__keyPill").all_text_contents()
            doc_link_count = page.locator(".studioLayout__docLink").count()
            content_text = page.locator('[data-role="content"]').inner_text()
            browser.close()

        expected_groups = {"subject", "domain", "form", "theme"}
        if nav_script_count != 1:
            raise AssertionError(f"expected one app bootstrap script on Studio route, got {nav_script_count}")
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
        if not tag_api_requests:
            raise AssertionError("Tag Groups did not request the local Studio tag API")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        print(f"local Studio Tag Groups OK: {base_url}/studio/tag-groups/")
        return 0
    finally:
        stop_studio_tag_server(server)


if __name__ == "__main__":
    raise SystemExit(main())
