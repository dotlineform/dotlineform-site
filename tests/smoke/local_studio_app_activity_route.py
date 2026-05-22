#!/usr/bin/env python3
"""Smoke-check the local Studio activity route shell."""

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


def activity_feed() -> dict[str, object]:
    return {
        "header": {
            "schema": "studio_activity_log_v1",
            "generated_at_utc": "2026-05-15T10:00:00Z",
            "entry_count": 1,
        },
        "entries": [
            {
                "id": "local-activity-smoke",
                "activity_id": "local-activity-smoke",
                "time_utc": "2026-05-15T10:00:00Z",
                "timestamp": "2026-05-15T10:00:00Z",
                "status": "completed",
                "page_label": "Catalogue Work",
                "user_action_label": "Save work",
                "script_purpose_label": "Save catalogue source",
                "detail_items": [
                    "Wrote source JSON",
                    "Updated Studio activity feed",
                ],
                "record_groups": {
                    "works": {
                        "count": 1,
                    },
                },
            }
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
        runtime_view = runtime_by_id.get("activity")
        if not runtime_view or runtime_view.get("path") != "/studio/activity/?mode=manage":
            raise AssertionError(f"runtime config missing activity: {runtime_views!r}")

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
            page.route(
                "http://127.0.0.1:8788/catalogue/read**",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(activity_feed()),
                ),
            )

            page.goto(f"{base_url}/studio/activity/?mode=manage", wait_until="domcontentloaded")
            root = page.locator("#studioActivityRoot")
            expect(root).to_be_visible(timeout=10_000)
            expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
            expect(root).to_have_attribute("data-studio-mode", "list", timeout=10_000)
            expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
            expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
            expect(page.locator("[data-activity-id='local-activity-smoke']")).to_be_visible(timeout=10_000)

            page.locator("[data-activity-id='local-activity-smoke']").click()
            expect(page.locator("[data-role='studio-modal']")).to_be_visible(timeout=10_000)
            modal_title = page.locator("[data-role='studio-modal'] .tagStudioModal__title").first.inner_text(timeout=10_000)
            modal_body = page.locator("[data-role='studio-modal'] .tagStudioModal__label").all_inner_texts()
            if modal_title != "Activity details" or modal_body != ["Wrote source JSON", "Updated Studio activity feed"]:
                raise AssertionError(f"unexpected activity modal title: {modal_title!r}")

            doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
            if doc_link != "/docs/?scope=studio&doc=studio-activity&mode=manage":
                raise AssertionError(f"activity doc link is not manage-mode: {doc_link!r}")
            nav_link = page.locator('.site-nav [data-studio-navigate="activity"]').get_attribute("href")
            if nav_link != "/studio/activity/?mode=manage":
                raise AssertionError(f"activity nav link is not manage-mode: {nav_link!r}")
            if not catalogue_service_requests:
                raise AssertionError("activity route did not request the catalogue read service")

            browser.close()

        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio activity route OK: {base_url}/studio/activity/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
