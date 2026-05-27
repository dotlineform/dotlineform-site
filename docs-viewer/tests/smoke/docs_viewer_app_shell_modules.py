#!/usr/bin/env python3
"""Smoke-check Docs Viewer app-shell helper contracts."""

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


def assert_management_actions_render(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="true">
                  <div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            const ids = [
                'docsViewerManageRow',
                'docsViewerManageActionsButton',
                'docsViewerManageActionsMenu',
                'docsViewerManageRebuildButton',
                'docsViewerManageNormalizeOrderButton',
                'docsViewerManageSettingsButton',
                'docsViewerManageNewScopeButton',
                'docsViewerManageDeleteScopeButton',
                'docsViewerManageImportButton',
                'docsViewerManageNewButton',
                'docsViewerManageEditButton',
                'docsViewerManageArchiveButton',
                'docsViewerManageDeleteButton',
                'docsViewerManageViewableButton',
                'docsViewerDraftToggle'
            ];
            return {
                returnedRowId: returned.managementActions && returned.managementActions.id,
                missingIds: ids.filter((id) => !document.getElementById(id)),
                menuRole: document.getElementById('docsViewerManageActionsMenu')?.getAttribute('role') || '',
                menuItemCount: document.querySelectorAll('#docsViewerManageActionsMenu [role="menuitem"]').length,
                hiddenScopedButtons: [
                    document.getElementById('docsViewerManageNewScopeButton')?.hidden,
                    document.getElementById('docsViewerManageDeleteScopeButton')?.hidden
                ],
                themeToggleCount: document.querySelectorAll('[data-docs-viewer-theme-toggle]').length,
                lightIconCount: document.querySelectorAll('[data-docs-viewer-theme-icon="light"]').length,
                darkIconHidden: document.querySelector('[data-docs-viewer-theme-icon="dark"]')?.hasAttribute('hidden')
            };
        }"""
    )
    if result["returnedRowId"] != "docsViewerManageRow":
        raise AssertionError(f"app shell did not return the management row: {result!r}")
    if result["missingIds"]:
        raise AssertionError(f"app shell omitted expected management refs: {result!r}")
    if result["menuRole"] != "menu" or result["menuItemCount"] != 10:
        raise AssertionError(f"app shell did not render the expected Actions menu: {result!r}")
    if result["hiddenScopedButtons"] != [True, True]:
        raise AssertionError(f"scope lifecycle buttons should start hidden until capabilities load: {result!r}")
    if result["themeToggleCount"] != 1 or result["lightIconCount"] != 1 or result["darkIconHidden"] is not True:
        raise AssertionError(f"theme toggle did not preserve expected refs/state: {result!r}")


def assert_management_actions_omitted(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false">
                  <div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            return {
                returnedRow: Boolean(returned.managementActions),
                manageRowCount: document.querySelectorAll('#docsViewerManageRow').length,
                actionButtonCount: document.querySelectorAll('#docsViewerManageActionsButton').length,
                mountChildCount: document.querySelector('[data-docs-viewer-management-actions-mount]').children.length
            };
        }"""
    )
    if result != {
        "returnedRow": False,
        "manageRowCount": 0,
        "actionButtonCount": 0,
        "mountChildCount": 0,
    }:
        raise AssertionError(f"public route management action omission failed: {result!r}")


def assert_render_is_idempotent(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="true">
                  <div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await module.initDocsViewerAppShell({ root, document });
            await module.initDocsViewerAppShell({ root, document });
            return {
                rowCount: document.querySelectorAll('#docsViewerManageRow').length,
                actionButtonCount: document.querySelectorAll('#docsViewerManageActionsButton').length,
                mountChildCount: document.querySelector('[data-docs-viewer-management-actions-mount]').children.length
            };
        }"""
    )
    if result != {"rowCount": 1, "actionButtonCount": 1, "mountChildCount": 1}:
        raise AssertionError(f"app shell render was not idempotent: {result!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", required=True, help="Site root to serve.")
    args = parser.parse_args()

    static_server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(base_url, wait_until="domcontentloaded")

            assert_management_actions_render(page)
            assert_management_actions_omitted(page)
            assert_render_is_idempotent(page)

            browser.close()
            if errors:
                raise AssertionError(f"page errors during app-shell module smoke: {errors!r}")
        print("Docs Viewer app-shell modules OK")
        return 0
    finally:
        static_server.shutdown()
        static_server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
