#!/usr/bin/env python3
"""Smoke-check the local Studio works route shell."""

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
        runtime_view = runtime_by_id.get("studio_works")
        if not runtime_view or runtime_view.get("path") != "/studio/studio-works/?mode=manage":
            raise AssertionError(f"runtime config missing studio_works: {runtime_views!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            data_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "request",
                lambda request: data_requests.append(request.url)
                if "/assets/data/works_index.json" in request.url
                or "/assets/data/series_index.json" in request.url
                or "/studio/data/generated/activity/work-storage-index.json" in request.url
                else None,
            )

            page.goto(f"{base_url}/studio/studio-works/?mode=manage", wait_until="domcontentloaded")
            root = page.locator("#worksStudioRoot")
            expect(root).to_be_visible(timeout=10_000)
            expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
            expect(root).to_have_attribute("data-studio-mode", "list", timeout=10_000)
            expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
            expect(page.locator(".worksList__item").first).to_be_visible(timeout=10_000)
            expect(page.locator("#worksListCount")).to_contain_text("works", timeout=10_000)

            static_series_base = root.get_attribute("data-series-base-href")
            back_href = page.locator("#worksIndexBackLink").get_attribute("href")
            if static_series_base is not None:
                raise AssertionError(f"studio-works kept static public series fallback: {static_series_base!r}")
            if back_href == "/series/":
                raise AssertionError("studio-works kept a relative public series back link")

            title_href = page.locator(".worksList__title").first.get_attribute("href")
            series_href = page.locator(".worksList__series").first.get_attribute("href")
            if not title_href or not title_href.startswith("http://127.0.0.1:4000/works/"):
                raise AssertionError(f"work link did not resolve through the public preview base: {title_href!r}")
            if "from=works_index" not in title_href:
                raise AssertionError(f"work link lost public works-index return marker: {title_href!r}")
            if not series_href or not series_href.startswith("http://127.0.0.1:4000/series/"):
                raise AssertionError(f"series link did not resolve through the public preview base: {series_href!r}")

            doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
            if not str(doc_link).endswith("/docs/?scope=studio&doc=studio-works&mode=manage"):
                raise AssertionError(f"studio-works doc link is not manage-mode: {doc_link!r}")
            nav_link = page.locator('.site-nav [data-studio-navigate="studio_catalogue"]').get_attribute("href")
            if nav_link != "/studio/catalogue/?mode=manage":
                raise AssertionError(f"studio-works parent nav link is not manage-mode: {nav_link!r}")
            if page.locator('.site-nav [data-studio-navigate="studio_works"]').count():
                raise AssertionError("studio-works should not appear as a top-nav item")
            if len(data_requests) < 3:
                raise AssertionError(f"studio-works route did not request all expected data sources: {data_requests!r}")

            browser.close()

        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio works route OK: {base_url}/studio/studio-works/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
