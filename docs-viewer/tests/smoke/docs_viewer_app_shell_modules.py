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


def assert_header_controls_render(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false" data-allow-scope-query="false">
                  <div
                    id="docsViewerHeaderControlsMount"
                    data-docs-viewer-header-controls-mount
                    data-enable-search="true"
                    data-search-placeholder="search library"
                    data-search-aria-label="Search library"
                  ></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            const searchInput = document.getElementById('docsViewerSearchInput');
            return {
                returnedHeaderClass: returned.headerControls && returned.headerControls.className,
                scopeSelectCount: document.querySelectorAll('#docsViewerScopeSelect').length,
                recentButtonText: document.getElementById('docsViewerRecentButton')?.textContent || '',
                recentButtonPressed: document.getElementById('docsViewerRecentButton')?.getAttribute('aria-pressed') || '',
                searchPlaceholder: searchInput?.getAttribute('placeholder') || '',
                searchAriaLabel: searchInput?.getAttribute('aria-label') || '',
                visibleLabel: document.querySelector('label[for="docsViewerSearchInput"]')?.textContent || '',
                managementMountCount: document.querySelectorAll('#docsViewerManageActionsMount').length,
                rowCount: document.querySelectorAll('.docsViewer__searchRow').length
            };
        }"""
    )
    expected = {
        "returnedHeaderClass": "docsViewer__searchRow",
        "scopeSelectCount": 0,
        "recentButtonText": "recently added",
        "recentButtonPressed": "false",
        "searchPlaceholder": "search library",
        "searchAriaLabel": "Search library",
        "visibleLabel": "Search library",
        "managementMountCount": 0,
        "rowCount": 1,
    }
    if result != expected:
        raise AssertionError(f"public header controls render failed: {result!r}")


def assert_header_controls_search_disabled_scope_only(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false" data-allow-scope-query="true">
                  <div
                    id="docsViewerHeaderControlsMount"
                    data-docs-viewer-header-controls-mount
                    data-enable-search="false"
                  ></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            return {
                returnedHeaderClass: returned.headerControls && returned.headerControls.className,
                scopeSelectCount: document.querySelectorAll('#docsViewerScopeSelect').length,
                scopeLabelFor: document.querySelector('.docsViewer__scopeField')?.getAttribute('for') || '',
                recentButtonCount: document.querySelectorAll('#docsViewerRecentButton').length,
                searchInputCount: document.querySelectorAll('#docsViewerSearchInput').length,
                managementMountCount: document.querySelectorAll('#docsViewerManageActionsMount').length,
                rowCount: document.querySelectorAll('.docsViewer__searchRow').length
            };
        }"""
    )
    expected = {
        "returnedHeaderClass": "docsViewer__searchRow",
        "scopeSelectCount": 1,
        "scopeLabelFor": "docsViewerScopeSelect",
        "recentButtonCount": 0,
        "searchInputCount": 0,
        "managementMountCount": 0,
        "rowCount": 1,
    }
    if result != expected:
        raise AssertionError(f"search-disabled scope header render failed: {result!r}")


def assert_header_controls_management_render(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="true" data-allow-scope-query="true">
                  <div
                    id="docsViewerHeaderControlsMount"
                    data-docs-viewer-header-controls-mount
                    data-enable-search="true"
                    data-search-placeholder="search studio docs"
                    data-search-aria-label="Search Studio docs"
                  ></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            return {
                returnedHeaderClass: returned.headerControls && returned.headerControls.className,
                returnedRowId: returned.managementActions && returned.managementActions.id,
                scopeSelectCount: document.querySelectorAll('#docsViewerScopeSelect').length,
                recentButtonCount: document.querySelectorAll('#docsViewerRecentButton').length,
                searchInputCount: document.querySelectorAll('#docsViewerSearchInput').length,
                managementMountCount: document.querySelectorAll('#docsViewerManageActionsMount').length,
                manageRowCount: document.querySelectorAll('#docsViewerManageRow').length,
                rowChildIds: Array.from(document.querySelector('.docsViewer__searchRow').children).map((node) => node.id || node.querySelector('[id]')?.id || '')
            };
        }"""
    )
    if result["returnedHeaderClass"] != "docsViewer__searchRow" or result["returnedRowId"] != "docsViewerManageRow":
        raise AssertionError(f"management header render did not return expected rows: {result!r}")
    if result["scopeSelectCount"] != 1 or result["recentButtonCount"] != 1 or result["searchInputCount"] != 1:
        raise AssertionError(f"management header render omitted expected controls: {result!r}")
    if result["managementMountCount"] != 1 or result["manageRowCount"] != 1:
        raise AssertionError(f"management header render omitted action mount/row: {result!r}")
    if result["rowChildIds"] != [
        "docsViewerScopeSelect",
        "docsViewerRecentButton",
        "docsViewerSearchInput",
        "docsViewerManageActionsMount",
    ]:
        raise AssertionError(f"management header control order changed unexpectedly: {result!r}")


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


def assert_index_panel_shell_render(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false">
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            const refs = module.getDocsViewerAppShellIndexPanelRefs({ root, document });
            return {
                returnedNavId: returned.indexPanel && returned.indexPanel.nav && returned.indexPanel.nav.id,
                refNavId: refs.nav && refs.nav.id,
                sidebarCount: document.querySelectorAll('.docsViewer__sidebar').length,
                navCount: document.querySelectorAll('#docsViewerNav').length,
                toggleCount: document.querySelectorAll('#docsViewerSidebarToggle').length,
                expandCount: document.querySelectorAll('#docsViewerSidebarExpand').length,
                toggleControls: document.getElementById('docsViewerSidebarToggle')?.getAttribute('aria-controls') || '',
                expandControls: document.getElementById('docsViewerSidebarExpand')?.getAttribute('aria-controls') || '',
                navLabel: document.getElementById('docsViewerNav')?.getAttribute('aria-label') || ''
            };
        }"""
    )
    expected = {
        "returnedNavId": "docsViewerNav",
        "refNavId": "docsViewerNav",
        "sidebarCount": 1,
        "navCount": 1,
        "toggleCount": 1,
        "expandCount": 1,
        "toggleControls": "docsViewerNav",
        "expandControls": "docsViewerNav",
        "navLabel": "Docs tree",
    }
    if result != expected:
        raise AssertionError(f"index panel shell render failed: {result!r}")


def assert_index_panel_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const shell = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            const state = await import('/docs-viewer/runtime/js/docs-viewer-index-panel.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false">
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await shell.initDocsViewerAppShell({ root, document });
            const refs = shell.getDocsViewerAppShellIndexPanelRefs({ root, document });
            shell.renderDocsViewerAppShellIndexPanelState({
                root,
                refs,
                projection: state.projectIndexPanelState('collapsed', { available: true })
            });
            const collapsed = {
                state: root.dataset.indexPanelState,
                sidebarState: root.dataset.sidebarState,
                toggleHidden: refs.sidebarToggle.hidden,
                toggleExpanded: refs.sidebarToggle.getAttribute('aria-expanded'),
                toggleLabel: refs.sidebarToggle.getAttribute('aria-label'),
                toggleIcon: refs.sidebarToggle.querySelector('.docsViewer__sidebarToggleIcon')?.textContent || '',
                expandHidden: refs.sidebarExpand.hidden
            };
            shell.renderDocsViewerAppShellIndexPanelState({
                root,
                refs,
                projection: state.projectIndexPanelState('expanded', { available: true })
            });
            const expanded = {
                state: root.dataset.indexPanelState,
                sidebarState: root.dataset.sidebarState,
                toggleHidden: refs.sidebarToggle.hidden,
                toggleExpanded: refs.sidebarToggle.getAttribute('aria-expanded'),
                toggleLabel: refs.sidebarToggle.getAttribute('aria-label'),
                expandHidden: refs.sidebarExpand.hidden
            };
            shell.renderDocsViewerAppShellIndexPanelState({
                root,
                refs,
                projection: state.projectIndexPanelState('normal', { available: false })
            });
            const unavailable = {
                state: root.dataset.indexPanelState,
                toggleHidden: refs.sidebarToggle.hidden,
                expandHidden: refs.sidebarExpand.hidden
            };
            return { collapsed, expanded, unavailable };
        }"""
    )
    if result["collapsed"] != {
        "state": "collapsed",
        "sidebarState": "collapsed",
        "toggleHidden": False,
        "toggleExpanded": "false",
        "toggleLabel": "Restore index panel",
        "toggleIcon": "›",
        "expandHidden": True,
    }:
        raise AssertionError(f"collapsed index projection failed: {result!r}")
    if result["expanded"] != {
        "state": "expanded",
        "sidebarState": "expanded",
        "toggleHidden": False,
        "toggleExpanded": "true",
        "toggleLabel": "Restore index panel",
        "expandHidden": True,
    }:
        raise AssertionError(f"expanded index projection failed: {result!r}")
    if result["unavailable"] != {
        "state": "normal",
        "toggleHidden": True,
        "expandHidden": True,
    }:
        raise AssertionError(f"unavailable index projection failed: {result!r}")


def assert_document_shell_render(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false">
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            const refs = module.getDocsViewerAppShellDocumentRefs({ root, document });
            const ids = [
                'docsViewerMeta',
                'docsViewerPath',
                'docsViewerUpdated',
                'docsViewerSummary',
                'docsViewerStatusPills',
                'docsViewerBookmarkToggle',
                'docsViewerContent',
                'docsViewerResultsStatus',
                'docsViewerResults',
                'docsViewerMore'
            ];
            return {
                returnedContentId: returned.documentShell && returned.documentShell.content && returned.documentShell.content.id,
                refContentId: refs.content && refs.content.id,
                mainCount: document.querySelectorAll('.docsViewer__main').length,
                missingIds: ids.filter((id) => !document.getElementById(id)),
                mainLive: document.querySelector('.docsViewer__main')?.getAttribute('aria-live') || '',
                bookmarkText: document.getElementById('docsViewerBookmarkToggle')?.textContent || '',
                bookmarkPressed: document.getElementById('docsViewerBookmarkToggle')?.getAttribute('aria-pressed') || '',
                metaHidden: document.getElementById('docsViewerMeta')?.hidden,
                resultsHidden: document.getElementById('docsViewerResults')?.hidden,
                moreHidden: document.getElementById('docsViewerMore')?.hidden
            };
        }"""
    )
    if result != {
        "returnedContentId": "docsViewerContent",
        "refContentId": "docsViewerContent",
        "mainCount": 1,
        "missingIds": [],
        "mainLive": "polite",
        "bookmarkText": "☆",
        "bookmarkPressed": "false",
        "metaHidden": True,
        "resultsHidden": True,
        "moreHidden": True,
    }:
        raise AssertionError(f"document shell render failed: {result!r}")


def assert_document_shell_management_shape(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="true">
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await module.initDocsViewerAppShell({ root, document });
            return {
                documentShellCount: document.querySelectorAll('.docsViewer__main').length,
                statusPillsCount: document.querySelectorAll('#docsViewerStatusPills').length,
                bookmarkToggleCount: document.querySelectorAll('#docsViewerBookmarkToggle').length,
                manageRowCount: document.querySelectorAll('#docsViewerManageRow').length,
                editButtonCount: document.querySelectorAll('#docsViewerManageEditButton').length
            };
        }"""
    )
    if result != {
        "documentShellCount": 1,
        "statusPillsCount": 1,
        "bookmarkToggleCount": 1,
        "manageRowCount": 1,
        "editButtonCount": 1,
    }:
        raise AssertionError(f"management document shell shape failed: {result!r}")


def assert_document_shell_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false">
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await module.initDocsViewerAppShell({ root, document });
            const refs = module.getDocsViewerAppShellDocumentRefs({ root, document });
            refs.more.innerHTML = '<button>More</button>';
            module.renderDocsViewerAppShellDocumentState({
                refs,
                projection: {
                    metaHidden: true,
                    contentHidden: true,
                    resultsStatusText: 'Searching...',
                    resultsStatusHidden: false,
                    resultsStatusError: true,
                    resultsHidden: false,
                    moreHidden: false
                }
            });
            const searchProjection = {
                metaHidden: refs.meta.hidden,
                contentHidden: refs.content.hidden,
                resultsStatusText: refs.resultsStatus.textContent,
                resultsStatusHidden: refs.resultsStatus.hidden,
                resultsStatusError: refs.resultsStatus.classList.contains('is-error'),
                resultsHidden: refs.results.hidden,
                moreHidden: refs.more.hidden,
                moreHtml: refs.more.innerHTML
            };
            module.renderDocsViewerAppShellDocumentState({
                refs,
                projection: {
                    contentHidden: false,
                    resultsStatusText: '',
                    resultsStatusHidden: true,
                    resultsStatusError: false,
                    resultsHidden: true,
                    moreHidden: true,
                    clearMore: true
                }
            });
            const documentProjection = {
                contentHidden: refs.content.hidden,
                resultsStatusText: refs.resultsStatus.textContent,
                resultsStatusHidden: refs.resultsStatus.hidden,
                resultsStatusError: refs.resultsStatus.classList.contains('is-error'),
                resultsHidden: refs.results.hidden,
                moreHidden: refs.more.hidden,
                moreHtml: refs.more.innerHTML
            };
            return { searchProjection, documentProjection };
        }"""
    )
    if result["searchProjection"] != {
        "metaHidden": True,
        "contentHidden": True,
        "resultsStatusText": "Searching...",
        "resultsStatusHidden": False,
        "resultsStatusError": True,
        "resultsHidden": False,
        "moreHidden": False,
        "moreHtml": "<button>More</button>",
    }:
        raise AssertionError(f"search document projection failed: {result!r}")
    if result["documentProjection"] != {
        "contentHidden": False,
        "resultsStatusText": "",
        "resultsStatusHidden": True,
        "resultsStatusError": False,
        "resultsHidden": True,
        "moreHidden": True,
        "moreHtml": "",
    }:
        raise AssertionError(f"document projection failed: {result!r}")


def assert_render_is_idempotent(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="true" data-allow-scope-query="true">
                  <div
                    id="docsViewerHeaderControlsMount"
                    data-docs-viewer-header-controls-mount
                    data-enable-search="true"
                  ></div>
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await module.initDocsViewerAppShell({ root, document });
            await module.initDocsViewerAppShell({ root, document });
            return {
                headerRowCount: document.querySelectorAll('.docsViewer__searchRow').length,
                scopeSelectCount: document.querySelectorAll('#docsViewerScopeSelect').length,
                recentButtonCount: document.querySelectorAll('#docsViewerRecentButton').length,
                searchInputCount: document.querySelectorAll('#docsViewerSearchInput').length,
                rowCount: document.querySelectorAll('#docsViewerManageRow').length,
                actionButtonCount: document.querySelectorAll('#docsViewerManageActionsButton').length,
                mountChildCount: document.querySelector('[data-docs-viewer-management-actions-mount]').children.length,
                sidebarCount: document.querySelectorAll('.docsViewer__sidebar').length,
                navCount: document.querySelectorAll('#docsViewerNav').length,
                toggleCount: document.querySelectorAll('#docsViewerSidebarToggle').length,
                indexMountChildCount: document.querySelector('[data-docs-viewer-index-panel-mount]').children.length,
                documentShellCount: document.querySelectorAll('.docsViewer__main').length,
                documentContentCount: document.querySelectorAll('#docsViewerContent').length,
                documentMountChildCount: document.querySelector('[data-docs-viewer-document-shell-mount]').children.length
            };
        }"""
    )
    if result != {
        "headerRowCount": 1,
        "scopeSelectCount": 1,
        "recentButtonCount": 1,
        "searchInputCount": 1,
        "rowCount": 1,
        "actionButtonCount": 1,
        "mountChildCount": 1,
        "sidebarCount": 1,
        "navCount": 1,
        "toggleCount": 1,
        "indexMountChildCount": 1,
        "documentShellCount": 1,
        "documentContentCount": 1,
        "documentMountChildCount": 1,
    }:
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

            assert_header_controls_render(page)
            assert_header_controls_search_disabled_scope_only(page)
            assert_header_controls_management_render(page)
            assert_management_actions_render(page)
            assert_management_actions_omitted(page)
            assert_index_panel_shell_render(page)
            assert_index_panel_projection(page)
            assert_document_shell_render(page)
            assert_document_shell_management_shape(page)
            assert_document_shell_projection(page)
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
