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
            page.on("pageerror", lambda exc: errors.append(str(exc)))

            for route, doc_id in [("/library/?doc=library", "library"), ("/analysis/?doc=analysis", "analysis")]:
                page.goto(route_url(base_url, route), wait_until="domcontentloaded")
                page.wait_for_selector("#docsViewerRoot:not([hidden])", timeout=args.timeout_ms)
                page.wait_for_function(
                    """docId => document.querySelector("#docsViewerContent h1")?.id === docId""",
                    arg=doc_id,
                    timeout=args.timeout_ms,
                )
                root_attrs = page.locator("#docsViewerRoot").evaluate(
                    """root => ({
                        allowManagement: root.dataset.allowManagement || "",
                        managementBaseUrl: root.dataset.managementBaseUrl || "",
                        includeScopeParam: root.dataset.includeScopeParam || "",
                        viewerBaseUrl: root.dataset.viewerBaseUrl || ""
                    })"""
                )
                base_css_count = page.locator('link[href*="docs-viewer-base.css"]').count()
                management_css_count = page.locator('link[href*="docs-viewer-management.css"]').count()
                studio_css_count = page.locator('link[href*="assets/studio/"], link[href*="studio/app/"]').count()
                studio_script_count = page.locator('script[src*="assets/studio/"], script[src*="studio/app/"]').count()
                manage_actions_count = page.locator(".docsViewer__manageActions").count()
                manage_button_count = page.locator("#docsViewerManageActionsButton").count()

                if root_attrs["allowManagement"] == "true":
                    raise AssertionError(f"{route} unexpectedly allows management: {root_attrs!r}")
                if root_attrs["managementBaseUrl"]:
                    raise AssertionError(f"{route} unexpectedly exposes management base URL: {root_attrs!r}")
                if root_attrs["viewerBaseUrl"] not in {"/library/", "/analysis/"}:
                    raise AssertionError(f"{route} has unexpected viewer base URL: {root_attrs!r}")
                if base_css_count != 1:
                    raise AssertionError(f"{route} expected one Docs Viewer base stylesheet, got {base_css_count}")
                if management_css_count:
                    raise AssertionError(f"{route} loaded management CSS")
                if studio_css_count or studio_script_count:
                    raise AssertionError(f"{route} loaded Studio-only assets")
                if manage_actions_count or manage_button_count:
                    raise AssertionError(f"{route} rendered management controls")

            browser.close()
            if errors:
                raise AssertionError(f"page errors during public Docs Viewer read-only smoke: {errors!r}")
        print(f"public Docs Viewer read-only OK: {base_url}/library/ and {base_url}/analysis/")
        return 0
    finally:
        static_server.shutdown()
        static_server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
