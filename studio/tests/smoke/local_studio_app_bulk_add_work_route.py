#!/usr/bin/env python3
"""Smoke-check the local Studio bulk-add-work route shell."""

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
        runtime_view = runtime_by_id.get("bulk_add_work")
        if not runtime_view or runtime_view.get("path") != "/studio/bulk-add-work/?mode=manage":
            raise AssertionError(f"runtime config missing bulk_add_work: {runtime_views!r}")
        runtime_pipeline = runtime_config.get("app", {}).get("runtime", {}).get("pipeline", {})
        if runtime_pipeline.get("workbooks", {}).get("bulk_import") != "data/works_bulk_import.xlsx":
            raise AssertionError(f"runtime config missing bulk import workbook path: {runtime_pipeline!r}")

        with urllib.request.urlopen(f"{base_url}/studio/bulk-add-work/?mode=manage", timeout=10) as response:
            bootstrap_html = response.read().decode("utf-8")
        if 'id="studioApp"' not in bootstrap_html or "studio-app.js" not in bootstrap_html:
            raise AssertionError("bulk-add-work should be served through the JavaScript Studio app bootstrap")
        if "bulkAddWorkRoot" in bootstrap_html:
            raise AssertionError("bulk-add-work route body should be rendered by JavaScript, not Python")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            console_errors: list[str] = []
            page_errors: list[str] = []
            legacy_catalogue_service_requests: list[str] = []
            local_catalogue_requests: list[str] = []
            viewports = (
                ("desktop", {"width": 1280, "height": 900}),
                ("mobile", {"width": 390, "height": 844}),
            )
            for label, viewport in viewports:
                page = browser.new_page(viewport=viewport)
                page.on("console", lambda message, current_label=label: console_errors.append(f"{current_label}: {message.text}") if message.type == "error" else None)
                page.on("pageerror", lambda error, current_label=label: page_errors.append(f"{current_label}: {error}"))
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

                page.goto(f"{base_url}/studio/bulk-add-work/?mode=manage", wait_until="domcontentloaded")
                root = page.locator("#bulkAddWorkRoot")
                expect(root).to_be_visible(timeout=10_000)
                expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
                expect(root).to_have_attribute("data-studio-mode", "idle", timeout=10_000)
                expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
                expect(root).to_have_attribute("data-studio-record-loaded", "false", timeout=10_000)
                expect(page.locator("#bulkAddWorkPreview")).to_be_enabled(timeout=10_000)
                expect(page.locator("#bulkAddWorkApply")).to_be_disabled(timeout=10_000)

                workbook_path = page.locator("#bulkAddWorkWorkbook").inner_text(timeout=10_000).strip()
                data_workbook_path = root.get_attribute("data-workbook-path")
                if workbook_path != "data/works_bulk_import.xlsx" or data_workbook_path != "data/works_bulk_import.xlsx":
                    raise AssertionError(f"unexpected workbook path: text={workbook_path!r}, data={data_workbook_path!r}")
                doc_link_count = page.locator(".studioLayout__docLink").count()
                if doc_link_count:
                    raise AssertionError("bulk-add-work still renders header doc pill")
                if page.locator('.site-nav [data-studio-navigate="bulk_add_work"]').count():
                    raise AssertionError("bulk-add-work should not appear as a top-nav item")
                page.close()
            if not local_catalogue_requests:
                raise AssertionError("bulk-add-work route did not call the local catalogue API")
            if legacy_catalogue_service_requests:
                raise AssertionError(f"bulk-add-work still called legacy catalogue service: {legacy_catalogue_service_requests}")

            browser.close()

        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio bulk-add-work route OK: {base_url}/studio/bulk-add-work/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
