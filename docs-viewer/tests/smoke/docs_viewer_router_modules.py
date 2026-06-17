#!/usr/bin/env python3
"""Smoke-check focused Docs Viewer router module contracts."""

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


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const router = await import('/docs-viewer/runtime/js/shared/docs-viewer-router.js');
            window.__docsViewerRouterModuleSmoke = { router };
        }"""
    )


def assert_missing_doc_history(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { router } = window.__docsViewerRouterModuleSmoke;
            const docsById = new Map([
                ['known', { doc_id: 'known' }],
                ['default-doc', { doc_id: 'default-doc' }]
            ]);
            const resolved = router.resolveViewerRouteDocId({
                requestedDocId: 'missing-doc',
                docsById,
                defaultRouteDocId: 'default-doc',
                defaultDocId: () => 'known'
            });
            const resolvedDefaultless = router.resolveViewerRouteDocId({
                requestedDocId: '',
                docsById,
                defaultRouteDocId: '',
                defaultDocId: () => 'known'
            });
            const resolvedStaleScopeDefault = router.resolveViewerRouteDocId({
                requestedDocId: 'moments',
                docsById,
                defaultRouteDocId: '',
                viewerScope: 'moments',
                defaultDocId: () => 'known'
            });
            const historyCalls = [];
            let missingHandled = false;
            await router.loadViewerDoc({
                docId: 'missing-doc',
                historyMode: 'push',
                hash: 'missing-section',
                state: {
                    docsById,
                    payloadCache: new Map(),
                    requestId: 0
                },
                resolveLoadableDocId: (docId) => docsById.has(docId) ? docId : '',
                setHistory: (docId, hash, query, mode) => historyCalls.push({ docId, hash, query, mode }),
                handleMissingDoc: () => { missingHandled = true; }
            });
            return { resolved, resolvedDefaultless, resolvedStaleScopeDefault, historyCalls, missingHandled };
        }"""
    )
    if result["resolved"] != {
        "requestedDocId": "missing-doc",
        "docId": "missing-doc",
        "corrected": False,
        "missing": True,
    }:
        raise AssertionError(f"missing route resolution changed: {result!r}")
    if result["historyCalls"] != [{"docId": "missing-doc", "hash": "missing-section", "query": "", "mode": "push"}]:
        raise AssertionError(f"missing doc history changed: {result!r}")
    if result["missingHandled"] is not True:
        raise AssertionError(f"missing doc handler was not called: {result!r}")
    if result["resolvedDefaultless"] != {
        "requestedDocId": "",
        "docId": "known",
        "corrected": True,
    }:
        raise AssertionError(f"defaultless route fallback changed: {result!r}")
    if result["resolvedStaleScopeDefault"] != {
        "requestedDocId": "moments",
        "docId": "known",
        "corrected": True,
    }:
        raise AssertionError(f"stale scope default fallback changed: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(route_url(base_url, "/404.html"), wait_until="domcontentloaded")
    install_fixture(page)
    assert_missing_doc_history(page)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=Path("."))
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()

    server, base_url = start_static_server(args.site_root)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_default_timeout(args.timeout_ms)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                run_smoke(page, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer router module smoke: {errors!r}")
    print("Docs Viewer router module smoke OK")


if __name__ == "__main__":
    main()
