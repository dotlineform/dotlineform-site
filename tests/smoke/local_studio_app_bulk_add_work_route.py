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


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.studio.studio_app_server import StudioAppServer  # noqa: E402


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def unavailable_json(route) -> None:
    route.fulfill(
        status=200,
        content_type="application/json",
        body='{"ok": false, "error": "catalogue service unavailable"}',
    )


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

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            catalogue_service_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "request",
                lambda request: catalogue_service_requests.append(request.url)
                if "127.0.0.1:8788" in request.url
                else None,
            )
            page.route("http://127.0.0.1:8788/**", unavailable_json)

            page.goto(f"{base_url}/studio/bulk-add-work/?mode=manage", wait_until="domcontentloaded")
            root = page.locator("#bulkAddWorkRoot")
            expect(root).to_be_visible(timeout=10_000)
            expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
            expect(root).to_have_attribute("data-studio-mode", "idle", timeout=10_000)
            expect(root).to_have_attribute("data-studio-service", "unavailable", timeout=10_000)
            expect(root).to_have_attribute("data-studio-record-loaded", "false", timeout=10_000)
            expect(page.locator("#bulkAddWorkPreview")).to_be_disabled(timeout=10_000)
            expect(page.locator("#bulkAddWorkApply")).to_be_disabled(timeout=10_000)

            workbook_path = page.locator("#bulkAddWorkWorkbook").inner_text(timeout=10_000).strip()
            data_workbook_path = root.get_attribute("data-workbook-path")
            if workbook_path != "data/works_bulk_import.xlsx" or data_workbook_path != "data/works_bulk_import.xlsx":
                raise AssertionError(f"unexpected workbook path: text={workbook_path!r}, data={data_workbook_path!r}")
            doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
            if doc_link != "/docs/?scope=studio&doc=bulk-add-work&mode=manage":
                raise AssertionError(f"bulk-add-work doc link is not manage-mode: {doc_link!r}")
            nav_link = page.locator('.site-nav [data-studio-navigate="bulk_add_work"]').get_attribute("href")
            if nav_link != "/studio/bulk-add-work/?mode=manage":
                raise AssertionError(f"bulk-add-work nav link is not manage-mode: {nav_link!r}")
            if not catalogue_service_requests:
                raise AssertionError("bulk-add-work route did not probe the catalogue service")

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
