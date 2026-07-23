#!/usr/bin/env python3
"""Smoke-check manage-index selection state, projection, and action-target isolation."""

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
            const inactiveSelectAll = module.selectAllDocsViewerIndexSelection(
                inactive,
                ['non-viewable', 'collapsed-child']
            );
            const owner = module.createDocsViewerIndexSelectionOwner();
            const entered = owner.enter();
            const firstToggle = owner.toggle('b');
            const duplicateCheck = owner.toggle('b', true);
            const selectedRange = owner.selectRange('d', ['a', 'b', 'c', 'd']);
            const reconciled = owner.reconcile(['a', 'b', 'd']);
            const cleared = owner.clear();
            owner.toggle('d', true);
            const missingAnchorRange = owner.selectRange('a', ['a', 'b', 'c']);
            const selectedAll = owner.selectAll([
                'root',
                'non-viewable',
                'collapsed-child',
                'root'
            ]);
            const exited = owner.exit();
            const lifecycleOwner = module.createDocsViewerIndexSelectionOwner({ initialScopeId: 'studio' });
            const studioTreeContext = {
                scopeId: 'studio',
                managementContext: true,
                indexViewId: 'index-tree'
            };
            lifecycleOwner.syncContext(studioTreeContext);
            lifecycleOwner.enter();
            lifecycleOwner.toggle('keep');
            lifecycleOwner.toggle('prune');
            const reloaded = lifecycleOwner.reconcileReload(['keep', 'other'], studioTreeContext);
            const navigationPreserved = lifecycleOwner.snapshot();
            const viewExit = lifecycleOwner.syncContext({
                ...studioTreeContext,
                indexViewId: 'index-graph'
            });
            const treeReturn = lifecycleOwner.syncContext(studioTreeContext);
            lifecycleOwner.enter();
            lifecycleOwner.toggle('keep');
            const scopeExit = lifecycleOwner.syncContext({
                scopeId: 'other',
                managementContext: true,
                indexViewId: 'index-tree'
            });
            lifecycleOwner.enter();
            lifecycleOwner.toggle('other');
            const managementExit = lifecycleOwner.syncContext({
                scopeId: 'other',
                managementContext: false,
                indexViewId: 'index-tree'
            });
            return {
                inactive,
                inactiveSelectAll,
                entered,
                firstToggle,
                duplicateCheck,
                selectedRange,
                reconciled,
                cleared,
                missingAnchorRange,
                selectedAll,
                exited,
                reloaded,
                navigationPreserved,
                viewExit,
                treeReturn,
                scopeExit,
                managementExit,
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
        "inactiveSelectAll": {
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
        "selectedAll": {
            "selectionModeActive": True,
            "selectedDocIds": ["root", "non-viewable", "collapsed-child"],
            "rangeAnchorDocId": "",
        },
        "exited": {
            "selectionModeActive": False,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "reloaded": {
            "selectionModeActive": True,
            "selectedDocIds": ["keep"],
            "rangeAnchorDocId": "",
        },
        "navigationPreserved": {
            "selectionModeActive": True,
            "selectedDocIds": ["keep"],
            "rangeAnchorDocId": "",
        },
        "viewExit": {
            "selectionModeActive": False,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "treeReturn": {
            "selectionModeActive": False,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "scopeExit": {
            "selectionModeActive": False,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "managementExit": {
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
                    prepareActive: caseResolver('prepare-document-package').targetDocIds,
                    prepareContext: caseResolver('prepare-document-package', 'context').targetDocIds,
                    prepareDisabledReason: caseResolver('prepare-document-package').disabledReason,
                    delete: caseResolver('delete').targetDocIds,
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
            const selectionDeleteActionIds = ['delete'];
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
                prepareControlStates: {
                    empty: management.docsViewerPreparePackageActionControlState({
                        capabilities: { document_packages: { available: true, prepare: true } },
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: definitions.resolveDocsViewerAction(
                            'prepare-document-package',
                            definitions.createDocsViewerActionContext({ activeDocId: 'active' })
                        )
                    }),
                    capabilityUnavailable: management.docsViewerPreparePackageActionControlState({
                        capabilities: {},
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: resolver('prepare-document-package')
                    }),
                    busy: management.docsViewerPreparePackageActionControlState({
                        capabilities: { document_packages: { available: true, prepare: true } },
                        managementAvailable: true,
                        managementBusy: true,
                        managementChecked: true,
                        resolution: resolver('prepare-document-package')
                    }),
                    workspaceUnavailable: management.docsViewerPreparePackageActionControlState({
                        capabilities: {
                            document_packages: {
                                available: false,
                                message: 'Package workspace is offline.',
                                prepare: false
                            }
                        },
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: resolver('prepare-document-package')
                    }),
                    ready: management.docsViewerPreparePackageActionControlState({
                        capabilities: { document_packages: { available: true, prepare: true } },
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: resolver('prepare-document-package')
                    })
                },
                selectionDeleteTargets: resolveTargets(selectionDeleteActionIds),
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
        "selectionActionIds": ["delete", "prepare-document-package"],
        "prepareControlStates": {
            "empty": {
                "disabled": True,
                "disabledReason": "Select one or more documents.",
            },
            "capabilityUnavailable": {
                "disabled": True,
                "disabledReason": "Prepare package capability is unavailable.",
            },
            "busy": {
                "disabled": True,
                "disabledReason": "Docs management is busy.",
            },
            "workspaceUnavailable": {
                "disabled": True,
                "disabledReason": "Package workspace is offline.",
            },
            "ready": {"disabled": False, "disabledReason": ""},
        },
        "isolationCases": [
            {
                "selectedDocIds": [],
                "prepareActive": [],
                "prepareContext": [],
                "prepareDisabledReason": "Select one or more documents.",
                "delete": [],
                "copyActive": ["active"],
                "copyContext": ["context"],
                "moveActive": ["active"],
                "moveContext": ["context"],
            },
            {
                "selectedDocIds": ["checked-a"],
                "prepareActive": ["checked-a"],
                "prepareContext": ["checked-a"],
                "prepareDisabledReason": "",
                "delete": ["checked-a"],
                "copyActive": ["active"],
                "copyContext": ["context"],
                "moveActive": ["active"],
                "moveContext": ["context"],
            },
            {
                "selectedDocIds": ["checked-a", "checked-b"],
                "prepareActive": ["checked-a", "checked-b"],
                "prepareContext": ["checked-a", "checked-b"],
                "prepareDisabledReason": "",
                "delete": ["checked-a", "checked-b"],
                "copyActive": ["active"],
                "copyContext": ["context"],
                "moveActive": ["active"],
                "moveContext": ["context"],
            },
        ],
        "selectionDeleteTargets": {
            "delete": ["checked-a", "checked-b"],
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
        raise AssertionError(f"unexpected checked-action target contract: {result!r}")


def assert_manage_index_visibility_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const appSession = await import('/docs-viewer/runtime/js/shared/docs-viewer-app-session.js');
            const indexState = await import('/docs-viewer/runtime/js/shared/docs-viewer-document-index-state.js');
            const selection = await import('/docs-viewer/runtime/js/management/docs-viewer-index-selection.js');
            const docs = [
                { doc_id: 'root', parent_id: '', title: 'Root', viewable: true },
                { doc_id: 'non-viewable', parent_id: 'root', title: 'Non-viewable', viewable: false },
                { doc_id: 'gated-child', parent_id: 'non-viewable', title: 'Gated child', viewable: true }
            ];
            const createIndex = managementContext => {
                const session = appSession.createDocsViewerAppSession({});
                session.state.managementContext = managementContext;
                session.state.allDocs = docs.map(doc => ({ ...doc }));
                const index = indexState.createDocsViewerDocumentIndexState({ state: session.state });
                index.applyDocVisibility();
                return { session, index };
            };
            const managed = createIndex(true);
            const owner = selection.createDocsViewerIndexSelectionOwner({
                initialState: {
                    selectionModeActive: true,
                    selectedDocIds: ['non-viewable'],
                    rangeAnchorDocId: 'non-viewable'
                }
            });
            managed.session.state.allDocs.find(doc => doc.doc_id === 'non-viewable').viewable = true;
            managed.index.applyDocVisibility();
            const afterViewabilityChange = owner.snapshot();
            const publicIndex = createIndex(false);
            return {
                manageDocIds: managed.session.state.docs.map(doc => doc.doc_id),
                manageChildIds: (managed.session.state.childrenByParent.get('non-viewable') || [])
                    .map(doc => doc.doc_id),
                publicDocIds: publicIndex.session.state.docs.map(doc => doc.doc_id),
                selectedAfterViewabilityChange: afterViewabilityChange.selectedDocIds,
                anchorAfterViewabilityChange: afterViewabilityChange.rangeAnchorDocId,
                stateOwnsVisibilityToggle: Object.prototype.hasOwnProperty.call(
                    managed.session.state,
                    'showNonViewable'
                ),
                domainOwnsVisibilityToggle: managed.session.domains.documentIndex.has('showNonViewable')
            };
        }"""
    )
    expected = {
        "manageDocIds": ["gated-child", "non-viewable", "root"],
        "manageChildIds": ["gated-child"],
        "publicDocIds": ["root"],
        "selectedAfterViewabilityChange": ["non-viewable"],
        "anchorAfterViewabilityChange": "non-viewable",
        "stateOwnsVisibilityToggle": False,
        "domainOwnsVisibilityToggle": False,
    }
    if result != expected:
        raise AssertionError(f"unexpected manage/public index visibility contract: {result!r}")


def assert_prepare_action_menu_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const management = await import('/docs-viewer/runtime/js/management/docs-viewer-management.js');
            const renderers = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js');
            const render = renderers.createDocsViewerManagementAppControlRenderers()['manage-actions-menu'];
            const rendered = render({
                control: { id: 'manage-actions', label: 'Actions', state: {} },
                document,
                existingRoot: null
            });
            document.body.replaceChildren(rendered.root);
            const prepare = document.querySelector('#docsViewerManagePreparePackageButton');
            const review = document.querySelector('#docsViewerManageReviewPackageButton');
            const registered = {
                prepareTag: prepare?.tagName || '',
                prepareActionId: prepare?.dataset.docsViewerAction || '',
                prepareHref: prepare?.getAttribute('href'),
                reviewTag: review?.tagName || '',
                reviewActionId: review?.dataset.docsViewerAction || '',
                reviewHref: review?.getAttribute('href')
            };
            management.projectDocsViewerPreparePackageActionControl(prepare, {
                disabled: true,
                disabledReason: 'Select one or more documents.'
            });
            const disabled = {
                disabled: prepare.disabled,
                reason: prepare.dataset.docsViewerDisabledReason,
                ariaLabel: prepare.getAttribute('aria-label'),
                title: prepare.title
            };
            management.projectDocsViewerPreparePackageActionControl(prepare, {
                disabled: false,
                disabledReason: ''
            });
            const enabled = {
                disabled: prepare.disabled,
                hasReason: Object.prototype.hasOwnProperty.call(prepare.dataset, 'docsViewerDisabledReason'),
                ariaLabel: prepare.getAttribute('aria-label'),
                title: prepare.title
            };
            return { registered, disabled, enabled };
        }"""
    )
    expected = {
        "registered": {
            "prepareTag": "BUTTON",
            "prepareActionId": "prepare-document-package",
            "prepareHref": None,
            "reviewTag": "BUTTON",
            "reviewActionId": "review-document-package",
            "reviewHref": None,
        },
        "disabled": {
            "disabled": True,
            "reason": "Select one or more documents.",
            "ariaLabel": "Prepare package. Select one or more documents.",
            "title": "Prepare package. Select one or more documents.",
        },
        "enabled": {
            "disabled": False,
            "hasReason": False,
            "ariaLabel": "Prepare package",
            "title": "Prepare package",
        },
    }
    if result != expected:
        raise AssertionError(f"unexpected Prepare package Action menu projection: {result!r}")


def assert_selection_projection_and_interaction(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const selection = await import('/docs-viewer/runtime/js/management/docs-viewer-index-selection.js');
            const interactions = await import('/docs-viewer/runtime/js/management/docs-viewer-management-interactions.js');
            const renderers = await import('/docs-viewer/runtime/js/management/docs-viewer-management-control-renderers.js');
            const appRenderers = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js');
            const hostedViews = await import('/docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js');
            const sidebarModule = await import('/docs-viewer/runtime/js/shared/docs-viewer-sidebar.js');
            document.body.innerHTML = `
              <div class="docsViewer">
                <nav class="docsViewer__nav"></nav>
              </div>`;
            const nav = document.querySelector('.docsViewer__nav');
            const docs = ['a', 'b', 'c', 'd'].map(id => ({ doc_id: id, parent_id: '', title: id.toUpperCase() }));
            const documentIndex = {
                childrenByParent: new Map([['', docs]]),
                docs,
                docsById: new Map(docs.map(doc => [doc.doc_id, doc])),
                expandedDocIds: new Set()
            };
            const selectedDocument = { selectedDocId: 'a' };
            const owner = selection.createDocsViewerIndexSelectionOwner();
            const renderGutter = doc => selection.createDocsViewerIndexSelectionGutter({
                document,
                doc,
                state: owner.snapshot()
            });
            const sidebar = sidebarModule.initDocsViewerSidebarRenderer({
                canDragCurrentDoc: () => true,
                documentIndex,
                nav,
                pathEl: null,
                renderBookmarkToggle: () => {},
                renderIndexSelectionGutter: renderGutter,
                scopeConfig: {},
                selectedDocument,
                statusForIndexDoc: () => null,
                toolbar: null,
                updateNavDragState: () => {},
                viewerTargetDocId: docId => docId,
                viewerUrl: docId => `/docs/?doc=${docId}`
            });
            sidebar.renderSidebar();
            await new Promise(resolve => requestAnimationFrame(resolve));
            const firstItem = nav.querySelector('.docsViewer__navItem');
            const firstLink = firstItem.querySelector('.docsViewer__navLink');
            const before = firstLink.getBoundingClientRect();
            owner.enter();
            selection.projectDocsViewerIndexSelectionRows({ nav, state: owner.snapshot() });
            await new Promise(resolve => requestAnimationFrame(resolve));
            const after = firstLink.getBoundingClientRect();

            let projectionCount = 0;
            const controller = interactions.createDocsViewerManagementInteractionController({
                nav,
                documentIndex,
                indexSelection: owner,
                management: { managementAvailable: true, managementBusy: false },
                routeSession: { managementContext: true },
                searchRecent: { searchRouteActive: false },
                selectedDocument,
                context: { cssEscape: value => CSS.escape(value) },
                refs: {},
                callbacks: {
                    onIndexSelectionChange: state => {
                        projectionCount += 1;
                        selection.projectDocsViewerIndexSelectionRows({ nav, state });
                    }
                }
            });
            controller.wireEvents();
            nav.querySelector('[data-docs-viewer-selection-checkbox="b"]').dispatchEvent(
                new MouseEvent('click', { bubbles: true, cancelable: true, detail: 1 })
            );
            nav.querySelector('[data-docs-viewer-selection-checkbox="d"]').dispatchEvent(
                new MouseEvent('click', { bubbles: true, cancelable: true, detail: 1, shiftKey: true })
            );

            const controlRenderer = renderers.createDocsViewerManagementControlRenderers()['manage-index-selection'];
            const inactiveControl = controlRenderer({
                control: { state: { active: false, count: 0, disabled: false } },
                document,
                existingRoot: null
            });
            const activeControl = controlRenderer({
                control: {
                    state: {
                        active: true,
                        count: owner.selectedDocIds().length,
                        disabled: false,
                        total: docs.length
                    }
                },
                document,
                existingRoot: inactiveControl.root
            });
            const completedControl = controlRenderer({
                control: {
                    state: {
                        active: true,
                        count: docs.length,
                        disabled: false,
                        total: docs.length
                    }
                },
                document,
                existingRoot: null
            });
            const controlDefinitions = hostedViews.createDocsViewerManagementViewDefinitions().controls;
            const controlDefinition = controlDefinitions
                .find(control => control.id === 'index-selection');
            return {
                activeDocId: selectedDocument.selectedDocId,
                activeLinkStillActive: firstLink.classList.contains('is-active'),
                checkedDocIds: Array.from(nav.querySelectorAll('[data-docs-viewer-selection-checkbox]:checked'))
                    .map(checkbox => checkbox.dataset.docsViewerSelectionCheckbox),
                controlCommands: Array.from(activeControl.root.querySelectorAll('[data-docs-viewer-selection-command]'))
                    .map(button => button.dataset.docsViewerSelectionCommand),
                controlCount: activeControl.root.querySelector('output').textContent,
                selectAllDisabled: activeControl.root.querySelector(
                    '[data-docs-viewer-selection-command="select-all"]'
                ).disabled,
                completedSelectAllDisabled: completedControl.root.querySelector(
                    '[data-docs-viewer-selection-command="select-all"]'
                ).disabled,
                controlDefinition: controlDefinition && {
                    appKinds: controlDefinition.appKinds,
                    ownerViewId: controlDefinition.ownerViewId,
                    renderer: controlDefinition.renderer,
                    surfaceId: controlDefinition.surfaceId
                },
                draggablePreserved: firstLink.draggable && firstLink.dataset.dragDocId === 'a',
                gutterIsRowSibling: firstItem.children[0].classList.contains('docsViewer__indexSelectionGutter')
                    && firstItem.children[1].classList.contains('docsViewer__navRow'),
                linkGeometryStable: before.x === after.x && before.y === after.y
                    && before.width === after.width && before.height === after.height,
                projectionCount,
                removedViewabilityControls: !controlDefinitions.some(
                    control => ['manage-show', 'manage-show-non-viewable'].includes(control.id)
                ) && ['manage-show', 'manage-show-non-viewable'].every(controlId => (
                    !Object.prototype.hasOwnProperty.call(
                        appRenderers.createDocsViewerManagementAppControlRenderers(),
                        controlId
                    )
                )),
                selectedDocIds: owner.selectedDocIds(),
                visibleDocIds: selection.visibleDocsViewerIndexSelectionDocIds(nav)
            };
        }"""
    )
    expected = {
        "activeDocId": "a",
        "activeLinkStillActive": True,
        "checkedDocIds": ["b", "c", "d"],
        "controlCommands": ["select-all", "clear", "done"],
        "controlCount": "3 selected",
        "selectAllDisabled": False,
        "completedSelectAllDisabled": True,
        "controlDefinition": {
            "appKinds": ["manage"],
            "ownerViewId": "index-tree",
            "renderer": "manage-index-selection",
            "surfaceId": "index-view",
        },
        "draggablePreserved": True,
        "gutterIsRowSibling": True,
        "linkGeometryStable": True,
        "projectionCount": 2,
        "removedViewabilityControls": True,
        "selectedDocIds": ["b", "c", "d"],
        "visibleDocIds": ["a", "b", "c", "d"],
    }
    if result != expected:
        raise AssertionError(f"unexpected index selection projection contract: {result!r}")


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
            page.add_style_tag(url=f"{base_url}/site/docs-viewer/static/css/docs-viewer.css")
            page.add_style_tag(url=f"{base_url}/docs-viewer/static/css/docs-viewer-manage.css")
            assert_selection_state(page)
            assert_manage_index_visibility_contract(page)
            assert_action_target_isolation(page)
            assert_prepare_action_menu_projection(page)
            assert_selection_projection_and_interaction(page)
            browser.close()
        print("Docs Viewer index selection module contracts OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
