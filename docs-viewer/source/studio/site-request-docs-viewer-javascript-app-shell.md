---
doc_id: site-request-docs-viewer-javascript-app-shell
title: Docs Viewer JavaScript App Shell Request
added_date: 2026-05-26
last_updated: 2026-05-27
ui_status: in-progress
parent_id: change-requests
sort_order: 14170
viewable: true
---
# Docs Viewer JavaScript App Shell Request

Status:

- in progress

- **App-shell migration foundation:** ~96% there
- **Full JavaScript App Shell Request goals:** ~75% there
- **Current priority:** finish panel toolbar/view switching before adding source editor, semantic-reference views, activity views, third-party visualization modules, or plugin-style extension work.

What is now in good shape:

- `docs-viewer.js` is now the stable compatibility entrypoint and delegates boot to `docs-viewer/runtime/js/docs-viewer-app-boot.js`.
- Shell rendering has moved into focused owners: management actions, header controls, index panel chrome, document shell chrome.
- Route context/access flags are explicit in `docs-viewer/runtime/js/docs-viewer-app-context.js`, `docs-viewer/runtime/js/docs-viewer-route-config.js`, and `docs-viewer/runtime/js/docs-viewer-access.js`.
- Route boot context has a stable source boundary: route shells carry `data-route-id` and `data-route-config-url`, while `docs-viewer/config/routes/docs-viewer-routes.json` owns browser-safe route records.
- Current panel projection has a focused compatibility owner in `docs-viewer/runtime/js/docs-viewer-panel-layout.js`, with the broader index/document/info state skeleton in `docs-viewer/runtime/js/docs-viewer-view-state.js`.
- Minimal hosted-view registration exists in `docs-viewer/runtime/js/docs-viewer-hosted-views.js`, including built-in compatibility view records and graceful absence for unavailable modules.
- The first visible info panel exists. `metadata-info` is public-safe and uses the hosted-view lifecycle/context helpers.
- Route/document workflow ownership has moved into `docs-viewer/runtime/js/docs-viewer-route-workflow.js`, with URL/query helpers, current-doc resolution, index/payload load orchestration, canonical route correction, route-link handling, and popstate coordination outside the compatibility runtime.
- Search/recent route callback bundling now belongs to `docs-viewer/runtime/js/docs-viewer-search-controller.js`, including explicit controller-owned callbacks for route application, history writes, current-doc resolution, result URLs, and default-doc fallback.
- Bookmark route callback bundling now belongs to `docs-viewer/runtime/js/docs-viewer-bookmarks.js`, including explicit controller-owned callbacks for search-debounce cancellation and document-load handoff.
- Public read-only and manage-mode separation is tested and still working.
- Management-only JS remains gated from public routes.

What is still incomplete against the broader request:

- Multi-panel architecture is still incomplete: `index/document/info` state, metadata info, and hosted-view lifecycle exist, but there is no toolbar/view-switching model or broader panel-module UI lifecycle.
- Route shells are route-context thin and no longer carry management modal/context-menu markup.
- `docs-viewer/runtime/js/docs-viewer-app-runtime.js` still owns compatibility wiring for app state, controller construction, config handoff, visibility rules, panel/info handoff, generated-data capability checks, and management-controller loading.
- Portable setup docs and proof fixture still need the cleaner “same app, two contexts” story backed by a repeatable fixture.

The remaining migration should be treated as completion work, not as optional polish.
The next slices should reduce shell and entrypoint ownership while preserving the current `/docs/`, `/library/`, and `/analysis/` behavior.

## Summary

Move Docs Viewer toward a JavaScript-owned app shell with a clear backend boundary for local editing workflows.

This request is now the current enabling slice for the panel architecture, hosted modules, manage-mode Markdown source editor, semantic-reference v2 work, and portable Docs Viewer direction.
It should be implemented before those feature requests add more runtime surface area.

This request is related to [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer), but it focuses on explaining and implementing the runtime shape rather than moving files.

The target is:

- JavaScript owns the Docs Viewer shell, routing, panels, document rendering, search UI, management UI, modals, and link behavior.
- Generated docs/search JSON and config own the read data contract.
- The Docs Viewer backend owns source writes, rebuilds, import, archive, delete, move, scope setup, source opening, and other filesystem operations.

Management mode is not treated as a removable publishing add-on in this request. Docs Viewer has two first-class uses:

- local editing and maintenance, where management mode and backend APIs are available
- public presentation, where the same viewer reads generated JSON without exposing write capabilities

Portability means those two uses can be explained, installed, and hosted cleanly from the same product boundary.

## Reason

The portable Docs Viewer direction needs a simple story.

The current architecture has made progress: Docs Viewer runtime modules, CSS, config, generated payloads, and services now sit under the `docs-viewer/` boundary. But the product story is still hard to explain because route shells, generated data, management capabilities, and backend service behavior are not described as one clean app/backend contract.

The intended model should be easier to communicate:

- The viewer app is browser JavaScript.
- The read contract is generated JSON plus config.
- Local editing uses the same viewer app with management mode enabled and a backend service available.
- Public presentation uses the same viewer app with write capabilities unavailable.
- The backend is a local capability for editing source docs, not the definition of the viewer.

This separation should make portability easier because a consuming project can understand which pieces are required for viewing, which pieces are required for editing, and which paths are project-specific.

## Goals

- define Docs Viewer as a JavaScript app with a narrow backend contract
- keep management mode as a first-class local editing workflow
- keep public presentation as the read-only generated-data workflow
- make scope setup, generated docs/search payloads, UI text, and external paths config-driven
- reduce host/Jekyll route-shell assumptions inside the viewer runtime
- make the install explanation clearer for another local project
- keep write operations behind explicit backend endpoints
- preserve current `/docs/`, `/library/`, and `/analysis/` behavior during migration

## Non-Goals

- removing management mode from portable installs
- turning Docs Viewer into only a static publishing widget
- allowing browser JavaScript to write source Markdown directly
- replacing the Python Docs Viewer backend as part of this request
- changing the generated docs payload schema in the first slice
- rewriting all Docs Viewer runtime modules in one batch
- merging Studio and Docs Viewer concepts

## Product Model

Docs Viewer should be explainable as one app with two runtime contexts.

### Local Editing Context

Local editing uses:

- Docs Viewer browser app
- generated docs/search payloads
- source scope config
- management UI
- local backend APIs for writes and rebuilds

This context powers `/docs/?mode=manage`.

It should support source editing workflows such as:

- create docs
- edit metadata
- move docs
- archive/delete docs
- import staged docs
- create or update scopes
- rebuild generated payloads
- open source files locally

### Public Presentation Context

Public presentation uses:

- Docs Viewer browser app
- generated docs/search payloads
- public viewer config
- read-only routing, search, index, document rendering, reports, bookmarks, and links

This context powers routes such as `/library/` and `/analysis/`.

It should not expose management controls or write-capable backend endpoints.

The public presentation context is not a separate product. It is the same viewer app running without local editing capabilities.

## Current Implementation Posture

This request should be treated as practical implementation work, not only as architectural background.

The aim is not to rewrite Docs Viewer in one pass.
The aim is to establish enough app-shell structure that new panel, editor, semantic-reference, and portable-viewer work can attach to a coherent browser-owned runtime instead of adding more behavior directly to existing route shells or `docs-viewer.js`.

Current priority:

- define the app/backend boundary as an implementation contract
- establish where browser-owned view state, panel state, optional modules, and generated-data reads live
- define public, manage, and manage-local access gates for views and modules
- keep direct browser reads for browser-safe generated/static repo artifacts
- reserve backend calls for source reads/writes, rebuilds, filesystem access, protected data, capability checks, and external/local workspace data
- identify the first focused owner modules that `docs-viewer.js` can orchestrate without becoming larger

This work should be completed far enough that the next feature slice can say exactly which app-shell state, config, module registration, and backend capabilities it uses.

## Optional Module Model

Docs Viewer modules should be pragmatic, not a heavy adapter framework.
For v1, a module can be a clearly identifiable folder with a small registration surface.
This is enough for repo-specific features such as the semantic Markdown source editor:

```text
docs-viewer/runtime/js/modules/source-editor/
```

Portable installs can omit that folder or disable the module in config.
When a module is absent or disabled, Docs Viewer core should simply omit the related view, panel action, or toolbar item.
The route should still boot normally.

This model keeps optional features separable without introducing the tighter boundary style used by Data Sharing adapters.
Use a more formal extension contract only if downstream portable installs actually need it.

## Target Architecture

```text
Docs Viewer JavaScript app
  - boot/runtime config
  - route and query-state handling
  - scope selection
  - index/sidebar/panel rendering
  - document payload loading and rendering
  - inline search and generated report loading
  - management UI and modals when management is enabled
  - backend client for management workflows

Generated data and config
  - docs indexes
  - per-doc payloads
  - search indexes
  - scope config
  - UI text
  - capability flags and route settings

Docs Viewer backend
  - source Markdown writes
  - source config writes
  - import/archive/delete/move/apply workflows
  - generated docs/search rebuilds
  - source opening
  - filesystem allowlists, backups, and validation
```

In this model, a route shell should mainly provide a mount point and route context. The Docs Viewer JavaScript app should render the viewer shell from config and generated data.

## Backend Boundary

The backend remains necessary for local editing.

The backend should own:

- source file mutation
- source config mutation
- import staging and apply workflows
- move/archive/delete workflows
- generated payload rebuilds
- backups and recovery points
- filesystem allowlists
- local source-file opening
- structured validation and error shaping

The browser should only call named Docs Viewer backend endpoints. It should not send arbitrary filesystem paths, shell commands, or direct write instructions.

The backend can remain Python. A future Node backend would still be a backend and would still need the same safety boundary. The important architecture decision is frontend/backend separation, not backend language.

## Third-Party Frontend Module Boundary

The JavaScript app-shell direction is compatible with third-party browser libraries.
Libraries such as D3.js, Cytoscape.js, charting packages, graph viewers, or other visualization/runtime components belong on the browser app side when they render interactive UI.

The app shell should support these libraries through panel or view modules rather than by adding them to the base route shell.
Heavy or specialized dependencies should be lazy-loaded only when the user opens the view that needs them.
This is a capability direction, not a current portable install promise.
Portable Docs Viewer should not ship third-party visualization libraries or user-facing config for them until an integration contract exists.
For portable installs, the host project should provide the module, data, and configuration unless Docs Viewer later defines a document-derived data class for these modules.

Third-party frontend modules should:

- mount inside an assigned app shell container, such as a panel body or document/report host
- consume generated data, config, and backend responses through explicit app APIs
- clean up DOM nodes, event listeners, timers, animation frames, observers, and library instances on unmount
- keep CSS and DOM mutations scoped to the module host
- avoid increasing the base viewer boot cost for routes that never use the module
- declare whether they are public, manage-only, or local manage-only
- be capability-gated in the same way as first-party views and actions

The backend or generator may provide data artifacts for these modules, such as:

- graph JSON
- host-specific relationship indexes
- report datasets
- validation or health-check results
- local operational diagnostics for manage mode
- precomputed metrics or layout hints

The backend should not own browser rendering logic or library-specific DOM behavior.
It should not accept arbitrary library commands, filesystem paths, or direct write instructions.
It should continue to expose named Docs Viewer endpoints and generated artifacts with explicit schemas.

Manage mode can be used to incubate new third-party or dependency-heavy modules before they are exposed in public presentation.
A module should move to public routes only after its generated/public-safe data contract, performance cost, accessibility behavior, visual design, and portable-install expectations are clear.
Dotlineform semantic-link modules are repo-specific Studio integrations and should not be treated as portable Docs Viewer core.

## Config Boundary

Config should describe installation-specific and mode-specific behavior.

Candidate config responsibilities:

- available scopes
- default scope
- generated docs index paths
- generated search index paths
- management-enabled routes
- public read-only routes
- UI text
- backend base URL for local editing
- feature flags for import, scope lifecycle, source opening, reports, or bookmarks
- feature flags and access metadata for optional panel/view modules
- module asset or import metadata when a view depends on optional third-party browser libraries
- enabled optional module ids where an install includes repo-specific or host-specific modules

The viewer app should consume this config directly. Route shells should not hardcode scope lists, management capability rules, or generated payload paths where those can be represented as config.

## Benefits

- clearer portable story: "browser app plus generated data, with backend APIs for local editing"
- management mode remains central to local editing rather than treated as an optional extra
- public routes stay read-only without becoming a separate viewer implementation
- host projects get a smaller integration surface
- route shells can become thinner and less Jekyll-specific
- management backend safety stays explicit
- generated JSON remains the stable read contract
- the same pattern can later inform Studio's JavaScript app-shell direction

## Risks

- moving shell ownership into JavaScript increases reliance on browser boot behavior
- management code could leak into public presentation if capability checks are weak
- generated config shape could become too broad if it tries to model every local detail
- route migration could temporarily duplicate Jekyll include logic and JS shell logic
- public and management contexts could drift if they are tested separately but not as one app
- third-party frontend libraries could add boot cost, CSS leakage, or lifecycle leaks if they bypass the app shell module boundary
- experimental visualization modules could be promoted to public presentation before their data and dependency contracts are stable

Mitigations:

- keep public and management contexts in one runtime contract
- lazy-load management-only modules only when management is enabled
- lazy-load optional third-party frontend libraries only when their view is selected
- require panel/view modules to mount, update, unmount, and dispose inside app-owned containers
- incubate uncertain third-party or data-visualization modules in manage mode before promoting them to public routes
- keep backend capability checks server-side as well as client-side
- migrate one shell responsibility at a time
- add smoke coverage for both `/docs/?mode=manage` and public read-only routes

## Proposed Approach

1. Make the app/backend contract executable.
   Define which behavior belongs to the browser app, generated data/config, and backend service, then apply that split to the first implementation slice.

2. Introduce the minimum app-shell owner modules needed now.
   Candidate first owners are route boot/config normalization, access capability projection, panel/view registration, optional module registration, and generated-data read helpers.

3. Make the route shell thinner where a concrete slice needs it.
   Keep route pages responsible for mount/context only. Move viewer shell composition into JavaScript where practical.

4. Make management capabilities explicit config plus backend capabilities.
   The browser can hide controls from config, but backend endpoints must still enforce write capability.

5. Preserve generated docs/search JSON as the read contract.
   Do not change payload shape just to move shell ownership.

6. Prove the pattern on the management route and one public route.
   `/docs/?mode=manage` and one public route such as `/library/` should both boot from the same app-shell model.

7. Update the portable setup docs after the runtime shape is proven.
   The install explanation should describe local editing and public presentation as two contexts of the same Docs Viewer app.

## Current Enabling Slice

The current implementation slice should avoid a broad rewrite while still doing enough to unblock future feature work.

Required slice:

- define or identify a small Docs Viewer app boot/orchestration module
- define a route context/config normalization shape used by both `/docs/?mode=manage` and public routes
- define public, manage, and manage-local access flags for views, actions, and optional modules
- define the minimal optional-module registration shape, including graceful absence when a repo-specific module is not present
- inventory the read surfaces needed by near-term panel and editor work as browser-safe generated/static reads versus backend reads
- identify the first focused `docs-viewer.js` responsibilities to hand to owner modules
- keep the existing generated JSON paths and backend endpoints
- keep `/docs/`, `/library/`, and `/analysis/` URLs unchanged
- verify management controls still appear only when management is enabled
- verify public routes do not load management-only modules

Optional first visible shell move:

- moved the management action area from `_includes/docs_viewer_shell.html` into `docs-viewer/runtime/js/docs-viewer-app-shell.js` and the focused `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`.
  `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` now provide only a management action mount for this area, while `docs-viewer/runtime/js/docs-viewer.js` remains the loaded compatibility entrypoint.
- moved the header controls from the shared and standalone shell templates into `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, coordinated by `docs-viewer/runtime/js/docs-viewer-app-shell.js`.
- moved the index panel shell chrome from the shared and standalone shell templates into `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, coordinated by `docs-viewer/runtime/js/docs-viewer-app-shell.js`.
  The templates now provide only `#docsViewerIndexPanelMount` for this area; `docs-viewer/runtime/js/docs-viewer-sidebar.js` remains the tree renderer inside the preserved `#docsViewerNav` body, and the existing index-panel state helper remains the storage/projection source.
- moved the document mount and read-only metadata shell from the shared and standalone shell templates into `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`, coordinated by `docs-viewer/runtime/js/docs-viewer-app-shell.js`.
  The templates now provide only `#docsViewerDocumentShellMount` for this area; the renderer preserves existing document, metadata, status-pill, bookmark, search/recent result, and more-result IDs. `docs-viewer/runtime/js/docs-viewer-sidebar.js` still renders breadcrumbs/read-only metadata, and `docs-viewer/runtime/js/docs-viewer-document-controller.js` still owns payload loading, Markdown/report mounting, search/recent pane switching, missing-doc, and error rendering.
- added `docs-viewer/runtime/js/docs-viewer-app-context.js` and `docs-viewer/runtime/js/docs-viewer-panel-layout.js` as the fifth app-shell slice.
  `docs-viewer-app-context.js` normalizes the existing `#docsViewerRoot` data attributes into route context and public/manage access flags.
  `docs-viewer-panel-layout.js` owns the current compatibility projection handoff for index panel state plus document/search/recent/results-status visibility.
  `docs-viewer/runtime/js/docs-viewer.js` still owns route boot orchestration, config loading, payload loading, search/recent rendering handoff, bookmark behavior, and management controller loading.
- added the route config and view foundation slice.
  `docs-viewer/runtime/js/docs-viewer-route-config.js` defines the route config shape and route/scope projection API while retaining current route data attributes as migration input.
  `docs-viewer/runtime/js/docs-viewer-access.js` defines static public/manage/manage-local access projection without moving backend capability checks out of the lazy management flow.
  `docs-viewer/runtime/js/docs-viewer-view-state.js` defines the index/document/info panel state skeleton, and `docs-viewer/runtime/js/docs-viewer-panel-layout.js` now projects that skeleton through today's two-panel behavior.
  `docs-viewer/runtime/js/docs-viewer-hosted-views.js` defines the minimal hosted-view record and lifecycle shape plus graceful absence for missing, disabled, or access-blocked modules.
  The specific info panel, panel toolbar UI, source editor, semantic-reference views, and third-party visualization modules remain deferred.
- added the first visible info-panel metadata view slice.
  `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js` renders the info panel shell and projection, `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` owns hosted-view lifecycle and graceful absence, and `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` renders public-safe selected-document metadata.
  `metadata-info` is now the built-in public info hosted view.
  The source editor, editable metadata saves, semantic-reference views, activity views, panel-toolbar generalization, third-party visualization modules, and plugin architecture remain deferred.
- added the route config handoff slice.
  Shared and standalone Docs Viewer shells now carry only `data-route-id` and `data-route-config-url` for boot route context.
  `docs-viewer/config/routes/docs-viewer-routes.json` owns the browser-safe route records, and `docs-viewer/runtime/js/docs-viewer-route-config.js` resolves that registry before the legacy inline/data-attribute fallback.
  `docs-viewer/runtime/js/docs-viewer-app-context.js` continues to expose the same route-context contract to downstream controllers.
  The local Docs Viewer service serves the same registry path with loopback management/generated-read URLs injected from service config.
- added the management shell extraction slice.
  Shared and standalone Docs Viewer shells now provide only `#docsViewerManagementShellMount` for the management-only context menu, metadata modal, import modal, settings modal, and import host refs.
  `docs-viewer/runtime/js/docs-viewer-app-shell.js` dynamically imports `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` only when `routeContext.access.canLoadManagementUi` allows management UI, and the existing management controller still owns write workflows, capability checks, and modal/action behavior.
- added the app boot ownership slice.
  `docs-viewer/runtime/js/docs-viewer.js` is now a stable import-and-start wrapper.
  `docs-viewer/runtime/js/docs-viewer-app-boot.js` owns root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, app-shell ref handoff, theme-toggle loading, single-start guarding, and runtime startup.
  `docs-viewer/runtime/js/docs-viewer-app-runtime.js` is the compatibility owner for the current route/document workflow until the next extraction slice.
  Existing `applyCurrentRoute`, `loadIndex`, `loadDoc`, URL/history behavior, search/recent handoff, bookmark orchestration, generated-data reads, reports, lazy management loading, and management import-open-on-load behavior remain preserved there.

The slice is successful when the panel architecture and semantic editor can be implemented against named app-shell owners, access gates, module registration, read contracts, and backend capabilities without adding unrelated responsibility to `docs-viewer.js`.

## Next Infrastructure Slices

The route config, access projection, panel/view-state skeleton, hosted-view lifecycle, and first metadata info view are complete.
The remaining work should finish the migration rather than start feature layers.

Recommended completion sequence:

1. Management shell extraction.
   Move management context-menu, metadata modal, import modal, settings modal, and any remaining management-only shell markup out of `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`.
   Target owner: a focused app-shell management shell renderer or modal-shell module, with the existing management controller still owning writes, capability checks, and workflow behavior.
   Acceptance: public routes still do not load management CSS/JS; local `/docs/?mode=manage` still renders metadata edit, import, settings, context actions, and management action gating; route shells keep only app mounts, route id/config URL, CSS links, and the entry script.
   Task tracker: [Docs Viewer App Shell Management Shell Extraction Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-management-shell-extraction-tasks).
   Implemented 2026-05-27: the route shells now provide the management shell mount only, and the app shell renders the preserved management refs through `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` only for management-capable route access.

2. App boot ownership.
   Extract the remaining boot/state/controller setup out of `docs-viewer.js` into a focused app boot owner while keeping `docs-viewer.js` as the stable compatibility entrypoint loaded by route shells.
   Target owner: `docs-viewer/runtime/js/docs-viewer-app-boot.js` or an equivalent app-runtime module.
   Acceptance: route-config resolution, app-shell initialization, controller construction, initial config/index/payload load, and initial management import open are readable as one boot workflow outside the entrypoint; `docs-viewer.js` becomes a small import-and-start wrapper.
   Task tracker: [Docs Viewer App Shell App Boot Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-app-boot-tasks).
   Implemented 2026-05-27: `docs-viewer/runtime/js/docs-viewer-app-boot.js` owns the boot workflow and starts `docs-viewer/runtime/js/docs-viewer-app-runtime.js`; the entrypoint is now a small wrapper.

3. Route/document workflow ownership.
   Move route application, current-doc resolution, document payload loading, missing-doc/error behavior, and history synchronization out of the compatibility runtime into a focused route/document workflow owner that builds on `docs-viewer-router.js` and `docs-viewer-document-controller.js`.
   Acceptance: `docs-viewer/runtime/js/docs-viewer-app-runtime.js` no longer owns `applyCurrentRoute`, `loadIndex`, `loadDoc`, URL canonicalization, or route-driven document/search/recent switching; `/docs/`, `/library/`, and `/analysis/` URL behavior remains unchanged.
   Task tracker: [Docs Viewer App Shell Route Document Workflow Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-route-document-workflow-tasks).
   Implemented 2026-05-27: `docs-viewer/runtime/js/docs-viewer-route-workflow.js` owns URL/query helpers, current-doc resolution, route application, index and payload loading, missing/error handoff, route-link handling, and popstate coordination. The compatibility runtime now wires explicit callbacks to search/recent, bookmarks, document rendering, management delegation, and panel/info updates.

4. Search/recent/bookmark orchestration cleanup.
   Finish the extraction around search/recent and bookmark orchestration so the app boot owner wires controllers but does not own their UI state transitions.
   Target owners: the existing search controller and bookmark modules unless a small app-level coordination helper is needed.
   Acceptance: inline search, recent results, more-results behavior, bookmark toggle/list behavior, and route history behavior are covered by focused module or route smokes without broad entrypoint state assertions.
   Task tracker: [Docs Viewer App Shell Search Recent Bookmark Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-search-recent-bookmark-tasks).

5. Panel toolbar and hosted-view completion.
   Add the minimal panel toolbar/view-switching contract only after the boot and route workflow are no longer centered in `docs-viewer.js`.
   This slice should generalize from the existing `metadata-info` view without adding source editing, semantic references, activity views, third-party visualization modules, or plugin architecture.
   Acceptance: hosted views can be switched, disabled, and access-gated through route config/view records; the metadata view remains public-safe; future source/editor views have a clear place to attach.

6. Portable fixture proof.
   Add or update a repeatable public fixture that proves the route-config registry, shell mounts, runtime assets, generated docs/search payloads, UI text, and public read-only behavior can work outside dotlineform incidental routes.
   A local manage fixture can follow, but the first proof should lock down the read-only app contract.
   Acceptance: the fixture uses the same app/runtime/config shape as dotlineform and has a small smoke check for route boot, document selection, search/recent, info panel, and absence of management-only assets.

## Shell Migration Sequence

All current shell responsibilities should eventually move into the JavaScript app shell.
The sequence matters because the first moves should prove the app-shell contract without taking unnecessary public-route risk.

Recommended order:

1. Management action area.
   Move the manage-mode action row and related capability-gated controls out of `_includes/docs_viewer_shell.html` first.
   This is the safest useful first move because it is manage-mode only, already depends on explicit capabilities, and currently has duplicated Liquid markup across search/scope branches.
   It should prove that route shells can provide a mount/context while JavaScript renders access-gated controls.
   Implemented 2026-05-27: the app shell imports the management action renderer only when route intent allows management, renders the existing management action ids into a route-provided mount, and leaves backend reachability/capability updates with the existing lazy management controller.

2. Scope picker and header controls.
   Move scope selection, recent/search control composition, and related route-context controls after the management action area.
   This proves config-driven route context and reduces route-shell assumptions without touching document rendering first.
   Implemented 2026-05-27: the shared and standalone shell templates now provide `#docsViewerHeaderControlsMount`; `docs-viewer/runtime/js/docs-viewer-app-shell.js` delegates to `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js` to render the preserved scope, recent, search, and management-action mount IDs before the existing runtime controllers read them.

3. Index panel shell.
   Move the sidebar/index panel container, toolbar, and panel-state projection into JavaScript after the first app-shell control slices are stable.
   This should align with the multi-panel work so index/document/info panel ownership does not split across Liquid and JavaScript.
   Implemented 2026-05-27: the shared and standalone shell templates now provide `#docsViewerIndexPanelMount`; `docs-viewer/runtime/js/docs-viewer-app-shell.js` delegates to `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js` to render the preserved sidebar toggle, expand button, and nav IDs before the existing runtime controllers read them. The slice deliberately keeps tree row rendering in `docs-viewer/runtime/js/docs-viewer-sidebar.js` and keeps state transitions/storage in the current index-panel helper until a broader panel-layout owner is introduced.

4. Document mount and metadata shell.
   Move document host, metadata host, results host, and document/status projection later, after app boot, route context, access gates, and panel ownership are proven.
   This has the highest public-reading blast radius and should not be the first proof of the app-shell migration.
   Implemented 2026-05-27: the shared and standalone shell templates now provide `#docsViewerDocumentShellMount`; `docs-viewer/runtime/js/docs-viewer-app-shell.js` delegates to `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js` to render the preserved document/meta/search-result IDs before existing runtime controllers read them. The slice adds only a narrow document/search/recent/results-status projection helper and deliberately defers info-panel or hosted-view architecture.

5. Route context and compatibility panel projection.
   Move route dataset normalization, public/manage access flags, shell ref collection, and the current index/document/search/recent projection handoffs into focused app-shell child modules.
   Implemented 2026-05-27: `docs-viewer/runtime/js/docs-viewer-app-context.js` owns route context normalization and access flags, `docs-viewer/runtime/js/docs-viewer-panel-layout.js` owns the compatibility panel projection handoff, and `docs-viewer/runtime/js/docs-viewer.js` consumes those owners while preserving route loading, generated-data reads, search/recent rendering, bookmark storage, report mounting, and management workflows.
   This deliberately does not introduce the full info-panel, panel-toolbar, hosted-view, or optional-module lifecycle architecture.

This order does not imply that later responsibilities are less important.
It only sequences the migration so each slice reduces shell ownership while preserving `/docs/`, `/library/`, and `/analysis/` behavior.

## Boot Module Decision

Create a new JavaScript app-shell module:

```text
docs-viewer/runtime/js/docs-viewer-app-shell.js
```

This module should coordinate shell rendering, route-context normalization, access/capability projection, and future panel/module ownership.

Keep `docs-viewer/runtime/js/docs-viewer.js` as the stable script loaded by `_includes/docs_viewer_shell.html` during the migration.
It should become a compatibility entrypoint that delegates to `docs-viewer-app-shell.js` and focused owner modules.
New shell-rendering responsibilities should go into `docs-viewer-app-shell.js` or child modules, not into `docs-viewer.js`.

This avoids a disruptive script/include change while stopping `docs-viewer.js` from becoming the long-term app-shell owner.
Each implementation slice should either move responsibility out of `docs-viewer.js` or keep it as orchestration only.

## Route Context Decision

Use a browser-safe route config record as the route/app handoff.
The current route shells carry only a route id and route-config URL for boot route context.
Inline route records and legacy data attributes remain only as resolver fallback compatibility, not as the normal shell contract.

The `docs_viewer_route_config_v1` schema is stored in `docs-viewer/config/routes/docs-viewer-routes.json` for `/docs/`, `/library/`, `/analysis/`, and future Docs Viewer installs.
The app shell should resolve the current route to a route config record, then use that record to determine:

- route id and route type
- default scope and default doc
- whether scope query is allowed
- viewer base URL and generated data paths
- public, manage, and manage-local capability defaults
- route-level feature flags
- panel defaults
- optional module availability
- UI/config asset paths

The route shell should move toward a minimal mount and script include.
If path inference is not enough during migration, the shell may pass only a stable route id as bootstrap compatibility.

This creates a durable route/app boundary before panel, editor, hosted-module, and portable-viewer features depend on it.
It also keeps route behavior validateable as data instead of spreading route context through Liquid branches or page-local markup.

## Capability Decision

Use route config and backend capability responses narrowly.
Neither should become a speculative permission framework.

Route config should contain static route intent that the current repo actually needs, such as route type, default scope/doc, generated data paths, route-level feature flags, panel defaults, and optional module availability.
Do not add route-config fields only because a hypothetical portable install might one day need them.

The backend capability response should start with the smallest useful check:

- local Docs Viewer backend reachable

Additional backend capability fields should be added only when a current repo requirement proves they are needed.
Each added field should answer a concrete runtime question that route config cannot answer safely.
For example, do not add a separate import capability unless this repo intentionally supports a mode where the backend is reachable and the scope is manageable but import must be disabled.

Client behavior should be:

- use the browser-safe route config record for static route/app decisions
- check backend reachability when entering manage mode
- cache the result in app state
- do not perform per-click capability checks before ordinary UI decisions
- let backend endpoints validate actual write/import/rebuild/archive/delete requests
- add narrower capability fields only if repeated unexpected errors show that reachability plus endpoint validation is not enough

Public or portable read-only installs may need no backend capability response at all.
Portable manage-mode installs should not inherit repo-specific capability checks unless the portable implementation actually needs them.

## Portability Fixture Relationship

The app-shell boundary improves the portable Docs Viewer story, but it is not strictly required for portability.
Docs Viewer is already technically portable with enough manual setup.
The missing proof is a repeatable fixture that demonstrates the intended install contract without relying on dotlineform's incidental routes, data, or local setup.

The fixture definition belongs in [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer).
That request should define two proof levels:

- a portable public fixture for the read-only generated-data app
- a later portable local manage fixture for local source writes, rebuilds, and private/local generated outputs

App-shell work should consume those fixture expectations, not redefine portability as a prerequisite for the app-shell migration.

## Hosted View Module Direction

Use a modular hosted-view architecture, not a plugin architecture.

The current repo comes first.
Panels should host named view modules that can be tightly integrated with repo data, generated artifacts, local helper code, and the local Docs Viewer backend where manage mode needs it.
Third-party data-visualization libraries such as D3.js or Cytoscape.js are conceptually in scope only because panel modules should not prevent them.
Docs Viewer is not promising to make those libraries easy to integrate, and portable Docs Viewer should not distribute them by default.

For this repo now:

- panels host named view modules
- view modules are ordinary repo JavaScript modules
- modules receive explicit app context, such as selected doc, scope, route mode, generated data readers, backend client when available, and view config
- modules may call repo-local helper code directly where that is the pragmatic integration path
- modules may manually import third-party libraries when this repo needs them
- modules own their UI, data shaping, third-party imports, and tight integration logic
- modules are not sandboxed, independently installable, or expected to run in arbitrary host projects

For future portability:

- keep modules in clear folders
- keep registration explicit
- control module availability through generated route/config data
- make absence graceful: if a module folder or config entry is missing, omit the related view/action rather than failing route boot
- avoid hardcoded dotlineform assumptions in the core panel host
- keep dotlineform-only behavior in dotlineform-specific modules

For a possible future plugin architecture:

- do not design it now
- do not add adapter layers, package manifests, sandbox protocols, marketplace assumptions, or generic data APIs
- avoid choices that would make a plugin system difficult later, such as global DOM mutations, untracked lifecycle cleanup, hidden dependencies on one route, or core code directly importing every optional module

The practical contract is:

- core Docs Viewer owns panel regions, view selection, lifecycle, access gating, and explicit module registration
- repo-specific modules own their UI, data exchange, data shaping, third-party imports, and integration logic

## Verification

Focused checks for implementation slices should include:

```bash
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py
$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py
$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py
node --check docs-viewer/runtime/js/docs-viewer.js
```

Browser smoke expectations:

- `/docs/?mode=manage` boots the Docs Viewer app and exposes management controls
- public read-only routes boot the same viewer app without management controls
- management-only modules are not loaded on public routes
- generated docs/search payloads remain the read contract
- write workflows still call backend endpoints and cannot be performed by static browser JS alone
