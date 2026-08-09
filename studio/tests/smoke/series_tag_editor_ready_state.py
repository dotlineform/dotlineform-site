#!/usr/bin/env python3
"""Smoke-check the Series Tag Editor route reaches the Studio ready state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402
from local_studio_tag_server import start_studio_tag_server, stop_studio_tag_server  # noqa: E402


def run(base_url: str, series_id: str) -> None:
    target = f"{base_url.rstrip('/')}/studio/series-tag-editor/?series={series_id}"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        requests: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        page.goto(target, wait_until="domcontentloaded")
        root = page.locator("#seriesTagEditorRoot")
        wait_for_route_ready(page, "#seriesTagEditorRoot", "data-studio-ready", "data-studio-busy")
        expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
        expect(page.locator("#analytics-tag-editor")).to_have_attribute("data-series-id", series_id, timeout=10_000)

        page.goto(f"{base_url.rstrip('/')}/studio/series-tag-editor/?series=002", wait_until="domcontentloaded")
        expect(page.locator("#seriesTagEditorRoot")).to_have_attribute("data-studio-ready", "true", timeout=10_000)
        expect(page.locator("#seriesTagEditorRoot")).to_have_attribute("data-studio-busy", "false", timeout=10_000)
        expect(page.locator("#seriesTagEditorEmpty")).to_have_text("Unknown series id: 002", timeout=10_000)

        expected_reads = (
            f"key=catalogue_lookup_series_base&record_id={series_id}",
            "key=catalogue_work_record&record_id=",
            "key=catalogue_lookup_series_base&record_id=002",
        )
        missing_reads = [token for token in expected_reads if not any(token in url for url in requests)]
        if missing_reads:
            raise AssertionError(f"Series Tag Editor missed exact Studio reads {missing_reads!r}: {requests!r}")
        public_reads = [
            url for url in requests
            if "/assets/data/series_index.json" in url
            or "/assets/series/index/" in url
            or "/assets/works/index/" in url
        ]
        if public_reads:
            raise AssertionError(f"Series Tag Editor retained public Catalogue reads: {public_reads!r}")
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
    server = None
    base_url = args.base_url
    if not base_url:
        server, base_url = start_studio_tag_server(REPO_ROOT)
    try:
        run(base_url, args.series)
    finally:
        if server is not None:
            stop_studio_tag_server(server)


if __name__ == "__main__":
    main()
