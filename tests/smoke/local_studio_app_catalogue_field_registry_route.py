#!/usr/bin/env python3
"""Smoke-check the local Studio catalogue field registry route shell."""

from __future__ import annotations

import argparse
import json
import re
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
        runtime_view = runtime_by_id.get("catalogue_field_registry")
        if not runtime_view or runtime_view.get("path") != "/studio/catalogue-field-registry/?mode=manage":
            raise AssertionError(f"runtime config missing catalogue_field_registry: {runtime_views!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            registry_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "request",
                lambda request: registry_requests.append(request.url)
                if "/assets/studio/data/catalogue_field_registry.json" in request.url
                else None,
            )

            page.goto(f"{base_url}/studio/catalogue-field-registry/?mode=manage", wait_until="domcontentloaded")
            root = page.locator("#fieldRegistryReviewRoot")
            expect(root).to_be_visible(timeout=10_000)
            expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
            expect(root).to_have_attribute("data-studio-mode", "registry", timeout=10_000)
            expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
            expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
            expect(page.locator("#fieldRegistryReviewOutput")).to_have_value(re.compile("catalogue_field_registry_v1"), timeout=10_000)

            page.locator("#fieldRegistryReviewSearch").fill("details_subfolder")
            expect(page.locator("#fieldRegistryReviewMeta")).to_contain_text("exact", timeout=10_000)
            expect(page.locator("#fieldRegistryReviewOutput")).to_have_value(re.compile("details_subfolder"), timeout=10_000)

            doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
            if doc_link != "/docs/?scope=studio&doc=catalogue-field-registry-review&mode=manage":
                raise AssertionError(f"catalogue-field-registry doc link is not manage-mode: {doc_link!r}")
            nav_link = page.locator('.site-nav [data-studio-navigate="catalogue_field_registry"]').get_attribute("href")
            if nav_link != "/studio/catalogue-field-registry/?mode=manage":
                raise AssertionError(f"catalogue-field-registry nav link is not manage-mode: {nav_link!r}")
            if not registry_requests:
                raise AssertionError("catalogue-field-registry route did not request the registry data")

            browser.close()

        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio catalogue-field-registry route OK: {base_url}/studio/catalogue-field-registry/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
