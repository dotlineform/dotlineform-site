---
doc_id: docs-viewer-javascript-inventory
title: Docs Viewer JavaScript Inventory
added_date: 2026-05-20
last_updated: 2026-06-04
ui_status: reference
parent_id: admin
viewable: true
---
# Docs Viewer JavaScript Inventory

Browser JavaScript under `docs-viewer/runtime/js/`.

Risk themes:

- private app runtime coordination
- management coordinator growth
- import workflow ownership
- scope lifecycle
- search/bookmark controller boundaries
- future feature panels that must attach to focused owners instead of the app runtime coordinator.

| File                                                | Focus                                                                                                                                                                                                                       |
|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| docs-html-import-modals.js                          | runtime support module.                                                                                                                                                                                                     |
| docs-html-import-render.js                          | Docs import result rendering helper.                                                                                                                                                                                        |
| docs-html-import-workflow.js                        | Docs import preview/write workflow helper.                                                                                                                                                                                  |
| docs-html-import.js                                 | Docs import controller after explicit workflow handoff and focused module-smoke coverage.                                                                                                                                   |
| docs-viewer-access.js                               | App-shell-owned static public/manage/manage-local access projection and hosted-view access check.                                                                                                                           |
| docs-viewer-app-boot.js                             | App boot owner for route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, and runtime startup.                                          |
| docs-viewer-app-composition.js                      | App-composition owner for runtime defaults, foundational owner creation, public/manage startup phase records, startup authority records, and initial startup sequencing.                                                    |
| docs-viewer-app-context.js                          | App-shell-owned route context assembly from route config/access projection and mutable route-context projection.                                                                                                            |
| docs-viewer-app-runtime.js                          | Private runtime coordination after route workflow and runtime-owner extraction; controller construction, config handoff, event binding, initial load sequencing, private callback handoffs, and returned app handle remain. |
| docs-viewer-app-session.js                          | App-session owner for state defaults, named state-domain facades, and public/manage route-session projection.                                                                                                               |
| docs-viewer-asset-url.js                            | Focused asset-version URL projection helper for static browser assets.                                                                                                                                                      |
| docs-viewer-bookmarks.js                            | bookmark/favourite support.                                                                                                                                                                                                 |
| docs-viewer-config-controller.js                    | config/scope setup.                                                                                                                                                                                                         |
| docs-viewer-config-service.js                       | Focused browser-safe config and UI-text fetch/retry owner consumed by the config controller.                                                                                                                                |
| docs-viewer-data.js                                 | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-document-controller.js                  | document rendering/controller support.                                                                                                                                                                                      |
| docs-viewer-document-index-state.js                 | Focused document-index projection owner for public/manage visibility filtering, manage-only tree omission, non-loadable fallback resolution, default-doc selection, and index status projection.                            |
| docs-viewer-drag-drop.js                            | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-favourites.js                           | bookmark/favourite support.                                                                                                                                                                                                 |
| docs-viewer-generated-data-runtime.js               | Focused generated-data request/capability owner for data request options, generated-read checks, retry/reload options, generated-search read capability projection, and named generated JSON read methods.                  |
| docs-viewer-hosted-views.js                         | App-shell-owned hosted-view registration shape, public-safe built-in records, route-record filtering, availability/access checks, and graceful absence.                                                                     |
| docs-viewer-index-panel-renderer.js                 | App-shell-owned index panel chrome renderer and projection applier.                                                                                                                                                         |
| docs-viewer-index-panel.js                          | index panel state, current-key persistence, toggle projection, and document-pane visibility helper.                                                                                                                         |
| docs-viewer-info-panel-controller.js                | Focused info-panel coordination owner for selected-document context, toggle state, toolbar click handoff, open/update/close behavior, and public-safe availability.                                                         |
| docs-viewer-info-panel-host.js                      | Info-panel hosted-view lifecycle owner for load, mount, update, unmount, close, and graceful absence.                                                                                                                       |
| docs-viewer-info-panel-renderer.js                  | App-shell-owned info-panel chrome renderer and projection applier.                                                                                                                                                          |
| docs-viewer-main-view-host.js                       | Main-view switch-intent and availability owner for rendered-document, search-results, and recent-results.                                                                                                                   |
| docs-viewer-main-view-renderer.js                   | App-shell-owned main-view shell, rendered-document metadata chrome, and narrow rendered/search/recent projection applier.                                                                                                   |
| docs-viewer-manage.js                               | Manage entrypoint wrapper that imports manage-owned document extras, hosted views, shell composition, and starts the manage app boot owner.                                                                                 |
| docs-viewer-management-action-workflow.js           | management viewability target workflow helper.                                                                                                                                                                              |
| docs-viewer-management-actions.js                   | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-capabilities.js              | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-client.js                    | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-config.js                    | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-document-actions-renderer.js | Manage-owned selected-document status/edit/source controls rendered above the shared main-view toolbar surface.                                                                                                             |
| docs-viewer-management-hosted-views.js              | Manage-owned hosted-view records, currently the markdown-sourcesource-editor view supplied by the manage entrypoint.                                                                                                        |
| docs-viewer-management-interactions.js              | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-modals.js                    | management modal controller after transient modal shell and metadata parent-picker extraction.                                                                                                                              |
| docs-viewer-management-render.js                    | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-shell-composition.js         | Manage-owned shell renderer composition supplied by the manage entrypoint so public-safe app shell code does not import management renderers.                                                                               |
| docs-viewer-management-shell-renderer.js            | Manage-owned management context-menu, metadata modal, import modal, settings modal, and import host renderer.                                                                                                               |
| docs-viewer-management.js                           | management coordinator after shared action workflow helper extraction.                                                                                                                                                      |
| docs-viewer-metadata-info-view.js                   | Public-safe read-only metadata info hosted view.                                                                                                                                                                            |
| docs-viewer-panel-layout.js                         | App-shell-owned panel projection handoff for index state, current main-view visibility, and the view-state skeleton.                                                                                                        |
| docs-viewer-public.js                               | Public entrypoint wrapper that imports and starts the public app boot owner.                                                                                                                                                |
| docs-viewer-render.js                               | rendering helper.                                                                                                                                                                                                           |
| docs-viewer-report-service.js                       | Focused local report endpoint adapter for source-config and broken-links audit reports.                                                                                                                                     |
| docs-viewer-reports.js                              | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-route-config.js                         | App-shell-owned route config resolver, browser-safe registry loader, and route/scope projection helper.                                                                                                                     |
| docs-viewer-route-workflow.js                       | Focused route/document workflow owner for URL/query helpers, current-doc resolution, route application, index and payload loading, route-link handling, and popstate coordination.                                          |
| docs-viewer-router.js                               | routing and history helper.                                                                                                                                                                                                 |
| docs-viewer-runtime-lazy-controller.js              | Neutral lazy-controller adapter used to keep management controller imports gated without loading management-only JS on public routes.                                                                                       |
| docs-viewer-scope-lifecycle.js                      | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-scope-select-menu.js                    | Focused custom scope select-menu projection and interaction owner consumed by the config controller.                                                                                                                        |
| docs-viewer-search-controller.js                    | search helper or controller.                                                                                                                                                                                                |
| docs-viewer-search.js                               | search helper or controller.                                                                                                                                                                                                |
| docs-viewer-service-context.js                      | Focused public/manage service-context projection owner; public contexts omit management and local generated-read backend surfaces.                                                                                          |
| docs-viewer-sidebar.js                              | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-tree.js                                 | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-view-context.js                         | Selected-document hosted-view context projector plus main-view module context shaping for future central-panel views.                                                                                                       |
| docs-viewer-view-state.js                           | App-shell-owned index/document/info view-state skeleton and projection helper.                                                                                                                                              |
| reports/docs-broken-links-report.js                 | Docs Broken Links report module after the old Studio route controller was retired.                                                                                                                                          |
| reports/docs-index-table-report.js                  | report module.                                                                                                                                                                                                              |
| reports/reports-list-report.js                      | report module.                                                                                                                                                                                                              |
| reports/semantic-references-report.js               | report module.                                                                                                                                                                                                              |
| reports/source-config-report.js                     | report module.                                                                                                                                                                                                              |
|                                                     |                                                                                                                                                                                                                             |

## Notes

### `docs-viewer/runtime/js/docs-viewer-public.js` and `docs-viewer/runtime/js/docs-viewer-manage.js`

These files are the route-specific ES module entrypoint wrappers loaded by public and manage route shells.

- Useful future work should reduce shared-runtime coupling or route-load cost, such as generated-payload loading, loadable-doc visibility state, broader panel-layout ownership, or management lazy-boundary hardening.
- Future route/document workflow changes should extend `docs-viewer-route-workflow.js`, not add responsibility back to the entrypoint or app runtime coordinator.
- Preserve `docs-viewer/runtime/js/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

`docs-viewer/runtime/js/docs-viewer-app-boot.js`

- Keep this module limited to root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, boot failure status projection, and starting the app runtime coordinator.
- Do not move route application, generated docs/search reads, search/recent state transitions, bookmark storage, report rendering, backend writes, or management capability checks into it.

### `docs-viewer/runtime/js/docs-viewer-app-runtime.js`

- This file remains the private app coordinator for focused controller construction, callback handoff, route-global updates, private management startup callbacks, and the small returned app handle.
- Do not add new feature lifecycle ownership here; future controller work should narrow complete controller families to explicit state-domain and service inputs.
- Next risk-reduction slices should focus on complete new owner boundaries for future features, not restore route/document/search/bookmark/info/generated-data/visibility/management workflow behavior here.

### `docs-viewer/runtime/js/docs-viewer-app-composition.js`

- This module owns startup phase sequencing and authority records, including the public/manage split between browser route/config context, browser-safe config assets, generated reads, browser storage, management capability checks, and management write endpoints.
- Keep this module limited to runtime defaults, foundational owner creation, startup phase records, startup authority records, public/manage startup gating, and initial startup sequence orchestration.
- Do not move rendering, validation, generated-read internals, config normalization, bookmark storage, management writes, report behavior, or controller-specific UI behavior into it.
- The private app runtime coordinator still constructs focused controllers until a later slice narrows remaining controller families away from function-scoped bridge callbacks.

### `docs-viewer/runtime/js/docs-viewer-app-session.js`

- Keep this module limited to app-session creation, state defaults, named domain facades, route-session projection, and the runtime-internal state object needed by remaining controller handoffs.
- Do not move controller construction, event binding, generated reads, URL history, document rendering, bookmark persistence, or management writes into it.
- Future slices should narrow complete controller families to the relevant domain facade and remove their broad-state dependency from runtime handoff.

### `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`

- This module owns named reads for `index-tree.json`, selected by-id payloads, recently-added payloads, search indexes, references indexes, and reference-target buckets. Public route reads must not fall back to public docs `index.json`.
- Keep this module limited to data request option shaping, generated-read capability caching, retry/reload option projection, generated-search read capability checks, and named generated JSON read methods.
- Low-level generated-data fetch/retry helpers in `docs-viewer/runtime/js/docs-viewer-data.js` are allowed here because this module is the feature-facing generated-data owner.
- Do not move config loading, payload rendering, backend write authority, or management capability UI projection into it.

### `docs-viewer/runtime/js/docs-viewer-config-service.js`

- Keep this module limited to Docs Viewer config and UI-text fetch/retry behavior using generated-data runtime request projection.
- Do not move config normalization, scope route projection, UI rendering, generated JSON read methods, backend writes, or management capability UI projection into it.

### `docs-viewer/runtime/js/docs-viewer-asset-url.js`

- Keep this module limited to reading the asset-version meta value and appending asset/reload query parameters for browser asset requests.
- Do not move fetch/retry behavior, generated-read capability checks, service base URLs, config normalization, or backend write behavior into it.

### `docs-viewer/runtime/js/docs-viewer-data.js`

- Keep this module limited to low-level JSON fetch/retry helpers, generated-read retry helpers, and management reload path construction behind the generated-data runtime and config service.
- Direct imports should stay limited to `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` and `docs-viewer/runtime/js/docs-viewer-config-service.js`; feature controllers, reports, route config, app boot, and route context should consume their named owner contracts instead.

### `docs-viewer/runtime/js/docs-viewer-service-context.js`

- Keep this module limited to projecting static route context into generated-read, config, and management service surfaces.
- Public contexts must continue to omit report registry loads, management base URLs, local generated-read service base URLs, backend probes, and management service adapters. Do not move capability truth or write authority into this module.

### `docs-viewer/runtime/js/docs-viewer-report-service.js`

- Keep this module limited to local report endpoint paths, request options, local-server missing-base errors, and response-envelope handling for source-config and broken-links audit reports.
- Do not move report DOM rendering, table sorting/filtering, activity UI labels, generated-data runtime reads, management writes outside report actions, or management capability truth into it.

### `docs-viewer/runtime/js/docs-viewer-document-index-state.js`

- Keep this module limited to all-doc/doc map projection, public/manage visibility filtering, non-viewable/manage-only tree handling, non-loadable fallback resolution, default-doc resolution, and index status projection.
- Do not move route URL state, sidebar DOM rendering, document payload loading, search/recent rendering, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`

- This controller now consumes explicit document-index, selected-document, scope-config, panel-view, route-access, URL, and trail inputs instead of broad `state`.
- Keep this module limited to selected-document hosted-view context, metadata-info default open behavior, toggle projection, toolbar click handoff, update-on-document-change, close behavior, view-state projection sync, and public-safe availability.
- Do not move info-panel chrome rendering, hosted-view registration, metadata presentation, document payload rendering, URL history, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`

- Keep this module limited to promise-cached dynamic controller loading and explicit context assembly.
- Do not name this module as management-only or statically import `docs-viewer-management.js` from public-route startup paths; public read-only smokes assert that management-only JS is not fetched.

### `docs-viewer/runtime/js/docs-viewer-route-workflow.js`

- The focused route/document workflow owner. route workflow now exposes a private command contract for route application, index loading, document loading, history writes, route resolution, and route URL creation. The contract is backed by route-session, scope-config, document-index, selected-document, search/recent, and status inputs rather than a broad runtime state handoff.
- Keep this module limited to URL/query helpers, current-doc resolution, route application, index and payload load orchestration, canonical URL correction, route-link handling, and popstate coordination.
- It should continue to delegate low-level URL/history operations to `docs-viewer/runtime/js/docs-viewer-router.js`, final document pane rendering to `docs-viewer/runtime/js/docs-viewer-document-controller.js`, search/recent rendering to `docs-viewer/runtime/js/docs-viewer-search-controller.js`, bookmark storage/rendering to `docs-viewer/runtime/js/docs-viewer-bookmarks.js`, and management writes/actions to the lazy management modules.

### `docs-viewer/runtime/js/docs-viewer-management.js`

- This controller now receives named `managementState`, `serviceClient`, and `routeReload` contracts from the lazy runtime boundary instead of broad runtime `state`. It builds a management-local state facade from explicit route-session, scope-config, document-index, selected-document, search/recent, generated-data, and management domains for existing management child modules.
- action menu markup is design-time record rendering in `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`; this controller preserves binding, capability projection, and command workflow handoff for the rendered stable ids.
- Keep service access behind the management service-client contract and post-write reloads behind the route-reload contract.
- Do not move new backend writes, generated-read behavior, public hosted-view behavior, route shell boot, or route URL primitives into this file.

### `docs-viewer/runtime/js/docs-viewer-config-controller.js`

- this controller now consumes explicit scope-config, document-index, search/recent, route-session, config-service, and route-command inputs instead of broad `state`.
- the scope picker now projects custom select-menu option rows with `emoji`, scope id label, and config-backed `meta` while preserving the hidden native select as the existing value/change bridge for route workflow handoff.
- Keep this module focused on browser-safe Docs Viewer config loading, route-scope resolution, scope-picker projection, route-global/root-dataset projection, UI-text merge, recent-limit/status-label projection, and management/status copy updates.
- Do not move document index loading, payload rendering, URL history primitives, generated-read capability checks, backend writes, management actions, or route shell boot into it.

### `docs-viewer/runtime/js/docs-viewer-search-controller.js`

- search/recent route command bundling moved into this focused owner through `createDocsViewerSearchRouteCommands(...)`. The controller now consumes explicit `searchRecent`, `documentIndex`, `selectedDocument`, `routeCommands`, and `paneCommands` inputs for route application, history writes, current-doc resolution, default-doc fallback, result URL creation, loadable-doc target resolution, and pane projection requests.
- recently-added rendering remains here, while generated recently-added payload reads are delegated through `docs-viewer-generated-data-runtime.js`.
- Keep this module focused on generated search-index loading, result/recent rendering, debounce handoff, search/recent route activation, more-results behavior, route command consumption, and pane command requests.
- Do not move low-level URL construction, browser history primitives, document payload rendering, config loading, management writes, or panel toolbar/view switching into it.

### `docs-viewer/runtime/js/docs-viewer-bookmarks.js`

- bookmark route command bundling moved into this focused owner through `createDocsViewerBookmarkRouteCommands(...)`. The controller now consumes explicit bookmark, document-index, selected-document, search/recent, route-command, and search-reset command inputs for bookmark rendering and document-load handoff when opening a bookmark.
- Keep this module focused on bookmark loading, IndexedDB support fallback, list/toggle rendering, selected-document bookmark UI projection, edit state, pending focus, bookmark events, route command consumption, search-reset command consumption, and status-pill fallback callbacks.
- Do not move low-level history construction, document payload rendering, info-panel lifecycle, management writes, or future bookmark grouping/sync/export features into the app runtime coordinator.

### `docs-viewer/runtime/js/docs-viewer-document-controller.js`

- this controller now consumes explicit route-session, scope-config, selected-document, generated-data, and status command inputs instead of `context.state`.
- report metadata interpretation, generated-data report reads, and local report-service handoff moved to manage-owned `docs-viewer/runtime/js/docs-viewer-management-document-reports.js`; this shared controller now calls only an optional document-extras hook supplied by the entrypoint.
- Keep this module focused on document pane projection, payload rendering, loading/missing/error states, selected-document updates, and optional document-extras hook invocation.
- Do not move URL/history primitives, tree visibility projection, sidebar DOM rendering, search/recent rendering, report runtime imports, local report endpoint ownership, backend writes, or management action behavior into it.

### `docs-viewer/runtime/js/docs-viewer-sidebar.js`

- this renderer now consumes explicit document-index, selected-document, and scope-config projections instead of `context.state`.
- Keep this module focused on tree row rendering, expand-state projection, selected-document highlighting, breadcrumb rendering, update-date display, and scope-config management text display.
- Do not move document payload rendering, route workflow, generated-data reads, bookmark storage, search/recent behavior, or management writes into it.

### `docs-viewer/runtime/js/docs-viewer-app-shell.js`

- the app-shell owner for management action-area coordination.
- Current scope is intentionally narrow: render top-bar layout through `docs-viewer/runtime/js/docs-viewer-top-bar-renderer.js`, render viewer toolbar controls through `docs-viewer/runtime/js/docs-viewer-viewer-toolbar-renderer.js`, render index panel chrome through `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, clear management mounts when present, call optional manage-owned shell renderers supplied by the manage entrypoint, and return the rendered surfaces before existing management/theme binding continues.
- It also renders the main-view shell through `docs-viewer/runtime/js/docs-viewer-main-view-renderer.js` before existing document, sidebar, bookmark, search, and management controllers read the preserved rendered-document/search/recent IDs.
- It also renders the info panel shell through `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`; lifecycle and metadata presentation stay in the focused info-panel host/view modules.
- It does not import management action, selected-document action, or management shell renderers. Manage-only shell rendering is injected through `docs-viewer/runtime/js/docs-viewer-management-shell-composition.js` during manage boot.
- The existing lazy management controller continues to own backend reachability, capability refresh, command wiring, and status projection.

### `docs-viewer/runtime/js/docs-viewer-top-bar-renderer.js`

- the focused top-bar layout owner for the viewer-toolbar surface and management-toolbar mount.
- Keep this module limited to rendering layout mounts and delegating control rendering to toolbar owners.

### `docs-viewer/runtime/js/docs-viewer-viewer-toolbar-renderer.js`

- the focused renderer for scope picker, recently-added button, search input, index-view toggle, and info/context panel toggle.
- the scope picker shell now renders the custom select-menu trigger/list plus a visually hidden native select with the preserved `docsViewerScopeSelect` id for controller/event compatibility.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount from route context.

### `docs-viewer/runtime/js/docs-viewer-scope-select-menu.js`

- the focused owner for custom scope select-menu option rendering, trigger projection, open/close behavior, keyboard navigation, and dispatching the preserved native select `change` event.
- Keep route navigation, browser config normalization, scope option record construction, and route-global projection in `docs-viewer/runtime/js/docs-viewer-config-controller.js`.

### `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`

- the focused renderer for management action markup.
- the management `Actions` menu is rendered from design-time item records that define stable ids, labels, optional emoji, and default visibility; command behavior remains outside this renderer.
- selected-document `Edit` and `Markdown source` controls moved to the rendered-document main-view toolbar; this renderer keeps broader management/admin Actions such as create, import, delete, settings, rebuild, and scope lifecycle commands.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount.

### `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`

- the focused renderer for management-only context menu and modal shell markup.
- Keep this module limited to preserving the existing `docsViewerContextMenu`, metadata modal, import modal, settings modal, and `docsHtmlImport*` host refs inside the management shell mount.
- Do not move metadata save behavior, import workflow behavior, settings writes, context-menu actions, backend reachability checks, generated-data reads, or management capability projection into this renderer.

### `docs-viewer/runtime/js/docs-viewer-management-shell-composition.js`

- the manage-owned app-shell renderer composition.
- Keep this module limited to importing management action, selected-document action, and management shell renderers and returning the renderer bundle consumed by `docs-viewer/runtime/js/docs-viewer-app-shell.js`.
- Keep it loaded only through `docs-viewer/runtime/js/docs-viewer-manage.js` and manage-specific tests. Public entrypoints and public-safe shared shell code must not import it.

### `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`

- the focused renderer for index panel shell chrome.
- Keep this module limited to rendering the sidebar container, toolbar controls, nav mount, and applying index-panel projection to DOM refs. Do not move tree row rendering, drag/drop behavior, search/recent behavior, or document payload rendering into it.

### `docs-viewer/runtime/js/docs-viewer-main-view-renderer.js`

- the focused renderer for main-view shell chrome, replacing the former document-shell renderer boundary.
- the shared main-view renderer is public-safe and no longer defines selected-document status pills or edit/source controls; those manage-only controls are rendered by `docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js`.
- Keep this module limited to rendering `.docsViewer__main`, the main-view toolbar surface, rendered-document metadata chrome, rendered-document/search/recent result mounts, and applying the current narrow rendered/search/recent/results-status projection to DOM refs.
- Do not move Markdown rendering, generated report loading, payload fetching, breadcrumb metadata rendering, status-pill content rendering, selected-document edit/source controls, bookmark storage, or search/recent result rendering into it.

### `docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js`

- the manage-owned renderer for selected-document status pills, `Edit`, and `Markdown source` controls.
- Keep this module loaded only through manage-capable shell composition; public entrypoints and public-safe shared renderers must not import it statically or duplicate its control ids/labels.
- Keep command behavior in `docs-viewer/runtime/js/docs-viewer-management.js` and its action/controller children.

### `docs-viewer/runtime/js/docs-viewer-management-document-reports.js`

- the manage-owned document report mounting module.
- Keep this module loaded only through `docs-viewer/runtime/js/docs-viewer-manage.js`; public entrypoints must not import it statically or expose the report registry route-config field.
- Keep report metadata detection, report-context construction, generated-data report reads, report registry URL handoff, and local report-service creation here before delegating to `docs-viewer/runtime/js/docs-viewer-reports.js`.
- Do not move report runtime imports or local report-service construction back into shared public-safe document rendering.

### `docs-viewer/runtime/js/docs-viewer-main-view-host.js`

- the focused main-view switch-intent owner.
- the host now exposes main-view module context creation and a toolbar projection helper, but source-editor service details remain outside the host and are supplied only through explicit context options.
- Keep this module limited to resolving main-view hosted-view availability, projecting active main-view state through panel layout, accepting switch requests for built-in main views, and passing generic main-view intent/toolbar/warning helpers into module contexts.
- Do not add source-editor service details, report migration behavior, arbitrary module loading, plugin behavior, or rendered-document/search/recent rendering into it.

### `docs-viewer/runtime/js/docs-viewer-app-context.js`

- the focused route-context owner for the app shell.
- Keep this module limited to assembling route context from route config/access projection, current URL management/import intent, viewer pathname, and bookmark storage scope.
- Do not move route application, config loading, generated-data fetching, backend capability checks, or write behavior into it.

### `docs-viewer/runtime/js/docs-viewer-panel-layout.js`

- the focused panel projection owner for the app shell.
- legacy sidebar local-storage migration was retired by cleanup tracker `FU-1`; this module reads and writes only the current `dotlineform-docs-viewer-index-panel:<scope>` key.
- Keep this module limited to index panel state storage/projection, current document/search/recent/results-status projection handoff, info-panel visibility/layout projection, and delegation to the view-state skeleton.
- Do not add toolbar controls, hosted-view registration, document payload rendering, search result rendering, or management action behavior to it.

### `docs-viewer/runtime/js/docs-viewer-route-config.js`

- the focused route config resolver and route/scope projection helper.
- Keep this module limited to the durable route config shape, browser-safe route-config registry loading/resolution, explicit route-config normalization for tests/boot callers, and projection of scope config into route globals.
- inline route-config scripts and legacy `#docsViewerRoot` route data-attribute fallback were removed. Route shells must use the registry contract; focused tests must pass explicit route config or route context rather than relying on shell data as a synthetic config source.
- route-config camelCase field aliases and object-map route registries were removed. The module now resolves only the `docs_viewer_route_config_v1` snake_case route record shape from a `docs_viewer_route_config_registry_v1` registry whose `routes` value is an array.
- Do not add config fetching, URL history changes, payload loading, or backend capability checks to it.

### `docs-viewer/runtime/js/docs-viewer-access.js`

- the focused static access projection helper.
- Keep this module limited to public/manage/manage-local route intent, hosted-view access defaults, and access checks.
- Do not add browser-side write authority, per-click permission checks, or backend reachability probing to it.

### `docs-viewer/runtime/js/docs-viewer-view-state.js`

- the focused index/document/info view-state skeleton.
- Keep this module pure and projection-oriented so later info-panel work can consume explicit state without reading broad route/controller state.
- Do not add DOM rendering, storage, toolbar event handling, or payload loading to it.

### `docs-viewer/runtime/js/docs-viewer-hosted-views.js`

- the focused hosted-view registration shape for ordinary repo JavaScript modules.
- panel-specific listing moved into this module through `listByPanel(...)` and `listDocsViewerHostedViewsForPanel(...)` so toolbars can consume the same available/disabled/unavailable/access-blocked state as direct registry resolution.
- hosted-view records may define `load`, `mount`, `update`, `unmount`, and `dispose`, but registration and visibility do not imply backend authority or write capability.
- built-in hosted-view records are current architecture and are exposed through `createDocsViewerBuiltInHostedViews()`. The old `createDocsViewerCompatibilityHostedViews()` alias was removed during architecture cleanup after active runtime callers and focused smokes had moved to the built-in factory.
- `createDocsViewerDefaultHostedViews()` is now the explicit code-owned registration surface for public-safe built-in records; `createDocsViewerRouteHostedViews(...)` strips route `module` strings and prevents route config from overriding default ids.
- manage-only `markdown-source` moved out of this shared hosted-view registry and into `docs-viewer/runtime/js/docs-viewer-management-hosted-views.js`, which is imported by the manage entrypoint.
- Keep this module limited to records, lifecycle method names, public-safe built-in hosted-view records, route-record filtering, panel-specific listing, access/availability checks, and graceful absence. The `metadata-info` record may load the focused metadata hosted-view module, but the registry should not own rendering, panel state, source editing, or management services.
- Do not turn it into a plugin system, arbitrary dependency loader, panel toolbar renderer, route-config module loader, or third-party visualization owner.

### `docs-viewer/runtime/js/docs-viewer-management-hosted-views.js`

- the manage-owned hosted-view record owner.
- This module currently defines the `markdown-source` main hosted view and lazy-loads `docs-viewer/runtime/js/modules/source-editor/source-editor.js`.
- Keep this module loaded only through `docs-viewer/runtime/js/docs-viewer-manage.js`; public entrypoints must not import it or the source-editor module.
- Do not move public hosted-view registration, route-config hosted-view filtering, panel state, or source-editor service implementation into it.

### `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`

- the focused renderer for info-panel shell chrome.
- minimal info-panel toolbar rendering and projection moved here. It renders view buttons from projected hosted-view options and marks disabled/access-blocked views as unavailable without owning lifecycle or route state.
- Keep this module limited to rendering the info-panel container, accessible title/label, close control, toolbar, hosted-view mount, status node, and projection attributes.
- Do not move hosted-view lifecycle, metadata rendering, source editing, panel toolbar selection, or management actions into it.

### `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`

- the focused lifecycle owner for info-panel hosted views.
- info hosted-view option projection moved here. The host now exposes `viewOptions()` and includes info view options in panel projection so the renderer can show available, disabled, unavailable, and access-blocked states.
- this host is the concrete Docs Viewer hosted-view lifecycle model: resolve/list, load, mount, update, unmount, close, dispose, and graceful absence. It should not become a general plugin platform.
- Keep this module limited to resolving/listing registered info views, loading them, mounting/updating/unmounting them in the assigned info-panel body, closing the panel, and reporting graceful absence.
- Do not add route-state mutation, URL history behavior, metadata field rendering, backend writes, or plugin discovery to it.

### `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`

- public and manage metadata-info rendering consume selected by-id payload metadata through `docs-viewer-view-context.js`, not public tree rows or public docs `index.json`.
- Keep this module limited to rendering selected-document metadata from explicit context fields.
- Do not read broad viewer state, expose source paths, add edit controls, or call management endpoints.

### `docs-viewer/runtime/js/docs-viewer-view-context.js`

- the focused selected-document hosted-view context projector.
- public-safe hosted views should receive explicit selected-document, route/access, payload, viewer-scope, URL, trail, and display-label inputs from this helper rather than reading broad runtime state.
- main-view module contexts now add generic `mainView` helpers for active-view id, switch requests, toolbar projection, and local warnings, plus source-editor service slots that are omitted unless route access allows management.
- selected metadata comes from the selected by-id payload cache; public contexts project only reader metadata while manage contexts can retain richer selected-document metadata.
- Keep this module limited to resolving the selected doc, cached payload, parent trail, route access flags, canonical URL, viewer scope, display labels, and generic main-view helper slots from explicit inputs.
- Future info views should extend or consume this helper
- Do not add DOM rendering, hosted-view lifecycle, URL history mutation, source-editor service implementation, or backend writes to it.

### `docs-viewer/runtime/js/modules/source-editor/source-editor.js`

- the manage-only Markdown source body editor module for the `markdown-source` main hosted view.
- Keep this module limited to source-body view orchestration, native textarea/gutter rendering, dirty-state projection, dirty leave confirmation, `Rebuild doc` submission, diagnostics display, rendered-payload reload handoff, and back-to-rendered switching.
- Do not add front matter editing, metadata writes, semantic-reference target picking, generated-data builder ownership, third-party editor dependencies, route URL state, or public-route source services to it.

### Docs Import And Management

- Current boundary: Docs Import is a Docs Viewer management-modal app, not a standalone route surface. `docs-viewer/runtime/js/docs-viewer-management.js` lazily initializes `docs-viewer/runtime/js/docs-html-import.js` only from the management modal host.
- Keep modal app state, scope/file selection, service availability display, and `studio:ready` route-ready dataset projection in `docs-viewer/runtime/js/docs-html-import.js`.
- Keep import result rendering in `docs-viewer/runtime/js/docs-html-import-render.js`.
- Keep preview/write orchestration in `docs-viewer/runtime/js/docs-html-import-workflow.js`.
- Keep import writes behind `docs-viewer/runtime/js/docs-viewer-management-client.js` and management endpoints such as `/docs/import-source`.
- Keep management-only workflows behind the lazy management boundary.
- management initialization, capability refresh, action/menu/modal binding, imports, settings, scope lifecycle, status pills, and write orchestration remain behind `docs-viewer/runtime/js/docs-viewer-management.js`, management child modules, and `docs-viewer/runtime/js/docs-viewer-management-client.js`; hosted-view visibility must not imply write authority.
- Keep make-viewable target resolution in `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js`.
- Move command-specific write behavior to `docs-viewer/runtime/js/docs-viewer-management-actions.js` or a workflow-specific module when it gains independent state.

### Reports, Search, And Bookmarks

- Keep reports self-contained and loaded through the report allowlist.
- Keep report mounting behind the manage entrypoint until a named public-promotion slice defines a public-safe report loader, registry/data input, CSS, route config, and asset-load tests.
- Keep local source-config and broken-links endpoint access behind `docs-viewer/runtime/js/docs-viewer-report-service.js`; report modules should consume `context.reportService` rather than `managementBaseUrl` or direct `window.fetch(...)`.
- Extract shared report table or pager helpers only after at least two reports need the same behavior.
- Keep search and bookmark storage/controller behavior focused; revisit if grouping, sync, export, or cross-scope behavior is added.