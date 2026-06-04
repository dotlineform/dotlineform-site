#!/usr/bin/env python3
"""Smoke-check public Docs Viewer installs stay read-only."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def wait_for_rendered_doc(page, doc_id: str, title: str, timeout_ms: int) -> None:
    page.wait_for_selector("#docsViewerRoot:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """expected => document.querySelector("#docsViewerContent h1")?.textContent.trim() === expected""",
        arg=title,
        timeout=timeout_ms,
    )
    page.wait_for_function(
        """docId => document.querySelector(".docsViewer__navLink.is-active")?.dataset.docId === docId""",
        arg=doc_id,
        timeout=timeout_ms,
    )


def assert_info_panel_route(
    page,
    base_url: str,
    route: str,
    doc_id: str,
    title: str,
    timeout_ms: int,
    viewport: dict[str, int],
) -> None:
    page.set_viewport_size(viewport)
    page.goto(route_url(base_url, route), wait_until="domcontentloaded")
    wait_for_rendered_doc(page, doc_id, title, timeout_ms)
    initial_url = page.url
    page.locator("#docsViewerInfoToggle").click()
    page.wait_for_selector("#docsViewerInfoPanel:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """docId => document.querySelector(".docsViewer__metadataInfoIdValue")?.textContent === docId""",
        arg=doc_id,
        timeout=timeout_ms,
    )
    state = page.locator("#docsViewerRoot").evaluate(
        """root => ({
            infoPanelState: root.dataset.infoPanelState || "",
            layout: root.dataset.viewerLayout || "",
            selectedHeading: document.querySelector("#docsViewerContent h1")?.textContent.trim() || "",
            panelTitle: document.querySelector(".docsViewer__metadataInfoTitle")?.textContent || "",
            docIdValue: document.querySelector(".docsViewer__metadataInfoIdValue")?.textContent || "",
            routeHref: document.querySelector(".docsViewer__metadataInfoRow a")?.getAttribute("href") || "",
            toggleExpanded: document.querySelector("#docsViewerInfoToggle")?.getAttribute("aria-expanded") || "",
            managementActions: document.querySelectorAll(".docsViewer__manageActions, #docsViewerManageActionsButton").length
        })"""
    )
    overlap = page.locator("#docsViewerRoot").evaluate(
        """() => {
            const main = document.querySelector(".docsViewer__main")?.getBoundingClientRect();
            const panel = document.querySelector("#docsViewerInfoPanel")?.getBoundingClientRect();
            if (!main || !panel) return true;
            return !(panel.left >= main.right || main.left >= panel.right || panel.top >= main.bottom || main.top >= panel.bottom);
        }"""
    )
    if page.url != initial_url:
        raise AssertionError(f"{route} info panel changed URL: {initial_url!r} -> {page.url!r}")
    if state["infoPanelState"] != "open" or state["toggleExpanded"] != "true":
        raise AssertionError(f"{route} info panel did not open: {state!r}")
    if state["selectedHeading"] != title or state["docIdValue"] != doc_id:
        raise AssertionError(f"{route} info panel lost selected document context: {state!r}")
    if not state["panelTitle"] or not state["routeHref"]:
        raise AssertionError(f"{route} info panel omitted metadata title/link: {state!r}")
    if state["managementActions"]:
        raise AssertionError(f"{route} info panel exposed management controls: {state!r}")
    if overlap:
        raise AssertionError(f"{route} info panel overlaps main view panel at viewport {viewport!r}")
    page.locator("#docsViewerInfoPanelClose").click()
    page.wait_for_function(
        """() => document.querySelector("#docsViewerInfoPanel")?.hidden === true""",
        timeout=timeout_ms,
    )
    closed = page.locator("#docsViewerRoot").evaluate(
        """root => ({
            infoPanelState: root.dataset.infoPanelState || "",
            toggleExpanded: document.querySelector("#docsViewerInfoToggle")?.getAttribute("aria-expanded") || "",
            selectedHeading: document.querySelector("#docsViewerContent h1")?.textContent.trim() || ""
        })"""
    )
    if closed != {"infoPanelState": "closed", "toggleExpanded": "false", "selectedHeading": title}:
        raise AssertionError(f"{route} info panel did not close cleanly: {closed!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", required=True, help="Built public site root to serve.")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    static_server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            request_failures: list[str] = []
            http_failures: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.on("requestfailed", lambda request: request_failures.append(f"{request.url}: {request.failure}"))
            page.on(
                "response",
                lambda response: http_failures.append(f"{response.status}: {response.url}") if response.status >= 400 else None,
            )

            for route, doc_id, title in [
                ("/library/?doc=library", "library", "Library"),
                ("/analysis/?doc=analysis", "analysis", "Analysis"),
            ]:
                page.goto(route_url(base_url, route), wait_until="domcontentloaded")
                wait_for_rendered_doc(page, doc_id, title, args.timeout_ms)
                root_attrs = page.locator("#docsViewerRoot").evaluate(
                    """async root => {
                        const routeConfigUrl = root.dataset.routeConfigUrl || "";
                        const payload = await fetch(routeConfigUrl).then(response => response.json());
                        const routeConfig = payload.routes.find(record => record.route_id === root.dataset.routeId) || {};
                        const uiTextUrl = routeConfig.config_urls?.ui_text || "";
                        const uiText = await fetch(uiTextUrl).then(response => response.json());
                        return {
                            allowManagement: root.dataset.allowManagement || "",
                            managementBaseUrl: root.dataset.managementBaseUrl || "",
                            includeScopeParam: root.dataset.includeScopeParam || "",
                            viewerBaseUrl: root.dataset.viewerBaseUrl || "",
                            routeId: root.dataset.routeId || "",
                            routeConfigUrl,
                            routeConfig,
                            uiTextUrl,
                            uiText,
                            routeIds: (payload.routes || []).map(record => record.route_id),
                            managementRouteCount: (payload.routes || []).filter(record => record.access?.allow_management === true).length,
                            hostedViewIds: (payload.routes || []).flatMap(record => (record.hosted_views?.records || []).map(view => view.id))
                        };
                    }"""
                )
                base_css_count = page.locator('link[href*="docs-viewer-base.css"]').count()
                management_css_count = page.locator('link[href*="docs-viewer-management.css"]').count()
                studio_css_count = page.locator('link[href*="assets/studio/"], link[href*="studio/app/"]').count()
                studio_script_count = page.locator('script[src*="assets/studio/"], script[src*="studio/app/"]').count()
                manage_actions_count = page.locator(".docsViewer__manageActions").count()
                manage_button_count = page.locator("#docsViewerManageActionsButton").count()
                manage_document_control_count = page.locator(
                    "#docsViewerManageEditButton, #docsViewerManageSourceButton, #docsViewerStatusPills"
                ).count()
                resource_urls = page.evaluate(
                    """() => performance.getEntriesByType('resource').map(entry => entry.name)"""
                )
                management_js_urls = [
                    url
                    for url in resource_urls
                    if "/docs-viewer/runtime/js/docs-viewer-management" in url
                ]

                if root_attrs["allowManagement"] == "true":
                    raise AssertionError(f"{route} unexpectedly allows management: {root_attrs!r}")
                if root_attrs["managementBaseUrl"]:
                    raise AssertionError(f"{route} unexpectedly exposes management base URL: {root_attrs!r}")
                if root_attrs["routeId"] not in {"library", "analysis"}:
                    raise AssertionError(f"{route} has unexpected route id: {root_attrs!r}")
                if root_attrs["routeConfigUrl"] != "/docs-viewer/config/routes/docs-viewer-public-routes.json":
                    raise AssertionError(f"{route} has unexpected route config URL: {root_attrs!r}")
                if root_attrs["routeConfig"].get("default_scope_id") != root_attrs["routeId"]:
                    raise AssertionError(f"{route} route config does not match route scope: {root_attrs!r}")
                if root_attrs["routeConfig"].get("access", {}).get("allow_management") is not False:
                    raise AssertionError(f"{route} route config unexpectedly allows management: {root_attrs!r}")
                if root_attrs["routeConfig"].get("viewer_base_url") not in {"/library/", "/analysis/"}:
                    raise AssertionError(f"{route} route config has unexpected viewer base URL: {root_attrs!r}")
                if root_attrs["routeConfig"].get("config_urls", {}).get("ui_text") != "/docs-viewer/config/ui-text/public.json":
                    raise AssertionError(f"{route} route config did not use public UI text: {root_attrs!r}")
                if root_attrs["uiTextUrl"] != "/docs-viewer/config/ui-text/public.json":
                    raise AssertionError(f"{route} loaded unexpected UI text URL: {root_attrs!r}")
                if root_attrs["uiText"] != {"recently_added_button": "recently added"}:
                    raise AssertionError(f"{route} public UI text widened unexpectedly: {root_attrs!r}")
                if root_attrs["managementRouteCount"] or "docs-manage" in root_attrs["routeIds"]:
                    raise AssertionError(f"{route} public route registry exposed management routes: {root_attrs!r}")
                if root_attrs["hostedViewIds"]:
                    raise AssertionError(f"{route} public route registry exposed hosted manage-only views: {root_attrs!r}")
                if base_css_count != 1:
                    raise AssertionError(f"{route} expected one Docs Viewer base stylesheet, got {base_css_count}")
                if management_css_count:
                    raise AssertionError(f"{route} loaded management CSS")
                if studio_css_count or studio_script_count:
                    raise AssertionError(f"{route} loaded Studio-only assets")
                if manage_actions_count or manage_button_count:
                    raise AssertionError(f"{route} rendered management controls")
                if manage_document_control_count:
                    raise AssertionError(f"{route} rendered management document controls")
                if management_js_urls:
                    raise AssertionError(f"{route} loaded management-only JS: {management_js_urls!r}")

                assert_info_panel_route(
                    page,
                    base_url,
                    route,
                    doc_id,
                    title,
                    args.timeout_ms,
                    {"width": 1280, "height": 900},
                )
                assert_info_panel_route(
                    page,
                    base_url,
                    route,
                    doc_id,
                    title,
                    args.timeout_ms,
                    {"width": 390, "height": 780},
                )

            browser.close()
            if errors:
                raise AssertionError(f"page errors during public Docs Viewer read-only smoke: {errors!r}")
            if request_failures:
                raise AssertionError(f"request failures during public Docs Viewer read-only smoke: {request_failures!r}")
            if http_failures:
                raise AssertionError(f"HTTP failures during public Docs Viewer read-only smoke: {http_failures!r}")
        print(f"public Docs Viewer read-only OK: {base_url}/library/ and {base_url}/analysis/")
        return 0
    finally:
        static_server.shutdown()
        static_server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
