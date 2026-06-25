#!/usr/bin/env python3
"""Smoke-check the Tag Aliases route reaches the Analytics ready state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from analytics_app_server import AnalyticsAppServer  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


def start_server() -> tuple[AnalyticsAppServer, str]:
    server = AnalyticsAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def run(base_url: str) -> None:
    target = f"{base_url.rstrip('/')}/analytics/tag-aliases/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(target, wait_until="domcontentloaded")
        root = page.locator("#tag-aliases")
        wait_for_route_ready(page, "#tag-aliases", "data-analytics-ready", "data-analytics-busy")
        expect(root).to_have_attribute("data-analytics-mode", "list", timeout=10_000)
        expect(root).to_have_attribute("data-analytics-record-loaded", "true", timeout=10_000)
        if errors:
            raise AssertionError(f"page errors during Tag Aliases route smoke: {errors!r}")
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = None
    base_url = args.base_url
    if not base_url:
        server, base_url = start_server()
    try:
        run(base_url)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
