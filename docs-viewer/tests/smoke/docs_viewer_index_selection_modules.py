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
            const indexManagement = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-index-controller.js'
            );
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
                    copyActive: caseResolver('copy').targetDocIds,
                    copyContext: caseResolver('copy', 'context').targetDocIds,
                    moveActive: caseResolver('move').targetDocIds,
                    moveContext: caseResolver('move', 'context').targetDocIds
                };
            });
            const ids = definitions.listDocsViewerActionDefinitions();
            const selectionActionIds = ids
                .filter(definition => definition.target === definitions.DOCS_VIEWER_ACTION_TARGETS.SELECTION)
                .map(definition => definition.id)
                .sort();
            const selectionDeleteActionIds = ['copy', 'delete', 'move'];
            const documentActionIds = ['copy-link', 'new-child', 'new-sibling', 'open', 'open-vscode'];
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
                    empty: indexManagement.docsViewerPreparePackageActionControlState({
                        capabilities: { document_packages: { available: true, prepare: true } },
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: definitions.resolveDocsViewerAction(
                            'prepare-document-package',
                            definitions.createDocsViewerActionContext({ activeDocId: 'active' })
                        )
                    }),
                    capabilityUnavailable: indexManagement.docsViewerPreparePackageActionControlState({
                        capabilities: {},
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: resolver('prepare-document-package')
                    }),
                    busy: indexManagement.docsViewerPreparePackageActionControlState({
                        capabilities: { document_packages: { available: true, prepare: true } },
                        managementAvailable: true,
                        managementBusy: true,
                        managementChecked: true,
                        resolution: resolver('prepare-document-package')
                    }),
                    workspaceUnavailable: indexManagement.docsViewerPreparePackageActionControlState({
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
                    ready: indexManagement.docsViewerPreparePackageActionControlState({
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
        "selectionActionIds": ["copy", "delete", "move", "prepare-document-package"],
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
                "copyActive": [],
                "copyContext": [],
                "moveActive": [],
                "moveContext": [],
            },
            {
                "selectedDocIds": ["checked-a"],
                "prepareActive": ["checked-a"],
                "prepareContext": ["checked-a"],
                "prepareDisabledReason": "",
                "delete": ["checked-a"],
                "copyActive": ["checked-a"],
                "copyContext": ["checked-a"],
                "moveActive": ["checked-a"],
                "moveContext": ["checked-a"],
            },
            {
                "selectedDocIds": ["checked-a", "checked-b"],
                "prepareActive": ["checked-a", "checked-b"],
                "prepareContext": ["checked-a", "checked-b"],
                "prepareDisabledReason": "",
                "delete": ["checked-a", "checked-b"],
                "copyActive": ["checked-a", "checked-b"],
                "copyContext": ["checked-a", "checked-b"],
                "moveActive": ["checked-a", "checked-b"],
                "moveContext": ["checked-a", "checked-b"],
            },
        ],
        "selectionDeleteTargets": {
            "copy": ["checked-a", "checked-b"],
            "delete": ["checked-a", "checked-b"],
            "move": ["checked-a", "checked-b"],
        },
        "documentActiveTargets": {
            "copy-link": ["active"],
            "new-child": ["active"],
            "new-sibling": ["active"],
            "open": ["active"],
            "open-vscode": ["active"],
        },
        "documentInvocationTargets": {
            "copy-link": ["context"],
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


def assert_index_actions_menu_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const appRenderers = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js');
            const controlRenderers = await import('/docs-viewer/runtime/js/management/docs-viewer-management-control-renderers.js');
            const hostedViews = await import('/docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js');
            const appRender = appRenderers.createDocsViewerManagementAppControlRenderers()['manage-actions-menu'];
            const app = appRender({
                control: { id: 'manage-actions', label: 'Actions', state: {} },
                document,
                existingRoot: null
            });
            const render = controlRenderers.createDocsViewerManagementControlRenderers()['manage-index-actions'];
            const itemStates = Object.fromEntries(
                ['prepare-document-package', 'copy', 'move', 'delete'].map(actionId => [
                    actionId,
                    { disabled: true, disabledReason: 'Select one or more documents.' }
                ])
            );
            const rendered = render({
                control: { id: 'index-actions', label: 'Index actions', state: { items: itemStates } },
                document,
                existingRoot: null
            });
            document.body.replaceChildren(app.root, rendered.root);
            const button = rendered.root.querySelector('#docsViewerIndexActionsButton');
            const menu = rendered.root.querySelector('#docsViewerIndexActionsMenu');
            const disabledItems = Array.from(
                menu.querySelectorAll('[data-docs-viewer-action]')
            ).map(item => ({
                actionId: item.dataset.docsViewerAction,
                label: item.querySelector('.docsViewer__actionMenuLabel')?.textContent || '',
                disabled: item.disabled,
                reason: item.dataset.docsViewerDisabledReason,
                ariaLabel: item.getAttribute('aria-label')
            }));
            menu.hidden = false;
            const rerendered = render({
                control: {
                    id: 'index-actions',
                    label: 'Index actions',
                    state: {
                        disabled: false,
                        items: Object.fromEntries(
                            ['prepare-document-package', 'copy', 'move', 'delete'].map(
                                actionId => [actionId, { disabled: false, disabledReason: '' }]
                            )
                        )
                    }
                },
                document,
                existingRoot: rendered.root
            });
            const definition = hostedViews.createDocsViewerManagementViewDefinitions().controls
                .find(control => control.id === 'index-actions');
            return {
                appMenu: {
                    hasPrepare: Boolean(app.root.querySelector('#docsViewerManagePreparePackageButton')),
                    hasDelete: Boolean(app.root.querySelector('#docsViewerManageDeleteButton')),
                    reviewActionId: app.root.querySelector('#docsViewerManageReviewPackageButton')
                        ?.dataset.docsViewerAction || ''
                },
                button: {
                    text: button.textContent,
                    ariaLabel: button.getAttribute('aria-label'),
                    disabled: button.disabled,
                    hasVisibleCount: /\\d/.test(button.textContent)
                },
                disabledItems,
                definition: {
                    ownerViewId: definition?.ownerViewId || '',
                    renderer: definition?.renderer || '',
                    surfaceId: definition?.surfaceId || ''
                },
                rerender: {
                    sameRoot: rerendered.root === rendered.root,
                    menuStayedOpen: !menu.hidden,
                    enabledItems: Array.from(menu.querySelectorAll('[data-docs-viewer-action]'))
                        .every(item => !item.disabled),
                    buttonStillEnabled: !button.disabled
                }
            };
        }"""
    )
    expected = {
        "appMenu": {
            "hasPrepare": False,
            "hasDelete": False,
            "reviewActionId": "review-document-package",
        },
        "button": {
            "text": "🛠️",
            "ariaLabel": "Index actions",
            "disabled": False,
            "hasVisibleCount": False,
        },
        "disabledItems": [
            {
                "actionId": "prepare-document-package",
                "label": "Prepare package…",
                "disabled": True,
                "reason": "Select one or more documents.",
                "ariaLabel": "Prepare package… Select one or more documents.",
            },
            {
                "actionId": "copy",
                "label": "Copy to scope…",
                "disabled": True,
                "reason": "Select one or more documents.",
                "ariaLabel": "Copy to scope… Select one or more documents.",
            },
            {
                "actionId": "move",
                "label": "Move to scope…",
                "disabled": True,
                "reason": "Select one or more documents.",
                "ariaLabel": "Move to scope… Select one or more documents.",
            },
            {
                "actionId": "delete",
                "label": "Delete…",
                "disabled": True,
                "reason": "Select one or more documents.",
                "ariaLabel": "Delete… Select one or more documents.",
            },
        ],
        "definition": {
            "ownerViewId": "index-tree",
            "renderer": "manage-index-actions",
            "surfaceId": "index-view",
        },
        "rerender": {
            "sameRoot": True,
            "menuStayedOpen": True,
            "enabledItems": True,
            "buttonStillEnabled": True,
        },
    }
    if result != expected:
        raise AssertionError(f"unexpected Index actions menu projection: {result!r}")


def assert_index_actions_selection_entry(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const controllerModule = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-index-controller.js'
            );
            document.body.innerHTML = `
              <button id="docsViewerIndexActionsButton" type="button"></button>
              <div id="docsViewerIndexActionsMenu" hidden></div>`;
            const docs = [
                { doc_id: 'a', parent_id: '', title: 'A' },
                { doc_id: 'b', parent_id: '', title: 'B' }
            ];
            let selectionState = null;
            let sidebarRenderCount = 0;
            const controller = controllerModule.createDocsViewerManagementIndexController({
                document,
                documentIndex: {
                    docs,
                    docsById: new Map(docs.map(doc => [doc.doc_id, doc]))
                },
                management: {
                    managementAvailable: true,
                    managementBusy: false,
                    managementCapabilities: {},
                    managementChecked: true
                },
                routeSession: { managementContext: true },
                searchRecent: { searchRouteActive: false },
                callbacks: {
                    activeDocId: () => 'b',
                    activeIndexViewId: () => 'index-tree',
                    projectIndexViewControlState: (controlId, state) => {
                        if (controlId === 'index-selection') selectionState = { ...state };
                    },
                    renderSidebar: () => { sidebarRenderCount += 1; },
                    resolveAction: actionId => ({
                        actionId,
                        disabledReason: 'Select one or more documents.',
                        enabled: false,
                        targetDocIds: []
                    }),
                    toggleIndexActionsMenu: () => {
                        const menu = document.querySelector('#docsViewerIndexActionsMenu');
                        menu.hidden = !menu.hidden;
                    },
                    viewerScope: () => 'studio'
                }
            });
            const handledOpen = controller.handleControl({
                actionId: '',
                controlId: 'index-actions',
                eventType: 'click'
            });
            const afterOpen = {
                menuOpen: !document.querySelector('#docsViewerIndexActionsMenu').hidden,
                selectedDocIds: controller.indexSelection.selectedDocIds(),
                selectionModeActive: controller.indexSelection.snapshot().selectionModeActive,
                selectionState,
                sidebarRenderCount
            };
            const handledClose = controller.handleControl({
                actionId: '',
                controlId: 'index-actions',
                eventType: 'click'
            });
            return {
                afterOpen,
                afterClose: {
                    menuOpen: !document.querySelector('#docsViewerIndexActionsMenu').hidden,
                    selectedDocIds: controller.indexSelection.selectedDocIds(),
                    sidebarRenderCount
                },
                handledClose,
                handledOpen
            };
        }"""
    )
    expected = {
        "afterOpen": {
            "menuOpen": True,
            "selectedDocIds": ["b"],
            "selectionModeActive": True,
            "selectionState": {
                "active": True,
                "allSelected": False,
                "disabled": False,
                "hasSelection": True,
                "hidden": False,
                "label": "Done selecting documents",
                "total": 2,
            },
            "sidebarRenderCount": 1,
        },
        "afterClose": {
            "menuOpen": False,
            "selectedDocIds": ["b"],
            "sidebarRenderCount": 1,
        },
        "handledClose": True,
        "handledOpen": True,
    }
    if result != expected:
        raise AssertionError(f"unexpected Index actions selection entry: {result!r}")


def assert_selection_projection_and_interaction(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const selection = await import('/docs-viewer/runtime/js/management/docs-viewer-index-selection.js');
            const interactions = await import('/docs-viewer/runtime/js/management/docs-viewer-management-interactions.js');
            const renderers = await import('/docs-viewer/runtime/js/management/docs-viewer-management-control-renderers.js');
            const appRenderers = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js');
            const hostedViews = await import('/docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js');
            const viewRegistry = await import('/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js');
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
                control: {
                    state: {
                        active: false,
                        allSelected: false,
                        disabled: false,
                        hasSelection: false,
                        total: docs.length
                    }
                },
                document,
                existingRoot: null
            });
            const activeControl = controlRenderer({
                control: {
                    state: {
                        active: true,
                        allSelected: false,
                        disabled: false,
                        hasSelection: true,
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
                        allSelected: true,
                        disabled: false,
                        hasSelection: true,
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
                hasSelectButton: Boolean(
                    activeControl.root.querySelector('[data-docs-viewer-selection-command="enter"]')
                ),
                hasSelectedCount: Boolean(
                    activeControl.root.querySelector('.docsViewer__indexSelectionCount')
                ),
                selectAllDisabled: activeControl.root.querySelector(
                    '[data-docs-viewer-selection-command="select-all"]'
                ).disabled,
                completedSelectAllDisabled: completedControl.root.querySelector(
                    '[data-docs-viewer-selection-command="select-all"]'
                ).disabled,
                normalizedSelectionState: viewRegistry.normalizeDocsViewerControlState({
                    active: true,
                    allSelected: true,
                    hasSelection: true,
                    total: docs.length
                }),
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
        "hasSelectButton": False,
        "hasSelectedCount": False,
        "selectAllDisabled": False,
        "completedSelectAllDisabled": True,
        "normalizedSelectionState": {
            "active": True,
            "allSelected": True,
            "hasSelection": True,
            "total": 4,
        },
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
            assert_index_actions_menu_projection(page)
            assert_index_actions_selection_entry(page)
            assert_selection_projection_and_interaction(page)
            browser.close()
        print("Docs Viewer index selection module contracts OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
