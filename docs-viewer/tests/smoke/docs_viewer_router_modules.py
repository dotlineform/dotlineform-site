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
            window.__docsViewerRouterModuleSmoke = { router, routeConfig, appContext, serviceContext, configuredScopeProvider, routeFeatures, appComposition, toolbarRenderer, configController, viewRegistry, mainViewRenderer };
        }"""
    )


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
        """() => {
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
                    'recently-added',
                    'bookmarks',
                    'reports'
                ],
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
                    recently_added_url: '/assets/data/docs/scopes/library/recently-added.json',
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
                recentlyAddedUrl: '/assets/data/docs/scopes/library/recently-added.json',
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
            const { routeConfig, routeFeatures, appComposition, toolbarRenderer, configController } = window.__docsViewerRouterModuleSmoke;
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
            const searchToolbarMount = document.createElement('div');
            toolbarRenderer.renderDocsViewerViewerToolbar({
                document,
                mount: searchToolbarMount,
                routeContext: { appContext: { featurePolicy: selected } }
            });
            const recentOnly = routeFeatures.normalizeDocsViewerRouteFeatures(['recently-added']);
            const recentToolbarMount = document.createElement('div');
            toolbarRenderer.renderDocsViewerViewerToolbar({
                document,
                mount: recentToolbarMount,
                routeContext: { appContext: { featurePolicy: recentOnly } }
            });
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
                        docs_viewer: { recently_added_limit: 7 }
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
                    recent: resolvedMinimalRoute.recentlyAddedUrl,
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
    if result["selected"]["search"] is not True or result["selected"]["recentlyAdded"] is not False:
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
                    { id: 'edit', ownerViewId: 'rendered-document', modeIds: ['rendered-document'], appKinds: ['manage'], features: ['management'] },
                    { id: 'markdown-source', ownerViewId: 'rendered-document', modeIds: ['rendered-document', 'markdown-source'], appKinds: ['manage'], features: ['source-editing'] },
                    { id: 'save-markdown-source', ownerViewId: 'rendered-document', modeIds: ['markdown-source'], appKinds: ['manage'], features: ['source-editing'] }
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
                    definitionSets,
                    projectionInputs: { appContext: publicContext },
                    routePolicy: { hiddenControls: ['invented-control'] }
                });
            } catch (error) {
                unknownPolicyRejected = /Unknown Docs Viewer route-policy control/.test(String(error && error.message || ''));
            }
            return {
                capabilityDenied: !capabilityRegistry.resolveControl('capability-control', {
                    activeViewId: 'rendered-document', activeModeId: 'rendered-document'
                }).available,
                duplicateRejected,
                emptyToolbar: toolbarMount.querySelector('#docsViewerMainViewToolbar') === null,
                manageMarkdownMode: manageRegistry.resolveMode('markdown-source').available,
                manageRenderedControls: manageRegistry.projectControls({
                    activeViewId: 'rendered-document', activeModeId: 'rendered-document'
                }).map((control) => control.id).sort(),
                manageSourceControls: manageRegistry.projectControls({
                    activeViewId: 'rendered-document', activeModeId: 'markdown-source'
                }).map((control) => control.id).sort(),
                publicEdit: publicRegistry.resolveControl('edit', {
                    activeViewId: 'rendered-document', activeModeId: 'rendered-document'
                }).available,
                publicMarkdownMode: publicRegistry.resolveMode('markdown-source').available,
                unknownPolicyRejected
            };
        }"""
    )
    expected = {
        "capabilityDenied": True,
        "duplicateRejected": True,
        "emptyToolbar": True,
        "manageMarkdownMode": True,
        "manageRenderedControls": ["bookmark", "edit", "info", "markdown-source"],
        "manageSourceControls": ["info", "markdown-source", "save-markdown-source"],
        "publicEdit": False,
        "publicMarkdownMode": False,
        "unknownPolicyRejected": True,
    }
    if result != expected:
        raise AssertionError(f"view/mode/control registry projection changed: {result!r}")


def assert_configured_scope_provider(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { configuredScopeProvider } = window.__docsViewerRouterModuleSmoke;
            const calls = [];
            const generatedData = {
                readDocsIndexTree: (options) => { calls.push(['index', options]); return Promise.resolve({ docs: [] }); },
                readDocumentPayload: (doc, options) => { calls.push(['document', doc.doc_id, options]); return Promise.resolve({ doc_id: doc.doc_id }); },
                readSearchIndex: (options) => { calls.push(['search', options]); return Promise.resolve({ entries: [] }); },
                readRecentlyAdded: (options) => { calls.push(['recent', options]); return Promise.resolve({ docs: [] }); },
                readReferencesIndex: (options) => { calls.push(['references-index', options]); return Promise.resolve({ targets: [] }); },
                readReferenceTarget: (options) => { calls.push(['reference-target', options]); return Promise.resolve({ docs: [] }); }
            };
            let viewerScope = 'alpha';
            const scopeConfig = {
                scopeConfigsById: new Map([
                    ['alpha', {
                        scopeId: 'alpha',
                        indexTreeUrl: '/data/alpha/index-tree.json',
                        recentlyAddedUrl: '/data/alpha/recently-added.json',
                        searchIndexUrl: '/search/alpha/index.json'
                    }],
                    ['beta', {
                        scopeId: 'beta',
                        indexTreeUrl: '/data/beta/index-tree.json',
                        recentlyAddedUrl: '/data/beta/recently-added.json',
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
            await readOnly.readRecentlyAdded();
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
                    writeSource: (payload, options) => { sourceCalls.push(['write', payload.doc_id, options]); return Promise.resolve({ doc_id: payload.doc_id }); }
                }
            });
            await withSource.readSource('doc-b');
            await withSource.writeSource({ doc_id: 'doc-b', source_body: '# B' });
            return {
                calls,
                readOnlyKeys: Object.keys(readOnly).sort(),
                sourceCalls,
                withSourceKeys: Object.keys(withSource).sort()
            };
        }"""
    )
    expected_read_only_keys = [
        "readDocument",
        "readIndex",
        "readRecentlyAdded",
        "readReferences",
        "readSearch",
    ]
    if result["readOnlyKeys"] != expected_read_only_keys:
        raise AssertionError(f"read-only provider exposed optional source methods: {result!r}")
    if result["withSourceKeys"] != expected_read_only_keys + ["readSource", "writeSource"]:
        raise AssertionError(f"source provider method projection changed: {result!r}")
    if result["calls"] != [
        ["index", {"indexTreeUrl": "/data/alpha/index-tree.json", "viewerScope": "alpha"}],
        ["document", "doc-a", {"docId": "doc-a", "viewerScope": "alpha"}],
        ["search", {"searchIndexUrl": "/search/alpha/index.json", "viewerScope": "alpha"}],
        ["recent", {"recentlyAddedUrl": "/data/alpha/recently-added.json", "viewerScope": "alpha"}],
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
    ]:
        raise AssertionError(f"configured-scope provider source delegation changed: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(route_url(base_url, "/404.html"), wait_until="domcontentloaded")
    install_fixture(page)
    assert_missing_doc_history(page)
    assert_route_config_scope_default(page)
    assert_route_feature_projection_and_startup(page)
    assert_explicit_app_and_service_context(page)
    assert_view_mode_control_registry(page)
    assert_configured_scope_provider(page)


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
