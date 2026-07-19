#!/usr/bin/env python3
"""Smoke-check focused Docs Viewer router module contracts."""

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


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const router = await import('/docs-viewer/runtime/js/shared/docs-viewer-router.js');
            const routeConfig = await import('/docs-viewer/runtime/js/shared/docs-viewer-route-config.js');
            const appContext = await import('/docs-viewer/runtime/js/shared/docs-viewer-app-context.js');
            const serviceContext = await import('/docs-viewer/runtime/js/shared/docs-viewer-service-context.js');
            const configuredScopeProvider = await import('/docs-viewer/runtime/js/shared/docs-viewer-configured-scope-provider.js');
            const routeFeatures = await import('/docs-viewer/runtime/js/shared/docs-viewer-route-features.js');
            const appComposition = await import('/docs-viewer/runtime/js/shared/docs-viewer-app-composition.js');
            const toolbarRenderer = await import('/docs-viewer/runtime/js/shared/docs-viewer-viewer-toolbar-renderer.js');
            const configController = await import('/docs-viewer/runtime/js/shared/docs-viewer-config-controller.js');
            const viewRegistry = await import('/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js');
            const mainViewRenderer = await import('/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js');
            const appSession = await import('/docs-viewer/runtime/js/shared/docs-viewer-app-session.js');
            const documentViewCoordinator = await import('/docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js');
            const generatedDataRuntime = await import('/docs-viewer/runtime/js/shared/docs-viewer-generated-data-runtime.js');
            const statusController = await import('/docs-viewer/runtime/js/shared/docs-viewer-status-controller.js');
            const controlSurfaceHost = await import('/docs-viewer/runtime/js/shared/docs-viewer-control-surface-host.js');
            const appControlRenderers = await import('/docs-viewer/runtime/js/shared/docs-viewer-app-control-renderers.js');
            const appShell = await import('/docs-viewer/runtime/js/shared/docs-viewer-app-shell.js');
            window.__docsViewerRouterModuleSmoke = { router, routeConfig, appContext, serviceContext, configuredScopeProvider, routeFeatures, appComposition, toolbarRenderer, configController, viewRegistry, mainViewRenderer, appSession, documentViewCoordinator, generatedDataRuntime, statusController, controlSurfaceHost, appControlRenderers, appShell };
        }"""
    )


def assert_control_surface_host(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const { controlSurfaceHost, routeFeatures, viewRegistry } = window.__docsViewerRouterModuleSmoke;
            const definitions = [
                viewRegistry.createDocsViewerSharedViewDefinitions(),
                { controls: [
                    {
                        id: 'select-index',
                        label: 'Select',
                        ownerType: 'view',
                        ownerViewId: 'index-tree',
                        surfaceId: 'index-view',
                        appKinds: ['manage'],
                        renderer: 'synthetic-button'
                    },
                    {
                        id: 'second-index-control',
                        label: 'Second',
                        ownerType: 'view',
                        ownerViewId: 'index-tree',
                        surfaceId: 'index-view',
                        appKinds: ['manage'],
                        renderer: 'synthetic-button'
                    }
                ] }
            ];
            const manageRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets: definitions,
                projectionInputs: {
                    appContext: {
                        kind: 'manage',
                        featurePolicy: routeFeatures.normalizeDocsViewerRouteFeatures(['management'])
                    }
                }
            });
            const publicRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets: definitions,
                projectionInputs: {
                    appContext: {
                        kind: 'public',
                        featurePolicy: routeFeatures.normalizeDocsViewerRouteFeatures([])
                    }
                }
            });
            const mount = document.createElement('div');
            const dispatches = [];
            const renderer = ({ control, document: documentRef }) => {
                if (control.id === 'second-index-control') {
                    const root = documentRef.createElement('div');
                    const button = documentRef.createElement('button');
                    button.type = 'button';
                    button.dataset.docsViewerAction = 'nested-action';
                    root.appendChild(button);
                    return { root, interactive: button };
                }
                const button = documentRef.createElement('button');
                button.type = 'button';
                button.textContent = control.label;
                return button;
            };
            const host = controlSurfaceHost.createDocsViewerControlSurfaceHost({
                mount,
                registry: manageRegistry,
                renderers: { 'synthetic-button': renderer },
                surfaceId: 'index-view',
                onDispatch: detail => dispatches.push({
                    actionId: detail.actionId,
                    controlId: detail.controlId,
                    eventType: detail.eventType,
                    surfaceId: detail.surfaceId
                })
            });
            const projected = host.render({
                activeViewId: 'index-tree',
                controlStateById: {
                    'select-index': { disabled: false, pressed: true, label: 'Select documents', count: 2 }
                }
            });
            const selectButton = mount.querySelector('[data-docs-viewer-control="select-index"]');
            selectButton.click();
            mount.querySelector('[data-docs-viewer-action="nested-action"]').click();
            const populated = {
                count: projected.length,
                hidden: mount.hidden,
                ids: Array.from(mount.children).map(node => node.dataset.docsViewerControl),
                select: {
                    count: selectButton.dataset.docsViewerControlCount,
                    label: selectButton.getAttribute('aria-label'),
                    pressed: selectButton.getAttribute('aria-pressed'),
                    surface: selectButton.dataset.docsViewerControlSurface
                }
            };
            const publicMount = document.createElement('div');
            const publicHost = controlSurfaceHost.createDocsViewerControlSurfaceHost({
                mount: publicMount,
                registry: publicRegistry,
                renderers: { 'synthetic-button': renderer },
                surfaceId: 'index-view'
            });
            const publicProjected = publicHost.render({ activeViewId: 'index-tree' });
            const optionalHost = controlSurfaceHost.createDocsViewerControlSurfaceHost({
                mount: null,
                registry: manageRegistry,
                renderers: { 'synthetic-button': renderer },
                surfaceId: 'index-view'
            });
            return {
                dispatches,
                optionalCount: optionalHost.render({ activeViewId: 'index-tree' }).length,
                populated,
                publicCount: publicProjected.length,
                publicHidden: publicMount.hidden
            };
        }"""
    )
    expected = {
        "dispatches": [{
            "actionId": "",
            "controlId": "select-index",
            "eventType": "click",
            "surfaceId": "index-view",
        }, {
            "actionId": "nested-action",
            "controlId": "second-index-control",
            "eventType": "click",
            "surfaceId": "index-view",
        }],
        "optionalCount": 0,
        "populated": {
            "count": 2,
            "hidden": False,
            "ids": ["select-index", "second-index-control"],
            "select": {
                "count": "2",
                "label": "Select documents",
                "pressed": "true",
                "surface": "index-view",
            },
        },
        "publicCount": 0,
        "publicHidden": True,
    }
    if result != expected:
        raise AssertionError(f"control-surface host contract changed: {result!r}")


def assert_app_shell_control_surface_mounts(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { appShell, routeFeatures, viewRegistry } = window.__docsViewerRouterModuleSmoke;
            const makeRoot = () => {
                const root = document.createElement('div');
                [
                    'header-controls',
                    'index-panel',
                    'main-view',
                    'info-panel',
                    'management-shell'
                ].forEach(name => {
                    const mount = document.createElement('div');
                    mount.setAttribute(`data-docs-viewer-${name}-mount`, '');
                    root.appendChild(mount);
                });
                return root;
            };
            const manageFeatures = routeFeatures.normalizeDocsViewerRouteFeatures([
                'bookmarks', 'source-editing', 'management'
            ]);
            const manageRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets: [
                    viewRegistry.createDocsViewerSharedViewDefinitions(),
                    {
                        modes: [{
                            id: 'markdown-source',
                            ownerViewId: 'rendered-document',
                            appKinds: ['manage'],
                            features: ['source-editing']
                        }],
                        controls: [{
                            id: 'manage-control',
                            ownerType: 'view',
                            ownerViewId: 'rendered-document',
                            surfaceId: 'main-view',
                            appKinds: ['manage'],
                            renderer: 'manage-control'
                        }]
                    }
                ],
                projectionInputs: { appContext: { kind: 'manage', featurePolicy: manageFeatures } }
            });
            const manageRoot = makeRoot();
            await appShell.initDocsViewerAppShell({
                root: manageRoot,
                document,
                routeContext: {
                    appContext: {
                        kind: 'manage',
                        featurePolicy: manageFeatures,
                        routeAccess: { managementUi: true }
                    }
                },
                viewRegistry: manageRegistry
            });
            const publicFeatures = routeFeatures.normalizeDocsViewerRouteFeatures([]);
            const publicRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets: [viewRegistry.createDocsViewerSharedViewDefinitions()],
                projectionInputs: { appContext: { kind: 'public', featurePolicy: publicFeatures } },
                routePolicy: { hiddenControls: ['bookmark', 'info'] }
            });
            const publicRoot = makeRoot();
            await appShell.initDocsViewerAppShell({
                root: publicRoot,
                document,
                routeContext: {
                    appContext: {
                        kind: 'public',
                        featurePolicy: publicFeatures,
                        routeAccess: { managementUi: false }
                    }
                },
                viewRegistry: publicRegistry
            });
            const counts = root => ({
                appViewer: root.querySelectorAll('[data-docs-viewer-control-surface-mount="app-viewer"]').length,
                appManagement: root.querySelectorAll('[data-docs-viewer-control-surface-mount="app-management"]').length,
                indexView: root.querySelectorAll('[data-docs-viewer-control-surface-mount="index-view"]').length,
                mainView: root.querySelectorAll('[data-docs-viewer-control-surface-mount="main-view"]').length
            });
            return { manage: counts(manageRoot), optionalPublic: counts(publicRoot) };
        }"""
    )
    expected = {
        "manage": {"appViewer": 1, "appManagement": 1, "indexView": 1, "mainView": 1},
        "optionalPublic": {"appViewer": 1, "appManagement": 0, "indexView": 1, "mainView": 0},
    }
    if result != expected:
        raise AssertionError(f"app-shell control-surface mounts changed: {result!r}")


def assert_missing_doc_history(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { router } = window.__docsViewerRouterModuleSmoke;
            const docsById = new Map([
                ['known', { doc_id: 'known' }],
                ['default-doc', { doc_id: 'default-doc' }]
            ]);
            const resolved = router.resolveViewerRouteDocId({
                requestedDocId: 'missing-doc',
                docsById,
                defaultRouteDocId: 'default-doc',
                defaultDocId: () => 'known'
            });
            const resolvedDefaultless = router.resolveViewerRouteDocId({
                requestedDocId: '',
                docsById,
                defaultRouteDocId: '',
                defaultDocId: () => 'known'
            });
            const resolvedStaleScopeDefault = router.resolveViewerRouteDocId({
                requestedDocId: 'moments',
                docsById,
                defaultRouteDocId: '',
                viewerScope: 'moments',
                defaultDocId: () => 'known'
            });
            const historyCalls = [];
            let missingHandled = false;
            await router.loadViewerDoc({
                docId: 'missing-doc',
                historyMode: 'push',
                hash: 'missing-section',
                state: {
                    docsById,
                    payloadCache: new Map(),
                    requestId: 0
                },
                resolveLoadableDocId: (docId) => docsById.has(docId) ? docId : '',
                setHistory: (docId, hash, query, mode) => historyCalls.push({ docId, hash, query, mode }),
                handleMissingDoc: () => { missingHandled = true; }
            });
            return { resolved, resolvedDefaultless, resolvedStaleScopeDefault, historyCalls, missingHandled };
        }"""
    )
    if result["resolved"] != {
        "requestedDocId": "missing-doc",
        "docId": "missing-doc",
        "corrected": False,
        "missing": True,
    }:
        raise AssertionError(f"missing route resolution changed: {result!r}")
    if result["historyCalls"] != [{"docId": "missing-doc", "hash": "missing-section", "query": "", "mode": "push"}]:
        raise AssertionError(f"missing doc history changed: {result!r}")
    if result["missingHandled"] is not True:
        raise AssertionError(f"missing doc handler was not called: {result!r}")
    if result["resolvedDefaultless"] != {
        "requestedDocId": "",
        "docId": "known",
        "corrected": True,
    }:
        raise AssertionError(f"defaultless route fallback changed: {result!r}")
    if result["resolvedStaleScopeDefault"] != {
        "requestedDocId": "moments",
        "docId": "known",
        "corrected": True,
    }:
        raise AssertionError(f"stale scope default fallback changed: {result!r}")


def assert_route_config_scope_default(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { routeConfig } = window.__docsViewerRouterModuleSmoke;
            const rawRouteConfig = {
                schema_version: 'docs_viewer_route_config_v4',
                app_kind: 'public',
                route_id: 'library',
                route_path: '/library/',
                default_scope_id: 'library',
                include_scope_param: false,
                viewer_base_url: '/library/',
                features: [
                    'configured-scope-discovery',
                    'search',
                    'recent',
                    'bookmarks',
                    'reports'
                ],
                recent_basis: 'edited',
                access: {
                    allow_scope_query: false,
                    management_ui: false
                },
                services: {
                    generated_data: { base_url: '' },
                    source: { base_url: '' },
                    management: { base_url: '' }
                },
                docs_paths: {
                    index_tree_url: '/assets/data/docs/scopes/library/index-tree.json',
                    recent_url: '/assets/data/docs/scopes/library/recent.json',
                    search_index_url: '/assets/data/search/library/index.json'
                },
                config_urls: {
                    docs_viewer: '/docs-viewer/config/defaults/docs-viewer-public-config.json',
                    report_registry: '/assets/data/docs/public-reports.json'
                }
            };
            const resolved = routeConfig.resolveDocsViewerRouteConfig({
                appKind: 'public',
                routeConfig: rawRouteConfig
            });
            let mismatchRejected = false;
            try {
                routeConfig.resolveDocsViewerRouteConfig({
                    appKind: 'manage',
                    routeConfig: rawRouteConfig
                });
            } catch (error) {
                mismatchRejected = /does not match/.test(String(error && error.message || ''));
            }
            const projection = routeConfig.routeConfigScopeProjection({
                scopeId: 'library',
                defaultDocId: 'library-root',
                includeScopeParam: false,
                viewerBaseUrl: '/library/',
                indexTreeUrl: '/assets/data/docs/scopes/library/index-tree.json',
                recentUrl: '/assets/data/docs/scopes/library/recent.json',
                searchIndexUrl: '/assets/data/search/library/index.json'
            }, { allowScopeQuery: false });
            return {
                appKind: resolved.appKind,
                mismatchRejected,
                defaultScopeId: resolved.defaultScopeId,
                viewerBaseUrl: resolved.viewerBaseUrl,
                defaultRouteDocId: projection.defaultRouteDocId
            };
        }"""
    )
    if result != {
        "appKind": "public",
        "mismatchRejected": True,
        "defaultScopeId": "library",
        "viewerBaseUrl": "/library/",
        "defaultRouteDocId": "library-root",
    }:
        raise AssertionError(f"route config scope-default projection changed: {result!r}")


def assert_route_feature_projection_and_startup(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { routeConfig, routeFeatures, appComposition, toolbarRenderer, configController, controlSurfaceHost, appControlRenderers, viewRegistry } = window.__docsViewerRouterModuleSmoke;
            const minimal = routeFeatures.normalizeDocsViewerRouteFeatures([]);
            const selected = routeFeatures.normalizeDocsViewerRouteFeatures([
                'configured-scope-discovery',
                'search',
                'bookmarks'
            ]);
            let unknownRejected = false;
            let dependencyRejected = false;
            try {
                routeFeatures.normalizeDocsViewerRouteFeatures(['not-a-feature']);
            } catch (error) {
                unknownRejected = /Unknown Docs Viewer route feature/.test(String(error && error.message || ''));
            }
            try {
                routeFeatures.normalizeDocsViewerRouteFeatures(['scope-selection']);
            } catch (error) {
                dependencyRejected = /requires configured-scope-discovery/.test(String(error && error.message || ''));
            }
            const resolvedMinimalRoute = routeConfig.resolveDocsViewerRouteConfig({
                appKind: 'review',
                routeConfig: {
                    schema_version: 'docs_viewer_route_config_v4',
                    app_kind: 'review',
                    route_id: 'minimal-review-shape',
                    route_path: '/minimal-review/',
                    default_scope_id: 'temporary',
                    include_scope_param: false,
                    viewer_base_url: '/minimal-review/',
                    features: [],
                    access: { allow_scope_query: false, management_ui: false },
                    services: {
                        generated_data: { base_url: '' },
                        source: { base_url: '' },
                        management: { base_url: '' }
                    },
                    docs_paths: { index_tree_url: '/temporary/index-tree.json' },
                    config_urls: { docs_viewer: '/temporary/viewer-settings.json' }
                }
            });

            const calls = [];
            await appComposition.startDocsViewerStartupPhases({
                composition: {
                    featurePolicy: selected,
                    shouldInitializeManagement: () => false,
                    shouldOpenImportOnLoad: () => false
                },
                bindEvents: () => calls.push('bind-events'),
                startBusy: () => { calls.push('start-busy'); return () => calls.push('stop-busy'); },
                loadConfiguredScopes: () => { calls.push('configured-scopes'); },
                loadViewerSettings: () => { calls.push('viewer-settings'); },
                initializeBookmarks: () => calls.push('bookmarks'),
                initializeManagement: () => calls.push('management'),
                loadIndex: () => { calls.push('index'); }
            });
            const minimalCalls = [];
            await appComposition.startDocsViewerStartupPhases({
                composition: {
                    featurePolicy: minimal,
                    shouldInitializeManagement: () => false,
                    shouldOpenImportOnLoad: () => false
                },
                bindEvents: () => minimalCalls.push('bind-events'),
                loadConfiguredScopes: () => minimalCalls.push('configured-scopes'),
                loadViewerSettings: () => minimalCalls.push('viewer-settings'),
                initializeBookmarks: () => minimalCalls.push('bookmarks'),
                initializeManagement: () => minimalCalls.push('management'),
                loadIndex: () => minimalCalls.push('index')
            });
            const minimalToolbarMount = document.createElement('div');
            toolbarRenderer.renderDocsViewerViewerToolbar({
                document,
                mount: minimalToolbarMount,
                routeContext: { appContext: { featurePolicy: minimal } }
            });
            const renderToolbarControls = (toolbarMount, featurePolicy) => {
                const registry = viewRegistry.createDocsViewerViewRegistry({
                    definitionSets: [viewRegistry.createDocsViewerSharedViewDefinitions()],
                    projectionInputs: { appContext: { kind: 'public', featurePolicy } }
                });
                const mount = toolbarMount.querySelector('[data-docs-viewer-control-surface-mount="app-viewer"]');
                controlSurfaceHost.createDocsViewerControlSurfaceHost({
                    mount,
                    registry,
                    renderers: appControlRenderers.createDocsViewerSharedControlRenderers(),
                    surfaceId: 'app-viewer'
                }).render({
                    controlStateById: { 'index-view-switch': { hidden: true } }
                });
            };
            const searchToolbarMount = document.createElement('div');
            toolbarRenderer.renderDocsViewerViewerToolbar({
                document,
                mount: searchToolbarMount,
                routeContext: { appContext: { featurePolicy: selected } }
            });
            const recentOnly = routeFeatures.normalizeDocsViewerRouteFeatures(['recent']);
            const recentToolbarMount = document.createElement('div');
            toolbarRenderer.renderDocsViewerViewerToolbar({
                document,
                mount: recentToolbarMount,
                routeContext: { appContext: { featurePolicy: recentOnly } }
            });
            renderToolbarControls(minimalToolbarMount, minimal);
            renderToolbarControls(searchToolbarMount, selected);
            renderToolbarControls(recentToolbarMount, recentOnly);
            const viewerSettingsState = {
                scopeConfig: {},
                searchRecent: {},
                documentIndex: { docs: [] }
            };
            const settingsController = configController.initDocsViewerConfigController({
                allowScopeQuery: false,
                configService: {
                    fetchDocsViewerConfig: () => Promise.resolve({
                        schema_version: 'docs_viewer_config_v1',
                        docs_viewer: { recent_limit: 7 }
                    })
                },
                defaultRecentLimit: 10,
                documentIndex: viewerSettingsState.documentIndex,
                featurePolicy: minimal,
                managementController: () => null,
                renderRecentMode: () => {},
                renderSidebar: () => {},
                root: document.createElement('div'),
                routeCommands: {},
                routeSession: {},
                scopeConfig: viewerSettingsState.scopeConfig,
                searchRecent: viewerSettingsState.searchRecent,
                uiStatusEmojiMaxLength: 8,
                viewerBaseUrl: () => '/minimal-review/',
                viewerScope: () => 'temporary'
            });
            await settingsController.loadViewerSettings();
            let scopeDiscoveryRejectedMissingScopes = false;
            try {
                await settingsController.loadConfiguredScopes();
            } catch (error) {
                scopeDiscoveryRejectedMissingScopes = /requires a scopes array/.test(String(error && error.message || ''));
            }
            return {
                calls,
                dependencyRejected,
                minimal,
                minimalCalls,
                optionalUrls: {
                    recent: resolvedMinimalRoute.recentUrl,
                    report: resolvedMinimalRoute.reportRegistryUrl,
                    search: resolvedMinimalRoute.searchIndexUrl
                },
                selected,
                settingsOnly: {
                    recentLimit: viewerSettingsState.searchRecent.recentLimit,
                    scopeDiscoveryRejectedMissingScopes
                },
                toolbarControls: {
                    minimalRecent: Boolean(minimalToolbarMount.querySelector('#docsViewerRecentButton')),
                    minimalSearch: Boolean(minimalToolbarMount.querySelector('#docsViewerSearchInput')),
                    recentOnlyRecent: Boolean(recentToolbarMount.querySelector('#docsViewerRecentButton')),
                    recentOnlySearch: Boolean(recentToolbarMount.querySelector('#docsViewerSearchInput')),
                    searchRecent: Boolean(searchToolbarMount.querySelector('#docsViewerRecentButton')),
                    searchSearch: Boolean(searchToolbarMount.querySelector('#docsViewerSearchInput'))
                },
                unknownRejected
            };
        }"""
    )
    if result["unknownRejected"] is not True or result["dependencyRejected"] is not True:
        raise AssertionError(f"route feature validation changed: {result!r}")
    if result["optionalUrls"] != {"recent": "", "report": "", "search": ""}:
        raise AssertionError(f"disabled features still require payload URLs: {result!r}")
    if result["calls"] != [
        "bind-events",
        "start-busy",
        "configured-scopes",
        "viewer-settings",
        "bookmarks",
        "index",
        "stop-busy",
    ]:
        raise AssertionError(f"feature-aware startup order changed: {result!r}")
    if result["minimalCalls"] != ["bind-events", "viewer-settings", "index"]:
        raise AssertionError(f"disabled startup features still ran: {result!r}")
    if result["selected"]["search"] is not True or result["selected"]["recent"] is not False:
        raise AssertionError(f"selected feature projection changed: {result!r}")
    if result["settingsOnly"] != {
        "recentLimit": 7,
        "scopeDiscoveryRejectedMissingScopes": True,
    }:
        raise AssertionError(f"viewer settings still depend on configured-scope discovery: {result!r}")
    if result["toolbarControls"] != {
        "minimalRecent": False,
        "minimalSearch": False,
        "recentOnlyRecent": True,
        "recentOnlySearch": False,
        "searchRecent": False,
        "searchSearch": True,
    }:
        raise AssertionError(f"feature toolbar construction changed: {result!r}")


def assert_explicit_app_and_service_context(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const { appContext, serviceContext } = window.__docsViewerRouterModuleSmoke;
            const routeConfig = {
                appKind: 'review',
                access: { allowScopeQuery: false, managementUi: false },
                services: {
                    generatedData: { baseUrl: 'http://127.0.0.1:8776' },
                    source: { baseUrl: 'http://127.0.0.1:8776' },
                    management: { baseUrl: '' }
                }
            };
            const projected = appContext.createDocsViewerAppContext({
                appKind: 'review',
                routeConfig
            });
            const services = serviceContext.createDocsViewerServiceContext({
                routeContext: {
                    appContext: projected,
                    docsViewerConfigUrl: '/docs-viewer/config/defaults/docs-viewer-config.json',
                    routeConfig
                }
            });
            return {
                kind: projected.kind,
                allowScopeQuery: projected.routeAccess.allowScopeQuery,
                managementUi: projected.routeAccess.managementUi,
                backendCapabilities: projected.backendCapabilities,
                availability: projected.serviceAvailability,
                generatedAuthority: services.generatedData.authority,
                generatedBaseUrl: services.generatedData.baseUrl,
                source: services.source,
                management: services.management
            };
        }"""
    )
    if result != {
        "kind": "review",
        "allowScopeQuery": False,
        "managementUi": False,
        "backendCapabilities": None,
        "availability": {
            "generatedData": {"available": True, "local": True},
            "source": {"available": True},
            "management": {"available": False},
        },
        "generatedAuthority": "local generated-read service",
        "generatedBaseUrl": "http://127.0.0.1:8776",
        "source": {
            "available": True,
            "authority": "source service endpoint; backend capability-gated",
            "baseUrl": "http://127.0.0.1:8776",
        },
        "management": None,
    }:
        raise AssertionError(f"app/service context authority projection changed: {result!r}")


def assert_view_mode_control_registry(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const { viewRegistry, mainViewRenderer, routeFeatures } = window.__docsViewerRouterModuleSmoke;
            const publicContext = {
                kind: 'public',
                featurePolicy: routeFeatures.normalizeDocsViewerRouteFeatures(['bookmarks'])
            };
            const manageContext = {
                kind: 'manage',
                featurePolicy: routeFeatures.normalizeDocsViewerRouteFeatures(['bookmarks', 'source-editing', 'management'])
            };
            const manageDefinitions = {
                modes: [{
                    id: 'markdown-source', ownerViewId: 'rendered-document', appKinds: ['manage'], features: ['source-editing']
                }],
                controls: [
                    { id: 'edit', ownerType: 'view', surfaceId: 'main-view', ownerViewId: 'rendered-document', modeIds: ['rendered-document'], appKinds: ['manage'], features: ['management'] },
                    { id: 'source-add-image', ownerType: 'view', surfaceId: 'main-view', ownerViewId: 'rendered-document', modeIds: ['markdown-source'], appKinds: ['manage'], features: ['source-editing'] },
                    { id: 'source-add-file', ownerType: 'view', surfaceId: 'main-view', ownerViewId: 'rendered-document', modeIds: ['markdown-source'], appKinds: ['manage'], features: ['source-editing'] },
                    { id: 'markdown-source', ownerType: 'view', surfaceId: 'main-view', ownerViewId: 'rendered-document', modeIds: ['rendered-document', 'markdown-source'], appKinds: ['manage'], features: ['source-editing'] },
                    { id: 'save-markdown-source', ownerType: 'view', surfaceId: 'main-view', ownerViewId: 'rendered-document', modeIds: ['markdown-source'], appKinds: ['manage'], features: ['source-editing'] },
                    { id: 'viewer-app-control', ownerType: 'app', surfaceId: 'app-viewer', appKinds: ['manage'] },
                    { id: 'index-view-control', ownerType: 'view', surfaceId: 'index-view', ownerViewId: 'index-tree', appKinds: ['manage'] }
                ]
            };
            const definitionSets = [viewRegistry.createDocsViewerSharedViewDefinitions(), manageDefinitions];
            const publicRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets,
                projectionInputs: { appContext: publicContext }
            });
            const manageRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets,
                projectionInputs: { appContext: manageContext }
            });
            const narrowedRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets,
                projectionInputs: { appContext: publicContext },
                routePolicy: { hiddenControls: ['bookmark', 'info'] }
            });
            const capabilityRegistry = viewRegistry.createDocsViewerViewRegistry({
                definitionSets: [
                    viewRegistry.createDocsViewerSharedViewDefinitions(),
                    { controls: [{
                        id: 'capability-control',
                        ownerType: 'view',
                        surfaceId: 'main-view',
                        ownerViewId: 'rendered-document',
                        requiredCapabilities: ['documents.write']
                    }] }
                ],
                projectionInputs: {
                    appContext: publicContext,
                    backendCapabilities: { documents: { write: false } }
                }
            });
            const mount = document.createElement('div');
            const toolbarMount = document.createElement('div');
            mainViewRenderer.renderDocsViewerMainView({ document, mount, toolbarMount, viewRegistry: narrowedRegistry });
            let duplicateRejected = false;
            let missingOwnerRejected = false;
            let mismatchedSurfaceRejected = false;
            let unknownPolicyRejected = false;
            try {
                viewRegistry.createDocsViewerViewRegistry({
                    definitionSets: [
                        viewRegistry.createDocsViewerSharedViewDefinitions(),
                        { views: [{ id: 'rendered-document', panel: 'main' }] }
                    ],
                    projectionInputs: { appContext: publicContext }
                });
            } catch (error) {
                duplicateRejected = /Duplicate Docs Viewer view/.test(String(error && error.message || ''));
            }
            try {
                viewRegistry.createDocsViewerViewRegistry({
                    definitionSets: [
                        viewRegistry.createDocsViewerSharedViewDefinitions(),
                        { controls: [{ id: 'missing-owner', surfaceId: 'app-viewer' }] }
                    ],
                    projectionInputs: { appContext: publicContext }
                });
            } catch (error) {
                missingOwnerRejected = /requires ownerType app or view/.test(String(error && error.message || ''));
            }
            try {
                viewRegistry.createDocsViewerViewRegistry({
                    definitionSets: [
                        viewRegistry.createDocsViewerSharedViewDefinitions(),
                        { controls: [{
                            id: 'mismatched-surface',
                            ownerType: 'view',
                            surfaceId: 'index-view',
                            ownerViewId: 'rendered-document'
                        }] }
                    ],
                    projectionInputs: { appContext: publicContext }
                });
            } catch (error) {
                mismatchedSurfaceRejected = /surface that does not match/.test(String(error && error.message || ''));
            }
            try {
                viewRegistry.createDocsViewerViewRegistry({
                    definitionSets,
                    projectionInputs: { appContext: publicContext },
                    routePolicy: { hiddenControls: ['invented-control'] }
                });
            } catch (error) {
                unknownPolicyRejected = /Unknown Docs Viewer route-policy control/.test(String(error && error.message || ''));
            }
            const appControl = manageRegistry.projectControls({
                surfaceId: 'app-viewer',
                controlStateById: {
                    'viewer-app-control': { hidden: 1, disabled: 0, label: ' Active ', count: '4', ignored: true }
                }
            }).find((control) => control.id === 'viewer-app-control');
            return {
                appControl: { id: appControl.id, state: appControl.state },
                capabilityDenied: !capabilityRegistry.resolveControl('capability-control', {
                    activeViewId: 'rendered-document', activeModeId: 'rendered-document'
                }).available,
                duplicateRejected,
                emptyToolbar: toolbarMount.querySelector('#docsViewerMainViewToolbar') === null,
                indexViewControls: manageRegistry.projectControls({
                    surfaceId: 'index-view', activeViewId: 'index-tree'
                }).map((control) => control.id),
                manageMarkdownMode: manageRegistry.resolveMode('markdown-source').available,
                manageRenderedControls: manageRegistry.projectControls({
                    surfaceId: 'main-view', activeViewId: 'rendered-document', activeModeId: 'rendered-document'
                }).map((control) => control.id),
                manageSourceControls: manageRegistry.projectControls({
                    surfaceId: 'main-view', activeViewId: 'rendered-document', activeModeId: 'markdown-source'
                }).map((control) => control.id),
                mismatchedSurfaceRejected,
                missingOwnerRejected,
                publicEdit: publicRegistry.resolveControl('edit', {
                    activeViewId: 'rendered-document', activeModeId: 'rendered-document'
                }).available,
                publicMarkdownMode: publicRegistry.resolveMode('markdown-source').available,
                unknownPolicyRejected
            };
        }"""
    )
    expected = {
        "appControl": {
            "id": "viewer-app-control",
            "state": {"hidden": True, "disabled": False, "label": "Active", "count": 4},
        },
        "capabilityDenied": True,
        "duplicateRejected": True,
        "emptyToolbar": True,
        "indexViewControls": ["index-view-control"],
        "manageMarkdownMode": True,
        "manageRenderedControls": ["bookmark", "info", "edit", "markdown-source"],
        "manageSourceControls": [
            "info",
            "source-add-image",
            "source-add-file",
            "markdown-source",
            "save-markdown-source",
        ],
        "mismatchedSurfaceRejected": True,
        "missingOwnerRejected": True,
        "publicEdit": False,
        "publicMarkdownMode": False,
        "unknownPolicyRejected": True,
    }
    if result != expected:
        raise AssertionError(f"view/mode/control registry projection changed: {result!r}")


def assert_configured_scope_provider(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { appComposition, configuredScopeProvider } = window.__docsViewerRouterModuleSmoke;
            const calls = [];
            const generatedData = {
                readDocsIndexTree: (options) => { calls.push(['index', options]); return Promise.resolve({ docs: [] }); },
                readDocumentPayload: (doc, options) => { calls.push(['document', doc.doc_id, options]); return Promise.resolve({ doc_id: doc.doc_id }); },
                readSearchIndex: (options) => { calls.push(['search', options]); return Promise.resolve({ entries: [] }); },
                readRecent: (options) => { calls.push(['recent', options]); return Promise.resolve({ docs: [] }); },
                readReferencesIndex: (options) => { calls.push(['references-index', options]); return Promise.resolve({ targets: [] }); },
                readReferenceTarget: (options) => { calls.push(['reference-target', options]); return Promise.resolve({ docs: [] }); }
            };
            let viewerScope = 'alpha';
            const scopeConfig = {
                scopeConfigsById: new Map([
                    ['alpha', {
                        scopeId: 'alpha',
                        indexTreeUrl: '/data/alpha/index-tree.json',
                        recentUrl: '/data/alpha/recent.json',
                        searchIndexUrl: '/search/alpha/index.json'
                    }],
                    ['beta', {
                        scopeId: 'beta',
                        indexTreeUrl: '/data/beta/index-tree.json',
                        recentUrl: '/data/beta/recent.json',
                        searchIndexUrl: '/search/beta/index.json'
                    }]
                ])
            };
            const readOnly = configuredScopeProvider.createDocsViewerConfiguredScopeProvider({
                generatedData,
                scopeConfig,
                viewerScope: () => viewerScope,
                window
            });
            await readOnly.readIndex();
            await readOnly.readDocument({ doc_id: 'doc-a', content_url: '/data/alpha/by-id/doc-a.json' });
            await readOnly.readSearch();
            await readOnly.readRecent();
            await readOnly.readReferences({ scope: 'beta' });
            await readOnly.readReferences({
                scope: 'beta',
                target: { target_kind: 'work', target_id: 'a b' }
            });
            viewerScope = 'beta';
            await readOnly.readIndex();

            const sourceCalls = [];
            const withSource = configuredScopeProvider.createDocsViewerConfiguredScopeProvider({
                generatedData,
                scopeConfig,
                viewerScope: () => viewerScope,
                window,
                source: {
                    readSource: (docId, options) => { sourceCalls.push(['read', docId, options]); return Promise.resolve({ doc_id: docId }); },
                    writeSource: (payload, options) => { sourceCalls.push(['write', payload.doc_id, options]); return Promise.resolve({ doc_id: payload.doc_id }); },
                    readDiagramSources: (docId, options) => { sourceCalls.push(['read-diagrams', docId, options]); return Promise.resolve({ sources: [] }); },
                    openDiagramSource: (payload, options) => { sourceCalls.push(['open-diagram', payload.media_identity, options]); return Promise.resolve({ ok: true }); },
                    listStagedMedia: (kind, options) => { sourceCalls.push(['list-media', kind, options]); return Promise.resolve({ files: [] }); },
                    previewStagedMedia: (payload, options) => { sourceCalls.push(['preview-media', payload.staged_filename, options]); return Promise.resolve(payload); },
                    applyStagedMedia: (payload, options) => { sourceCalls.push(['apply-media', payload.staged_filename, options]); return Promise.resolve(payload); }
                }
            });
            await withSource.readSource('doc-b');
            await withSource.writeSource({ doc_id: 'doc-b', source_body: '# B' });
            await withSource.readDiagramSources('doc-b');
            await withSource.openDiagramSource({ doc_id: 'doc-b', media_identity: 'docs/beta/svg/diagram.svg' });
            await withSource.listStagedMedia('image');
            await withSource.previewStagedMedia({ staged_filename: 'diagram.svg' });
            await withSource.applyStagedMedia({ staged_filename: 'diagram.svg' });
            const packageProvider = {
                readIndex: () => Promise.resolve({ docs: [] }),
                readDocument: () => Promise.resolve({ doc_id: 'package-doc' })
            };
            let providerContext = null;
            const injected = appComposition.createDocsViewerCollectionProvider({
                createCollectionProvider: (context) => {
                    providerContext = context;
                    return packageProvider;
                },
                generatedData,
                routeContext: { appContext: { kind: 'review' } },
                routeSession: {},
                scopeConfig,
                serviceContext: { generatedData: { available: true } },
                source: null,
                viewerScope: () => 'package-001',
                window
            });
            let invalidProviderRejected = false;
            try {
                appComposition.createDocsViewerCollectionProvider({
                    createCollectionProvider: () => ({ readIndex: () => Promise.resolve({ docs: [] }) })
                });
            } catch (error) {
                invalidProviderRejected = /requires readDocument/.test(String(error && error.message || ''));
            }
            return {
                calls,
                injectedProvider: injected === packageProvider,
                invalidProviderRejected,
                providerContext: {
                    appKind: providerContext.routeContext.appContext.kind,
                    generatedData: providerContext.generatedData === generatedData,
                    serviceContext: providerContext.serviceContext.generatedData.available,
                    viewerScope: providerContext.viewerScope()
                },
                readOnlyKeys: Object.keys(readOnly).sort(),
                sourceCalls,
                withSourceKeys: Object.keys(withSource).sort()
            };
        }"""
    )
    expected_read_only_keys = [
        "readDocument",
        "readIndex",
        "readRecent",
        "readReferences",
        "readSearch",
    ]
    if result["readOnlyKeys"] != expected_read_only_keys:
        raise AssertionError(f"read-only provider exposed optional source methods: {result!r}")
    expected_source_keys = [
        "applyStagedMedia",
        "listStagedMedia",
        "openDiagramSource",
        "previewStagedMedia",
        *expected_read_only_keys,
        "readDiagramSources",
        "readSource",
        "writeSource",
    ]
    if result["withSourceKeys"] != sorted(expected_source_keys):
        raise AssertionError(f"source provider method projection changed: {result!r}")
    if result["injectedProvider"] is not True or result["invalidProviderRejected"] is not True:
        raise AssertionError(f"code-owned collection provider injection changed: {result!r}")
    if result["providerContext"] != {
        "appKind": "review",
        "generatedData": True,
        "serviceContext": True,
        "viewerScope": "package-001",
    }:
        raise AssertionError(f"collection provider context projection changed: {result!r}")
    if result["calls"] != [
        ["index", {"indexTreeUrl": "/data/alpha/index-tree.json", "viewerScope": "alpha"}],
        ["document", "doc-a", {"docId": "doc-a", "viewerScope": "alpha"}],
        ["search", {"searchIndexUrl": "/search/alpha/index.json", "viewerScope": "alpha"}],
        ["recent", {"recentUrl": "/data/alpha/recent.json", "viewerScope": "alpha"}],
        ["references-index", {"baseUrl": "/data/beta", "viewerScope": "beta"}],
        ["reference-target", {
            "staticUrl": "/data/beta/references/by-target/work/a%20b.json",
            "targetKind": "work",
            "targetSlug": "a%20b",
            "viewerScope": "beta",
        }],
        ["index", {"indexTreeUrl": "/data/beta/index-tree.json", "viewerScope": "beta"}],
    ]:
        raise AssertionError(f"configured-scope provider transport delegation changed: {result!r}")
    if result["sourceCalls"] != [
        ["read", "doc-b", {"scope": "beta"}],
        ["write", "doc-b", {"scope": "beta"}],
        ["read-diagrams", "doc-b", {"scope": "beta"}],
        ["open-diagram", "docs/beta/svg/diagram.svg", {"scope": "beta"}],
        ["list-media", "image", {"scope": "beta"}],
        ["preview-media", "diagram.svg", {"scope": "beta"}],
        ["apply-media", "diagram.svg", {"scope": "beta"}],
    ]:
        raise AssertionError(f"configured-scope provider source delegation changed: {result!r}")


def assert_phase_five_runtime_owners(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const modules = window.__docsViewerRouterModuleSmoke;
            const session = modules.appSession.createDocsViewerAppSession({
                defaultRecentLimit: 10,
                panelLayout: {
                    indexPanelState: () => 'normal',
                    projectViewState: () => ({})
                },
                routeContext: {
                    appContext: { kind: 'manage', routeAccess: { managementUi: true } }
                },
                searchBatchSize: 50,
                window: {}
            });
            const removedFacadeFields = {
                panelExpanded: session.domains.panelView.has('expandedDocIds'),
                panelRegistry: session.domains.panelView.has('viewRegistry'),
                documentStatusMap: session.domains.documentIndex.has('uiStatusByValue'),
                managementContext: session.domains.management.has('managementContext'),
                managementEmoji: session.domains.management.has('docNonViewableEmoji'),
                generatedCapabilities: session.domains.generatedData.has('managementCapabilities'),
                generatedOwnCapabilities: session.domains.generatedData.has('generatedDataCapabilities'),
                generatedReload: session.domains.generatedData.has('reloadNonce'),
                busyMessage: session.domains.busyStatus.has('managementMessage')
            };

            const statusRoot = document.createElement('div');
            const status = document.createElement('p');
            const statusState = { pendingBusyCount: 0 };
            const statusOwner = modules.statusController.createDocsViewerStatusController({
                root: statusRoot,
                state: statusState,
                status
            });
            statusOwner.setStatus('Working', true);
            const stopFirst = statusOwner.startBusy();
            const stopSecond = statusOwner.startBusy();
            stopFirst();
            stopFirst();
            const nestedBusyCount = statusState.pendingBusyCount;
            stopSecond();

            const generatedOwner = modules.generatedDataRuntime.createDocsViewerGeneratedDataRuntime({
                generatedBaseUrl: 'http://127.0.0.1:9999',
                generatedData: session.domains.generatedData,
                management: session.domains.management,
                selectedDocument: session.domains.selectedDocument,
                viewerScope: 'studio',
                window: {
                    fetch: () => Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            capabilities: {
                                generated_data_reads: true,
                                scopes: { studio: { available: true, generated_data_reads: true } }
                            }
                        })
                    }),
                    setTimeout
                }
            });
            const generatedReadAvailable = await generatedOwner.checkGeneratedDataReadCapability('studio');

            const featurePolicy = modules.routeFeatures.normalizeDocsViewerRouteFeatures([
                'bookmarks', 'source-editing', 'management'
            ]);
            const registry = modules.viewRegistry.createDocsViewerViewRegistry({
                definitionSets: [
                    modules.viewRegistry.createDocsViewerSharedViewDefinitions(),
                    {
                        modes: [{
                            id: 'markdown-source',
                            ownerViewId: 'rendered-document',
                            appKinds: ['manage'],
                            features: ['source-editing']
                        }],
                        controls: [{
                            id: 'save-markdown-source',
                            ownerType: 'view',
                            surfaceId: 'main-view',
                            ownerViewId: 'rendered-document',
                            modeIds: ['markdown-source'],
                            appKinds: ['manage'],
                            features: ['source-editing']
                        }]
                    }
                ],
                projectionInputs: { appContext: { kind: 'manage', featurePolicy } }
            });
            const viewState = { panels: { main: { activeViewId: 'rendered-document' } } };
            let controlProjectionCount = 0;
            const coordinator = modules.documentViewCoordinator.createDocsViewerDocumentViewCoordinator({
                appContext: { kind: 'manage', featurePolicy },
                buildTrail: () => [],
                collectionProvider: {},
                documentIndex: { allDocsById: new Map(), docsById: new Map() },
                infoPanelRefs: { body: document.createElement('div') },
                mount: document.createElement('div'),
                panelLayout: {
                    projectInfoPanel: () => {},
                    projectViewState: () => viewState,
                    setActiveMainView: () => ({ id: 'rendered-document' })
                },
                panelView: { viewState },
                projectMainView: () => {},
                projectControlStates: () => { controlProjectionCount += 1; },
                root: document.createElement('div'),
                scopeConfig: { uiStatusByValue: new Map() },
                selectedDocument: { payloadCache: new Map(), selectedDocId: '' },
                showWarning: () => {},
                sourceEditorServices: null,
                viewRegistry: registry,
                viewerScope: 'studio',
                viewerTargetDocId: (docId) => docId,
                viewerUrl: () => ''
            });
            coordinator.requestDocumentMode('markdown-source', { warn: false });

            return {
                activeMode: coordinator.activeViewState().activeModeId,
                busyAfterStop: statusState.pendingBusyCount,
                busyDataset: statusRoot.dataset.docsViewerBusy,
                controlProjectionCount,
                generatedReadAvailable,
                generatedStateSeparated: Boolean(
                    session.domains.generatedData.generatedDataCapabilities
                    && session.domains.management.managementCapabilities === null
                ),
                nestedBusyCount,
                removedFacadeFields,
                saveControlActive: coordinator.controlActive('save-markdown-source'),
                statusError: status.classList.contains('is-error'),
                statusText: status.textContent
            };
        }"""
    )
    expected = {
        "activeMode": "markdown-source",
        "busyAfterStop": 0,
        "busyDataset": "false",
        "controlProjectionCount": 3,
        "generatedReadAvailable": True,
        "generatedStateSeparated": True,
        "nestedBusyCount": 1,
        "removedFacadeFields": {
            "panelExpanded": False,
            "panelRegistry": False,
            "documentStatusMap": False,
            "managementContext": False,
            "managementEmoji": False,
            "generatedCapabilities": False,
            "generatedOwnCapabilities": True,
            "generatedReload": False,
            "busyMessage": False,
        },
        "saveControlActive": True,
        "statusError": True,
        "statusText": "Working",
    }
    if result != expected:
        raise AssertionError(f"Phase 5 runtime owner contract changed: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(route_url(base_url, "/404.html"), wait_until="domcontentloaded")
    install_fixture(page)
    assert_missing_doc_history(page)
    assert_route_config_scope_default(page)
    assert_route_feature_projection_and_startup(page)
    assert_explicit_app_and_service_context(page)
    assert_view_mode_control_registry(page)
    assert_control_surface_host(page)
    assert_app_shell_control_surface_mounts(page)
    assert_configured_scope_provider(page)
    assert_phase_five_runtime_owners(page)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=Path("."))
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()

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
                run_smoke(page, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer router module smoke: {errors!r}")
    print("Docs Viewer router module smoke OK")


if __name__ == "__main__":
    main()
