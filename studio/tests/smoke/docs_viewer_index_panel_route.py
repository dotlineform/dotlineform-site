#!/usr/bin/env python3
"""Smoke-check Docs Viewer index panel route wiring."""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

from docs_viewer_routes import (
    assert_index_panel_expanded_tree_click,
    assert_index_panel_toggle,
    route_url,
    start_static_server,
    wait_for_doc,
)


def run(site_root: Path, timeout_ms: int) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(route_url(base_url, "/docs/?scope=studio&doc=docs-viewer"), wait_until="domcontentloaded")
            wait_for_doc(page, "docs-viewer", timeout_ms)
            assert_index_panel_toggle(page, timeout_ms)
            assert_index_panel_expanded_tree_click(page, timeout_ms)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default="/tmp/dlf-jekyll-build", help="Built site root to serve.")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run(Path(args.site_root), args.timeout_ms)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
