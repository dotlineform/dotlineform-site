#!/usr/bin/env python3
"""Smoke-check the Series Tag Editor route reaches the Analytics ready state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402
from transitional_tag_servers import start_transitional_tag_servers, stop_transitional_tag_servers  # noqa: E402


def run(base_url: str, series_id: str) -> None:
    target = f"{base_url.rstrip('/')}/analytics/series-tag-editor/?series={series_id}"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(target, wait_until="domcontentloaded")
        root = page.locator("#seriesTagEditorRoot")
        wait_for_route_ready(page, "#seriesTagEditorRoot", "data-analytics-ready", "data-analytics-busy")
        expect(root).to_have_attribute("data-analytics-record-loaded", "true", timeout=10_000)
        expect(page.locator("#analytics-tag-editor")).to_have_attribute("data-series-id", series_id, timeout=10_000)
        if errors:
            raise AssertionError(f"page errors during Series Tag Editor route smoke: {errors!r}")
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    parser.add_argument("--series", default="036")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    studio_server = None
    server = None
    previous_studio_env = (None, None)
    base_url = args.base_url
    if not base_url:
        studio_server, server, base_url, previous_studio_env = start_transitional_tag_servers(REPO_ROOT)
    try:
        run(base_url, args.series)
    finally:
        if studio_server is not None and server is not None:
            stop_transitional_tag_servers(studio_server, server, previous_studio_env)


if __name__ == "__main__":
    main()
