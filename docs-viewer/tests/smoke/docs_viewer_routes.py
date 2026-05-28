#!/usr/bin/env python3
"""Smoke-check Docs Viewer route, history, and scope behavior."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, sync_playwright


ROOT_SELECTOR = "#docsViewerRoot"
CONTENT_SELECTOR = "#docsViewerContent"
RESULTS_SELECTOR = "#docsViewerResults"
SEARCH_SELECTOR = "#docsViewerSearchInput"


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


def query_value(url: str, key: str) -> str:
    return (parse_qs(urlparse(url).query).get(key) or [""])[0]


def wait_for_doc(page: Page, doc_id: str, timeout_ms: int) -> str:
    page.wait_for_selector(f"{ROOT_SELECTOR}:not([hidden])", timeout=timeout_ms)
    page.wait_for_selector(f"{CONTENT_SELECTOR}:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """([selector, docId]) => {
            const heading = document.querySelector(`${selector} h1`);
            return heading && heading.id === docId;
        }""",
        arg=[CONTENT_SELECTOR, doc_id],
        timeout=timeout_ms,
    )
    active_doc = query_value(page.url, "doc")
    if active_doc != doc_id:
        raise AssertionError(f"expected URL doc={doc_id!r}, got {active_doc!r} in {page.url}")
    return page.locator(f"{CONTENT_SELECTOR} h1").inner_text()


def wait_for_search_route(page: Page, query: str, timeout_ms: int) -> dict[str, object]:
    page.wait_for_selector(f"{ROOT_SELECTOR}:not([hidden])", timeout=timeout_ms)
    page.wait_for_selector(f"{RESULTS_SELECTOR}:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """([selector, expected]) => document.querySelector(selector)?.value === expected""",
        arg=[SEARCH_SELECTOR, query],
        timeout=timeout_ms,
    )
    page.wait_for_function(
        """selector => {
            const status = document.querySelector(selector);
            return status && !status.hidden && status.textContent.trim().length > 0;
        }""",
        arg="#docsViewerStatus",
        timeout=timeout_ms,
    )
    search_query = query_value(page.url, "q")
    if search_query != query:
        raise AssertionError(f"expected URL q={query!r}, got {search_query!r} in {page.url}")
    return {
        "query": search_query,
        "status": page.locator("#docsViewerStatus").inner_text(),
        "result_count": page.locator(".docsViewer__resultItem").count(),
        "content_hidden": page.locator(CONTENT_SELECTOR).evaluate("node => node.hidden"),
    }


def assert_marker_survived(page: Page, label: str) -> None:
    marker = page.evaluate("window.__docsViewerRouteSmokeMarker || ''")
    if marker != "route-smoke":
        raise AssertionError(f"browser reloaded during {label}; route marker was lost")


def assert_hash_target(page: Page, target_id: str, timeout_ms: int) -> None:
    if urlparse(page.url).fragment != target_id:
        raise AssertionError(f"expected URL hash #{target_id}, got {page.url}")
    page.wait_for_function(
        """targetId => {
            const target = document.getElementById(targetId);
            if (!target) return false;
            return !document.querySelector("#docsViewerContent")?.hidden && target.offsetParent !== null;
        }""",
        arg=target_id,
        timeout=timeout_ms,
    )


def assert_index_panel_toggle(page: Page, timeout_ms: int) -> None:
    page.wait_for_function(
        """selector => document.querySelector(selector)?.dataset.indexPanelState === 'normal'""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )
    step_toggle = page.locator("#docsViewerSidebarToggle")
    expand_toggle = page.locator("#docsViewerSidebarExpand")
    page.wait_for_function(
        """() => {
            const step = document.querySelector('#docsViewerSidebarToggle');
            const expand = document.querySelector('#docsViewerSidebarExpand');
            return step &&
                expand &&
                !step.hidden &&
                !expand.hidden &&
                step.textContent.trim() === '‹' &&
                expand.textContent.trim() === '⤢' &&
                (step.compareDocumentPosition(expand) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
        }""",
        timeout=timeout_ms,
    )
    expand_toggle.click()
    page.wait_for_function(
        """selector => {
            const root = document.querySelector(selector);
            const content = document.querySelector('#docsViewerContent');
            const step = document.querySelector('#docsViewerSidebarToggle');
            const expand = document.querySelector('#docsViewerSidebarExpand');
            return root?.dataset.indexPanelState === 'expanded' &&
                content &&
                getComputedStyle(content.closest('.docsViewer__main')).display === 'none' &&
                step &&
                !step.hidden &&
                step.textContent.trim() === '‹' &&
                expand &&
                expand.hidden;
        }""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )
    step_toggle.click()
    page.wait_for_function(
        """selector => document.querySelector(selector)?.dataset.indexPanelState === 'normal'""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )
    step_toggle.click()
    page.wait_for_function(
        """selector => {
            const root = document.querySelector(selector);
            const nav = document.querySelector('#docsViewerNav');
            const main = document.querySelector('.docsViewer__main');
            const step = document.querySelector('#docsViewerSidebarToggle');
            const expand = document.querySelector('#docsViewerSidebarExpand');
            return root?.dataset.indexPanelState === 'collapsed' &&
                nav &&
                getComputedStyle(nav).display === 'none' &&
                main &&
                getComputedStyle(main).display !== 'none' &&
                step &&
                !step.hidden &&
                step.textContent.trim() === '›' &&
                expand &&
                expand.hidden;
        }""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )
    step_toggle.click()
    page.wait_for_function(
        """selector => {
            const root = document.querySelector(selector);
            const nav = document.querySelector('#docsViewerNav');
            const main = document.querySelector('.docsViewer__main');
            return root?.dataset.indexPanelState === 'normal' &&
                nav &&
                getComputedStyle(nav).display !== 'none' &&
                main &&
                getComputedStyle(main).display !== 'none';
        }""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )


def assert_index_panel_expanded_tree_click(page: Page, timeout_ms: int) -> None:
    page.wait_for_function(
        """selector => document.querySelector(selector)?.dataset.indexPanelState === 'normal'""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )
    page.locator("#docsViewerSidebarExpand").click()
    page.wait_for_function(
        """selector => {
            const root = document.querySelector(selector);
            const main = document.querySelector('.docsViewer__main');
            return root?.dataset.indexPanelState === 'expanded' &&
                main &&
                getComputedStyle(main).display === 'none';
        }""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )
    page.locator("#docsViewerNav a[data-doc-id='docs-viewer-overview']").first.click()
    page.wait_for_function(
        """([selector, docId]) => {
            const heading = document.querySelector(`${selector} h1`);
            return heading && heading.id === docId;
        }""",
        arg=[CONTENT_SELECTOR, "docs-viewer-overview"],
        timeout=timeout_ms,
    )
    active_doc = query_value(page.url, "doc")
    if active_doc != "docs-viewer-overview":
        raise AssertionError(f"expected tree click to set doc='docs-viewer-overview', got {active_doc!r} in {page.url}")
    page.wait_for_function(
        """selector => {
            const root = document.querySelector(selector);
            const activeLink = document.querySelector("#docsViewerNav a[data-doc-id='docs-viewer-overview']");
            const main = document.querySelector('.docsViewer__main');
            return root?.dataset.indexPanelState === 'expanded' &&
                activeLink?.classList.contains('is-active') &&
                activeLink?.getAttribute('aria-current') === 'page' &&
                main &&
                getComputedStyle(main).display === 'none';
        }""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )


def run_route_smoke(page: Page, base_url: str, timeout_ms: int) -> dict[str, object]:
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    page.goto(route_url(base_url, "/docs/?scope=studio&doc=docs-viewer"), wait_until="domcontentloaded")
    docs_title = wait_for_doc(page, "docs-viewer", timeout_ms)
    assert_index_panel_toggle(page, timeout_ms)
    page.evaluate("window.__docsViewerRouteSmokeMarker = 'route-smoke'")

    page.locator(f"{CONTENT_SELECTOR} a[href*='doc=docs-viewer-overview']").first.click()
    wait_for_doc(page, "docs-viewer-overview", timeout_ms)
    assert_marker_survived(page, "internal link routing")

    page.go_back(wait_until="domcontentloaded")
    wait_for_doc(page, "docs-viewer", timeout_ms)
    assert_marker_survived(page, "history back")

    page.go_forward(wait_until="domcontentloaded")
    overview_title = wait_for_doc(page, "docs-viewer-overview", timeout_ms)
    assert_marker_survived(page, "history forward")

    page.evaluate(
        """() => {
            const link = document.createElement('a');
            link.id = 'docsViewerRouteSmokeMissingLink';
            link.href = '/docs/?scope=studio&doc=missing-route-smoke';
            link.textContent = 'Missing route smoke';
            document.querySelector('#docsViewerContent').appendChild(link);
        }"""
    )
    page.locator("#docsViewerRouteSmokeMissingLink").click()
    page.wait_for_function(
        """([selector, expectedDoc]) => {
            const content = document.querySelector(selector);
            return content &&
                !content.hidden &&
                content.textContent.includes('Document not found.') &&
                new URL(window.location.href).searchParams.get('doc') === expectedDoc;
        }""",
        arg=[CONTENT_SELECTOR, "missing-route-smoke"],
        timeout=timeout_ms,
    )
    assert_marker_survived(page, "missing-doc routing")
    page.go_back(wait_until="domcontentloaded")
    wait_for_doc(page, "docs-viewer-overview", timeout_ms)
    assert_marker_survived(page, "missing-doc history back")

    page.goto(
        route_url(base_url, "/docs/?scope=studio&doc=docs-viewer-overview#current-url-and-state-contract"),
        wait_until="domcontentloaded",
    )
    hash_title = wait_for_doc(page, "docs-viewer-overview", timeout_ms)
    assert_hash_target(page, "current-url-and-state-contract", timeout_ms)

    page.goto(route_url(base_url, "/docs/?scope=studio&doc=docs-viewer&q=viewer"), wait_until="domcontentloaded")
    search = wait_for_search_route(page, "viewer", timeout_ms)

    page.goto(route_url(base_url, "/library/?doc=library"), wait_until="domcontentloaded")
    library_title = wait_for_doc(page, "library", timeout_ms)
    if urlparse(page.url).path.rstrip("/") != "/library":
        raise AssertionError(f"expected Library route path, got {page.url}")

    if errors:
        raise AssertionError(f"page errors during Docs Viewer route smoke: {errors!r}")

    return {
        "direct_doc": docs_title,
        "internal_link_doc": overview_title,
        "hash_doc": hash_title,
        "search": search,
        "library_doc": library_title,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a built site root on a temporary local HTTP server.")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    static_server = None
    base_url = args.base_url
    if args.site_root:
        static_server, base_url = start_static_server(Path(args.site_root))

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                result = run_route_smoke(page, base_url, args.timeout_ms)
                print(json.dumps(result, sort_keys=True))
            finally:
                browser.close()
    finally:
        if static_server is not None:
            static_server.shutdown()
            static_server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
