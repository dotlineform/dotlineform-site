#!/usr/bin/env python3
"""Smoke-check Docs Viewer theme normalization, projection, and storage ownership."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
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


def assert_theme_module_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-theme.js'
            );
            const createRoot = () => {
                const root = document.createElement('div');
                root.innerHTML = `
                    <button data-docs-viewer-theme-toggle>
                        <span data-docs-viewer-theme-icon="light"></span>
                        <span data-docs-viewer-theme-icon="dark"></span>
                    </button>
                    <button data-docs-viewer-theme-toggle>
                        <span data-docs-viewer-theme-icon="light"></span>
                        <span data-docs-viewer-theme-icon="dark"></span>
                    </button>
                `;
                document.body.appendChild(root);
                return root;
            };
            const toggleState = root => Array.from(
                root.querySelectorAll('[data-docs-viewer-theme-toggle]')
            ).map(button => ({
                pressed: button.getAttribute('aria-pressed'),
                label: button.getAttribute('aria-label'),
                title: button.title,
                lightHidden: button.querySelector(
                    '[data-docs-viewer-theme-icon="light"]'
                ).hasAttribute('hidden'),
                darkHidden: button.querySelector(
                    '[data-docs-viewer-theme-icon="dark"]'
                ).hasAttribute('hidden')
            }));
            const createStorage = initialValue => ({
                value: initialValue,
                writes: [],
                getItem(key) {
                    return key === 'theme' ? this.value : null;
                },
                setItem(key, value) {
                    this.writes.push([key, value]);
                    this.value = value;
                }
            });

            document.documentElement.removeAttribute('data-theme');
            const normalizedRoot = createRoot();
            const normalizedStorage = createStorage('sepia');
            const normalizedOwner = module.initDocsViewerThemeToggle({
                root: normalizedRoot,
                document,
                storage: normalizedStorage
            });
            const normalized = {
                theme: document.documentElement.getAttribute('data-theme'),
                stored: normalizedStorage.value,
                writes: normalizedStorage.writes.slice(),
                toggles: toggleState(normalizedRoot)
            };
            normalizedRoot.querySelector('[data-docs-viewer-theme-toggle]').click();
            const toggled = {
                theme: document.documentElement.getAttribute('data-theme'),
                stored: normalizedStorage.value,
                writes: normalizedStorage.writes.slice(),
                toggles: toggleState(normalizedRoot)
            };
            normalizedOwner.setTheme('invented');
            const programmaticFallback = {
                theme: document.documentElement.getAttribute('data-theme'),
                stored: normalizedStorage.value,
                toggles: toggleState(normalizedRoot)
            };
            normalizedRoot.remove();

            document.documentElement.setAttribute('data-theme', 'dark');
            const precedenceRoot = createRoot();
            const precedenceStorage = createStorage('light');
            module.initDocsViewerThemeToggle({
                root: precedenceRoot,
                document,
                storage: precedenceStorage
            });
            const attributePrecedence = {
                theme: document.documentElement.getAttribute('data-theme'),
                stored: precedenceStorage.value,
                writes: precedenceStorage.writes.slice(),
                toggles: toggleState(precedenceRoot)
            };
            precedenceRoot.remove();

            document.documentElement.removeAttribute('data-theme');
            const blockedRoot = createRoot();
            const blockedStorage = {
                getItem() { throw new Error('blocked read'); },
                setItem() { throw new Error('blocked write'); }
            };
            const blockedOwner = module.initDocsViewerThemeToggle({
                root: blockedRoot,
                document,
                storage: blockedStorage
            });
            const blockedStorageFallback = {
                owner: Boolean(blockedOwner),
                theme: document.documentElement.getAttribute('data-theme'),
                toggles: toggleState(blockedRoot)
            };
            blockedRoot.remove();

            const emptyRoot = document.createElement('div');
            const emptyOwner = module.initDocsViewerThemeToggle({
                root: emptyRoot,
                document,
                storage: createStorage('dark')
            });
            document.documentElement.removeAttribute('data-theme');
            return {
                normalized,
                toggled,
                programmaticFallback,
                attributePrecedence,
                blockedStorageFallback,
                emptyOwner
            };
        }"""
    )
    light_toggle = {
        "pressed": "false",
        "label": "Switch to dark mode",
        "title": "Switch to dark mode",
        "lightHidden": False,
        "darkHidden": True,
    }
    dark_toggle = {
        "pressed": "true",
        "label": "Switch to light mode",
        "title": "Switch to light mode",
        "lightHidden": True,
        "darkHidden": False,
    }
    expected = {
        "normalized": {
            "theme": "light",
            "stored": "light",
            "writes": [["theme", "light"]],
            "toggles": [light_toggle, light_toggle],
        },
        "toggled": {
            "theme": "dark",
            "stored": "dark",
            "writes": [["theme", "light"], ["theme", "dark"]],
            "toggles": [dark_toggle, dark_toggle],
        },
        "programmaticFallback": {
            "theme": "light",
            "stored": "light",
            "toggles": [light_toggle, light_toggle],
        },
        "attributePrecedence": {
            "theme": "dark",
            "stored": "dark",
            "writes": [["theme", "dark"]],
            "toggles": [dark_toggle, dark_toggle],
        },
        "blockedStorageFallback": {
            "owner": True,
            "theme": "light",
            "toggles": [light_toggle, light_toggle],
        },
        "emptyOwner": None,
    }
    if result != expected:
        raise AssertionError(f"unexpected Docs Viewer theme module contract: {result!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", required=True)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.goto(base_url, wait_until="domcontentloaded", timeout=args.timeout_ms)
                assert_theme_module_contract(page)
            finally:
                browser.close()
        if errors:
            raise AssertionError(f"page errors during Docs Viewer theme module smoke: {errors!r}")
        print("Docs Viewer theme module OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
