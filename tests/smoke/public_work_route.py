#!/usr/bin/env python3
"""Smoke-check representative public work page navigation/content rendering."""

from __future__ import annotations

import argparse
import re

from playwright.sync_api import expect, sync_playwright


def run(base_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{base_url.rstrip('/')}/works/00001/?series=009", wait_until="domcontentloaded")
        expect(page.locator("#workTitleHidden")).to_contain_text("a poem divided into 4 parts", timeout=10_000)
        expect(page.locator("#pageBackLink")).to_contain_text("a poem divided into 4 parts", timeout=10_000)
        expect(page.locator("#workSeriesLink")).to_contain_text("a poem divided into 4 parts", timeout=10_000)
        expect(page.locator("#seriesNav")).to_be_visible(timeout=10_000)
        expect(page.locator("#seriesNavCounter")).to_contain_text("1/", timeout=10_000)
        href_pattern = re.compile(r"/works/[0-9]+/\?series=009")
        expect(page.locator("#seriesNavPrev")).to_have_attribute("href", href_pattern, timeout=10_000)
        expect(page.locator("#seriesNavNext")).to_have_attribute("href", href_pattern, timeout=10_000)
        if errors:
            raise AssertionError(f"page errors during public work route smoke: {errors!r}")
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.base_url)


if __name__ == "__main__":
    main()
