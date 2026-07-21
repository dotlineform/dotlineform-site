#!/usr/bin/env python3
"""Smoke-check committed local tree move projection module contracts."""

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


def assert_model_and_dom_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const stateModule = await import('/site/docs-viewer/runtime/js/shared/docs-viewer-document-index-state.js');
            const sidebarModule = await import('/site/docs-viewer/runtime/js/shared/docs-viewer-sidebar.js');
            const projectionModule = await import('/site/docs-viewer/runtime/js/shared/docs-viewer-tree-move-projection.js');

            const oldParent = { doc_id: 'old-parent', title: 'Old parent', parent_id: '' };
            const moving = { doc_id: 'moving', title: 'Middle', parent_id: 'old-parent' };
            const movingChild = { doc_id: 'moving-child', title: 'Moving child', parent_id: 'moving' };
            const target = { doc_id: 'target', title: 'Target', parent_id: '' };
            const alpha = { doc_id: 'alpha', title: 'Alpha', parent_id: 'target' };
            const zeta = { doc_id: 'zeta', title: 'Zeta', parent_id: 'target' };
            const other = { doc_id: 'other', title: 'Other', parent_id: '' };
            const otherChild = { doc_id: 'other-child', title: 'Other child', parent_id: 'other' };
            const records = [oldParent, moving, movingChild, target, alpha, zeta, other, otherChild];
            const state = {
                allDocs: records,
                allDocsById: new Map(),
                docs: [],
                docsById: new Map(),
                childrenByParent: new Map(),
                expandedDocIds: new Set(['old-parent', 'moving', 'other']),
                managementContext: true,
                manageOnlyTreeRootIds: new Set(),
                nonLoadableDocIds: new Set(),
                showNonViewable: true,
                uiStatusByValue: new Map()
            };
            const documentIndex = stateModule.createDocsViewerDocumentIndexState({ state });
            documentIndex.applyDocVisibility();

            document.body.innerHTML = '<nav id="nav"></nav><div id="path"></div>';
            const nav = document.getElementById('nav');
            const sidebar = sidebarModule.initDocsViewerSidebarRenderer({
                canDragCurrentDoc: () => true,
                cssEscape: (value) => CSS.escape(String(value || '')),
                documentIndex: state,
                nav,
                pathEl: document.getElementById('path'),
                renderBookmarkToggle: () => {},
                selectedDocument: { selectedDocId: 'moving-child' },
                statusForIndexDoc: () => null,
                toolbar: null,
                updateNavDragState: () => {},
                viewerTargetDocId: (docId) => docId,
                viewerUrl: (docId) => '/docs/?doc=' + docId
            });
            sidebar.renderSidebar();

            const movedItemBefore = nav.querySelector('[data-doc-row-id="moving"]').closest('li');
            const movedChildBefore = nav.querySelector('[data-doc-row-id="moving-child"]');
            const otherItemBefore = nav.querySelector('[data-doc-row-id="other"]').closest('li');
            const targetItemBefore = nav.querySelector('[data-doc-row-id="target"]').closest('li');

            const metaDocIds = [];
            let infoUpdateCount = 0;
            const projectionOwner = projectionModule.createDocsViewerTreeMoveProjection({
                documentIndex,
                documentIndexState: state,
                renderMeta: (doc) => metaDocIds.push(doc.doc_id),
                selectedDocument: { selectedDocId: 'moving-child' },
                sidebar,
                updateInfoPanel: () => { infoUpdateCount += 1; }
            });
            const projection = projectionOwner.project({ doc_id: 'moving', parent_id: 'target' });
            const movedItemAfter = nav.querySelector('[data-doc-row-id="moving"]').closest('li');
            const targetList = targetItemBefore.querySelector(':scope > .docsViewer__navList--child');
            const targetOrder = Array.from(targetList.children).map((item) => {
                return item.querySelector(':scope > [data-doc-row-id]').dataset.docRowId;
            });
            const oldParentItem = nav.querySelector('[data-doc-row-id="old-parent"]').closest('li');
            const targetToggle = targetItemBefore.querySelector(':scope > .docsViewer__navRow > [data-toggle-doc-id="target"]');

            const staleState = {
                allDocsById: new Map([['stale', { doc_id: 'stale', title: 'Stale', parent_id: '' }]]),
                docsById: new Map([['stale', { doc_id: 'stale', title: 'Stale', parent_id: '' }]]),
                childrenByParent: new Map()
            };
            let reconciliationError = '';
            try {
                projectionModule.projectCommittedTreeMoveModel(staleState, { doc_id: 'stale', parent_id: '' });
            } catch (error) {
                reconciliationError = error.message;
            }

            return {
                affectsMovedChild: projectionModule.treeMoveAffectsDoc(state.docsById, 'moving', 'moving-child'),
                movedParentId: state.docsById.get('moving').parent_id,
                oldChildren: (state.childrenByParent.get('old-parent') || []).map((doc) => doc.doc_id),
                targetChildren: (state.childrenByParent.get('target') || []).map((doc) => doc.doc_id),
                targetOrder,
                movedIdentityPreserved: movedItemAfter === movedItemBefore,
                movedChildIdentityPreserved: nav.querySelector('[data-doc-row-id="moving-child"]') === movedChildBefore,
                otherIdentityPreserved: nav.querySelector('[data-doc-row-id="other"]').closest('li') === otherItemBefore,
                targetIdentityPreserved: nav.querySelector('[data-doc-row-id="target"]').closest('li') === targetItemBefore,
                oldParentHasChildrenList: Boolean(oldParentItem.querySelector(':scope > .docsViewer__navList--child')),
                oldParentHasSpacer: Boolean(oldParentItem.querySelector(':scope > .docsViewer__navRow > .docsViewer__toggleSpacer')),
                targetExpanded: targetToggle && targetToggle.getAttribute('aria-expanded'),
                unrelatedExpanded: state.expandedDocIds.has('other'),
                metaDocIds,
                infoUpdateCount,
                reconciliationError
            };
        }"""
    )

    expected_order = ["alpha", "moving", "zeta"]
    if result["movedParentId"] != "target" or result["targetChildren"] != expected_order:
        raise AssertionError(f"model did not project the committed parent and ordering: {result!r}")
    if result["oldChildren"]:
        raise AssertionError(f"old parent child collection was not cleared: {result!r}")
    if result["targetOrder"] != expected_order:
        raise AssertionError(f"mounted destination order does not match the model: {result!r}")
    for key in (
        "affectsMovedChild",
        "movedIdentityPreserved",
        "movedChildIdentityPreserved",
        "otherIdentityPreserved",
        "targetIdentityPreserved",
        "oldParentHasSpacer",
        "unrelatedExpanded",
    ):
        if not result[key]:
            raise AssertionError(f"local move projection did not preserve {key}: {result!r}")
    if result["oldParentHasChildrenList"] or result["targetExpanded"] != "true":
        raise AssertionError(f"affected parent chrome was not projected: {result!r}")
    if result["metaDocIds"] != ["moving-child"] or result["infoUpdateCount"] != 1:
        raise AssertionError(f"displayed descendant ancestry was not re-projected: {result!r}")
    if "exactly one current child collection" not in result["reconciliationError"]:
        raise AssertionError(f"stale model did not fail reconciliation explicitly: {result!r}")


def assert_action_workflow_projection_and_recovery(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const actionsModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions.js');

            function response(payload) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve(payload)
                });
            }

            function controllerFixture(projectCommittedMove, reloadDocsIndex) {
                const moving = { doc_id: 'moving', title: 'Moving', parent_id: 'old-parent' };
                const selectedDocument = {
                    selectedDocId: 'displayed',
                    payloadCache: new Map([['moving', { doc_id: 'moving' }], ['displayed', { doc_id: 'displayed' }]])
                };
                const searchRecent = {
                    searchEntries: [{ id: 'moving' }],
                    searchLoaded: true,
                    searchRequestPromise: Promise.resolve(),
                    recentEntries: [{ doc_id: 'moving' }],
                    recentLoaded: true,
                    recentRequestPromise: Promise.resolve()
                };
                const messages = [];
                const requests = [];
                const controller = actionsModule.createDocsViewerManagementActionController({
                    root: document.body,
                    documentIndex: {
                        allDocs: [moving],
                        docsById: new Map([['moving', moving], ['target', { doc_id: 'target', title: 'Target', parent_id: '' }]])
                    },
                    management: {},
                    selectedDocument,
                    searchRecent,
                    context: {
                        findAllDocById: () => null,
                        formatText: (value) => value
                    },
                    refs: {},
                    resolveAction: () => ({ enabled: true, targetDocIds: ['moving'] }),
                    callbacks: {
                        clearDragState: () => {},
                        managementClientOptions: () => ({
                            baseUrl: 'http://management.test',
                            scope: 'studio',
                            fetch: (url, options) => {
                                requests.push({ url, body: JSON.parse(options.body) });
                                return response({
                                    ok: true,
                                    scope: 'studio',
                                    doc_id: 'moving',
                                    record: { doc_id: 'moving', parent_id: 'target' },
                                    changed_doc_ids: ['moving']
                                });
                            }
                        }),
                        projectCommittedMove,
                        reloadDocsIndex,
                        renderManagementUi: () => {},
                        setManagementBusy: () => {},
                        setManagementMessage: (message, isError) => messages.push({ message, isError })
                    }
                });
                return { controller, messages, requests, searchRecent, selectedDocument };
            }

            const normalProjected = [];
            const normalReloads = [];
            const normal = controllerFixture(
                (record) => normalProjected.push(record),
                (docId) => { normalReloads.push(docId); return Promise.resolve(); }
            );
            await normal.controller.handleMoveDoc('moving', 'target');

            const recoveryReloads = [];
            const recovery = controllerFixture(
                () => { throw new Error('stale model'); },
                (docId) => { recoveryReloads.push(docId); return Promise.resolve(); }
            );
            await recovery.controller.handleMoveDoc('moving', 'target');

            return {
                normalProjected,
                normalReloads,
                normalRequests: normal.requests,
                selectedDocId: normal.selectedDocument.selectedDocId,
                movingCached: normal.selectedDocument.payloadCache.has('moving'),
                displayedCached: normal.selectedDocument.payloadCache.has('displayed'),
                searchLoaded: normal.searchRecent.searchLoaded,
                recentLoaded: normal.searchRecent.recentLoaded,
                searchEntryCount: normal.searchRecent.searchEntries.length,
                recentEntryCount: normal.searchRecent.recentEntries.length,
                recoveryReloads,
                recoveryLastMessage: recovery.messages[recovery.messages.length - 1]
            };
        }"""
    )

    if result["normalProjected"] != [{"doc_id": "moving", "parent_id": "target"}]:
        raise AssertionError(f"normal workflow did not project the committed record: {result!r}")
    if result["normalReloads"]:
        raise AssertionError(f"normal successful move performed an index reload: {result!r}")
    if result["normalRequests"] != [
        {
            "url": "http://management.test/docs/move",
            "body": {"scope": "studio", "doc_id": "moving", "parent_id": "target"},
        }
    ]:
        raise AssertionError(f"normal workflow made unexpected requests: {result!r}")
    if result["selectedDocId"] != "displayed":
        raise AssertionError(f"normal move changed the displayed document: {result!r}")
    if result["movingCached"] or not result["displayedCached"]:
        raise AssertionError(f"document cache invalidation was not targeted: {result!r}")
    if result["searchLoaded"] or result["recentLoaded"] or result["searchEntryCount"] or result["recentEntryCount"]:
        raise AssertionError(f"search/recent caches were not invalidated: {result!r}")
    if result["recoveryReloads"] != ["displayed"]:
        raise AssertionError(f"projection failure did not perform one selected-doc recovery reload: {result!r}")
    recovery_message = result["recoveryLastMessage"]
    if not recovery_message["isError"] or "reloaded after a local update failed" not in recovery_message["message"]:
        raise AssertionError(f"projection recovery was not visible: {result!r}")


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
            assert_model_and_dom_projection(page)
            assert_action_workflow_projection_and_recovery(page)
            browser.close()
        print("Docs Viewer local tree move projection modules OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
