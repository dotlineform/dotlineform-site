---
doc_id: docs-viewer-overview
title: Overview
added_date: 2026-04-24
last_updated: 2026-07-12
ui_status: urgent
summary: Current Docs Viewer route-shell, shared runtime, controller lifecycle, URL, and generated-read overview, with links to focused architecture owners.
parent_id: docs-viewer
---
# Docs Viewer Overview

## Purpose

The Docs Viewer is a shared documentation reader used by the site's docs-domain scopes.
It provides:

- a left-hand tree navigation loaded from generated `index-tree.json` payloads
- a right-hand document pane for rendered doc content
- inline docs search within the same viewer shell
- a shared recently-added list beside inline docs search

Current live scopes:

- Studio docs at `/docs/` through the standalone Docs Viewer service
- validated returned-package review at `/docs-review/` when the independent review capability is enabled
- Library docs at `/library/`
- Analysis docs at `/analysis/`
- Moments docs at `/moments/`

Catalogue pages do not use the Docs Viewer.

This page is a system overview, not a row-level module inventory. Use [Runtime](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) for the durable public/manage/review boundary, [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) for the returned-package workflow, and [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) for current owners.

## Shared Module Model

The current implementation is split into three layers.
Use [Docs Viewer Static Route Template](/docs/?scope=studio&doc=docs-viewer-static-route-template) for the public/manage route shell ownership, stable mount points, and runtime entrypoint boundaries.

### 1. Scope-owned route shells and service shell

Public route pages identify the active Docs Viewer route through `data-route-id` or the current path and locate the browser-safe route-config registry through `data-route-config-url`.
The local `/docs/` management route and `/docs-review/` returned-package route are served by the standalone Docs Viewer service from separate static route shells.

The registry defines scope-specific values such as:

- the docs index URL
- the search index URL
- the base route
- the default root doc
- whether the scope parameter is part of the canonical URL

Current public route shells:

- `site/library/index.html`
- `site/analysis/index.html`

New public route shells are created from:

- `docs-viewer/templates/public-route/index.html`

Current management service shell:

- `docs-viewer/shell/docs-viewer-manage.html`

Current review service shell:

- `docs-viewer/shell/docs-viewer-review.html`

### 2. Shared shell contract

Public route shells and the management service shell expose the stable mount points that the app shell fills before the runtime binds route behavior.
The public route shell template renders:

- the sidebar nav container
- the main content pane
- the optional inline search input
- main-view toolbar breadcrumbs and document controls

The management service shell renders the same app-owned mount contract plus management-only mounts and local-service context when enabled.

### 3. Public, Manage, And Review Entrypoints

The viewer behavior starts from route-specific entrypoints:

- `site/docs-viewer/runtime/js/public/docs-viewer-public.js` for public read-only routes
- `docs-viewer/runtime/js/management/docs-viewer-manage.js` for the local `/docs/` management shell
- `docs-viewer/runtime/js/review/docs-viewer-review.js` for the local `/docs-review/` returned-package shell

The entry modules delegate boot to `site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js`, which resolves route config, initializes the app shell, and starts the private app runtime coordinator.
The private app runtime coordinator delegates app composition and startup sequencing to `site/docs-viewer/runtime/js/shared/docs-viewer-app-composition.js`, then wires focused controllers through explicit domain/command inputs where available and the runtime-internal broad state object for controller families that have not yet been narrowed.
The lazy management controller family receives explicit document-index, selected-document, search/recent, route-session, scope-config, and management domains and does not reconstruct a cross-domain state facade. Generated-read capability state remains owned only by `docs-viewer-generated-data-runtime.js`.
Current helper modules:

- `site/docs-viewer/runtime/js/shared/docs-viewer-app-composition.js` owns runtime defaults, foundational owner construction, feature-filtered hosted-view registration, startup authority records, and feature-aware startup sequencing
- `site/docs-viewer/runtime/js/shared/docs-viewer-route-features.js` owns allowlisted route-feature normalization, dependency checks, queries, and code-record filtering
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-session.js` owns app-session creation, state defaults, single-owner named state-domain facades, and public/manage route-session projection
- `site/docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js` owns main-view/display-mode/info host construction, active view/mode/control projection, info defaults, and document/search/recent view transitions
- `site/docs-viewer/runtime/js/shared/docs-viewer-status-controller.js` owns viewer status/error display and nested busy-state projection
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js` owns remaining private runtime wiring for focused controllers, config handoff, event handlers, private management/startup callbacks, and the intentionally small returned app handle: `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`
- `site/docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js` owns route/document workflow orchestration: URL/query helpers, current-doc resolution, route application, index and payload loading, canonical route correction, route-link handling, and popstate coordination
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-context.js` owns explicit `public`/`manage`/`review` app kind, route context, preserved route-query identity, feature-policy slot, service-availability projection, and the backend-capability input slot
- `site/docs-viewer/runtime/js/shared/docs-viewer-access.js` owns scope-query and management-UI route access plus hosted-view/mode access checks
- `site/docs-viewer/runtime/js/shared/docs-viewer-service-context.js` owns independent `generatedData`, `source`, `management`, and browser-safe `config` service surfaces
- `site/docs-viewer/runtime/js/shared/docs-viewer-configured-scope-provider.js` owns feature-facing collection reads for index, document, search, recently added, references, and explicitly supplied source methods
- `docs-viewer/runtime/js/review/docs-viewer-returned-package-provider.js` owns package-selected index, document, source, manifest, inventory, and build reads/writes through the focused review service
- `docs-viewer/runtime/js/management/docs-viewer-management-source-adapter.js` is the manage-entrypoint-owned optional source endpoint adapter; backend capabilities still authorize operations
- `site/docs-viewer/runtime/js/shared/docs-viewer-generated-data-runtime.js` owns generated-data transport option shaping, generated-read capability caching, retry/reload options, generated-search read capability checks, payload normalization, and static/local reads behind the provider
- `site/docs-viewer/runtime/js/shared/docs-viewer-config-service.js` owns browser-safe Docs Viewer config and UI-text fetch/retry behavior
- `site/docs-viewer/runtime/js/shared/docs-viewer-config-controller.js` exposes configured-scope discovery and general viewer-settings loading as separate operations over the shared config envelope
- `site/docs-viewer/runtime/js/shared/docs-viewer-asset-url.js` owns asset-version URL projection for static browser assets
- `site/docs-viewer/runtime/js/shared/docs-viewer-data.js` owns low-level JSON fetch/retry primitives only behind the generated-data runtime and config service
- `docs-viewer/runtime/js/reports/docs-viewer-report-service.js` owns local report endpoint access for source-config and broken-links audit reports in management-capable contexts
- `site/docs-viewer/runtime/js/shared/docs-viewer-document-index-state.js` owns document visibility/loadability projection for public and manage contexts, including non-viewable/manage-only filtering, non-loadable fallbacks, default-doc resolution, and index status projection
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js` owns selected-document info-panel coordination, toggle projection, outside-context view selection, close behavior, and update-on-document-change behavior
- `site/docs-viewer/runtime/js/shared/docs-viewer-runtime-lazy-controller.js` owns neutral lazy-controller loading; the private app runtime coordinator uses it to keep the management controller import gated behind management route access
- `site/docs-viewer/runtime/js/shared/docs-viewer-router.js` owns low-level URL, route parsing, history, requested-doc resolution, and route/payload helper functions used by the workflow owner
- `site/docs-viewer/runtime/js/shared/docs-viewer-tree.js` owns pure document sorting, children-map construction, visibility checks, and doc-id set normalization
- `site/docs-viewer/runtime/js/shared/docs-viewer-search.js` owns pure search-entry normalization, scoring, matching, result ordering, and recently-added document ordering
- `site/docs-viewer/runtime/js/shared/docs-viewer-search-controller.js` owns inline-search and recently-added controller behavior, including generated search-index loading, result/recent rendering, debounce and more-results behavior, explicit route command consumption, and pane command requests from search/recent state-domain inputs
- `site/docs-viewer/runtime/js/shared/docs-viewer-bookmarks.js` owns bookmark storage, bookmark row/toggle rendering, selected-document bookmark projection, explicit document-load route command consumption, and search-reset command consumption when opening a bookmark
- `site/docs-viewer/runtime/js/shared/docs-viewer-favourites.js` owns bookmark record normalization, ordering, key generation, and IndexedDB persistence helpers
- `site/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js` owns document pane visibility, payload rendering, loading/missing/error states, collection-provider report handoff, and report mount context
- `site/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js` owns code-defined view, document-mode, and document-control normalization, lookup, eligibility, and active control projection
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js` owns info hosted-view option projection, lifecycle, switching, close behavior, update handoff, and graceful absence
- `docs-viewer/runtime/js/reports/docs-viewer-reports.js` owns report lookup and access checks
- `docs-viewer/runtime/js/reports/docs-index-table-report.js` owns the reusable docs-index table report
- Docs Import is a management-modal app: `docs-html-import.js` owns the import host, source-family dispatch, and route-ready projection; `docs-html-import-workflow.js` owns ordinary single-source preview/write orchestration; `docs-import-collection-controller.js` and `docs-import-collection-view.js` own collection preview/decision state and its body-free rendering; import writes stay behind management endpoints through `docs-viewer-management-client.js`

This runtime is shared across the current docs scopes.
It reads the shell configuration, loads the generated JSON for the active scope, coordinates tree navigation, loads document payloads, and delegates document/search pane rendering to focused controllers.

When route config supplies a local `services.generated_data.base_url` and that server advertises generated-data read capability, the runtime reads the active scope index, document payloads, docs-search index, and generated reference JSON through that server.
Local Studio uses this path because generated docs/search reads are served by the Python app. The generated-data URL is projected independently of source and management service URLs.
Public route records contain blank local service surfaces, so `/library/`, `/analysis/`, and `/moments/` use generated JSON asset URLs directly without backend probes.
The returned app handle is not a feature-module escape hatch: it does not expose broad app/session state, composition/session internals, management service handles, backend capability probes, the management lazy loader, or route workflow bridge methods.
Management reload and selected-document refresh still use private callbacks inside the app runtime coordinator and management controller context.

## Controller And View Lifecycle

The Docs Viewer lifecycle is intentionally small:

- app composition creates foundational owners, records startup authority, and sequences startup phases
- route-lifetime controllers use `initialize` only for startup work such as bookmark loading or management capability checks
- route-lifetime controllers use `bind` to attach event listeners for their owned DOM/window surface
- controller `update` or `project` methods refresh visible state after route, selected-document, panel, search, bookmark, or capability changes
- hosted info views use `load`, `mount`, `update`, `unmount`, `close`, and optional `dispose` through `docs-viewer-info-panel-host.js`

Public-safe hosted views receive explicit selected-document, route/access, payload, viewer-scope, URL, trail, and display-label inputs from `docs-viewer-view-context.js`.
They must mount without management services, backend probes, local generated-read service base URLs, write-capable handles, or management assets.
Manage-only hosted views may receive explicit management service or capability inputs, but registration and visibility do not imply write authority.
Writes remain behind the management backend endpoints and server-side validation.

Current event binding is owned by focused controllers where practical:

- `docs-viewer-route-workflow.js` binds route links and popstate
- `docs-viewer-search-controller.js` binds search/recent controls
- `docs-viewer-bookmarks.js` binds bookmark controls
- `docs-viewer-info-panel-controller.js` binds info-panel controls
- `docs-viewer-management.js` and child modules bind management-only controls after lazy loading

## Current URL And State Contract

The current viewer URL model is query-based rather than path-segment based.

Current URL state:

- `doc` selects the active document
- `scope` selects the active docs scope on `/docs/`
- `q` activates inline docs search for the current scope
- `/docs/` is the local manage route when the Docs Viewer service is available
- `package` selects the validated external package on `/docs-review/` and is preserved by internal history writes
- `view=source` selects temporary returned Markdown editing on `/docs-review/`
- `report_sort`, `report_dir`, and `report_filter` hold state for report-backed document panes
- `#hash` targets a heading within the rendered document

Explicit `doc` values are preserved in browser history even when the document no longer exists.
In that case the viewer shows `Document not found.` at the clicked URL so Back/Forward navigation behaves like a normal page visit.

The local management shell normalizes onto canonical scoped URLs:

- `/docs/?scope=studio&doc=<doc_id>`
- `/docs/?scope=library&doc=<doc_id>`
- `/docs/?scope=analysis&doc=<doc_id>`

The browser runtime keeps internal `/docs/?scope=<scope>&doc=<doc_id>` links canonical and does not add a management query.
Source Markdown links should stay canonical and should not include management route state.

Public read-only docs routes use:

- `/library/?doc=<doc_id>`
- `/analysis/?doc=<doc_id>`

## Current Runtime Behavior

At runtime the viewer:

1. loads the scope index JSON
2. builds the tree from `parent_id`
3. uses generated title order for root siblings and each parent’s children, with `doc_id` as the tie-breaker
4. loads per-doc rendered HTML from the selected document payload
5. keeps the left navigation in place while the right pane switches between document view and inline search results

Current document metadata behavior:

- the document H1 is treated as the visible title
- the main-view toolbar breadcrumb path shows ancestor docs only, so it does not duplicate the current document title
- root-level docs hide the breadcrumb path while preserving the main-view toolbar for document controls
- selected-document metadata such as summary, dates, UI status, visibility, and route belongs in the info panel metadata view

Current sidebar behavior:

- larger screens show index panel controls in the header for view-supported layout states
- `index-tree` supports normal and collapsed states and does not expose direct expanded mode
- management-enabled Docs Viewer routes can switch the index panel between `index-tree` and the placeholder `index-graph` view through the round toolbar pill immediately left of Actions
- the placeholder `index-graph` view supports direct expanded mode, so the expand control is visible only while that view is active in normal state
- the one-step control restores collapsed to normal, collapses normal to collapsed, and restores expanded to normal
- the collapsed rail keeps the one-step control visible so the index can always be restored
- the collapsed desktop layout widens the Docs Viewer reading measure without making prose fully fluid
- the collapsed state is stored per viewer scope in browser storage
- smaller screens keep the existing stacked layout and do not show the collapse control, because the document pane already has the full viewport width

Current search behavior:

- docs search is inline within the viewer rather than a separate docs search page
- docs search includes only viewable docs
- docs search excludes docs where `viewable: false`
- the viewer lazily loads the scope search index when `q` is present
- result links route back into the same viewer URL model
- modified, non-primary, target, and download clicks on result links and document links keep native browser behavior, so command-click and context-menu open-in-new-tab are handled by the browser
- search and recently-added list entries use title plus muted metadata rather than showing `doc_id`
- search metadata uses `last_updated` and, when available, parent title in the form `date • parent`

Current recently-added behavior:

- the button is rendered by the shared shell when inline docs search is enabled
- the runtime sorts current-scope viewable docs by `added_date` descending, then title ascending
- the list is capped by `docs_viewer.recently_added_limit` in the Docs Viewer config family
- list metadata uses `added_date` and, when available, parent title in the form `date • parent`

Current report behavior:

- docs source front matter can opt into a report with `viewer_report`
- `viewer_report_scope` selects the generated docs scope the report reads; if omitted, the current viewer scope is used
- `viewer_report_access` gates reports to public, manage, or local-only contexts
- report-backed docs remain normal docs in the index, so `parent_id`, title-ordered placement, visibility, bookmarks, and management moves still work normally
- public/read-only reports consume generated-data callbacks; local/manage reports consume `docs-viewer-report-service.js` for local source-config and broken-links audit endpoint access
- the first report is `docs_index_table`, a scope-aware generated-docs table with filter buttons, sortable columns, and Docs Viewer row links
- the Library Documents review now uses `viewer_report: docs_index_table` with `viewer_report_scope: library`

Current visibility behavior:

- generated docs tree and by-id payloads can carry `viewable: false` docs that remain generated and manageable
- source front matter uses `viewable: false` for non-viewable docs and omits `viewable` for the default viewable state
- public/default viewer navigation, inline search, and recently-added lists include only docs where `viewable !== false`
- public/default viewer discovery also excludes descendants of a non-viewable parent, without changing descendant `viewable` values

Current manage-mode draft behavior:

- public/default tree rendering includes only docs whose generated tree node is not `viewable: false`
- manage mode always includes non-viewable docs in the tree
- manage mode preserves the source hierarchy when non-viewable docs are included; children are not automatically changed when a parent is non-viewable
- the manage toolbar includes a right-aligned light/dark toggle that stores the selected theme in browser storage and applies it to the standalone `/docs/` shell
- the manage toolbar has a `show viewable` checkbox, checked by default, that keeps viewable docs visible for context
- unchecking `show viewable` gives a focused non-viewable/draft review tree
- manage-mode direct links to a viewable doc auto-enable `show viewable` so links can land on the target
- non-viewable docs are prefixed with the configured draft marker in the index and use Docs Viewer config and CSS policy for draft display
- a selected non-viewable doc can be made viewable through the manage toolbar; the action prompts before also making required non-viewable ancestors or optional descendants viewable

Document metadata display is centralized in the info panel so public and management routes do not need separate inline header metadata rules. Docs search continues to use `last_updated`; revisiting search metadata and ranking is a separate search task.

## Scope Boundary

The current design keeps some behavior scope-specific and some behavior shared.

Scope-owned:

- source doc trees
- compact `index-tree.json` payloads, compact `recently-added.json` payloads, and per-doc payloads
- scope-level viewer options in generated tree payloads
- route/page shell copy
- route ids on route shells and browser-safe route records in `docs-viewer/config/routes/docs-viewer-routes.json`

Shared:

- shell structure
- viewer runtime
- tree-navigation model
- document rendering model
- inline docs search interaction pattern

The rule for when this should and should not fork is recorded in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
