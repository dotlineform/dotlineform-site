---
doc_id: docs-viewer-javascript-inventory
title: Docs Viewer JavaScript Inventory
added_date: 2026-05-20
last_updated: 2026-05-28
ui_status: review
parent_id: studio-javascript-payload-inventory
sort_order: 7020
viewable: true
---
# Docs Viewer JavaScript Inventory

This document is the Docs Viewer-specific review slice of [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory).
It uses the same four-risk scoring model as the parent inventory, but limits the table and follow-up notes to browser JavaScript under `docs-viewer/runtime/js/`.

## Current Summary

Measured on 2026-05-21 from [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).

- Docs Viewer browser JavaScript files in this focused app-shell snapshot: 53
- Files above target score 4: 14
- General risk themes: compatibility runtime coordination, management coordinator growth, import workflow ownership, scope lifecycle, search/bookmark controller boundaries, and future feature panels that must attach to focused owners instead of the compatibility runtime.

| Score | Files |
| ---: | ---: |
| 9 | 0 |
| 8 | 0 |
| 7 | 0 |
| 6 | 7 |
| 5 | 7 |
| 4 | 39 |

## Current Priorities

| Docs rank | Full rank | File | Maint. | Struct. | Perf. | Arch. | Risk | Focus |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | `docs-viewer/runtime/js/docs-viewer-app-runtime.js` | 2 | 2 | 1 | 1 | 6 | Compatibility Docs Viewer runtime coordination after route workflow and runtime-owner extraction; app state defaults, controller construction, config handoff, event binding, initial load sequencing, and returned runtime API remain. |
| 2 | 9 | `docs-viewer/runtime/js/docs-viewer-management-modals.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer management modal controller after transient modal shell and metadata parent-picker extraction. |
| 3 | 15 | `docs-viewer/runtime/js/docs-viewer-management.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer management coordinator after shared action workflow helper extraction. |
| 4 | 18 | `docs-viewer/runtime/js/docs-viewer-bookmarks.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer bookmark/favourite support. |
| 5 | 19 | `docs-viewer/runtime/js/docs-viewer-management-actions.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer management support module. |
| 6 | 20 | `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer runtime support module. |
| 7 | 33 | `docs-viewer/runtime/js/docs-html-import.js` | 2 | 1 | 1 | 2 | 6 | Docs import controller after explicit workflow handoff and focused module-smoke coverage. |
| 8 | 34 | `docs-viewer/runtime/js/docs-html-import-workflow.js` | 2 | 1 | 1 | 1 | 5 | Docs import preview/write workflow helper. |
| 9 | 35 | `docs-viewer/runtime/js/docs-viewer-config-controller.js` | 2 | 1 | 1 | 1 | 5 | Docs Viewer config/scope setup. |
| 10 | 36 | `docs-viewer/runtime/js/docs-viewer-search-controller.js` | 2 | 1 | 1 | 1 | 5 | Docs Viewer search helper or controller. |
| 11 | 54 | `docs-viewer/runtime/js/docs-viewer-document-controller.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer document rendering/controller support. |
| 12 | 55 | `docs-viewer/runtime/js/docs-viewer-reports.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer runtime support module. |
| 13 | 25 | `docs-viewer/runtime/js/reports/docs-broken-links-report.js` | 2 | 1 | 1 | 1 | 5 | Docs Broken Links report module after the old Studio route controller was retired. |
| 14 | 56 | `docs-viewer/runtime/js/docs-viewer-router.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer routing and history helper. |
| new | new | `docs-viewer/runtime/js/docs-viewer-route-workflow.js` | 1 | 1 | 1 | 1 | 4 | Focused route/document workflow owner for URL/query helpers, current-doc resolution, route application, index and payload loading, route-link handling, and popstate coordination. |
| new | new | `docs-viewer/runtime/js/docs-viewer-service-context.js` | 1 | 1 | 1 | 1 | 4 | Focused public/manage service-context projection owner; public contexts omit management and local generated-read backend surfaces. |
| new | new | `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` | 1 | 1 | 1 | 1 | 4 | Focused generated-data request/capability owner for data request options, generated-read checks, retry/reload options, generated-search read capability projection, and named generated JSON read methods. |
| new | new | `docs-viewer/runtime/js/docs-viewer-document-index-state.js` | 1 | 1 | 1 | 1 | 4 | Focused document-index projection owner for public/manage visibility filtering, manage-only tree omission, non-loadable fallback resolution, default-doc selection, and index status projection. |
| new | new | `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js` | 1 | 1 | 1 | 1 | 4 | Focused info-panel coordination owner for selected-document context, toggle state, toolbar click handoff, open/update/close behavior, and public-safe availability. |
| new | new | `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js` | 1 | 1 | 1 | 1 | 4 | Neutral lazy-controller adapter used to keep management controller imports gated without loading management-only JS on public routes. |
| new | new | `docs-viewer/runtime/js/docs-viewer-app-composition.js` | 1 | 1 | 1 | 1 | 4 | App-composition owner for runtime defaults, foundational owner creation, public/manage startup phase records, startup authority records, and initial startup sequencing. |
| 15 | 59 | `docs-viewer/runtime/js/docs-html-import-modals.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 16 | 60 | `docs-viewer/runtime/js/docs-html-import-render.js` | 1 | 1 | 1 | 1 | 4 | Docs import result rendering helper. |
| 17 | 61 | `docs-viewer/runtime/js/docs-viewer-data.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 18 | 62 | `docs-viewer/runtime/js/docs-viewer-drag-drop.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 19 | 63 | `docs-viewer/runtime/js/docs-viewer-favourites.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer bookmark/favourite support. |
| 20 | 64 | `docs-viewer/runtime/js/docs-viewer-management-capabilities.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 21 | 65 | `docs-viewer/runtime/js/docs-viewer-management-client.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 22 | 66 | `docs-viewer/runtime/js/docs-viewer-management-config.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 23 | 67 | `docs-viewer/runtime/js/docs-viewer-management-interactions.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 24 | 68 | `docs-viewer/runtime/js/docs-viewer-management-render.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 25 | 69 | `docs-viewer/runtime/js/docs-viewer-render.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer rendering helper. |
| 26 | 70 | `docs-viewer/runtime/js/docs-viewer-search.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer search helper or controller. |
| 27 | 71 | `docs-viewer/runtime/js/docs-viewer-sidebar.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 28 | 72 | `docs-viewer/runtime/js/docs-viewer-tree.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 29 | 73 | `docs-viewer/runtime/js/reports/change-history-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 30 | 74 | `docs-viewer/runtime/js/reports/docs-index-table-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 31 | 75 | `docs-viewer/runtime/js/reports/reports-list-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 32 | 76 | `docs-viewer/runtime/js/reports/semantic-references-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 33 | 77 | `docs-viewer/runtime/js/reports/source-config-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 34 | 152 | `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management normalize-order and viewability target workflow helper. |
| 35 | 153 | `docs-viewer/runtime/js/docs-viewer-index-panel.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer index panel state, persistence migration, toggle projection, and document-pane visibility helper. |
| 36 | 154 | `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned index panel chrome renderer and projection applier. |
| 37 | new | `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned document shell, read-only metadata chrome, and narrow document/search/recent projection applier. |
| 38 | new | `docs-viewer/runtime/js/docs-viewer-app-context.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned route context assembly from route config/access projection and mutable route-context projection. |
| 39 | new | `docs-viewer/runtime/js/docs-viewer-panel-layout.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned compatibility panel projection handoff for index state, current document/search/recent visibility, and the view-state skeleton. |
| 40 | new | `docs-viewer/runtime/js/docs-viewer-route-config.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned route config resolver, migration data-attribute fallback, and route/scope projection helper. |
| 41 | new | `docs-viewer/runtime/js/docs-viewer-access.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned static public/manage/manage-local access projection and hosted-view access check. |
| 42 | new | `docs-viewer/runtime/js/docs-viewer-view-state.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned index/document/info view-state skeleton and projection helper. |
| 43 | new | `docs-viewer/runtime/js/docs-viewer-hosted-views.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned hosted-view registration shape, built-in compatibility records, availability/access checks, and graceful absence. |
| 44 | new | `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned info-panel chrome renderer and projection applier. |
| 45 | new | `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` | 1 | 1 | 1 | 1 | 4 | Info-panel hosted-view lifecycle owner for load, mount, update, unmount, close, and graceful absence. |
| 46 | new | `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` | 1 | 1 | 1 | 1 | 4 | Public-safe read-only metadata info hosted view. |
| 47 | new | `docs-viewer/runtime/js/docs-viewer-view-context.js` | 1 | 1 | 1 | 1 | 4 | Selected-document hosted-view context projector for metadata and planned future info views. |
| 48 | new | `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned management context-menu, metadata modal, import modal, settings modal, and import host renderer. |
| 49 | new | `docs-viewer/runtime/js/docs-viewer-app-boot.js` | 1 | 1 | 1 | 1 | 4 | App boot owner for route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, and runtime startup. |
| 50 | new | `docs-viewer/runtime/js/docs-viewer-app-session.js` | 1 | 1 | 1 | 1 | 4 | App-session owner for state defaults, named state-domain facades, public/manage route-session projection, and the temporary compatibility state bridge. |
| 51 | new | `docs-viewer/runtime/js/docs-viewer.js` | 1 | 1 | 1 | 1 | 4 | Stable Docs Viewer entrypoint wrapper that imports and starts the app boot owner. |

## Follow-Up Notes

### `docs-viewer/runtime/js/docs-viewer.js`

- Current risk score: 4.
- This file is now the shared ES module entrypoint wrapper loaded by route shells.
- 2026-05-27 owner note: management action-area shell coordination moved to `docs-viewer/runtime/js/docs-viewer-app-shell.js`; `docs-viewer.js` only initializes that owner before existing route boot and waits for it before management/theme binding.
- 2026-05-27 owner note: header-control composition moved to `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, coordinated by the app shell before `docs-viewer.js` reads the preserved control IDs.
- 2026-05-27 owner note: index panel chrome composition moved to `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, coordinated by the app shell before `docs-viewer.js` reads the preserved `docsViewerSidebarToggle`, `docsViewerSidebarExpand`, and `docsViewerNav` IDs.
- 2026-05-27 owner note: document shell composition moved to `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`, coordinated by the app shell before `docs-viewer.js` reads the preserved document/meta/search-result IDs. The entry module still orchestrates route boot and passes document-shell refs to focused controllers.
- 2026-05-27 owner note: route dataset normalization and access flag projection moved to `docs-viewer/runtime/js/docs-viewer-app-context.js`; shell ref grouping moved behind `docs-viewer/runtime/js/docs-viewer-app-shell.js`; compatibility panel projection handoff moved to `docs-viewer/runtime/js/docs-viewer-panel-layout.js`. The entry module still owns route boot orchestration, config loading, payload loading, search/recent rendering handoff, bookmark behavior, and lazy management controller loading.
- 2026-05-27 owner note: route config resolution moved to `docs-viewer/runtime/js/docs-viewer-route-config.js`, static access projection moved to `docs-viewer/runtime/js/docs-viewer-access.js`, the index/document/info skeleton moved to `docs-viewer/runtime/js/docs-viewer-view-state.js`, and hosted-view registration moved to `docs-viewer/runtime/js/docs-viewer-hosted-views.js`. `docs-viewer.js` instantiates those owners but still does not own their contracts.
- 2026-05-27 owner note: info-panel chrome moved to `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`, hosted-view lifecycle moved to `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`, selected-document context projection moved to `docs-viewer/runtime/js/docs-viewer-view-context.js`, and metadata rendering moved to `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`. `docs-viewer.js` now passes explicit route/viewer inputs into the context helper and wires open/close events, but should not absorb panel DOM composition, lifecycle, context shaping, or metadata presentation.
- 2026-05-27 owner note: management-only context-menu and modal shell markup moved to `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`, dynamically imported by the app shell only when route access allows management UI. The compatibility runtime passes the rendered refs into the lazy management controller after app-shell initialization but still leaves management workflows and backend capability checks in the existing management modules.
- 2026-05-27 owner note: app boot ownership moved to `docs-viewer/runtime/js/docs-viewer-app-boot.js`, and route/document workflow ownership later moved to `docs-viewer/runtime/js/docs-viewer-route-workflow.js`. `docs-viewer.js` should remain an import-and-start wrapper.
- Useful future slices should reduce shared-runtime coupling or route-load cost, such as generated-payload loading, loadable-doc visibility state, broader panel-layout ownership, or management lazy-boundary hardening.
- Future route/document workflow changes should extend `docs-viewer-route-workflow.js`, not add responsibility back to the entrypoint or compatibility runtime.
- Preserve `docs-viewer/runtime/js/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

### `docs-viewer/runtime/js/docs-viewer-app-boot.js`

- Added 2026-05-27 as the focused app boot owner.
- Keep this module limited to root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, boot failure status projection, and starting the compatibility runtime.
- Do not move route application, generated docs/search reads, search/recent state transitions, bookmark storage, report rendering, backend writes, or management capability checks into it.

### `docs-viewer/runtime/js/docs-viewer-app-runtime.js`

- Added 2026-05-27 as the compatibility owner for the existing shared route/document workflow after the entrypoint became a wrapper.
- Current risk score: 6 after the route/document workflow and compatibility-runtime owner extractions.
- 2026-05-27 owner note: URL/query helpers, current-doc resolution, route application, index-load orchestration, payload-load orchestration, missing/error handoff, route-link handling, and popstate coordination moved to `docs-viewer/runtime/js/docs-viewer-route-workflow.js`.
- 2026-05-27 owner note: search/recent route callback bundling moved behind `createDocsViewerSearchRouteCallbacks(...)` in `docs-viewer/runtime/js/docs-viewer-search-controller.js`; bookmark route callback bundling moved behind `createDocsViewerBookmarkRouteCallbacks(...)` in `docs-viewer/runtime/js/docs-viewer-bookmarks.js`.
- 2026-05-27 owner note: info-panel toolbar click handoff now opens the selected info hosted view through `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`; toolbar rendering and view option projection stay in focused panel/hosted-view modules.
- 2026-05-28 owner note: generated-data request shaping and generated-read capability caching moved to `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`.
- 2026-05-28 owner note: document visibility/loadability projection moved to `docs-viewer/runtime/js/docs-viewer-document-index-state.js`.
- 2026-05-28 owner note: selected-document info-panel coordination moved to `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`.
- 2026-05-28 owner note: lazy management loading and management context assembly moved behind neutral `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`; keep the actual management controller import gated so public routes do not fetch management-only JS.
- 2026-05-28 owner note: app-session and state default creation moved to `docs-viewer/runtime/js/docs-viewer-app-session.js`; `docs-viewer-app-runtime.js` now creates the session, passes the compatibility state bridge to existing controllers, updates the route-session domain during route-global changes, and returns `appSession`.
- 2026-05-28 owner note: service-context projection moved to `docs-viewer/runtime/js/docs-viewer-service-context.js`; public contexts strip management base URLs and local generated-read service base URLs before controllers are assembled.
- 2026-05-28 owner note: route workflow, search controller, and document controller now consume named generated-data read methods instead of assembling fetch/reload/capability bundles locally.
- 2026-05-28 owner note: runtime defaults, service-context handoff, hosted-view registry creation, panel layout creation, app-session creation, generated-data runtime creation, document-index state creation, public/manage startup phase records, startup authority records, and initial startup sequencing moved to `docs-viewer/runtime/js/docs-viewer-app-composition.js`.
- 2026-05-28 owner note: the returned app handle was narrowed to `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`. Broad `state`, app-composition internals, app-session internals, the management lazy loader, and route workflow bridges are no longer returned; management reload/startup flows still receive private callbacks inside the runtime.
- This module now remains the runtime coordinator for focused controller construction, config handoff, focused-controller callback handoff, event handler definitions, private management/startup callback handoff, and the small returned app handle.
- Next risk-reduction slices should focus on complete new owner boundaries for future features, not restore route/document/search/bookmark/info/generated-data/visibility/management workflow behavior here.

### `docs-viewer/runtime/js/docs-viewer-app-composition.js`

- Added 2026-05-28 as the app-composition and startup phase owner.
- Current risk score: 4.
- Keep this module limited to runtime defaults, foundational owner creation, startup phase records, startup authority records, public/manage startup gating, and initial startup sequence orchestration.
- Do not move rendering, validation, generated-read internals, config normalization, bookmark storage, management writes, report behavior, or controller-specific UI behavior into it.
- The compatibility runtime still constructs focused controllers until a later slice narrows controller families away from function-scoped bridge callbacks.

### `docs-viewer/runtime/js/docs-viewer-app-session.js`

- Added 2026-05-28 as the app-session and state-domain owner.
- Current risk score: 4.
- Keep this module limited to app-session creation, state defaults, named domain facades, route-session projection, and the explicit temporary compatibility state bridge.
- Do not move controller construction, event binding, generated reads, URL history, document rendering, bookmark persistence, or management writes into it.
- Future slices should narrow complete controller families to the relevant domain facade and remove their broad-state dependency from runtime handoff.

### `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`

- Added 2026-05-28 as the focused generated-data request owner.
- Current risk score: 4.
- Keep this module limited to data request option shaping, generated-read capability caching, retry/reload option projection, generated-search read capability checks, and named generated JSON read methods for docs indexes, payloads, search indexes, references indexes, and reference-target buckets.
- Do not move config loading, payload rendering, backend write authority, or management capability UI projection into it.

### `docs-viewer/runtime/js/docs-viewer-service-context.js`

- Added 2026-05-28 as the focused public/manage service-context projection owner.
- Current risk score: 4.
- Keep this module limited to projecting static route context into generated-read, config, report, and management service surfaces.
- Public contexts must continue to omit management base URLs, local generated-read service base URLs, backend probes, and management service adapters. Do not move capability truth or write authority into this module.

### `docs-viewer/runtime/js/docs-viewer-document-index-state.js`

- Added 2026-05-28 as the focused document-index projection owner.
- Current risk score: 4.
- Keep this module limited to all-doc/doc map projection, public/manage visibility filtering, hidden/manage-only tree handling, non-loadable fallback resolution, default-doc resolution, and index status projection.
- Do not move route URL state, sidebar DOM rendering, document payload loading, search/recent rendering, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`

- Added 2026-05-28 as the focused info-panel coordination owner.
- Current risk score: 4.
- Keep this module limited to selected-document hosted-view context, metadata-info default open behavior, toggle projection, toolbar click handoff, update-on-document-change, close behavior, and public-safe availability.
- Do not move info-panel chrome rendering, hosted-view registration, metadata presentation, document payload rendering, URL history, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`

- Added 2026-05-28 as a neutral lazy-controller adapter.
- Current risk score: 4.
- Keep this module limited to promise-cached dynamic controller loading and explicit context assembly.
- Do not name this module as management-only or statically import `docs-viewer-management.js` from public-route startup paths; public read-only smokes assert that management-only JS is not fetched.

### `docs-viewer/runtime/js/docs-viewer-route-workflow.js`

- Added 2026-05-27 as the focused route/document workflow owner.
- Current risk score: 4.
- Keep this module limited to URL/query helpers, current-doc resolution, route application, index and payload load orchestration, canonical URL correction, route-link handling, and popstate coordination.
- It should continue to delegate low-level URL/history operations to `docs-viewer/runtime/js/docs-viewer-router.js`, final document pane rendering to `docs-viewer/runtime/js/docs-viewer-document-controller.js`, search/recent rendering to `docs-viewer/runtime/js/docs-viewer-search-controller.js`, bookmark storage/rendering to `docs-viewer/runtime/js/docs-viewer-bookmarks.js`, and management writes/actions to the lazy management modules.

### `docs-viewer/runtime/js/docs-viewer-search-controller.js`

- Current risk score: 5.
- 2026-05-27 owner note: search/recent route callback bundling moved into this focused owner through `createDocsViewerSearchRouteCallbacks(...)`. The controller now consumes explicit route callbacks for route application, history writes, current-doc resolution, default-doc fallback, result URL creation, and loadable-doc target resolution.
- Keep this module focused on generated search-index loading, result/recent rendering, debounce handoff, search/recent route activation, more-results behavior, and pane projection requests.
- Do not move low-level URL construction, browser history primitives, document payload rendering, config loading, management writes, or panel toolbar/view switching into it.

### `docs-viewer/runtime/js/docs-viewer-bookmarks.js`

- Current risk score: 6.
- 2026-05-27 owner note: bookmark route callback bundling moved into this focused owner through `createDocsViewerBookmarkRouteCallbacks(...)`. The controller now consumes explicit route callbacks for search-debounce cancellation and document-load handoff when opening a bookmark.
- Keep this module focused on bookmark loading, IndexedDB support fallback, list/toggle rendering, selected-document bookmark UI projection, edit state, pending focus, bookmark events, route callback consumption, and status-pill fallback callbacks.
- Do not move low-level history construction, document payload rendering, info-panel lifecycle, management writes, or future bookmark grouping/sync/export features into the compatibility runtime.

### `docs-viewer/runtime/js/docs-viewer-app-shell.js`

- Added 2026-05-27 as the app-shell owner for management action-area coordination.
- Current scope is intentionally narrow: render route-provided header controls through `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, render index panel chrome through `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, clear the management action mount, import `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js` only when route intent allows management, and return the rendered rows before existing management/theme binding continues.
- It also renders the document shell through `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js` before existing document, sidebar, bookmark, search, and management controllers read the preserved IDs.
- It also renders the info panel shell through `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`; lifecycle and metadata presentation stay in the focused info-panel host/view modules.
- It also clears and renders the management shell mount through `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` only when route access allows management UI.
- The existing lazy management controller continues to own backend reachability, capability refresh, command wiring, and status projection.
- Revisit the inventory table and score during the next full JavaScript inventory refresh; the expected target score for this focused renderer is 4 or lower while it stays limited to shell rendering.

### `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`

- Added 2026-05-27 as the focused renderer for scope picker, recently-added button, search input, and management-action mount composition.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount from route context.

### `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`

- Added 2026-05-27 as the focused renderer for management action markup.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount.

### `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`

- Added 2026-05-27 as the focused renderer for management-only context menu and modal shell markup.
- Keep this module limited to preserving the existing `docsViewerContextMenu`, metadata modal, import modal, settings modal, and `docsHtmlImport*` host refs inside the management shell mount.
- Do not move metadata save behavior, import workflow behavior, settings writes, context-menu actions, backend reachability checks, generated-data reads, or management capability projection into this renderer.

### `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`

- Added 2026-05-27 as the focused renderer for index panel shell chrome.
- Keep this module limited to rendering the sidebar container, toolbar controls, nav mount, and applying index-panel projection to DOM refs. Do not move tree row rendering, drag/drop behavior, search/recent behavior, or document payload rendering into it.

### `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`

- Added 2026-05-27 as the focused renderer for document shell chrome.
- Keep this module limited to rendering `.docsViewer__main`, read-only metadata chrome, document/search/recent result mounts, and applying the current narrow document/search/recent/results-status projection to DOM refs.
- Do not move Markdown rendering, generated report loading, payload fetching, breadcrumb metadata rendering, status-pill content rendering, bookmark storage, or search/recent result rendering into it.

### `docs-viewer/runtime/js/docs-viewer-app-context.js`

- Added 2026-05-27 as the focused route-context owner for the app shell.
- Keep this module limited to assembling route context from route config/access projection, current URL management/import intent, viewer pathname, and bookmark storage scope.
- Do not move route application, config loading, generated-data fetching, backend capability checks, or write behavior into it.

### `docs-viewer/runtime/js/docs-viewer-panel-layout.js`

- Added 2026-05-27 as the focused compatibility panel projection owner for the app shell.
- Keep this module limited to index panel state storage/projection, current document/search/recent/results-status projection handoff, info-panel visibility/layout projection, and delegation to the view-state skeleton.
- Do not add toolbar controls, hosted-view registration, document payload rendering, search result rendering, or management action behavior to it.

### `docs-viewer/runtime/js/docs-viewer-route-config.js`

- Added 2026-05-27 as the focused route config resolver and route/scope projection helper.
- Keep this module limited to the durable route config shape, browser-safe route-config registry loading/resolution, migration inline/data-attribute fallback, and projection of scope config into route globals.
- Do not add config fetching, URL history changes, payload loading, or backend capability checks to it.

### `docs-viewer/runtime/js/docs-viewer-access.js`

- Added 2026-05-27 as the focused static access projection helper.
- Keep this module limited to public/manage/manage-local route intent, hosted-view access defaults, and access checks.
- Do not add browser-side write authority, per-click permission checks, or backend reachability probing to it.

### `docs-viewer/runtime/js/docs-viewer-view-state.js`

- Added 2026-05-27 as the focused index/document/info view-state skeleton.
- Keep this module pure and projection-oriented so later info-panel work can consume explicit state without reading broad route/controller state.
- Do not add DOM rendering, storage, toolbar event handling, or payload loading to it.

### `docs-viewer/runtime/js/docs-viewer-hosted-views.js`

- Added 2026-05-27 as the focused hosted-view registration shape for ordinary repo JavaScript modules.
- 2026-05-27 owner note: panel-specific listing moved into this module through `listByPanel(...)` and `listDocsViewerHostedViewsForPanel(...)` so toolbars can consume the same available/disabled/unavailable/access-blocked state as direct registry resolution.
- Keep this module limited to records, lifecycle method names, built-in compatibility view records, panel-specific listing, access/availability checks, and graceful absence. The `metadata-info` record may load the focused metadata hosted-view module, but the registry should not own rendering or panel state.
- Do not turn it into a plugin system, dependency loader, panel toolbar renderer, or third-party visualization owner.

### `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`

- Added 2026-05-27 as the focused renderer for info-panel shell chrome.
- 2026-05-27 owner note: minimal info-panel toolbar rendering and projection moved here. It renders view buttons from projected hosted-view options and marks disabled/access-blocked views as unavailable without owning lifecycle or route state.
- Keep this module limited to rendering the info-panel container, accessible title/label, close control, toolbar, hosted-view mount, status node, and projection attributes.
- Do not move hosted-view lifecycle, metadata rendering, source editing, panel toolbar selection, or management actions into it.

### `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`

- Added 2026-05-27 as the focused lifecycle owner for info-panel hosted views.
- 2026-05-27 owner note: info hosted-view option projection moved here. The host now exposes `viewOptions()` and includes info view options in panel projection so the renderer can show available, disabled, unavailable, and access-blocked states.
- Keep this module limited to resolving/listing registered info views, loading them, mounting/updating/unmounting them in the assigned info-panel body, closing the panel, and reporting graceful absence.
- Do not add route-state mutation, URL history behavior, metadata field rendering, backend writes, or plugin discovery to it.

### `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`

- Added 2026-05-27 as the first public-safe read-only info hosted view.
- Keep this module limited to rendering selected-document metadata from explicit context fields.
- Do not read broad viewer state, expose source paths, add edit controls, or call management endpoints.

### `docs-viewer/runtime/js/docs-viewer-view-context.js`

- Added 2026-05-27 as the focused selected-document hosted-view context projector.
- Keep this module limited to resolving the selected doc, cached payload, parent trail, route access flags, canonical URL, viewer scope, and display labels from explicit inputs.
- Future info views should extend or consume this helper rather than adding context shaping directly to `docs-viewer.js`.
- Do not add DOM rendering, hosted-view lifecycle, URL history mutation, or backend writes to it.

### Docs Import And Management

- Keep import result rendering in `docs-viewer/runtime/js/docs-html-import-render.js`.
- Keep preview/write orchestration in `docs-viewer/runtime/js/docs-html-import-workflow.js`.
- Keep management-only workflows behind the lazy management boundary.
- Keep normalize-order choice shaping and make-viewable target resolution in `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js`.
- Move command-specific write behavior to `docs-viewer/runtime/js/docs-viewer-management-actions.js` or a workflow-specific module when it gains independent state.

### Reports, Search, And Bookmarks

- Keep reports self-contained and loaded through the report allowlist.
- Extract shared report table or pager helpers only after at least two reports need the same behavior.
- Keep search and bookmark storage/controller behavior focused; revisit if grouping, sync, export, or cross-scope behavior is added.

## Refresh Notes

1. Refresh [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) first using the parent inventory scoring model.
2. Copy the Docs Viewer subset into this document and preserve the category columns.
3. Update follow-up notes only for files whose risk category changed or where new implementation work is planned.
4. Keep `docs-viewer/runtime/js/docs-viewer.js` separate from the all-script implementation plan unless the user explicitly starts that shared-runtime track.

## Related References

- [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [JavaScript Inventory Implementation Plan](/docs/?scope=studio&doc=javascript-inventory-implementation-plan)
