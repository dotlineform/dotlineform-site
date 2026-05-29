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
            const module = await import('/docs-viewer/runtime/js/docs-viewer-index-panel.js');
            const storage = new Map();
            const storageAdapter = {
                getItem: (key) => storage.has(key) ? storage.get(key) : null,
                setItem: (key, value) => storage.set(key, value)
            };
            const storageKey = module.buildIndexPanelStorageKey('studio');
            const defaultState = module.readIndexPanelState({ storage: storageAdapter, storageKey });
            module.persistIndexPanelState({ storage: storageAdapter, storageKey, state: 'collapsed' });
            const storedCollapsed = module.readIndexPanelState({ storage: storageAdapter, storageKey });
            module.persistIndexPanelState({ storage: storageAdapter, storageKey, state: 'expanded' });
            const storedExpanded = module.readIndexPanelState({ storage: storageAdapter, storageKey });
            module.persistIndexPanelState({ storage: storageAdapter, storageKey, state: 'invalid' });
            const normalizedInvalid = module.readIndexPanelState({ storage: storageAdapter, storageKey });
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
            const treeProjection = module.projectIndexPanelState('normal', {
                available: true,
                capabilities: { layoutStates: ['normal', 'collapsed'], toolbar: false }
            });
            const treeExpandedProjection = module.projectIndexPanelState('expanded', {
                available: true,
                capabilities: { layoutStates: ['normal', 'collapsed'], toolbar: false }
            });
            module.persistIndexPanelState({
                storage: storageAdapter,
                storageKey,
                state: 'expanded',
                capabilities: { layoutStates: ['normal', 'collapsed'], toolbar: false }
            });
            const cappedStoredExpanded = module.readIndexPanelState({ storage: storageAdapter, storageKey });
            const expandedProjection = module.projectIndexPanelState('expanded', { available: true });
            const unavailableProjection = module.projectIndexPanelState('expanded', { available: false });
            return {
                storageKey,
                defaultState,
                storedCollapsed,
                storedExpanded,
                normalizedInvalid,
                sequence,
                directExpanded,
                collapsedProjection,
                normalProjection,
                treeProjection,
                treeExpandedProjection,
                cappedStoredExpanded,
                expandedProjection,
                unavailableProjection
            };
        }"""
    )
    if result["storageKey"] != "dotlineform-docs-viewer-index-panel:studio":
        raise AssertionError(f"unexpected storage key: {result!r}")
    if result["defaultState"] != "normal":
        raise AssertionError(f"empty storage did not default to normal: {result!r}")
    if result["storedCollapsed"] != "collapsed":
        raise AssertionError(f"stored collapsed was not preserved: {result!r}")
    if result["storedExpanded"] != "expanded":
        raise AssertionError(f"stored expanded was not preserved: {result!r}")
    if result["normalizedInvalid"] != "normal":
        raise AssertionError(f"invalid stored state was not normalized: {result!r}")
    if result["sequence"] != ["normal", "collapsed", "normal"]:
        raise AssertionError(f"unexpected state sequence: {result!r}")
    if result["directExpanded"] != ["expanded", "expanded", "expanded"]:
        raise AssertionError(f"unexpected direct expanded sequence: {result!r}")
    if result["collapsedProjection"]["stepLabel"] != "Restore index panel" or result["collapsedProjection"]["expandHidden"] is not True:
        raise AssertionError(f"collapsed projection mismatch: {result!r}")
    if result["normalProjection"]["stepLabel"] != "Collapse index panel" or result["normalProjection"]["stepIcon"] != "‹" or result["normalProjection"]["expandHidden"] is not False:
        raise AssertionError(f"normal projection mismatch: {result!r}")
    if result["treeProjection"]["expandHidden"] is not True or result["treeProjection"]["expandedState"] != "normal":
        raise AssertionError(f"tree capability projection should not expose expanded mode: {result!r}")
    if result["treeExpandedProjection"]["activeState"] != "normal" or result["treeExpandedProjection"]["documentPaneVisible"] is not True:
        raise AssertionError(f"unsupported expanded tree state was not restored: {result!r}")
    if result["cappedStoredExpanded"] != "normal":
        raise AssertionError(f"unsupported persisted state was not capped: {result!r}")
    if result["expandedProjection"]["documentPaneVisible"] is not False:
        raise AssertionError(f"expanded mode should hide document pane: {result!r}")
    if result["expandedProjection"]["expandHidden"] is not True or result["expandedProjection"]["stepIcon"] != "‹" or result["expandedProjection"]["stepLabel"] != "Restore index panel":
        raise AssertionError(f"expanded controls mismatch: {result!r}")
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
