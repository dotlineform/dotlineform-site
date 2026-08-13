#!/usr/bin/env python3
"""Smoke-check standalone Docs Viewer Manage route boot and service projection."""

from __future__ import annotations

import argparse

from playwright.sync_api import sync_playwright

from docs_viewer_route_smoke_support import (
    start_docs_viewer_server,
    wait_for_document,
)


DOC_ID = "d-20260501-174746-efd581"
DOC_TITLE = "Testing"


def manage_route_state(page) -> dict[str, object]:
    return page.locator("#docsViewerRoot").evaluate(
        """async root => {
            const configUrl = root.dataset.routeConfigUrl || '';
            const payload = await fetch(configUrl).then(response => response.json());
            const route = (payload.routes || []).find(record => (
                record.route_id === root.dataset.routeId
            )) || {};
            return {
                appKind: root.dataset.docsViewerAppKind || '',
                managementUi: root.dataset.managementUi || '',
                sourceService: root.dataset.sourceService || '',
                ready: root.dataset.docsViewerReady || '',
                busy: root.dataset.docsViewerBusy || '',
                routeId: root.dataset.routeId || '',
                routeConfigUrl: configUrl,
                viewerBaseUrl: route.viewer_base_url || '',
                generatedBaseUrl: route.services?.generated_data?.base_url || '',
                sourceBaseUrl: route.services?.source?.base_url || '',
                managementBaseUrl: route.services?.management?.base_url || ''
            };
        }"""
    )


def assert_manage_route_boundary(state: dict[str, object], base_url: str) -> None:
    expected = {
        "appKind": "manage",
        "managementUi": "true",
        "sourceService": "true",
        "ready": "true",
        "busy": "false",
        "routeId": "docs-manage",
        "routeConfigUrl": "/docs-viewer/config/routes/docs-viewer-routes.json",
        "viewerBaseUrl": "/docs/",
        "generatedBaseUrl": base_url,
        "sourceBaseUrl": base_url,
        "managementBaseUrl": base_url,
    }
    if state != expected:
        raise AssertionError(f"Docs Viewer Manage route boundary changed: {state!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_docs_viewer_server()
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on("pageerror", lambda error: errors.append(error.stack or str(error)))
                page.goto(
                    f"{base_url}/docs/?scope=studio&doc={DOC_ID}",
                    wait_until="domcontentloaded",
                )
                wait_for_document(page, DOC_TITLE, args.timeout_ms)
                assert_manage_route_boundary(manage_route_state(page), base_url)
            finally:
                browser.close()
        if errors:
            raise AssertionError(f"page errors during Docs Viewer Manage boot: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()

    print(f"Docs Viewer Manage route boundary OK: {base_url}/docs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
