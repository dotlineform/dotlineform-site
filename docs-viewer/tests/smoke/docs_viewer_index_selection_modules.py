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
                ['non-publishable', 'collapsed-child']
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
                'non-publishable',
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
            "selectedDocIds": ["root", "non-publishable", "collapsed-child"],
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


def assert_subscope_selection_owner(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const definitions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js'
            );
            const indexSelection = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-index-selection.js'
            );
            const subscopeSelection = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-subscope-selection.js'
            );
            const prepareTargets = owner => definitions.resolveDocsViewerAction(
                'prepare-document-package',
                definitions.createDocsViewerActionContext({
                    activeDocId: 'parent-report',
                    selectedDocIds: owner.selectedDocIds()
                })
            ).targetDocIds;

            const unavailable = subscopeSelection.createDocsViewerSubscopeSelectionOwner({
                initialState: {
                    selectionModeActive: true,
                    selectedDocIds: ['unowned'],
                    rangeAnchorDocId: 'unowned'
                }
            });
            const unavailableEnter = unavailable.enter();

            const tags = subscopeSelection.createDocsViewerSubscopeSelectionOwner();
            tags.notify({
                type: 'mount',
                collection: { scope: ' Studio ', sub_scope: ' Tags ' }
            }, { managementContext: true });
            const mounted = {
                available: tags.available(),
                collection: tags.collection()
            };
            const entered = tags.enter();
            tags.toggle('b');
            const range = tags.selectRange('d', ['a', 'b', 'c', 'd']);
            const detailPreserved = tags.notify({
                type: 'state',
                state: 'detail',
                collection: { scope: 'studio', sub_scope: 'tags' }
            });
            const refreshed = tags.notify({
                type: 'refresh',
                collection: { scope: 'studio', sub_scope: 'tags' },
                documents: [
                    { doc_id: 'b' },
                    { doc_id: 'd' },
                    { doc_id: 'other' }
                ]
            });
            const selectedAll = tags.selectAll(['d', 'b', 'd']);
            const cleared = tags.clear();
            const done = tags.done();

            const index = indexSelection.createDocsViewerIndexSelectionOwner();
            index.enter();
            index.toggle('index-only');
            tags.enter();
            tags.toggle('tag-only');
            const notes = subscopeSelection.createDocsViewerSubscopeSelectionOwner();
            notes.notify({
                type: 'mount',
                collection: { scope: 'studio', sub_scope: 'notes' }
            }, { managementContext: true });
            notes.enter();
            notes.toggle('note-only');
            const isolatedTargets = {
                index: prepareTargets(index),
                notes: prepareTargets(notes),
                tags: prepareTargets(tags)
            };

            const changedCollection = tags.notify({
                type: 'mount',
                collection: { scope: 'studio', sub_scope: 'notes' }
            });
            tags.enter();
            tags.toggle('notes-after-change');
            const leftManagement = tags.syncContext({ managementContext: false });
            const unavailableAfterManagementExit = tags.enter();
            tags.syncContext({ managementContext: true });
            tags.enter();
            tags.toggle('before-unmount');
            const unmounted = tags.notify({
                type: 'unmount',
                collection: { scope: 'studio', sub_scope: 'notes' }
            });
            const unavailableAfterUnmount = tags.enter();

            return {
                unavailableEnter,
                mounted,
                entered,
                range,
                detailPreserved,
                refreshed,
                selectedAll,
                cleared,
                done,
                isolatedTargets,
                changedCollection,
                changedCollectionIdentity: tags.collection(),
                leftManagement,
                unavailableAfterManagementExit,
                unmounted,
                unavailableAfterUnmount,
                indexPreserved: index.snapshot(),
                notesPreserved: notes.snapshot(),
                frozen: Object.isFrozen(range) && Object.isFrozen(range.selectedDocIds)
            };
        }"""
    )
    inactive = {
        "selectionModeActive": False,
        "selectedDocIds": [],
        "rangeAnchorDocId": "",
    }
    expected = {
        "unavailableEnter": inactive,
        "mounted": {
            "available": True,
            "collection": {"scope": "studio", "sub_scope": "tags"},
        },
        "entered": {
            "selectionModeActive": True,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "range": {
            "selectionModeActive": True,
            "selectedDocIds": ["b", "c", "d"],
            "rangeAnchorDocId": "b",
        },
        "detailPreserved": {
            "selectionModeActive": True,
            "selectedDocIds": ["b", "c", "d"],
            "rangeAnchorDocId": "b",
        },
        "refreshed": {
            "selectionModeActive": True,
            "selectedDocIds": ["b", "d"],
            "rangeAnchorDocId": "b",
        },
        "selectedAll": {
            "selectionModeActive": True,
            "selectedDocIds": ["d", "b"],
            "rangeAnchorDocId": "",
        },
        "cleared": {
            "selectionModeActive": True,
            "selectedDocIds": [],
            "rangeAnchorDocId": "",
        },
        "done": inactive,
        "isolatedTargets": {
            "index": ["index-only"],
            "notes": ["note-only"],
            "tags": ["tag-only"],
        },
        "changedCollection": inactive,
        "changedCollectionIdentity": {"scope": "studio", "sub_scope": "notes"},
        "leftManagement": inactive,
        "unavailableAfterManagementExit": inactive,
        "unmounted": inactive,
        "unavailableAfterUnmount": inactive,
        "indexPreserved": {
            "selectionModeActive": True,
            "selectedDocIds": ["index-only"],
            "rangeAnchorDocId": "index-only",
        },
        "notesPreserved": {
            "selectionModeActive": True,
            "selectedDocIds": ["note-only"],
            "rangeAnchorDocId": "note-only",
        },
        "frozen": True,
    }
    if result != expected:
        raise AssertionError(f"unexpected sub-scope selection owner contract: {result!r}")


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
        "selectionActionIds": [
            "copy",
            "delete",
            "export-docs",
            "move",
            "prepare-document-package",
            "set-publishable",
        ],
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
                { doc_id: 'root', parent_id: '', title: 'Root', publishable: true },
                { doc_id: 'non-publishable', parent_id: 'root', title: 'Non-publishable', publishable: false },
                { doc_id: 'gated-child', parent_id: 'non-publishable', title: 'Gated child', publishable: true }
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
                    selectedDocIds: ['non-publishable'],
                    rangeAnchorDocId: 'non-publishable'
                }
            });
            managed.session.state.allDocs.find(doc => doc.doc_id === 'non-publishable').publishable = true;
            managed.index.applyDocVisibility();
            const afterPublishabilityChange = owner.snapshot();
            const publicIndex = createIndex(false);
            return {
                manageDocIds: managed.session.state.docs.map(doc => doc.doc_id),
                manageChildIds: (managed.session.state.childrenByParent.get('non-publishable') || [])
                    .map(doc => doc.doc_id),
                publicDocIds: publicIndex.session.state.docs.map(doc => doc.doc_id),
                selectedAfterPublishabilityChange: afterPublishabilityChange.selectedDocIds,
                anchorAfterPublishabilityChange: afterPublishabilityChange.rangeAnchorDocId,
                stateOwnsVisibilityToggle: Object.prototype.hasOwnProperty.call(
                    managed.session.state,
                    'showNonPublishable'
                ),
                domainOwnsVisibilityToggle: managed.session.domains.documentIndex.has('showNonPublishable')
            };
        }"""
    )
    expected = {
        "manageDocIds": ["gated-child", "non-publishable", "root"],
        "manageChildIds": ["gated-child"],
        "publicDocIds": ["root"],
        "selectedAfterPublishabilityChange": ["non-publishable"],
        "anchorAfterPublishabilityChange": "non-publishable",
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
            const actionIds = [
                'export-docs',
                'prepare-document-package',
                'set-publishable',
                'copy',
                'move',
                'delete'
            ];
            const itemStates = Object.fromEntries(
                actionIds.map(actionId => [
                    actionId,
                    {
                        disabled: true,
                        disabledReason: 'Select one or more documents.',
                        hidden: actionId === 'set-publishable'
                    }
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
                hidden: item.hidden,
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
                            actionIds.map(
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
                    hasExport: Boolean(app.root.querySelector('#docsViewerManageExportButton')),
                    hasPrepare: Boolean(app.root.querySelector('#docsViewerManagePreparePackageButton')),
                    hasDelete: Boolean(app.root.querySelector('#docsViewerManageDeleteButton')),
                    hasRetiredReviewPackage: Boolean(
                        app.root.querySelector('#docsViewerManageReviewPackageButton')
                    )
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
                    setPublishableVisible: !menu.querySelector(
                        '[data-docs-viewer-action="set-publishable"]'
                    ).hidden,
                    buttonStillEnabled: !button.disabled
                }
            };
        }"""
    )
    expected = {
        "appMenu": {
            "hasExport": False,
            "hasPrepare": False,
            "hasDelete": False,
            "hasRetiredReviewPackage": False,
        },
        "button": {
            "text": "🛠️",
            "ariaLabel": "Index actions",
            "disabled": False,
            "hasVisibleCount": False,
        },
        "disabledItems": [
            {
                "actionId": "export-docs",
                "label": "Export…",
                "disabled": True,
                "hidden": False,
                "reason": "Select one or more documents.",
                "ariaLabel": "Export… Select one or more documents.",
            },
            {
                "actionId": "prepare-document-package",
                "label": "Prepare package…",
                "disabled": True,
                "hidden": False,
                "reason": "Select one or more documents.",
                "ariaLabel": "Prepare package… Select one or more documents.",
            },
            {
                "actionId": "set-publishable",
                "label": "Set Publishable…",
                "disabled": True,
                "hidden": True,
                "reason": "Select one or more documents.",
                "ariaLabel": "Set Publishable… Select one or more documents.",
            },
            {
                "actionId": "copy",
                "label": "Copy to…",
                "disabled": True,
                "hidden": False,
                "reason": "Select one or more documents.",
                "ariaLabel": "Copy to… Select one or more documents.",
            },
            {
                "actionId": "move",
                "label": "Move to scope…",
                "disabled": True,
                "hidden": False,
                "reason": "Select one or more documents.",
                "ariaLabel": "Move to scope… Select one or more documents.",
            },
            {
                "actionId": "delete",
                "label": "Delete…",
                "disabled": True,
                "hidden": False,
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
            "setPublishableVisible": True,
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


def assert_set_publishable_workflow(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const client = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-client.js'
            );
            const controller = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-index-controller.js'
            );
            const workflow = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-publishable-workflow.js'
            );
            const capabilities = {
                publishing: { confirm: true, apply: true },
                scopes: {
                    studio: {
                        available: true,
                        publishable: true,
                        publishing: { confirm: true, apply: true }
                    },
                    local: {
                        available: true,
                        publishable: false,
                        publishing: { confirm: true, apply: true }
                    }
                }
            };
            const resolution = {
                enabled: true,
                disabledReason: '',
                targetDocIds: ['checked-a', 'checked-b']
            };
            const control = options => controller.docsViewerSetPublishableActionControlState({
                capabilities,
                managementAvailable: true,
                managementBusy: false,
                managementChecked: true,
                resolution,
                source: { scope: 'studio' },
                ...options
            });
            const modalOptions = workflow.setPublishableChoiceOptions({
                checkedDocIds: ['checked-a', 'checked-b']
            });
            const appliedCalls = [];
            const appliedEvents = [];
            const busy = [];
            const messages = [];
            let choiceOptions = null;
            const applied = await workflow.openDocsViewerSetPublishableWorkflow({
                source: { scope: 'studio', sub_scope: 'works' },
                checkedDocIds: ['checked-a', 'checked-b'],
                choose: options => {
                    choiceOptions = options;
                    return Promise.resolve({ confirmed: true, value: 'exclude' });
                },
                apply: (source, docIds, publishable) => {
                    appliedCalls.push({ source, docIds, publishable });
                    return Promise.resolve({
                        ok: true,
                        operation: 'set_publishable',
                        target: source,
                        requested_doc_ids: docIds,
                        publishable,
                        summary_text: '2 documents excluded from next Publish.'
                    });
                },
                callbacks: {
                    onApplied: payload => appliedEvents.push(payload.requested_doc_ids.slice()),
                    setBusy: value => busy.push(value),
                    setMessage: (message, isError) => messages.push({ message, isError })
                }
            });
            let cancelledApplyCount = 0;
            const cancelled = await workflow.openDocsViewerSetPublishableWorkflow({
                source: { scope: 'studio' },
                checkedDocIds: ['checked-a'],
                choose: () => Promise.resolve({ confirmed: false, value: '' }),
                apply: () => { cancelledApplyCount += 1; }
            });
            let duplicateRejected = false;
            try {
                await workflow.openDocsViewerSetPublishableWorkflow({
                    source: { scope: 'studio' },
                    checkedDocIds: ['checked-a', 'checked-a']
                });
            } catch (error) {
                duplicateRejected = /must not contain duplicates/.test(
                    String(error && error.message || '')
                );
            }
            const mismatchMessages = [];
            const mismatch = await workflow.openDocsViewerSetPublishableWorkflow({
                source: { scope: 'studio' },
                checkedDocIds: ['checked-a', 'checked-b'],
                choose: () => Promise.resolve({ confirmed: true, value: 'include' }),
                apply: () => Promise.resolve({
                    ok: true,
                    operation: 'set_publishable',
                    target: { scope: 'studio' },
                    requested_doc_ids: ['checked-b', 'checked-a'],
                    publishable: true
                }),
                callbacks: {
                    setMessage: (message, isError) => mismatchMessages.push({ message, isError })
                }
            });
            const fetchCalls = [];
            await client.setManagedDocsPublishable(
                { scope: 'studio', sub_scope: 'works' },
                ['checked-a', 'checked-b'],
                false,
                {
                    baseUrl: '/manage',
                    fetch: async (url, options) => {
                        fetchCalls.push({
                            url,
                            method: options.method,
                            payload: JSON.parse(options.body)
                        });
                        return {
                            ok: true,
                            status: 200,
                            json: async () => ({ ok: true })
                        };
                    }
                }
            );
            const summarizeModal = options => ({
                title: options.title,
                body: options.body,
                name: options.name,
                choices: options.choices,
                primaryLabel: options.primaryLabel,
                cancelLabel: options.cancelLabel,
                requiredMessage: options.requiredMessage
            });
            return {
                applied: applied && applied.requested_doc_ids,
                appliedCalls,
                appliedEvents,
                busy,
                cancelled,
                cancelledApplyCount,
                choiceOptions: summarizeModal(choiceOptions),
                controlStates: {
                    ready: control({}),
                    empty: control({
                        resolution: {
                            enabled: false,
                            disabledReason: 'Select one or more documents.'
                        }
                    }),
                    busy: control({ managementBusy: true }),
                    local: control({ source: { scope: 'local' } }),
                    unchecked: control({ managementChecked: false })
                },
                duplicateRejected,
                fetchCalls,
                messages,
                mismatch,
                mismatchMessages,
                modalOptions: summarizeModal(modalOptions)
            };
        }"""
    )
    expected_modal = {
        "title": "Set Publishable…",
        "body": "2 checked documents.",
        "name": "docsViewerSetPublishableChoice",
        "choices": [
            {"value": "include", "label": "Include in next Publish"},
            {"value": "exclude", "label": "Exclude from next Publish"},
        ],
        "primaryLabel": "OK",
        "cancelLabel": "Cancel",
        "requiredMessage": "Choose whether to include or exclude the checked documents.",
    }
    assert result == {
        "applied": ["checked-a", "checked-b"],
        "appliedCalls": [{
            "source": {"scope": "studio", "sub_scope": "works"},
            "docIds": ["checked-a", "checked-b"],
            "publishable": False,
        }],
        "appliedEvents": [["checked-a", "checked-b"]],
        "busy": [True, False],
        "cancelled": None,
        "cancelledApplyCount": 0,
        "choiceOptions": expected_modal,
        "controlStates": {
            "ready": {"hidden": False, "disabled": False, "disabledReason": ""},
            "empty": {
                "hidden": False,
                "disabled": True,
                "disabledReason": "Select one or more documents.",
            },
            "busy": {
                "hidden": False,
                "disabled": True,
                "disabledReason": "Docs management is busy.",
            },
            "local": {"hidden": True, "disabled": True, "disabledReason": ""},
            "unchecked": {"hidden": True, "disabled": True, "disabledReason": ""},
        },
        "duplicateRejected": True,
        "fetchCalls": [{
            "url": "/manage/docs/set-publishable",
            "method": "POST",
            "payload": {
                "scope": "studio",
                "sub_scope": "works",
                "doc_ids": ["checked-a", "checked-b"],
                "publishable": False,
                "confirm": True,
            },
        }],
        "messages": [
            {"message": "Updating checked documents…", "isError": False},
            {"message": "2 documents excluded from next Publish.", "isError": False},
        ],
        "mismatch": None,
        "mismatchMessages": [
            {"message": "Updating checked documents…", "isError": False},
            {
                "message": "Set Publishable response did not match the exact checked selection.",
                "isError": True,
            },
        ],
        "modalOptions": expected_modal,
    }, result


def assert_static_snapshot_export_workflow(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const actions = await import('/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js');
            const capabilities = await import('/docs-viewer/runtime/js/management/docs-viewer-management-capabilities.js');
            const client = await import('/docs-viewer/runtime/js/management/docs-viewer-management-client.js');
            const controllerModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-index-controller.js');
            const selection = await import('/docs-viewer/runtime/js/management/docs-viewer-index-selection.js');
            const workflow = await import('/docs-viewer/runtime/js/management/docs-viewer-static-html-export-workflow.js');
            const preview = {
                ok: true,
                schema_version: 'docs_static_html_snapshot_preview_v2',
                operation: 'preview',
                dry_run: true,
                scope: 'studio',
                doc_ids: ['a', 'b'],
                document_count: 2,
                media_count: 2,
                media_bytes: 1536,
                external_dependency_count: 1,
                selection_kind: 'partial',
                default_doc_id: 'a',
                export_date: '2026-07-31',
                destination_label: '/docs-export/studio selection - 2026-07-31/',
                target_state: 'absent',
                replacement_required: false,
                replace_allowed: true,
                existing_snapshot: null,
                plan_revision: 'a'.repeat(64),
                target_revision: 'b'.repeat(64)
            };
            const projectedCapability = capabilities.scopeStaticHtmlExportCapability({
                static_html_export: { preview: true, apply: true, error: '' },
                scopes: {
                    library: {
                        available: false,
                        static_html_export: { preview: true, apply: true, error: '' }
                    }
                }
            }, 'library');
            const providerNeutralControl = controllerModule.docsViewerStaticHtmlExportActionControlState({
                capabilities: {
                    static_html_export: { preview: true, apply: true, error: '' },
                    scopes: {
                        library: {
                            available: false,
                            static_html_export: { preview: true, apply: true, error: '' }
                        }
                    }
                },
                managementAvailable: false,
                managementBusy: false,
                managementChecked: true,
                resolution: {
                    enabled: true,
                    disabledReason: '',
                    targetDocIds: ['library']
                },
                scope: 'library',
                workflowActive: false
            });

            const clientRequests = [];
            const fakeFetch = async (url, request) => {
                clientRequests.push({
                    method: request.method,
                    path: new URL(url).pathname,
                    payload: JSON.parse(request.body)
                });
                return { ok: true, status: 200, json: async () => ({ ok: true }) };
            };
            const clientOptions = { baseUrl: 'http://management.test', scope: 'studio', fetch: fakeFetch };
            await client.previewManagedDocsStaticHtmlExport(['b', 'a'], clientOptions);
            await client.applyManagedDocsStaticHtmlExport(preview, clientOptions);

            const busy = [];
            const messages = [];
            let refreshCount = 0;
            let previewArgs = null;
            let applyUsedPreview = false;
            let confirmOptions = null;
            const applied = await workflow.openStaticHtmlSnapshotExportWorkflow({
                root: document.body,
                scope: 'studio',
                checkedDocIds: ['b', 'a'],
                clientOptions,
                previewSnapshot: async (docIds, options) => {
                    previewArgs = { docIds, sameOptions: options === clientOptions };
                    return preview;
                },
                confirmSnapshot: async options => {
                    confirmOptions = options;
                    return true;
                },
                applySnapshot: async (value, options) => {
                    applyUsedPreview = value === preview && options === clientOptions;
                    return { ok: true, summary_text: 'Snapshot complete.' };
                },
                callbacks: {
                    setBusy: value => busy.push(value),
                    setMessage: (message, isError) => messages.push([message, isError]),
                    onApplied: async () => { refreshCount += 1; }
                }
            });

            const recognized = {
                ...preview,
                target_state: 'recognized',
                replacement_required: true,
                existing_snapshot: {
                    scope: 'studio',
                    document_count: 1,
                    generated_at: '2026-07-31T12:00:00+01:00'
                }
            };
            const blocked = {
                ...preview,
                target_state: 'non_directory',
                replace_allowed: false
            };
            const unrecognized = {
                ...preview,
                target_state: 'unrecognized',
                replacement_required: true
            };
            let duplicateError = '';
            try {
                workflow.validateStaticHtmlSnapshotPreview(
                    { ...preview, doc_ids: ['a', 'a'] },
                    { scope: 'studio', checkedDocIds: ['a', 'b'] }
                );
            } catch (error) {
                duplicateError = String(error && error.message || '');
            }
            let mediaSummaryError = '';
            try {
                workflow.validateStaticHtmlSnapshotPreview(
                    { ...preview, media_count: -1 },
                    { scope: 'studio', checkedDocIds: ['a', 'b'] }
                );
            } catch (error) {
                mediaSummaryError = String(error && error.message || '');
            }

            document.body.innerHTML = `
              <button id="docsViewerIndexActionsButton" type="button"></button>
              <div id="docsViewerIndexActionsMenu"></div>`;
            const docs = [
                { doc_id: 'a', parent_id: '', title: 'A' },
                { doc_id: 'b', parent_id: '', title: 'B' }
            ];
            const owner = selection.createDocsViewerIndexSelectionOwner();
            owner.enter();
            owner.toggle('a', true);
            let dispatchedOptions = null;
            const controller = controllerModule.createDocsViewerManagementIndexController({
                document,
                documentIndex: { docs, docsById: new Map(docs.map(doc => [doc.doc_id, doc])) },
                indexSelection: owner,
                management: {
                    managementAvailable: true,
                    managementBusy: false,
                    managementChecked: true,
                    managementCapabilities: {
                        static_html_export: { preview: true, apply: true, error: '' },
                        scopes: {
                            studio: { static_html_export: { preview: true, apply: true, error: '' } }
                        }
                    }
                },
                routeSession: { managementContext: true },
                searchRecent: { searchRouteActive: false },
                openSnapshotExportWorkflow: options => {
                    dispatchedOptions = options;
                    return Promise.resolve({ ok: true });
                },
                callbacks: {
                    activeDocId: () => 'b',
                    activeIndexViewId: () => 'index-tree',
                    hideIndexActionsMenu: () => {},
                    managementClientOptions: () => clientOptions,
                    projectIndexViewControlState: () => {},
                    renderManagementUi: () => {},
                    resolveAction: actionId => actions.resolveDocsViewerAction(actionId, {
                        activeDocId: 'b',
                        selectedDocIds: owner.selectedDocIds()
                    }),
                    setManagementBusy: () => {},
                    setManagementMessage: () => {},
                    viewerScope: () => 'studio'
                }
            });
            const handled = controller.handleControl({
                actionId: 'export-docs',
                controlId: 'index-actions',
                eventType: 'click'
            });
            await new Promise(resolve => setTimeout(resolve, 0));

            document.body.innerHTML = `
              <div id="snapshotModalRoot">
                <button id="docsViewerIndexActionsButton" type="button"></button>
                <div id="docsViewerIndexActionsMenu"></div>
              </div>`;
            const modalRoot = document.querySelector('#snapshotModalRoot');
            const modalOwner = selection.createDocsViewerIndexSelectionOwner();
            modalOwner.enter();
            modalOwner.toggle('a', true);
            const modalManagement = {
                managementAvailable: true,
                managementBusy: false,
                managementChecked: true,
                managementCapabilities: {
                    static_html_export: { preview: true, apply: true, error: '' },
                    scopes: {
                        studio: { static_html_export: { preview: true, apply: true, error: '' } }
                    }
                }
            };
            const modalPreview = {
                ...preview,
                doc_ids: ['a'],
                document_count: 1,
                selection_kind: 'single',
                destination_label: '/docs-export/studio selection - 2026-07-31/'
            };
            const modalRequests = [];
            const modalMessages = [];
            let modalRefreshCount = 0;
            const modalFetch = async (url, request) => {
                const path = new URL(url).pathname;
                modalRequests.push({ path, payload: JSON.parse(request.body) });
                return {
                    ok: true,
                    status: 200,
                    json: async () => path.endsWith('/preview')
                        ? modalPreview
                        : { ok: true, summary_text: 'Modal snapshot complete.' }
                };
            };
            const modalController = controllerModule.createDocsViewerManagementIndexController({
                root: modalRoot,
                document,
                documentIndex: { docs, docsById: new Map(docs.map(doc => [doc.doc_id, doc])) },
                indexSelection: modalOwner,
                management: modalManagement,
                routeSession: { managementContext: true },
                searchRecent: { searchRouteActive: false },
                callbacks: {
                    activeDocId: () => 'b',
                    activeIndexViewId: () => 'index-tree',
                    hideIndexActionsMenu: () => {},
                    managementClientOptions: () => ({
                        baseUrl: 'http://management.test',
                        scope: 'studio',
                        fetch: modalFetch
                    }),
                    projectIndexViewControlState: () => {},
                    refreshManagementCapabilities: () => { modalRefreshCount += 1; },
                    renderManagementUi: () => {},
                    resolveAction: actionId => actions.resolveDocsViewerAction(actionId, {
                        activeDocId: 'b',
                        selectedDocIds: modalOwner.selectedDocIds()
                    }),
                    setManagementBusy: value => { modalManagement.managementBusy = value; },
                    setManagementMessage: (message, isError) => {
                        modalMessages.push([message, isError]);
                    },
                    viewerScope: () => 'studio'
                }
            });
            const modalHandled = modalController.handleControl({
                actionId: 'export-docs',
                controlId: 'index-actions',
                eventType: 'click'
            });
            const waitFor = async predicate => {
                for (let attempt = 0; attempt < 100; attempt += 1) {
                    if (predicate()) return;
                    await new Promise(resolve => setTimeout(resolve, 5));
                }
                throw new Error('Timed out waiting for snapshot modal flow.');
            };
            await waitFor(() => modalRoot.querySelector('[data-role="modal-primary"]'));
            const modalText = modalRoot.querySelector('.docsViewer__modalCard').innerText
                .split(/\\n+/)
                .map(value => value.trim())
                .filter(Boolean);
            const modalPrimary = modalRoot.querySelector('[data-role="modal-primary"]');
            const modalPrimaryLabel = modalPrimary.textContent;
            modalPrimary.click();
            await waitFor(() => modalMessages.some(item => item[0] === 'Modal snapshot complete.'));

            const recognizedOptions = workflow.staticHtmlSnapshotConfirmationOptions(recognized);
            const blockedOptions = workflow.staticHtmlSnapshotConfirmationOptions(blocked);
            const unrecognizedOptions = workflow.staticHtmlSnapshotConfirmationOptions(unrecognized);
            return {
                applied,
                applyUsedPreview,
                busy,
                clientRequests,
                confirmation: {
                    body: confirmOptions.body,
                    primaryDisabled: confirmOptions.primaryDisabled,
                    primaryLabel: confirmOptions.primaryLabel,
                    title: confirmOptions.title
                },
                dispatched: {
                    checkedDocIds: dispatchedOptions && dispatchedOptions.checkedDocIds,
                    handled,
                    scope: dispatchedOptions && dispatchedOptions.scope
                },
                duplicateError,
                mediaSummaryError,
                messages,
                modalFlow: {
                    handled: modalHandled,
                    messages: modalMessages,
                    modalText,
                    primaryLabel: modalPrimaryLabel,
                    refreshCount: modalRefreshCount,
                    requests: modalRequests,
                    selectedDocIds: modalOwner.selectedDocIds()
                },
                previewArgs,
                projectedCapability,
                providerNeutralControl,
                recognized: {
                    body: recognizedOptions.body,
                    initialFocus: recognizedOptions.initialFocus,
                    primaryLabel: recognizedOptions.primaryLabel,
                    primaryTone: recognizedOptions.primaryTone
                },
                blocked: {
                    body: blockedOptions.body,
                    primaryDisabled: blockedOptions.primaryDisabled,
                    primaryLabel: blockedOptions.primaryLabel
                },
                unrecognized: {
                    body: unrecognizedOptions.body,
                    primaryLabel: unrecognizedOptions.primaryLabel
                },
                refreshCount
            };
        }"""
    )
    expected = {
        "applied": {"ok": True, "summary_text": "Snapshot complete."},
        "applyUsedPreview": True,
        "busy": [True, False, True, False],
        "clientRequests": [
            {
                "method": "POST",
                "path": "/docs/export/static-html/preview",
                "payload": {"scope": "studio", "doc_ids": ["b", "a"]},
            },
            {
                "method": "POST",
                "path": "/docs/export/static-html/apply",
                "payload": {
                    "scope": "studio",
                    "doc_ids": ["a", "b"],
                    "export_date": "2026-07-31",
                    "plan_revision": "a" * 64,
                    "target_revision": "b" * 64,
                    "confirm": True,
                    "replace_existing": False,
                },
            },
        ],
        "confirmation": {
            "body": [
                "/docs-export/studio selection - 2026-07-31/",
                "Includes 2 media files (1.5 KB).",
                "Leaves 1 external media reference unchanged.",
            ],
            "primaryDisabled": False,
            "primaryLabel": "Create snapshot",
            "title": "Export 2 documents to:",
        },
        "dispatched": {"checkedDocIds": ["a"], "handled": True, "scope": "studio"},
        "duplicateError": "Snapshot preview documents no longer match the checked selection.",
        "mediaSummaryError": "Snapshot preview media summary is invalid.",
        "messages": [
            ["Preparing dated snapshot…", False],
            ["", False],
            ["Exporting dated snapshot…", False],
            ["Snapshot complete.", False],
        ],
        "modalFlow": {
            "handled": True,
            "messages": [
                ["Preparing dated snapshot…", False],
                ["", False],
                ["Exporting dated snapshot…", False],
                ["Modal snapshot complete.", False],
            ],
            "modalText": [
                "Export 1 document to:",
                "/docs-export/studio selection - 2026-07-31/",
                "Includes 2 media files (1.5 KB).",
                "Leaves 1 external media reference unchanged.",
                "Cancel",
                "Create snapshot",
            ],
            "primaryLabel": "Create snapshot",
            "refreshCount": 1,
            "requests": [
                {
                    "path": "/docs/export/static-html/preview",
                    "payload": {"scope": "studio", "doc_ids": ["a"]},
                },
                {
                    "path": "/docs/export/static-html/apply",
                    "payload": {
                        "scope": "studio",
                        "doc_ids": ["a"],
                        "export_date": "2026-07-31",
                        "plan_revision": "a" * 64,
                        "target_revision": "b" * 64,
                        "confirm": True,
                        "replace_existing": False,
                    },
                },
            ],
            "selectedDocIds": ["a"],
        },
        "previewArgs": {"docIds": ["b", "a"], "sameOptions": True},
        "projectedCapability": {"available": True, "reason": ""},
        "providerNeutralControl": {"disabled": False, "disabledReason": ""},
        "recognized": {
            "body": [
                "/docs-export/studio selection - 2026-07-31/",
                "Includes 2 media files (1.5 KB).",
                "Leaves 1 external media reference unchanged.",
            ],
            "initialFocus": "cancel",
            "primaryLabel": "Replace",
            "primaryTone": "danger",
        },
        "blocked": {
            "body": [
                "/docs-export/studio selection - 2026-07-31/",
                "Includes 2 media files (1.5 KB).",
                "Leaves 1 external media reference unchanged.",
            ],
            "primaryDisabled": True,
            "primaryLabel": "Unavailable",
        },
        "unrecognized": {
            "body": [
                "/docs-export/studio selection - 2026-07-31/",
                "Includes 2 media files (1.5 KB).",
                "Leaves 1 external media reference unchanged.",
            ],
            "primaryLabel": "Replace",
        },
        "refreshCount": 1,
    }
    if result != expected:
        raise AssertionError(f"unexpected static snapshot Export workflow: {result!r}")


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
                removedPublishabilityControls: !controlDefinitions.some(
                    control => ['manage-show', 'manage-show-non-publishable'].includes(control.id)
                ) && ['manage-show', 'manage-show-non-publishable'].every(controlId => (
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
        "removedPublishabilityControls": True,
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
            assert_subscope_selection_owner(page)
            assert_manage_index_visibility_contract(page)
            assert_action_target_isolation(page)
            assert_index_actions_menu_projection(page)
            assert_index_actions_selection_entry(page)
            assert_set_publishable_workflow(page)
            assert_static_snapshot_export_workflow(page)
            assert_selection_projection_and_interaction(page)
            browser.close()
        print("Docs Viewer index selection module contracts OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
