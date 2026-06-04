#!/usr/bin/env python3
"""Smoke-check the standalone Docs Viewer service manage shell."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import sys
from pathlib import Path
from threading import Thread
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))

from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402


def start_server() -> tuple[DocsViewerServer, str]:
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=True,
    )
    server = DocsViewerServer(("127.0.0.1", 0), REPO_ROOT, config)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    server.docs_viewer_config = replace(config, port=server.server_address[1], base_url=base_url)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, base_url


def query_value(url: str, key: str) -> str:
    return (parse_qs(urlparse(url).query).get(key) or [""])[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=10) as response:
            health = json.loads(response.read().decode("utf-8"))
        if health.get("service") != "docs_viewer" or health.get("ok") is not True:
            raise AssertionError(f"unexpected health response: {health!r}")

        with urllib.request.urlopen(f"{base_url}/capabilities", timeout=10) as response:
            capabilities = json.loads(response.read().decode("utf-8"))
        studio_caps = capabilities.get("capabilities", {}).get("scopes", {}).get("studio", {})
        if capabilities.get("capabilities", {}).get("docs_management") is not True:
            raise AssertionError(f"expected Docs Viewer management to be enabled: {capabilities!r}")
        if studio_caps.get("available") is not True or studio_caps.get("generated_data_reads") is not True:
            raise AssertionError(f"expected real Studio generated data reads: {studio_caps!r}")

        preview_payload = json.dumps({"scope": "studio", "doc_id": "docs-viewer"}).encode("utf-8")
        preview_request = urllib.request.Request(
            f"{base_url}/docs/delete-preview",
            data=preview_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(preview_request, timeout=10) as response:
            delete_preview = json.loads(response.read().decode("utf-8"))
        if delete_preview.get("ok") is not True or delete_preview.get("doc_id") != "docs-viewer":
            raise AssertionError(f"unexpected delete preview response: {delete_preview!r}")

        rejected_request = urllib.request.Request(
            f"{base_url}/docs/delete-preview",
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
                if "/docs/generated/" in request.url
                else None,
            )
            page.on(
                "request",
                lambda request: management_posts.append(request.url)
                if request.method == "POST" and "/docs/" in urlparse(request.url).path
                else None,
            )
            page.on(
                "request",
                lambda request: broken_link_requests.append(request.url)
                if request.method == "POST" and urlparse(request.url).path == "/docs/broken-links"
                else None,
            )
            page.goto(f"{base_url}/docs/?scope=studio&doc=docs-viewer&mode=manage", wait_until="domcontentloaded")
            page.wait_for_selector("#docsViewerRoot:not([hidden])", timeout=args.timeout_ms)
            page.wait_for_selector("#docsViewerContent:not([hidden])", timeout=args.timeout_ms)
            page.wait_for_function(
                """() => document.querySelector("#docsViewerContent h1")?.textContent?.trim() === "Docs Viewer" """,
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
            page.wait_for_function(
                """() => {
                    const root = document.querySelector("#docsViewerRoot");
                    const nav = document.querySelector("#docsViewerNav");
                    const step = document.querySelector("#docsViewerSidebarToggle");
                    const expand = document.querySelector("#docsViewerSidebarExpand");
                    const viewToggle = document.querySelector("#docsViewerIndexViewToggle");
                    return root?.dataset.indexPanelState === "normal" &&
                        root?.dataset.indexPanelView === "index-tree" &&
                        nav &&
                        nav.querySelector('a[data-doc-id="docs-viewer-overview"]') &&
                        step &&
                        step.getAttribute("aria-controls") === "docsViewerNav" &&
                        !step.hidden &&
                        expand &&
                        expand.getAttribute("aria-controls") === "docsViewerNav" &&
                        expand.hidden &&
                        viewToggle &&
                        viewToggle.dataset.activeIndexPanelView === "index-tree" &&
                        viewToggle.dataset.indexPanelView === "index-graph";
                }""",
                timeout=args.timeout_ms,
            )
            page.locator("#docsViewerSidebarToggle").click()
            page.wait_for_function(
                """() => {
                    const root = document.querySelector("#docsViewerRoot");
                    const nav = document.querySelector("#docsViewerNav");
                    const main = document.querySelector(".docsViewer__main");
                    return root?.dataset.indexPanelState === "collapsed" &&
                        nav &&
                        getComputedStyle(nav).display === "none" &&
                        main &&
                        getComputedStyle(main).display !== "none";
                }""",
                timeout=args.timeout_ms,
            )
            page.locator("#docsViewerSidebarToggle").click()
            page.wait_for_function(
                """() => document.querySelector("#docsViewerRoot")?.dataset.indexPanelState === "normal" """,
                timeout=args.timeout_ms,
            )
            page.locator("#docsViewerIndexViewToggle").click()
            page.wait_for_function(
                """() => {
                    const root = document.querySelector("#docsViewerRoot");
                    const placeholder = document.querySelector("#docsViewerIndexPlaceholder");
                    const expand = document.querySelector("#docsViewerSidebarExpand");
                    return root?.dataset.indexPanelView === "index-graph" &&
                        root?.dataset.indexPanelState === "normal" &&
                        placeholder &&
                        !placeholder.hidden &&
                        expand &&
                        !expand.hidden;
                }""",
                timeout=args.timeout_ms,
            )
            page.locator("#docsViewerSidebarExpand").click()
            page.wait_for_function(
                """() => {
                    const root = document.querySelector("#docsViewerRoot");
                    const main = document.querySelector(".docsViewer__main");
                    return root?.dataset.indexPanelState === "expanded" &&
                        root?.dataset.indexPanelView === "index-graph" &&
                        main &&
                        getComputedStyle(main).display === "none";
                }""",
                timeout=args.timeout_ms,
            )
            page.locator("#docsViewerIndexViewToggle").click()
            page.wait_for_function(
                """() => {
                    const root = document.querySelector("#docsViewerRoot");
                    const nav = document.querySelector("#docsViewerNav");
                    const main = document.querySelector(".docsViewer__main");
                    const expand = document.querySelector("#docsViewerSidebarExpand");
                    return root?.dataset.indexPanelState === "normal" &&
                        root?.dataset.indexPanelView === "index-tree" &&
                        nav &&
                        getComputedStyle(nav).display !== "none" &&
                        main &&
                        getComputedStyle(main).display !== "none" &&
                        expand &&
                        expand.hidden;
                }""",
                timeout=args.timeout_ms,
            )
            page.locator('#docsViewerNav a[data-doc-id="docs-viewer-overview"]').first.click()
            page.wait_for_function(
                """() => {
                    const root = document.querySelector("#docsViewerRoot");
                    const heading = document.querySelector("#docsViewerContent h1");
                    const activeLink = document.querySelector('#docsViewerNav a[data-doc-id="docs-viewer-overview"]');
                    return root?.dataset.indexPanelState === "normal" &&
                        root?.dataset.indexPanelView === "index-tree" &&
                        heading?.textContent?.trim() === "Docs Viewer Overview" &&
                        activeLink?.classList.contains("is-active") &&
                        activeLink?.getAttribute("aria-current") === "page";
                }""",
                timeout=args.timeout_ms,
            )
            tree_url = page.url
            page.goto(f"{base_url}/docs/?scope=studio&doc=docs-viewer&mode=manage", wait_until="domcontentloaded")
            page.wait_for_function(
                """() => document.querySelector("#docsViewerContent h1")?.textContent?.trim() === "Docs Viewer" """,
                timeout=args.timeout_ms,
            )
            root_attrs = page.locator("#docsViewerRoot").evaluate(
                """async root => {
                    const routeConfigUrl = root.dataset.routeConfigUrl || "";
                    const payload = await fetch(routeConfigUrl).then(response => response.json());
                    const routeConfig = payload.routes.find(record => record.route_id === root.dataset.routeId) || {};
                    const uiTextUrl = routeConfig.config_urls?.ui_text || "";
                    const uiText = await fetch(uiTextUrl).then(response => response.json());
                    return {
                        allowManagement: root.dataset.allowManagement || "",
                        allowScopeQuery: root.dataset.allowScopeQuery || "",
                        includeScopeParam: root.dataset.includeScopeParam || "",
                        viewerBaseUrl: root.dataset.viewerBaseUrl || "",
                        routeId: root.dataset.routeId || "",
                        routeConfigUrl,
                        routeConfig,
                        uiTextUrl,
                        uiText: {
                            recently_added_button: uiText.recently_added_button || "",
                            scope_new_button: uiText.scope_new_button || "",
                            scope_delete_menu_button: uiText.scope_delete_menu_button || "",
                            settings_button: uiText.settings_button || "",
                            import_button: uiText.docs_html_import?.import_button || ""
                        },
                        configUrl: root.dataset.docsViewerConfigUrl || "",
                        generatedBaseUrl: root.dataset.generatedBaseUrl || "",
                        managementBaseUrl: root.dataset.managementBaseUrl || ""
                    };
                }"""
            )
            studio_css_count = page.locator('link[href*="/studio/app/assets/css/studio.css"]').count()
            main_css_count = page.locator('link[href*="/assets/css/main.css"]').count()
            viewer_css_count = page.locator('link[href*="/docs-viewer/static/css/docs-viewer.css"]').count()
            base_css_count = page.locator('link[href*="docs-viewer-base.css"]').count()
            management_css_count = page.locator('link[href*="docs-viewer-management.css"]').count()
            docs_script_count = page.locator('script[src*="docs-viewer-manage.js"]').count()

            page.locator("#docsViewerInfoToggle").click()
            page.wait_for_function(
                """() => document.querySelector(".docsViewer__metadataInfoIdValue")?.textContent === "docs-viewer" """,
                timeout=args.timeout_ms,
            )
            info_panel_state = page.locator("#docsViewerRoot").evaluate(
                """root => ({
                    infoPanelState: root.dataset.infoPanelState || "",
                    layout: root.dataset.viewerLayout || "",
                    docIdValue: document.querySelector(".docsViewer__metadataInfoIdValue")?.textContent || "",
                    routeHref: document.querySelector(".docsViewer__metadataInfoRow a")?.getAttribute("href") || "",
                    editButtonVisible: Boolean(document.querySelector("#docsViewerManageEditButton"))
                })"""
            )
            page.locator("#docsViewerInfoPanelClose").click()
            page.wait_for_function(
                """() => document.querySelector("#docsViewerInfoPanel")?.hidden === true """,
                timeout=args.timeout_ms,
            )

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

        expected_attrs = {
            "allowManagement": "true",
            "allowScopeQuery": "",
            "includeScopeParam": "true",
            "viewerBaseUrl": "/docs/",
            "routeId": "docs-manage",
            "routeConfigUrl": "/docs-viewer/config/routes/docs-viewer-routes.json",
            "routeConfig": {
                "schema_version": "docs_viewer_route_config_v1",
                "route_id": "docs-manage",
                "route_path": "/docs/",
                "route_type": "manage",
                "default_scope_id": "studio",
                "default_doc_id": "dev-home",
                "include_scope_param": True,
                "allow_scope_query": True,
                "viewer_base_url": "/docs/",
                "generated_base_url": base_url,
                "access": {
                    "allow_management": True,
                    "allow_scope_query": True,
                    "management_base_url": base_url,
                    "management_mode_value": "manage",
                },
                "docs_paths": {
                    "index_url": "/docs-viewer/generated/docs/studio/index.json",
                    "search_index_url": "/docs-viewer/generated/search/studio/index.json",
                },
                "config_urls": {
                    "docs_viewer": "/docs-viewer/config/defaults/docs-viewer-config.json",
                    "ui_text": "/docs-viewer/config/ui-text/manage.json",
                    "report_registry": "/assets/data/docs/reports.json",
                },
                "panels": {
                    "index": {"enabled": True, "default_state": "normal"},
                    "main": {"enabled": True, "default_view": "rendered-document"},
                    "info": {"enabled": True, "default_view": "metadata-info"},
                },
                "hosted_views": {
                    "records": [
                        {
                            "id": "index-graph",
                            "label": "Index graph",
                            "panel": "index",
                            "access": "manage",
                            "renderer": "index-placeholder",
                            "availability": "available",
                            "placeholder_text": "Graph index placeholder",
                            "capabilities": {
                                "layout_states": ["normal", "collapsed", "expanded"],
                                "toolbar": True,
                                "toolbar_view": "index-graph-toolbar",
                            },
                        }
                    ]
                },
            },
            "uiTextUrl": "/docs-viewer/config/ui-text/manage.json",
            "uiText": {
                "recently_added_button": "recently added",
                "scope_new_button": "New scope",
                "scope_delete_menu_button": "Delete scope",
                "settings_button": "Settings",
                "import_button": "Import",
            },
            "configUrl": "",
            "generatedBaseUrl": "",
            "managementBaseUrl": "",
        }
        if root_attrs != expected_attrs:
            raise AssertionError(f"unexpected Docs Viewer root attrs: {root_attrs!r}")
        if query_value(tree_url, "doc") != "docs-viewer-overview" or query_value(tree_url, "mode") != "manage":
            raise AssertionError(f"expected tree click to keep docs-viewer-overview active in manage mode, got {tree_url}")
        if info_panel_state != {
            "infoPanelState": "open",
            "layout": "index-document-info",
            "docIdValue": "docs-viewer",
            "routeHref": "/docs/?scope=studio&mode=manage&doc=docs-viewer",
            "editButtonVisible": True,
        }:
            raise AssertionError(f"unexpected manage-mode info panel state: {info_panel_state!r}")
        if not any("/docs/generated/index" in url for url in generated_requests):
            raise AssertionError(f"expected generated index request through Docs Viewer service: {generated_requests!r}")
        if not any("/docs/generated/payload" in url for url in generated_requests):
            raise AssertionError(f"expected generated payload request through Docs Viewer service: {generated_requests!r}")
        if not any(urlparse(url).path == "/docs/delete-preview" for url in management_posts):
            raise AssertionError(f"expected delete preview request through Docs Viewer service: {management_posts!r}")
        if "child docs still depend" not in delete_blocker_text:
            raise AssertionError(f"expected delete preview blocker status, got {delete_blocker_text!r}")
        if main_css_count or studio_css_count:
            raise AssertionError(f"standalone Docs Viewer shell should not load host CSS: main={main_css_count}, studio={studio_css_count}")
        if viewer_css_count != 1 or base_css_count or management_css_count != 1 or docs_script_count != 1:
            raise AssertionError(
                "unexpected Docs Viewer asset counts: "
                f"viewer={viewer_css_count}, base={base_css_count}, management={management_css_count}, script={docs_script_count}"
            )
        if query_value(final_url, "mode") != "manage":
            raise AssertionError(f"expected mode=manage in URL, got {final_url}")
        if title != "Docs Viewer":
            raise AssertionError(f"unexpected docs title: {title!r}")
        if not any(urlparse(url).path == "/docs/broken-links" for url in broken_link_requests):
            raise AssertionError(f"expected broken-links report request through Docs Viewer service: {broken_link_requests!r}")
        if report_scope != "studio":
            raise AssertionError(f"expected broken-links report to default to Studio scope, got {report_scope!r}")
        if "broken link" not in report_status:
            raise AssertionError(f"expected broken-links report status, got {report_status!r}")
        if errors:
            raise AssertionError(f"page errors during Docs Viewer service smoke: {errors!r}")
        print(f"Docs Viewer service manage shell OK: {base_url}/docs/?scope=studio&doc=docs-viewer&mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
