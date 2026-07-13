#!/usr/bin/env python3
"""Smoke-check Docs Viewer management capability error projection."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


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


def assert_capability_error_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-management-capabilities.js');
            const management = {
                managementCapabilities: null,
                managementCapabilityCheckId: 0,
                managementCapabilityError: '',
                managementChecked: false,
                managementAvailable: false
            };
            const routeSession = { managementContext: false };
            const renderEvents = [];
            let fetchCount = 0;
            const controller = module.createDocsViewerManagementCapabilityController({
                management,
                routeSession,
                context: {
                    MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS: 60,
                    MANAGEMENT_CAPABILITY_RETRY_DELAY_MS: 500,
                    isManagementContext: () => true,
                    managementBaseUrl: 'http://127.0.0.1:9999'
                },
                callbacks: {
                    viewerScope: () => 'studio',
                    managementClientOptions: () => ({
                        baseUrl: 'http://127.0.0.1:9999',
                        fetch: () => {
                            fetchCount += 1;
                            return Promise.resolve({
                            ok: false,
                            status: 400,
                            json: () => Promise.resolve({
                                ok: false,
                                error: "Unknown parent_id 'missing-parent' for doc 'broken-parent-doc'"
                            })
                            });
                        }
                    }),
                    renderManagementUi: () => renderEvents.push({
                        checked: management.managementChecked,
                        available: management.managementAvailable,
                        error: management.managementCapabilityError
                    }),
                    renderSidebar: () => {}
                }
            });
            controller.initialize();
            await new Promise((resolve) => window.setTimeout(resolve, 20));
            return { management, routeSession, renderEvents, fetchCount };
        }"""
    )
    management = result["management"]
    if management["managementChecked"] is not True or management["managementAvailable"] is not False:
        raise AssertionError(f"unexpected capability state after failed retries: {result!r}")
    if result["routeSession"]["managementContext"] is not True:
        raise AssertionError(f"management context was not projected through route-session state: {result!r}")
    expected = "Unknown parent_id 'missing-parent' for doc 'broken-parent-doc'"
    if management["managementCapabilityError"] != expected:
        raise AssertionError(f"capability error was not retained for UI projection: {result!r}")
    if not any(event.get("error") == expected for event in result["renderEvents"]):
        raise AssertionError(f"management renderer was not called with the capability error: {result!r}")
    if result["fetchCount"] != 1:
        raise AssertionError(f"400 capability errors should not consume the retry budget: {result!r}")


def assert_active_scope_delete_navigation(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-management-capabilities.js');
            const payload = { action: 'delete_scope', scope_id: 'tmp', fallback_scope_id: 'studio' };
            return {
                active: module.scopeDeleteNavigationTarget(payload, 'tmp'),
                other: module.scopeDeleteNavigationTarget(payload, 'dlf'),
                nonDelete: module.scopeDeleteNavigationTarget({ action: 'create_scope' }, 'tmp')
            };
        }"""
    )
    if result != {"active": "studio", "other": "", "nonDelete": ""}:
        raise AssertionError(f"unexpected active-scope delete navigation: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(route_url(base_url, "/"), wait_until="domcontentloaded")
    assert_capability_error_projection(page)
    assert_active_scope_delete_navigation(page)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repo/site root to serve.")
    args = parser.parse_args(argv)

    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            run_smoke(page, base_url)
            browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer management capabilities modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
