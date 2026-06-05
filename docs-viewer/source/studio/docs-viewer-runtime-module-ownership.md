---
doc_id: docs-viewer-runtime-module-ownership
title: Docs Viewer Runtime Module Ownership
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: reference
parent_id: docs-viewer-runtime-boundary
viewable: true
---
# Docs Viewer Runtime Module Ownership

This document records the grouped runtime module owner map for [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).
It is intentionally grouped by responsibility.
Use [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) for row-level risk scores, score history, and detailed evidence.

## Ownership Rules

- Extracted helper modules must not import route entrypoints or mutate private runtime coordinator state directly.
- Public-safe modules must not import manage-owned modules, management service clients, report registries, source editors, import workflows, settings, scope lifecycle, or manage-only CSS assumptions.
- The management controller receives a narrow context API through the neutral lazy-controller adapter so public read-only viewers do not download or execute management-only orchestration.
- Route workflow commands are exposed only through the private route workflow command contract, backed by explicit route-session, scope-config, document-index, selected-document, search/recent, and status inputs.
- The returned app handle stays intentionally small: `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`.

## Entrypoints And Boot

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Public entrypoint | `docs-viewer-public.js` | Starts the public app boot path and does not import manage-owned hosted views, shell renderers, reports, source editor, import, settings, or scope lifecycle modules. |
| Manage entrypoint | `docs-viewer-manage.js` | Supplies manage-owned document extras, hosted views, shell composition, and starts the manage app boot path. |
| App boot | `docs-viewer-app-boot.js` | Root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, and runtime startup. |
| App composition | `docs-viewer-app-composition.js` | Runtime defaults, service-context handoff, hosted-view registry creation, panel layout creation, app-session creation, generated-data runtime creation, config-service creation, document-index state creation, startup authority records, and initial startup sequencing. |
| App session | `docs-viewer-app-session.js` | State defaults, named state-domain facades, public/manage route-session projection, and runtime-internal state object while remaining controller handoffs are narrowed. |
| Private runtime coordinator | `docs-viewer-app-runtime.js` | Focused controller construction, callback handoff, config/controller bridges, event handler definitions, private management/startup route callbacks, and the small returned app handle. |

## Route, Data, And Config

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Route workflow | `docs-viewer-route-workflow.js` | Current URL/query helpers, current-doc resolution, route application, canonical URL correction, document index load orchestration, payload load orchestration, route-link handling, popstate coordination, and private route command contract. |
| Route context/config | `docs-viewer-app-context.js`, `docs-viewer-route-config.js`, `docs-viewer-access.js` | Route context, explicit route config shape, browser-safe registry resolution, route/scope projection, and static public/manage/manage-local access projection. |
| Config controller/service | `docs-viewer-config-controller.js`, `docs-viewer-config-service.js` | Browser-safe config/UI-text loading, scope route projection, scope picker projection, UI-text merge, recent-limit/status-label projection, and config fetch/retry behavior. |
| Generated-data runtime | `docs-viewer-generated-data-runtime.js` | Generated-data request option shaping, generated-read capability caching, reload/retry option projection, generated-search read capability checks, and named read methods for generated JSON payloads. |
| Low-level data primitives | `docs-viewer-data.js` | Low-level JSON fetch/retry and generated-read reload path primitives reserved for generated-data runtime and config-service owners. |
| Asset URL projection | `docs-viewer-asset-url.js` | Asset-version URL projection shared by boot, route config, route context, report registry, config-service, and generated-data runtime owners. |
| Document index state | `docs-viewer-document-index-state.js` | Document visibility/loadability projection, non-viewable/manage-only tree filtering, non-loadable fallback resolution, default-doc selection, and index status projection. |

## Shell, Panels, And Hosted Views

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Shared app shell | `docs-viewer-app-shell.js` | Public-safe JavaScript-owned shell composition before route behavior wiring; manage renderers are supplied by the manage entrypoint. |
| Manage shell composition | `docs-viewer-management-shell-composition.js`, `docs-viewer-management-shell-renderer.js`, `docs-viewer-management-document-actions-renderer.js` | Manage-owned renderer bundle, context menu, metadata modal, import modal, settings modal, import host refs, status pills, `Edit`, and `Markdown source` controls. |
| Panel layout/view state | `docs-viewer-panel-layout.js`, `docs-viewer-view-state.js` | App-shell panel projection and index/main/info view-state skeleton. |
| Hosted-view registry | `docs-viewer-hosted-views.js`, `docs-viewer-management-hosted-views.js` | Minimal hosted-view registration, public-safe built-in records, access/availability checks, graceful absence, and manage-owned records such as `markdown-source`. |
| Main-view host | `docs-viewer-main-view-host.js`, `docs-viewer-view-context.js` | Main-view availability checks, active view projection, switch-intent handling, toolbar handoff, selected-document context projection, and capability-gated source-editor service slots. |
| Info-panel host | `docs-viewer-info-panel-controller.js`, `docs-viewer-info-panel-renderer.js`, `docs-viewer-info-panel-host.js`, `docs-viewer-metadata-info-view.js` | Info toggle/toolbar binding, selected-document hosted-view context, open/close/update behavior, public-safe metadata rendering, and graceful absence. |

## Document, Navigation, Search, And Bookmarks

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Document controller | `docs-viewer-document-controller.js` | Rendered-document visibility, loading/missing/error states, final payload rendering, selected-document projection, search/recent pane handoff, and optional document-extras hook. |
| Sidebar/tree rendering | `docs-viewer-sidebar.js`, `docs-viewer-tree.js` | Sidebar tree rendering, breadcrumb metadata rendering, expanded-row projection, selected-document highlighting, pure tree and visibility helpers. |
| Search/recent | `docs-viewer-search-controller.js`, `docs-viewer-search.js` | Search index loading, result rendering, recent rendering, debounce behavior, search/recent state-domain input, route command consumption, more-results behavior, and pane command requests. |
| Bookmarks/favourites | `docs-viewer-bookmarks.js`, `docs-viewer-favourites.js` | Bookmark state, rendering, IndexedDB storage orchestration, bookmark events, selected-document bookmark UI projection, route command consumption, and bookmark record storage helpers. |
| Read-oriented rendering | `docs-viewer-render.js` | Result and bookmark markup helpers imported by entry and bookmark controllers. |
| URL primitives | `docs-viewer-router.js` | Low-level URL building, anchor route parsing, browser history writes, requested-doc resolution, canonical route correction, popstate helper behavior, and payload-load helper behavior. |

## Manage-Only Runtime

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Lazy management boundary | `docs-viewer-runtime-lazy-controller.js` | Neutral lazy-controller loading, named management state-domain, service-client, and route-reload contracts, and gated management controller import. |
| Management controller | `docs-viewer-management.js` and child modules | Management-local facade, capability checks, action/menu/modal coordination, imports, settings, scope lifecycle, status pills, and write orchestration. |
| Management client | `docs-viewer-management-client.js` | Docs Viewer service transport helpers used by management controller workflows. |
| Management render helpers | `docs-viewer-management-render.js` | Management-only markup helpers imported by management controller. |
| Drag/drop | `docs-viewer-drag-drop.js` | Drag/drop helpers used by the management controller. |
| Manage reports | `docs-viewer-management-document-reports.js`, `docs-viewer-report-service.js`, `docs-viewer/runtime/js/reports/*` | Manage-owned report mounting, report-context construction, report registry URL handoff, local report-service creation, and report endpoint access. |
| Source editor | `docs-viewer/runtime/js/modules/source-editor/source-editor.js` | Manage-only source-body editor rendering, dirty-state handling, rebuild submission, diagnostics, and rendered-view return behavior. |
| Docs import | `docs-html-import.js`, `docs-html-import-workflow.js`, `docs-html-import-render.js`, `docs-html-import-modals.js` | Docs Import modal state, preview/write orchestration, overwrite prompts, result rendering, and modal behavior behind management service contracts. |

## Public Index Slimming Ownership

The current payload-loading ownership after public index slimming is:

- `docs-viewer-generated-data-runtime.js` owns named reads for docs index tree, selected by-id payloads, recently-added payloads, search indexes, references indexes, and reference-target buckets.
- `docs-viewer-tree-payload-adapter.js` owns normalizing `index-tree.json` and `recently-added.json` payloads into the runtime record shape.
- `docs-viewer-document-index-state.js` owns public/manage visibility filtering, manage-only tree-root omission, non-loadable fallback resolution, default-doc selection, and index status projection after the normalized tree payload is loaded.
- `docs-viewer-route-workflow.js` owns route application, `index-tree.json` loading orchestration, selected-document payload loading, URL/history writes, and missing/error projection through its private route command contract.
- `docs-viewer-search-controller.js` owns search and recently-added rendering while delegating generated search/recent payload reads to `docs-viewer-generated-data-runtime.js`.
- `docs-viewer-view-context.js` and `docs-viewer-metadata-info-view.js` hydrate and render info-panel metadata from selected by-id payloads rather than tree rows or public `index.json`.
- Public-safe modules must not import manage-owned metadata, report, source-editor, import, settings, scope lifecycle, or management client modules.
