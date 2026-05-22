#!/usr/bin/env python3
"""Smoke-check the local Studio app Docs Viewer management shell."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from threading import Thread
import json
import urllib.request
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.studio.studio_app_server import StudioAppServer  # noqa: E402


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def query_value(url: str, key: str) -> str:
    return (parse_qs(urlparse(url).query).get(key) or [""])[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/studio/api/docs/capabilities", timeout=10) as response:
            capabilities = json.loads(response.read().decode("utf-8"))
        studio_caps = capabilities.get("capabilities", {}).get("scopes", {}).get("studio", {})
        if capabilities.get("ok") is not True:
            raise AssertionError(f"unexpected capabilities response: {capabilities!r}")
        if studio_caps.get("available") is not True:
            raise AssertionError(f"expected local Docs API to report real Studio scope availability: {studio_caps!r}")
        if capabilities.get("capabilities", {}).get("docs_management") is not False:
            raise AssertionError(f"expected local Docs API writes to remain disabled: {capabilities!r}")
        if capabilities.get("capabilities", {}).get("generated_data_reads") is not True:
            raise AssertionError(f"expected local Docs API generated reads to be enabled: {capabilities!r}")
        if studio_caps.get("generated_data_reads") is not True or studio_caps.get("generated_search_reads") is not True:
            raise AssertionError(f"expected Studio generated reads to be enabled: {studio_caps!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            generated_requests: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.on(
                "request",
                lambda request: generated_requests.append(request.url)
                if "/studio/api/docs/docs/generated/" in request.url
                else None,
            )
            page.goto(f"{base_url}/docs/?scope=studio&doc=docs-viewer&mode=manage", wait_until="domcontentloaded")
            page.wait_for_selector("#docsViewerRoot:not([hidden])", timeout=args.timeout_ms)
            page.wait_for_selector("#docsViewerContent:not([hidden])", timeout=args.timeout_ms)
            page.wait_for_function(
                """() => document.querySelector("#docsViewerContent h1")?.id === "docs-viewer" """,
                timeout=args.timeout_ms,
            )
            page.wait_for_function(
                """() => {
                    const status = document.querySelector("#docsViewerStatus");
                    return status &&
                        !status.hidden &&
                        status.textContent.includes("Manage mode unavailable");
                }""",
                timeout=3000,
            )
            root_attrs = page.locator("#docsViewerRoot").evaluate(
                """root => ({
                    allowManagement: root.dataset.allowManagement,
                    allowScopeQuery: root.dataset.allowScopeQuery,
                    includeScopeParam: root.dataset.includeScopeParam,
                    viewerBaseUrl: root.dataset.viewerBaseUrl,
                    configUrl: root.dataset.docsViewerConfigUrl,
                    managementBaseUrl: root.dataset.managementBaseUrl
                })"""
            )
            management_css_count = page.locator('link[href*="docs-viewer-management.css"]').count()
            docs_script_count = page.locator('script[src*="docs-viewer.js"]').count()
            nav_link = page.locator('[data-studio-navigate="docs"]').get_attribute("href")
            status_text = page.locator("#docsViewerStatus").inner_text()
            header_box = page.locator(".site-title").bounding_box()
            docs_box = page.locator("#docsViewerRoot").bounding_box()
            title = page.locator("#docsViewerContent h1").inner_text()
            final_url = page.url
            browser.close()

        if root_attrs != {
            "allowManagement": "true",
            "allowScopeQuery": "true",
            "includeScopeParam": "true",
            "viewerBaseUrl": "/docs/",
            "configUrl": "/assets/docs-viewer/data/docs-viewer-config.json",
            "managementBaseUrl": "/studio/api/docs",
        }:
            raise AssertionError(f"unexpected Docs Viewer root attrs: {root_attrs!r}")
        if "Manage mode unavailable" not in status_text:
            raise AssertionError(f"expected immediate manage-mode unavailable status, got {status_text!r}")
        if not any("/docs/generated/index" in url for url in generated_requests):
            raise AssertionError(f"expected generated index request through local Docs API: {generated_requests!r}")
        if not any("/docs/generated/payload" in url for url in generated_requests):
            raise AssertionError(f"expected generated payload request through local Docs API: {generated_requests!r}")
        if not header_box or not docs_box:
            raise AssertionError("could not measure local Docs Viewer layout")
        if abs(header_box["x"] - docs_box["x"]) > 1:
            raise AssertionError(f"Docs Viewer should align with the centered shell content: header={header_box}, docs={docs_box}")
        if management_css_count != 1:
            raise AssertionError(f"expected one management stylesheet, got {management_css_count}")
        if docs_script_count != 1:
            raise AssertionError(f"expected one Docs Viewer script, got {docs_script_count}")
        if nav_link != "/docs/":
            raise AssertionError(f"unexpected docs nav href: {nav_link!r}")
        if query_value(final_url, "mode") != "manage":
            raise AssertionError(f"expected mode=manage in URL, got {final_url}")
        if title != "Docs Viewer":
            raise AssertionError(f"unexpected docs title: {title!r}")
        if errors:
            raise AssertionError(f"page errors during local Docs Viewer smoke: {errors!r}")
        print(f"local Studio Docs Viewer OK: {base_url}/docs/?scope=studio&doc=docs-viewer&mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
