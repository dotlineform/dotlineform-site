#!/usr/bin/env python3
"""Smoke-check operational Studio routes reach ready state without local services."""

from __future__ import annotations

import argparse

from playwright.sync_api import expect, sync_playwright


ROUTES = [
    {
        "path": "/studio/bulk-add-work/",
        "root": "#bulkAddWorkRoot",
        "button": "#bulkAddWorkPreview",
    },
    {
        "path": "/studio/project-state/",
        "root": "#projectStateRoot",
        "button": "#projectStateRunButton",
    },
    {
        "path": "/studio/audits/",
        "root": "#studioAuditsRoot",
        "button": "[data-run-audit]",
    },
    {
        "path": "/studio/thumbnail-quality/",
        "root": "#thumbnailQualityRoot",
        "button": "#thumbnailQualityRefreshButton",
    },
]


def run(base_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("http://127.0.0.1:8788/**", lambda route: route.abort())
        page.route("http://127.0.0.1:8789/**", lambda route: route.abort())
        page.route("http://127.0.0.1:8790/**", lambda route: route.abort())
        for route in ROUTES:
            page.goto(f"{base_url.rstrip('/')}{route['path']}", wait_until="domcontentloaded")
            root = page.locator(route["root"])
            expect(root).to_be_visible(timeout=10_000)
            expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
            expect(root).to_have_attribute("data-studio-service", "unavailable", timeout=10_000)
            expect(page.locator(route["button"])).to_be_disabled(timeout=10_000)
        if errors:
            raise AssertionError(f"page errors during operational route ready smoke: {errors!r}")
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
