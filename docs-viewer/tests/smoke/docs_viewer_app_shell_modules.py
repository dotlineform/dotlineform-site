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
                  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
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
            const shellIds = [
                'docsViewerContextMenu',
                'docsViewerMetadataModal',
                'docsViewerMetadataForm',
                'docsViewerMetadataTitleInput',
                'docsViewerMetadataSummaryInput',
                'docsViewerMetadataStatusInput',
                'docsViewerMetadataHiddenInput',
                'docsViewerMetadataParentInput',
                'docsViewerMetadataParentPopup',
                'docsViewerMetadataSortOrderInput',
                'docsViewerMetadataCancelButton',
                'docsViewerMetadataSaveButton',
                'docsViewerImportModal',
                'docsHtmlImportRoot',
                'docsHtmlImportBootStatus',
                'docsViewerSettingsModal',
                'docsViewerSettingsForm',
                'docsViewerSettingsUpdatedInput',
                'docsViewerSettingsCancelButton',
                'docsViewerSettingsSaveButton'
            ];
            return {
                returnedRowId: returned.managementActions && returned.managementActions.id,
                returnedContextMenuId: returned.managementShell && returned.managementShell.contextMenu && returned.managementShell.contextMenu.id,
                missingIds: ids.filter((id) => !document.getElementById(id)),
                missingShellIds: shellIds.filter((id) => !document.getElementById(id)),
                menuRole: document.getElementById('docsViewerManageActionsMenu')?.getAttribute('role') || '',
                menuItemCount: document.querySelectorAll('#docsViewerManageActionsMenu [role="menuitem"]').length,
                contextActionCount: document.querySelectorAll('#docsViewerContextMenu [data-context-action]').length,
                metadataDialogLabel: document.querySelector('#docsViewerMetadataModal [role="dialog"]')?.getAttribute('aria-labelledby') || '',
                importRouteReady: document.getElementById('docsHtmlImportRoot')?.dataset.studioReady || '',
                settingsFieldName: document.getElementById('docsViewerSettingsUpdatedInput')?.getAttribute('name') || '',
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
    if result["returnedContextMenuId"] != "docsViewerContextMenu":
        raise AssertionError(f"app shell did not return the management shell refs: {result!r}")
    if result["missingIds"]:
        raise AssertionError(f"app shell omitted expected management refs: {result!r}")
    if result["missingShellIds"]:
        raise AssertionError(f"app shell omitted expected management shell refs: {result!r}")
    if result["menuRole"] != "menu" or result["menuItemCount"] != 10:
        raise AssertionError(f"app shell did not render the expected Actions menu: {result!r}")
    if result["contextActionCount"] != 5 or result["metadataDialogLabel"] != "docsViewerMetadataHeading":
        raise AssertionError(f"management context/metadata shell changed unexpectedly: {result!r}")
    if result["importRouteReady"] != "false" or result["settingsFieldName"] != "show_updated_date":
        raise AssertionError(f"management import/settings shell changed unexpectedly: {result!r}")
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
                  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await module.initDocsViewerAppShell({ root, document });
            return {
                returnedRow: Boolean(returned.managementActions),
                returnedManagementShell: Boolean(returned.managementShell),
                manageRowCount: document.querySelectorAll('#docsViewerManageRow').length,
                actionButtonCount: document.querySelectorAll('#docsViewerManageActionsButton').length,
                contextMenuCount: document.querySelectorAll('#docsViewerContextMenu').length,
                metadataModalCount: document.querySelectorAll('#docsViewerMetadataModal').length,
                importRootCount: document.querySelectorAll('#docsHtmlImportRoot').length,
                settingsModalCount: document.querySelectorAll('#docsViewerSettingsModal').length,
                actionsMountChildCount: document.querySelector('[data-docs-viewer-management-actions-mount]').children.length,
                shellMountChildCount: document.querySelector('[data-docs-viewer-management-shell-mount]').children.length
            };
        }"""
    )
    if result != {
        "returnedRow": False,
        "returnedManagementShell": False,
        "manageRowCount": 0,
        "actionButtonCount": 0,
        "contextMenuCount": 0,
        "metadataModalCount": 0,
        "importRootCount": 0,
        "settingsModalCount": 0,
        "actionsMountChildCount": 0,
        "shellMountChildCount": 0,
    }:
        raise AssertionError(f"public route management action omission failed: {result!r}")


def assert_route_context_and_shell_refs(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const context = await import('/docs-viewer/runtime/js/docs-viewer-app-context.js');
            const shell = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            window.history.replaceState({}, '', '/docs/?scope=studio&doc=intro&mode=manage&import=1');
            document.body.innerHTML = `
                <section
                  id="docsViewerRoot"
                  data-allow-management="true"
                  data-allow-scope-query="true"
                  data-docs-viewer-config-url="/docs-viewer/config/defaults/docs-viewer-config.json"
                  data-viewer-base-url="/docs/"
                  data-viewer-scope="studio"
                  data-index-url="/assets/data/docs/scopes/studio/index.json"
                  data-search-index-url="/assets/data/search/studio/index.json"
                  data-default-doc-id="dev-home"
                  data-include-scope-param="true"
                  data-ui-text-url="/docs-viewer/config/ui-text/ui-text.json"
                  data-report-registry-url="/assets/data/docs/reports.json"
                  data-management-base-url="http://127.0.0.1:8789/"
                >
                  <div id="docsViewerHeaderControlsMount" data-docs-viewer-header-controls-mount data-enable-search="true"></div>
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                  <p id="docsViewerStatus"></p>
                  <div id="docsViewerBookmarkRow"></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await shell.initDocsViewerAppShell({ root, document });
            const route = context.createDocsViewerRouteContext({
                root,
                window,
                assetVersion: 'smoke',
                managementModeValue: 'manage'
            });
            const refs = shell.getDocsViewerAppShellRefs({ root, document });
            const updated = context.updateDocsViewerRouteContext(route, {
                viewerScope: 'library',
                indexUrl: '/assets/data/docs/scopes/library/index.json?v=smoke',
                searchIndexUrl: '/assets/data/search/library/index.json?v=smoke',
                defaultRouteDocId: 'library-home',
                viewerBaseUrl: '/library/',
                includeScopeParam: false
            }, { window });
            return {
                routeConfigSource: route.routeConfig.source,
                routeType: route.routeConfig.routeType,
                allowManagement: route.access.allowManagement,
                canLoadManagementUi: route.access.canLoadManagementUi,
                backendReachability: route.access.backendReachability,
                allowScopeQuery: route.access.allowScopeQuery,
                managementRequested: route.access.managementRequested,
                importRequested: route.access.importRequested,
                publicReadOnly: route.access.publicReadOnly,
                indexUrl: route.indexUrl,
                searchIndexUrl: route.searchIndexUrl,
                managementBaseUrl: route.managementBaseUrl,
                generatedBaseUrl: route.generatedBaseUrl,
                bookmarkScope: route.bookmarkScope,
                refs: {
                    scopeSelect: refs.headerControls.scopeSelect?.id || '',
                    recentButton: refs.headerControls.recentButton?.id || '',
                    searchInput: refs.headerControls.searchInput?.id || '',
                    nav: refs.indexPanel.nav?.id || '',
                    content: refs.documentShell.content?.id || '',
                    infoBody: refs.infoPanel.body?.id || '',
                    status: refs.status?.id || '',
                    bookmarkRow: refs.bookmarkRow?.id || '',
                    managementRow: refs.managementActions.row?.id || '',
                    contextMenu: refs.managementShell.contextMenu?.id || '',
                    metadataModal: refs.managementShell.metadataModal?.id || '',
                    importRoot: refs.managementShell.importRoot?.id || '',
                    settingsModal: refs.managementShell.settingsModal?.id || ''
                },
                updated: {
                    viewerScope: updated.viewerScope,
                    viewerPathname: updated.viewerPathname,
                    bookmarkScope: updated.bookmarkScope,
                    includeScopeParam: updated.includeScopeParam
                }
            };
        }"""
    )
    if result != {
        "routeConfigSource": "dataset",
        "routeType": "manage",
        "allowManagement": True,
        "canLoadManagementUi": True,
        "backendReachability": "unknown",
        "allowScopeQuery": True,
        "managementRequested": True,
        "importRequested": True,
        "publicReadOnly": False,
        "indexUrl": "/assets/data/docs/scopes/studio/index.json?v=smoke",
        "searchIndexUrl": "/assets/data/search/studio/index.json?v=smoke",
        "managementBaseUrl": "http://127.0.0.1:8789",
        "generatedBaseUrl": "http://127.0.0.1:8789",
        "bookmarkScope": "studio",
        "refs": {
            "scopeSelect": "docsViewerScopeSelect",
            "recentButton": "docsViewerRecentButton",
            "searchInput": "docsViewerSearchInput",
            "nav": "docsViewerNav",
            "content": "docsViewerContent",
            "infoBody": "docsViewerInfoPanelBody",
            "status": "docsViewerStatus",
            "bookmarkRow": "docsViewerBookmarkRow",
            "managementRow": "docsViewerManageRow",
            "contextMenu": "docsViewerContextMenu",
            "metadataModal": "docsViewerMetadataModal",
            "importRoot": "docsHtmlImportRoot",
            "settingsModal": "docsViewerSettingsModal",
        },
        "updated": {
            "viewerScope": "library",
            "viewerPathname": "/library/",
            "bookmarkScope": "library",
            "includeScopeParam": False,
        },
    }:
        raise AssertionError(f"route context or shell refs contract failed: {result!r}")


def assert_route_config_explicit_and_access_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const context = await import('/docs-viewer/runtime/js/docs-viewer-app-context.js');
            const routeConfig = await import('/docs-viewer/runtime/js/docs-viewer-route-config.js');
            const access = await import('/docs-viewer/runtime/js/docs-viewer-access.js');
            window.history.replaceState({}, '', '/library/?mode=manage&import=1');
            document.body.innerHTML = `
                <section
                  id="docsViewerRoot"
                  data-allow-management="true"
                  data-allow-scope-query="true"
                  data-viewer-base-url="/legacy/"
                  data-viewer-scope="legacy"
                ></section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const explicitRouteConfig = {
                schema_version: 'docs_viewer_route_config_v1',
                route_id: 'library-public',
                route_type: 'public',
                default_scope_id: 'library',
                default_doc_id: 'library',
                include_scope_param: false,
                allow_scope_query: false,
                viewer_base_url: '/library/',
                generated_base_url: 'http://127.0.0.1:8789',
                docs_paths: {
                    index_url: '/assets/data/docs/scopes/library/index.json',
                    search_index_url: '/assets/data/search/library/index.json'
                },
                config_urls: {
                    docs_viewer: '/docs-viewer/config/defaults/docs-viewer-public-config.json',
                    ui_text: '/docs-viewer/config/ui-text/ui-text.json',
                    report_registry: '/assets/data/docs/reports.json'
                },
                access: {
                    allow_management: false,
                    allow_scope_query: false,
                    management_base_url: 'http://127.0.0.1:8789',
                    management_mode_value: 'manage'
                },
                panels: {
                    index: { enabled: true, default_state: 'normal' },
                    document: { enabled: true, default_view: 'document' },
                    info: { enabled: false, default_view: '' }
                },
                hosted_views: {
                    records: [
                        { id: 'extra-public', label: 'Extra', panel: 'document', access: 'public', availability: 'available' }
                    ]
                }
            };
            const resolved = routeConfig.resolveDocsViewerRouteConfig({ root, routeConfig: explicitRouteConfig });
            const route = context.createDocsViewerRouteContext({ root, window, assetVersion: 'smoke', routeConfig: explicitRouteConfig });
            const projected = access.createDocsViewerAccessProjection({
                routeConfig: resolved,
                search: window.location.search
            });
            return {
                source: resolved.source,
                routeId: resolved.routeId,
                routeType: resolved.routeType,
                defaultScopeId: resolved.defaultScopeId,
                legacyIgnored: route.viewerBaseUrl,
                indexUrl: route.indexUrl,
                routeGeneratedBaseUrl: route.generatedBaseUrl,
                routeManagementBaseUrl: route.managementBaseUrl,
                allowManagement: projected.allowManagement,
                canLoadManagementUi: projected.canLoadManagementUi,
                backendReachability: projected.backendReachability,
                writeAvailability: projected.writeAvailability,
                publicReadOnly: projected.publicReadOnly,
                requestedMode: projected.requestedMode,
                managementRequested: projected.managementRequested,
                importRequested: projected.importRequested,
                hostedViewCount: resolved.hostedViews.records.length
            };
        }"""
    )
    if result != {
        "source": "explicit",
        "routeId": "library-public",
        "routeType": "public",
        "defaultScopeId": "library",
        "legacyIgnored": "/library/",
        "indexUrl": "/assets/data/docs/scopes/library/index.json?v=smoke",
        "routeGeneratedBaseUrl": "",
        "routeManagementBaseUrl": "",
        "allowManagement": False,
        "canLoadManagementUi": False,
        "backendReachability": "unavailable",
        "writeAvailability": "unavailable",
        "publicReadOnly": True,
        "requestedMode": "",
        "managementRequested": False,
        "importRequested": False,
        "hostedViewCount": 1,
    }:
        raise AssertionError(f"explicit route config/access projection failed: {result!r}")


def assert_route_config_inline_and_malformed_fallback(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const context = await import('/docs-viewer/runtime/js/docs-viewer-app-context.js');
            const routeConfig = await import('/docs-viewer/runtime/js/docs-viewer-route-config.js');
            window.history.replaceState({}, '', '/analysis/?doc=analysis');
            document.body.innerHTML = `
                <section
                  id="docsViewerRoot"
                  data-route-id="legacy-library"
                  data-route-config-script-id="docsViewerRouteConfig"
                  data-allow-management="false"
                  data-allow-scope-query="false"
                  data-viewer-base-url="/legacy/"
                  data-viewer-scope="legacy"
                  data-index-url="/legacy/index.json"
                  data-search-index-url="/legacy/search.json"
                  data-default-doc-id="legacy-home"
                >
                  <script type="application/json" id="docsViewerRouteConfig" data-docs-viewer-route-config>{
                    "schema_version": "docs_viewer_route_config_v1",
                    "route_id": "analysis-public",
                    "default_scope_id": "analysis",
                    "default_doc_id": "analysis",
                    "include_scope_param": false,
                    "allow_scope_query": false,
                    "viewer_base_url": "/analysis/",
                    "generated_base_url": "",
                    "docs_paths": {
                      "index_url": "/assets/data/docs/scopes/analysis/index.json",
                      "search_index_url": "/assets/data/search/analysis/index.json"
                    },
                    "config_urls": {
                      "docs_viewer": "/docs-viewer/config/defaults/docs-viewer-public-config.json",
                      "ui_text": "/docs-viewer/config/ui-text/ui-text.json",
                      "report_registry": "/assets/data/docs/reports.json"
                    },
                    "access": {
                      "allow_management": false,
                      "allow_scope_query": false,
                      "management_base_url": ""
                    },
                    "panels": {
                      "index": { "enabled": true, "default_state": "normal" },
                      "document": { "enabled": true, "default_view": "document" },
                      "info": { "enabled": true, "default_view": "metadata-info" }
                    },
                    "hosted_views": {
                      "records": [
                        { "id": "analysis-extra", "label": "Analysis extra", "panel": "info", "access": "public" }
                      ]
                    }
                  }</script>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const inline = routeConfig.resolveDocsViewerRouteConfig({ root, document });
            const route = context.createDocsViewerRouteContext({ root, document, window, assetVersion: 'smoke' });
            document.body.innerHTML = `
                <section
                  id="docsViewerRoot"
                  data-route-id="legacy-library"
                  data-route-config-script-id="docsViewerRouteConfig"
                  data-allow-management="false"
                  data-allow-scope-query="false"
                  data-viewer-base-url="/library/"
                  data-viewer-scope="library"
                  data-index-url="/assets/data/docs/scopes/library/index.json"
                  data-search-index-url="/assets/data/search/library/index.json"
                  data-default-doc-id="library"
                  data-docs-viewer-config-url="/docs-viewer/config/defaults/docs-viewer-public-config.json"
                >
                  <script type="application/json" id="docsViewerRouteConfig" data-docs-viewer-route-config>{malformed</script>
                </section>
            `;
            const fallbackRoot = document.getElementById('docsViewerRoot');
            const fallback = routeConfig.resolveDocsViewerRouteConfig({ root: fallbackRoot, document });
            return {
                inline: {
                    source: inline.source,
                    routeId: inline.routeId,
                    defaultScopeId: inline.defaultScopeId,
                    viewerBaseUrl: inline.viewerBaseUrl,
                    indexUrl: inline.indexUrl,
                    hostedViews: inline.hostedViews.records.map((record) => record.id),
                    routeViewerBaseUrl: route.routeViewerBaseUrl,
                    routeIndexUrl: route.indexUrl
                },
                fallback: {
                    source: fallback.source,
                    routeId: fallback.routeId,
                    defaultScopeId: fallback.defaultScopeId,
                    viewerBaseUrl: fallback.viewerBaseUrl,
                    indexUrl: fallback.indexUrl,
                    docsViewerConfigUrl: fallback.docsViewerConfigUrl
                }
            };
        }"""
    )
    if result != {
        "inline": {
            "source": "inline",
            "routeId": "analysis-public",
            "defaultScopeId": "analysis",
            "viewerBaseUrl": "/analysis/",
            "indexUrl": "/assets/data/docs/scopes/analysis/index.json",
            "hostedViews": ["analysis-extra"],
            "routeViewerBaseUrl": "/analysis/",
            "routeIndexUrl": "/assets/data/docs/scopes/analysis/index.json?v=smoke",
        },
        "fallback": {
            "source": "dataset",
            "routeId": "legacy-library",
            "defaultScopeId": "library",
            "viewerBaseUrl": "/library/",
            "indexUrl": "/assets/data/docs/scopes/library/index.json",
            "docsViewerConfigUrl": "/docs-viewer/config/defaults/docs-viewer-public-config.json",
        },
    }:
        raise AssertionError(f"inline route config/fallback behavior failed: {result!r}")


def assert_route_config_registry_resolution(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const context = await import('/docs-viewer/runtime/js/docs-viewer-app-context.js');
            const routeConfig = await import('/docs-viewer/runtime/js/docs-viewer-route-config.js');
            const shell = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            window.history.replaceState({}, '', '/analysis/?doc=analysis');
            document.body.innerHTML = `
                <section
                  id="docsViewerRoot"
                  data-route-id="analysis"
                  data-route-config-url="/docs-viewer/config/routes/docs-viewer-routes.json"
                >
                  <div id="docsViewerHeaderControlsMount" data-docs-viewer-header-controls-mount data-enable-search="true"></div>
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const resolved = await routeConfig.resolveDocsViewerRouteConfigAsync({
                root,
                document,
                window,
                assetVersion: 'smoke'
            });
            const route = context.createDocsViewerRouteContext({
                root,
                document,
                window,
                assetVersion: 'smoke',
                resolvedRouteConfig: resolved
            });
            await shell.initDocsViewerAppShell({ root, document, routeContext: route });
            return {
                source: resolved.source,
                routeId: resolved.routeId,
                routeType: resolved.routeType,
                defaultScopeId: route.viewerScope,
                indexUrl: route.indexUrl,
                searchIndexUrl: route.searchIndexUrl,
                docsViewerConfigUrl: route.docsViewerConfigUrl,
                allowManagement: route.access.allowManagement,
                allowScopeQuery: route.access.allowScopeQuery,
                scopeSelectCount: document.querySelectorAll('#docsViewerScopeSelect').length,
                recentButtonCount: document.querySelectorAll('#docsViewerRecentButton').length,
                managementMountCount: document.querySelectorAll('#docsViewerManageActionsMount').length
            };
        }"""
    )
    if result != {
        "source": "registry",
        "routeId": "analysis",
        "routeType": "public",
        "defaultScopeId": "analysis",
        "indexUrl": "/assets/data/docs/scopes/analysis/index.json?v=smoke",
        "searchIndexUrl": "/assets/data/search/analysis/index.json?v=smoke",
        "docsViewerConfigUrl": "/docs-viewer/config/defaults/docs-viewer-public-config.json",
        "allowManagement": False,
        "allowScopeQuery": False,
        "scopeSelectCount": 0,
        "recentButtonCount": 1,
        "managementMountCount": 0,
    }:
        raise AssertionError(f"registry route config resolution failed: {result!r}")


def assert_app_boot_public_context_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const boot = await import('/docs-viewer/runtime/js/docs-viewer-app-boot.js');
            window.history.replaceState({}, '', '/analysis/?doc=analysis');
            document.body.innerHTML = `
                <section id="docsViewerRoot">
                  <div id="docsViewerHeaderControlsMount" data-docs-viewer-header-controls-mount data-enable-search="true"></div>
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                  <div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>
                  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
                  <p id="docsViewerStatus"></p>
                  <div id="docsViewerBookmarkRow"></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const routeConfig = {
                schema_version: 'docs_viewer_route_config_v1',
                route_id: 'analysis-public',
                route_type: 'public',
                default_scope_id: 'analysis',
                default_doc_id: 'analysis',
                viewer_base_url: '/analysis/',
                docs_paths: {
                    index_url: '/assets/data/docs/scopes/analysis/index.json',
                    search_index_url: '/assets/data/search/analysis/index.json'
                },
                config_urls: {
                    docs_viewer: '/docs-viewer/config/defaults/docs-viewer-public-config.json',
                    ui_text: '/docs-viewer/config/ui-text/ui-text.json',
                    report_registry: '/assets/data/docs/reports.json'
                },
                access: {
                    allow_management: false,
                    allow_scope_query: false,
                    management_base_url: ''
                }
            };
            const context = await boot.resolveDocsViewerAppBootContext({
                root,
                document,
                window,
                assetVersion: 'boot-smoke',
                routeConfig
            });
            return {
                rootId: context.root.id,
                assetVersion: context.assetVersion,
                routeId: context.routeContext.routeConfig.routeId,
                routeSource: context.routeContext.routeConfig.source,
                canLoadManagementUi: context.routeContext.access.canLoadManagementUi,
                appShellReadyPromise: typeof context.appShellReady.then === 'function',
                searchInputId: context.appShellRefs.headerControls.searchInput?.id || '',
                navId: context.appShellRefs.indexPanel.nav?.id || '',
                contentId: context.appShellRefs.documentShell.content?.id || '',
                infoBodyId: context.appShellRefs.infoPanel.body?.id || '',
                manageRowCount: document.querySelectorAll('#docsViewerManageRow').length,
                contextMenuCount: document.querySelectorAll('#docsViewerContextMenu').length,
                actionsMountChildCount: document.querySelector('[data-docs-viewer-management-actions-mount]').children.length,
                shellMountChildCount: document.querySelector('[data-docs-viewer-management-shell-mount]').children.length
            };
        }"""
    )
    if result != {
        "rootId": "docsViewerRoot",
        "assetVersion": "boot-smoke",
        "routeId": "analysis-public",
        "routeSource": "explicit",
        "canLoadManagementUi": False,
        "appShellReadyPromise": True,
        "searchInputId": "docsViewerSearchInput",
        "navId": "docsViewerNav",
        "contentId": "docsViewerContent",
        "infoBodyId": "docsViewerInfoPanelBody",
        "manageRowCount": 0,
        "contextMenuCount": 0,
        "actionsMountChildCount": 0,
        "shellMountChildCount": 0,
    }:
        raise AssertionError(f"public app boot context contract failed: {result!r}")


def assert_app_session_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-session.js');
            const panelLayout = {
                indexPanelState: () => ({ expanded: false, source: 'stub' }),
                projectViewState: () => ({ document: { mode: 'document' }, info: { open: false } })
            };
            const routeContext = {
                routeConfig: { routeId: 'analysis-public' },
                access: {
                    publicReadOnly: true,
                    canLoadManagementUi: false
                }
            };
            const session = module.createDocsViewerAppSession({
                defaultRecentLimit: 12,
                hostedViewRegistry: { registry: true },
                panelLayout,
                routeContext,
                searchBatchSize: 25,
                window: {}
            });
            session.domains.searchRecent.searchQuery = 'metadata';
            session.domains.bookmarks.set('bookmarksLoaded', true);
            session.domains.routeSession.updateRouteContext({
                routeConfig: { routeId: 'docs-manage' },
                access: {
                    publicReadOnly: false,
                    canLoadManagementUi: true
                }
            });
            const unknownSet = session.domains.bookmarks.set('searchQuery', 'leak');
            return {
                compatibilitySameState: session.compatibilityBridge.state === session.state,
                bridgeName: session.compatibilityBridge.name,
                domainNames: Object.keys(session.domains).sort(),
                searchAuthority: session.domains.searchRecent.authority,
                managementAuthority: session.domains.management.authority,
                searchQuery: session.state.searchQuery,
                bookmarksLoaded: session.state.bookmarksLoaded,
                unknownSet,
                leakedSearchQuery: session.state.searchQuery,
                routePublicReadOnly: session.domains.routeSession.publicReadOnly,
                routeCanLoadManagementUi: session.domains.routeSession.canLoadManagementUi,
                searchVisibleCount: session.state.searchVisibleCount,
                recentLimit: session.state.recentLimit,
                bookmarkSupport: session.state.bookmarkSupport,
                hostedViewsSameRef: session.state.hostedViews.registry === true,
                indexPanelSource: session.state.indexPanelState.source,
                viewStateInfoOpen: session.state.viewState.info.open,
                defaultManagementText: session.state.managementText.copyLinkLabel,
                docHiddenEmoji: session.state.managementText.docHiddenEmoji,
                documentIndexFields: session.domains.documentIndex.fields.slice(0, 3)
            };
        }"""
    )
    expected_domain_names = [
        "bookmarks",
        "busyStatus",
        "documentIndex",
        "generatedData",
        "management",
        "panelView",
        "routeSession",
        "scopeConfig",
        "searchRecent",
        "selectedDocument",
    ]
    if result["compatibilitySameState"] is not True or result["bridgeName"] != "runtime-state-compatibility":
        raise AssertionError(f"app session compatibility bridge failed: {result!r}")
    if result["domainNames"] != expected_domain_names:
        raise AssertionError(f"app session domain names changed unexpectedly: {result!r}")
    if result["searchAuthority"] != "generated static data or local generated-read service plus browser-only query state":
        raise AssertionError(f"app session search authority changed: {result!r}")
    if result["managementAuthority"] != "management backend capability and write flow":
        raise AssertionError(f"app session management authority changed: {result!r}")
    if result["searchQuery"] != "metadata" or result["bookmarksLoaded"] is not True:
        raise AssertionError(f"app session domain facade did not mutate shared state: {result!r}")
    if result["unknownSet"] is not False or result["leakedSearchQuery"] != "metadata":
        raise AssertionError(f"app session domain facade allowed cross-domain mutation: {result!r}")
    if result["routePublicReadOnly"] is not False or result["routeCanLoadManagementUi"] is not True:
        raise AssertionError(f"app session route context update failed: {result!r}")
    if result["searchVisibleCount"] != 25 or result["recentLimit"] != 12:
        raise AssertionError(f"app session defaults changed unexpectedly: {result!r}")
    if result["bookmarkSupport"] is not False or result["hostedViewsSameRef"] is not True:
        raise AssertionError(f"app session support/hosted view defaults failed: {result!r}")
    if result["indexPanelSource"] != "stub" or result["viewStateInfoOpen"] is not False:
        raise AssertionError(f"app session panel defaults failed: {result!r}")
    if result["defaultManagementText"] != "Copy Link" or result["docHiddenEmoji"] != "🚫":
        raise AssertionError(f"app session management text defaults changed: {result!r}")
    if result["documentIndexFields"] != ["allDocs", "allDocsById", "docs"]:
        raise AssertionError(f"app session document index domain fields changed: {result!r}")


def assert_app_composition_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const context = await import('/docs-viewer/runtime/js/docs-viewer-app-context.js');
            const shell = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            const compositionModule = await import('/docs-viewer/runtime/js/docs-viewer-app-composition.js');
            function baseRouteConfig(overrides = {}) {
                return Object.assign({
                    schema_version: 'docs_viewer_route_config_v1',
                    route_id: 'analysis-public',
                    route_type: 'public',
                    default_scope_id: 'analysis',
                    default_doc_id: 'analysis',
                    include_scope_param: false,
                    allow_scope_query: false,
                    viewer_base_url: '/analysis/',
                    generated_base_url: '',
                    docs_paths: {
                        index_url: '/assets/data/docs/scopes/analysis/index.json',
                        search_index_url: '/assets/data/search/analysis/index.json'
                    },
                    config_urls: {
                        docs_viewer: '/docs-viewer/config/defaults/docs-viewer-public-config.json',
                        ui_text: '/docs-viewer/config/ui-text/ui-text.json',
                        report_registry: '/assets/data/docs/reports.json'
                    },
                    access: {
                        allow_management: false,
                        allow_scope_query: false,
                        management_base_url: ''
                    },
                    panels: {
                        index: { enabled: true, default_state: 'normal' },
                        document: { enabled: true, default_view: 'document' },
                        info: { enabled: true, default_view: 'metadata-info' }
                    },
                    hosted_views: { records: [] }
                }, overrides);
            }
            async function createComposition(routeConfig, url) {
                window.history.replaceState({}, '', url);
                document.body.innerHTML = `
                    <section id="docsViewerRoot">
                      <div id="docsViewerHeaderControlsMount" data-docs-viewer-header-controls-mount data-enable-search="true"></div>
                      <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                      <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                      <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                      <div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>
                      <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
                      <p id="docsViewerStatus"></p>
                      <div id="docsViewerBookmarkRow"></div>
                    </section>
                `;
                const root = document.getElementById('docsViewerRoot');
                const routeContext = context.createDocsViewerRouteContext({
                    root,
                    document,
                    window,
                    assetVersion: 'composition-smoke',
                    routeConfig
                });
                await shell.initDocsViewerAppShell({ root, document, routeContext });
                const appShellRefs = shell.getDocsViewerAppShellRefs({ root, document });
                const composition = compositionModule.createDocsViewerAppComposition({
                    root,
                    window,
                    routeContext,
                    appShellRefs,
                    assetVersion: 'composition-smoke',
                    viewerScope: () => routeContext.viewerScope,
                    indexPanelAvailable: () => true
                });
                return { routeContext, composition };
            }
            const publicCreated = await createComposition(
                baseRouteConfig({
                    generated_base_url: 'http://127.0.0.1:9999',
                    access: {
                        allow_management: false,
                        allow_scope_query: false,
                        management_base_url: 'http://127.0.0.1:8789'
                    }
                }),
                '/analysis/?doc=analysis&mode=manage&import=1'
            );
            const manageCreated = await createComposition(
                baseRouteConfig({
                    route_id: 'docs-manage',
                    route_type: 'manage',
                    default_scope_id: 'studio',
                    default_doc_id: 'dev-home',
                    include_scope_param: true,
                    allow_scope_query: true,
                    viewer_base_url: '/docs/',
                    generated_base_url: 'http://127.0.0.1:8789/',
                    docs_paths: {
                        index_url: '/assets/data/docs/scopes/studio/index.json',
                        search_index_url: '/assets/data/search/studio/index.json'
                    },
                    config_urls: {
                        docs_viewer: '/docs-viewer/config/defaults/docs-viewer-config.json',
                        ui_text: '/docs-viewer/config/ui-text/ui-text.json',
                        report_registry: '/assets/data/docs/reports.json'
                    },
                    access: {
                        allow_management: true,
                        allow_scope_query: true,
                        management_base_url: 'http://127.0.0.1:8789/'
                    }
                }),
                '/docs/?scope=studio&doc=dev-home&mode=manage&import=1'
            );
            const startupOrder = [];
            await compositionModule.startDocsViewerStartupPhases({
                composition: {
                    shouldOpenImportOnLoad: (getCurrentMode) => getCurrentMode() === 'manage'
                },
                bindEvents: () => startupOrder.push('bind'),
                startBusy: () => {
                    startupOrder.push('busy-start');
                    return () => startupOrder.push('busy-stop');
                },
                loadDocsViewerConfig: () => startupOrder.push('docs-config'),
                renderIndexPanelState: () => startupOrder.push('index-panel'),
                loadViewerConfig: () => startupOrder.push('viewer-config'),
                initializeBookmarks: () => startupOrder.push('bookmarks'),
                initializeManagement: () => startupOrder.push('management'),
                loadIndex: () => startupOrder.push('index'),
                openImportOnLoad: () => startupOrder.push('import'),
                getCurrentMode: () => 'manage'
            });
            return {
                public: {
                    phases: publicCreated.composition.startupPhases.map((phase) => phase.id),
                    generatedAuthority: publicCreated.composition.serviceContext.generatedRead.authority,
                    generatedBaseUrl: publicCreated.composition.generatedBaseUrl,
                    managementContext: publicCreated.composition.serviceContext.management,
                    managementBaseUrl: publicCreated.composition.managementBaseUrl,
                    shouldOpenImport: publicCreated.composition.shouldOpenImportOnLoad(() => 'manage'),
                    recentLimit: publicCreated.composition.state.recentLimit,
                    sameState: publicCreated.composition.appSession.state === publicCreated.composition.state,
                    authorityPhases: publicCreated.composition.startupAuthorities.map((record) => record.phase)
                },
                manage: {
                    phases: manageCreated.composition.startupPhases.map((phase) => phase.id),
                    generatedAuthority: manageCreated.composition.serviceContext.generatedRead.authority,
                    generatedBaseUrl: manageCreated.composition.generatedBaseUrl,
                    managementAuthority: manageCreated.composition.serviceContext.management.authority,
                    managementBaseUrl: manageCreated.composition.managementBaseUrl,
                    shouldInitialize: manageCreated.composition.shouldInitializeManagement(() => 'manage'),
                    shouldInitializePublicMode: manageCreated.composition.shouldInitializeManagement(() => ''),
                    shouldOpenImport: manageCreated.composition.shouldOpenImportOnLoad(() => 'manage'),
                    authorityPhases: manageCreated.composition.startupAuthorities.map((record) => record.phase)
                },
                startupOrder
            };
        }"""
    )
    if result["public"] != {
        "phases": [
            "bind-events",
            "load-docs-viewer-config",
            "load-viewer-config-ui-text",
            "initialize-bookmarks",
            "load-initial-index-route",
        ],
        "generatedAuthority": "generated static asset",
        "generatedBaseUrl": "",
        "managementContext": None,
        "managementBaseUrl": "",
        "shouldOpenImport": False,
        "recentLimit": 10,
        "sameState": True,
        "authorityPhases": [
            "root/app-shell input validation",
            "app session creation",
            "service-context creation",
            "config and UI text load",
            "generated data reads",
            "bookmark initialization",
        ],
    }:
        raise AssertionError(f"public app composition contract failed: {result!r}")
    if result["manage"] != {
        "phases": [
            "bind-events",
            "load-docs-viewer-config",
            "load-viewer-config-ui-text",
            "initialize-bookmarks",
            "initialize-management",
            "load-initial-index-route",
            "open-import-on-load",
        ],
        "generatedAuthority": "local generated-read service",
        "generatedBaseUrl": "http://127.0.0.1:8789",
        "managementAuthority": "management backend capability/write endpoint",
        "managementBaseUrl": "http://127.0.0.1:8789",
        "shouldInitialize": True,
        "shouldInitializePublicMode": False,
        "shouldOpenImport": True,
        "authorityPhases": [
            "root/app-shell input validation",
            "app session creation",
            "service-context creation",
            "config and UI text load",
            "generated data reads",
            "bookmark initialization",
            "management initialization",
            "import-open-on-load",
        ],
    }:
        raise AssertionError(f"manage app composition contract failed: {result!r}")
    if result["startupOrder"] != [
        "bind",
        "busy-start",
        "docs-config",
        "index-panel",
        "viewer-config",
        "bookmarks",
        "management",
        "index",
        "import",
        "busy-stop",
    ]:
        raise AssertionError(f"app startup phase order changed: {result!r}")


def assert_app_boot_management_context_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const boot = await import('/docs-viewer/runtime/js/docs-viewer-app-boot.js');
            window.history.replaceState({}, '', '/docs/?scope=studio&doc=dev-home&mode=manage&import=1');
            document.body.innerHTML = `
                <section id="docsViewerRoot">
                  <div id="docsViewerHeaderControlsMount" data-docs-viewer-header-controls-mount data-enable-search="true"></div>
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                  <div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>
                  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
                  <p id="docsViewerStatus"></p>
                  <div id="docsViewerBookmarkRow"></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const routeConfig = {
                schema_version: 'docs_viewer_route_config_v1',
                route_id: 'docs-manage',
                route_type: 'manage',
                default_scope_id: 'studio',
                default_doc_id: 'dev-home',
                include_scope_param: true,
                allow_scope_query: true,
                viewer_base_url: '/docs/',
                generated_base_url: 'http://127.0.0.1:8789',
                docs_paths: {
                    index_url: '/assets/data/docs/scopes/studio/index.json',
                    search_index_url: '/assets/data/search/studio/index.json'
                },
                config_urls: {
                    docs_viewer: '/docs-viewer/config/defaults/docs-viewer-config.json',
                    ui_text: '/docs-viewer/config/ui-text/ui-text.json',
                    report_registry: '/assets/data/docs/reports.json'
                },
                access: {
                    allow_management: true,
                    allow_scope_query: true,
                    management_base_url: 'http://127.0.0.1:8789',
                    management_mode_value: 'manage'
                }
            };
            const context = await boot.resolveDocsViewerAppBootContext({
                root,
                document,
                window,
                assetVersion: 'boot-smoke',
                routeConfig
            });
            return {
                routeId: context.routeContext.routeConfig.routeId,
                allowManagement: context.routeContext.access.allowManagement,
                canLoadManagementUi: context.routeContext.access.canLoadManagementUi,
                managementRequested: context.routeContext.access.managementRequested,
                importRequested: context.routeContext.openImportOnLoad,
                managementBaseUrl: context.routeContext.managementBaseUrl,
                manageRowId: context.appShellRefs.managementActions.row?.id || '',
                contextMenuId: context.appShellRefs.managementShell.contextMenu?.id || '',
                metadataModalId: context.appShellRefs.managementShell.metadataModal?.id || '',
                importRootId: context.appShellRefs.managementShell.importRoot?.id || '',
                settingsModalId: context.appShellRefs.managementShell.settingsModal?.id || '',
                manageRowCount: document.querySelectorAll('#docsViewerManageRow').length,
                contextMenuCount: document.querySelectorAll('#docsViewerContextMenu').length
            };
        }"""
    )
    if result != {
        "routeId": "docs-manage",
        "allowManagement": True,
        "canLoadManagementUi": True,
        "managementRequested": True,
        "importRequested": True,
        "managementBaseUrl": "http://127.0.0.1:8789",
        "manageRowId": "docsViewerManageRow",
        "contextMenuId": "docsViewerContextMenu",
        "metadataModalId": "docsViewerMetadataModal",
        "importRootId": "docsHtmlImportRoot",
        "settingsModalId": "docsViewerSettingsModal",
        "manageRowCount": 1,
        "contextMenuCount": 1,
    }:
        raise AssertionError(f"management app boot context contract failed: {result!r}")


def assert_app_boot_start_is_single_start(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const boot = await import('/docs-viewer/runtime/js/docs-viewer-app-boot.js');
            window.history.replaceState({}, '', '/analysis/?doc=analysis');
            document.body.innerHTML = `
                <section id="docsViewerRoot">
                  <div id="docsViewerHeaderControlsMount" data-docs-viewer-header-controls-mount data-enable-search="true"></div>
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                  <p id="docsViewerStatus"></p>
                  <div id="docsViewerBookmarkRow"></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const routeConfig = {
                schema_version: 'docs_viewer_route_config_v1',
                route_id: 'analysis-public',
                route_type: 'public',
                default_scope_id: 'analysis',
                default_doc_id: 'analysis',
                viewer_base_url: '/analysis/',
                docs_paths: {
                    index_url: '/assets/data/docs/scopes/analysis/index.json',
                    search_index_url: '/assets/data/search/analysis/index.json'
                },
                config_urls: {
                    docs_viewer: '/docs-viewer/config/defaults/docs-viewer-public-config.json',
                    ui_text: '/docs-viewer/config/ui-text/ui-text.json',
                    report_registry: '/assets/data/docs/reports.json'
                },
                access: {
                    allow_management: false,
                    allow_scope_query: false,
                    management_base_url: ''
                }
            };
            const first = boot.startDocsViewerApp({ root, document, window, assetVersion: 'boot-smoke', routeConfig });
            const second = boot.startDocsViewerApp({ root, document, window, assetVersion: 'boot-smoke', routeConfig });
            const app = await first;
            if (app && app.initialLoadPromise) await app.initialLoadPromise;
            const handleKeys = Object.keys(app || {}).sort();
            const activeLink = document.querySelector('#docsViewerNav a[aria-current="page"]');
            return {
                samePromise: first === second,
                handleKeys,
                hasBroadRuntimeState: Boolean(app && app.state),
                hasCompositionBridge: Boolean(app && app.appComposition),
                hasSessionBridge: Boolean(app && app.appSession),
                hasManagementBridge: Boolean(app && app.loadManagementController),
                hasRouteWorkflowBridge: Boolean(app && (app.applyCurrentRoute || app.loadIndex || app.loadDoc)),
                hasInitialLoadPromise: Boolean(app && app.initialLoadPromise && typeof app.initialLoadPromise.then === 'function'),
                routeId: app && app.routeContext ? app.routeContext().routeConfig.routeId : '',
                headerRowCount: document.querySelectorAll('.docsViewer__searchRow').length,
                navCount: document.querySelectorAll('#docsViewerNav').length,
                documentShellCount: document.querySelectorAll('.docsViewer__main').length,
                activeDocId: activeLink?.dataset.docId || '',
                activeDocText: activeLink?.textContent.trim() || ''
            };
        }"""
    )
    if result["samePromise"] is not True:
        raise AssertionError(f"app boot did not preserve a single start promise: {result!r}")
    if result["handleKeys"] != ["appShellRefs", "initialLoadPromise", "root", "routeContext"]:
        raise AssertionError(f"app boot returned unexpected runtime handle keys: {result!r}")
    if (
        result["hasBroadRuntimeState"] is not False
        or result["hasCompositionBridge"] is not False
        or result["hasSessionBridge"] is not False
        or result["hasManagementBridge"] is not False
        or result["hasRouteWorkflowBridge"] is not False
    ):
        raise AssertionError(f"app boot exposed retired runtime internals: {result!r}")
    if result["hasInitialLoadPromise"] is not True or result["routeId"] != "analysis-public":
        raise AssertionError(f"app boot did not return the intended runtime contract: {result!r}")
    if result["headerRowCount"] != 1 or result["navCount"] != 1 or result["documentShellCount"] != 1:
        raise AssertionError(f"single-start boot duplicated shell markup: {result!r}")
    if result["activeDocId"] != "analysis" or result["activeDocText"] != "Analysis":
        raise AssertionError(f"single-start boot did not complete initial route load: {result!r}")


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
                'docsViewerInfoToggle',
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
                infoToggleHidden: document.getElementById('docsViewerInfoToggle')?.hidden,
                infoToggleExpanded: document.getElementById('docsViewerInfoToggle')?.getAttribute('aria-expanded') || '',
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
        "infoToggleHidden": True,
        "infoToggleExpanded": "false",
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
                infoToggleCount: document.querySelectorAll('#docsViewerInfoToggle').length,
                bookmarkToggleCount: document.querySelectorAll('#docsViewerBookmarkToggle').length,
                manageRowCount: document.querySelectorAll('#docsViewerManageRow').length,
                editButtonCount: document.querySelectorAll('#docsViewerManageEditButton').length
            };
        }"""
    )
    if result != {
        "documentShellCount": 1,
        "statusPillsCount": 1,
        "infoToggleCount": 1,
        "bookmarkToggleCount": 1,
        "manageRowCount": 1,
        "editButtonCount": 1,
    }:
        raise AssertionError(f"management document shell shape failed: {result!r}")


def assert_management_shell_mount_does_not_shift_document(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            if (!document.querySelector('link[data-docs-viewer-css-smoke]')) {
                await new Promise((resolve, reject) => {
                    const link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = '/docs-viewer/static/css/docs-viewer.css';
                    link.dataset.docsViewerCssSmoke = 'true';
                    link.onload = resolve;
                    link.onerror = reject;
                    document.head.appendChild(link);
                });
            }
            const module = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" class="docsViewer" data-allow-management="true">
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await module.initDocsViewerAppShell({ root, document });
            await new Promise((resolve) => requestAnimationFrame(resolve));
            const indexRect = document.querySelector('[data-docs-viewer-index-panel-mount]').getBoundingClientRect();
            const documentRect = document.querySelector('[data-docs-viewer-document-shell-mount]').getBoundingClientRect();
            const managementMount = document.querySelector('[data-docs-viewer-management-shell-mount]');
            return {
                managementMountDisplay: getComputedStyle(managementMount).display,
                sameRow: Math.abs(indexRect.top - documentRect.top) < 2,
                documentLeftAfterIndex: documentRect.left > indexRect.left,
                contextMenuCount: document.querySelectorAll('#docsViewerContextMenu').length,
                metadataModalCount: document.querySelectorAll('#docsViewerMetadataModal').length
            };
        }"""
    )
    if result != {
        "managementMountDisplay": "contents",
        "sameRow": True,
        "documentLeftAfterIndex": True,
        "contextMenuCount": 1,
        "metadataModalCount": 1,
    }:
        raise AssertionError(f"management shell mount shifted document layout: {result!r}")


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
                    moreHidden: false,
                    infoToggleHidden: false,
                    infoTogglePressed: true,
                    infoToggleLabel: 'Hide document info'
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
                moreHtml: refs.more.innerHTML,
                infoToggleHidden: refs.infoToggle.hidden,
                infoToggleExpanded: refs.infoToggle.getAttribute('aria-expanded'),
                infoToggleLabel: refs.infoToggle.getAttribute('aria-label')
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
                    infoToggleHidden: true,
                    infoTogglePressed: false,
                    infoToggleLabel: 'Show document info',
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
                moreHtml: refs.more.innerHTML,
                infoToggleHidden: refs.infoToggle.hidden,
                infoToggleExpanded: refs.infoToggle.getAttribute('aria-expanded'),
                infoToggleLabel: refs.infoToggle.getAttribute('aria-label')
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
        "infoToggleHidden": False,
        "infoToggleExpanded": "true",
        "infoToggleLabel": "Hide document info",
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
        "infoToggleHidden": True,
        "infoToggleExpanded": "false",
        "infoToggleLabel": "Show document info",
    }:
        raise AssertionError(f"document projection failed: {result!r}")


def assert_info_panel_shell_and_metadata_lifecycle(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const shell = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            const hostedViews = await import('/docs-viewer/runtime/js/docs-viewer-hosted-views.js');
            const access = await import('/docs-viewer/runtime/js/docs-viewer-access.js');
            const infoHost = await import('/docs-viewer/runtime/js/docs-viewer-info-panel-host.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false">
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            const returned = await shell.initDocsViewerAppShell({ root, document });
            const refs = shell.getDocsViewerAppShellInfoPanelRefs({ root, document });
            const publicAccess = access.createDocsViewerAccessProjection({
                routeConfig: { routeType: 'public', access: { allowManagement: false } },
                search: ''
            });
            const registry = hostedViews.registerDocsViewerHostedViews(
                hostedViews.createDocsViewerHostedViewRegistry({ accessProjection: publicAccess }),
                hostedViews.createDocsViewerBuiltInHostedViews().concat([
                    {
                        id: 'details-info',
                        label: 'Details',
                        panel: 'info',
                        access: 'public',
                        availability: 'available',
                        load: () => Promise.resolve({
                            mount: ({ mount }) => { mount.textContent = 'Details view'; },
                            update: ({ mount }) => { mount.textContent = 'Details updated'; },
                            unmount: ({ mount }) => { mount.replaceChildren(); }
                        })
                    },
                    { id: 'disabled-info', label: 'Disabled', panel: 'info', access: 'public', availability: 'disabled' },
                    { id: 'manage-info', label: 'Manage', panel: 'info', access: 'manage', availability: 'available' }
                ])
            );
            const host = infoHost.createDocsViewerInfoPanelHost({
                refs,
                registry,
                project: (projection) => shell.renderDocsViewerAppShellInfoPanelState({ root, refs, projection })
            });
            const context = {
                canonicalUrl: '/docs/?scope=studio&doc=example',
                parentTrail: [{ doc_id: 'parent-doc', title: 'Parent Doc' }],
                selectedDoc: {
                    doc_id: 'example',
                    title: 'Example Doc',
                    summary: 'A compact metadata summary.',
                    scope: 'studio',
                    parent_id: 'parent-doc',
                    added_date: '2026-05-01',
                    last_updated: '2026-05-27',
                    viewable: true,
                    hidden: false,
                    ui_status: 'done'
                },
                statusLabel: 'Done',
                viewerScope: 'studio'
            };
            await host.open('metadata-info', context);
            const openProjection = {
                returnedPanelId: returned.infoPanel && returned.infoPanel.panel && returned.infoPanel.panel.id,
                refPanelId: refs.panel && refs.panel.id,
                panelHidden: refs.panel.hidden,
                rootState: root.dataset.infoPanelState,
                rootLayout: root.dataset.viewerLayout,
                activeViewId: refs.panel.dataset.activeViewId,
                toolbarHidden: refs.toolbar.hidden,
                toolbarButtons: Array.from(refs.toolbar.querySelectorAll('[data-info-panel-view]')).map((button) => ({
                    id: button.dataset.infoPanelView,
                    pressed: button.getAttribute('aria-pressed'),
                    disabled: button.disabled,
                    text: button.textContent
                })),
                title: refs.body.querySelector('.docsViewer__metadataInfoTitle')?.textContent || '',
                routeText: Array.from(refs.body.querySelectorAll('.docsViewer__metadataInfoRow')).find((row) => row.querySelector('dt')?.textContent === 'Route')?.querySelector('a')?.textContent || '',
                rowLabels: Array.from(refs.body.querySelectorAll('.docsViewer__metadataInfoTerm')).map((node) => node.textContent)
            };
            await host.open('details-info', context);
            const switchedProjection = {
                activeViewId: refs.panel.dataset.activeViewId,
                bodyText: refs.body.textContent,
                toolbarButtons: Array.from(refs.toolbar.querySelectorAll('[data-info-panel-view]')).map((button) => ({
                    id: button.dataset.infoPanelView,
                    pressed: button.getAttribute('aria-pressed'),
                    disabled: button.disabled
                }))
            };
            await host.update(Object.assign({}, context, {
                selectedDoc: Object.assign({}, context.selectedDoc, { summary: '' }),
                statusLabel: ''
            }));
            const switchedUpdateText = refs.body.textContent;
            await host.open('metadata-info', Object.assign({}, context, {
                selectedDoc: Object.assign({}, context.selectedDoc, { summary: '' }),
                statusLabel: ''
            }));
            const missingSummary = Array.from(refs.body.querySelectorAll('.docsViewer__metadataInfoRow')).find((row) => row.querySelector('dt')?.textContent === 'Summary')?.querySelector('dd')?.textContent || '';
            await host.close();
            const closedProjection = {
                panelHidden: refs.panel.hidden,
                rootState: root.dataset.infoPanelState,
                bodyChildCount: refs.body.children.length
            };
            await host.open('not-registered', context);
            const missingProjection = {
                panelHidden: refs.panel.hidden,
                statusHidden: refs.status.hidden,
                statusText: refs.status.textContent,
                bodyChildCount: refs.body.children.length
            };
            await host.close();
            await host.open('metadata-info', { selectedDoc: null, viewerScope: 'studio' });
            const emptyText = refs.body.textContent.trim();
            return { openProjection, switchedProjection, switchedUpdateText, missingSummary, closedProjection, missingProjection, emptyText };
        }"""
    )
    if result["openProjection"] != {
        "returnedPanelId": "docsViewerInfoPanel",
        "refPanelId": "docsViewerInfoPanel",
        "panelHidden": False,
        "rootState": "open",
        "rootLayout": "index-document-info",
        "activeViewId": "metadata-info",
        "toolbarHidden": False,
        "toolbarButtons": [
            {"id": "metadata-info", "pressed": "true", "disabled": False, "text": "Metadata info"},
            {"id": "details-info", "pressed": "false", "disabled": False, "text": "Details"},
            {"id": "disabled-info", "pressed": "false", "disabled": True, "text": "Disabled"},
            {"id": "manage-info", "pressed": "false", "disabled": True, "text": "Manage"},
        ],
        "title": "Example Doc",
        "routeText": "/docs/?scope=studio&doc=example",
        "rowLabels": ["Scope", "Summary", "Parent path", "Added", "Updated", "UI status", "Visibility", "Route"],
    }:
        raise AssertionError(f"info panel metadata open projection failed: {result!r}")
    if result["switchedProjection"] != {
        "activeViewId": "details-info",
        "bodyText": "Details view",
        "toolbarButtons": [
            {"id": "metadata-info", "pressed": "false", "disabled": False},
            {"id": "details-info", "pressed": "true", "disabled": False},
            {"id": "disabled-info", "pressed": "false", "disabled": True},
            {"id": "manage-info", "pressed": "false", "disabled": True},
        ],
    }:
        raise AssertionError(f"info panel hosted-view switching failed: {result!r}")
    if result["switchedUpdateText"] != "Details updated":
        raise AssertionError(f"switched info view did not receive update: {result!r}")
    if result["missingSummary"] != "No summary":
        raise AssertionError(f"metadata view did not tolerate missing summary: {result!r}")
    if result["closedProjection"] != {
        "panelHidden": True,
        "rootState": "closed",
        "bodyChildCount": 0,
    }:
        raise AssertionError(f"info panel close projection failed: {result!r}")
    if result["missingProjection"] != {
        "panelHidden": False,
        "statusHidden": False,
        "statusText": "This info view is unavailable.",
        "bodyChildCount": 0,
    }:
        raise AssertionError(f"missing info view should be graceful: {result!r}")
    if result["emptyText"] != "Select a document to see metadata.":
        raise AssertionError(f"metadata empty-selection state failed: {result!r}")


def assert_hosted_view_context_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const context = await import('/docs-viewer/runtime/js/docs-viewer-view-context.js');
            const docsById = new Map([
                ['child-doc', {
                    doc_id: 'child-doc',
                    title: 'Child Doc',
                    parent_id: 'parent-doc',
                    ui_status: 'done'
                }]
            ]);
            const allDocsById = new Map(docsById);
            const payloadCache = new Map([
                ['child-doc', { doc_id: 'child-doc', content_html: '<h1>Child</h1>' }]
            ]);
            const uiStatusByValue = new Map([
                ['done', { label: 'Done', emoji: '✓' }]
            ]);
            const built = context.createDocsViewerHostedViewContext({
                allDocsById,
                buildTrail: () => [
                    { doc_id: 'parent-doc', title: 'Parent Doc' },
                    { doc_id: 'child-doc', title: 'Child Doc' }
                ],
                docsById,
                payloadCache,
                routeAccess: {
                    allowManagement: true,
                    publicReadOnly: false,
                    routeType: 'manage'
                },
                selectedDocId: 'child-doc',
                uiStatusByValue,
                viewerScope: 'studio',
                viewerTargetDocId: (docId) => docId,
                viewerUrl: (docId) => `/docs/?scope=studio&mode=manage&doc=${docId}`
            });
            const missing = context.createDocsViewerHostedViewContext({
                docsById,
                selectedDocId: 'missing-doc',
                viewerScope: 'studio'
            });
            return {
                selectedDocId: built.selectedDoc && built.selectedDoc.doc_id,
                payloadDocId: built.payload && built.payload.doc_id,
                parentTrail: built.parentTrail.map((doc) => doc.doc_id),
                statusLabel: built.statusLabel,
                canonicalUrl: built.canonicalUrl,
                access: built.access,
                viewerScope: built.viewerScope,
                missingSelectedDoc: missing.selectedDoc,
                missingPayload: missing.payload,
                fallbackStatus: context.docsViewerStatusLabel('draft', new Map())
            };
        }"""
    )
    if result != {
        "selectedDocId": "child-doc",
        "payloadDocId": "child-doc",
        "parentTrail": ["parent-doc"],
        "statusLabel": "✓ Done",
        "canonicalUrl": "/docs/?scope=studio&mode=manage&doc=child-doc",
        "access": {
            "allowManagement": True,
            "publicReadOnly": False,
            "routeType": "manage",
        },
        "viewerScope": "studio",
        "missingSelectedDoc": None,
        "missingPayload": None,
        "fallbackStatus": "draft",
    }:
        raise AssertionError(f"hosted-view context contract failed: {result!r}")


def assert_panel_layout_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const shell = await import('/docs-viewer/runtime/js/docs-viewer-app-shell.js');
            const panels = await import('/docs-viewer/runtime/js/docs-viewer-panel-layout.js');
            document.body.innerHTML = `
                <section id="docsViewerRoot" data-allow-management="false">
                  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
                </section>
            `;
            const root = document.getElementById('docsViewerRoot');
            await shell.initDocsViewerAppShell({ root, document });
            const refs = shell.getDocsViewerAppShellRefs({ root, document });
            const values = {
                'dotlineform-docs-viewer-sidebar:studio': 'collapsed',
                'dotlineform-docs-viewer-index-panel:library': 'expanded'
            };
            const storage = {
                getItem: (key) => Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null,
                setItem: (key, value) => { values[key] = value; }
            };
            let available = true;
            const layout = panels.createDocsViewerPanelLayout({
                root,
                storage,
                storageScope: 'studio',
                indexPanelRefs: refs.indexPanel,
                documentShellRefs: refs.documentShell,
                infoPanelRefs: refs.infoPanel,
                panels: {
                    index: { enabled: true, defaultState: 'normal' },
                    document: { enabled: true, defaultView: 'document-host' },
                    info: { enabled: true, defaultView: 'metadata-info' }
                },
                indexPanelAvailable: () => available
            });
            const initialState = layout.indexPanelState();
            layout.renderIndexPanelState();
            const initialProjection = {
                state: root.dataset.indexPanelState,
                sidebar: root.dataset.sidebarState,
                toggleLabel: refs.indexPanel.sidebarToggle.getAttribute('aria-label')
            };
            const toggledState = layout.toggleIndexPanelState();
            const storedStudio = values['dotlineform-docs-viewer-index-panel:studio'];
            layout.setStorageScope('library');
            layout.renderIndexPanelState();
            const libraryProjection = {
                state: root.dataset.indexPanelState,
                sidebar: root.dataset.sidebarState,
                expandHidden: refs.indexPanel.sidebarExpand.hidden
            };
            available = false;
            const unavailableToggleState = layout.toggleIndexPanelState();
            layout.renderIndexPanelState();
            refs.documentShell.more.innerHTML = '<button>More</button>';
            layout.projectDocumentShell({
                contentHidden: true,
                resultsStatusText: 'Recent docs',
                resultsStatusHidden: false,
                resultsHidden: false,
                moreHidden: false
            });
            const recentProjection = {
                contentHidden: refs.documentShell.content.hidden,
                resultsStatusText: refs.documentShell.resultsStatus.textContent,
                resultsStatusHidden: refs.documentShell.resultsStatus.hidden,
                resultsHidden: refs.documentShell.results.hidden,
                moreHidden: refs.documentShell.more.hidden,
                moreHtml: refs.documentShell.more.innerHTML
            };
            layout.projectDocumentShell({ moreHidden: true, clearMore: true });
            layout.projectInfoPanel({
                activeViewId: 'metadata-info',
                label: 'Document metadata',
                title: 'Info',
                visible: true
            });
            const openInfoProjection = {
                panelHidden: refs.infoPanel.panel.hidden,
                infoState: root.dataset.infoPanelState,
                layout: root.dataset.viewerLayout,
                activeViewId: refs.infoPanel.panel.dataset.activeViewId
            };
            layout.projectInfoPanel({ visible: false });
            const closedInfoProjection = {
                panelHidden: refs.infoPanel.panel.hidden,
                infoState: root.dataset.infoPanelState,
                layout: root.dataset.viewerLayout
            };
            return {
                initialState,
                initialProjection,
                toggledState,
                storedStudio,
                libraryState: layout.indexPanelState(),
                libraryProjection,
                unavailableToggleState,
                unavailableProjectedState: root.dataset.indexPanelState,
                recentProjection,
                moreAfterClear: refs.documentShell.more.innerHTML,
                openInfoProjection,
                closedInfoProjection
            };
        }"""
    )
    if result != {
        "initialState": "collapsed",
        "initialProjection": {
            "state": "collapsed",
            "sidebar": "collapsed",
            "toggleLabel": "Restore index panel",
        },
        "toggledState": "normal",
        "storedStudio": "normal",
        "libraryState": "expanded",
        "libraryProjection": {
            "state": "expanded",
            "sidebar": "expanded",
            "expandHidden": True,
        },
        "unavailableToggleState": "expanded",
        "unavailableProjectedState": "normal",
        "recentProjection": {
            "contentHidden": True,
            "resultsStatusText": "Recent docs",
            "resultsStatusHidden": False,
            "resultsHidden": False,
            "moreHidden": False,
            "moreHtml": "<button>More</button>",
        },
        "moreAfterClear": "",
        "openInfoProjection": {
            "panelHidden": False,
            "infoState": "open",
            "layout": "index-document-info",
            "activeViewId": "metadata-info",
        },
        "closedInfoProjection": {
            "panelHidden": True,
            "infoState": "closed",
            "layout": "index-document",
        },
    }:
        raise AssertionError(f"panel layout contract failed: {result!r}")


def assert_view_state_and_hosted_view_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const viewStateModule = await import('/docs-viewer/runtime/js/docs-viewer-view-state.js');
            const hostedViews = await import('/docs-viewer/runtime/js/docs-viewer-hosted-views.js');
            const access = await import('/docs-viewer/runtime/js/docs-viewer-access.js');
            const publicAccess = access.createDocsViewerAccessProjection({
                routeConfig: {
                    routeType: 'public',
                    access: {
                        allowManagement: false,
                        allowScopeQuery: false,
                        managementModeValue: 'manage'
                    }
                },
                search: ''
            });
            const registry = hostedViews.registerDocsViewerHostedViews(
                hostedViews.createDocsViewerHostedViewRegistry({ accessProjection: publicAccess }),
                hostedViews.createDocsViewerBuiltInHostedViews().concat([
                    { id: 'manage-source', label: 'Source', panel: 'document', access: 'manage', availability: 'available' },
                    { id: 'disabled-info', label: 'Info', panel: 'info', access: 'public', availability: 'disabled' }
                ])
            );
            const state = viewStateModule.createDocsViewerViewState({
                routeId: 'library-public',
                indexPanelState: 'expanded',
                panels: {
                    index: { enabled: true, defaultState: 'normal' },
                    document: { enabled: true, defaultView: 'document-host' },
                    info: { enabled: false, defaultView: 'metadata-info' }
                }
            });
            const projected = viewStateModule.projectDocsViewerViewState(state, {
                indexProjection: { activeState: 'expanded', documentPaneVisible: false }
            });
            const updated = viewStateModule.updateDocsViewerViewState(state, {
                indexPanelState: 'normal',
                documentViewId: 'search-results',
                infoMounted: true
            });
            const updatedProjection = viewStateModule.projectDocsViewerViewState(updated, {
                indexProjection: { activeState: 'normal', documentPaneVisible: true }
            });
            return {
                projected,
                updatedProjection,
                documentHost: registry.resolve('document-host'),
                missing: registry.resolve('not-registered'),
                manageSource: registry.resolve('manage-source'),
                disabledInfo: registry.resolve('disabled-info'),
                metadataInfo: registry.resolve('metadata-info'),
                registeredIds: registry.list().map((view) => `${view.id}:${view.available ? 'yes' : view.unavailableReason}`).sort(),
                infoViewIds: hostedViews.listDocsViewerHostedViewsForPanel(registry, 'info').map((view) => `${view.id}:${view.available ? 'yes' : view.unavailableReason}`).sort(),
                documentViewIds: registry.listByPanel('document').map((view) => view.id).sort()
            };
        }"""
    )
    if result["projected"] != {
        "index": {
            "panel": "index",
            "visible": True,
            "mounted": True,
            "state": "expanded",
            "activeViewId": "index-tree",
        },
        "document": {
            "panel": "document",
            "visible": False,
            "mounted": True,
            "activeViewId": "document-host",
        },
        "info": {
            "panel": "info",
            "visible": False,
            "mounted": False,
            "activeViewId": "metadata-info",
        },
    }:
        raise AssertionError(f"view state expanded projection failed: {result!r}")
    if result["updatedProjection"]["document"]["visible"] is not True:
        raise AssertionError(f"view state did not restore document panel: {result!r}")
    if result["updatedProjection"]["document"]["activeViewId"] != "search-results":
        raise AssertionError(f"view state did not update active document view: {result!r}")
    if result["documentHost"]["available"] is not True or result["documentHost"]["registered"] is not True:
        raise AssertionError(f"document hosted view should resolve as available: {result!r}")
    if result["missing"] != {
        "id": "not-registered",
        "view": None,
        "registered": False,
        "available": False,
        "reason": "missing",
    }:
        raise AssertionError(f"missing hosted view should be graceful: {result!r}")
    if result["manageSource"]["reason"] != "access" or result["disabledInfo"]["reason"] != "disabled":
        raise AssertionError(f"hosted view access/disabled states failed: {result!r}")
    if result["metadataInfo"]["available"] is not True or result["metadataInfo"]["registered"] is not True:
        raise AssertionError(f"built-in metadata info view should be public and available: {result!r}")
    if "metadata-info:yes" not in result["registeredIds"] or "index-tree:yes" not in result["registeredIds"]:
        raise AssertionError(f"hosted view registry listing lost built-in views: {result!r}")
    if result["infoViewIds"] != ["disabled-info:disabled", "metadata-info:yes"]:
        raise AssertionError(f"hosted view panel listing changed: {result!r}")
    if "document-host" not in result["documentViewIds"] or "search-results" not in result["documentViewIds"]:
        raise AssertionError(f"document hosted view panel listing changed: {result!r}")


def assert_route_workflow_contract(page: Page, base_url: str) -> None:
    result = page.evaluate(
        """async ({ baseUrl }) => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-route-workflow.js');
            const root = document.createElement('section');
            document.body.innerHTML = '';
            document.body.appendChild(root);
            const searchInput = document.createElement('input');
            root.appendChild(searchInput);
            const calls = [];
            const fetchCalls = [];
            const state = {
                allDocs: [],
                allDocsById: new Map(),
                docs: [],
                docsById: new Map(),
                scopeConfigsById: new Map(),
                childrenByParent: new Map(),
                payloadCache: new Map(),
                selectedDocId: '',
                expandedDocIds: new Set(),
                requestId: 0,
                searchQuery: '',
                searchVisibleCount: 50,
                searchRouteActive: false,
                recentModeActive: false,
                managementMode: false,
                nonLoadableDocIds: new Set(),
                manageOnlyTreeRootIds: new Set(),
                showUpdatedDate: true,
                reloadNonce: '',
                reloadExpectedDocId: ''
            };
            const payloads = {
                '/index.json': {
                    viewer_options: {
                        non_loadable_doc_ids: ['folder'],
                        manage_only_tree_root_ids: ['private'],
                        show_updated_date: false
                    },
                    docs: [
                        { doc_id: 'folder', title: 'Folder', parent_id: '', sort_order: 1, content_url: '/folder.json', viewable: true },
                        { doc_id: 'child', title: 'Child', parent_id: 'folder', sort_order: 1, content_url: '/child.json', viewable: true },
                        { doc_id: 'intro', title: 'Intro', parent_id: '', sort_order: 2, content_url: '/intro.json', viewable: true }
                    ]
                },
                '/child.json': { content_html: '<h1>Child</h1>' },
                '/intro.json': { content_html: '<h1>Intro</h1>' }
            };
            function applyDocVisibility() {
                state.allDocsById = new Map(state.allDocs.map((doc) => [doc.doc_id, doc]));
                state.docs = state.allDocs.slice();
                state.docsById = new Map(state.docs.map((doc) => [doc.doc_id, doc]));
                const children = new Map([['', []]]);
                state.docs.forEach((doc) => {
                    const parent = doc.parent_id || '';
                    if (!children.has(parent)) children.set(parent, []);
                    children.get(parent).push(doc);
                });
                state.childrenByParent = children;
            }
            function resolveLoadableDocId(docId) {
                return docId === 'folder' ? 'child' : state.docsById.has(docId) ? docId : '';
            }
            function defaultDocId() {
                return 'intro';
            }
            function responseFor(url) {
                const path = new URL(url, window.location.origin).pathname;
                fetchCalls.push(path);
                const payload = payloads[path];
                if (!payload) return Promise.resolve({ ok: false, status: 404, json: async () => ({}) });
                return Promise.resolve({ ok: true, status: 200, json: async () => payload });
            }
            function stateDomain(fields) {
                const domain = {};
                fields.forEach((fieldName) => {
                    Object.defineProperty(domain, fieldName, {
                        enumerable: true,
                        get: () => state[fieldName],
                        set: (value) => { state[fieldName] = value; }
                    });
                });
                return domain;
            }
            const workflow = module.initDocsViewerRouteWorkflow({
                allowManagement: () => false,
                allowScopeQuery: () => false,
                applyDocVisibility,
                cancelSearchDebounce: () => calls.push('cancel-search'),
                clearManagementMessageForDocChange: (docId) => calls.push(`clear:${docId}`),
                content: document.createElement('div'),
                defaultDocId,
                defaultRouteDocId: () => 'folder',
                expandTrail: (docId) => calls.push(`expand:${docId}`),
                handleManagementRootClick: () => false,
                handleMissingDoc: () => calls.push('missing'),
                handlePayloadError: (error) => calls.push(`payload-error:${error.message}`),
                generatedData: {
                    readDocsIndex: ({ indexUrl }) => responseFor(indexUrl).then((response) => response.json()),
                    readDocumentPayload: (doc) => responseFor(doc.content_url).then((response) => response.json())
                },
                hasActiveQuery: (query) => {
                    const value = typeof query === 'string' ? query : state.searchQuery;
                    return Boolean(String(value || '').trim());
                },
                hideContextMenu: () => calls.push('hide-context'),
                hideDocPane: () => calls.push('hide-doc-pane'),
                includeScopeParam: () => false,
                indexUrl: () => '/index.json',
                managementModeValue: 'manage',
                renderBookmarkUi: () => calls.push('bookmarks'),
                renderDocLoadingState: (doc) => calls.push(`loading:${doc.doc_id}`),
                renderManagementUi: () => calls.push('management-ui'),
                renderPayload: (doc, payload, hash) => calls.push(`payload:${doc.doc_id}:${hash}:${payload.content_html}`),
                renderSearchMode: () => calls.push(`search:${state.searchQuery}`),
                renderSidebar: () => calls.push('sidebar'),
                resolveLoadableDocId,
                root,
                routeSession: {
                    get managementMode() { return state.managementMode; },
                    set managementMode(value) { state.managementMode = Boolean(value); }
                },
                routeScopeFromUrl: () => 'library',
                routeViewerBaseUrl: () => '/docs/',
                scopeConfig: stateDomain(['scopeConfigsById']),
                documentIndex: stateDomain([
                    'allDocs',
                    'docs',
                    'docsById',
                    'expandedDocIds',
                    'nonLoadableDocIds',
                    'manageOnlyTreeRootIds',
                    'showUpdatedDate'
                ]),
                selectedDocument: stateDomain([
                    'selectedDocId',
                    'payloadCache',
                    'requestId',
                    'reloadNonce',
                    'reloadExpectedDocId'
                ]),
                searchRecent: stateDomain([
                    'searchQuery',
                    'searchVisibleCount',
                    'searchRouteActive',
                    'recentModeActive'
                ]),
                searchBatchSize: 50,
                searchInput,
                setRecentModeActive: (active) => { state.recentModeActive = Boolean(active); calls.push(`recent:${active}`); },
                statusCommands: {
                    setStatus: (message, isError) => calls.push(`status:${message}:${Boolean(isError)}`),
                    startBusy: () => {
                        calls.push('busy-start');
                        return () => calls.push('busy-stop');
                    }
                },
                syncHiddenVisibilityForRequestedDoc: () => calls.push('sync-hidden'),
                updateInfoPanel: () => calls.push('info'),
                viewerBaseUrl: () => '/library/',
                viewerPathname: () => '/library/',
                viewerScope: () => 'library',
                window
            });

            history.replaceState(null, '', `${baseUrl}/library/?doc=folder&q=find&mode=manage#part`);
            const routeCommands = workflow.commands;
            await routeCommands.loadIndex();
            const afterIndexUrl = location.pathname + location.search + location.hash;
            const afterIndex = {
                selectedDocId: state.selectedDocId,
                searchQuery: state.searchQuery,
                searchInput: searchInput.value,
                managementMode: state.managementMode,
                nonLoadable: Array.from(state.nonLoadableDocIds),
                manageOnly: Array.from(state.manageOnlyTreeRootIds),
                showUpdatedDate: state.showUpdatedDate
            };

            history.replaceState(null, '', `${baseUrl}/library/?doc=missing`);
            routeCommands.applyCurrentRoute({ historyMode: 'replace', hash: '' });
            const afterMissingUrl = location.pathname + location.search + location.hash;

            await routeCommands.loadDoc('child', { historyMode: 'push', hash: 'payload-hash' });
            const afterPayloadUrl = location.pathname + location.search + location.hash;
            const cachedChild = state.payloadCache.get('child')?.content_html || '';

            root.innerHTML = '<a id="introLink" href="/library/?doc=intro#intro-hash">Intro</a>';
            workflow.bindRouteLinks();
            document.getElementById('introLink').dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, button: 0 }));
            await Promise.resolve();
            await Promise.resolve();
            const afterLinkUrl = location.pathname + location.search + location.hash;

            workflow.bindPopstate();
            history.replaceState(null, '', `${baseUrl}/library/?doc=child#back-hash`);
            window.dispatchEvent(new PopStateEvent('popstate', { state: { docId: 'child' } }));
            await Promise.resolve();
            await Promise.resolve();
            const afterPopstateUrl = location.pathname + location.search + location.hash;

            return {
                afterIndex,
                afterIndexUrl,
                afterMissingUrl,
                afterPayloadUrl,
                afterLinkUrl,
                afterPopstateUrl,
                cachedChild,
                calls,
                fetchCalls
            };
        }""",
        {"baseUrl": base_url},
    )
    if result["afterIndexUrl"] != "/library/?doc=child&q=find#part":
        raise AssertionError(f"route workflow did not canonicalize public search URL: {result!r}")
    if result["afterIndex"] != {
        "selectedDocId": "child",
        "searchQuery": "find",
        "searchInput": "find",
        "managementMode": False,
        "nonLoadable": ["folder"],
        "manageOnly": ["private"],
        "showUpdatedDate": False,
    }:
        raise AssertionError(f"route workflow index/current-doc state changed unexpectedly: {result!r}")
    if result["afterMissingUrl"] != "/library/?doc=missing" or "missing" not in result["calls"]:
        raise AssertionError(f"route workflow missing-doc handling failed: {result!r}")
    if result["afterPayloadUrl"] != "/library/?doc=child#payload-hash" or result["cachedChild"] != "<h1>Child</h1>":
        raise AssertionError(f"route workflow payload load/history failed: {result!r}")
    if result["afterLinkUrl"] != "/library/?doc=intro#intro-hash":
        raise AssertionError(f"route workflow link interception failed: {result!r}")
    if result["afterPopstateUrl"] != "/library/?doc=child#back-hash":
        raise AssertionError(f"route workflow popstate handling changed URL unexpectedly: {result!r}")
    if "/index.json" not in result["fetchCalls"] or "/child.json" not in result["fetchCalls"] or "/intro.json" not in result["fetchCalls"]:
        raise AssertionError(f"route workflow did not hand off expected fetches: {result!r}")


def assert_search_controller_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-search-controller.js');
            document.body.innerHTML = `
                <button id="recent" type="button"></button>
                <input id="search" />
                <p id="status"></p>
                <ol id="results"></ol>
                <div id="more"></div>
            `;
            const recentButton = document.getElementById('recent');
            const searchInput = document.getElementById('search');
            const resultsStatus = document.getElementById('status');
            const results = document.getElementById('results');
            const more = document.getElementById('more');
            const calls = [];
            const routeCalls = [];
            const paneCalls = [];
            const routeWorkflow = {
                applyCurrentRoute: (options) => routeCalls.push(`apply:${options.historyMode}:${options.hash || ''}`),
                resolveDocId: () => ({ docId: 'intro' }),
                setHistory: (docId, hash, query, mode) => routeCalls.push(`history:${docId}:${hash || ''}:${query || ''}:${mode}`),
                viewerUrl: (docId, hash, query) => `/docs/?doc=${docId}${query ? `&q=${encodeURIComponent(query)}` : ''}${hash ? `#${hash}` : ''}`
            };
            const documentIndex = {
                docs: [
                    { doc_id: 'intro', title: 'Intro Guide', parent_id: '', added_date: '2026-05-27', viewable: true },
                    { doc_id: 'second', title: 'Second Guide', parent_id: 'intro', added_date: '2026-05-26', viewable: true },
                    { doc_id: 'hidden', title: 'Hidden Guide', parent_id: '', added_date: '2026-05-28', viewable: false }
                ],
                docsById: new Map([
                    ['intro', { doc_id: 'intro', title: 'Intro Guide', parent_id: '', added_date: '2026-05-27', viewable: true }],
                    ['second', { doc_id: 'second', title: 'Second Guide', parent_id: 'intro', added_date: '2026-05-26', viewable: true }]
                ])
            };
            const selectedDocument = {
                selectedDocId: 'intro'
            };
            const searchRecent = {
                searchEntries: [
                    {
                        kind: 'doc',
                        id: 'intro',
                        title: 'Intro Guide',
                        displayMeta: '2026-05-27',
                        parentTitle: '',
                        lastUpdated: '2026-05-27',
                        searchTerms: ['guide'],
                        searchText: 'intro guide',
                        titleNorm: 'intro guide',
                        idNorm: 'intro',
                        titleTokens: ['intro', 'guide'],
                        parentTitleNorm: ''
                    },
                    {
                        kind: 'doc',
                        id: 'second',
                        title: 'Second Guide',
                        displayMeta: '2026-05-26 • Intro Guide',
                        parentTitle: 'Intro Guide',
                        lastUpdated: '2026-05-26',
                        searchTerms: ['guide'],
                        searchText: 'second guide intro',
                        titleNorm: 'second guide',
                        idNorm: 'second',
                        titleTokens: ['second', 'guide'],
                        parentTitleNorm: 'intro guide'
                    }
                ],
                searchLoaded: true,
                searchRequestPromise: null,
                searchQuery: 'guide',
                searchVisibleCount: 1,
                searchRouteActive: false,
                recentModeActive: false,
                recentLimit: 2
            };
            const controller = module.initDocsViewerSearchController({
                generatedData: {
                    readSearchIndex: () => Promise.resolve({ entries: [] })
                },
                hasActiveQuery: (query) => Boolean(String(typeof query === 'string' ? query : searchRecent.searchQuery || '').trim()),
                hideContextMenu: () => calls.push('hide-context'),
                documentIndex,
                more,
                paneCommands: {
                    hideDocPane: () => paneCalls.push('hide-doc'),
                    showRecentPane: () => paneCalls.push('recent-pane'),
                    showSearchPane: () => paneCalls.push('search-pane')
                },
                recentButton,
                results,
                resultsStatus,
                routeCommands: module.createDocsViewerSearchRouteCommands({
                    defaultDocId: () => 'intro',
                    routeCommands: routeWorkflow,
                    viewerTargetDocId: (docId) => docId
                }),
                searchBatchSize: 1,
                searchDebounceMs: 0,
                searchRecent,
                searchIndexUrl: () => '/search.json',
                searchInput,
                selectedDocument,
                setRecentModeActive: (active) => {
                    searchRecent.recentModeActive = Boolean(active);
                    calls.push(`recent:${Boolean(active)}`);
                },
                setStatus: (message, isError) => calls.push(`status:${message}:${Boolean(isError)}`),
                startBusy: () => {
                    calls.push('busy-start');
                    return () => calls.push('busy-stop');
                },
                viewerScope: () => 'studio'
            });
            controller.bind();
            controller.renderSearchMode();
            const firstSearch = {
                status: resultsStatus.textContent,
                resultCount: results.querySelectorAll('li').length,
                moreHidden: more.hidden,
                firstHref: results.querySelector('a')?.getAttribute('href') || ''
            };
            more.querySelector('button[data-role="more"]').click();
            const afterMore = {
                status: resultsStatus.textContent,
                resultCount: results.querySelectorAll('li').length,
                moreHidden: more.hidden
            };
            recentButton.click();
            const afterRecent = {
                status: resultsStatus.textContent,
                resultCount: results.querySelectorAll('li').length,
                recentModeActive: searchRecent.recentModeActive,
                query: searchRecent.searchQuery,
                input: searchInput.value
            };
            searchInput.value = 'guide';
            searchInput.dispatchEvent(new InputEvent('input', { bubbles: true }));
            await new Promise((resolve) => setTimeout(resolve, 10));
            searchRecent.searchRouteActive = true;
            searchInput.value = '';
            searchInput.dispatchEvent(new InputEvent('input', { bubbles: true }));
            return {
                firstSearch,
                afterMore,
                afterRecent,
                calls,
                routeCalls,
                paneCalls,
                finalQuery: searchRecent.searchQuery,
                finalRouteActive: searchRecent.searchRouteActive
            };
        }"""
    )
    if result["firstSearch"] != {
        "status": "Showing 1 of 2 results",
        "resultCount": 1,
        "moreHidden": False,
        "firstHref": "/docs/?doc=intro",
    }:
        raise AssertionError(f"search controller initial render changed: {result!r}")
    if result["afterMore"] != {
        "status": "2 results",
        "resultCount": 2,
        "moreHidden": True,
    }:
        raise AssertionError(f"search controller more-results behavior changed: {result!r}")
    if result["afterRecent"] != {
        "status": "2 recently added docs",
        "resultCount": 2,
        "recentModeActive": True,
        "query": "",
        "input": "",
    }:
        raise AssertionError(f"recent-mode controller behavior changed: {result!r}")
    expected_route_calls = [
        "history:intro:::push",
        "history:intro::guide:push",
        "apply:none:",
        "history:intro:::replace",
        "apply:none:",
    ]
    if result["routeCalls"] != expected_route_calls:
        raise AssertionError(f"search controller route handoff changed: {result!r}")
    if "search-pane" not in result["paneCalls"] or "recent-pane" not in result["paneCalls"]:
        raise AssertionError(f"search controller pane handoff changed: {result!r}")
    if result["finalQuery"] != "" or result["finalRouteActive"] is not False:
        raise AssertionError(f"search controller clear-route state changed: {result!r}")


def assert_bookmark_controller_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-bookmarks.js');
            document.body.innerHTML = `
                <div id="bookmarkRow"></div>
                <button id="bookmarkToggle" type="button"></button>
                <input id="search" value="guide" />
            `;
            const bookmarkRow = document.getElementById('bookmarkRow');
            const bookmarkToggle = document.getElementById('bookmarkToggle');
            const searchInput = document.getElementById('search');
            const calls = [];
            const bookmarks = {
                bookmarks: [
                    {
                        key: 'library::intro',
                        scope: 'library',
                        doc_id: 'intro',
                        label: 'Intro bookmark',
                        default_title: 'Intro',
                        created_at_utc: '2026-05-27T00:00:00.000Z',
                        updated_at_utc: '2026-05-27T00:00:00.000Z',
                        order: 1
                    },
                    {
                        key: 'library::second',
                        scope: 'library',
                        doc_id: 'second',
                        label: 'Second bookmark',
                        default_title: 'Second',
                        created_at_utc: '2026-05-27T00:00:01.000Z',
                        updated_at_utc: '2026-05-27T00:00:01.000Z',
                        order: 2
                    }
                ],
                bookmarksLoaded: true,
                bookmarkSupport: true,
                editingBookmarkKey: '',
                pendingBookmarkFocusKey: ''
            };
            const documentIndex = {
                docsById: new Map([
                    ['intro', { doc_id: 'intro', title: 'Intro' }],
                    ['second', { doc_id: 'second', title: 'Second' }]
                ])
            };
            const searchRecent = {
                searchQuery: 'guide',
                searchVisibleCount: 10,
                searchRouteActive: false
            };
            const selectedDocument = {
                selectedDocId: 'intro'
            };
            const routeWorkflow = {
                loadDoc: (docId, options) => {
                    calls.push(`load:${docId}:${options.historyMode}:${options.hash || ''}`);
                    return Promise.resolve(null);
                }
            };
            const controller = module.initDocsViewerBookmarks({
                bookmarks,
                bookmarkRow,
                bookmarkScope: () => 'library',
                bookmarkToggle,
                cssEscape: (value) => String(value).replace(/["\\\\]/g, '\\\\$&'),
                dbName: 'smoke',
                dbVersion: 1,
                documentIndex,
                hideContextMenu: () => calls.push('hide-context'),
                renderStatusPills: () => calls.push('status-pills'),
                routeCommands: module.createDocsViewerBookmarkRouteCommands({
                    routeCommands: routeWorkflow
                }),
                searchRecent,
                searchResetCommand: {
                    resetForBookmarkOpen: () => {
                        calls.push('reset-search');
                        searchRecent.searchQuery = '';
                        searchRecent.searchVisibleCount = 50;
                        searchInput.value = '';
                    }
                },
                selectedDocument,
                setStatus: (message, isError) => calls.push(`status:${message}:${Boolean(isError)}`),
                storeName: 'favorites'
            });
            controller.bind();
            controller.renderUi();
            const initial = {
                toggleHidden: bookmarkToggle.hidden,
                toggleText: bookmarkToggle.textContent,
                togglePressed: bookmarkToggle.getAttribute('aria-pressed'),
                rowHidden: bookmarkRow.hidden,
                rowCount: bookmarkRow.querySelectorAll('[data-bookmark-key]').length,
                activeOpen: bookmarkRow.querySelector('[data-bookmark-open="intro"]')?.getAttribute('aria-current') || ''
            };
            bookmarkRow.querySelector('[data-bookmark-open="second"]').click();
            const afterOpen = {
                query: searchRecent.searchQuery,
                visibleCount: searchRecent.searchVisibleCount,
                input: searchInput.value
            };
            bookmarkRow.querySelector('[data-bookmark-open="second"]').dispatchEvent(
                new MouseEvent('contextmenu', { bubbles: true, cancelable: true })
            );
            const afterRenameStart = {
                editingKey: bookmarks.editingBookmarkKey,
                inputCount: bookmarkRow.querySelectorAll('[data-bookmark-input="library::second"]').length
            };
            return {
                initial,
                afterOpen,
                afterRenameStart,
                calls
            };
        }"""
    )
    if result["initial"] != {
        "toggleHidden": False,
        "toggleText": "★",
        "togglePressed": "true",
        "rowHidden": False,
        "rowCount": 2,
        "activeOpen": "page",
    }:
        raise AssertionError(f"bookmark controller render hooks changed: {result!r}")
    if result["afterOpen"] != {"query": "", "visibleCount": 50, "input": ""}:
        raise AssertionError(f"bookmark controller route handoff did not reset search state: {result!r}")
    if result["afterRenameStart"] != {"editingKey": "library::second", "inputCount": 1}:
        raise AssertionError(f"bookmark controller rename state changed: {result!r}")
    if result["calls"][:3] != ["status-pills", "reset-search", "load:second:push:"]:
        raise AssertionError(f"bookmark controller callbacks changed: {result!r}")


def assert_document_and_sidebar_controller_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const documentModule = await import('/docs-viewer/runtime/js/docs-viewer-document-controller.js');
            const sidebarModule = await import('/docs-viewer/runtime/js/docs-viewer-sidebar.js');
            document.body.innerHTML = `
                <nav id="nav"></nav>
                <section id="meta" hidden>
                  <p id="path"></p>
                  <p id="updated"></p>
                  <p id="summary"></p>
                </section>
                <main id="content"></main>
                <ol id="results"></ol>
                <div id="more"></div>
            `;
            const calls = [];
            const docs = [
                { doc_id: 'intro', title: 'Intro', parent_id: '', sort_order: 1, last_updated: '2026-05-28', viewable: true },
                { doc_id: 'child', title: 'Child', parent_id: 'intro', sort_order: 1, summary: 'Child summary', viewable: true },
                { doc_id: 'hidden', title: 'Hidden', parent_id: '', sort_order: 2, hidden: true, viewable: false }
            ];
            const documentIndex = {
                docs,
                docsById: new Map(docs.map((doc) => [doc.doc_id, doc])),
                childrenByParent: new Map([
                    ['', [docs[0], docs[2]]],
                    ['intro', [docs[1]]]
                ]),
                expandedDocIds: new Set(),
                statusForIndexDoc: (doc) => doc.doc_id === 'intro' ? { emoji: 'ok' } : null,
                viewerTargetDocId: (docId) => docId === 'intro' ? 'child' : docId
            };
            const selectedDocument = {
                selectedDocId: ''
            };
            const scopeConfig = {
                scopeConfigs: [{ scope_id: 'studio', indexUrl: '/assets/data/docs/scopes/studio/index.json' }],
                scopeConfigsById: new Map([
                    ['studio', { scope_id: 'studio', indexUrl: '/assets/data/docs/scopes/studio/index.json' }]
                ]),
                managementText: {
                    metadataHiddenLabel: 'hidden',
                    docHiddenEmoji: 'H'
                },
                showUpdatedDate: true
            };
            const sidebar = sidebarModule.initDocsViewerSidebarRenderer({
                canDragCurrentDoc: () => false,
                documentIndex,
                meta: document.getElementById('meta'),
                nav: document.getElementById('nav'),
                pathEl: document.getElementById('path'),
                renderBookmarkToggle: () => calls.push('bookmark-toggle'),
                renderStatusPills: () => calls.push('status-pills'),
                scopeConfig,
                selectedDocument,
                statusForIndexDoc: documentIndex.statusForIndexDoc,
                summaryEl: document.getElementById('summary'),
                updateNavDragState: () => calls.push('drag-state'),
                updatedEl: document.getElementById('updated'),
                viewerTargetDocId: documentIndex.viewerTargetDocId,
                viewerUrl: (docId) => `/docs/?doc=${docId}`
            });
            sidebar.expandTrail('child');
            sidebar.renderSidebar();

            const documentController = documentModule.initDocsViewerDocumentController({
                allowManagement: false,
                checkGeneratedDataReadCapability: () => Promise.resolve(false),
                clearResultsStatus: () => calls.push('clear-results'),
                content: document.getElementById('content'),
                generatedData: {
                    readScopeIndex: ({ viewerScope }) => Promise.resolve({ viewerScope }),
                    readReferencesIndex: ({ viewerScope }) => Promise.resolve({ viewerScope }),
                    readReferenceTarget: ({ targetSlug }) => Promise.resolve({ targetSlug })
                },
                hasActiveQuery: () => false,
                managementBaseUrl: () => '',
                meta: document.getElementById('meta'),
                more: document.getElementById('more'),
                projectDocumentShell: (projection) => calls.push(`shell:${Object.keys(projection).sort().join(',')}`),
                renderBookmarkToggle: () => calls.push('bookmark-toggle'),
                renderBookmarkUi: () => calls.push('bookmark-ui'),
                renderManagementUi: () => calls.push('management-ui'),
                renderMeta: sidebar.renderMeta,
                renderSearchMode: () => calls.push('search-mode'),
                renderSidebar: sidebar.renderSidebar,
                renderStatusPills: () => calls.push('status-pills'),
                reportRegistryUrl: () => '/assets/data/docs/reports.json',
                results: document.getElementById('results'),
                routeSession: { managementMode: false },
                scopeConfig,
                selectedDocument,
                setRecentModeActive: (active) => calls.push(`recent:${Boolean(active)}`),
                statusCommands: {
                    closeStatusMenu: () => calls.push('close-status-menu'),
                    setStatus: (message, isError) => calls.push(`status:${message}:${Boolean(isError)}`)
                },
                viewerScope: () => 'studio',
                viewerUrlForScope: (scope, docId) => `/${scope}/?doc=${docId}`
            });
            documentController.renderPayload(docs[1], { content_html: '<h1 id="part">Child</h1>' }, 'part');
            await new Promise((resolve) => requestAnimationFrame(resolve));
            return {
                selectedDocId: selectedDocument.selectedDocId,
                expanded: Array.from(documentIndex.expandedDocIds),
                activeHref: document.querySelector('.docsViewer__navLink.is-active')?.getAttribute('href') || '',
                rootHref: document.querySelector('[data-doc-id="intro"]')?.getAttribute('href') || '',
                hiddenTitle: document.querySelector('[data-doc-id="hidden"]')?.getAttribute('title') || '',
                contentHtml: document.getElementById('content').innerHTML,
                pathText: document.getElementById('path').textContent,
                summaryText: document.getElementById('summary').textContent,
                metaHidden: document.getElementById('meta').hidden,
                calls
            };
        }"""
    )
    if result["selectedDocId"] != "child":
        raise AssertionError(f"document controller did not update selected-document domain: {result!r}")
    if result["expanded"] != ["intro"]:
        raise AssertionError(f"sidebar renderer did not use document-index expansion state: {result!r}")
    if result["activeHref"] != "/docs/?doc=child" or result["rootHref"] != "/docs/?doc=child":
        raise AssertionError(f"sidebar renderer route URL projection changed: {result!r}")
    if result["hiddenTitle"] != "hidden":
        raise AssertionError(f"sidebar renderer management text projection changed: {result!r}")
    if result["contentHtml"] != '<h1 id="part">Child</h1>':
        raise AssertionError(f"document controller payload render changed: {result!r}")
    if result["pathText"] != "Intro" or result["summaryText"] != "Child summary" or result["metaHidden"] is not False:
        raise AssertionError(f"sidebar metadata render changed: {result!r}")
    for expected in ["close-status-menu", "bookmark-ui", "management-ui", "status::false"]:
        if expected not in result["calls"]:
            raise AssertionError(f"document/sidebar callbacks changed: {result!r}")


def assert_generated_data_runtime_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js');
            let fetchCount = 0;
            const requestUrls = [];
            const state = {
                reloadNonce: 'nonce-1',
                reloadExpectedDocId: 'doc-2',
                managementAvailable: true,
                managementCapabilities: null,
                generatedDataReadChecked: false,
                generatedDataReadAvailable: false,
                generatedDataReadRequestPromise: null
            };
            const runtime = module.createDocsViewerGeneratedDataRuntime({
                assetVersion: 'asset-1',
                generatedBaseUrl: 'http://127.0.0.1:8789',
                reloadRetryAttempts: 7,
                reloadRetryDelayMs: 11,
                state,
                viewerScope: () => 'studio',
                window: {
                    fetch: async (url) => {
                        requestUrls.push(String(url));
                        fetchCount += 1;
                        if (String(url).includes('/docs/generated/search')) {
                            return {
                                ok: true,
                                async json() {
                                    return { entries: [{ id: 'doc-1', title: 'Doc one' }] };
                                }
                            };
                        }
                        return {
                            ok: true,
                            async json() {
                                return {
                                    capabilities: {
                                        generated_data_reads: true,
                                        scopes: {
                                            studio: { available: true, generated_data_reads: true, generated_search_reads: true },
                                            library: { available: true, generated_data_reads: false, generated_search_reads: false }
                                        }
                                    }
                                };
                            }
                        };
                    },
                    setTimeout: (resolve) => resolve()
                }
            });
            const requestOptions = runtime.dataRequestOptions({ viewerScope: 'library', extra: 'value' });
            const studioAllowed = await runtime.checkGeneratedDataReadCapability('studio');
            const libraryAllowed = await requestOptions.checkGeneratedDataReadCapability();
            const searchAllowed = requestOptions.scopeSupportsGeneratedSearchReads();
            const cachedStudioAllowed = await runtime.checkGeneratedDataReadCapability('studio');
            const searchPayload = await runtime.readSearchIndex({
                searchIndexUrl: '/assets/search/studio/index.json',
                viewerScope: 'studio'
            });
            const staticRequests = [];
            const publicRuntime = module.createDocsViewerGeneratedDataRuntime({
                assetVersion: 'asset-2',
                generatedBaseUrl: '',
                state: {
                    reloadNonce: '',
                    reloadExpectedDocId: '',
                    managementAvailable: false,
                    managementCapabilities: null,
                    generatedDataReadChecked: false,
                    generatedDataReadAvailable: false,
                    generatedDataReadRequestPromise: null
                },
                viewerScope: () => 'library',
                window: {
                    fetch: async (url) => {
                        staticRequests.push(String(url));
                        return {
                            ok: true,
                            async json() {
                                return { entries: [] };
                            }
                        };
                    },
                    setTimeout: (resolve) => resolve()
                }
            });
            await publicRuntime.readSearchIndex({
                searchIndexUrl: '/assets/search/library/index.json',
                viewerScope: 'library'
            });
            return {
                requestShape: {
                    assetVersion: requestOptions.assetVersion,
                    reloadNonce: requestOptions.reloadNonce,
                    reloadExpectedDocId: requestOptions.reloadExpectedDocId,
                    reloadRetryAttempts: requestOptions.reloadRetryAttempts,
                    reloadRetryDelayMs: requestOptions.reloadRetryDelayMs,
                    managementAvailable: requestOptions.managementAvailable,
                    managementBaseUrl: requestOptions.managementBaseUrl,
                    extra: requestOptions.extra
                },
                studioAllowed,
                libraryAllowed,
                searchAllowed,
                cachedStudioAllowed,
                searchEntryCount: searchPayload.entries.length,
                searchRequestPath: new URL(requestUrls[1]).pathname,
                staticSearchRequest: staticRequests[0],
                fetchCount,
                checked: state.generatedDataReadChecked,
                available: state.generatedDataReadAvailable
            };
        }"""
    )
    if result != {
        "requestShape": {
            "assetVersion": "asset-1",
            "reloadNonce": "nonce-1",
            "reloadExpectedDocId": "doc-2",
            "reloadRetryAttempts": 7,
            "reloadRetryDelayMs": 11,
            "managementAvailable": True,
            "managementBaseUrl": "http://127.0.0.1:8789",
            "extra": "value",
        },
        "studioAllowed": True,
        "libraryAllowed": False,
        "searchAllowed": False,
        "cachedStudioAllowed": True,
        "searchEntryCount": 1,
        "searchRequestPath": "/docs/generated/search",
        "staticSearchRequest": "/assets/search/library/index.json?v=asset-2",
        "fetchCount": 2,
        "checked": True,
        "available": True,
    }:
        raise AssertionError(f"generated-data runtime contract changed unexpectedly: {result!r}")


def assert_config_controller_contract(page: Page, base_url: str) -> None:
    result = page.evaluate(
        """async ({ baseUrl }) => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-config-controller.js');
            document.body.innerHTML = `
                <section id="root"></section>
                <select id="scopeSelect"></select>
                <button id="recentButton"></button>
            `;
            history.replaceState(null, '', `${baseUrl}/docs/?scope=library`);
            const calls = [];
            const fetchUrls = [];
            const root = document.getElementById('root');
            const scopeSelect = document.getElementById('scopeSelect');
            const recentButton = document.getElementById('recentButton');
            const scopeConfig = {
                docsViewerConfigLoaded: false,
                docsViewerConfigRequestPromise: null,
                scopeConfigs: [],
                scopeConfigsById: new Map(),
                defaultScopeId: '',
                viewerConfigLoaded: false,
                viewerConfigRequestPromise: null,
                uiStatuses: [],
                uiStatusByValue: new Map(),
                recentLimit: 10,
                managementText: {
                    statusPillSetLabel: 'Set status: {label}',
                    statusPillClearLabel: 'Clear status: {label}',
                    statusPillReadonlyLabel: 'Status: {label}',
                    statusMenuLabel: 'Document status',
                    statusPillSaving: 'Saving...',
                    statusPillSaved: 'Saved.',
                    statusPillFailed: 'Failed.'
                }
            };
            const documentIndex = {
                docs: [{ doc_id: 'intro' }]
            };
            const searchRecent = {
                recentLimit: 10,
                recentModeActive: true
            };
            const routeSession = {
                managementMode: true
            };
            const configPayload = {
                schema_version: 'docs_viewer_config_v1',
                default_scope_id: 'studio',
                docs_viewer: {
                    recently_added_limit: 3,
                    scope_type_badges: {
                        public: { emoji: 'P' }
                    },
                    ui_statuses_by_scope: {
                        library: [
                            { ui_status: 'review', label: 'Review', emoji: 'R' }
                        ]
                    }
                },
                scopes: [
                    {
                        scope_id: 'studio',
                        scope_type: 'local',
                        viewer_base_url: '/docs/',
                        include_scope_param: true,
                        default_doc_id: 'studio-home',
                        index_url: '/studio/index.json',
                        search_index_url: '/studio/search.json'
                    },
                    {
                        scope_id: 'library',
                        scope_type: 'public',
                        viewer_base_url: '/library/',
                        include_scope_param: false,
                        default_doc_id: 'library-home',
                        index_url: '/library/index.json',
                        search_index_url: '/library/search.json'
                    }
                ]
            };
            const textPayload = {
                recently_added_button: 'Latest docs',
                status_pill_set_label: 'Set {label}',
                status_pill_saved: 'Saved status.'
            };
            const originalFetch = window.fetch;
            window.fetch = (url) => {
                fetchUrls.push(String(url));
                const payload = String(url).includes('ui-text') ? textPayload : configPayload;
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve(payload)
                });
            };
            try {
                const controller = module.initDocsViewerConfigController({
                    allowScopeQuery: true,
                    configService: {
                        docsViewerConfigUrl: '/config.json',
                        uiTextUrl: '/ui-text.json',
                        dataRequestOptions: (options) => ({ marker: options && options.reloadNonce || 'none' })
                    },
                    defaultRecentLimit: 10,
                    documentIndex,
                    getCurrentMode: () => 'manage',
                    managementController: () => ({ applyConfig: () => calls.push('apply-management-config') }),
                    managementMode: 'manage',
                    recentButton,
                    renderRecentMode: () => calls.push('render-recent'),
                    renderSidebar: () => calls.push('render-sidebar'),
                    renderStatusPills: () => calls.push('render-status-pills'),
                    root,
                    routeCommands: {
                        applyRouteGlobals: (projection) => calls.push(`route:${projection.viewerScope}:${projection.defaultRouteDocId}:${projection.includeScopeParam}`)
                    },
                    routeSession,
                    routeViewerBaseUrl: '/docs/',
                    scopeConfig,
                    scopeSelect,
                    searchRecent,
                    uiStatusEmojiMaxLength: 4,
                    viewerBaseUrl: () => '/docs/',
                    viewerScope: () => 'library'
                });
                const loadedScope = await controller.loadDocsViewerConfig();
                await controller.loadViewerConfig();
                return {
                    fetchUrls,
                    loadedDefault: loadedScope.defaultScopeId,
                    scopeIds: scopeConfig.scopeConfigs.map((config) => config.scopeId),
                    selectedScope: scopeSelect.value,
                    optionText: Array.from(scopeSelect.options).map((option) => option.textContent),
                    rootDataset: {
                        viewerScope: root.dataset.viewerScope,
                        indexUrl: root.dataset.indexUrl,
                        searchIndexUrl: root.dataset.searchIndexUrl,
                        defaultDocId: root.dataset.defaultDocId,
                        viewerBaseUrl: root.dataset.viewerBaseUrl,
                        includeScopeParam: root.dataset.includeScopeParam
                    },
                    recentLimit: searchRecent.recentLimit,
                    statusLabel: scopeConfig.uiStatusByValue.get('review')?.label || '',
                    recentButtonText: recentButton.textContent,
                    managementText: scopeConfig.managementText,
                    calls
                };
            } finally {
                window.fetch = originalFetch;
            }
        }""",
        {"baseUrl": base_url},
    )
    if result["loadedDefault"] != "studio" or result["scopeIds"] != ["library", "studio"]:
        raise AssertionError(f"config controller scope normalization changed: {result!r}")
    if result["selectedScope"] != "library" or result["optionText"] != ["P library", "studio"]:
        raise AssertionError(f"config controller scope picker projection changed: {result!r}")
    if result["rootDataset"] != {
        "viewerScope": "library",
        "indexUrl": "/library/index.json",
        "searchIndexUrl": "/library/search.json",
        "defaultDocId": "library-home",
        "viewerBaseUrl": "/docs/",
        "includeScopeParam": "true",
    }:
        raise AssertionError(f"config controller route-global projection changed: {result!r}")
    if result["recentLimit"] != 3 or result["statusLabel"] != "Review" or result["recentButtonText"] != "Latest docs":
        raise AssertionError(f"config controller UI config projection changed: {result!r}")
    if result["managementText"]["statusPillSetLabel"] != "Set {label}" or result["managementText"]["statusPillSaved"] != "Saved status.":
        raise AssertionError(f"config controller management text projection changed: {result!r}")
    for expected in ["route:library:library-home:true", "apply-management-config", "render-sidebar", "render-status-pills", "render-recent"]:
        if expected not in result["calls"]:
            raise AssertionError(f"config controller callback contract changed: {result!r}")


def assert_service_context_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-service-context.js');
            const publicContext = module.createDocsViewerServiceContext({
                routeContext: {
                    access: { allowManagement: false },
                    docsViewerConfigUrl: '/docs-viewer/config/defaults/docs-viewer-config.json',
                    generatedBaseUrl: 'http://127.0.0.1:8789',
                    managementBaseUrl: 'http://127.0.0.1:8789',
                    reportRegistryUrl: '/assets/data/docs/reports.json',
                    uiTextUrl: '/docs-viewer/config/ui-text/ui-text.json'
                }
            });
            const manageContext = module.createDocsViewerServiceContext({
                routeContext: {
                    access: { allowManagement: true },
                    docsViewerConfigUrl: '/docs-viewer/config/defaults/docs-viewer-config.json',
                    generatedBaseUrl: 'http://127.0.0.1:8789/',
                    managementBaseUrl: 'http://127.0.0.1:8789/',
                    reportRegistryUrl: '/assets/data/docs/reports.json',
                    uiTextUrl: '/docs-viewer/config/ui-text/ui-text.json'
                }
            });
            return {
                publicReadOnly: publicContext.access.publicReadOnly,
                publicGeneratedBase: publicContext.generatedRead.baseUrl,
                publicManagement: publicContext.management,
                publicConfigAuthority: publicContext.config.authority,
                publicReportAuthority: publicContext.reports.authority,
                manageReadOnly: manageContext.access.publicReadOnly,
                manageGeneratedBase: manageContext.generatedRead.baseUrl,
                manageManagementBase: manageContext.management && manageContext.management.baseUrl,
                manageManagementAuthority: manageContext.management && manageContext.management.authority
            };
        }"""
    )
    if result != {
        "publicReadOnly": True,
        "publicGeneratedBase": "",
        "publicManagement": None,
        "publicConfigAuthority": "browser-safe config asset",
        "publicReportAuthority": "browser-safe config asset",
        "manageReadOnly": False,
        "manageGeneratedBase": "http://127.0.0.1:8789",
        "manageManagementBase": "http://127.0.0.1:8789",
        "manageManagementAuthority": "management backend capability/write endpoint",
    }:
        raise AssertionError(f"Docs Viewer service context contract changed unexpectedly: {result!r}")


def assert_document_index_state_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-document-index-state.js');
            const publicState = {
                allDocs: [
                    { doc_id: 'root', title: 'Root', sort_order: 1, viewable: true },
                    { doc_id: 'child', parent_id: 'root', title: 'Child', sort_order: 1, viewable: true },
                    { doc_id: 'hidden-root', title: 'Hidden', sort_order: 2, hidden: true, viewable: true },
                    { doc_id: 'hidden-child', parent_id: 'hidden-root', title: 'Hidden child', sort_order: 1, viewable: true },
                    { doc_id: 'draft-root', title: 'Draft root', sort_order: 3, viewable: true },
                    { doc_id: 'draft-child', parent_id: 'draft-root', title: 'Draft child', sort_order: 1, viewable: true }
                ],
                allDocsById: new Map(),
                childrenByParent: new Map(),
                docs: [],
                docsById: new Map(),
                manageOnlyTreeRootIds: new Set(['draft-root']),
                managementMode: false,
                nonLoadableDocIds: new Set(['root']),
                showHidden: false,
                uiStatusByValue: new Map([['planned', { label: 'Planned' }]])
            };
            const publicIndex = module.createDocsViewerDocumentIndexState({ state: publicState });
            publicIndex.applyDocVisibility();
            const publicDocs = publicState.docs.map((doc) => doc.doc_id);
            const defaultDoc = publicIndex.defaultDocId();
            const rootTarget = publicIndex.viewerTargetDocId('root');
            const missingTarget = publicIndex.viewerTargetDocId('missing');
            const manageState = Object.assign({}, publicState, {
                allDocs: publicState.allDocs.map((doc) => Object.assign({}, doc)),
                allDocsById: new Map(),
                childrenByParent: new Map(),
                docs: [],
                docsById: new Map(),
                managementMode: true,
                showHidden: false,
                nonLoadableDocIds: new Set(['root']),
                manageOnlyTreeRootIds: new Set(['draft-root'])
            });
            const manageIndex = module.createDocsViewerDocumentIndexState({ state: manageState });
            manageIndex.applyDocVisibility();
            manageIndex.syncHiddenVisibilityForRequestedDoc(() => 'hidden-root');
            manageIndex.applyDocVisibility();
            return {
                publicDocs,
                defaultDoc,
                rootTarget,
                missingTarget,
                publicHiddenStatus: publicIndex.statusForIndexDoc(publicState.allDocsById.get('hidden-root')),
                manageShowHidden: manageState.showHidden,
                manageDocs: manageState.docs.map((doc) => doc.doc_id),
                findHidden: manageIndex.findAllDocById('hidden-root')?.doc_id || ''
            };
        }"""
    )
    if result != {
        "publicDocs": ["child", "root"],
        "defaultDoc": "child",
        "rootTarget": "child",
        "missingTarget": "missing",
        "publicHiddenStatus": None,
        "manageShowHidden": True,
        "manageDocs": ["child", "draft-child", "hidden-child", "root", "hidden-root", "draft-root"],
        "findHidden": "hidden-root",
    }:
        raise AssertionError(f"document-index state contract changed unexpectedly: {result!r}")


def assert_info_panel_controller_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const info = await import('/docs-viewer/runtime/js/docs-viewer-info-panel-controller.js');
            const hosted = await import('/docs-viewer/runtime/js/docs-viewer-hosted-views.js');
            document.body.innerHTML = `
                <button id="infoToggle"></button>
                <button id="closeButton"></button>
                <div id="toolbar"><button id="metadataButton" data-info-panel-view="metadata-info"></button></div>
                <div id="body"></div>
            `;
            const registry = hosted.createDocsViewerHostedViewRegistry({ accessProjection: { allowManagement: false, publicReadOnly: true } });
            const events = [];
            registry.register({
                id: 'metadata-info',
                label: 'Metadata',
                panel: 'info',
                access: 'public',
                load: () => Promise.resolve({
                    mount: ({ mount, selectedDoc }) => {
                        events.push(`mount:${selectedDoc.doc_id}`);
                        mount.textContent = selectedDoc.title;
                    },
                    update: ({ selectedDoc }) => {
                        events.push(`update:${selectedDoc.doc_id}`);
                    },
                    unmount: () => {
                        events.push('unmount');
                    }
                })
            });
            const projections = [];
            const shellProjections = [];
            const documentIndex = {
                allDocsById: new Map([['doc-1', { doc_id: 'doc-1', title: 'Doc one' }]]),
                docsById: new Map([['doc-1', { doc_id: 'doc-1', title: 'Doc one' }]])
            };
            const selectedDocument = {
                payloadCache: new Map(),
                selectedDocId: 'doc-1'
            };
            const scopeConfig = {
                uiStatusByValue: new Map()
            };
            const panelView = {
                viewState: {}
            };
            const controller = info.createDocsViewerInfoPanelController({
                buildTrail: () => [],
                documentIndex,
                infoToggle: document.getElementById('infoToggle'),
                panelView,
                projectDocumentShell: (projection) => shellProjections.push(projection),
                projectInfoPanel: (projection) => projections.push(projection),
                projectViewState: () => ({ info: 'open' }),
                refs: {
                    body: document.getElementById('body'),
                    closeButton: document.getElementById('closeButton'),
                    toolbar: document.getElementById('toolbar')
                },
                registry,
                routeAccess: { allowManagement: false, publicReadOnly: true },
                scopeConfig,
                selectedDocument,
                viewerScope: () => 'studio',
                viewerTargetDocId: (docId) => docId,
                viewerUrl: (docId) => `/docs/?doc=${docId}`
            });
            controller.bind();
            controller.renderToggleState();
            document.getElementById('infoToggle').click();
            await new Promise((resolve) => setTimeout(resolve, 0));
            controller.update();
            await new Promise((resolve) => setTimeout(resolve, 0));
            document.getElementById('metadataButton').click();
            await new Promise((resolve) => setTimeout(resolve, 0));
            document.getElementById('closeButton').click();
            await new Promise((resolve) => setTimeout(resolve, 0));
            return {
                events,
                bodyText: document.getElementById('body').textContent,
                shellProjections,
                panelVisibility: projections.map((projection) => projection.visible),
                viewState: panelView.viewState,
                openAfterClose: controller.isOpen()
            };
        }"""
    )
    if result["events"] != ["mount:doc-1", "update:doc-1", "unmount", "mount:doc-1", "unmount"]:
        raise AssertionError(f"info-panel lifecycle changed unexpectedly: {result!r}")
    if result["bodyText"] != "" or result["openAfterClose"] is not False:
        raise AssertionError(f"info-panel close state changed unexpectedly: {result!r}")
    if result["viewState"] != {"info": "open"}:
        raise AssertionError(f"info-panel view-state projection changed unexpectedly: {result!r}")
    if not any(projection.get("infoTogglePressed") is True for projection in result["shellProjections"]):
        raise AssertionError(f"info-panel toggle projection never opened: {result!r}")
    if result["panelVisibility"][-1] is not False:
        raise AssertionError(f"info-panel final projection should be closed: {result!r}")


def assert_management_runtime_adapter_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js');
            const disabled = module.createDocsViewerManagementRuntimeAdapter({
                allowManagement: false,
                appShellReady: Promise.resolve()
            });
            const disabledResult = await disabled.load();
            let importCount = 0;
            let loadedCount = 0;
            const adapter = module.createDocsViewerManagementRuntimeAdapter({
                allowManagement: true,
                appShellReady: Promise.resolve(),
                constants: { MANAGEMENT_MODE: 'manage' },
                context: {
                    root: { id: 'root' },
                    managementState: {
                        domains: {
                            selectedDocument: { selectedDocId: 'doc-1' }
                        }
                    },
                    serviceClient: {
                        managementBaseUrl: 'http://127.0.0.1:8789'
                    }
                },
                importManagement: async () => {
                    importCount += 1;
                    return {
                        initDocsViewerManagement(context) {
                            return {
                                contextMode: context.MANAGEMENT_MODE,
                                rootId: context.root.id,
                                selectedDocId: context.managementState.domains.selectedDocument.selectedDocId,
                                managementBaseUrl: context.serviceClient.managementBaseUrl
                            };
                        }
                    };
                },
                onLoaded: () => {
                    loadedCount += 1;
                }
            });
            const first = await adapter.load();
            const second = await adapter.load();
            return {
                disabledResult,
                sameController: first === second,
                importCount,
                loadedCount,
                controller: adapter.controller()
            };
        }"""
    )
    if result != {
        "disabledResult": None,
        "sameController": True,
        "importCount": 1,
        "loadedCount": 1,
        "controller": {
            "contextMode": "manage",
            "rootId": "root",
            "selectedDocId": "doc-1",
            "managementBaseUrl": "http://127.0.0.1:8789",
        },
    }:
        raise AssertionError(f"management runtime adapter contract changed unexpectedly: {result!r}")


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
                  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
                  <div id="docsViewerDocumentShellMount" data-docs-viewer-document-shell-mount></div>
                  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
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
                contextMenuCount: document.querySelectorAll('#docsViewerContextMenu').length,
                metadataModalCount: document.querySelectorAll('#docsViewerMetadataModal').length,
                importRootCount: document.querySelectorAll('#docsHtmlImportRoot').length,
                settingsModalCount: document.querySelectorAll('#docsViewerSettingsModal').length,
                managementShellMountChildCount: document.querySelector('[data-docs-viewer-management-shell-mount]').children.length,
                sidebarCount: document.querySelectorAll('.docsViewer__sidebar').length,
                navCount: document.querySelectorAll('#docsViewerNav').length,
                toggleCount: document.querySelectorAll('#docsViewerSidebarToggle').length,
                indexMountChildCount: document.querySelector('[data-docs-viewer-index-panel-mount]').children.length,
                documentShellCount: document.querySelectorAll('.docsViewer__main').length,
                documentContentCount: document.querySelectorAll('#docsViewerContent').length,
                documentMountChildCount: document.querySelector('[data-docs-viewer-document-shell-mount]').children.length,
                infoPanelCount: document.querySelectorAll('#docsViewerInfoPanel').length,
                infoBodyCount: document.querySelectorAll('#docsViewerInfoPanelBody').length,
                infoMountChildCount: document.querySelector('[data-docs-viewer-info-panel-mount]').children.length
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
        "contextMenuCount": 1,
        "metadataModalCount": 1,
        "importRootCount": 1,
        "settingsModalCount": 1,
        "managementShellMountChildCount": 4,
        "sidebarCount": 1,
        "navCount": 1,
        "toggleCount": 1,
        "indexMountChildCount": 1,
        "documentShellCount": 1,
        "documentContentCount": 1,
        "documentMountChildCount": 1,
        "infoPanelCount": 1,
        "infoBodyCount": 1,
        "infoMountChildCount": 1,
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
            assert_route_context_and_shell_refs(page)
            assert_route_config_explicit_and_access_projection(page)
            assert_route_config_inline_and_malformed_fallback(page)
            assert_route_config_registry_resolution(page)
            assert_app_session_contract(page)
            assert_app_composition_contract(page)
            assert_app_boot_public_context_contract(page)
            assert_app_boot_management_context_contract(page)
            assert_app_boot_start_is_single_start(page)
            assert_index_panel_shell_render(page)
            assert_index_panel_projection(page)
            assert_document_shell_render(page)
            assert_document_shell_management_shape(page)
            assert_management_shell_mount_does_not_shift_document(page)
            assert_document_shell_projection(page)
            assert_info_panel_shell_and_metadata_lifecycle(page)
            assert_hosted_view_context_contract(page)
            assert_panel_layout_contract(page)
            assert_view_state_and_hosted_view_contract(page)
            assert_route_workflow_contract(page, base_url)
            assert_search_controller_contract(page)
            assert_bookmark_controller_contract(page)
            assert_document_and_sidebar_controller_contract(page)
            assert_generated_data_runtime_contract(page)
            assert_config_controller_contract(page, base_url)
            assert_service_context_contract(page)
            assert_document_index_state_contract(page)
            assert_info_panel_controller_contract(page)
            assert_management_runtime_adapter_contract(page)
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
