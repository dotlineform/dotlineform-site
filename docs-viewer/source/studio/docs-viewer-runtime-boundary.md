---
doc_id: docs-viewer-runtime-boundary
title: Runtime Boundary
added_date: 2026-03-31
last_updated: 2026-06-04
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Runtime Boundary

## Purpose

This document records the current boundary between:

- scope-specific docs shells such as service-owned `/docs/` and public Jekyll `/library/`
- the public Docs Viewer entrypoint in `docs-viewer/runtime/js/docs-viewer-public.js`
- the local/manage Docs Viewer entrypoint in `docs-viewer/runtime/js/docs-viewer-manage.js`

It exists as a guardrail so the repo can continue adding scope-specific docs behavior without forking stable lower-level viewer primitives.

It also records the public/manage promotion policy for Docs Viewer runtime work.
Public read-only installs should be lightweight deliverables that import only the data, JavaScript, CSS, and browser-visible config they need.
Local/manage installs can keep the full management surface, local-service workflows, report tooling, source editing, imports, and scope lifecycle behavior.

## Current boundary

Current model:

- scope pages may diverge at the route-shell level
- public and manage routes load separate entrypoint assets
- public and manage routes still share lower-level boot/runtime modules where the current slice has not split them yet
- the public structural shell include renders only public shell mounts
- the local manage shell renders the management-capable shell

Current shell examples:

- `docs-viewer/shell/docs-viewer-shell.html` for local `/docs/` management mode
- `library/index.md`
- `analysis/index.md`

Current entrypoints and shared implementation:

- `docs-viewer/runtime/js/docs-viewer-public.js` as the public read-only entrypoint loaded by public route shells
- `docs-viewer/runtime/js/docs-viewer-manage.js` as the local/manage entrypoint loaded by the Docs Viewer service shell
- `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the app boot owner for root discovery, asset-version read, route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, theme-toggle loading, single-start guarding, and runtime startup
- `docs-viewer/runtime/js/docs-viewer-app-composition.js` as the app-composition owner for runtime defaults, service-context projection handoff, hosted-view registry creation, panel layout creation, app-session creation, generated-data runtime creation, config-service creation, document-index state creation, public/manage startup phase descriptions, startup authority notes, and initial startup phase sequencing
- `docs-viewer/runtime/js/docs-viewer-app-session.js` as the app-session owner for state default creation, named state-domain facades, and public/manage route-session projection. It still returns the broad state object for runtime-internal controller handoff while controller families finish moving to explicit domains, but it no longer exposes a separate compatibility bridge.
- `docs-viewer/runtime/js/docs-viewer-app-runtime.js` as the private app runtime coordinator for focused controller construction, callback handoff, config/controller bridges, event handler definitions, private management/startup route callbacks, and the intentionally small returned app handle: `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`
- `docs-viewer/runtime/js/docs-viewer-route-workflow.js` as the focused route/document workflow owner for current URL/query helpers, current-doc resolution, route application, canonical URL correction, document index load orchestration, document payload load orchestration, missing-doc and payload-error handoff, route-link handling, popstate coordination, and the private route command contract consumed by focused controllers and management reloads
- `docs-viewer/runtime/js/docs-viewer-service-context.js` for explicit public/manage service context projection; public contexts keep static generated/config assets and omit report registry loads, management base URLs, local generated-read service base URLs, backend probes, and management service adapters
- `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` for generated-data request option shaping, generated-read capability caching, reload/retry option projection, generated-search read capability checks, and named read methods for docs index, document payload, search index, cross-scope docs index, references index, and reference-target JSON
- `docs-viewer/runtime/js/docs-viewer-config-service.js` for browser-safe Docs Viewer config and UI-text asset reads using the generated-data runtime request projection
- `docs-viewer/runtime/js/docs-viewer-asset-url.js` for asset-version URL projection shared by boot, route config, route context, report registry, config-service, and generated-data runtime owners
- `docs-viewer/runtime/js/docs-viewer-data.js` for low-level JSON fetch/retry and generated-read reload path primitives; direct imports are reserved for `docs-viewer-generated-data-runtime.js` and `docs-viewer-config-service.js`
- `docs-viewer/runtime/js/docs-viewer-report-service.js` for local report endpoint access in management-capable contexts, including source-config reads and broken-links audit requests
- `docs-viewer/runtime/js/docs-viewer-document-index-state.js` for document visibility/loadability projection, non-viewable/manage-only tree filtering, non-loadable fallback resolution, default-doc selection, and index status projection
- `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js` for selected-document info-panel coordination, default metadata-info open/close behavior, toolbar click handoff, toggle projection, update-on-document-change behavior, and public-safe hosted-view context handoff from explicit document-index, selected-document, scope-config, panel-view, route-access, URL, and trail inputs
- `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js` for neutral lazy-controller loading, currently used by the private app runtime coordinator to pass named management state-domain, service-client, and route-reload contracts and import the management controller only when management is allowed
- `docs-viewer/runtime/js/docs-viewer-app-context.js` and `docs-viewer/runtime/js/docs-viewer-route-config.js` for route context, explicit route config shape, browser-safe route-config registry resolution, and route/scope projection imported by the entry and config controllers
- `docs-viewer/runtime/js/docs-viewer-config-controller.js` for config-service-backed Docs Viewer config loading, scope route projection, scope picker projection, UI-text merge, recent-limit/status-label projection, and management/status copy updates from explicit scope-config, document-index, search/recent, route-session, config-service, and route-command inputs
- `docs-viewer/runtime/js/docs-viewer-access.js` for static public/manage/manage-local access projection imported by route context and hosted-view helpers
- `docs-viewer/runtime/js/docs-viewer-app-shell.js` and its renderer children for JavaScript-owned shell composition before the entry controller wires route behavior
- `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` for management-only context menu, metadata modal, import modal, settings modal, and import host refs rendered only when route access allows management UI
- `docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js` for management-only selected-document status pills, `Edit`, and `Markdown source` controls rendered only through manage-capable shell composition; public-safe main-view chrome must not define or hide these controls
- `docs-viewer/runtime/js/docs-viewer-management-document-reports.js` for manage-owned document report mounting, report-context construction, report registry URL handoff, and local report-service creation; public entrypoints do not import it
- `docs-viewer/runtime/js/docs-viewer-panel-layout.js` and `docs-viewer/runtime/js/docs-viewer-view-state.js` for app-shell panel projection and the index/main/info view-state skeleton
- `docs-viewer/runtime/js/docs-viewer-hosted-views.js` for minimal hosted-view registration, panel-specific listing, access/availability checks, built-in hosted-view records, and graceful absence
- `docs-viewer/runtime/js/docs-viewer-main-view-host.js` for main-view hosted-view availability checks, active main-view state projection, and switch-intent handling for `rendered-document`, `search-results`, and `recent-results`
- `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js` for app-shell-owned info-panel chrome and projection attributes
- `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` for info-panel hosted-view option projection, load, mount, update, unmount, close, and graceful absence behavior
- `docs-viewer/runtime/js/docs-viewer-view-context.js` for explicit selected-document hosted-view context projection shared by metadata and planned future info views
- `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` for the first read-only public-safe metadata hosted view
- `docs-viewer/runtime/js/docs-viewer-management.js` as the management-mode controller loaded only by management-enabled viewer shells; it builds a management-local state facade from explicit route-session, scope-config, document-index, selected-document, search/recent, generated-data, and management domains
- `docs-viewer/runtime/js/docs-viewer-management-render.js` for management-only markup helpers imported by the management controller
- `docs-viewer/runtime/js/docs-viewer-management-client.js` for Docs Viewer service transport helpers used by the management controller
- `docs-viewer/runtime/js/docs-viewer-drag-drop.js` for drag/drop helpers used by the management controller
- `docs-viewer/runtime/js/docs-viewer-tree.js` for pure tree and visibility helpers imported by focused document-index and management modules
- `docs-viewer/runtime/js/docs-viewer-search.js` for pure inline-search and recently-added helpers imported by the search controller
- `docs-viewer/runtime/js/docs-viewer-search-controller.js` for inline-search and recently-added controller ownership: search index loading, result rendering, recent rendering, search debounce behavior, explicit search/recent state-domain input, route command consumption, more-results behavior, and pane command requests
- `docs-viewer/runtime/js/docs-viewer-bookmarks.js` for bookmark state, rendering, IndexedDB storage orchestration, bookmark events, selected-document bookmark UI projection, explicit route command consumption, and search-reset command consumption when opening a bookmark
- `docs-viewer/runtime/js/docs-viewer-favourites.js` for bookmark record and IndexedDB storage helpers imported by the bookmark controller
- `docs-viewer/runtime/js/docs-viewer-document-controller.js` for rendered-document visibility, loading/missing/error states, final payload rendering, selected-document projection, existing search/recent pane projection handoff, and the optional document-extras hook used by manage-owned report mounting
- `docs-viewer/runtime/js/docs-viewer-sidebar.js` for tree sidebar rendering, breadcrumb metadata rendering, expanded-row projection, selected-document highlighting, and scope-config management text/date display from explicit document-index, selected-document, and scope-config inputs
- `docs-viewer/runtime/js/docs-viewer-render.js` for read-oriented result and bookmark markup helpers imported by the entry and bookmark controllers
- `docs-viewer/runtime/js/docs-viewer-router.js` for low-level URL building, anchor route parsing, browser history writes, requested-doc resolution, canonical route correction, popstate helper behavior, and payload-load helper behavior imported by the route workflow owner
- `_includes/docs_viewer_shell.html`
- `docs-viewer/static/css/docs-viewer.css` for basic/public viewer styling, portable Docs Viewer tokens, and shell utilities loaded by public Jekyll routes and the local manage shell
- `docs-viewer/static/css/docs-viewer-reports.css` for report styling loaded by the local manage shell until a report is explicitly promoted to public
- `docs-viewer/static/css/docs-viewer-manage.css` for management-only shell and modal styling

The shell loads the entrypoint as an ES module.
Extracted helper modules must not import the entrypoint or mutate private runtime coordinator state directly.
The management controller receives a narrow context API through the neutral lazy-controller adapter so public read-only viewers do not download or execute management-only orchestration.
Route workflow commands such as `applyCurrentRoute`, `loadIndex`, `loadDoc`, and `setHistory` are exposed only through the private route workflow command contract, backed by explicit route-session, scope-config, document-index, selected-document, search/recent, and status inputs.
They are not returned on the public app handle and should not be reintroduced as one-off runtime wrapper callbacks.
The returned app handle also does not expose broad app/session state, app-composition internals, app-session internals, management service handles, backend capability probes, or the management lazy loader.

Current CSS base boundary:

- public `/library/` and `/analysis/` routes intentionally get `assets/css/main.css` from the public site layout, then load Docs Viewer-owned basic viewer CSS through the shared include
- standalone local `/docs/` gets Docs Viewer-owned basic viewer CSS from the Docs Viewer service shell, then loads report CSS and management CSS
- `docs-viewer/static/css/docs-viewer.css` supplies portable Docs Viewer tokens, shell utilities such as `visually-hidden`, `muted`, `small`, hidden-state handling inside `.docsViewer`, and viewer component tokens with Docs Viewer theme-token and host-token fallbacks

Because Docs Viewer has public read-only installs and a planned portable shell, reusable Docs Viewer code should not depend on Studio CSS or unrelated public-site page classes.
Standalone Docs Viewer pages should use the Docs Viewer-owned base layer for page-level shell defaults, while public Jekyll routes may continue to inherit their public host base intentionally.

Current scope-owned data:

- `docs-viewer/generated/docs/studio/`
- `assets/data/docs/scopes/library/`
- `assets/data/docs/scopes/analysis/`

## Public And Manage Install Policy

Docs Viewer should split public and local/manage deliverables at the entrypoint and shell-composition level, while keeping shared lower-level core modules where they are genuinely common.

This is not a full codebase fork.
The public and manage installs should not duplicate core infrastructure such as generated docs index parsing and public-safe record projection, tree helpers, route helpers, generated-data reads, search normalization, URL builders, and renderer primitives.
Those shared modules remain appropriate when they have no local-service, write-authority, management UI, or manage-only CSS/config dependency.

The durable boundary is:

- public surface is only what the public entrypoint imports, the public shell renders, and public route/config records expose
- manage surface is only what the manage entrypoint imports, the manage shell renders, and management capability checks plus server-side endpoints authorize
- shared core is not public surface by itself
- route config and hosted-view records are visibility and composition metadata, not proof that a module, stylesheet, report, service, or data payload belongs in public

Default feature flow:

1. Build new Docs Viewer capabilities in local/manage first unless the request is explicitly public-only.
2. Keep the capability behind the manage entrypoint, management shell, management UI text, management CSS, and management service contracts.
3. Promote a capability to public only through a named public-promotion step.
4. In that promotion step, choose the exact public modules, CSS, config, data contract, route records, and tests.
5. Add tests that prove manage-only assets and data do not load on public routes after promotion.

Promotion should be explicit because public scopes are public-reader installs, not local tools with disabled controls.
Do not implement a new feature by adding it to one broad runtime and then hiding it from public with scattered mode checks.
Access checks still matter for graceful unavailable states, but they are not a substitute for not shipping manage-only assets to public routes.

Reports are the reference example.
The manage install can keep the full report framework, local-service reports, source/config audits, semantic-reference reports, broken-link audits, and admin tables.
Public installs should not load report runtime, report CSS, or report registry data until a specific public report is promoted.
When that happens, only the selected public-safe report loader, public-safe data source, minimum report renderer/CSS, route config, and asset-load tests should move across.
Manage-only reports must remain absent from public entrypoint imports and public route loads.

Public promotion acceptance should include:

- public route network/import assertions for JS, CSS, route config, UI text, report metadata, and generated data
- public DOM assertions that management controls, source-editor controls, import hosts, settings controls, scope lifecycle controls, and local-service status surfaces are not rendered
- manage smoke coverage proving the full management surface still loads through the manage entrypoint
- source docs describing what was promoted and why it is public-safe

Related implementation request:

- [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints)

## Controller And Hosted-View Lifecycle Contract

Docs Viewer controllers and hosted views use a practical lifecycle, not a framework-level plugin system.

Controller terms:

- `create`: assemble a controller with explicit refs, callbacks, state-domain inputs, services, and config values.
- `initialize`: run startup work that should not happen at construction time, such as bookmark storage loading or management capability checks.
- `bind`: attach DOM/window event listeners for the controller's owned surface. Bind is a startup phase and should be called once.
- `update` or `project`: render or project current state after selected document, route state, panel state, or capability state changes.
- `dispose`: optional cleanup for controllers that gain a shorter lifetime than the route or own external subscriptions, timers, workers, observers, or hosted resources.

Hosted-view terms:

- `load`: optional lazy module load or factory step.
- `mount`: render into an explicit mount element from an explicit hosted-view context.
- `update`: refresh an already-mounted view from a new explicit context.
- `unmount`: clear the active mounted view when switching views or closing a panel.
- `close`: host action that marks the panel closed and unmounts the active view.
- `dispose`: final cleanup for the active view if the host itself is discarded.

Current owner map:

- `docs-viewer/runtime/js/docs-viewer-app-composition.js` owns startup phase sequencing and startup authority records.
- `docs-viewer/runtime/js/docs-viewer-app-session.js` owns named state-domain facades plus the runtime-internal broad state object still used by remaining controller handoffs.
- `docs-viewer/runtime/js/docs-viewer-route-workflow.js` owns route-link and popstate binding, URL/history helpers, route application, index/payload workflow handoff, and the private route command contract for search/recent, bookmarks, startup index loading, and management reloads.
- `docs-viewer/runtime/js/docs-viewer-search-controller.js` owns search/recent binding, generated search reads, debounce, result/recent rendering, route command consumption, and pane command requests from explicit state-domain inputs.
- `docs-viewer/runtime/js/docs-viewer-bookmarks.js` owns bookmark storage initialization, bookmark binding, rendering, document-load route command consumption, and search-reset command consumption from explicit bookmark/document/search inputs.
- `docs-viewer/runtime/js/docs-viewer-document-controller.js` owns rendered-document pane projection, payload rendering, loading/missing/error states, existing search/recent pane projection handoff, and optional document-extras hook invocation. Report metadata interpretation and report-service handoff are manage-owned.
- `docs-viewer/runtime/js/docs-viewer-management-document-reports.js` owns manage-only report metadata detection, generated-data report read handoff, report registry URL handoff, and local report-service construction before delegating to the allowlisted report runtime.
- `docs-viewer/runtime/js/docs-viewer-report-service.js` owns browser-side local report endpoint paths, request options, local-server missing-base errors, and response-envelope differences for source-config and broken-links audit reports.
- `docs-viewer/runtime/js/docs-viewer-sidebar.js` owns sidebar tree and document metadata rendering from explicit document-index, selected-document, and scope-config inputs.
- `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js` owns info toggle/toolbar binding, selected-document hosted-view context projection, host open/close/update handoff, view-state projection sync, and toggle projection from explicit document-index, selected-document, scope-config, panel-view, route-access, URL, and trail inputs.
- `docs-viewer/runtime/js/docs-viewer-config-controller.js` owns browser-safe Docs Viewer config loading, route-scope resolution, scope-picker projection, route-global/root-dataset projection, UI-text merge, recent-limit/status-label projection, and management/status copy updates from explicit scope-config, document-index, search/recent, route-session, config-service, and route-command inputs.
- `docs-viewer/runtime/js/docs-viewer-config-service.js` owns browser-safe Docs Viewer config and UI-text fetch/retry behavior. Config controllers consume this service instead of importing low-level data helpers.
- `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` owns all feature-facing generated-data reads. Feature controllers and reports consume named generated-data methods through route/search/document report contexts rather than importing low-level fetch/reload helpers.
- `docs-viewer/runtime/js/docs-viewer-asset-url.js` owns asset-version URL projection. It is not a generated-data read owner and should stay free of service capability or reload behavior.
- `docs-viewer/runtime/js/docs-viewer-management.js` owns the management-local facade and orchestration over management action, modal, capability, interaction, scope-lifecycle, service-client, and route-reload contracts. It receives named management state-domain, service-client, and route-reload inputs from the lazy runtime boundary rather than the broad runtime state object.
- `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` owns info hosted-view resolution, load, mount, update, unmount, close, dispose, option projection, and graceful absence.
- `docs-viewer/runtime/js/docs-viewer-hosted-views.js` owns the minimal hosted-view record shape, lifecycle method defaults, panel-specific listing, access/availability checks, built-in/repo-owned default hosted-view records through `createDocsViewerDefaultHostedViews()`, and route-config hosted-view filtering through `createDocsViewerRouteHostedViews(...)`.
- `docs-viewer/runtime/js/docs-viewer-main-view-host.js` owns main-view availability checks, switch-intent handling, active main-view state projection, main-view toolbar projection handoff, and main-view module-context creation for `rendered-document`, `search-results`, `recent-results`, and manage-only mounted modules such as `markdown-source`.
- `docs-viewer/runtime/js/docs-viewer-view-context.js` owns public-safe selected-document hosted-view context projection and the main-view module context shape with selected document, scope, route access, main-view intent/toolbar/warning helpers, and capability-gated source-editor service slots.
- `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` owns the first public-safe read-only metadata hosted view.
- `docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js` owns manage-only selected-document status/edit/source controls above the shared main-view toolbar surface.
- `docs-viewer/runtime/js/modules/source-editor/source-editor.js` owns manage-only source-body editor rendering, dirty-state handling, rebuild submission, diagnostics, and rendered-view return behavior.
- `docs-viewer/runtime/js/docs-viewer-management.js` and its child modules own manage-mode capability checks, action/menu/modal coordination, imports, settings, scope lifecycle, status pills, and write orchestration behind the lazy management boundary.

Lifecycle owner rules:

- Use lifecycle methods only where they reduce coupling or clarify phase ownership.
- Keep stateless render/project helpers stateless.
- Public-safe hosted views must mount without management services, backend probes, local generated-read service base URLs, write-capable service handles, or management CSS/JS.
- Manage-only hosted views may receive explicit management service or capability inputs, but visibility and registration do not imply write authority.
- Manage-owned document extras may mount report surfaces; public entrypoints must not supply report extras unless a named public-promotion request defines the public report assets and tests.
- Main-view source-editor service slots must be omitted from public contexts and supplied only through explicit management-capable context construction.
- Route-config hosted-view records are metadata/capability declarations only. They must not load arbitrary modules, override built-in or repo-owned ids, or create plugin behavior.
- Backend writes remain behind named management endpoints with server-side validation.
- Future feature views should attach through panel/controller contracts and explicit context or service inputs, not by modifying route shell markup or reading broad runtime state.
- Do not turn hosted-view records into a plugin platform, third-party loader, source editor, semantic-reference editor, or visualization extension point without a separate request.

Generated-data helper boundary:

- Feature-facing controllers must consume `docs-viewer-generated-data-runtime.js` named read methods through explicit controller or report-context inputs.
- Config loading must consume `docs-viewer-config-service.js`; the config controller must not import `docs-viewer-data.js` directly.
- Low-level fetch/retry helpers in `docs-viewer-data.js` are current architecture only as primitives behind `docs-viewer-generated-data-runtime.js` and `docs-viewer-config-service.js`.
- Static asset URL projection belongs in `docs-viewer-asset-url.js`; callers should not import `docs-viewer-data.js` only to add asset versions.

Docs Import boundary:

- The user-facing Docs Import surface is the Docs Viewer management modal mounted by `docs-viewer-management-shell-renderer.js` and initialized lazily by `docs-viewer-management.js`.
- `docs-html-import.js` owns the modal app state, scope/file selection, route-ready dataset projection, service availability display, and event binding for the import surface.
- `docs-html-import-workflow.js` owns preview/write orchestration and overwrite/replacement prompts for the import flow.
- Import writes stay behind `docs-viewer-management-client.js` calls to management endpoints such as `/docs/import-source`; future import behavior should extend the import workflow or management service contracts rather than duplicating route-readiness or service probing patterns.

Current route capability boundary:

- `/docs/` is the only route that enables `?mode=manage`; it is served by the standalone Docs Viewer service
- `/docs/` can switch the loaded docs scope with `?scope=studio`, `?scope=library`, or `?scope=analysis`
- `/library/` and `/analysis/` are public read-only viewer routes and do not render management controls, configure write-capable management mode, or load management-only CSS
- public read-only viewer routes also avoid publishing or loading management-only JS/CSS, the HTML import modules, the local manage-capable route registry, management base URLs, local generated-read service base URLs, and backend capability probes
- local `bin/local-studio` links to the configured Docs Viewer service but does not serve Docs Viewer management, generated reads, or Docs Viewer assets
- a `mode=manage` query on a public viewer route is normalized away by the shared runtime because those routes cannot perform local writes on the static public site
- canonical internal docs links stay read-only-safe and omit `mode=manage`; the management-capable `/docs/` shell preserves manage mode at runtime only when the current session is already in manage mode

Current app-shell route handoff boundary:

- route config is the preferred durable route/app shape for new app-shell work
- the shared and standalone route shells expose only `data-route-id` and `data-route-config-url` as boot route context
- the shared and standalone route shells provide app mounts for header controls, index panel, management shell, main view, and info panel; management-only context-menu and modal markup is no longer authored in the route shell templates
- `docs-viewer/config/routes/docs-viewer-routes.json` is the local service route-config registry for `/docs/`, `/library/`, and `/analysis/`
- `docs-viewer/config/routes/docs-viewer-public-routes.json` is the Jekyll-published public route-config registry for `/library/` and `/analysis/`; it intentionally omits the local `/docs/` management route and manage-only hosted views
- `docs-viewer/runtime/js/docs-viewer-route-config.js` fetches that registry and resolves the current `docs_viewer_route_config_v1` record; route config resolution no longer reads inline config scripts or legacy `#docsViewerRoot` data attributes
- the standalone Docs Viewer service serves the same route registry path with local `/docs/` management and generated-read base URLs injected from service config; static public builds keep those URLs blank
- scope-specific generated docs and search paths remain owned by `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json`
- backend reachability and write availability are not browser-side route-config authority; they remain in the local management capability flow
- the first info-panel hosted view is read-only and public-safe; source paths, local filesystem actions, editable metadata saves, semantic references, and activity history remain outside the info-panel metadata view contract
- info-panel hosted views can be listed and switched through the app-shell toolbar; disabled, unavailable, missing, and access-blocked views stay graceful and do not create write authority
- main-view route config uses the `main` panel key and `rendered-document` as the default central view; `panels.document` and `document-host` are retired rather than compatibility aliases

## What should stay scope-specific

These are normal route-shell differences and should not force a runtime fork.

- scope-specific inline search controls or other shell actions
- different viewer data index URLs
- different base routes and default docs
- whether the route shell enables management mode
- whether the route shell exposes scope switching
- surrounding page context and navigation state
- scope-specific copy or small shell-level layout changes
- distinct source trees and generated JSON artifacts
- scope-specific viewer options in generated docs indexes, such as manage-only structural tree roots

These are expected uses of the current architecture.

## What should not trigger a fork

The following are not good reasons to split the runtime.

- adding or removing a button in one scope page
- changing page-level copy
- changing which scope-owned JSON tree the viewer loads
- adding small optional shell parameters to the shared include
- keeping Studio and library docs in separate source roots
- hiding a structural tree branch in one scope when that rule can be expressed as generated scope-owned data

If the difference can be expressed through data, route-shell composition, or a small include option, the runtime should stay shared.

## Potential fork triggers

A fork only becomes justified if the scopes stop being the same kind of viewer.

### Fundamentally different navigation model

Examples:

- one scope stays a tree-based docs viewer while another becomes faceted browsing
- one scope wants timeline or gallery navigation instead of a docs tree

### Fundamentally different rendering model

Examples:

- one scope needs a richer content renderer with annotations, embedded canvases, or interactive reading tools
- one scope needs a different page anatomy than the sidebar-plus-content viewer

### Fundamentally different URL and state model

Examples:

- one scope needs nested route segments rather than `?doc=...`
- one scope needs version switching, compare state, or multi-pane state in the URL

### Fundamentally different performance model

Examples:

- one scope remains small and loads one index JSON
- another scope needs chunked indexes, lazy subtree loading, or other large-corpus behavior

### Fundamentally different interaction contract

Examples:

- one scope stays read-only
- another scope needs editing affordances, advanced keyboard navigation, or persistent review state

## Preferred response before forking

If a new requirement appears, prefer these steps in order:

1. express it as scope-owned data
2. express it as route-shell divergence
3. add a narrow optional include parameter
4. add a narrow runtime option if the core viewer model is still the same
5. fork only if the viewer model itself has diverged

This order is intended to delay a fork until there is clear evidence that the scopes are no longer the same product.

## Practical design rule

Use one runtime while the scopes are still:

- tree-index driven
- document-viewer shaped
- compatible with the same URL/state contract
- compatible with the same loading strategy

Consider a fork only when a new scope would otherwise force the shared runtime to carry a second competing model of navigation, rendering, or interaction.
