---
doc_id: docs-viewer-runtime-module-ownership
title: Runtime Module Ownership
added_date: 2026-06-05
last_updated: 2026-07-12
summary: Grouped owner map for Docs Viewer entrypoints, boot, routes, data, state, panels, controllers, and manage-only runtime modules.
parent_id: docs-viewer-runtime-boundary
---
# Docs Viewer Runtime Module Ownership

This document records the grouped runtime module owner map for [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).
It is intentionally grouped by responsibility.
Use [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) for row-level risk scores, score history, and detailed evidence.

## Ownership Rules

- Extracted helper modules must not import route entrypoints or mutate private runtime coordinator state directly.
- Public-safe modules must not import manage- or review-owned modules, local service clients, report registries, source editors, import workflows, settings, scope lifecycle, or local-only CSS assumptions.
- The management controller receives a narrow context API through the neutral lazy-controller adapter so public read-only viewers do not download or execute management-only orchestration.
- Route workflow commands are exposed only through the private route workflow command contract, backed by explicit route-session, scope-config, document-index, selected-document, search/recent, and status inputs.
- The returned app handle stays intentionally small: `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`.
- This document is the durable current-owner map and must be updated in the same slice whenever responsibility moves.
- `docs-viewer-app-context.js` owns explicit app context plus route context; `docs-viewer-access.js` owns route visibility/composition projection; `docs-viewer-service-context.js` owns independent named service surfaces.
- `docs-viewer-configured-scope-provider.js` owns the current configured-scope collection contract. `docs-viewer-route-features.js` owns allowlisted feature normalization and code-record filtering without owning feature lifecycle.

## Entrypoints And Boot

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Public entrypoint | `docs-viewer-public.js` | Starts the public app boot path and does not import manage-owned hosted views, shell renderers, reports, source editor, import, settings, or scope lifecycle modules. |
| Manage entrypoint | `docs-viewer-manage.js` | Supplies manage-owned document extras, hosted views, shell composition, and starts the manage app boot path. |
| Review entrypoint | `docs-viewer-review.js` | Supplies the returned-package provider, review hosted views and controls, package workflow controller, and starts the review app boot path without management authority. |
| App boot | `docs-viewer-app-boot.js` | Root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, and runtime startup. |
| App composition | `docs-viewer-app-composition.js` | Runtime defaults, service/provider/session construction, feature-filtered hosted-view registration, startup authority records, and feature-aware startup sequencing. |
| App session | `docs-viewer-app-session.js` | State defaults, single-owner named state-domain facades, public/manage route-session projection, and runtime-internal state object. |
| Private runtime coordinator | `docs-viewer-app-runtime.js` | Remaining focused controller wiring, config/controller handoff, event handler definitions, private management/startup callbacks, and the small returned app handle. |
| Document-view coordinator | `docs-viewer-document-view-coordinator.js` | Main-view/display-mode/info host construction, active view/mode/control queries, mode-specific info defaults, and rendered/search/recent transitions. |
| Status controller | `docs-viewer-status-controller.js` | Viewer status text/error projection and nested busy-state accounting. |

## Route, Data, And Config

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Route workflow | `docs-viewer-route-workflow.js` | Current URL/query helpers, current-doc resolution, route application, canonical URL correction, document index load orchestration, payload load orchestration, route-link handling, popstate coordination, and private route command contract. |
| App context, route access, and route config | `docs-viewer-app-context.js`, `docs-viewer-route-config.js`, `docs-viewer-access.js` | Explicit `public`/`manage`/`review` app kind, entrypoint/route validation, route visibility/composition policy, browser-safe registry resolution, preserved route-query identity, route context, and scope projection. |
| Route features | `docs-viewer-route-features.js` | Allowlisted feature ids, dependency validation, normalized feature policy, feature queries, and code-owned record filtering. Route config cannot register implementations. |
| Service context | `docs-viewer-service-context.js` | Independent `generatedData`, `source`, `management`, and browser-safe `config` service surfaces. Presence and URLs do not grant backend capability. |
| Config controller/service | `docs-viewer-config-controller.js`, `docs-viewer-config-service.js` | Shared config-envelope fetch/retry, independently callable configured-scope discovery and viewer-settings loading, scope route/picker projection, and UI-text/settings projection. |
| Configured-scope provider | `docs-viewer-configured-scope-provider.js` | Feature-facing `readIndex`, `readDocument`, `readSearch`, `readRecentlyAdded`, and `readReferences` methods, configured-scope URL resolution, reference-target projection, and optional source-method projection. |
| Returned-package provider | `docs-viewer-returned-package-provider.js`, `docs-viewer-review-client.js` | Package-selected index, document, source, manifest, inventory, and build transport for `/docs-review/`; wrapper normalization keeps external generated paths out of the shared viewer. |
| Source-service adapter | `docs-viewer-management-source-adapter.js` | Manage-entrypoint-owned optional source endpoint delegation. Its explicit contribution supplies provider methods but does not grant backend authority. |
| Generated-data runtime | `docs-viewer-generated-data-runtime.js` | Generated-data transport shaping, separately owned generated-read capability caching, selected-document reload projection, generated-search capability checks, payload normalization, and static/local generated JSON reads behind the provider. |
| Low-level data primitives | `docs-viewer-data.js` | Low-level JSON fetch/retry and generated-read reload path primitives reserved for generated-data runtime and config-service owners. |
| Asset URL projection | `docs-viewer-asset-url.js` | Asset-version URL projection shared by boot, route config, route context, report registry, config-service, and generated-data runtime owners. |
| Document index state | `docs-viewer-document-index-state.js` | Document visibility/loadability projection, non-viewable/manage-only tree filtering, non-loadable fallback resolution, default-doc selection, and index status projection. |

## Shell, Panels, Views, And Document Controls

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Shared app shell | `docs-viewer-app-shell.js` | Public-safe JavaScript-owned shell composition before route behavior wiring; manage renderers are supplied by the manage entrypoint. |
| Manage shell composition | `docs-viewer-management-shell-composition.js`, `docs-viewer-management-shell-renderer.js`, `docs-viewer-management-document-actions-renderer.js` | Manage-owned renderer bundle, context menu, metadata modal, import modal, settings modal, import host refs, and selected-document `Edit` / `Markdown source` controls. |
| Panel layout/view state | `docs-viewer-panel-layout.js`, `docs-viewer-view-state.js` | App-shell panel projection and index/main/info view-state skeleton. |
| View registry | `docs-viewer-view-registry.js`, `docs-viewer-management-hosted-views.js` | Code-owned shared definitions plus manage entrypoint contributions, view/mode/control lookup, app/feature/capability eligibility, route narrowing, and active control projection. |
| Main-view host | `docs-viewer-main-view-host.js`, `docs-viewer-view-context.js` | Main-view availability checks, active view projection, switch-intent handling, toolbar handoff, and selected-document context projection. |
| Document display modes | `docs-viewer-document-display-mode-host.js`, `docs-viewer-management-hosted-views.js`, `docs-viewer-view-context.js` | Rendered/source display-mode lifecycle inside the document main view, including capability-gated source-editor service slots. |
| Info-panel host | `docs-viewer-info-panel-controller.js`, `docs-viewer-info-panel-renderer.js`, `docs-viewer-info-panel-host.js`, `docs-viewer-metadata-info-view.js` | Info toggle binding, selected-document hosted-view context, outside-context view selection, open/close/update behavior, public-safe metadata rendering, and graceful absence. |

## Document, Navigation, Search, And Bookmarks

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Document controller | `docs-viewer-document-controller.js` | Rendered-document visibility, loading/missing/error states, final payload rendering, selected-document projection, search/recent pane handoff, and optional document-extras hook. |
| Sidebar/tree rendering | `docs-viewer-sidebar.js`, `docs-viewer-tree.js` | Sidebar tree rendering, main-view breadcrumb path rendering, expanded-row projection, selected-document highlighting, pure tree and visibility helpers. |
| Search/recent | `docs-viewer-search-controller.js`, `docs-viewer-search.js` | Search index loading, result rendering, recent rendering, debounce behavior, search/recent state-domain input, route command consumption, more-results behavior, and pane command requests. |
| Bookmarks/favourites | `docs-viewer-bookmarks.js`, `docs-viewer-favourites.js` | Bookmark state, rendering, IndexedDB storage orchestration, bookmark events, selected-document bookmark UI projection, route command consumption, and bookmark record storage helpers. |
| Read-oriented rendering | `docs-viewer-render.js` | Result and bookmark markup helpers imported by entry and bookmark controllers. |
| URL primitives | `docs-viewer-router.js` | Low-level URL building, anchor route parsing, browser history writes, requested-doc resolution, canonical route correction, popstate helper behavior, and payload-load helper behavior. |

## Manage-Only Runtime

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Lazy management boundary | `docs-viewer-runtime-lazy-controller.js` | Neutral lazy-controller loading, named management state-domain, service-client, and route-reload contracts, and gated management controller import. |
| Management controller | `docs-viewer-management.js` and child modules | Management-local facade, capability/status/control projection, focused-controller composition, and write orchestration. |
| Management event router | `docs-viewer-management-event-router.js` | Stable management control binding, Actions-menu toggle/dismissal, named command dispatch, and ordered interaction/modal root and keyboard delegation. |
| Management import workflow | `docs-viewer-management-import-controller.js` | Lazy Docs Import initialization, retry state, boot-error projection, and handoff from the management action to the import modal host. |
| Management modal composition | `docs-viewer-management-modal-composition.js`, `docs-viewer-management-modals.js` | Management shell-ref resolution, focused workflow assembly, and shared metadata/import/settings modal UI state, visibility, focus, and event behavior. |
| Metadata workflow | `docs-viewer-management-metadata-workflow.js` | Metadata parent-option projection, form validation and payload shaping, selected-document modal handoff, and save-result delegation to the action controller. |
| Settings workflow | `docs-viewer-management-settings-workflow.js` | Settings service reads, editable-field selection, modal load/error projection, and the narrow field/change/close contract consumed by the action controller. |
| Scope lifecycle controller | `docs-viewer-management-scope-lifecycle-controller.js` | Scope/sub-scope lifecycle control projection, event wiring, lazy flow loading, workflow option composition, failure projection, and post-apply config/capability refresh. |
| Management client | `docs-viewer-management-client.js` | Docs Viewer service transport helpers used by management controller workflows. |
| Drag/drop | `docs-viewer-drag-drop.js` | Drag/drop helpers used by the management controller. |
| Manage reports | `docs-viewer-management-document-reports.js`, `docs-viewer-report-service.js`, `docs-viewer/runtime/js/reports/*` | Manage-owned report mounting, report-context construction, report registry URL handoff, local report-service creation, and report endpoint access. |
| Source editor | `docs-viewer/runtime/js/management/source-editor/source-editor.js` | Local source-body document display mode rendering, dirty-state handling, rebuild submission, diagnostics, and rendered-view return behavior. Manage and review entrypoints may supply different providers; public entrypoints never import it. |
| Docs import | `docs-html-import.js`, `docs-html-import-workflow.js`, `docs-html-import-render.js`, `docs-html-import-modals.js` | Initialized Docs Import modal state, preview/write orchestration, overwrite prompts, result rendering, and modal behavior behind management service contracts. The management import workflow owns lazy initialization and host handoff. |

## Review-Only Runtime And Service

| Owner | Modules | Responsibility |
| --- | --- | --- |
| Review package workflow | `docs-viewer-review-controller.js`, `docs-viewer-review-document-controls.js`, `docs-viewer-review-hosted-views.js` | Package selection, explicit build, inventory visibility, canonical comparison, and review source-mode/control projection. |
| Review package services | `docs_review_packages.py`, `docs_review_build.py`, `docs_review_service.py`, `docs_review_routes.py` | Validated package-root containment, trusted manifest and inventory reads, synthetic builds, package-aware assets, generated reads, body-only temporary Markdown writes, parent-update rejection, and focused route dispatch. |

## Public Index Slimming Ownership

The current payload-loading ownership after public index slimming is:

- `docs-viewer-configured-scope-provider.js` owns feature-facing reads for index, selected document, search, recently added, references, and explicitly supplied source methods.
- `docs-viewer-generated-data-runtime.js` owns the static/local generated-data transport, capability, retry, reload, and normalization behavior behind that provider.
- `docs-viewer-tree-payload-adapter.js` owns normalizing nested `index-tree.json` and `recently-added.json` payloads into the runtime record shape, including deriving in-memory child `parent_id` values from nested tree position.
- `docs-viewer-document-index-state.js` owns public/manage visibility filtering, manage-only tree-root omission, non-loadable fallback resolution, default-doc selection, and index status projection after the normalized tree payload is loaded.
- `docs-viewer-route-workflow.js` owns route application, `index-tree.json` loading orchestration, selected-document payload loading, URL/history writes, and missing/error projection through its private route command contract.
- `docs-viewer-search-controller.js` owns search and recently-added rendering while delegating collection reads to the configured-scope provider.
- `docs-viewer-view-context.js` and `docs-viewer-metadata-info-view.js` hydrate and render info-panel metadata from selected by-id payloads rather than tree rows or public `index.json`.
- Public-safe modules must not import manage-owned metadata, report, source-editor, import, settings, scope lifecycle, or management client modules.
