#!/usr/bin/env python3
"""Smoke-check local Studio catalogue editor route shells."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.studio.studio_app_server import StudioAppServer  # noqa: E402


ROUTES = [
    {
        "id": "catalogue_series_editor",
        "path": "/studio/catalogue-series/?mode=manage",
        "root": "#catalogueSeriesRoot",
        "route": "catalogue-series",
        "doc": "/docs/?scope=studio&doc=catalogue-series-editor&mode=manage",
    },
    {
        "id": "catalogue_work_editor",
        "path": "/studio/catalogue-work/?mode=manage",
        "root": "#catalogueWorkRoot",
        "route": "catalogue-work",
        "doc": "/docs/?scope=studio&doc=catalogue-work-editor&mode=manage",
    },
    {
        "id": "catalogue_work_detail_editor",
        "path": "/studio/catalogue-work-detail/?mode=manage",
        "root": "#catalogueWorkDetailRoot",
        "route": "catalogue-work-detail",
        "doc": "/docs/?scope=studio&doc=catalogue-work-detail-editor&mode=manage",
    },
    {
        "id": "catalogue_moment_editor",
        "path": "/studio/catalogue-moment/?mode=manage",
        "root": "#catalogueMomentRoot",
        "route": "catalogue-moment",
        "doc": "/docs/?scope=studio&doc=catalogue-moment-editor&mode=manage",
    },
]


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
        public_preview_base = runtime_config.get("app", {}).get("runtime", {}).get("sites", {}).get("public_preview", {}).get("base", "")
        if not public_preview_base:
            raise AssertionError(f"runtime config missing public preview base: {runtime_config!r}")
        for route in ROUTES:
            runtime_view = runtime_by_id.get(route["id"])
            if not runtime_view or runtime_view.get("path") != route["path"]:
                raise AssertionError(f"runtime config missing {route['id']}: {runtime_views!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            legacy_catalogue_service_requests: list[str] = []
            local_catalogue_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "request",
                lambda request: legacy_catalogue_service_requests.append(request.url)
                if "127.0.0.1:8788" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: local_catalogue_requests.append(request.url)
                if "/studio/api/catalogue/" in request.url
                else None,
            )

            for route in ROUTES:
                page.goto(f"{base_url}{route['path']}", wait_until="domcontentloaded")
                root = page.locator(route["root"])
                expect(root).to_be_visible(timeout=10_000)
                expect(root).to_have_attribute("data-studio-route", route["route"], timeout=10_000)
                expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
                expect(root).to_have_attribute("data-studio-busy", "false", timeout=10_000)
                expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
                expect(root).to_have_attribute("data-studio-record-loaded", "false", timeout=10_000)
                doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
                if doc_link != route["doc"]:
                    raise AssertionError(f"{route['id']} doc link is not manage-mode: {doc_link!r}")
                nav_link = page.locator('.site-nav [data-studio-navigate="studio_catalogue"]').get_attribute("href")
                if nav_link != "/studio/catalogue/?mode=manage":
                    raise AssertionError(f"{route['id']} parent nav link is not manage-mode: {nav_link!r}")
                if page.locator(f'.site-nav [data-studio-navigate="{route["id"]}"]').count():
                    raise AssertionError(f"{route['id']} should not appear as a top-nav item")

            public_link_checks = [
                {
                    "url": "/studio/catalogue-series/?mode=manage&series=001",
                    "root": "#catalogueSeriesRoot",
                    "selector": "#catalogueSeriesSummary a[href*='/series/']",
                    "prefix": f"{public_preview_base}/series/001/",
                },
                {
                    "url": "/studio/catalogue-work/?mode=manage&work=00001",
                    "root": "#catalogueWorkRoot",
                    "selector": "#catalogueWorkSummary a[href*='/works/']",
                    "prefix": f"{public_preview_base}/works/00001/",
                },
                {
                    "url": "/studio/catalogue-work-detail/?mode=manage&detail=00001-001",
                    "root": "#catalogueWorkDetailRoot",
                    "selector": "#catalogueWorkDetailSummary a[href*='/work_details/']",
                    "prefix": f"{public_preview_base}/work_details/00001-001/",
                },
                {
                    "url": "/studio/catalogue-moment/?mode=manage&moment=13-moments-in-october",
                    "root": "#catalogueMomentRoot",
                    "selector": "#catalogueMomentSummary a[href*='/moments/']",
                    "prefix": f"{public_preview_base}/moments/13-moments-in-october/",
                },
            ]
            for check in public_link_checks:
                page.goto(f"{base_url}{check['url']}", wait_until="domcontentloaded")
                root = page.locator(check["root"])
                expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
                expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
                public_href = page.locator(check["selector"]).first.get_attribute("href")
                if not public_href or not public_href.startswith(check["prefix"]):
                    raise AssertionError(f"catalogue editor public link did not use public preview base: {public_href!r}")

            browser.close()

        if not local_catalogue_requests:
            raise AssertionError("catalogue editor routes did not call the local catalogue API")
        if legacy_catalogue_service_requests:
            raise AssertionError(f"catalogue editor routes still called legacy catalogue service: {legacy_catalogue_service_requests}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio catalogue editor routes OK: {base_url}/studio/catalogue-work/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
