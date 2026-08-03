#!/usr/bin/env python3
"""Smoke-check the focused public-safe Table Detail View contracts."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_RUNTIME_PREFIX = "/docs-viewer/runtime/js/shared/"
MANAGEMENT_RUNTIME_PREFIX = "/docs-viewer/runtime/js/management/"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        clean_path = path.split("?", 1)[0].split("#", 1)[0]
        if clean_path.startswith(SHARED_RUNTIME_PREFIX):
            relative_path = clean_path.removeprefix(SHARED_RUNTIME_PREFIX)
            return str(REPO_ROOT / "site/docs-viewer/runtime/js/shared" / relative_path)
        if clean_path.startswith(MANAGEMENT_RUNTIME_PREFIX):
            relative_path = clean_path.removeprefix(MANAGEMENT_RUNTIME_PREFIX)
            return str(REPO_ROOT / "docs-viewer/runtime/js/management" / relative_path)
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_entrypoint_composition() -> None:
    public_entry = (REPO_ROOT / "site/docs-viewer/runtime/js/public/docs-viewer-public.js").read_text(encoding="utf-8")
    manage_entry = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js").read_text(encoding="utf-8")

    required = (
        "CONTENT_DETAIL_BACK_CONTROL_ID",
        "contentDetailBackControlId",
        "docs-viewer-content-detail-view.js",
        "docs-viewer-table-detail.js",
        "tableDetailAdapter",
    )
    if any(value not in public_entry for value in required):
        raise AssertionError("public entrypoint did not explicitly compose Table Detail View")
    if any(value not in manage_entry for value in required):
        raise AssertionError("Manage entrypoint did not explicitly compose Table Detail View")
    managed_required = (
        "createDocsViewerManagedTableTools",
        "docs-viewer-managed-table-tools.js",
        "managedTableDetailAdapter",
        "withDocsViewerManagedTableToolDefinitions",
    )
    if any(value not in manage_entry for value in managed_required):
        raise AssertionError("Manage entrypoint did not explicitly compose Managed Table Tools")
    if "/management/" in public_entry:
        raise AssertionError("public Table Detail composition imports management runtime")


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const modules = await Promise.all([
                import('/docs-viewer/runtime/js/shared/docs-viewer-app-control-renderers.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-content-detail-view.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-control-surface-host.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-main-view-host.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-panel-layout.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-table-detail.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js'),
                import('/docs-viewer/runtime/js/management/docs-viewer-managed-table-tools.js')
            ]);
            window.__docsViewerTableDetailSmoke = {
                controlRenderers: modules[0],
                contentDetail: modules[1],
                controlHost: modules[2],
                documentController: modules[3],
                mainViewHost: modules[4],
                panelLayout: modules[5],
                tableDetail: modules[6],
                viewRegistry: modules[7],
                managedTableTools: modules[8]
            };
        }"""
    )


def assert_document_controller_table_mount(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const { documentController } = window.__docsViewerTableDetailSmoke;
            const content = document.createElement('article');
            const order = [];
            let tableMount = null;
            const requested = [];
            const requestContentDetail = target => {
                requested.push(target);
                return true;
            };
            const controller = documentController.initDocsViewerDocumentController({
                content,
                toolbar: document.createElement('div'),
                results: document.createElement('div'),
                more: document.createElement('div'),
                tableDetailAdapter: {
                    releaseDocument() { order.push('table-release'); },
                    mountDocument(context) {
                        order.push('table');
                        tableMount = {
                            generation: context.documentMountGeneration,
                            html: context.content.innerHTML,
                            requestAccepted: context.requestContentDetail({ kind: 'table' }),
                            viewerScope: context.viewerScope
                        };
                    }
                },
                diagramDetailAdapter: {
                    releaseDocument() { order.push('diagram-release'); },
                    mountDocument() { order.push('diagram'); }
                },
                mountDocumentExtras: () => order.push('extras'),
                requestContentDetail,
                viewerScope: () => 'library',
                scopeConfig: {
                    scopeConfigsById: new Map([['library', { scopeId: 'library', scopeType: 'public' }]])
                },
                selectedDocument: { selectedDocId: '' },
                routeSession: { managementContext: false },
                hasActiveQuery: () => false,
                clearResultsStatus: () => {},
                setRecentModeActive: () => {},
                projectDocumentShell: () => {},
                renderBookmarkToggle: () => {},
                renderBookmarkUi: () => {},
                renderManagementUi: () => {},
                renderMeta: () => {},
                renderSearchMode: () => {},
                renderSidebar: () => {},
                statusCommands: { setStatus: () => {} }
            });
            controller.renderPayload(
                { doc_id: 'd-table', title: 'Table' },
                { content_html: '<table data-docs-content-detail="table"><tr><td>one</td></tr></table>' },
                ''
            );
            controller.showSearchPane();
            controller.renderDocLoadingState({ doc_id: 'd-next', title: 'Next' });
            return { order, requested, tableMount };
        }"""
    )
    if result["order"] != [
        "table-release",
        "diagram-release",
        "table",
        "diagram",
        "extras",
        "table-release",
        "table-release",
        "diagram-release",
    ]:
        raise AssertionError(f"rendered-document table adapter order changed: {result!r}")
    if result["tableMount"] != {
        "generation": 1,
        "html": '<table data-docs-content-detail="table"><tbody><tr><td>one</td></tr></tbody></table>',
        "requestAccepted": True,
        "viewerScope": "library",
    }:
        raise AssertionError(f"rendered-document table context changed: {result!r}")
    if result["requested"] != [{"kind": "table"}]:
        raise AssertionError(f"rendered-document did not preserve the exact view request callback: {result!r}")


def assert_table_detail_lifecycle(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const modules = window.__docsViewerTableDetailSmoke;
            const root = document.createElement('div');
            root.className = 'docsViewer';
            root.dataset.docsViewerAppKind = 'public';
            const actions = document.createElement('div');
            const sidebar = document.createElement('aside');
            sidebar.className = 'docsViewer__sidebar';
            const main = document.createElement('article');
            main.className = 'docsViewer__main';
            const content = document.createElement('div');
            content.className = 'docsViewer__content content';
            const infoPanel = document.createElement('aside');
            infoPanel.className = 'docsViewer__infoPanel';
            main.appendChild(content);
            root.append(actions, sidebar, main, infoPanel);
            document.body.replaceChildren(root);

            const columns = Array.from({ length: 2 }, (_, index) => `Column ${index + 1}`);
            const header = columns.map((value, index) => `<th id="head-${index}">${value}</th>`).join('');
            const rows = Array.from({ length: 2 }, (_, row) => (
                '<tr>' + columns.map((_, column) => (
                    `<td headers="head-${column}">row-${row}-column-${column}-long-unbroken-value</td>`
                )).join('') + '</tr>'
            )).join('');
            content.innerHTML = [
                '<p id="before">Before table</p>',
                '<table id="source-table" aria-labelledby="head-0" data-docs-content-detail="table"><thead><tr>',
                header,
                '</tr></thead><tbody>', rows, '</tbody></table>',
                '<table id="ordinary"><thead><tr><th>Ordinary</th></tr></thead><tbody><tr><td>Fallback</td></tr></tbody></table>',
                '<p id="after">After table</p>'
            ].join('');
            const sourceTable = content.querySelector('#source-table');

            const tableAdapter = modules.tableDetail.createDocsViewerTableDetailAdapter();
            const contentDefinitions = modules.contentDetail.withDocsViewerContentDetailDefinitions(null, {
                tableDetailAdapter: tableAdapter
            });
            const contexts = ['public', 'manage', 'review'].reduce((values, kind) => {
                const registry = modules.viewRegistry.createDocsViewerViewRegistry({
                    definitionSets: [modules.viewRegistry.createDocsViewerSharedViewDefinitions(), contentDefinitions],
                    projectionInputs: { appContext: { kind, featurePolicy: {} } }
                });
                values[kind] = {
                    view: registry.resolveView('content-detail').available,
                    controls: registry.projectControls({
                        surfaceId: 'main-view', activeViewId: 'content-detail'
                    }).map(control => control.id)
                };
                return values;
            }, {});
            const registry = modules.viewRegistry.createDocsViewerViewRegistry({
                definitionSets: [modules.viewRegistry.createDocsViewerSharedViewDefinitions(), contentDefinitions],
                projectionInputs: { appContext: { kind: 'public', featurePolicy: {} } }
            });
            const panelLayout = modules.panelLayout.createDocsViewerPanelLayout({
                root,
                indexPanelRefs: { sidebar },
                mainViewRefs: {},
                infoPanelRefs: { panel: infoPanel },
                viewRegistry: registry
            });
            panelLayout.renderIndexPanelState();
            panelLayout.projectInfoPanel({ activeViewId: 'metadata-info', visible: true });

            const controlStates = {};
            let host = null;
            const surface = modules.controlHost.createDocsViewerControlSurfaceHost({
                mount: actions,
                registry,
                renderers: modules.controlRenderers.createDocsViewerSharedControlRenderers(),
                surfaceId: 'main-view',
                onDispatch: detail => {
                    if (detail.controlId === modules.contentDetail.CONTENT_DETAIL_BACK_CONTROL_ID) {
                        host.requestView('rendered-document', { reason: 'back', warn: false });
                    }
                }
            });
            const renderControls = () => surface.render({
                activeViewId: host ? host.activeViewId() : 'rendered-document',
                activeModeId: 'rendered-document',
                controlStateById: controlStates
            });
            const warnings = [];
            host = modules.mainViewHost.createDocsViewerMainViewHost({
                contextOptions: {},
                defaultViewId: 'rendered-document',
                mount: content,
                panelLayout,
                projectControlState: (id, state) => {
                    controlStates[id] = state;
                    renderControls();
                },
                projectToolbar: () => {},
                projectViewState: () => panelLayout.projectViewState(),
                registry,
                showWarning: message => warnings.push(message),
                onViewChange: renderControls,
                updatePanelViewState: () => {}
            });
            renderControls();

            let requestedTarget = null;
            const mounted = tableAdapter.mountDocument({
                content,
                doc: { doc_id: 'd-table' },
                document,
                documentMountGeneration: 7,
                requestContentDetail: target => {
                    requestedTarget = target;
                    return host.requestView('content-detail', {
                        reason: 'content-detail-open', targetContext: target, warn: true
                    });
                },
                viewerScope: 'library'
            });
            const openControls = Array.from(content.querySelectorAll('.docsViewer__tableDetailOpen'));
            const openControlPresentation = {
                accessibleLabel: openControls[0].getAttribute('aria-label'),
                iconClass: openControls[0].querySelector('svg')?.classList.contains('docsViewer__diagramDetailIcon') || false,
                iconPath: openControls[0].querySelector('path')?.getAttribute('d') || '',
                title: openControls[0].getAttribute('title'),
                visibleText: openControls[0].textContent.trim()
            };
            openControls[0].focus();
            openControls[0].click();
            await new Promise(resolve => setTimeout(resolve, 0));

            const detailRoot = content.querySelector('[data-docs-content-detail-view="table"]');
            const viewport = detailRoot.querySelector('.docsViewer__tableDetailViewport');
            const clone = viewport.querySelector('table');
            const cloneHeader = clone.querySelector('th');
            const cloneCell = clone.querySelector('td');
            const expanded = {
                active: host.activeViewId(),
                activeMarker: content.dataset.docsContentDetailActive,
                cloneAriaRelationship: clone.getAttribute('aria-labelledby') === cloneHeader.id,
                cloneHeadersRelationship: cloneCell.getAttribute('headers') === cloneHeader.id,
                cloneIdChanged: clone.id !== 'source-table' && cloneHeader.id !== 'head-0',
                cloneMarkerRemoved: !clone.hasAttribute('data-docs-content-detail'),
                frozenTarget: Object.isFrozen(requestedTarget) && Object.isFrozen(requestedTarget.documentTarget),
                infoHidden: infoPanel.hidden,
                layout: root.dataset.viewerLayout,
                originalRetained: content.contains(sourceTable),
                sidebarHidden: sidebar.hidden,
            };

            actions.querySelector('.docsViewer__contentDetailBack').click();
            await new Promise(resolve => setTimeout(resolve, 0));
            const restored = {
                active: host.activeViewId(),
                activeMarker: content.hasAttribute('data-docs-content-detail-active'),
                detailRemoved: !content.querySelector('[data-docs-content-detail-view]'),
                infoRestored: !infoPanel.hidden,
                layout: root.dataset.viewerLayout,
                originalIdentity: content.querySelector('#source-table') === sourceTable,
                sidebarRestored: !sidebar.hidden
            };

            const released = tableAdapter.releaseDocument({ content, document });
            host.requestView('content-detail', {
                reason: 'content-detail-open', targetContext: requestedTarget, warn: true
            });
            await new Promise(resolve => setTimeout(resolve, 0));
            await new Promise(resolve => setTimeout(resolve, 0));
            return {
                composition: contexts,
                controlCount: openControls.length,
                openControlPresentation,
                expanded,
                mounted,
                ordinaryUndecorated: content.querySelector('#ordinary') !== null,
                released,
                restored,
                staleFailure: {
                    active: host.activeViewId(),
                    layout: root.dataset.viewerLayout,
                    warning: warnings.at(-1) || ''
                }
            };
        }"""
    )
    if result["composition"] != {
        "public": {
            "view": True,
            "controls": ["content-detail-back", "content-detail-label"],
        },
        "manage": {
            "view": True,
            "controls": ["content-detail-back", "content-detail-label"],
        },
        "review": {"view": False, "controls": []},
    }:
        raise AssertionError(f"Content Detail app-kind composition changed: {result!r}")
    if result["mounted"] != {"found": 1, "decorated": 1, "skipped": 0}:
        raise AssertionError(f"marked-table registration changed: {result!r}")
    if result["controlCount"] != 1 or not result["ordinaryUndecorated"]:
        raise AssertionError(f"table decoration eligibility changed: {result!r}")
    if result["openControlPresentation"] != {
        "accessibleLabel": "Open table 1",
        "iconClass": True,
        "iconPath": "M14 5h5v5M19 5l-8 8M19 13v6H5V5h6",
        "title": "Open table 1",
        "visibleText": "",
    }:
        raise AssertionError(f"table detail icon control changed: {result!r}")
    expected_expanded = {
        "active": "content-detail",
        "activeMarker": "true",
        "cloneAriaRelationship": True,
        "cloneHeadersRelationship": True,
        "cloneIdChanged": True,
        "cloneMarkerRemoved": True,
        "frozenTarget": True,
        "infoHidden": True,
        "layout": "expanded-main",
        "originalRetained": True,
        "sidebarHidden": True,
    }
    if result["expanded"] != expected_expanded:
        raise AssertionError(f"expanded table presentation changed: {result!r}")
    expected_restored = {
        "active": "rendered-document",
        "activeMarker": False,
        "detailRemoved": True,
        "infoRestored": True,
        "layout": "index-document-info",
        "originalIdentity": True,
        "sidebarRestored": True,
    }
    if result["restored"] != expected_restored:
        raise AssertionError(f"Back restoration changed: {result!r}")
    if result["released"] != {"released": 1}:
        raise AssertionError(f"table target cleanup changed: {result!r}")
    stale = result["staleFailure"]
    if stale["active"] != "rendered-document" or stale["layout"] != "index-document-info":
        raise AssertionError(f"stale target did not return to the document layout: {result!r}")
    if "stale or unavailable" not in stale["warning"]:
        raise AssertionError(f"stale target failure was not explicit: {result!r}")


def assert_managed_table_tools(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const managed = window.__docsViewerTableDetailSmoke.managedTableTools;
            const copied = [];
            const statuses = [];
            const controlStates = {};
            const tools = managed.createDocsViewerManagedTableTools({
                writeClipboardText: text => {
                    copied.push(text);
                    return Promise.resolve();
                }
            });
            const table = document.createElement('table');
            table.innerHTML = [
                '<thead><tr><th>Project</th><th>Owner</th></tr></thead>',
                '<tbody><tr><td> Alpha   Beta </td><td><a href="/studio">Studio Team</a></td></tr>',
                '<tr><td></td><td>Last</td></tr></tbody>'
            ].join('');
            document.body.replaceChildren(table);
            const handlers = tools.controlHandlers();
            const extension = tools.presentationExtension.mount({
                document,
                table,
                viewport: document.body
            });
            extension.activate({
                projectControlState: (id, state) => { controlStates[id] = state; }
            });

            const definitions = managed.withDocsViewerManagedTableToolDefinitions({
                controls: [], modes: [], views: []
            });
            const renderers = managed.createDocsViewerManagedTableToolControlRenderers();
            const copy = renderers[managed.CONTENT_DETAIL_COPY_TABLE_CONTROL_ID]({ document });
            const handles = Array.from(table.querySelectorAll('.docsViewer__tableResizeHandle'));
            const initial = {
                controls: definitions.controls.map(control => [control.id, control.label]),
                copyText: copy.textContent.trim(),
                copyIconRect: Boolean(copy.querySelector('svg rect')),
                copyIconPath: Boolean(copy.querySelector('svg path')),
                handleCount: handles.length,
                handleLabels: handles.map(handle => handle.getAttribute('aria-label')),
                handleRole: handles[0]?.getAttribute('role') || '',
                resetDisabled: controlStates[managed.CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID].disabled
            };

            const firstBefore = Number(handles[0].getAttribute('aria-valuenow'));
            handles[0].dispatchEvent(new KeyboardEvent('keydown', {
                bubbles: true, cancelable: true, key: 'ArrowRight'
            }));
            const firstAfter = Number(handles[0].getAttribute('aria-valuenow'));
            const secondBefore = Number(handles[1].getAttribute('aria-valuenow'));
            handles[1].dispatchEvent(new PointerEvent('pointerdown', {
                bubbles: true, button: 0, cancelable: true, clientX: 100, pointerId: 21
            }));
            handles[1].dispatchEvent(new PointerEvent('pointermove', {
                bubbles: true, cancelable: true, clientX: 132, pointerId: 21
            }));
            handles[1].dispatchEvent(new PointerEvent('pointerup', {
                bubbles: true, cancelable: true, clientX: 132, pointerId: 21
            }));
            const secondAfter = Number(handles[1].getAttribute('aria-valuenow'));
            const resized = {
                keyboardDelta: firstAfter - firstBefore,
                managedClass: table.classList.contains('docsViewer__tableDetailTable--managedWidths'),
                pointerDelta: secondAfter - secondBefore,
                resetEnabled: !controlStates[managed.CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID].disabled,
                widthColumns: table.querySelectorAll('colgroup[data-docs-viewer-managed-table-widths] > col').length
            };

            handlers[managed.CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID]({
                setStatus: (message, error) => statuses.push({ message, error })
            });
            const resetState = {
                managedClass: table.classList.contains('docsViewer__tableDetailTable--managedWidths'),
                resetDisabled: controlStates[managed.CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID].disabled,
                widthColumns: table.querySelectorAll('colgroup[data-docs-viewer-managed-table-widths] > col').length
            };
            handlers[managed.CONTENT_DETAIL_COPY_TABLE_CONTROL_ID]({
                setStatus: (message, error) => statuses.push({ message, error })
            });
            await new Promise(resolve => setTimeout(resolve, 0));

            const spanTable = document.createElement('table');
            spanTable.innerHTML = [
                '<thead><tr><th rowspan="2">A</th><th>B</th></tr><tr><th>C</th></tr></thead>',
                '<tbody><tr><td colspan="2"> Value\\nwith   space </td></tr></tbody>'
            ].join('');
            const spanTsv = managed.serializeDocsViewerTableToTsv(spanTable);

            extension.release();
            const released = {
                handles: table.querySelectorAll('.docsViewer__tableResizeHandle').length,
                managedClass: table.classList.contains('docsViewer__tableDetailTable--managedWidths'),
                resetHidden: controlStates[managed.CONTENT_DETAIL_RESET_WIDTHS_CONTROL_ID].hidden,
                copyHidden: controlStates[managed.CONTENT_DETAIL_COPY_TABLE_CONTROL_ID].hidden
            };
            handlers[managed.CONTENT_DETAIL_COPY_TABLE_CONTROL_ID]({
                setStatus: (message, error) => statuses.push({ message, error })
            });
            await new Promise(resolve => setTimeout(resolve, 0));
            return {
                copied,
                initial,
                released,
                resetState,
                resized,
                spanTsv,
                statuses
            };
        }"""
    )
    if result["initial"] != {
        "controls": [
            ["content-detail-reset-widths", "Reset widths"],
            ["content-detail-copy-table", "Copy table"],
        ],
        "copyText": "",
        "copyIconRect": True,
        "copyIconPath": True,
        "handleCount": 2,
        "handleLabels": ["Resize Project", "Resize Owner"],
        "handleRole": "separator",
        "resetDisabled": True,
    }:
        raise AssertionError(f"Managed Table Tools presentation changed: {result!r}")
    if result["resized"] != {
        "keyboardDelta": 16,
        "managedClass": True,
        "pointerDelta": 32,
        "resetEnabled": True,
        "widthColumns": 2,
    }:
        raise AssertionError(f"Managed Table Tools resizing changed: {result!r}")
    if result["resetState"] != {"managedClass": False, "resetDisabled": True, "widthColumns": 0}:
        raise AssertionError(f"Managed Table Tools Reset changed: {result!r}")
    if result["copied"] != ["Project\tOwner\nAlpha Beta\tStudio Team\n\tLast"]:
        raise AssertionError(f"Copy table TSV changed: {result!r}")
    if result["spanTsv"] != "A\tB\n\tC\nValue with space\t":
        raise AssertionError(f"semantic span serialization changed: {result!r}")
    if result["released"] != {
        "copyHidden": True,
        "handles": 0,
        "managedClass": False,
        "resetHidden": True,
    }:
        raise AssertionError(f"Managed Table Tools lifecycle cleanup changed: {result!r}")
    if result["statuses"] != [{"message": "Copy table is unavailable.", "error": True}]:
        raise AssertionError(f"Managed Table Tools failure reporting changed: {result!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=Path("site"))
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()

    assert_entrypoint_composition()
    server, base_url = start_static_server(args.site_root)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_default_timeout(args.timeout_ms)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                page.goto(f"{base_url}/404.html", wait_until="domcontentloaded")
                install_fixture(page)
                assert_document_controller_table_mount(page)
                assert_table_detail_lifecycle(page)
                assert_managed_table_tools(page)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Table Detail View smoke: {errors!r}")
    print("Docs Viewer table detail module smoke OK")


if __name__ == "__main__":
    main()
