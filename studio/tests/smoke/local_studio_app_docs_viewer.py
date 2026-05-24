#!/usr/bin/env python3
"""Smoke-check the local Studio app Docs Viewer management shell."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from threading import Thread
import json
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


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
        if capabilities.get("capabilities", {}).get("docs_management") is not True:
            raise AssertionError(f"expected local Docs API management to be enabled: {capabilities!r}")
        if capabilities.get("capabilities", {}).get("generated_data_reads") is not True:
            raise AssertionError(f"expected local Docs API generated reads to be enabled: {capabilities!r}")
        if studio_caps.get("generated_data_reads") is not True or studio_caps.get("generated_search_reads") is not True:
            raise AssertionError(f"expected Studio generated reads to be enabled: {studio_caps!r}")
        preview_payload = json.dumps({"scope": "studio", "doc_id": "docs-viewer"}).encode("utf-8")
        preview_request = urllib.request.Request(
            f"{base_url}/studio/api/docs/docs/delete-preview",
            data=preview_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(preview_request, timeout=10) as response:
            delete_preview = json.loads(response.read().decode("utf-8"))
        if delete_preview.get("ok") is not True or delete_preview.get("doc_id") != "docs-viewer":
            raise AssertionError(f"unexpected delete preview response: {delete_preview!r}")
        rejected_request = urllib.request.Request(
            f"{base_url}/studio/api/docs/docs/delete-preview",
            data=preview_payload,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://example.com",
            },
            method="POST",
        )
        try:
            urllib.request.urlopen(rejected_request, timeout=10)
        except urllib.error.HTTPError as error:
            if error.code != 403:
                raise AssertionError(f"expected disallowed Origin to return 403, got {error.code}") from error
        else:
            raise AssertionError("disallowed Origin should be rejected")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            generated_requests: list[str] = []
            management_posts: list[str] = []
            broken_link_requests: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.on(
                "request",
                lambda request: generated_requests.append(request.url)
                if "/studio/api/docs/docs/generated/" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: management_posts.append(request.url)
                if request.method == "POST" and "/studio/api/docs/docs/" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: broken_link_requests.append(request.url)
                if request.method == "POST" and "/studio/api/docs/docs/broken-links" in request.url
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
                    const actions = document.querySelector(".docsViewer__manageActions");
                    const button = document.querySelector("#docsViewerManageActionsButton");
                    return actions && !actions.hidden && button && !button.disabled;
                }""",
                timeout=args.timeout_ms,
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
            main_css_count = page.locator('link[href*="/assets/css/main.css"]').count()
            studio_css_count = page.locator('link[href*="/studio/app/assets/css/studio.css"]').count()
            management_css_count = page.locator('link[href*="docs-viewer-management.css"]').count()
            docs_script_count = page.locator('script[src*="docs-viewer.js"]').count()
            nav_link = page.locator('[data-studio-navigate="docs"]').get_attribute("href")
            actions_visible = page.locator(".docsViewer__manageActions").is_visible()
            actions_disabled = page.locator("#docsViewerManageActionsButton").is_disabled()
            page.locator("#docsViewerManageActionsButton").click()
            page.locator("#docsViewerManageDeleteButton").click()
            page.wait_for_function(
                """() => {
                    const status = document.querySelector("#docsViewerStatus");
                    return status &&
                        !status.hidden &&
                        status.textContent.includes("child docs still depend");
                }""",
                timeout=args.timeout_ms,
            )
            delete_blocker_text = page.locator("#docsViewerStatus").inner_text()
            header_box = page.locator(".site-title").bounding_box()
            docs_box = page.locator("#docsViewerRoot").bounding_box()
            title = page.locator("#docsViewerContent h1").inner_text()
            final_url = page.url
            page.goto(f"{base_url}/docs/?scope=studio&doc=docs-broken-links&mode=manage", wait_until="domcontentloaded")
            page.wait_for_selector('#docsViewerContent .docsViewerReport[data-report-id="docs_broken_links"]', timeout=args.timeout_ms)
            page.wait_for_function(
                """() => {
                    const report = document.querySelector('.docsViewerReport[data-report-id="docs_broken_links"]');
                    const button = document.querySelector('#docsBrokenLinksReportRun');
                    const status = report && report.querySelector('.docsViewerReport__status');
                    return report && button && !button.disabled && status && !/Running/.test(status.textContent);
                }""",
                timeout=args.timeout_ms,
            )
            report_status = page.locator('.docsViewerReport[data-report-id="docs_broken_links"] .docsViewerReport__status').inner_text()
            report_scope = page.locator('.docsViewerReport[data-report-id="docs_broken_links"] select').input_value()
            browser.close()

        if root_attrs != {
            "allowManagement": "true",
            "allowScopeQuery": "true",
            "includeScopeParam": "true",
            "viewerBaseUrl": "/docs/",
            "configUrl": "/studio/docs-viewer/config/runtime/docs-viewer-config.json",
            "managementBaseUrl": "/studio/api/docs",
        }:
            raise AssertionError(f"unexpected Docs Viewer root attrs: {root_attrs!r}")
        if not actions_visible or actions_disabled:
            raise AssertionError("expected Docs Viewer management actions to be available")
        if not any("/docs/generated/index" in url for url in generated_requests):
            raise AssertionError(f"expected generated index request through local Docs API: {generated_requests!r}")
        if not any("/docs/generated/payload" in url for url in generated_requests):
            raise AssertionError(f"expected generated payload request through local Docs API: {generated_requests!r}")
        if not any("/docs/delete-preview" in url for url in management_posts):
            raise AssertionError(f"expected delete preview request through local Docs API: {management_posts!r}")
        if "child docs still depend" not in delete_blocker_text:
            raise AssertionError(f"expected delete preview blocker status, got {delete_blocker_text!r}")
        if not header_box or not docs_box:
            raise AssertionError("could not measure local Docs Viewer layout")
        if abs(header_box["x"] - docs_box["x"]) > 1:
            raise AssertionError(f"Docs Viewer should align with the centered shell content: header={header_box}, docs={docs_box}")
        if main_css_count:
            raise AssertionError(f"Docs Viewer management shell should not load public main CSS, got {main_css_count}")
        if studio_css_count != 1:
            raise AssertionError(f"expected one Studio shell stylesheet, got {studio_css_count}")
        if management_css_count != 1:
            raise AssertionError(f"expected one management stylesheet, got {management_css_count}")
        if docs_script_count != 1:
            raise AssertionError(f"expected one Docs Viewer script, got {docs_script_count}")
        if nav_link != "/docs/?mode=manage":
            raise AssertionError(f"unexpected docs nav href: {nav_link!r}")
        if query_value(final_url, "mode") != "manage":
            raise AssertionError(f"expected mode=manage in URL, got {final_url}")
        if title != "Docs Viewer":
            raise AssertionError(f"unexpected docs title: {title!r}")
        if not any("/docs/broken-links" in url for url in broken_link_requests):
            raise AssertionError(f"expected broken-links report request through local Docs API: {broken_link_requests!r}")
        if report_scope != "studio":
            raise AssertionError(f"expected broken-links report to default to Studio scope, got {report_scope!r}")
        if "studio" not in report_status:
            raise AssertionError(f"expected broken-links report status to include selected scope, got {report_status!r}")
        if errors:
            raise AssertionError(f"page errors during local Docs Viewer smoke: {errors!r}")
        print(f"local Studio Docs Viewer OK: {base_url}/docs/?scope=studio&doc=docs-viewer&mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
