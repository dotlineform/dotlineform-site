---
doc_id: site-request-docs-viewer-public-manage-entrypoints
title: Docs Viewer Public/Manage Entrypoint Split Request
added_date: 2026-06-04
last_updated: 2026-06-04
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Public/Manage Entrypoint Split Request

Status:

- draft

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
- keep common infrastructure in shared core modules rather than duplicating route parsing, generated-data reads, tree helpers, search helpers, URL helpers, and renderer primitives
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

Good shared-core candidates:

- docs index normalization
- generated-data read helpers that do not probe local services unless called through a manage service context
- route and URL helpers
- tree helpers
- search normalization/scoring
- result rendering primitives
- asset-version URL helpers
- public-safe hosted-view context helpers
- generic DOM projection helpers with no manage-only controls

Poor shared-core candidates:

- management client calls
- local-service capability probing
- source editor services
- imports and write workflows
- report modules that read local endpoints
- scope lifecycle workflows
- management modals, menus, settings, status mutation, or source-opening behavior
- UI text bundles that include manage-only copy

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

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Record the public/manage install policy in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary). |
| 2 | planned | Inventory current public route loads for JS modules, CSS files, route config, UI text, report registry, generated docs data, and generated search data. |
| 3 | planned | Define the target public entrypoint import graph and the target manage entrypoint import graph. |
| 4 | planned | Create a public shell renderer or public shell path that renders only public controls and public panel mounts. |
| 5 | planned | Create a manage shell renderer or manage shell path that keeps the full current management-capable shell. |
| 6 | planned | Split public and manage UI text so public routes do not load management/import/scope lifecycle copy. |
| 7 | planned | Split public and manage CSS loading so public routes do not load report or management styling unless the specific public surface needs it. |
| 8 | planned | Move report runtime, report CSS, and report registry loading behind the manage entrypoint until a specific public report is promoted. |
| 9 | planned | Ensure public main-view rendering omits management-only hidden controls rather than rendering disabled or hidden manage DOM. |
| 10 | planned | Keep shared core modules public-safe and move reusable manage-only behavior into manage-owned modules outside shared core. |
| 11 | planned | Add public-route tests that assert absence of manage-only JS, CSS, UI text, report registry, source editor, import, settings, scope lifecycle, and management controls. |
| 12 | planned | Add manage-route smoke coverage proving current management behavior still loads through the manage entrypoint. |
| 13 | planned | Update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), [Docs Viewer Reports](/docs/?scope=studio&doc=docs-viewer-reports), and related runtime docs after the split is implemented. |

## Acceptance Criteria

- public `/library/` and `/analysis/` visible behavior remains unchanged
- local/manage `/docs/` visible behavior remains unchanged
- public routes load a public entrypoint, public shell, public CSS, public UI text, public route config, and public generated data only
- public routes do not request management JS, management CSS, management UI text, report registry data, report modules, import modules, source editor modules, scope lifecycle modules, settings/status mutation modules, or management client modules
- public DOM does not contain management toolbar hosts, hidden edit/source buttons, import hosts, settings controls, scope lifecycle controls, or management-only status controls
- manage route still loads management toolbar, management shell hosts, source editor, imports, reports, settings, status mutation, scope lifecycle, and local-service behavior where currently available
- shared core modules remain reusable without carrying management authority or public route leakage
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
- [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming)
- [Docs Viewer Runtime Risk Reduction Request](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-risk-reduction)
- [Docs Viewer Reports](/docs/?scope=studio&doc=docs-viewer-reports)
- [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts)
