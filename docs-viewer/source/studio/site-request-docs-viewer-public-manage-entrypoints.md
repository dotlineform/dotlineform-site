---
doc_id: site-request-docs-viewer-public-manage-entrypoints
title: Docs Viewer Public/Manage Entrypoint Split Request
added_date: 2026-06-04
last_updated: 2026-06-04
ui_status: in-progress
parent_id: change-requests
---
# Docs Viewer Public/Manage Entrypoint Split Request

Status:

- in progress

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
| `docs-viewer/config/ui-text/ui-text.json` | Shared UI text, currently includes public and manage copy. | New public UI text bundle, for example `docs-viewer/config/ui-text/public.json`. | New manage UI text bundle, for example `docs-viewer/config/ui-text/manage.json`. | Split. |
| `docs-viewer/config/reports/reports.json` | Source report registry. | No public projection unless a specific public report is promoted. | Keep as report source registry for manage/report tooling. | Manage-owned until promotion. |
| `assets/data/docs/reports.json` | Browser-visible report registry projection. | Do not load on public routes until a specific public report is promoted; later use a public report projection if needed. | Keep for manage report runtime. | Move behind manage entrypoint. |
| `assets/data/docs/scopes/<scope>/index.json` | Public flat docs index used for tree construction and document selection. | Narrow or replace for public runtime after nav/tree payload exists. | Not used by manage except as static public data. | Slim after nav/tree slice. |
| Public nav/tree payload | Not present. | New tree-ready payload using the shared tree shape, for example `assets/data/docs/scopes/<scope>/nav.json`. | None. | New. |
| `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json` | Public rendered document payload. | Keep as selected-document payload, with reader-facing metadata only where possible. | Manage can still read public by-id payloads when viewing public scopes, but manage source/edit data comes from manage endpoints. | Mostly unchanged. |
| `assets/data/search/<scope>/index.json` | Public docs search index for public scopes. | Keep if public search remains enabled. | Manage uses local generated search for local scopes. | Mostly unchanged. |
| `docs-viewer/generated/docs/<scope>/index.json` | Local/manage generated docs index for local scopes such as `studio`. | None. | Narrow or replace for manage navigation after manage nav/tree payload exists; keep only if other manage features still require the rich flat projection. | Review after nav/tree slice. |
| Manage nav/tree payload | Not present. | None. | New richer tree-ready payload using the same shared tree shape, for example `docs-viewer/generated/docs/<scope>/nav.json`; include manage-only fields only after confirming context-menu, drag/drop, status, or viewability needs. | New. |
| `docs-viewer/generated/search/<scope>/index.json` | Local/manage generated search index for local scopes such as `studio`. | None. | Keep manage/local search projection. | Manage-owned. |
| `docs-viewer/static/css/docs-viewer-base.css` | Docs Viewer base tokens and utilities. | Keep only if it remains public-safe. | Manage can also load it. | Shared public-safe. |
| `docs-viewer/static/css/docs-viewer.css` | Shared viewer, panel, search, toolbar, and some manage-adjacent control styling. | Split or narrow to public reader/index/main/info/search styles, for example `docs-viewer-public.css`. | Manage can load public-safe reader CSS plus manage-only CSS. | Split/narrow. |
| `docs-viewer/static/css/docs-viewer-reports.css` | Report styling currently loaded by the shared shell. | Do not load until a specific public report is promoted; then load only the minimum public report CSS. | Load through the manage entrypoint/report runtime. | Move behind manage entrypoint. |
| `docs-viewer/static/css/docs-viewer-management.css` | Management-only shell, action, modal, and workflow styling. | None. | Keep manage-only. | Unchanged. |
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
| 4 | in progress | Create a public shell renderer or public shell path that renders only public controls and public panel mounts, citing baseline sections: Current Public DOM Controls and Current Public Route Loads. Explicit public entrypoint and public route shell path are in place; boot-created hidden manage controls remain task 9 follow-through. |
| 5 | done | Create a manage shell renderer or manage shell path that keeps the full current management-capable shell, citing baseline sections: Current Manage DOM Controls and Current Manage Route Loads. |
| 6 | planned | Split public and manage UI text so public routes do not load management/import/scope lifecycle copy, citing baseline sections: Current JSON Config And Data Loads and Current Public Route Loads. |
| 7 | planned | Split public and manage CSS loading so public routes do not load report or management styling unless the specific public surface needs it, citing baseline sections: Current CSS Loads And Selectors and Current Public Route Loads. |
| 8 | planned | Move report runtime, report CSS, and report registry loading behind the manage entrypoint until a specific public report is promoted, citing baseline sections: Current Public Route Loads, Current Manage Route Loads, and Current JSON Config And Data Loads. |
| 9 | planned | Ensure public main-view rendering omits management-only hidden controls rather than rendering disabled or hidden manage DOM, citing baseline sections: Current Public DOM Controls and Current CSS Loads And Selectors. |
| 10 | planned | Keep shared core modules public-safe and move reusable manage-only behavior into manage-owned modules outside shared core, citing baseline section: Current Shared Static Import Graph. |
| 11 | planned | Audit touched shared modules to remove public/manage mode switches, manage capability switches, hidden manage controls, and disabled manage behavior; move manage-only behavior into manage-owned modules, citing baseline sections: Current Shared Static Import Graph and Current Fallback And Compatibility Paths. |
| 12 | planned | Remove compatibility aliases and silent fallback paths discovered in touched boot/config/data surfaces, or document a named blocker with removal criteria before adjacent behavior is added, citing baseline section: Current Fallback And Compatibility Paths. |
| 13 | planned | Add build-time public and manage nav/tree payloads and switch the index panel to render the route-appropriate tree-ready payload through a payload-agnostic tree renderer after the entrypoint/shell boundary is in place, citing baseline sections: Current Index Tree Construction, Current JSON Config And Data Loads, and Current Shared Static Import Graph. |
| 14 | planned | Coordinate public nav/tree payload follow-through with [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming), citing baseline sections: Current Index Tree Construction and Current JSON Config And Data Loads. |
| 15 | planned | Add public-route tests that assert absence of manage-only JS, CSS, UI text, report registry, source editor, import, settings, scope lifecycle, and management controls, citing baseline sections: Current Public Route Loads, Current Public DOM Controls, Current CSS Loads And Selectors, and Current JSON Config And Data Loads. |
| 16 | planned | Add manage-route smoke coverage proving current management behavior still loads through the manage entrypoint, citing baseline sections: Current Manage Route Loads and Current Manage DOM Controls. |
| 17 | planned | Update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), [Docs Viewer Reports](/docs/?scope=studio&doc=docs-viewer-reports), and related runtime docs after the split is implemented, citing changed baseline sections and implementation decisions. |

## Acceptance Criteria

- public `/library/` and `/analysis/` visible behavior remains unchanged
- local/manage `/docs/` visible behavior remains unchanged
- public routes load a public entrypoint, public shell, public CSS, public UI text, public route config, and public generated data only
- public routes do not request management JS, management CSS, management UI text, report registry data, report modules, import modules, source editor modules, scope lifecycle modules, settings/status mutation modules, or management client modules
- public DOM does not contain management toolbar hosts, hidden edit/source buttons, import hosts, settings controls, scope lifecycle controls, or management-only status controls
- manage route still loads management toolbar, management shell hosts, source editor, imports, reports, settings, status mutation, scope lifecycle, and local-service behavior where currently available
- shared core modules remain reusable without carrying management authority or public route leakage
- shared core modules do not branch on public/manage mode or receive manage capability switches; manage-only behavior is composed above them through manage-owned modules
- public and manage index-panel rendering can use route-appropriate tree-ready nav payloads rather than doing full flat-index tree construction in the browser
- required public assets and manage capabilities fail visibly when missing rather than silently falling back to alternate data paths
- touched boot/config/data surfaces do not retain compatibility aliases or legacy field fallbacks unless a separately approved migration plan has named removal criteria
- public promotion policy is documented and tested with at least one negative assertion that catches accidental public asset widening

## Verification

Docs-only creation of this request needs source review only.

Implementation slices should use proportional checks:

- static import graph check for public and manage entrypoints
- public Jekyll smoke for `/library/` and `/analysis/`
- browser network/request assertions for public route asset loads
- DOM assertions for absent public management controls
- manage smoke for `/docs/?mode=manage`
- focused module tests for route-config, shell rendering, UI-text selection, and report gating

Do not rebuild generated docs payloads manually for this request document.
Generated payload updates are handled by the local docs watcher or `bin/local-studio`.

## Related Docs

- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer Public/Manage Entrypoint Baseline Inventory](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints-baseline)
- [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming)
- [Docs Viewer Runtime Risk Reduction Request](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-risk-reduction)
- [Docs Viewer Reports](/docs/?scope=studio&doc=docs-viewer-reports)
- [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts)
