---
doc_id: studio-runtime
title: Studio Runtime
added_date: 2026-04-24
last_updated: 2026-06-02
parent_id: studio
---
# Studio Runtime

This document describes the current Studio route shell, shared runtime modules, and sibling-app boundaries.
Studio route hosting now runs through the local Python Studio app server for active operational routes.
Use [Local Studio App](/docs/?scope=studio&doc=local-studio-app) for the local server boundary, [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes) for the route inventory, and [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis) for endpoint ownership.

## Route Shell

The local Studio app server owns active Studio route URLs.
For JavaScript-shell routes, Python serves a generic bootstrap and `studio/app/frontend/js/studio-app.js` renders the shared shell and route body.
`studio/app/server/studio/studio_app_config.py` validates the route registry and advertises the runtime view list, and `studio/app/server/studio/studio_app_server.py` dispatches the route.

The browser-rendered Studio shell provides the shared admin-facing navigation model:

- `Catalogue`
- `Docs`
- `Admin`

Search is no longer a standalone Studio navigation domain.
Analytics and Data Sharing are served by the standalone Local Analytics app, not by Local Studio navigation.
Catalogue search administration should be reached from the Catalogue dashboard, while document search administration should stay inside Docs Viewer manage mode.

The Studio shell renders:

- the page title
- the route body from the route-local shell module

The public site uses the user-facing `Works` / `Library` header nav. The only intended crossover points are:

- the site title at top left, which returns to the public site
- the footer `studio` link, which enters `/studio/`

Studio does not render page-level Docs Viewer links or carry Docs Viewer route metadata.
Developer documentation is reached directly through the standalone Docs Viewer service.

## Route Registry

Studio route shell metadata lives in `studio/app/frontend/config/studio-config.json` under `app.routes`.
`app.runtime.routes` is not the route registry; it is reserved for local runtime endpoints such as `/health` and `/studio/runtime-config.json`.

Each registered route uses these fields:

- `label`
- `title`
- `path`
- `script` for shell-rendered routes
- `nav`
- `shell_type`
- `ready_state_route_id`

Current shell type:

- `javascript` for active Studio routes rendered by the browser shell

`studio/app/server/studio/studio_app_config.py` validates the registry before exposing runtime config.
Validation catches duplicate paths, missing required fields, missing scripts for shell-rendered routes, unsupported shell types, Studio route metadata left in `paths.routes`, and shell-route IDs/paths that do not match a current Local Studio route.

The runtime config exposes the same records as `app.runtime.views` for existing navigation helpers and smoke tests.

`studio/app/frontend/js/studio-route-registry.js` is the browser-side shell contract helper for the migration.
It resolves the active route from `window.location.pathname`, normalizes route fields for the future shell, and returns a shell contract without rendering or mounting any route.

`studio/app/frontend/js/studio-app.js` is the browser-owned Studio app shell.
For routes marked `shell_type: "javascript"`, Python serves a minimal bootstrap with `<div id="studioApp">`; the browser shell loads runtime config, resolves the active route, renders the shared Studio header/title shell, asks the route-local body renderer for markup, and then imports the configured route script.
Project State, Studio Audits, Studio Activity, Bulk Add Work, Catalogue Drafts, Catalogue Field Registry, Studio Works, and the Catalogue editor family use this path.
Their body markup lives in route-local `*-shell.js` modules, and their existing controllers stay in the configured route scripts.

## Studio Pages

Operational Studio route shells are hosted by the local app.
Active local shells include `/studio/`, operational Studio routes, Studio Works, Catalogue Field Registry, Catalogue Drafts, and the four catalogue editor routes.
The maintained mounted-route inventory lives in [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes).
Docs Viewer, Analytics/Data Sharing, and UI Catalogue are sibling local apps with their own route shells.

UI Catalogue demo routes are standalone reference surfaces under `/admin/ui-catalogue/demos/` and are not Studio route shells.

## Shared Runtime Modules

Shared Studio runtime and wiring currently live in:

- `studio/app/frontend/js/studio-config.js`
  loads the configured runtime URL from `meta[name="dlf-studio-config-url"]`, resolves root-relative paths against the current site base path, and builds configured Studio route URLs while preserving existing query state. Local Studio views use `/studio/runtime-config.json`, which the app server builds from checked-in Studio config plus local runtime endpoints.
- `studio/app/frontend/js/studio-app.js`
  owns the browser-rendered Studio shell and route script import for active Studio-local routes
- `studio/app/frontend/js/studio-route-body-renderers.js`
  owns the route-id to route-body-renderer mapping for JavaScript-shell routes
- `studio/app/frontend/js/studio-navigation.js`
  resolves local Studio route URLs, public preview links, and modal event dispatch
- `studio/app/frontend/js/studio-data.js`
  provides shared JSON loading and common shaping helpers for Studio pages
- `studio/app/frontend/js/studio-transport.js`
  provides local-write endpoint definitions, health probing, and shared JSON POST transport
- `studio/app/frontend/js/studio-route-state.js`
  provides the shared route-root `data-studio-ready` and `data-studio-busy` helpers used by adopted Studio pages for browser smoke tests and future automation
- `studio/app/frontend/js/*-shell.js`
  own static route body markup for the JavaScript shell before the existing side-effect route controllers boot
- `studio/app/frontend/js/catalogue-*-editor.js` and focused sibling modules
  own catalogue editor route orchestration, forms, selection flows, modals, actions, and section rendering

Analytics and Data Sharing route controllers now live under `analytics-app/app/frontend/js/` and are served by the standalone Local Analytics app.

Retired catalogue create routes:

- `/studio/catalogue-new-work/`, `/studio/catalogue-new-work-detail/`, and `/studio/catalogue-new-series/` are no longer published Studio pages.
- The old standalone controllers `site/assets/studio/js/catalogue-new-work-editor.js`, `site/assets/studio/js/catalogue-new-work-detail-editor.js`, and `site/assets/studio/js/catalogue-new-series-editor.js` have been removed.
- Active create behavior now lives in `studio/app/frontend/js/catalogue-work-editor.js`, `studio/app/frontend/js/catalogue-work-detail-editor.js`, and `studio/app/frontend/js/catalogue-series-editor.js`.

Studio controller splits that are already live:

- Catalogue Work Editor:
  - `catalogue-work-editor.js`
  - `catalogue-work-fields.js`
  - `catalogue-work-form.js`
  - `catalogue-work-sections.js`
  - `catalogue-work-actions.js`
  - `catalogue-work-selection.js`
- Catalogue Series Editor:
  - `catalogue-series-editor.js`
  - `catalogue-series-fields.js`
  - `catalogue-series-membership.js`
- Catalogue Moment Editor:
  - `catalogue-moment-editor.js`
  - `catalogue-moment-fields.js`
  - `catalogue-moment-actions.js`
  - `catalogue-moment-selection.js`
  - `catalogue-moment-form.js`
  - `catalogue-moment-sections.js`
  - `catalogue-moment-import.js`

## Route Ready State

Studio pages can expose a shared machine-readable route state on their main page root.

Shared attributes:

- `data-studio-ready="false"` while initial route data and first render are still loading
- `data-studio-ready="true"` after the route has reached its initial stable interaction state
- `data-studio-busy="true"` while a route-level command is running
- `data-studio-busy="false"` when no route-level command is running

Optional route detail attributes:

- `data-studio-route`
- `data-studio-mode`
- `data-studio-service`
- `data-studio-record-loaded`

`studio/app/frontend/js/studio-route-state.js` owns the helper functions for setting these attributes and dispatching the optional `studio:ready` event. The current route inventory and implementation rules are documented in [Studio Ready State](/docs/?scope=studio&doc=studio-ready-state).

Static landing and reference routes use `studio/app/frontend/js/studio-static-route.js` to mark the page ready after DOM load with `data-studio-mode="landing"` or `data-studio-mode="reference"`. These static route attributes are intentionally small framework markers for future route development.

## Relation to `/docs/`

Studio no longer owns a separate documentation route and does not link to Docs Viewer from its runtime shell.
Studio developer docs remain authored under the Studio docs scope, but `/docs/` is a self-contained developer resource served by the standalone Docs Viewer service.

Current boundary:

- Studio section docs live in `docs-viewer/source/studio/`
- `docs-viewer/build/build_docs.py` builds the Studio docs payload into the Studio docs scope
- the standalone Docs Viewer service serves `/docs/` when developer documentation is needed
- Local Studio does not expose Docs Viewer external-link config, route doc IDs, static/runtime assets, generated-data passthroughs, or API adapters

This means Studio documentation changes must stay aligned with the shared Docs Viewer behavior documented in **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** and **[Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)**.

## Local Development Boundary

`bin/local-studio` is the current Studio route runner.

It starts the local Studio app server and the docs live rebuild watcher.
It does not start public-site preview, Local Analytics, UI Catalogue, or the standalone Docs Viewer service; use each runner directly or `bin/local-all` for all local services.

The runner is sufficient for route-shell and Studio write-flow testing, but not a full content-generation pipeline.
Detailed runner behavior lives in [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio).
Local server ownership lives in [Local Studio App](/docs/?scope=studio&doc=local-studio-app).
Endpoint ownership lives in [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis).

## Current Catalogue UI Baseline

After Phase 3, the current Catalogue shell conventions are:

- Catalogue-domain pages no longer render a persistent page-link strip above the editor content
- work, series, and detail editors now use the right-hand summary rail for readiness state as well as current-record context
- work and detail editors now place compact media previews at the top of that summary rail
- work detail rows on the work editor now use thumbnail-led navigation rather than text-only rows
- the Catalogue dashboard uses grouped directional link lists rather than card panels
- metadata editors use a shared single-column row layout with labels on the left
- Catalogue Drafts is a sortable draft-record list and links directly into work, series, detail, and moment editors
- work-owned downloads and links are edited from the work editor rather than standalone child-record pages

Current operational reporting conventions are:

- `Studio Activity` is the unified surface for covered Studio save, create, delete, publication, import, report, audit, tag, docs, lookup, search, and build effects
