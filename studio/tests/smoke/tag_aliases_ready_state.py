#!/usr/bin/env python3
"""Smoke-check the Tag Aliases route reaches the Studio ready state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402
from local_studio_tag_server import start_studio_tag_server, stop_studio_tag_server  # noqa: E402


def run(base_url: str) -> None:
    target = f"{base_url.rstrip('/')}/studio/tag-aliases/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(target, wait_until="domcontentloaded")
        root = page.locator("#tag-aliases")
        wait_for_route_ready(page, "#tag-aliases", "data-studio-ready", "data-studio-busy")
        expect(root).to_have_attribute("data-studio-mode", "list", timeout=10_000)
        expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
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
        server, base_url = start_studio_tag_server(REPO_ROOT)
    try:
        run(base_url)
    finally:
        if server is not None:
            stop_studio_tag_server(server)


if __name__ == "__main__":
    main()
