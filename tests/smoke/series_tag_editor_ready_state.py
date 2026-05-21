#!/usr/bin/env python3
"""Smoke-check the Series Tag Editor route reaches the Studio ready state."""

from __future__ import annotations

import argparse

from playwright.sync_api import expect, sync_playwright


def run(base_url: str, series_id: str) -> None:
    target = f"{base_url.rstrip('/')}/studio/analytics/series-tag-editor/?series={series_id}"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(target, wait_until="domcontentloaded")
        root = page.locator("#seriesTagEditorRoot")
        expect(root).to_be_visible(timeout=10_000)
        expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
        expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
        expect(page.locator("#tag-studio")).to_have_attribute("data-series-id", series_id, timeout=10_000)
        if errors:
            raise AssertionError(f"page errors during Series Tag Editor route smoke: {errors!r}")
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--series", default="036")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.base_url, args.series)


if __name__ == "__main__":
    main()
