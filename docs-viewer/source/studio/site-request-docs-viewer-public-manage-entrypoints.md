---
doc_id: site-request-docs-viewer-public-manage-entrypoints
title: Docs Viewer Public/Manage Entrypoint Split Request
added_date: 2026-06-04
last_updated: 2026-06-04
ui_status: done
parent_id: change-requests
---
# Docs Viewer Public/Manage Entrypoint Split Request

Status:

- done

## Summary

Split Docs Viewer public and local/manage installs at the entrypoint and shell-composition level, while keeping genuinely shared lower-level core modules.

The goal is a lighter public Docs Viewer install that is easier to maintain and test without unnecessarily duplicating core infrastructure.
This request does not change current visible behavior.
It reorganizes how public routes and manage routes load JavaScript, CSS, UI text, route config, report support, panel views, and future promoted features.

## Decision

Use separate public and manage application deliverables, not a fully separate public codebase.

Target shape:

- `docs-viewer-public.js` boots public read-only routes such as `/library/` and `/analysis/`
- `docs-viewer-manage.js` boots the local `/docs/` management shell
- public route shells render only public DOM mounts and public controls
- manage route shells render the full management-capable shell
- shared lower-level modules remain available when they have no management UI, local-service, write-authority, manage-only CSS, or manage-only config dependency
- public features are promoted from manage to public through explicit public-promotion work, not by default sharing

This creates a controlled path:

- local/manage can grow first
- public can stay lightweight
- later public promotion chooses only the specific modules, CSS, config, data, and tests that are public-safe

## Goals

- reduce public route JavaScript, CSS, config, UI-text, and data payloads to public needs only
- prevent accidental public loading of manage-only modules, report tooling, local-service code, source editing, imports, settings, scope lifecycle, or management controls
- keep common infrastructure in shared core modules rather than duplicating route parsing, generated-data reads, payload-agnostic tree view-model/rendering primitives, search helpers, URL helpers, and renderer primitives
- make public promotion a deliberate implementation step with named assets and tests
- keep current visible behavior for public `/library/`, public `/analysis/`, and local/manage `/docs/`
- make tests simpler by asserting public entrypoint loads and manage entrypoint loads separately
- keep management writes and local-only reads behind the existing Docs Viewer management service and server-side validation

## Non-Goals

- no visible UI redesign in this request
- no change to public URL contracts
- no change to management URL contracts
- no removal of current public search, recently-added, bookmark, index, document, or info-panel behavior unless a later request explicitly changes those features
- no full public codebase fork
- no duplication of stable shared core infrastructure
- no report promotion to public in this request
- no public source editing, import, settings, scope lifecycle, or management status workflow
- no generated docs payload slimming in this request; that is tracked by [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming)

## Current Problem

The current shared entrypoint has useful access gating, but it is not a true lightweight public install boundary.

Current good behavior:

- public routes use a public route registry
- public routes use a public Docs Viewer config
- management CSS is not loaded by public route shells
- the management controller is behind a management-only dynamic import gate
- manage-only source editor implementation is a dynamic import and is not available on public routes

Current leakage and weight risks:

- public routes still use the broad shared runtime static graph
- public routes still load shared CSS that includes features not currently public, such as report styling
- public routes still load shared UI text that contains management/import/scope lifecycle copy
- public shell rendering can create hidden manage-only controls instead of omitting them from public DOM
- public route config can reference report registry data even when no public route currently needs reports
- access-aware runtime decisions are becoming a maintenance pattern instead of a narrow safety layer

The problem is not only whether manage functionality is runnable.
The public install should also avoid downloading or rendering artifacts that are not public surface.

## Architecture Shape

### Public Entrypoint

`docs-viewer-public.js` should own public route boot.

It should import only:

- public route-config resolution
- public app context projection
- public shell rendering
- public generated docs/search reads
- public index tree rendering
- public rendered-document loading
- current public search and recently-added behavior
- current public bookmark behavior if retained
- current public info-panel metadata behavior if retained
- shared pure helpers needed by those features

It should not import:

- management controller
- management action renderers
- management shell renderers
- management client
- source editor
- import modules
- scope lifecycle modules
- settings/status mutation modules
- report runtime or report modules unless a specific public report has been promoted
- management CSS or management UI text

### Manage Entrypoint

`docs-viewer-manage.js` should own local `/docs/` boot.

It can import the full local/manage app:

- manage route config
- manage shell rendering
- management toolbar and management shell hosts
- local generated-read service behavior
- management capability checks
- management client and management endpoints
- source editor
- import workflow
- settings/status mutation
- scope lifecycle
- report runtime and report modules
- management CSS and UI text

Manage can reuse public-style reader modules through shared core or shared reader components, but manage-only code should not flow back into the public entrypoint by default.

### Shared Core

Shared core should stay small and public-safe.
Manage-only reusable code can exist, but it is not shared core; it belongs in manage-owned modules that the public entrypoint cannot import accidentally.
Shared modules must be stable primitives used consistently by both public and manage.
They should not branch on public/manage mode, accept public/manage capability switches, or contain disabled manage behavior for public routes.
Manage mode is built on top through manage-owned composition.

Good shared-core candidates:

- generated docs index parsing and public-safe record projection
- static generated-data read helpers for browser-visible JSON assets
- route and URL helpers
- payload-agnostic tree view-model and rendering primitives
- search normalization/scoring
- result rendering primitives
- asset-version URL helpers
- reader-facing hosted-view context helpers with no manage-only slots
- generic DOM projection helpers with no manage-only controls

Poor shared-core candidates:

- management client calls
- local-service capability probing
- local-service generated reads
- source editor services
- imports and write workflows
- report modules that read local endpoints
- scope lifecycle workflows
- management modals, menus, settings, status mutation, or source-opening behavior
- UI text bundles that include manage-only copy

## Indicative JSON And CSS Artifact Split

This table is indicative.
Exact file names can change during implementation, but the public/manage ownership should not.

| current artifact | current role | future public artifact | future manage artifact | action |
| --- | --- | --- | --- | --- |
| `docs-viewer/config/routes/docs-viewer-public-routes.json` | Public route registry for `/library/` and `/analysis/`. | Keep as the public route registry; remove fields for artifacts public does not load, such as report registry, until promoted. | None. | Narrow. |
| `docs-viewer/config/routes/docs-viewer-routes.json` | Local service route registry for `/docs/`, plus public route records. | None. Public routes should not load this registry. | Keep as the manage/service route registry, or split to `docs-viewer-manage-routes.json` if that makes ownership clearer. | Manage-owned. |
| `docs-viewer/config/defaults/docs-viewer-public-config.json` | Browser-visible public scope config. | Keep as public config and narrow to public scopes/features. | None. | Narrow. |
| `docs-viewer/config/defaults/docs-viewer-config.json` | Local/manage Docs Viewer config with local scopes and richer status/config data. | None. | Keep as manage config, or rename/split only if needed for clarity. | Manage-owned. |
| `docs-viewer/config/ui-text/ui-text.json` | Former shared UI text bundle that included public and manage copy. | `docs-viewer/config/ui-text/public.json`. | `docs-viewer/config/ui-text/manage.json`. | Split; shared bundle retired. |
| `docs-viewer/config/reports/reports.json` | Source report registry. | No public projection unless a specific public report is promoted. | Keep as report source registry for manage/report tooling. | Manage-owned until promotion. |
| `assets/data/docs/reports.json` | Browser-visible report registry projection. | Do not load on public routes until a specific public report is promoted; later use a public report projection if needed. | Keep for manage report runtime. | Move behind manage entrypoint. |
| `assets/data/docs/scopes/<scope>/index.json` | Public flat docs index used for tree construction and document selection. | Narrow or replace for public runtime after nav/tree payload exists. | Not used by manage except as static public data. | Slim after nav/tree slice. |
| Public nav/tree payload | Not present. | New tree-ready payload using the shared tree shape, for example `assets/data/docs/scopes/<scope>/nav.json`. | None. | New. |
| `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json` | Public rendered document payload. | Keep as selected-document payload, with reader-facing metadata only where possible. | Manage can still read public by-id payloads when viewing public scopes, but manage source/edit data comes from manage endpoints. | Mostly unchanged. |
| `assets/data/search/<scope>/index.json` | Public docs search index for public scopes. | Keep if public search remains enabled. | Manage uses local generated search for local scopes. | Mostly unchanged. |
| `docs-viewer/generated/docs/<scope>/index.json` | Local/manage generated docs index for local scopes such as `studio`. | None. | Narrow or replace for manage navigation after manage nav/tree payload exists; keep only if other manage features still require the rich flat projection. | Review after nav/tree slice. |
| Manage nav/tree payload | Not present. | None. | New richer tree-ready payload using the same shared tree shape, for example `docs-viewer/generated/docs/<scope>/nav.json`; include manage-only fields only after confirming context-menu, drag/drop, status, or viewability needs. | New. |
| `docs-viewer/generated/search/<scope>/index.json` | Local/manage generated search index for local scopes such as `studio`. | None. | Keep manage/local search projection. | Manage-owned. |
| `docs-viewer/static/css/docs-viewer.css` | Basic Docs Viewer shell, panel, search, toolbar, utility, token, and reader styling. | Keep as the complete basic/public viewer stylesheet. | Manage also loads it before report and manage-only CSS. | Consolidate base/public viewer contract here. |
| `docs-viewer/static/css/docs-viewer-reports.css` | Report styling currently loaded by the shared shell. | Do not load until a specific public report is promoted; then load only the minimum public report CSS. | Load through the manage entrypoint/report runtime. | Move behind manage entrypoint. |
| `docs-viewer/static/css/docs-viewer-manage.css` | Management-only shell, action, modal, import, source-editor, scope lifecycle, drag/drop, draft/non-viewable nav, and selected-document status mutation/menu styling. | None. | Keep manage-only. | Manage-owned. |
| `assets/css/main.css` | Host public-site layout/prose CSS inherited by public Jekyll routes. | Unchanged host CSS outside Docs Viewer split. | Not part of local Docs Viewer manage shell. | Out of scope. |

## Shared Modules Are Stable Primitives

Shared modules are not lowest-common-denominator implementations with public/manage branches.
They are stable primitives applied consistently by both entrypoints.

For a shared module:

- public and manage should call the same primitive for the same primitive behavior
- public/manage mode should not be an input
- public/manage capability switches should not be an input
- manage-only actions, services, controls, fields, context menus, drag/drop, and mutation behavior should not live inside it
- disabled or hidden manage behavior should not be embedded for public routes

Manage-only behavior is additive.
The manage entrypoint may load manage-owned modules that compose around or above shared primitives.
Those manage-owned modules can add context menus, drag/drop, status/viewability controls, source/metadata actions, local-service calls, and management-specific UI.
They should not require the shared primitive to become mode-aware.

Applied to the index panel, the shared tree renderer should own only the stable tree behavior.
The manage index layer can add right-click menus or management actions around that rendered tree, but the shared renderer should not receive a mode flag or manage capability map to decide what kind of tree it is.

## Public Promotion Policy

New Docs Viewer functionality starts in local/manage unless the request is explicitly public-only.

Promotion to public requires a named implementation step that defines:

- the exact public feature behavior
- public data inputs
- public route config
- public UI text
- public CSS
- public JavaScript modules
- public tests and asset-load assertions
- manage-only modules that must remain absent

Do not promote by adding a feature to a broad shared runtime and hiding it from public with scattered access checks.
Access checks remain useful for graceful unavailable states, but they are not the primary public install boundary.

Reports are the reference case.
The local/manage app can keep all report support.
Public should have no report runtime, report CSS, or report registry load until a specific public-safe report is selected.
When a report is promoted, only that report loader, its public-safe data source, the minimum report renderer/CSS, and route config should move into the public entrypoint.

## No Compatibility Or Silent Fallbacks

This refactor should not add compatibility aliases, legacy route/config field fallbacks, broad shared-entrypoint aliases, or silent alternate data paths.

Code should fail visibly when required public assets or manage capabilities are missing.
It should not hide failures or inaccessible data by trying another source and rendering as if the primary contract succeeded.

Allowed outcomes:

- public route shows a visible error when a required public config, nav/tree payload, docs payload, search payload, CSS, or entrypoint asset is missing
- manage route shows a clear unavailable state when a local management service or capability is unavailable
- a report or view shows an explicit unavailable state when it is not public or not available in the current route

Disallowed outcomes:

- public route tries a local generated-read service and silently falls back to static JSON
- manage route silently falls back to a public payload when local manage data is inaccessible
- runtime keeps legacy shared entrypoint aliases so old and new public/manage boot paths both work indefinitely
- route/config readers accept old field names without a separately approved migration plan and removal criteria
- missing public data is hidden by rendering a partial tree, document, or report as if it succeeded

If an implementation slice discovers a compatibility path, it should remove it in that slice or stop and document a named blocker with owner, reason, and removal criteria before adding adjacent behavior.

## Index Panel Tree Data

The index panel should do the least possible runtime shaping in both public and manage installs.

Both public and manage routes should move toward build-time tree projection rather than browser-time grouping of flat records.
The browser should load a nav/tree payload that is already ordered and already filtered for the current install.

Build time should own:

- parent/child tree construction
- root and sibling ordering
- public viewability filtering for public payloads
- manage visibility/loadability projection for manage payloads
- compact public nav record projection
- richer manage nav record projection only where confirmed manage behavior needs it
- optional path, depth, or trail fields only when a reader or manage surface needs them

Runtime should own:

- loading the route-appropriate nav/tree payload
- rendering tree rows
- expanding and collapsing UI state
- highlighting the selected doc
- routing to selected documents

The shared module should be a payload-agnostic tree renderer over a stable tree view model, not a public index owner or a manage index owner.
Public and manage entrypoints should provide their own loaders/adapters:

- public: `assets/data/docs/scopes/<scope>/nav.json` to public index view model
- manage: `docs-viewer/generated/docs/<scope>/nav.json` or equivalent richer payload to manage index view model

The basic tree shape should be the same where possible.
The manage payload can include optional manage-only fields or side payload references only after confirming what right-click menus, drag/drop, status indicators, viewability controls, or source/metadata actions actually need.
Manage-only behavior should layer on top of the shared tree renderer through manage-owned modules.
The shared tree renderer should not receive a public/manage mode, receive a manage capability map, know how to open context menus, mutate status, call management services, or handle source/edit workflows.

This should not be implemented before the public/manage entrypoint and shell boundary exists.
The first slice should make the public deliverable real.
After that, public and manage nav/tree payloads can target their entrypoints directly instead of being folded into the current broad shared runtime.

This nav/tree work is related to, but distinct from, [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming).
The entrypoint split creates the public runtime boundary.
The nav/tree payloads then give the index panel purpose-built data contracts.
The public index slimming request can remove or narrow flat public index fields once public navigation no longer depends on browser-time tree construction.

## Implementation Steer

Implement this request as a sequence of slices rather than one broad rewrite.

Suggested order:

1. Establish the public/manage entrypoint and shell boundary.
2. Complete [Docs Viewer Public/Manage Entrypoint Baseline Inventory](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints-baseline).
3. Remove compatibility aliases or silent fallback paths discovered in the touched boot/config/data surfaces.
4. Add load/import tests that prove public routes do not request manage-only JS, CSS, UI text, report registry data, or management DOM.
5. Split public/manage UI text and CSS along the new boundary.
6. Move report runtime, report CSS, and report registry loading behind the manage entrypoint.
7. Remove public DOM creation for hidden manage-only controls.
8. Add build-time public and manage nav/tree payloads and switch the index panel to render the route-appropriate tree-ready payload through a payload-agnostic tree renderer.
9. Use the new public nav/tree payload to unblock public index slimming work.
10. Update runtime, reports, index-payload, and JavaScript inventory docs after each implemented slice.

The nav/tree payload work should be part of this lighter-public-install program, but it should come after the entrypoint/shell split.
Doing it first would make the new payloads fit the existing broad runtime, preserving the ambiguity this request is trying to remove.

## Target Entrypoint Graphs

This graph target is based on these baseline sections:

- Current Public Route Loads
- Current Manage Route Loads
- Current Shared Static Import Graph

### Public Entrypoint Graph

`docs-viewer-public.js` should initially boot the current public reader behavior while making the public entry asset explicit.
The first implementation slice may reuse current shared boot/runtime modules where the baseline marks them as mixed, but public route HTML should point at the public entrypoint so later slices can remove mixed imports without changing route templates again.

Target first-slice public graph:

- `docs-viewer-public.js`
- public boot wrapper or shared boot with an explicit public app kind
- route-context and public route-registry resolution from `docs-viewer/config/routes/docs-viewer-public-routes.json`
- public shell path that renders top bar, reader toolbar, index panel, main view, info panel, status, and bookmark row only
- public config read from `docs-viewer/config/defaults/docs-viewer-public-config.json`
- public generated/static docs index, by-id payload, and search index reads
- public reader controllers for route workflow, document rendering, search, bookmarks, info panel, sidebar, hosted metadata info, and panel layout
- shared primitives for access projection, route URLs, asset-version URLs, search normalization, rendering helpers, and tree grouping until nav/tree payloads replace browser-time grouping

Target public graph exclusions:

- `docs-viewer-management*.js`
- `docs-html-import*.js`
- `docs-viewer-scope-lifecycle.js`
- `docs-viewer-management-client.js`
- `modules/source-editor/source-editor.js`
- report runtime, report registry, and report CSS until a named public report is promoted
- management shell/action renderers, management modals, settings, status mutation, context menu, drag/drop, source opening, and local generated-read service probes

### Manage Entrypoint Graph

`docs-viewer-manage.js` should boot the local `/docs/` management shell.
It may continue to compose the current full runtime while the public split proceeds, because manage remains the owner of local-service capabilities and management UI.

Target first-slice manage graph:

- `docs-viewer-manage.js`
- manage boot wrapper or shared boot with an explicit manage app kind
- route-context and manage route-registry resolution from `docs-viewer/config/routes/docs-viewer-routes.json`
- manage shell path with top bar, reader toolbar, management action row, index panel, management shell host, main view, info panel, status, and bookmark row
- manage config read from `docs-viewer/config/defaults/docs-viewer-config.json`
- manage UI text read from the current shared UI text bundle until the UI-text split task replaces it
- generated docs/search reads from local generated assets or loopback generated-read service
- management capability checks and local management client calls
- management actions, modals, source editor, import, settings/status/viewability mutation, scope lifecycle, drag/drop, report runtime, report registry, and report service
- shared reader controllers and primitives where they remain public-safe

Target manage graph exclusions:

- public route registry as a manage boot dependency
- public-only UI text or public-only CSS once those split tasks are complete
- silent fallback to public payloads when local manage data is inaccessible

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Record the public/manage install policy in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary). |
| 2 | done | Complete [Docs Viewer Public/Manage Entrypoint Baseline Inventory](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints-baseline), including current public route loads, manage route loads, shared static import graph, JSON/config/data loads, CSS loads/selectors, public/manage DOM controls, fallback/compatibility paths, and current index tree construction. |
| 3 | done | Define the target public entrypoint import graph and the target manage entrypoint import graph, citing baseline sections: Current Public Route Loads, Current Manage Route Loads, and Current Shared Static Import Graph. |
| 4 | done | Create a public shell renderer or public shell path that renders only public controls and public panel mounts, citing baseline sections: Current Public DOM Controls and Current Public Route Loads. Explicit public entrypoint and public route shell path are in place; manage-only selected-document controls were removed from shared main-view rendering rather than hidden with route-access checks. |
| 5 | done | Create a manage shell renderer or manage shell path that keeps the full current management-capable shell, citing baseline sections: Current Manage DOM Controls and Current Manage Route Loads. |
| 6 | done | Split public and manage UI text so public routes do not load management/import/scope lifecycle copy, including `New scope` and `Delete scope` action/modal copy, citing baseline sections: Current JSON Config And Data Loads and Current Public Route Loads. Public routes now use `docs-viewer/config/ui-text/public.json`; the local manage route uses `docs-viewer/config/ui-text/manage.json`; the retired shared `docs-viewer/config/ui-text/ui-text.json` path was removed rather than kept as a compatibility alias. |
| 7 | done | Correct the CSS asset contract so `docs-viewer/static/css/docs-viewer.css` is the complete basic/public Docs Viewer stylesheet. Folded `docs-viewer/static/css/docs-viewer-base.css` into it, removed the temporary `docs-viewer/static/css/docs-viewer-public.css` asset, made public Jekyll routes load only `docs-viewer/static/css/docs-viewer.css`, and made the local manage shell load `docs-viewer/static/css/docs-viewer.css` plus report and manage-only CSS. This is the first CSS split checkpoint; public-safe manage selector extraction remains task 7a. |
| 7a | done | Extract manage-only CSS into a manage layer after the base asset contract is corrected. Moved local/manage-only controls and layout out of `docs-viewer/static/css/docs-viewer.css` into `docs-viewer/static/css/docs-viewer-manage.css`, including management shell/action/modal styling, imports, source editor, scope lifecycle, settings, drag/drop, draft/non-viewable nav styling, and selected-document status mutation/menu controls. `docs-viewer/static/css/docs-viewer.css` is now public-safe by static selector check; report selectors remain isolated in `docs-viewer/static/css/docs-viewer-reports.css`. |
| 8 | done | Move report runtime, report CSS, and report registry loading behind the manage entrypoint until a specific public report is promoted, citing baseline sections: Current Public Route Loads, Current Manage Route Loads, and Current JSON Config And Data Loads. Report CSS no longer loads on public routes; public route config no longer exposes `report_registry`; the public static import graph excludes report runtime/service/modules; report mounting is supplied by the manage entrypoint through `docs-viewer/runtime/js/docs-viewer-management-document-reports.js`; and the report runtime no longer keeps a silent fallback registry. |
| 9 | done | Extract manage-only selected-document controls from shared main-view rendering into a manage-owned document-actions renderer or equivalent manage shell composition module. The shared main-view renderer must not define, create, or hide `#docsViewerManageEditButton`, `#docsViewerManageSourceButton`, status mutation controls, source-opening controls, or other management-only DOM; citing baseline sections: Current Public DOM Controls and Current CSS Loads And Selectors. |
| 10 | done | Keep shared core modules public-safe and move reusable manage-only behavior into manage-owned modules outside shared core. Route access can guard unavailable states and dynamic manage imports, but shared core must not contain manage-only control definitions that are conditionally omitted for public routes. Selected-document status/edit/source controls, report mounting, the `markdown-source` source-editor hosted-view record, and management shell renderer composition are now manage-owned. The shared app shell accepts an explicit manage-owned renderer bundle rather than importing management action, selected-document action, or management shell renderers itself; citing baseline section: Current Shared Static Import Graph. |
| 11 | done | Audit touched shared modules to remove public/manage mode switches, manage capability switches, hidden manage controls, disabled manage behavior, and access-aware manage-control rendering. The main-view renderer, report-mounting, management-shell refs, source-editor hosted-view registration, and app-shell management renderer import slices are complete. Later touched modules must repeat this audit and move manage-only rendering, event wiring, source/edit/status/report controls, and mutation affordances into manage-owned modules composed above shared primitives. This shared-runtime audit remains owned by this entrypoint-boundary request even when nav/tree payload work is implemented by the public index slimming request; citing baseline sections: Current Shared Static Import Graph and Current Fallback And Compatibility Paths. |
| 12 | done | Remove compatibility aliases and silent fallback paths discovered in touched boot/config/data surfaces, or document a named blocker with removal criteria before adjacent behavior is added, citing baseline section: Current Fallback And Compatibility Paths. Removed route-config camelCase field aliases, object-map route-registry fallback, the report-registry camelCase field fallback, and the report runtime's in-memory fallback registry. Current route-config resolution requires the `docs_viewer_route_config_v1` snake_case contract and `docs_viewer_route_config_registry_v1` registries with a `routes` array. |
| 13 | deferred | Add build-time public and manage nav/tree payloads and switch the index panel to render the route-appropriate tree-ready payload through a payload-agnostic tree renderer after the entrypoint/shell boundary is in place, citing baseline sections: Current Index Tree Construction, Current JSON Config And Data Loads, and Current Shared Static Import Graph. This work is deferred from this entrypoint-split request and will be implemented in [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming). |
| 14 | deferred | Coordinate public nav/tree payload follow-through with [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming), including scope lifecycle `write_generated_outputs` behavior for newly created scopes, citing baseline sections: Current Index Tree Construction and Current JSON Config And Data Loads. This coordination is now owned by the public index slimming request, including scope lifecycle create/delete follow-through for generated nav/tree outputs. |
| 15 | done | Add public-route tests that assert absence of manage-only JS, CSS, UI text, report registry, source editor, import, settings, scope lifecycle, and management controls, citing baseline sections: Current Public Route Loads, Current Public DOM Controls, Current CSS Loads And Selectors, and Current JSON Config And Data Loads. Static ownership checks and public DOM assertions now cover selected-document status/edit/source controls; public-route smoke asserts `docs-viewer/config/ui-text/public.json` is the loaded UI text bundle and contains only the current public reader key. CSS tests now assert public routes load only the basic `docs-viewer/static/css/docs-viewer.css` Docs Viewer stylesheet and do not load report or manage CSS. Public smoke and static tests now assert public routes do not expose or fetch report registry data and do not import report runtime/service/modules. Static public graph tests now assert source-editor hosted-view registration and source-editor module loading stay out of public-safe shared hosted-view defaults. Public-route smoke now asserts public routes do not request `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` and do not render scope lifecycle controls. Static public graph tests now assert public routes do not import the manage shell renderer composition or management shell/action/document-action renderers, and now fail if the public entrypoint static graph imports manage-owned module families, Docs Import modules, report modules, the management client, scope lifecycle, or the source editor. |
| 16 | done | Add manage-route smoke coverage proving current management behavior still loads through the manage entrypoint, citing baseline sections: Current Manage Route Loads and Current Manage DOM Controls. Initial manage smoke coverage proves selected-document edit/source controls still load through the manage entrypoint; manage service smoke now asserts `docs-viewer/config/ui-text/manage.json` carries management, settings, import, and scope lifecycle copy and that current report behavior still runs through the manage entrypoint. Manage entrypoint static checks now prove `markdown-source` hosted-view registration is supplied by `docs-viewer/runtime/js/docs-viewer-management-hosted-views.js`, and manage shell renderer composition is supplied by `docs-viewer/runtime/js/docs-viewer-management-shell-composition.js`. Static import-graph checks now prove the manage entrypoint includes manage-owned shell, document-action, report, hosted-view, report-service, and report-runtime modules. Later slices must extend coverage for settings, imports, and scope lifecycle when those surfaces are materially changed. |
| 17 | done | Update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), [Docs Viewer Reports](/docs/?scope=studio&doc=docs-viewer-reports), and related runtime docs after the split is implemented, citing changed baseline sections and implementation decisions. Runtime boundary, JavaScript inventory, and reports docs now record manage-owned report mounting, public report absence, manage-owned source-editor hosted-view registration, and manage-owned shell renderer composition. Later nav/tree and scope-lifecycle changes are deferred to their owning requests rather than left open in this entrypoint split. |
| 18 | done | Audit and update scope lifecycle create/delete behavior after each asset/config split so `New scope` creates public route files and generated outputs that use the public entrypoint/config/CSS/nav contracts, while `Delete scope` removes only manifest-recorded scope files and never deletes shared public or manage entrypoint assets, citing baseline sections: Current Manage DOM Controls, Current JSON Config And Data Loads, Current CSS Loads And Selectors, and Current Fallback And Compatibility Paths. Current create/delete tests verify public read-only scope creation writes the read-only route include rather than management route markup, local scopes skip public route creation, and delete removes manifest-recorded scope files plus scope config/manifest changes without deleting shared entrypoint, CSS, or config assets. Static template tests pin the read-only route include to the public route registry, public entrypoint default, and basic public CSS contract; scope lifecycle tests now also assert created scope manifests do not record shared public/manage entrypoint, CSS, or route-registry assets as delete-owned scope files. Future nav/tree payload work must extend these lifecycle assertions for new nav outputs. |

## Acceptance Criteria

- public `/library/` and `/analysis/` visible behavior remains unchanged
- local/manage `/docs/` visible behavior remains unchanged
- public routes load a public entrypoint, public shell, public CSS, public UI text, public route config, and public generated data only
- public routes do not request management JS, management CSS, management UI text, report registry data, report modules, import modules, source editor modules, scope lifecycle modules, settings/status mutation modules, or management client modules
- public DOM does not contain management toolbar hosts, hidden edit/source buttons, import hosts, settings controls, scope lifecycle controls, or management-only status controls
- manage route still loads management toolbar, management shell hosts, source editor, imports, reports, settings, status mutation, scope lifecycle, and local-service behavior where currently available
- shared core modules remain reusable without carrying management authority or public route leakage
- shared core modules do not branch on public/manage mode or receive manage capability switches; manage-only behavior is composed above them through manage-owned modules
- public-safe shared renderers do not define manage-only selectors, element ids, action ids, modal/source/import/status mutation controls, or strings such as `Markdown source`, `New scope`, `Delete scope`, and report registry paths
- static source/import tests prove manage-only selected-document controls live in manage-owned modules and are absent from the public entrypoint static import graph
- public and manage index-panel rendering can use route-appropriate tree-ready nav payloads rather than doing full flat-index tree construction in the browser
- `New scope` creates public read-only route files that load the public Docs Viewer entrypoint and public-safe route/config/UI-text/CSS/nav payloads only
- scope lifecycle generated-output options create every required public/manage generated payload introduced by this split, including future nav/tree payloads
- `Delete scope` removes only user-created, manifest-recorded scope files and generated scope outputs; it does not delete or rewrite shared public entrypoint, manage entrypoint, shared core modules, shared CSS, or shared config assets
- scope lifecycle action/menu/modals and copy remain manage-only and are absent from public route asset loads and DOM
- required public assets and manage capabilities fail visibly when missing rather than silently falling back to alternate data paths
- touched boot/config/data surfaces do not retain compatibility aliases or legacy field fallbacks unless a separately approved migration plan has named removal criteria
- public promotion policy is documented and tested with at least one negative assertion that catches accidental public asset widening

## Verification

Docs-only creation of this request needs source review only.

Implementation slices should use proportional checks:

- static import graph check for public and manage entrypoints
- static source checks for public-safe shared modules that assert absence of manage-only selectors, ids, labels, route actions, report registry URLs, local-service clients, source-editor module paths, import workflow paths, settings/status mutation wiring, and scope lifecycle strings
- static ownership checks that assert selected-document edit/source/status controls are defined by manage-owned modules and not by public-safe shared renderers
- public Jekyll smoke for `/library/` and `/analysis/`
- browser network/request assertions for public route asset loads
- DOM assertions for absent public management controls
- manage smoke for `/docs/?mode=manage`
- focused module tests for route-config, shell rendering, UI-text selection, and report gating

Do not rebuild generated docs payloads manually for this request document.
Generated payload updates are handled by the local docs watcher or `bin/local-studio`.

### Verification Log

2026-06-04 close-out boundary tests:

- Added public static import-graph coverage proving `docs-viewer/runtime/js/docs-viewer-public.js` does not statically import manage-owned module families, Docs Import modules, report modules, `docs-viewer-management-client.js`, `docs-viewer-scope-lifecycle.js`, or `modules/source-editor/source-editor.js`.
- Added manage static import-graph coverage proving `docs-viewer/runtime/js/docs-viewer-manage.js` includes manage-owned shell composition, selected-document action rendering, report mounting, hosted-view ownership, report service, and report runtime modules.
- Extended scope lifecycle create coverage so user-created public read-only scopes do not record shared public/manage entrypoints, shared CSS, or route registries as manifest-owned scope files that delete may remove.
- Marked tasks 15-18 done; nav/tree payload work remains deferred to [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming).
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/python/test_docs_management_service.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/python/test_docs_management_service.py`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Generated docs payloads were not manually rebuilt.

2026-06-04 route-config compatibility cleanup:

- `docs-viewer/runtime/js/docs-viewer-route-config.js` now reads only the snake_case route-config contract for route fields, access fields, config URLs, docs paths, panel defaults, hosted views, and hosted-view placeholder text.
- Route-config registries now require `routes` to be an array; the object-map route-registry fallback was removed.
- Required route-config fields now fail visibly when absent instead of resolving as a partial public route config.
- Focused app-shell smoke now asserts camelCase-only route configs fail, object-map registries fail, and nested camelCase panel/hosted-view aliases are ignored.
- Updated `docs-viewer/source/studio/docs-viewer-runtime-boundary.md` and `docs-viewer/source/studio/docs-viewer-javascript-inventory.md`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-route-config.js`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/routes/docs-viewer-routes.json`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/routes/docs-viewer-public-routes.json`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Generated docs payloads were not manually rebuilt.

2026-06-04 shared app-shell manage composition:

- Added `docs-viewer/runtime/js/docs-viewer-management-shell-composition.js` as the manage-owned import bundle for management action rendering, selected-document management actions, and management shell rendering.
- `docs-viewer/runtime/js/docs-viewer-app-shell.js` no longer imports management action, selected-document action, or management shell renderers. It clears available mounts and calls only an explicit manage-owned renderer bundle supplied by the manage entrypoint or manage-specific tests.
- `docs-viewer/runtime/js/docs-viewer-manage.js` now supplies the manage shell renderer bundle during manage app boot; `docs-viewer/runtime/js/docs-viewer-public.js` does not import it.
- `_config.yml` excludes the new manage-owned shell composition module from the public Jekyll build with the other manage-only Docs Viewer modules.
- Static public-entrypoint tests now assert the public static graph excludes `docs-viewer/runtime/js/docs-viewer-management-shell-composition.js`, management action renderers, selected-document action renderers, and management shell renderers.
- Updated `docs-viewer/source/studio/docs-viewer-runtime-boundary.md` and `docs-viewer/source/studio/docs-viewer-javascript-inventory.md`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-management-shell-composition.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-manage.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py docs-viewer/services/docs_viewer_service.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/routes/docs-viewer-public-routes.json`
- Passed: `git diff --check`
- Generated docs payloads were not manually rebuilt.

2026-06-04 scope-lifecycle public boundary assertions:

- Added static template coverage proving `_includes/docs_viewer_readonly_route.html` uses the public route registry, disables management, and delegates to `_includes/docs_viewer_shell.html`, whose default script entrypoint is `docs-viewer/runtime/js/docs-viewer-public.js` and whose Docs Viewer-owned stylesheet is only `docs-viewer/static/css/docs-viewer.css`.
- Extended public read-only browser smoke coverage so `/library/` and `/analysis/` fail if they request `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` or render `#docsViewerManageNewScopeButton`, `#docsViewerManageDeleteScopeButton`, or `.docsViewerScopeLifecycle`.
- Existing scope lifecycle service coverage already verifies public read-only scope creation writes the read-only route include instead of management route markup, local scope creation does not create public routes, and delete removes only manifest-recorded scope files plus scope config/manifest changes.
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_service.py`
- Generated docs payloads were not manually rebuilt.

2026-06-04 source-editor hosted-view manage ownership:

- `docs-viewer/runtime/js/docs-viewer-hosted-views.js` now exposes only public-safe default hosted-view records; `markdown-source` is no longer part of the shared default hosted-view set.
- Added `docs-viewer/runtime/js/docs-viewer-management-hosted-views.js` as the manage-owned hosted-view record owner for `markdown-source` and its lazy source-editor module load.
- `docs-viewer/runtime/js/docs-viewer-manage.js` now supplies manage-owned hosted views during manage app boot; the public entrypoint does not import the manage hosted-view record owner.
- `_config.yml` excludes the new manage-owned hosted-view module from the public Jekyll build with the other manage-only Docs Viewer modules.
- `docs-viewer/runtime/js/docs-viewer-app-shell.js` no longer hardcodes management-shell modal/import/settings element refs; it stores refs returned by the manage shell renderer on the route root after manage shell rendering.
- Static public-entrypoint tests now scan the public static graph for source-editor/import/settings/scope-lifecycle/report ownership leaks and assert the shared app shell excludes manage-shell modal refs.
- Updated `docs-viewer/source/studio/docs-viewer-javascript-inventory.md` and `docs-viewer/source/studio/docs-viewer-runtime-boundary.md`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-hosted-views.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-management-hosted-views.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-manage.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-composition.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `git diff --check`
- Generated docs payloads were not manually rebuilt.

2026-06-04 report-runtime manage gating:

- Public route configs no longer include `config_urls.report_registry` for `/library/` or `/analysis/`.
- `docs-viewer/runtime/js/docs-viewer-document-controller.js` no longer imports report service, report runtime, or report metadata strings; it calls an optional document-extras hook.
- `docs-viewer/runtime/js/docs-viewer-manage.js` supplies manage-owned report mounting through `docs-viewer/runtime/js/docs-viewer-management-document-reports.js`.
- `docs-viewer/runtime/js/docs-viewer-reports.js` now requires an explicit registry URL and no longer falls back to an in-memory registry.
- `docs-viewer/runtime/js/docs-viewer-service-context.js` no longer projects an unused report-registry service surface.
- Updated `docs-viewer/source/studio/docs-viewer-reports.md`, `docs-viewer/source/studio/docs-viewer-runtime-boundary.md`, and `docs-viewer/source/studio/docs-viewer-javascript-inventory.md`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-manage.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-management-document-reports.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-reports.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-service-context.js`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_viewer_service.py docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/routes/docs-viewer-public-routes.json`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/routes/docs-viewer-routes.json`
- Passed: `git diff --check`
- Generated docs payloads were not manually rebuilt.

2026-06-04 selected-document manage-control extraction:

- Passed: `node --check docs-viewer/runtime/js/docs-viewer-main-view-renderer.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_viewer_service.py docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Generated docs payloads were not manually rebuilt.

2026-06-04 UI text split:

- Public route config now points `/library/` and `/analysis/` at `docs-viewer/config/ui-text/public.json`.
- Manage route config now points `/docs/` at `docs-viewer/config/ui-text/manage.json`.
- Retired shared UI text path `docs-viewer/config/ui-text/ui-text.json` was removed; no active runtime, config, service, test, or projection-contract references remain.
- Added public smoke assertions that public routes load the public bundle and that it contains only `recently_added_button`.
- Added manage smoke assertions that the local manage route loads the manage bundle and receives management, settings, import, and scope lifecycle sentinel copy.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-management.js`
- Passed: `node --check docs-viewer/runtime/js/docs-html-import.js`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/public_docs_viewer_readonly.py docs-viewer/tests/smoke/docs_viewer_service_manage.py docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_management_modal.py`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/ui-text/public.json`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/ui-text/manage.json`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/routes/docs-viewer-public-routes.json`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool docs-viewer/config/routes/docs-viewer-routes.json`
- Passed: `$HOME/miniconda3/bin/python3 -m json.tool studio/checks/projection_contract.json`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `git diff --check`
- Generated docs payloads were not manually rebuilt.

2026-06-04 CSS asset-contract correction:

- Folded the former `docs-viewer/static/css/docs-viewer-base.css` contract into `docs-viewer/static/css/docs-viewer.css`.
- Removed the temporary `docs-viewer/static/css/docs-viewer-public.css` asset from the active implementation.
- Public Jekyll routes now load only `docs-viewer/static/css/docs-viewer.css` for Docs Viewer-owned CSS through `_includes/docs_viewer_shell.html`.
- The local manage service shell loads `docs-viewer/static/css/docs-viewer.css`, `docs-viewer/static/css/docs-viewer-reports.css`, and `docs-viewer/static/css/docs-viewer-manage.css`.
- Added public smoke assertions that `/library/` and `/analysis/` load the basic viewer stylesheet and do not request retired base CSS, temporary public CSS, report CSS, or management CSS.
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_viewer_service.py docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `git diff --check`
- Generated docs payloads were not manually rebuilt.

2026-06-04 manage CSS extraction:

- Renamed the active manage-only stylesheet from `docs-viewer/static/css/docs-viewer-management.css` to `docs-viewer/static/css/docs-viewer-manage.css`.
- Moved management shell mount, manage toolbar mount, selected-document status mutation/menu controls, and draft-color styling out of `docs-viewer/static/css/docs-viewer.css` into `docs-viewer/static/css/docs-viewer-manage.css`.
- Added service static denylist entries for retired CSS paths: `docs-viewer/static/css/docs-viewer-base.css`, `docs-viewer/static/css/docs-viewer-management.css`, and `docs-viewer/static/css/docs-viewer-public.css`.
- Added static CSS ownership tests that keep manage/import/source-editor/scope-lifecycle/settings/status mutation/report selectors out of `docs-viewer/static/css/docs-viewer.css` and require the manage selectors in `docs-viewer/static/css/docs-viewer-manage.css`.
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_viewer_service.py docs-viewer/tests/python/test_docs_viewer_service.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py docs-viewer/tests/smoke/docs_viewer_service_manage.py docs-viewer/tests/smoke/docs_viewer_management_modal.py`
- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `git diff --check`
- Generated docs payloads were not manually rebuilt.

## Related Docs

- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer Public/Manage Entrypoint Baseline Inventory](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints-baseline)
- [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming)
- [Docs Viewer Runtime Risk Reduction Request](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-risk-reduction)
- [Docs Viewer Reports](/docs/?scope=studio&doc=docs-viewer-reports)
- [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts)
