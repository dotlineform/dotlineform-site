#!/usr/bin/env python3
"""Smoke-check the local Studio project-state route shell."""

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
        runtime_view = runtime_by_id.get("project_state")
        if not runtime_view or runtime_view.get("path") != "/studio/project-state/?mode=manage":
            raise AssertionError(f"runtime config missing project_state: {runtime_views!r}")
        catalogue_service = runtime_config.get("app", {}).get("runtime", {}).get("services", {}).get("catalogue", {})
        if catalogue_service.get("project_state_report") != "/studio/api/catalogue/project-state-report":
            raise AssertionError(f"runtime config missing local project-state API: {catalogue_service!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            legacy_catalogue_service_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "request",
                lambda request: legacy_catalogue_service_requests.append(request.url)
                if "127.0.0.1:8788" in request.url
                else None,
            )
            page.route("http://127.0.0.1:8788/**", lambda route: route.abort())

            page.goto(f"{base_url}/studio/project-state/?mode=manage", wait_until="domcontentloaded")
            root = page.locator("#projectStateRoot")
            expect(root).to_be_visible(timeout=10_000)
            expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
            expect(root).to_have_attribute("data-studio-mode", "idle", timeout=10_000)
            expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
            expect(root).to_have_attribute("data-studio-record-loaded", "false", timeout=10_000)
            expect(page.locator("#projectStateRunButton")).to_be_enabled(timeout=10_000)
            expect(page.locator("#projectStateOpenButton")).to_be_enabled(timeout=10_000)

            doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
            if doc_link != "/docs/?scope=studio&doc=project-state-page&mode=manage":
                raise AssertionError(f"project-state doc link is not manage-mode: {doc_link!r}")
            nav_link = page.locator('.site-nav [data-studio-navigate="studio_catalogue"]').get_attribute("href")
            if nav_link != "/studio/catalogue/?mode=manage":
                raise AssertionError(f"project-state parent nav link is not manage-mode: {nav_link!r}")
            if page.locator('.site-nav [data-studio-navigate="project_state"]').count():
                raise AssertionError("project-state should not appear as a top-nav item")
            if legacy_catalogue_service_requests:
                raise AssertionError(f"project-state route should not request legacy 8788 endpoints: {legacy_catalogue_service_requests!r}")

            browser.close()

        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio project-state route OK: {base_url}/studio/project-state/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
