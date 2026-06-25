#!/usr/bin/env python3
"""Smoke-check the public site header theme toggle."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


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


def assert_theme_toggle(page: Page, base_url: str, viewport: dict[str, int]) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.goto(route_url(base_url, "/series/"), wait_until="domcontentloaded")
    page.wait_for_selector(".siteThemeToggle", timeout=10_000)
    state = page.evaluate(
        """() => {
            const button = document.querySelector("#themeToggle");
            const footerToggle = document.querySelector(".site-footer #themeToggle");
            const lightIcon = button?.querySelector('[data-theme-icon="light"]');
            const darkIcon = button?.querySelector('[data-theme-icon="dark"]');
            return {
                buttonCount: document.querySelectorAll("#themeToggle").length,
                footerToggle: Boolean(footerToggle),
                theme: document.documentElement.getAttribute("data-theme"),
                pressed: button?.getAttribute("aria-pressed") || "",
                label: button?.getAttribute("aria-label") || "",
                title: button?.getAttribute("title") || "",
                text: button?.textContent.trim() || "",
                lightHidden: lightIcon ? lightIcon.hasAttribute("hidden") : null,
                darkHidden: darkIcon ? darkIcon.hasAttribute("hidden") : null
            };
        }"""
    )
    expected = {
        "buttonCount": 1,
        "footerToggle": False,
        "theme": "light",
        "pressed": "false",
        "label": "Switch to dark mode",
        "title": "Switch to dark mode",
        "text": "",
        "lightHidden": False,
        "darkHidden": True,
    }
    actual = {key: state.get(key) for key in expected}
    if actual != expected:
        raise AssertionError(f"unexpected public theme toggle default state at {viewport!r}: {state!r}")

    page.locator("#themeToggle").click()
    dark_state = page.evaluate(
        """() => {
            const button = document.querySelector("#themeToggle");
            const lightIcon = button?.querySelector('[data-theme-icon="light"]');
            const darkIcon = button?.querySelector('[data-theme-icon="dark"]');
            return {
                theme: document.documentElement.getAttribute("data-theme"),
                storedTheme: window.localStorage.getItem("theme"),
                pressed: button?.getAttribute("aria-pressed") || "",
                label: button?.getAttribute("aria-label") || "",
                lightHidden: lightIcon ? lightIcon.hasAttribute("hidden") : null,
                darkHidden: darkIcon ? darkIcon.hasAttribute("hidden") : null
            };
        }"""
    )
    if dark_state != {
        "theme": "dark",
        "storedTheme": "dark",
        "pressed": "true",
        "label": "Switch to light mode",
        "lightHidden": True,
        "darkHidden": False,
    }:
        raise AssertionError(f"unexpected public theme toggle dark state: {dark_state!r}")

    page.locator("#themeToggle").click()
    final_state = page.evaluate(
        """() => ({
            theme: document.documentElement.getAttribute("data-theme"),
            storedTheme: window.localStorage.getItem("theme")
        })"""
    )
    if final_state != {"theme": "light", "storedTheme": "light"}:
        raise AssertionError(f"public theme toggle did not return to light state: {final_state!r}")
    return {"width": viewport["width"], "height": viewport["height"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default="/tmp/dlf-jekyll-build")
    args = parser.parse_args()

    server, base_url = start_static_server(Path(args.site_root))
    try:
        results = []
        errors: list[str] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                page = browser.new_page(viewport=viewport)
                page.on("pageerror", lambda error: errors.append(str(error)))
                results.append(assert_theme_toggle(page, base_url, viewport))
                page.close()
            browser.close()
        if errors:
            raise AssertionError(f"page errors during public theme toggle smoke: {errors!r}")
        print(json.dumps({"base_url": base_url, "viewports": results}, sort_keys=True))
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
