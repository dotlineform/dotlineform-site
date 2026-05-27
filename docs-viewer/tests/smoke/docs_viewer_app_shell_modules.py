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
                generated_base_url: '',
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
                    management_base_url: '',
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
                allowManagement: projected.allowManagement,
                canLoadManagementUi: projected.canLoadManagementUi,
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
        "allowManagement": False,
        "canLoadManagementUi": False,
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
                hostedViews.createDocsViewerCompatibilityHostedViews()
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
                title: refs.body.querySelector('.docsViewer__metadataInfoTitle')?.textContent || '',
                routeText: Array.from(refs.body.querySelectorAll('.docsViewer__metadataInfoRow')).find((row) => row.querySelector('dt')?.textContent === 'Route')?.querySelector('a')?.textContent || '',
                rowLabels: Array.from(refs.body.querySelectorAll('.docsViewer__metadataInfoTerm')).map((node) => node.textContent)
            };
            await host.update(Object.assign({}, context, {
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
            return { openProjection, missingSummary, closedProjection, missingProjection, emptyText };
        }"""
    )
    if result["openProjection"] != {
        "returnedPanelId": "docsViewerInfoPanel",
        "refPanelId": "docsViewerInfoPanel",
        "panelHidden": False,
        "rootState": "open",
        "rootLayout": "index-document-info",
        "activeViewId": "metadata-info",
        "title": "Example Doc",
        "routeText": "/docs/?scope=studio&doc=example",
        "rowLabels": ["Scope", "Summary", "Parent path", "Added", "Updated", "UI status", "Visibility", "Route"],
    }:
        raise AssertionError(f"info panel metadata open projection failed: {result!r}")
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
                hostedViews.createDocsViewerCompatibilityHostedViews().concat([
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
                registeredIds: registry.list().map((view) => `${view.id}:${view.available ? 'yes' : view.unavailableReason}`).sort()
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
        raise AssertionError(f"compat metadata info view should be public and available: {result!r}")
    if "metadata-info:yes" not in result["registeredIds"] or "index-tree:yes" not in result["registeredIds"]:
        raise AssertionError(f"hosted view registry listing lost compatibility views: {result!r}")


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
            assert_index_panel_shell_render(page)
            assert_index_panel_projection(page)
            assert_document_shell_render(page)
            assert_document_shell_management_shape(page)
            assert_document_shell_projection(page)
            assert_info_panel_shell_and_metadata_lifecycle(page)
            assert_hosted_view_context_contract(page)
            assert_panel_layout_contract(page)
            assert_view_state_and_hosted_view_contract(page)
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
