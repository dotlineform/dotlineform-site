#!/usr/bin/env python3
"""Smoke-check Docs Viewer index panel JavaScript helpers."""

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


def assert_index_panel_helpers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/studio/docs-viewer/runtime/js/docs-viewer-index-panel.js');
            const storage = new Map();
            const storageAdapter = {
                getItem: (key) => storage.has(key) ? storage.get(key) : null,
                setItem: (key, value) => storage.set(key, value)
            };
            const storageKey = module.buildIndexPanelStorageKey('studio');
            const legacyKey = module.buildLegacySidebarStorageKey('studio');
            storage.set(legacyKey, 'expanded');
            const migratedNormal = module.readIndexPanelState({ storage: storageAdapter, storageKey, legacyStorageKey: legacyKey });
            storage.set(legacyKey, 'collapsed');
            const migratedCollapsed = module.readIndexPanelState({ storage: storageAdapter, storageKey, legacyStorageKey: legacyKey });
            module.persistIndexPanelState({ storage: storageAdapter, storageKey, state: 'expanded' });
            const storedExpanded = module.readIndexPanelState({ storage: storageAdapter, storageKey, legacyStorageKey: legacyKey });
            const sequence = [
                module.nextIndexPanelState('collapsed'),
                module.nextIndexPanelState('normal'),
                module.nextIndexPanelState('expanded')
            ];
            const directExpanded = [
                module.expandedIndexPanelState('collapsed'),
                module.expandedIndexPanelState('normal'),
                module.expandedIndexPanelState('expanded')
            ];
            const collapsedProjection = module.projectIndexPanelState('collapsed', { available: true });
            const normalProjection = module.projectIndexPanelState('normal', { available: true });
            const expandedProjection = module.projectIndexPanelState('expanded', { available: true });
            const unavailableProjection = module.projectIndexPanelState('expanded', { available: false });
            return {
                storageKey,
                legacyKey,
                migratedNormal,
                migratedCollapsed,
                storedExpanded,
                sequence,
                directExpanded,
                collapsedProjection,
                normalProjection,
                expandedProjection,
                unavailableProjection
            };
        }"""
    )
    if result["storageKey"] != "dotlineform-docs-viewer-index-panel:studio":
        raise AssertionError(f"unexpected storage key: {result!r}")
    if result["legacyKey"] != "dotlineform-docs-viewer-sidebar:studio":
        raise AssertionError(f"unexpected legacy storage key: {result!r}")
    if result["migratedNormal"] != "normal":
        raise AssertionError(f"legacy expanded did not migrate to normal: {result!r}")
    if result["migratedCollapsed"] != "collapsed":
        raise AssertionError(f"legacy collapsed did not migrate: {result!r}")
    if result["storedExpanded"] != "expanded":
        raise AssertionError(f"stored expanded was not preserved: {result!r}")
    if result["sequence"] != ["normal", "collapsed", "normal"]:
        raise AssertionError(f"unexpected state sequence: {result!r}")
    if result["directExpanded"] != ["expanded", "expanded", "expanded"]:
        raise AssertionError(f"unexpected direct expanded sequence: {result!r}")
    if result["collapsedProjection"]["stepLabel"] != "Restore index panel" or result["collapsedProjection"]["expandHidden"] is not True:
        raise AssertionError(f"collapsed projection mismatch: {result!r}")
    if result["normalProjection"]["stepLabel"] != "Collapse index panel" or result["normalProjection"]["stepIcon"] != "‹" or result["normalProjection"]["expandHidden"] is not False:
        raise AssertionError(f"normal projection mismatch: {result!r}")
    if result["expandedProjection"]["documentPaneVisible"] is not False:
        raise AssertionError(f"expanded mode should hide document pane: {result!r}")
    if result["expandedProjection"]["expandHidden"] is not True or result["expandedProjection"]["stepIcon"] != "‹" or result["expandedProjection"]["stepLabel"] != "Restore index panel":
        raise AssertionError(f"expanded controls mismatch: {result!r}")
    if result["expandedProjection"]["legacySidebarState"] != "expanded":
        raise AssertionError(f"expanded mode should remain sidebar-expanded for compatibility: {result!r}")
    if result["unavailableProjection"]["activeState"] != "normal" or result["unavailableProjection"]["toggleHidden"] is not True:
        raise AssertionError(f"unavailable projection mismatch: {result!r}")


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_index_panel_helpers(page)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for module imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()
