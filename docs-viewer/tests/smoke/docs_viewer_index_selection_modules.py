#!/usr/bin/env python3
"""Smoke-check manage-index selection state and action-target isolation."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class RuntimeStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        if path.startswith("/docs-viewer/runtime/js/shared/"):
            path = "/site" + path
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(RuntimeStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_selection_state(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-index-selection.js');
            const inactive = module.createDocsViewerIndexSelectionState({
                selectionModeActive: false,
                selectedDocIds: ['stale'],
                rangeAnchorDocId: 'stale'
            });
            const owner = module.createDocsViewerIndexSelectionOwner();
            const entered = owner.enter();
            const firstToggle = owner.toggle('b');
            const duplicateCheck = owner.toggle('b', true);
            const selectedRange = owner.selectRange('d', ['a', 'b', 'c', 'd']);
            const reconciled = owner.reconcile(['a', 'b', 'd']);
            const cleared = owner.clear();
            owner.toggle('d', true);
            const missingAnchorRange = owner.selectRange('a', ['a', 'b', 'c']);
            const exited = owner.exit();
            return {
                inactive,
                entered,
                firstToggle,
                duplicateCheck,
                selectedRange,
                reconciled,
                cleared,
                missingAnchorRange,
                exited,
                frozen: Object.isFrozen(firstToggle) && Object.isFrozen(firstToggle.selectedDocIds),
                selectedCopyIsIndependent: owner.selectedDocIds() !== owner.snapshot().selectedDocIds
            };
        }"""
    )
    expected = {
        "inactive": {
            "selectionModeActive": False,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "entered": {
            "selectionModeActive": True,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "firstToggle": {
            "selectionModeActive": True,
            "selectedDocIds": ["b"],
            "rangeAnchorDocId": "b",
        },
        "duplicateCheck": {
            "selectionModeActive": True,
            "selectedDocIds": ["b"],
            "rangeAnchorDocId": "b",
        },
        "selectedRange": {
            "selectionModeActive": True,
            "selectedDocIds": ["b", "c", "d"],
            "rangeAnchorDocId": "b",
        },
        "reconciled": {
            "selectionModeActive": True,
            "selectedDocIds": ["b", "d"],
            "rangeAnchorDocId": "b",
        },
        "cleared": {
            "selectionModeActive": True,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "missingAnchorRange": {
            "selectionModeActive": True,
            "selectedDocIds": ["d", "a"],
            "rangeAnchorDocId": "a",
        },
        "exited": {
            "selectionModeActive": False,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "frozen": True,
        "selectedCopyIsIndependent": True,
    }
    if result != expected:
        raise AssertionError(f"unexpected index selection state contract: {result!r}")


def assert_action_target_isolation(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const definitions = await import('/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js');
            const management = await import('/docs-viewer/runtime/js/management/docs-viewer-management.js');
            const selection = await import('/docs-viewer/runtime/js/management/docs-viewer-index-selection.js');
            const owner = selection.createDocsViewerIndexSelectionOwner({
                initialState: {
                    selectionModeActive: true,
                    selectedDocIds: ['checked-a', 'checked-b', 'checked-a'],
                    rangeAnchorDocId: 'checked-a'
                }
            });
            const selectedDocument = { selectedDocId: 'active' };
            const resolver = management.createDocsViewerManagementActionResolver({
                indexSelection: owner,
                selectedDocument
            });
            const actionContext = management.createDocsViewerManagementActionContext({
                indexSelection: owner,
                selectedDocument,
                invocationDocId: 'context'
            });
            const isolationCases = [[], ['checked-a'], ['checked-a', 'checked-b']].map(selectedDocIds => {
                const caseOwner = selection.createDocsViewerIndexSelectionOwner({
                    initialState: { selectionModeActive: true, selectedDocIds }
                });
                const caseResolver = management.createDocsViewerManagementActionResolver({
                    indexSelection: caseOwner,
                    selectedDocument
                });
                return {
                    selectedDocIds,
                    delete: caseResolver('delete').targetDocIds,
                    show: caseResolver('show').targetDocIds,
                    copyActive: caseResolver('copy-link').targetDocIds,
                    copyContext: caseResolver('copy-link', 'context').targetDocIds,
                    moveActive: caseResolver('move').targetDocIds,
                    moveContext: caseResolver('move', 'context').targetDocIds
                };
            });
            const ids = definitions.listDocsViewerActionDefinitions();
            const selectionActionIds = ids
                .filter(definition => definition.target === definitions.DOCS_VIEWER_ACTION_TARGETS.SELECTION)
                .map(definition => definition.id)
                .sort();
            const activeActionIds = ['delete', 'show'];
            const documentActionIds = ['copy-link', 'move', 'new-child', 'new-sibling', 'open', 'open-vscode'];
            const resolveTargets = (actionIds, invocation) => Object.fromEntries(actionIds.map(actionId => {
                const resolution = invocation
                    ? resolver(actionId, invocation)
                    : resolver(actionId);
                return [actionId, resolution.targetDocIds];
            }));
            return {
                actionContext,
                isolationCases,
                selectionActionIds,
                activeTargets: resolveTargets(activeActionIds),
                documentActiveTargets: resolveTargets(documentActionIds),
                documentInvocationTargets: resolveTargets(documentActionIds, 'context')
            };
        }"""
    )
    expected = {
        "actionContext": {
            "activeDocId": "active",
            "invocationDocId": "context",
            "primaryDocId": "context",
            "selectedDocIds": ["checked-a", "checked-b"],
        },
        "selectionActionIds": [],
        "isolationCases": [
            {
                "selectedDocIds": [],
                "delete": ["active"],
                "show": ["active"],
                "copyActive": ["active"],
                "copyContext": ["context"],
                "moveActive": ["active"],
                "moveContext": ["context"],
            },
            {
                "selectedDocIds": ["checked-a"],
                "delete": ["active"],
                "show": ["active"],
                "copyActive": ["active"],
                "copyContext": ["context"],
                "moveActive": ["active"],
                "moveContext": ["context"],
            },
            {
                "selectedDocIds": ["checked-a", "checked-b"],
                "delete": ["active"],
                "show": ["active"],
                "copyActive": ["active"],
                "copyContext": ["context"],
                "moveActive": ["active"],
                "moveContext": ["context"],
            },
        ],
        "activeTargets": {
            "delete": ["active"],
            "show": ["active"],
        },
        "documentActiveTargets": {
            "copy-link": ["active"],
            "move": ["active"],
            "new-child": ["active"],
            "new-sibling": ["active"],
            "open": ["active"],
            "open-vscode": ["active"],
        },
        "documentInvocationTargets": {
            "copy-link": ["context"],
            "move": ["context"],
            "new-child": ["context"],
            "new-sibling": ["context"],
            "open": ["context"],
            "open-vscode": ["context"],
        },
    }
    if result != expected:
        raise AssertionError(f"checked ids changed current action targets: {result!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_static_server(args.site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded", timeout=args.timeout_ms)
            assert_selection_state(page)
            assert_action_target_isolation(page)
            browser.close()
        print("Docs Viewer index selection module contracts OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
