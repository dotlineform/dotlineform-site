---
doc_id: docs-viewer-javascript-inventory
title: Docs Viewer JavaScript Inventory
added_date: 2026-05-20
last_updated: 2026-05-31
ui_status: reference
parent_id: studio-risk-analysis-policy
viewable: true
---
# Docs Viewer JavaScript Inventory

This document is the Docs Viewer-specific transition-evidence slice of [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).
It uses the same four-risk scoring model as the parent inventory, but limits the table and follow-up notes to browser JavaScript under `docs-viewer/runtime/js/`.

## Transition Status

Use [Docs Viewer Risk Inventory](/docs/?scope=studio&doc=docs-viewer-risk-inventory) and [Docs Viewer Runtime Risk Reduction Request](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-risk-reduction) for current priority and implementation ownership.
This page remains as row-level browser JavaScript evidence, owner notes, and score history for Docs Viewer runtime work.

Do not use this table as a separate frontend priority queue.
When a Docs Viewer row becomes actionable, move the app-level evidence into the app inventory or the focused runtime request before implementation.

## Current Summary

Measured on 2026-05-21 from [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).

- Docs Viewer browser JavaScript files in this focused app-shell snapshot: 57
- Files above target score 4: 14
- General risk themes: private app runtime coordination, management coordinator growth, import workflow ownership, scope lifecycle, search/bookmark controller boundaries, and future feature panels that must attach to focused owners instead of the app runtime coordinator.

| Score | Files |
| ---: | ---: |
| 9 | 0 |
| 8 | 0 |
| 7 | 0 |
| 6 | 7 |
| 5 | 7 |
| 4 | 43 |

## Current Priorities

| Docs rank | Full rank | File | Maint. | Struct. | Perf. | Arch. | Risk | Focus |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | `docs-viewer/runtime/js/docs-viewer-app-runtime.js` | 2 | 2 | 1 | 1 | 6 | Private Docs Viewer runtime coordination after route workflow and runtime-owner extraction; controller construction, config handoff, event binding, initial load sequencing, private callback handoffs, and returned app handle remain. |
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
| new | new | `docs-viewer/runtime/js/docs-viewer-config-service.js` | 1 | 1 | 1 | 1 | 4 | Focused browser-safe Docs Viewer config and UI-text fetch/retry owner consumed by the config controller. |
| new | new | `docs-viewer/runtime/js/docs-viewer-scope-select-menu.js` | 1 | 1 | 1 | 1 | 4 | Focused custom scope select-menu projection and interaction owner consumed by the config controller. |
| new | new | `docs-viewer/runtime/js/docs-viewer-asset-url.js` | 1 | 1 | 1 | 1 | 4 | Focused asset-version URL projection helper for static browser assets. |
| new | new | `docs-viewer/runtime/js/docs-viewer-report-service.js` | 1 | 1 | 1 | 1 | 4 | Focused local report endpoint adapter for source-config and broken-links audit reports. |
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
| 30 | 74 | `docs-viewer/runtime/js/reports/docs-index-table-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 31 | 75 | `docs-viewer/runtime/js/reports/reports-list-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 32 | 76 | `docs-viewer/runtime/js/reports/semantic-references-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 33 | 77 | `docs-viewer/runtime/js/reports/source-config-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 34 | 152 | `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management viewability target workflow helper. |
| 35 | 153 | `docs-viewer/runtime/js/docs-viewer-index-panel.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer index panel state, current-key persistence, toggle projection, and document-pane visibility helper. |
| 36 | 154 | `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned index panel chrome renderer and projection applier. |
| 37 | new | `docs-viewer/runtime/js/docs-viewer-main-view-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned main-view shell, rendered-document metadata chrome, and narrow rendered/search/recent projection applier. |
| 38 | new | `docs-viewer/runtime/js/docs-viewer-app-context.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned route context assembly from route config/access projection and mutable route-context projection. |
| 39 | new | `docs-viewer/runtime/js/docs-viewer-panel-layout.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned panel projection handoff for index state, current main-view visibility, and the view-state skeleton. |
| 40 | new | `docs-viewer/runtime/js/docs-viewer-route-config.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned route config resolver, browser-safe registry loader, and route/scope projection helper. |
| 41 | new | `docs-viewer/runtime/js/docs-viewer-access.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned static public/manage/manage-local access projection and hosted-view access check. |
| 42 | new | `docs-viewer/runtime/js/docs-viewer-view-state.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned index/document/info view-state skeleton and projection helper. |
| 43 | new | `docs-viewer/runtime/js/docs-viewer-hosted-views.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned hosted-view registration shape, built-in hosted-view records, availability/access checks, and graceful absence. |
| 43a | new | `docs-viewer/runtime/js/docs-viewer-main-view-host.js` | 1 | 1 | 1 | 1 | 4 | Main-view switch-intent and availability owner for rendered-document, search-results, and recent-results. |
| 44 | new | `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned info-panel chrome renderer and projection applier. |
| 45 | new | `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` | 1 | 1 | 1 | 1 | 4 | Info-panel hosted-view lifecycle owner for load, mount, update, unmount, close, and graceful absence. |
| 46 | new | `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` | 1 | 1 | 1 | 1 | 4 | Public-safe read-only metadata info hosted view. |
| 47 | new | `docs-viewer/runtime/js/docs-viewer-view-context.js` | 1 | 1 | 1 | 1 | 4 | Selected-document hosted-view context projector for metadata and planned future info views. |
| 48 | new | `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned management context-menu, metadata modal, import modal, settings modal, and import host renderer. |
| 49 | new | `docs-viewer/runtime/js/docs-viewer-app-boot.js` | 1 | 1 | 1 | 1 | 4 | App boot owner for route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, and runtime startup. |
| 50 | new | `docs-viewer/runtime/js/docs-viewer-app-session.js` | 1 | 1 | 1 | 1 | 4 | App-session owner for state defaults, named state-domain facades, and public/manage route-session projection. |
| 51 | new | `docs-viewer/runtime/js/docs-viewer.js` | 1 | 1 | 1 | 1 | 4 | Stable Docs Viewer entrypoint wrapper that imports and starts the app boot owner. |

## Follow-Up Notes

### `docs-viewer/runtime/js/docs-viewer.js`

- Current risk score: 4.
- This file is now the shared ES module entrypoint wrapper loaded by route shells.
- 2026-05-27 owner note: management action-area shell coordination moved to `docs-viewer/runtime/js/docs-viewer-app-shell.js`; `docs-viewer.js` only initializes that owner before existing route boot and waits for it before management/theme binding.
- 2026-05-31 owner note: top-bar layout now lives in `docs-viewer/runtime/js/docs-viewer-top-bar-renderer.js`, and viewer toolbar controls live in `docs-viewer/runtime/js/docs-viewer-viewer-toolbar-renderer.js`. The index-view toggle and info/context toggle are viewer-toolbar controls rather than management-action or document-meta controls.
- 2026-05-27 owner note: index panel chrome composition moved to `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, coordinated by the app shell before `docs-viewer.js` reads the preserved `docsViewerSidebarToggle`, `docsViewerSidebarExpand`, and `docsViewerNav` IDs.
- 2026-06-03 owner note: main-view shell composition now lives in `docs-viewer/runtime/js/docs-viewer-main-view-renderer.js`, coordinated by the app shell before runtime controllers read the preserved rendered-document metadata/search-result IDs. The app-shell boundary exposes `mainView` refs rather than `documentShell` refs.
- 2026-05-27 owner note: route dataset normalization and access flag projection moved to `docs-viewer/runtime/js/docs-viewer-app-context.js`; shell ref grouping moved behind `docs-viewer/runtime/js/docs-viewer-app-shell.js`; panel projection handoff moved to `docs-viewer/runtime/js/docs-viewer-panel-layout.js`. The entry module still owns route boot orchestration, config loading, payload loading, search/recent rendering handoff, bookmark behavior, and lazy management controller loading.
- 2026-06-03 owner note: route config, view state, and hosted-view records now use the `main` panel and `rendered-document` view id directly. `panels.document` and `document-host` were retired rather than kept as compatibility aliases.
- 2026-06-03 owner note: main-view switch validation and active-view projection moved to `docs-viewer/runtime/js/docs-viewer-main-view-host.js` for `rendered-document`, `search-results`, and `recent-results`; report-host migration remains deferred.
- 2026-05-27 owner note: route config resolution moved to `docs-viewer/runtime/js/docs-viewer-route-config.js`, static access projection moved to `docs-viewer/runtime/js/docs-viewer-access.js`, the index/main/info skeleton moved to `docs-viewer/runtime/js/docs-viewer-view-state.js`, and hosted-view registration moved to `docs-viewer/runtime/js/docs-viewer-hosted-views.js`. `docs-viewer.js` instantiates those owners but still does not own their contracts.
- 2026-05-27 owner note: info-panel chrome moved to `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`, hosted-view lifecycle moved to `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`, selected-document context projection moved to `docs-viewer/runtime/js/docs-viewer-view-context.js`, and metadata rendering moved to `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`. `docs-viewer.js` now passes explicit route/viewer inputs into the context helper and wires open/close events, but should not absorb panel DOM composition, lifecycle, context shaping, or metadata presentation.
- 2026-05-27 owner note: management-only context-menu and modal shell markup moved to `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`, dynamically imported by the app shell only when route access allows management UI. The private app runtime coordinator passes the rendered refs into the lazy management controller after app-shell initialization while management workflows and backend capability checks stay in the management modules.
- 2026-05-27 owner note: app boot ownership moved to `docs-viewer/runtime/js/docs-viewer-app-boot.js`, and route/document workflow ownership later moved to `docs-viewer/runtime/js/docs-viewer-route-workflow.js`. `docs-viewer.js` should remain an import-and-start wrapper.
- Useful future slices should reduce shared-runtime coupling or route-load cost, such as generated-payload loading, loadable-doc visibility state, broader panel-layout ownership, or management lazy-boundary hardening.
- Future route/document workflow changes should extend `docs-viewer-route-workflow.js`, not add responsibility back to the entrypoint or app runtime coordinator.
- Preserve `docs-viewer/runtime/js/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

### `docs-viewer/runtime/js/docs-viewer-app-boot.js`

- Added 2026-05-27 as the focused app boot owner.
- Keep this module limited to root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, boot failure status projection, and starting the app runtime coordinator.
- Do not move route application, generated docs/search reads, search/recent state transitions, bookmark storage, report rendering, backend writes, or management capability checks into it.

### `docs-viewer/runtime/js/docs-viewer-app-runtime.js`

- Added 2026-05-27 as the private runtime coordinator for the existing shared route/document workflow after the entrypoint became a wrapper.
- Current risk score: 6 after the route/document workflow and runtime-owner extractions.
- 2026-05-27 owner note: URL/query helpers, current-doc resolution, route application, index-load orchestration, payload-load orchestration, missing/error handoff, route-link handling, and popstate coordination moved to `docs-viewer/runtime/js/docs-viewer-route-workflow.js`.
- 2026-05-28 owner note: search/recent route command bundling is now `createDocsViewerSearchRouteCommands(...)`, and the search controller consumes explicit search/recent, document-index, selected-document, route-command, and pane-command inputs instead of the broad runtime state.
- 2026-05-28 owner note: bookmark document-load command bundling is now `createDocsViewerBookmarkRouteCommands(...)`, and the bookmark controller consumes explicit bookmark, document-index, selected-document, search/recent, route-command, and search-reset command inputs instead of the broad runtime state.
- 2026-05-27 owner note: info-panel toolbar click handoff now opens the selected info hosted view through `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`; toolbar rendering and view option projection stay in focused panel/hosted-view modules.
- 2026-05-28 owner note: generated-data request shaping and generated-read capability caching moved to `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`.
- 2026-05-28 owner note: document visibility/loadability projection moved to `docs-viewer/runtime/js/docs-viewer-document-index-state.js`.
- 2026-05-28 owner note: lazy management context no longer receives broad runtime `state`; it receives named management state-domain, service-client, and route-reload contracts, and `docs-viewer-management.js` builds a management-local facade from those domains for existing child modules.
- 2026-05-28 owner note: document payload rendering and sidebar tree rendering now consume explicit state-domain inputs. `docs-viewer-document-controller.js` receives route-session, scope-config, selected-document, generated-data, and status commands; `docs-viewer-sidebar.js` receives document-index, selected-document, and scope-config projections instead of the broad runtime state.
- 2026-05-28 owner note: selected-document info-panel coordination moved to `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`; the controller now consumes explicit document-index, selected-document, scope-config, panel-view, route-access, URL, and trail inputs instead of the broad runtime state.
- 2026-05-28 owner note: config/scope setup now consumes explicit scope-config, document-index, search/recent, route-session, config-service, and route-command inputs through `docs-viewer/runtime/js/docs-viewer-config-controller.js` instead of broad runtime state.
- 2026-05-28 owner note: lazy management loading and management context assembly moved behind neutral `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`; keep the actual management controller import gated so public routes do not fetch management-only JS.
- 2026-05-28 owner note: app-session and state default creation moved to `docs-viewer/runtime/js/docs-viewer-app-session.js`; `docs-viewer-app-runtime.js` now creates the session, uses named domains for narrowed controllers, keeps the broad state object only for runtime-internal controller handoffs that still need it, and updates the route-session domain during route-global changes.
- 2026-05-28 owner note: service-context projection moved to `docs-viewer/runtime/js/docs-viewer-service-context.js`; public contexts strip management base URLs and local generated-read service base URLs before controllers are assembled.
- 2026-05-28 owner note: route workflow, search controller, and document controller now consume named generated-data read methods instead of assembling fetch/reload/capability bundles locally.
- 2026-05-28 owner note: runtime defaults, service-context handoff, hosted-view registry creation, panel layout creation, app-session creation, generated-data runtime creation, document-index state creation, public/manage startup phase records, startup authority records, and initial startup sequencing moved to `docs-viewer/runtime/js/docs-viewer-app-composition.js`.
- 2026-05-28 owner note: the returned app handle was narrowed to `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`. Broad `state`, app-composition internals, app-session internals, the management lazy loader, and route workflow bridges are no longer returned; search/recent, bookmarks, startup index loading, and management reloads now consume the private route workflow command contract instead of one-off runtime wrappers.
- 2026-05-28 owner note: `compatibilityBridge` was removed from app-session, and `composition.state` was removed from app-composition. Focused tests now assert named state-domain and composition owner contracts rather than temporary compatibility aliases.
- 2026-05-28 lifecycle note: this file remains the private app coordinator for focused controller construction, callback handoff, route-global updates, private management startup callbacks, and the small returned app handle. Do not add new feature lifecycle ownership here; future controller work should narrow complete controller families to explicit state-domain and service inputs.
- This module now remains the runtime coordinator for focused controller construction, config handoff, focused-controller callback handoff, event handler definitions, private management/startup callback handoff, and the small returned app handle.
- Next risk-reduction slices should focus on complete new owner boundaries for future features, not restore route/document/search/bookmark/info/generated-data/visibility/management workflow behavior here.

### `docs-viewer/runtime/js/docs-viewer-app-composition.js`

- Added 2026-05-28 as the app-composition and startup phase owner.
- Current risk score: 4.
- 2026-05-28 lifecycle note: this module owns startup phase sequencing and authority records, including the public/manage split between browser route/config context, browser-safe config assets, generated reads, browser storage, management capability checks, and management write endpoints.
- Keep this module limited to runtime defaults, foundational owner creation, startup phase records, startup authority records, public/manage startup gating, and initial startup sequence orchestration.
- Do not move rendering, validation, generated-read internals, config normalization, bookmark storage, management writes, report behavior, or controller-specific UI behavior into it.
- The private app runtime coordinator still constructs focused controllers until a later slice narrows remaining controller families away from function-scoped bridge callbacks.

### `docs-viewer/runtime/js/docs-viewer-app-session.js`

- Added 2026-05-28 as the app-session and state-domain owner.
- Current risk score: 4.
- Keep this module limited to app-session creation, state defaults, named domain facades, route-session projection, and the runtime-internal state object needed by remaining controller handoffs.
- Do not move controller construction, event binding, generated reads, URL history, document rendering, bookmark persistence, or management writes into it.
- Future slices should narrow complete controller families to the relevant domain facade and remove their broad-state dependency from runtime handoff.

### `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`

- Added 2026-05-28 as the focused generated-data request owner.
- Current risk score: 4.
- Keep this module limited to data request option shaping, generated-read capability caching, retry/reload option projection, generated-search read capability checks, and named generated JSON read methods for docs indexes, payloads, search indexes, references indexes, and reference-target buckets.
- Low-level generated-data fetch/retry helpers in `docs-viewer/runtime/js/docs-viewer-data.js` are allowed here because this module is the feature-facing generated-data owner.
- Do not move config loading, payload rendering, backend write authority, or management capability UI projection into it.

### `docs-viewer/runtime/js/docs-viewer-config-service.js`

- Added 2026-05-28 as the focused browser-safe config asset read owner.
- Current risk score: 4.
- Keep this module limited to Docs Viewer config and UI-text fetch/retry behavior using generated-data runtime request projection.
- Do not move config normalization, scope route projection, UI rendering, generated JSON read methods, backend writes, or management capability UI projection into it.

### `docs-viewer/runtime/js/docs-viewer-asset-url.js`

- Added 2026-05-28 as the focused asset-version URL projection helper.
- Current risk score: 4.
- Keep this module limited to reading the asset-version meta value and appending asset/reload query parameters for browser asset requests.
- Do not move fetch/retry behavior, generated-read capability checks, service base URLs, config normalization, or backend write behavior into it.

### `docs-viewer/runtime/js/docs-viewer-data.js`

- Current risk score: 4.
- 2026-05-28 owner note: static asset-version helpers moved to `docs-viewer/runtime/js/docs-viewer-asset-url.js`; config asset fetches moved behind `docs-viewer/runtime/js/docs-viewer-config-service.js`.
- Keep this module limited to low-level JSON fetch/retry helpers, generated-read retry helpers, and management reload path construction behind the generated-data runtime and config service.
- Direct imports should stay limited to `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` and `docs-viewer/runtime/js/docs-viewer-config-service.js`; feature controllers, reports, route config, app boot, and route context should consume their named owner contracts instead.

### `docs-viewer/runtime/js/docs-viewer-service-context.js`

- Added 2026-05-28 as the focused public/manage service-context projection owner.
- Current risk score: 4.
- Keep this module limited to projecting static route context into generated-read, config, report, and management service surfaces.
- Public contexts must continue to omit management base URLs, local generated-read service base URLs, backend probes, and management service adapters. Do not move capability truth or write authority into this module.

### `docs-viewer/runtime/js/docs-viewer-report-service.js`

- Added 2026-05-28 as the focused local report endpoint adapter.
- Current risk score: 4.
- Keep this module limited to local report endpoint paths, request options, local-server missing-base errors, and response-envelope handling for source-config and broken-links audit reports.
- Do not move report DOM rendering, table sorting/filtering, activity UI labels, generated-data runtime reads, management writes outside report actions, or management capability truth into it.

### `docs-viewer/runtime/js/docs-viewer-document-index-state.js`

- Added 2026-05-28 as the focused document-index projection owner.
- Current risk score: 4.
- Keep this module limited to all-doc/doc map projection, public/manage visibility filtering, hidden/manage-only tree handling, non-loadable fallback resolution, default-doc resolution, and index status projection.
- Do not move route URL state, sidebar DOM rendering, document payload loading, search/recent rendering, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`

- Added 2026-05-28 as the focused info-panel coordination owner.
- Current risk score: 4.
- 2026-05-28 owner note: this controller now consumes explicit document-index, selected-document, scope-config, panel-view, route-access, URL, and trail inputs instead of broad `state`.
- Keep this module limited to selected-document hosted-view context, metadata-info default open behavior, toggle projection, toolbar click handoff, update-on-document-change, close behavior, view-state projection sync, and public-safe availability.
- Do not move info-panel chrome rendering, hosted-view registration, metadata presentation, document payload rendering, URL history, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`

- Added 2026-05-28 as a neutral lazy-controller adapter.
- Current risk score: 4.
- Keep this module limited to promise-cached dynamic controller loading and explicit context assembly.
- Do not name this module as management-only or statically import `docs-viewer-management.js` from public-route startup paths; public read-only smokes assert that management-only JS is not fetched.

### `docs-viewer/runtime/js/docs-viewer-route-workflow.js`

- Added 2026-05-27 as the focused route/document workflow owner.
- Current risk score: 4.
- 2026-05-28 owner note: route workflow now exposes a private command contract for route application, index loading, document loading, history writes, route resolution, and route URL creation. The contract is backed by route-session, scope-config, document-index, selected-document, search/recent, and status inputs rather than a broad runtime state handoff.
- Keep this module limited to URL/query helpers, current-doc resolution, route application, index and payload load orchestration, canonical URL correction, route-link handling, and popstate coordination.
- It should continue to delegate low-level URL/history operations to `docs-viewer/runtime/js/docs-viewer-router.js`, final document pane rendering to `docs-viewer/runtime/js/docs-viewer-document-controller.js`, search/recent rendering to `docs-viewer/runtime/js/docs-viewer-search-controller.js`, bookmark storage/rendering to `docs-viewer/runtime/js/docs-viewer-bookmarks.js`, and management writes/actions to the lazy management modules.

### `docs-viewer/runtime/js/docs-viewer-management.js`

- Current risk score: 6.
- 2026-05-28 owner note: this controller now receives named `managementState`, `serviceClient`, and `routeReload` contracts from the lazy runtime boundary instead of broad runtime `state`. It builds a management-local state facade from explicit route-session, scope-config, document-index, selected-document, search/recent, generated-data, and management domains for existing management child modules.
- 2026-05-29 owner note: action menu markup is design-time record rendering in `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`; this controller preserves binding, capability projection, and command workflow handoff for the rendered stable ids.
- Keep service access behind the management service-client contract and post-write reloads behind the route-reload contract.
- Do not move new backend writes, generated-read behavior, public hosted-view behavior, route shell boot, or route URL primitives into this file.

### `docs-viewer/runtime/js/docs-viewer-config-controller.js`

- Current risk score: 5.
- 2026-05-28 owner note: this controller now consumes explicit scope-config, document-index, search/recent, route-session, config-service, and route-command inputs instead of broad `state`.
- 2026-05-29 owner note: the scope picker now projects custom select-menu option rows with `emoji`, scope id label, and config-backed `meta` while preserving the hidden native select as the existing value/change bridge for route workflow handoff.
- Keep this module focused on browser-safe Docs Viewer config loading, route-scope resolution, scope-picker projection, route-global/root-dataset projection, UI-text merge, recent-limit/status-label projection, and management/status copy updates.
- Do not move document index loading, payload rendering, URL history primitives, generated-read capability checks, backend writes, management actions, or route shell boot into it.

### `docs-viewer/runtime/js/docs-viewer-search-controller.js`

- Current risk score: 5.
- 2026-05-28 owner note: search/recent route command bundling moved into this focused owner through `createDocsViewerSearchRouteCommands(...)`. The controller now consumes explicit `searchRecent`, `documentIndex`, `selectedDocument`, `routeCommands`, and `paneCommands` inputs for route application, history writes, current-doc resolution, default-doc fallback, result URL creation, loadable-doc target resolution, and pane projection requests.
- Keep this module focused on generated search-index loading, result/recent rendering, debounce handoff, search/recent route activation, more-results behavior, route command consumption, and pane command requests.
- Do not move low-level URL construction, browser history primitives, document payload rendering, config loading, management writes, or panel toolbar/view switching into it.

### `docs-viewer/runtime/js/docs-viewer-bookmarks.js`

- Current risk score: 6.
- 2026-05-28 owner note: bookmark route command bundling moved into this focused owner through `createDocsViewerBookmarkRouteCommands(...)`. The controller now consumes explicit bookmark, document-index, selected-document, search/recent, route-command, and search-reset command inputs for bookmark rendering and document-load handoff when opening a bookmark.
- Keep this module focused on bookmark loading, IndexedDB support fallback, list/toggle rendering, selected-document bookmark UI projection, edit state, pending focus, bookmark events, route command consumption, search-reset command consumption, and status-pill fallback callbacks.
- Do not move low-level history construction, document payload rendering, info-panel lifecycle, management writes, or future bookmark grouping/sync/export features into the app runtime coordinator.

### `docs-viewer/runtime/js/docs-viewer-document-controller.js`

- Current risk score: 5.
- 2026-05-28 owner note: this controller now consumes explicit route-session, scope-config, selected-document, generated-data, and status command inputs instead of `context.state`.
- 2026-05-28 owner note: local report endpoint access moved to `docs-viewer/runtime/js/docs-viewer-report-service.js`; this controller now passes a report-service adapter through report context instead of `managementBaseUrl`.
- Keep this module focused on document pane projection, payload rendering, loading/missing/error states, selected-document updates, generated-data-backed report read handoff, and report-service handoff.
- Do not move URL/history primitives, tree visibility projection, sidebar DOM rendering, search/recent rendering, local report endpoint ownership, backend writes, or management action behavior into it.

### `docs-viewer/runtime/js/docs-viewer-sidebar.js`

- Current risk score: 4.
- 2026-05-28 owner note: this renderer now consumes explicit document-index, selected-document, and scope-config projections instead of `context.state`.
- Keep this module focused on tree row rendering, expand-state projection, selected-document highlighting, breadcrumb rendering, update-date display, and scope-config management text display.
- Do not move document payload rendering, route workflow, generated-data reads, bookmark storage, search/recent behavior, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-app-shell.js`

- Added 2026-05-27 as the app-shell owner for management action-area coordination.
- Current scope is intentionally narrow: render top-bar layout through `docs-viewer/runtime/js/docs-viewer-top-bar-renderer.js`, render viewer toolbar controls through `docs-viewer/runtime/js/docs-viewer-viewer-toolbar-renderer.js`, render index panel chrome through `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, clear the management toolbar mount, import `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js` only when route intent allows management, and return the rendered surfaces before existing management/theme binding continues.
- It also renders the main-view shell through `docs-viewer/runtime/js/docs-viewer-main-view-renderer.js` before existing document, sidebar, bookmark, search, and management controllers read the preserved rendered-document/search/recent IDs.
- It also renders the info panel shell through `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`; lifecycle and metadata presentation stay in the focused info-panel host/view modules.
- It also clears and renders the management shell mount through `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` only when route access allows management UI.
- The existing lazy management controller continues to own backend reachability, capability refresh, command wiring, and status projection.
- Revisit the inventory table and score during the next full JavaScript inventory refresh; the expected target score for this focused renderer is 4 or lower while it stays limited to shell rendering.

### `docs-viewer/runtime/js/docs-viewer-top-bar-renderer.js`

- Added 2026-05-31 as the focused top-bar layout owner for the viewer-toolbar surface and management-toolbar mount.
- Keep this module limited to rendering layout mounts and delegating control rendering to toolbar owners.

### `docs-viewer/runtime/js/docs-viewer-viewer-toolbar-renderer.js`

- Added 2026-05-31 as the focused renderer for scope picker, recently-added button, search input, index-view toggle, and info/context panel toggle.
- 2026-05-29 owner note: the scope picker shell now renders the custom select-menu trigger/list plus a visually hidden native select with the preserved `docsViewerScopeSelect` id for controller/event compatibility.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount from route context.

### `docs-viewer/runtime/js/docs-viewer-scope-select-menu.js`

- Added 2026-05-29 as the focused owner for custom scope select-menu option rendering, trigger projection, open/close behavior, keyboard navigation, and dispatching the preserved native select `change` event.
- Keep route navigation, browser config normalization, scope option record construction, and route-global projection in `docs-viewer/runtime/js/docs-viewer-config-controller.js`.

### `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`

- Added 2026-05-27 as the focused renderer for management action markup.
- 2026-05-29 owner note: the management `Actions` menu is rendered from design-time item records that define stable ids, labels, optional emoji, and default visibility; command behavior remains outside this renderer.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount.

### `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`

- Added 2026-05-27 as the focused renderer for management-only context menu and modal shell markup.
- Keep this module limited to preserving the existing `docsViewerContextMenu`, metadata modal, import modal, settings modal, and `docsHtmlImport*` host refs inside the management shell mount.
- Do not move metadata save behavior, import workflow behavior, settings writes, context-menu actions, backend reachability checks, generated-data reads, or management capability projection into this renderer.

### `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`

- Added 2026-05-27 as the focused renderer for index panel shell chrome.
- Keep this module limited to rendering the sidebar container, toolbar controls, nav mount, and applying index-panel projection to DOM refs. Do not move tree row rendering, drag/drop behavior, search/recent behavior, or document payload rendering into it.

### `docs-viewer/runtime/js/docs-viewer-main-view-renderer.js`

- Added 2026-06-03 as the focused renderer for main-view shell chrome, replacing the former document-shell renderer boundary.
- Keep this module limited to rendering `.docsViewer__main`, rendered-document metadata chrome, rendered-document/search/recent result mounts, and applying the current narrow rendered/search/recent/results-status projection to DOM refs.
- Do not move Markdown rendering, generated report loading, payload fetching, breadcrumb metadata rendering, status-pill content rendering, bookmark storage, or search/recent result rendering into it.

### `docs-viewer/runtime/js/docs-viewer-main-view-host.js`

- Added 2026-06-03 as the focused main-view switch-intent owner.
- Keep this module limited to resolving main-view hosted-view availability, projecting active main-view state through panel layout, and accepting switch requests for built-in main views.
- Do not add source-editor service details, report migration behavior, arbitrary module loading, plugin behavior, or rendered-document/search/recent rendering into it.

### `docs-viewer/runtime/js/docs-viewer-app-context.js`

- Added 2026-05-27 as the focused route-context owner for the app shell.
- Keep this module limited to assembling route context from route config/access projection, current URL management/import intent, viewer pathname, and bookmark storage scope.
- Do not move route application, config loading, generated-data fetching, backend capability checks, or write behavior into it.

### `docs-viewer/runtime/js/docs-viewer-panel-layout.js`

- Added 2026-05-27 as the focused panel projection owner for the app shell.
- 2026-05-28 owner note: legacy sidebar local-storage migration was retired by cleanup tracker `FU-1`; this module reads and writes only the current `dotlineform-docs-viewer-index-panel:<scope>` key.
- Keep this module limited to index panel state storage/projection, current document/search/recent/results-status projection handoff, info-panel visibility/layout projection, and delegation to the view-state skeleton.
- Do not add toolbar controls, hosted-view registration, document payload rendering, search result rendering, or management action behavior to it.

### `docs-viewer/runtime/js/docs-viewer-route-config.js`

- Added 2026-05-27 as the focused route config resolver and route/scope projection helper.
- Keep this module limited to the durable route config shape, browser-safe route-config registry loading/resolution, explicit route-config normalization for tests/boot callers, and projection of scope config into route globals.
- 2026-05-28 owner note: inline route-config scripts and legacy `#docsViewerRoot` route data-attribute fallback were removed. Route shells must use the registry contract; focused tests must pass explicit route config or route context rather than relying on shell data as a synthetic config source.
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
- 2026-05-28 lifecycle note: hosted-view records may define `load`, `mount`, `update`, `unmount`, and `dispose`, but registration and visibility do not imply backend authority or write capability.
- 2026-05-28 owner note: built-in hosted-view records are current architecture and are exposed through `createDocsViewerBuiltInHostedViews()`. The old `createDocsViewerCompatibilityHostedViews()` alias was removed during architecture cleanup after active runtime callers and focused smokes had moved to the built-in factory.
- Keep this module limited to records, lifecycle method names, built-in hosted-view records, panel-specific listing, access/availability checks, and graceful absence. The `metadata-info` record may load the focused metadata hosted-view module, but the registry should not own rendering or panel state.
- Do not turn it into a plugin system, dependency loader, panel toolbar renderer, or third-party visualization owner.

### `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`

- Added 2026-05-27 as the focused renderer for info-panel shell chrome.
- 2026-05-27 owner note: minimal info-panel toolbar rendering and projection moved here. It renders view buttons from projected hosted-view options and marks disabled/access-blocked views as unavailable without owning lifecycle or route state.
- Keep this module limited to rendering the info-panel container, accessible title/label, close control, toolbar, hosted-view mount, status node, and projection attributes.
- Do not move hosted-view lifecycle, metadata rendering, source editing, panel toolbar selection, or management actions into it.

### `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`

- Added 2026-05-27 as the focused lifecycle owner for info-panel hosted views.
- 2026-05-27 owner note: info hosted-view option projection moved here. The host now exposes `viewOptions()` and includes info view options in panel projection so the renderer can show available, disabled, unavailable, and access-blocked states.
- 2026-05-28 lifecycle note: this host is the concrete Docs Viewer hosted-view lifecycle model: resolve/list, load, mount, update, unmount, close, dispose, and graceful absence. It should not become a general plugin platform.
- Keep this module limited to resolving/listing registered info views, loading them, mounting/updating/unmounting them in the assigned info-panel body, closing the panel, and reporting graceful absence.
- Do not add route-state mutation, URL history behavior, metadata field rendering, backend writes, or plugin discovery to it.

### `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`

- Added 2026-05-27 as the first public-safe read-only info hosted view.
- Keep this module limited to rendering selected-document metadata from explicit context fields.
- Do not read broad viewer state, expose source paths, add edit controls, or call management endpoints.

### `docs-viewer/runtime/js/docs-viewer-view-context.js`

- Added 2026-05-27 as the focused selected-document hosted-view context projector.
- 2026-05-28 lifecycle note: public-safe hosted views should receive explicit selected-document, route/access, payload, viewer-scope, URL, trail, and display-label inputs from this helper rather than reading broad runtime state.
- Keep this module limited to resolving the selected doc, cached payload, parent trail, route access flags, canonical URL, viewer scope, and display labels from explicit inputs.
- Future info views should extend or consume this helper rather than adding context shaping directly to `docs-viewer.js`.
- Do not add DOM rendering, hosted-view lifecycle, URL history mutation, or backend writes to it.

### Docs Import And Management

- Current boundary: Docs Import is a Docs Viewer management-modal app, not a standalone route surface. `docs-viewer/runtime/js/docs-viewer-management.js` lazily initializes `docs-viewer/runtime/js/docs-html-import.js` only from the management modal host.
- Keep modal app state, scope/file selection, service availability display, and `studio:ready` route-ready dataset projection in `docs-viewer/runtime/js/docs-html-import.js`.
- Keep import result rendering in `docs-viewer/runtime/js/docs-html-import-render.js`.
- Keep preview/write orchestration in `docs-viewer/runtime/js/docs-html-import-workflow.js`.
- Keep import writes behind `docs-viewer/runtime/js/docs-viewer-management-client.js` and management endpoints such as `/docs/import-source`.
- Keep management-only workflows behind the lazy management boundary.
- 2026-05-28 lifecycle note: management initialization, capability refresh, action/menu/modal binding, imports, settings, scope lifecycle, status pills, and write orchestration remain behind `docs-viewer/runtime/js/docs-viewer-management.js`, management child modules, and `docs-viewer/runtime/js/docs-viewer-management-client.js`; hosted-view visibility must not imply write authority.
- Keep make-viewable target resolution in `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js`.
- Move command-specific write behavior to `docs-viewer/runtime/js/docs-viewer-management-actions.js` or a workflow-specific module when it gains independent state.

### Reports, Search, And Bookmarks

- Keep reports self-contained and loaded through the report allowlist.
- Keep local source-config and broken-links endpoint access behind `docs-viewer/runtime/js/docs-viewer-report-service.js`; report modules should consume `context.reportService` rather than `managementBaseUrl` or direct `window.fetch(...)`.
- Extract shared report table or pager helpers only after at least two reports need the same behavior.
- Keep search and bookmark storage/controller behavior focused; revisit if grouping, sync, export, or cross-scope behavior is added.

## Refresh Notes

1. Refresh [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) first using the parent inventory scoring model.
2. Copy the Docs Viewer subset into this document and preserve the category columns.
3. Update follow-up notes only for files whose risk category changed or where new implementation work is planned.
4. Keep `docs-viewer/runtime/js/docs-viewer.js` separate from the all-script implementation plan unless the user explicitly starts that shared-runtime track.

## Related References

- [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy)
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
