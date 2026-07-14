---
doc_id: docs-viewer-javascript-inventory
title: JavaScript Inventory
added_date: 2026-05-20
last_updated: 2026-07-14
parent_id: docs-viewer-runtime-boundary
---
# Docs Viewer JavaScript Inventory

Browser JavaScript under `docs-viewer/runtime/js/`.

Risk themes:

- private app runtime coordination
- management coordinator growth
- import workflow ownership
- scope lifecycle
- search/bookmark controller boundaries
- review-package composition that must remain outside the app runtime and management coordinators.

| File                                                | Focus                                                                                                                                                                                                                       |
|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| docs-html-import-modals.js                          | Filename-conflict modal rendering and interaction through the shared management-modal focus contract.                                                                                                                      |
| docs-html-import-render.js                          | Docs import result rendering helper.                                                                                                                                                                                        |
| docs-html-import-workflow.js                        | Docs import preview/write workflow helper.                                                                                                                                                                                  |
| docs-html-import.js                                 | Docs import controller for source-type partitioning, ordinary-file multi-selection, reviewed-package single selection, refreshed staging state, and explicit workflow handoff.                                              |
| docs-viewer-access.js                               | Explicit public/manage/review app-kind normalization and narrow route-access projection.                                                                                                                                  |
| docs-viewer-app-boot.js                             | App boot owner for route/config context, code-owned view-registry assembly, app-shell initialization, shell-ref handoff, theme loading, and runtime startup.                                                               |
| docs-viewer-app-composition.js                      | App-composition owner for runtime defaults, foundational owner creation, view-registry capability-input handoff, startup records, authority records, and feature-aware startup sequencing.                                |
| docs-viewer-app-context.js                          | Explicit app-context and route-context assembly, service-availability projection, and mutable scope route-context projection.                                                                                               |
| docs-viewer-app-runtime.js                          | Private runtime wiring after document-view/status extraction; remaining focused controller construction, config handoff, event binding, startup callbacks, and returned app handle.                                      |
| docs-viewer-app-session.js                          | App-session owner for state defaults, single-owner named state-domain facades, and public/manage route-session projection.                                                                                                |
| docs-viewer-asset-url.js                            | Focused asset-version URL projection helper for static browser assets.                                                                                                                                                      |
| docs-viewer-bookmarks.js                            | bookmark/favourite support.                                                                                                                                                                                                 |
| docs-viewer-config-controller.js                    | config/scope setup.                                                                                                                                                                                                         |
| docs-viewer-config-service.js                       | Focused browser-safe config and UI-text fetch/retry owner consumed by the config controller.                                                                                                                                |
| docs-viewer-configured-scope-provider.js            | Configured-scope collection provider for named index, document, search, recent, reference, and optional source reads/writes without granting backend authority.                                                            |
| docs-viewer-data.js                                 | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-document-controller.js                  | document rendering/controller support.                                                                                                                                                                                      |
| docs-viewer-document-index-state.js                 | Focused document-index projection owner for public/manage visibility filtering, manage-only tree omission, non-loadable fallback resolution, default-doc selection, and index status projection.                            |
| docs-viewer-document-view-coordinator.js            | Document main-view coordination owner for host construction, active view/mode/control projection, info defaults, and rendered/search/recent transitions.                                                                  |
| docs-viewer-drag-drop.js                            | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-favourites.js                           | bookmark/favourite support.                                                                                                                                                                                                 |
| docs-viewer-generated-data-runtime.js               | Generated-data request owner using explicit generated-data, management, and selected-document domains with separate generated-read capability state and named JSON read methods.                                         |
| docs-viewer-document-display-mode-host.js           | Document-view display-mode lifecycle owner for rendered/source modes inside the rendered-document main view.                                                                                                               |
| docs-viewer-index-panel-renderer.js                 | App-shell-owned index panel chrome renderer and projection applier.                                                                                                                                                         |
| docs-viewer-index-panel.js                          | index panel state, current-key persistence, toggle projection, and document-pane visibility helper.                                                                                                                         |
| docs-viewer-info-panel-controller.js                | Focused info-panel coordination owner for selected-document context, toggle state, outside-context view selection, open/update/close behavior, and public-safe availability.                                                |
| docs-viewer-info-panel-host.js                      | Info-panel hosted-view lifecycle owner for load, mount, update, unmount, close, and graceful absence.                                                                                                                       |
| docs-viewer-info-panel-renderer.js                  | App-shell-owned info-panel chrome renderer and projection applier.                                                                                                                                                          |
| docs-viewer-main-view-host.js                       | Main-view switch-intent and availability owner for rendered-document, search-results, and recent-results.                                                                                                                   |
| docs-viewer-main-view-renderer.js                   | App-shell-owned main-view shell, rendered-document toolbar chrome, and narrow rendered/search/recent projection applier.                                                                                                    |
| docs-viewer-manage.js                               | Manage entrypoint wrapper that imports manage-owned document extras, hosted views, shell composition, and starts the manage app boot owner.                                                                                 |
| docs-viewer-management-action-workflow.js           | management viewability target workflow helper.                                                                                                                                                                              |
| docs-viewer-management-actions.js                   | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-capabilities.js              | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-client.js                    | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-config.js                    | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-document-actions-renderer.js | Manage-owned selected-document edit/source controls rendered into the shared main-view toolbar action area.                                                                                                                 |
| docs-viewer-management-event-router.js              | Stable control-to-command binding, Actions-menu behavior, and ordered root/keyboard event delegation.                                                                                                                       |
| docs-viewer-management-hosted-views.js              | Manage-owned view, document-mode, and document-control definitions supplied by the manage entrypoint.                                                                                                                      |
| docs-viewer-management-interactions.js              | management support module.                                                                                                                                                                                                  |
| docs-viewer-management-import-controller.js         | Lazy Docs Import initialization, retry/error state, and management-modal host handoff.                                                                                                                                      |
| docs-viewer-management-metadata-workflow.js          | Metadata parent projection, validation, payload shaping, and save handoff.                                                                                                                                                   |
| docs-viewer-management-modal-composition.js          | Focused metadata/settings workflow and shared management-modal controller composition.                                                                                                                                      |
| docs-viewer-management-modals.js                    | Metadata/import/settings modal lifecycle, explicit focus containment, and keyboard dismissal after transient modal shell and metadata parent-picker extraction.                                                             |
| docs-viewer-management-render.js                    | management support module.                                                                                                                                                                                                  |
| docs-viewer-review-sessions-modal.js                | Review-session modal rendering, selection controls, shared focus containment, Escape dismissal, and focus return.                                                                                                          |
| docs-viewer-management-settings-workflow.js          | Settings service loading and narrow field/change/close workflow contract.                                                                                                                                                    |
| docs-viewer-management-scope-lifecycle-controller.js | Scope/sub-scope control projection, event wiring, lazy flow loading, and post-apply refresh composition.                                                                                                                      |
| docs-viewer-management-shell-composition.js         | Manage-owned shell renderer composition supplied by the manage entrypoint so public-safe app shell code does not import management renderers.                                                                               |
| docs-viewer-management-shell-renderer.js            | Manage-owned management context-menu, metadata modal, import modal, settings modal, and import host renderer.                                                                                                               |
| docs-viewer-management.js                           | management coordinator after shared action workflow helper extraction.                                                                                                                                                      |
| docs-viewer-metadata-info-view.js                   | Public-safe read-only metadata info hosted view.                                                                                                                                                                            |
| docs-viewer-panel-layout.js                         | App-shell-owned panel projection handoff for index state, current main-view visibility, and the view-state skeleton.                                                                                                        |
| docs-viewer-public.js                               | Public entrypoint wrapper that imports and starts the public app boot owner.                                                                                                                                                |
| review/docs-viewer-returned-package-provider.js     | Read-only returned-package collection provider for package-selected generated, manifest, inventory, list, and repair operations.                                                                                          |
| review/docs-viewer-review-client.js                 | Focused JSON transport and error normalization for Docs Review endpoints.                                                                                                                                                    |
| review/docs-viewer-review-controller.js             | Review package selection, repair-state, inventory, identity-only import handoff, shared-toolbar, and canonical-comparison workflow owner.                                                                                   |
| review/docs-viewer-review.js                        | Read-only review entrypoint that contributes only the returned-package provider and review controller to shared app boot.                                                                                                  |
| docs-viewer-render.js                               | rendering helper.                                                                                                                                                                                                           |
| docs-viewer-report-service.js                       | Focused local report endpoint adapter for source-config and broken-links audit reports.                                                                                                                                     |
| docs-viewer-reports.js                              | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-route-config.js                         | App-shell-owned route config resolver, browser-safe registry loader, and route/scope projection helper.                                                                                                                     |
| docs-viewer-route-features.js                       | Allowlisted route-feature normalization, dependency validation, feature queries, and feature filtering for code-owned runtime records.                                                                                     |
| docs-viewer-view-registry.js                        | Sole code-owned normalization, lookup, and eligibility projection for panel views, document modes, and document controls.                                                                                                  |
| docs-viewer-route-workflow.js                       | Focused route/document workflow owner for URL/query helpers, current-doc resolution, route application, index and payload loading, route-link handling, and popstate coordination.                                          |
| docs-viewer-router.js                               | routing and history helper.                                                                                                                                                                                                 |
| docs-viewer-runtime-lazy-controller.js              | Neutral lazy-controller adapter used to keep management controller imports gated without loading management-only JS on public routes.                                                                                       |
| docs-viewer-scope-lifecycle.js                      | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-scope-select-menu.js                    | Focused custom scope select-menu projection and interaction owner consumed by the config controller.                                                                                                                        |
| docs-viewer-search-controller.js                    | search helper or controller.                                                                                                                                                                                                |
| docs-viewer-search.js                               | search helper or controller.                                                                                                                                                                                                |
| docs-viewer-service-context.js                      | Independent generated-data, source, management, and browser-safe config service-surface projection.                                                                                                                        |
| docs-viewer-management-source-adapter.js            | Manage-entrypoint-owned optional source-service transport adapter supplied to the configured-scope provider; backend capabilities remain authoritative.                                                                  |
| docs-viewer-sidebar.js                              | runtime support module.                                                                                                                                                                                                     |
| docs-viewer-status-controller.js                    | Viewer status text/error projection and nested route busy-state owner.                                                                                                                                                     |
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

### `site/docs-viewer/runtime/js/public/docs-viewer-public.js` and `docs-viewer/runtime/js/management/docs-viewer-manage.js`

These files are the route-specific ES module entrypoint wrappers loaded by public and manage route shells.

- Useful future work should reduce shared-runtime coupling or route-load cost, such as generated-payload loading, loadable-doc visibility state, broader panel-layout ownership, or management lazy-boundary hardening.
- Future route/document workflow changes should extend `docs-viewer-route-workflow.js`, not add responsibility back to the entrypoint or app runtime coordinator.
- Preserve `site/docs-viewer/runtime/js/shared/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

`site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js`

- Keep this module limited to root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, boot failure status projection, and starting the app runtime coordinator.
- Do not move route application, generated docs/search reads, search/recent state transitions, bookmark storage, report rendering, backend writes, or management capability checks into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js`

- This file remains the private app coordinator for focused controller construction, callback handoff, route-global updates, private management startup callbacks, and the small returned app handle.
- Document-view host construction, active control queries, mode/info synchronization, repeated view-transition chains, and status/busy projection moved to focused Phase 5 owners.
- Do not add new feature lifecycle ownership here; future controller work should narrow complete controller families to explicit state-domain and service inputs.
- Next risk-reduction slices should focus on complete new owner boundaries for future features, not restore route/document/search/bookmark/info/generated-data/visibility/management workflow behavior here.

### `site/docs-viewer/runtime/js/shared/docs-viewer-app-composition.js`

- This module owns foundational provider/service construction, dynamic backend-capability inputs for the boot-owned view registry, and feature-aware startup phase sequencing and authority records.
- Keep this module limited to runtime defaults, foundational owner creation, startup phase records, startup authority records, public/manage startup gating, and initial startup sequence orchestration.
- Do not move rendering, validation, generated-read internals, config normalization, bookmark storage, management writes, report behavior, or controller-specific UI behavior into it.
- The private app runtime coordinator still constructs focused controllers until a later slice narrows remaining controller families away from function-scoped bridge callbacks.

### `site/docs-viewer/runtime/js/shared/docs-viewer-app-session.js`

- Keep this module limited to app-session creation, state defaults, single-owner named domain facades, route-session projection, and the runtime-internal state object needed by remaining controller handoffs.
- Phase 5 removed duplicate facade exposure for panel expansion, status labels, non-viewable presentation, management route identity, backend capability/reload state, management messages, and the view registry.
- Do not move controller construction, event binding, generated reads, URL history, document rendering, bookmark persistence, or management writes into it.
- Future slices should narrow complete controller families to the relevant domain facade and remove their broad-state dependency from runtime handoff.

### `site/docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js`

- Own main-view host, document display-mode host, and info-panel controller construction from explicit registry and document-context inputs.
- Own active view/mode projection, control eligibility queries, mode-specific info defaults, and rendered/search/recent transition sequencing.
- Keep lifecycle implementations in the focused hosts and keep document/search/info rendering plus live interaction state in their controllers.
- Do not add route loading, payload transport, source writes, bookmark persistence, management commands, or generic event-bus behavior.

### `site/docs-viewer/runtime/js/shared/docs-viewer-status-controller.js`

- Own viewer status text/error projection and nested busy-state accounting against the narrow `busyStatus` domain.
- Keep management message state in the management domain; the status controller receives only display commands and a busy counter.
- Do not add workflow messages, backend capability state, request orchestration, or controller lifecycle.

### `site/docs-viewer/runtime/js/shared/docs-viewer-generated-data-runtime.js`

- This module owns transport reads for `index-tree.json`, selected by-id payloads, recently-added payloads, search indexes, references indexes, and reference-target buckets. Public route reads must not fall back to public docs `index.json`.
- Keep this module limited to data request option shaping, generated-read capability caching, retry/reload option projection, generated-search read capability checks, payload normalization, and static/local generated JSON transport behind the configured-scope provider.
- Low-level generated-data fetch/retry helpers in `site/docs-viewer/runtime/js/shared/docs-viewer-data.js` are allowed here because this module is the generated-read transport owner.
- Do not move config loading, payload rendering, backend write authority, or management capability UI projection into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-configured-scope-provider.js`

- This module owns the feature-facing collection contract for configured scopes: `readIndex`, `readDocument`, `readSearch`, `readRecentlyAdded`, and `readReferences`.
- It resolves active or explicitly requested configured-scope URLs and reference targets, then delegates generated transport to `docs-viewer-generated-data-runtime.js`.
- `readSource` and `writeSource` must be absent unless the corresponding source adapter methods are explicitly supplied. Provider or method presence does not grant backend authority.
- Do not add returned-package behavior, UI lifecycle, retry loops, capability truth, DOM work, or management workflow orchestration here.

### `docs-viewer/runtime/js/management/docs-viewer-management-source-adapter.js`

- This manage-entrypoint-owned module supplies optional source-service delegation to the provider's `readSource` and `writeSource` methods.
- It does not infer capability from a base URL; the backend endpoint remains authoritative and may reject an operation.
- Do not move source-editor UI lifecycle, generated document reload, management capability projection, or canonical import/promotion behavior into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-config-service.js`

- Keep this module limited to Docs Viewer config and UI-text fetch/retry behavior using generated-data runtime request projection.
- Do not move config normalization, scope route projection, UI rendering, generated JSON read methods, backend writes, or management capability UI projection into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-route-features.js`

- This module owns the allowlist for `configured-scope-discovery`, `scope-selection`, `search`, `recently-added`, `bookmarks`, `reports`, `source-editing`, and `management`.
- It rejects unknown ids and invalid feature dependencies, projects camelCase feature policy, and filters code-owned records by their required feature.
- It does not register controllers, modules, handlers, routes, or backend authority.

### `site/docs-viewer/runtime/js/shared/docs-viewer-asset-url.js`

- Keep this module limited to reading the asset-version meta value and appending asset/reload query parameters for browser asset requests.
- Do not move fetch/retry behavior, generated-read capability checks, service base URLs, config normalization, or backend write behavior into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-data.js`

- Keep this module limited to low-level JSON fetch/retry helpers, generated-read retry helpers, and management reload path construction behind the generated-data runtime and config service.
- Direct imports should stay limited to `site/docs-viewer/runtime/js/shared/docs-viewer-generated-data-runtime.js` and `site/docs-viewer/runtime/js/shared/docs-viewer-config-service.js`; feature controllers, reports, route config, app boot, and route context should consume their named owner contracts instead.

### `site/docs-viewer/runtime/js/shared/docs-viewer-service-context.js`

- Keep this module limited to projecting normalized route service records into independent `generatedData`, `source`, `management`, and browser-safe `config` surfaces.
- `generatedData` may use static assets or a local base URL without implying that source or management services exist.
- Service presence and URLs do not grant backend capability or write authority. Public route config must keep every local base URL blank.

### `docs-viewer/runtime/js/reports/docs-viewer-report-service.js`

- Keep this module limited to local report endpoint paths, request options, local-server missing-base errors, and response-envelope handling for source-config and broken-links audit reports.
- Do not move report DOM rendering, table sorting/filtering, activity UI labels, generated-data runtime reads, management writes outside report actions, or management capability truth into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-document-index-state.js`

- Keep this module limited to all-doc/doc map projection, public/manage visibility filtering, non-viewable/manage-only tree handling, non-loadable fallback resolution, default-doc resolution, and index status projection.
- Do not move route URL state, sidebar DOM rendering, document payload loading, search/recent rendering, or management writes into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js`

- This controller now consumes explicit document-index, selected-document, scope-config, panel-view, app-context, URL, and trail inputs instead of broad `state`.
- Keep this module limited to selected-document hosted-view context, configured default-view opening, toggle projection, update-on-document-change, close behavior, view-state projection sync, and public-safe availability.
- Do not move info-panel chrome rendering, hosted-view registration, metadata presentation, document payload rendering, URL history, or management writes into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-runtime-lazy-controller.js`

- Keep this module limited to promise-cached dynamic controller loading and explicit context assembly.
- Do not name this module as management-only or statically import `docs-viewer-management.js` from public-route startup paths; public read-only smokes assert that management-only JS is not fetched.

### `site/docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js`

- The focused route/document workflow owner. route workflow now exposes a private command contract for route application, index loading, document loading, history writes, route resolution, and route URL creation. The contract is backed by route-session, scope-config, document-index, selected-document, search/recent, and status inputs rather than a broad runtime state handoff.
- Keep this module limited to URL/query helpers, current-doc resolution, route application, index and payload load orchestration, canonical URL correction, route-link handling, and popstate coordination.
- It should continue to delegate low-level URL/history operations to `site/docs-viewer/runtime/js/shared/docs-viewer-router.js`, final document pane rendering to `site/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js`, search/recent rendering to `site/docs-viewer/runtime/js/shared/docs-viewer-search-controller.js`, bookmark storage/rendering to `site/docs-viewer/runtime/js/shared/docs-viewer-bookmarks.js`, and management writes/actions to the lazy management modules.

### `docs-viewer/runtime/js/management/docs-viewer-management.js`

- This controller receives named `managementState`, `serviceClient`, and `routeReload` contracts from the lazy runtime boundary instead of broad runtime `state`. It consumes document-index, selected-document, search/recent, route-session, scope-config, and management domains directly and passes only the required named domains to each child controller.
- It composes the current active route document into the behavior-preserving one-document action context and supplies pure action resolutions to render projection and command workflows. It does not own action definitions or multiple-selection state.
- The former management-local cross-domain property facade is removed. Management capability checks mutate only the management and route-session domains; generated-read capability caching remains solely in `docs-viewer-generated-data-runtime.js`.
- action menu markup is design-time record rendering in `docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js`; this controller preserves binding, capability projection, and command workflow handoff for the rendered stable ids.
- metadata and settings shell refs, validation/loading behavior, and modal handoffs are composed by focused workflow owners rather than this coordinator.
- stable management-control binding, Actions-menu interaction, and root/keyboard event delegation belong to `docs-viewer-management-event-router.js`.
- Keep service access behind the management service-client contract and post-write reloads behind the route-reload contract.
- Do not move new backend writes, generated-read behavior, public hosted-view behavior, route shell boot, or route URL primitives into this file.

### `docs-viewer/runtime/js/management/docs-viewer-action-definitions.js`

- The manage-owned, code-owned action-target contract for canonical action ids, `scope`/`active-document`/`selection` targets, `primary`/`all`/`exactly-one` selection policies, disabled reasons, stable target-id resolution, and the temporary one-document context adapter used before multiple selection exists.
- The module is pure and side-effect free. It must not own renderer placement, DOM refs, handlers, modal/workflow state, hosted-view eligibility, backend capabilities, service transport, or mutation implementation.
- Shared and manage-only control records may reference its canonical ids through passive `actionId`/`data-docs-viewer-action` values; public entrypoints do not import this manage-only module.

### `docs-viewer/runtime/js/management/docs-viewer-management-import-controller.js`

- Owns the management-side Docs Import lifecycle boundary: lazy module loading, single in-flight initialization, retry after a failed load, staged-file refresh on every later modal open, boot-error projection, terminal imported-document handoff, and the action-to-modal handoff.
- Receives explicit import host refs, service/config URLs, and scope/modal callbacks; it forwards busy and terminal-result projection to the modal owner but does not own import preview/write behavior or general management modal behavior.
- Keep Docs Import preview and write orchestration in `docs-viewer/runtime/js/import/docs-html-import.js` and its child modules.

### `docs-viewer/runtime/js/management/docs-viewer-management-event-router.js`

- Owns stable management control binding, the Actions-menu toggle/dismissal contract, named command invocation, and ordered root/keyboard delegation to interaction and modal controllers.
- It receives named command callbacks and focused controller getters; it does not own command implementation, workflow state, capability policy, drag/drop behavior, or a generic application event bus.
- Scope lifecycle retains its own five control bindings; the event router invokes that focused controller's wiring contract during management startup.

### `docs-viewer/runtime/js/management/docs-viewer-management-interactions.js`

- Owns manage-only navigation, edit, context-menu, and current single-document drag event routing.
- Context-menu records and events use the same canonical `data-docs-viewer-action` ids as toolbar and Actions-menu controls, while target/cardinality interpretation remains in `docs-viewer-action-definitions.js`.
- It does not own action targeting or multiple-selection state. The multiple-selection slice must delegate selected ids, primary id, anchor, range/toggle behavior, pruning, and row projection to the focused selection owner.

### `docs-viewer/runtime/js/management/docs-viewer-management-modal-composition.js`

- Resolves the metadata/import/settings shell refs and composes the shared modal UI-state controller with the focused metadata and settings workflow owners.
- It connects explicit selected-document, service-read, message, and action callbacks; it does not own write execution, capability projection, or route reloads.

### `docs-viewer/runtime/js/management/docs-viewer-management-metadata-workflow.js`

- Owns metadata parent-option projection, form validation and payload shaping, explicit document-id modal opening with active-document fallback, config-time option refresh, and delegation of confirmed payloads to the action controller.
- Metadata writes and post-write index reloads remain in `docs-viewer-management-actions.js`.

### `docs-viewer/runtime/js/management/docs-viewer-management-settings-workflow.js`

- Owns settings service loading, editable-field selection, load-error projection, and the explicit field-state/change/close methods used by the action controller.
- Settings writes and post-write viewer reloads remain in `docs-viewer-management-actions.js`; service transport remains in `docs-viewer-management-client.js`.

### `docs-viewer/runtime/js/management/docs-viewer-management-scope-lifecycle-controller.js`

- Owns the five scope/sub-scope lifecycle controls, capability-based visibility/disabled projection, event wiring, lazy loading and validation of `docs-viewer-scope-lifecycle.js`, flow-option composition, error projection, and post-apply config/capability refresh or renamed-scope navigation.
- `docs-viewer-scope-lifecycle.js` remains the create/rename/delete modal, field-state, validation, preview, confirmation, apply, and result owner; endpoint transport remains in `docs-viewer-management-client.js`.
- Keep backend manifest planning/apply and future create/rename/delete flow splits outside this controller.

### `site/docs-viewer/runtime/js/shared/docs-viewer-config-controller.js`

- this controller now consumes explicit scope-config, document-index, search/recent, route-session, config-service, and route-command inputs instead of broad `state`.
- configured-scope discovery and general viewer-settings loading are separate commands over one cached browser-config envelope; viewer settings do not require a scopes array.
- the scope picker now projects custom select-menu option rows with `emoji`, scope id label, and config-backed `meta` while preserving the hidden native select as the existing value/change bridge for route workflow handoff.
- Keep this module focused on browser-safe config-envelope loading, configured-scope discovery, viewer-settings loading, route-scope resolution, scope-picker projection, route-global/root-dataset projection, UI-text merge, recent-limit/status-label projection, and management/status copy updates.
- Do not move document index loading, payload rendering, URL history primitives, generated-read capability checks, backend writes, management actions, or route shell boot into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-search-controller.js`

- search/recent route command bundling moved into this focused owner through `createDocsViewerSearchRouteCommands(...)`. The controller now consumes explicit `searchRecent`, `documentIndex`, `selectedDocument`, `routeCommands`, and `paneCommands` inputs for route application, history writes, current-doc resolution, default-doc fallback, result URL creation, loadable-doc target resolution, and pane projection requests.
- recently-added rendering remains here, while search and recent collection reads are delegated through the configured-scope provider.
- Keep this module focused on generated search-index loading, result/recent rendering, debounce handoff, search/recent route activation, more-results behavior, route command consumption, and pane command requests.
- Do not move low-level URL construction, browser history primitives, document payload rendering, config loading, management writes, or panel toolbar/view switching into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-bookmarks.js`

- bookmark route command bundling moved into this focused owner through `createDocsViewerBookmarkRouteCommands(...)`. The controller now consumes explicit bookmark, document-index, selected-document, search/recent, route-command, and search-reset command inputs for bookmark rendering and document-load handoff when opening a bookmark.
- Keep this module focused on bookmark loading, IndexedDB support fallback, list/toggle rendering, selected-document bookmark UI projection, edit state, pending focus, bookmark events, route command consumption, search-reset command consumption, and status-pill fallback callbacks.
- Do not move low-level history construction, document payload rendering, info-panel lifecycle, management writes, or future bookmark grouping/sync/export features into the app runtime coordinator.

### `site/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js`

- this controller now consumes explicit route-session, scope-config, selected-document, collection-provider, and status command inputs instead of `context.state`.
- report metadata interpretation, generated-data report reads, and local report-service handoff moved to manage-owned `docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js`; this shared controller now calls only an optional document-extras hook supplied by the entrypoint.
- Keep this module focused on document pane projection, payload rendering, loading/missing/error states, selected-document updates, and optional document-extras hook invocation.
- Do not move URL/history primitives, tree visibility projection, sidebar DOM rendering, search/recent rendering, report runtime imports, local report endpoint ownership, backend writes, or management action behavior into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-sidebar.js`

- this renderer now consumes explicit document-index, selected-document, and scope-config projections instead of `context.state`.
- Keep this module focused on tree row rendering, expand-state projection, selected-document highlighting, breadcrumb rendering, update-date display, and scope-config management text display.
- Do not move document payload rendering, route workflow, generated-data reads, bookmark storage, search/recent behavior, or management writes into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-app-shell.js`

- the app-shell owner for management action-area coordination.
- Current scope is intentionally narrow: render top-bar layout through `site/docs-viewer/runtime/js/shared/docs-viewer-top-bar-renderer.js`, render viewer toolbar controls through `site/docs-viewer/runtime/js/shared/docs-viewer-viewer-toolbar-renderer.js`, render index panel chrome through `site/docs-viewer/runtime/js/shared/docs-viewer-index-panel-renderer.js`, clear management mounts when present, call optional manage-owned shell renderers supplied by the manage entrypoint, and return the rendered surfaces before existing management/theme binding continues.
- It also renders the main-view shell through `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js` and passes the top-bar main-view toolbar slot to that renderer before existing document, sidebar, bookmark, search, and management controllers read the preserved rendered-document/search/recent IDs.
- It also renders the info panel shell through `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js`; lifecycle and metadata presentation stay in the focused info-panel host/view modules.
- It does not import management action, selected-document action, or management shell renderers. Manage-only shell rendering is injected through `docs-viewer/runtime/js/management/docs-viewer-management-shell-composition.js` during manage boot.
- The existing lazy management controller continues to own backend reachability, capability refresh, command wiring, and status projection.

### `site/docs-viewer/runtime/js/shared/docs-viewer-top-bar-renderer.js`

- the focused top-bar layout owner for the viewer-toolbar surface, main-view toolbar mount, and management-toolbar mount.
- Keep this module limited to rendering layout mounts and delegating control rendering to toolbar owners.

### `site/docs-viewer/runtime/js/shared/docs-viewer-viewer-toolbar-renderer.js`

- the focused renderer for the recently-added button, search input, and index-view toggle.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount from route context.

### `site/docs-viewer/runtime/js/shared/docs-viewer-scope-select-menu.js`

- the focused owner for custom scope select-menu option rendering, trigger projection, open/close behavior, keyboard navigation, and dispatching the preserved native select `change` event.
- Keep route navigation, browser config normalization, scope option record construction, and route-global projection in `site/docs-viewer/runtime/js/shared/docs-viewer-config-controller.js`.

### `docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js`

- the focused renderer for management toolbar markup, including the icon-only direct Import shortcut, Actions menu, capability-gated direct Publish shortcut, viewability controls, and scope picker shell.
- the scope picker shell renders the custom select-menu trigger/list plus a visually hidden native select with the preserved `docsViewerScopeSelect` id for controller/event compatibility.
- the management `Actions` menu is rendered from design-time item records that define stable DOM ids, canonical action ids, labels, optional emoji, and default visibility; direct and menu Import controls and direct and menu Publish controls share projected state and command owners outside this renderer.
- selected-document `Edit` and `Markdown source` controls moved to the rendered-document main-view toolbar; this renderer keeps broader management/admin Actions such as create, import, delete, settings, rebuild, and scope lifecycle commands.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount.

### `docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js`

- the focused renderer for management-only context menu and modal shell markup.
- Keep this module limited to preserving the existing `docsViewerContextMenu`, metadata modal, import modal, settings modal, and `docsHtmlImport*` host refs inside the management shell mount.
- Do not move metadata save behavior, import workflow behavior, settings writes, context-menu actions, backend reachability checks, generated-data reads, or management capability projection into this renderer.

### `docs-viewer/runtime/js/management/docs-viewer-management-shell-composition.js`

- the manage-owned app-shell renderer composition.
- Keep this module limited to importing management action, selected-document action, and management shell renderers and returning the renderer bundle consumed by `site/docs-viewer/runtime/js/shared/docs-viewer-app-shell.js`.
- Keep it loaded only through `docs-viewer/runtime/js/management/docs-viewer-manage.js` and manage-specific tests. Public entrypoints and public-safe shared shell code must not import it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-index-panel-renderer.js`

- the focused renderer for index panel shell chrome.
- Keep this module limited to rendering the sidebar container, toolbar controls, nav mount, and applying index-panel projection to DOM refs. Do not move tree row rendering, drag/drop behavior, search/recent behavior, or document payload rendering into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js`

- the focused renderer for main-view shell chrome, replacing the former document-shell renderer boundary.
- the shared main-view renderer is public-safe and defines the selected-document breadcrumb path, bookmark toggle, info-panel toggle, and action mount; projected control records may add a passive canonical `actionId` DOM reference without importing manage-only target policy. The app shell mounts that toolbar in the top bar, and manage-only edit/source controls are rendered by `docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js`.
- Keep this module limited to rendering `.docsViewer__main`, the main-view toolbar surface, rendered-document/search/recent result mounts, and applying the current narrow rendered/search/recent/results-status projection to DOM refs.
- Do not move Markdown rendering, generated report loading, payload fetching, breadcrumb path population, selected-document edit/source controls, bookmark storage, metadata display, or search/recent result rendering into it.

### `docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js`

- the manage-owned renderer for active/resolved-document `Edit` and `Markdown source` controls, using the passive canonical `actionId` supplied by each hosted-view control record.
- Keep this module loaded only through manage-capable shell composition; public entrypoints and public-safe shared renderers must not import it statically or duplicate its control ids/labels.
- Keep command behavior in `docs-viewer/runtime/js/management/docs-viewer-management.js` and its action/controller children.

### `docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js`

- the manage-owned document report mounting module.
- Keep this module loaded only through `docs-viewer/runtime/js/management/docs-viewer-manage.js`; public entrypoints must not import it statically or expose the report registry route-config field.
- Keep report metadata detection, report-context construction, configured-scope provider reads, report registry URL handoff, and local report-service creation here before delegating to `docs-viewer/runtime/js/reports/docs-viewer-reports.js`.
- Do not move report runtime imports or local report-service construction back into shared public-safe document rendering.

### `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-host.js`

- the focused main-view switch-intent owner.
- the host exposes main-view module context creation and a toolbar projection helper. Source-editor service details remain outside the host and are supplied only through document display mode context options.
- Keep this module limited to resolving main-view hosted-view availability, projecting active main-view state through panel layout, accepting switch requests for built-in main views, and passing generic main-view intent/toolbar/warning helpers into module contexts.
- Do not add source-editor service details, report migration behavior, arbitrary module loading, plugin behavior, or rendered-document/search/recent rendering into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-app-context.js`

- the focused app-context and route-context owner for the app shell.
- Keep this module limited to explicit app kind, route-access projection, feature-policy slot, service-availability projection, backend-capability input slot, current URL import intent, viewer pathname, and bookmark storage scope.
- Do not move route application, config loading, generated-data fetching, backend capability checks, or write behavior into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-panel-layout.js`

- the focused panel projection owner for the app shell.
- legacy sidebar local-storage migration was retired by cleanup tracker `FU-1`; this module reads and writes only the current `dotlineform-docs-viewer-index-panel:<scope>` key.
- Keep this module limited to index panel state storage/projection, current document/search/recent/results-status projection handoff, info-panel visibility/layout projection, and delegation to the view-state skeleton.
- Do not add toolbar controls, hosted-view registration, document payload rendering, search result rendering, or management action behavior to it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js`

- the focused route config resolver and route/scope projection helper.
- Keep this module limited to the durable route config shape, browser-safe route-config registry loading/resolution, explicit route-config normalization for tests/boot callers, and projection of scope config into route globals.
- inline route-config scripts and legacy `#docsViewerRoot` route data-attribute fallback were removed. Route shells must use the registry contract; focused tests must pass explicit route config or route context rather than relying on shell data as a synthetic config source.
- route-config camelCase field aliases and object-map route registries were removed. The module resolves only the `docs_viewer_route_config_v4` snake_case route record shape from a `docs_viewer_route_config_registry_v1` registry whose `routes` value is an array.
- v4 requires explicit `app_kind`, allowlisted `features`, narrow access policy, and named `generated_data`, `source`, and `management` service records; entrypoint app kind must match the selected route record.
- v4 rejects route-owned hosted-view records and the retired whole-toolbar switch. Its `view_policy` can only narrow registered view, mode, and control ids.
- Search, recently-added, and report URLs are required only when their features are enabled.
- Do not add config fetching, URL history changes, payload loading, or backend capability checks to it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-access.js`

- the focused explicit app-kind and route-access projection helper.
- Keep this module limited to `public`/`manage`/`review` app-kind normalization plus scope-query and management-UI composition policy.
- Do not add browser-side write authority, per-click permission checks, or backend reachability probing to it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-view-state.js`

- the focused index/document/info view-state skeleton.
- Keep this module pure and projection-oriented so later info-panel work can consume explicit state without reading broad route/controller state.
- Do not add DOM rendering, storage, toolbar event handling, or payload loading to it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js`

- the sole normalization, duplicate-id validation, lookup, and eligibility owner for panel views, document modes, and document controls.
- shared public-safe definitions and entrypoint contributions are combined before route narrowing; routes cannot register definitions or executable module paths.
- eligibility consumes app kind, route features, backend capability inputs, route policy, and active view/mode state.
- lifecycle loading, DOM creation, handlers, and live pressed/dirty/busy/disabled state remain outside this module.
- Do not turn it into a plugin system, arbitrary dependency loader, service caller, renderer, or mutable interaction-state owner.

### `docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js`

- the manage-owned view, document-mode, and document-control definition owner.
- This module defines index graph, semantic-token-picker, the `markdown-source` display mode, and manage document controls; its lifecycle functions lazy-load the source editor and semantic picker.
- Keep this module loaded only through `docs-viewer/runtime/js/management/docs-viewer-manage.js`; public entrypoints must not import it or the source-editor module.
- Do not move public definitions, route-policy normalization, panel state, or source-editor service implementation into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js`

- the focused renderer for info-panel shell chrome.
- Keep this module limited to rendering the info-panel container, accessible title, close control, hosted-view mount, status node, and projection attributes.
- Do not move hosted-view lifecycle, metadata rendering, source editing, panel view selection, or management actions into it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js`

- the focused lifecycle owner for info-panel hosted views.
- The host exposes `viewOptions()` only for controller-level availability checks; the info panel shell does not render an internal hosted-view toolbar.
- this host is the concrete Docs Viewer hosted-view lifecycle model: resolve/list, load, mount, update, unmount, close, dispose, and graceful absence. It should not become a general plugin platform.
- Keep this module limited to resolving/listing registered info views, loading them, mounting/updating/unmounting them in the assigned info-panel body, closing the panel, and reporting graceful absence.
- Do not add route-state mutation, URL history behavior, metadata field rendering, backend writes, or plugin discovery to it.

### `site/docs-viewer/runtime/js/shared/docs-viewer-metadata-info-view.js`

- public and manage metadata-info rendering consume selected by-id payload metadata through `docs-viewer-view-context.js`, not public tree rows or public docs `index.json`.
- Keep this module limited to rendering selected-document metadata from explicit context fields.
- Do not read broad viewer state, expose source paths, add edit controls, or call management endpoints.

### `site/docs-viewer/runtime/js/shared/docs-viewer-view-context.js`

- the focused selected-document hosted-view context projector.
- public-safe hosted views should receive explicit selected-document, app-context, payload, viewer-scope, URL, trail, and display-label inputs from this helper rather than reading broad runtime state.
- main-view module contexts add generic `mainView` helpers for active-view id, switch requests, toolbar projection, and local warnings. Document display mode contexts add `documentView` helpers. Source-editor service slots are present only when the explicit source service surface is available.
- selected metadata comes from the selected by-id payload cache; public contexts project only reader metadata while manage contexts can retain richer selected-document metadata.
- Keep this module limited to resolving the selected doc, cached payload, parent trail, app context, canonical URL, viewer scope, display labels, and generic main-view/document-view helper slots from explicit inputs.
- Future info views should extend or consume this helper
- Do not add DOM rendering, hosted-view lifecycle, URL history mutation, source-editor service implementation, or backend writes to it.

### `docs-viewer/runtime/js/management/source-editor/source-editor.js`

- the manage-only Markdown source body editor module for the `markdown-source` document display mode.
- Keep this module limited to source-body view orchestration, native wrapping textarea rendering, dirty-state projection, dirty leave confirmation, `Rebuild doc` submission, diagnostics display, rendered-payload reload handoff, and back-to-rendered switching.
- Do not add front matter editing, metadata writes, semantic-reference target picking, generated-data builder ownership, third-party editor dependencies, route URL state, or public-route source services to it.

### Docs Import And Management

- Current boundary: Docs Import is a Docs Viewer management-modal app, not a standalone route surface. `docs-viewer/runtime/js/management/docs-viewer-management-import-controller.js` lazily initializes `docs-viewer/runtime/js/import/docs-html-import.js` only from the management modal host.
- Keep modal app state, source-type partitioning, ordinary-file multi-selection, reviewed-package single selection, refreshed staging state, scope selection, service availability display, and `studio:ready` route-ready dataset projection in `docs-viewer/runtime/js/import/docs-html-import.js`.
- Keep import result rendering in `docs-viewer/runtime/js/import/docs-html-import-render.js`.
- Keep preview/write orchestration in `docs-viewer/runtime/js/import/docs-html-import-workflow.js`.
- Single-source and collection workflows signal busy and terminal-result state without changing management-modal controls directly; `docs-viewer-management-modals.js` owns disabling `Cancel` while busy, replacing `Import`/`Cancel` with `Close`, and restoring normal actions when the modal reopens.
- Keep import writes behind `docs-viewer/runtime/js/management/docs-viewer-management-client.js` and management endpoints such as `/docs/import-source`.
- Keep management-only workflows behind the lazy management boundary.
- management initialization, capability refresh, event routing, and write orchestration remain behind `docs-viewer/runtime/js/management/docs-viewer-management.js`, management child modules, and `docs-viewer/runtime/js/management/docs-viewer-management-client.js`; control/root/keyboard routing belongs to `docs-viewer-management-event-router.js`, lazy import initialization belongs to `docs-viewer-management-import-controller.js`, metadata/settings composition belongs to their focused workflow owners, and scope/sub-scope lifecycle composition belongs to `docs-viewer-management-scope-lifecycle-controller.js`; hosted-view visibility must not imply write authority.
- Keep make-viewable target resolution in `docs-viewer/runtime/js/management/docs-viewer-management-action-workflow.js`.
- Move command-specific write behavior to `docs-viewer/runtime/js/management/docs-viewer-management-actions.js` or a workflow-specific module when it gains independent state.

### Reports, Search, And Bookmarks

- Keep reports self-contained and loaded through the report allowlist.
- Keep report mounting behind the manage entrypoint until a named public-promotion slice defines a public-safe report loader, registry/data input, CSS, route config, and asset-load tests.
- Keep local source-config and broken-links endpoint access behind `docs-viewer/runtime/js/reports/docs-viewer-report-service.js`; report modules should consume `context.reportService` rather than `managementBaseUrl` or direct `window.fetch(...)`.
- Extract shared report table or pager helpers only after at least two reports need the same behavior.
- Keep search and bookmark storage/controller behavior focused; revisit if grouping, sync, export, or cross-scope behavior is added.
