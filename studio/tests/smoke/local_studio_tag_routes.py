#!/usr/bin/env python3
"""Smoke-check the Studio-owned tag route shells."""

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


ROUTES = [
    {
        "view_id": "tag_registry",
        "runtime_path": "/studio/tag-registry/",
        "path": "/studio/tag-registry/",
        "root": "#tag-registry",
        "mode": "list",
        "expected_requests": [
            "/studio/api/tags/tag-registry",
            "/studio/api/tags/tag-aliases",
            "/studio/api/tags/tag-assignments",
            "/studio/api/tags/tag-groups",
        ],
    },
    {
        "view_id": "tag_aliases",
        "runtime_path": "/studio/tag-aliases/",
        "path": "/studio/tag-aliases/",
        "root": "#tag-aliases",
        "mode": "list",
        "expected_requests": [
            "/studio/api/tags/tag-aliases",
            "/studio/api/tags/tag-registry",
            "/studio/api/tags/tag-groups",
        ],
    },
    {
        "view_id": "series_tags",
        "runtime_path": "/studio/series-tags/",
        "path": "/studio/series-tags/",
        "root": "#series-tags",
        "mode": "list",
        "expected_requests": [
            "/studio/api/tags/tag-assignments",
            "/studio/api/tags/tag-registry",
            "/studio/api/tags/tag-groups",
        ],
    },
    {
        "view_id": "series_tag_editor",
        "runtime_path": "/studio/series-tag-editor/",
        "path": "/studio/series-tag-editor/?series=036",
        "root": "#seriesTagEditorRoot",
        "mode": "edit",
        "expected_requests": [
            "/studio/api/tags/tag-registry",
            "/studio/api/tags/tag-aliases",
            "/studio/api/tags/tag-assignments",
            "/studio/api/tags/health",
        ],
    },
]

HOME_TAG_ROUTE_IDS = (
    "tag_groups",
    "tag_registry",
    "tag_aliases",
    "series_tags",
    "series_tag_editor",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_studio_tag_server(REPO_ROOT)
    try:
        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
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
            if not str(runtime_view.get("template") or "").startswith("/studio/app/frontend/routes/"):
                raise AssertionError(f"runtime config missing route template for {route['view_id']}: {runtime_view!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            requests: list[str] = []
            external_tag_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))
            page.on(
                "request",
                lambda request: external_tag_requests.append(request.url)
                if "/studio/api/tags/" in request.url and not request.url.startswith(base_url)
                else None,
            )

            page.goto(f"{base_url}/studio/", wait_until="domcontentloaded")
            wait_for_route_ready(page, "#studioHomeRoot", "data-studio-ready", "data-studio-busy")
            tag_heading = page.locator(".studioHomeLinks__column h3", has_text="tags")
            if tag_heading.count() != 1:
                raise AssertionError("Studio home did not render one tags column")
            tag_column = tag_heading.locator("..")
            for route_id in HOME_TAG_ROUTE_IDS:
                runtime_view = runtime_by_id.get(route_id)
                path = str(runtime_view.get("path") if runtime_view else "")
                if not path or tag_column.locator(f'a.studioHomeLinks__pill[href="{path}"]').count() != 1:
                    raise AssertionError(f"Studio home tags column did not link {route_id}: {path!r}")

            for route in ROUTES:
                page.goto(f"{base_url}{route['path']}", wait_until="domcontentloaded")
                if page.locator("#studioApp").count() != 1:
                    raise AssertionError(f"{route['path']} did not render through the Studio shell")
                wait_for_route_ready(page, route["root"], "data-studio-ready", "data-studio-busy")
                root = page.locator(route["root"])
                mode = root.get_attribute("data-studio-mode")
                record_loaded = root.get_attribute("data-studio-record-loaded")
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
                    theme_toggle = page.locator("[data-studio-theme-toggle]")
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
                if route["view_id"] == "series_tags":
                    retired_controls = page.locator(
                        '[data-role="open-session-modal"], '
                        '[data-role="open-import-modal"], '
                        '[data-role="series-tags-session-modal-host"], '
                        '[data-role="series-tags-import-modal-host"]'
                    )
                    if retired_controls.count():
                        raise AssertionError("Series Tags still renders offline session or import controls")

            browser.close()

        for route in ROUTES:
            missing = [
                expected
                for expected in route["expected_requests"]
                if not any(expected in request for request in requests)
            ]
            if missing:
                raise AssertionError(f"{route['path']} did not request expected local APIs: {missing!r}")
        if external_tag_requests:
            raise AssertionError(f"Studio tag routes should use same-origin APIs: {external_tag_requests!r}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio tag routes OK: {base_url}/studio/tag-registry/")
        return 0
    finally:
        stop_studio_tag_server(server)


if __name__ == "__main__":
    raise SystemExit(main())
