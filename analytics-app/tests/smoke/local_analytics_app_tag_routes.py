#!/usr/bin/env python3
"""Smoke-check local Analytics tag route shells."""

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
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


ROUTES = [
    {
        "view_id": "tag_registry",
        "runtime_path": "/analytics/tag-registry/",
        "path": "/analytics/tag-registry/",
        "root": "#tag-registry",
        "mode": "list",
        "expected_requests": [
            "/analytics/api/tag-registry",
            "/analytics/api/tag-aliases",
            "/analytics/api/tag-assignments",
            "/analytics/api/tag-groups",
        ],
    },
    {
        "view_id": "tag_aliases",
        "runtime_path": "/analytics/tag-aliases/",
        "path": "/analytics/tag-aliases/",
        "root": "#tag-aliases",
        "mode": "list",
        "expected_requests": [
            "/analytics/api/tag-aliases",
            "/analytics/api/tag-registry",
            "/analytics/api/tag-groups",
        ],
    },
    {
        "view_id": "series_tags",
        "runtime_path": "/analytics/series-tags/",
        "path": "/analytics/series-tags/",
        "root": "#series-tags",
        "mode": "list",
        "expected_requests": [
            "/analytics/api/tag-assignments",
            "/analytics/api/tag-registry",
            "/analytics/api/tag-groups",
            "/analytics/api/health",
        ],
    },
    {
        "view_id": "series_tag_editor",
        "runtime_path": "/analytics/series-tag-editor/",
        "path": "/analytics/series-tag-editor/?series=036",
        "root": "#seriesTagEditorRoot",
        "mode": "edit",
        "expected_requests": [
            "/analytics/api/tag-registry",
            "/analytics/api/tag-aliases",
            "/analytics/api/tag-assignments",
            "/analytics/api/health",
        ],
    },
]


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
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        public_preview_base = runtime_config.get("app", {}).get("runtime", {}).get("sites", {}).get("public_preview", {}).get("base", "")
        runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
        if not public_preview_base:
            raise AssertionError(f"runtime config missing public preview base: {runtime_config!r}")
        for route in ROUTES:
            runtime_view = runtime_by_id.get(route["view_id"])
            if not runtime_view or runtime_view.get("path") != route["runtime_path"]:
                raise AssertionError(f"runtime config missing {route['view_id']}: {runtime_views!r}")
            if runtime_view.get("shell_type") != "html-template":
                raise AssertionError(f"runtime config missing template shell type for {route['view_id']}: {runtime_view!r}")
            if not str(runtime_view.get("template") or "").startswith("/analytics/app/frontend/routes/"):
                raise AssertionError(f"runtime config missing route template for {route['view_id']}: {runtime_view!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            requests: list[str] = []
            legacy_requests: list[str] = []
            static_tag_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))
            page.on("request", lambda request: legacy_requests.append(request.url) if "127.0.0.1:8787" in request.url else None)
            page.on(
                "request",
                lambda request: static_tag_requests.append(request.url)
                if "/analytics/data/canonical/tag-" in request.url
                else None,
            )

            for route in ROUTES:
                page.goto(f"{base_url}{route['path']}", wait_until="domcontentloaded")
                if page.locator("[data-analytics-route-outlet]").count() != 1:
                    raise AssertionError(f"{route['path']} did not render the static Analytics shell outlet")
                wait_for_route_ready(page, route["root"], "data-analytics-ready", "data-analytics-busy")
                root = page.locator(route["root"])
                mode = root.get_attribute("data-analytics-mode")
                record_loaded = root.get_attribute("data-analytics-record-loaded")
                doc_link_count = page.locator(".studioLayout__docLink").count()
                if mode != route["mode"]:
                    raise AssertionError(f"{route['path']} expected {route['mode']} mode, got {mode!r}")
                if record_loaded != "true":
                    raise AssertionError(f"{route['path']} did not report loaded data")
                if doc_link_count:
                    raise AssertionError(f"{route['path']} still renders header doc pill")
                if route["view_id"] == "series_tag_editor":
                    series_id = page.locator("#analytics-tag-editor").get_attribute("data-series-id")
                    if series_id != "036":
                        raise AssertionError(f"series tag editor did not load series 036: {series_id!r}")
                    series_href = page.locator("#seriesTagEditorCat a").get_attribute("href")
                    primary_work_href = page.locator("#seriesTagEditorPrimaryWork a").get_attribute("href")
                    if series_href != f"{public_preview_base}/series/?series=036":
                        raise AssertionError(f"series link did not use public preview base: {series_href!r}")
                    if primary_work_href and not primary_work_href.startswith(f"{public_preview_base}/works/?work="):
                        raise AssertionError(f"primary work link did not use public preview base: {primary_work_href!r}")
                    theme_toggle = page.locator("[data-analytics-theme-toggle]")
                    if theme_toggle.count() != 1:
                        raise AssertionError("series tag editor did not expose exactly one theme toggle")
                    if page.evaluate("document.documentElement.getAttribute('data-theme')") != "light":
                        raise AssertionError("series tag editor did not start in light theme")
                    theme_toggle.click()
                    if page.evaluate("document.documentElement.getAttribute('data-theme')") != "dark":
                        raise AssertionError("series tag editor theme toggle did not switch to dark")
                    if theme_toggle.get_attribute("aria-pressed") != "true":
                        raise AssertionError("series tag editor theme toggle did not update pressed state")
                    theme_toggle.click()
                    if page.evaluate("document.documentElement.getAttribute('data-theme')") != "light":
                        raise AssertionError("series tag editor theme toggle did not switch back to light")

            browser.close()

        for route in ROUTES:
            missing = [
                expected
                for expected in route["expected_requests"]
                if not any(expected in request for request in requests)
            ]
            if missing:
                raise AssertionError(f"{route['path']} did not request expected local APIs: {missing!r}")
        if legacy_requests:
            raise AssertionError(f"local tag routes should not request legacy 8787 endpoints: {legacy_requests!r}")
        if static_tag_requests:
            raise AssertionError(f"local tag routes should not request static analytics tag data: {static_tag_requests!r}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Analytics tag routes OK: {base_url}/analytics/tag-registry/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
