#!/usr/bin/env python3
"""Smoke-check the local Studio Catalogue dashboard route shell."""

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

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


ROUTE_ID = "studio_catalogue"
ROUTE_PATH = "/studio/catalogue/?mode=manage"
ROOT_SELECTOR = "#studioCatalogueDashboardRoot"
DOC_HREF = "/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan&mode=manage"
EXPECTED_LINKS = {
    "/studio/catalogue-series/?mode=manage",
    "/studio/catalogue-work/?mode=manage",
    "/studio/catalogue-work-detail/?mode=manage",
    "/studio/bulk-add-work/?mode=manage",
    "/studio/catalogue-moment/?mode=manage",
    "/studio/catalogue-status/?mode=manage",
    "/studio/studio-works/?mode=manage",
    "/studio/project-state/?mode=manage",
}


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
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
        runtime_view = runtime_by_id.get(ROUTE_ID)
        if not runtime_view or runtime_view.get("path") != ROUTE_PATH:
            raise AssertionError(f"runtime config missing {ROUTE_ID}: {runtime_views!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            data_requests: list[str] = []
            local_catalogue_requests: list[str] = []
            legacy_catalogue_service_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "request",
                lambda request: data_requests.append(request.url)
                if "/assets/data/works_index.json" in request.url
                or "/assets/data/series_index.json" in request.url
                or "/studio/data/canonical/analytics/tag-registry.json" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: local_catalogue_requests.append(request.url)
                if "/studio/api/catalogue/" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: legacy_catalogue_service_requests.append(request.url)
                if "127.0.0.1:8788" in request.url
                else None,
            )

            page.goto(f"{base_url}{ROUTE_PATH}", wait_until="domcontentloaded")
            root = page.locator(ROOT_SELECTOR)
            expect(root).to_be_visible(timeout=10_000)
            expect(root).to_have_attribute("data-studio-route", "studio-catalogue", timeout=10_000)
            expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
            expect(root).to_have_attribute("data-studio-busy", "false", timeout=10_000)
            expect(root).to_have_attribute("data-studio-mode", "dashboard", timeout=10_000)
            expect(page.locator('[data-studio-metric="series-count"]')).not_to_have_text("--", timeout=10_000)
            expect(page.locator('[data-studio-metric="works-count"]')).not_to_have_text("--", timeout=10_000)

            doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
            if doc_link != DOC_HREF:
                raise AssertionError(f"Catalogue dashboard doc link is not manage-mode: {doc_link!r}")
            nav_link = page.locator(f'.site-nav [data-studio-navigate="{ROUTE_ID}"]').get_attribute("href")
            if nav_link != ROUTE_PATH:
                raise AssertionError(f"Catalogue dashboard nav link is not manage-mode: {nav_link!r}")
            hrefs = set(page.locator(".catalogueDashboardPills a").evaluate_all("(nodes) => nodes.map((node) => node.getAttribute('href'))"))
            if not EXPECTED_LINKS.issubset(hrefs):
                raise AssertionError(f"Catalogue dashboard links missing manage-mode targets: {sorted(hrefs)!r}")

            browser.close()

        if len(data_requests) < 3:
            raise AssertionError(f"Catalogue dashboard did not request expected data sources: {data_requests!r}")
        if not local_catalogue_requests:
            raise AssertionError("Catalogue dashboard did not request the local catalogue API")
        if legacy_catalogue_service_requests:
            raise AssertionError(f"Catalogue dashboard still called legacy catalogue service: {legacy_catalogue_service_requests}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio Catalogue dashboard route OK: {base_url}{ROUTE_PATH}")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
