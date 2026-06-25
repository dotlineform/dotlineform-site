---
doc_id: studio-runtime
title: Studio Runtime
added_date: 2026-04-24
last_updated: 2026-06-21
parent_id: studio
---
# Studio Runtime

This document describes the current Studio route shell, shared runtime modules, and sibling-app boundaries.
Studio route hosting now runs through the local Python Studio app server for active operational routes.
Use [Local Studio App](/docs/?scope=studio&doc=local-studio-app) for the local server boundary, [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes) for the route inventory, and [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis) for endpoint ownership.
Use [Studio Static Route Template](/docs/?scope=studio&doc=studio-static-route-template) for route template ownership and route script boundaries.

## Route Shell

The local Studio app server owns active Studio route URLs.
For template-backed routes, Python serves `studio/app/frontend/studio-shell.html` as the static outer document.
That document mounts `studio/app/frontend/js/studio-app.js`, which loads runtime config, resolves the active route, renders shared Studio chrome, fetches the configured route template, and then imports the route script.
`studio/app/server/studio/studio_app_config.py` validates the route registry and advertises the runtime view list, and `studio/app/server/studio/studio_app_server.py` dispatches the route.

The browser-rendered Studio shell owns only stable app chrome:

- the `dotlineform studio` home link
- the light/dark theme control
- the page title
- the route content mount populated from the configured static route template

The route template owns stable route DOM such as page roots, panels, forms, search inputs, loading nodes, and dynamic render targets.
The route script owns behavior, route-ready state, data loading, event binding, dynamic repeated UI, modals, and local API calls.
Dynamic values that depend on runtime config are applied by route scripts after config load rather than injected by Python or by JavaScript string shell factories.

The shared top navigation currently has no primary route items; `/studio/` provides the catalogue entry-point link list inside the home route content.
Search is no longer a standalone Studio navigation domain.
Analytics and Data Sharing are served by the standalone Local Analytics app, not by Local Studio navigation.
Catalogue search administration should be reached from the relevant Studio catalogue workflows, while document search administration should stay inside Docs Viewer manage mode.

The public site uses the user-facing `Works` / `Library` header nav.
The Studio shell does not mirror that public navigation; its top-left title returns to `/studio/`.
The intended public-to-Studio crossover is the public footer `studio` link.

Studio does not render page-level Docs Viewer links or carry Docs Viewer route metadata.
Developer documentation is reached directly through the standalone Docs Viewer service.

## Route Registry

Studio route shell metadata lives in `studio/app/frontend/config/studio-config.json` under `app.routes`.
`app.runtime.routes` is not the route registry; it is reserved for local runtime endpoints such as `/health` and `/studio/runtime-config.json`.

Each registered route uses these fields:

- `label`
- `title`
- `path`
- `template`
- `script`
- `nav`
- `shell_type`
- `ready_state_route_id`

Current shell type:

- `html-template` for active Studio routes rendered by the browser shell from `studio/app/frontend/routes/*.html`

`studio/app/server/studio/studio_app_config.py` validates the registry before exposing runtime config.
Validation catches duplicate paths, missing required fields, missing templates or scripts for shell-rendered routes, unsupported shell types, Studio route metadata left in `paths.routes`, and shell-route paths outside `/studio/`.

The runtime config exposes the same records as `app.runtime.views` for existing navigation helpers and smoke tests.

`studio/app/frontend/js/studio-route-registry.js` is the browser-side shell contract helper.
It resolves the active route from `window.location.pathname`, normalizes route fields, and returns a shell contract without rendering or mounting any route.

`studio/app/frontend/js/studio-app.js` is the browser-owned Studio app shell.
For routes marked `shell_type: "html-template"`, Python serves a minimal bootstrap with `<div id="studioApp">`; the browser shell loads runtime config, resolves the active route, renders the shared Studio header/title shell, fetches the configured route template, and then imports the configured route script.
Studio Home, Project State, Bulk Add Work, Catalogue Drafts, Catalogue Field Registry, Studio Works, Catalogue Series, and Catalogue Work use this path.
Their stable body markup lives in `studio/app/frontend/routes/*.html`, and their controllers stay in the configured route scripts.

## Studio Pages

Operational Studio route shells are hosted by the local app.
Active local shells include `/studio/`, operational Studio routes, Studio Works, Catalogue Field Registry, Catalogue Drafts, Catalogue Series, and Catalogue Work.
The maintained mounted-route inventory lives in [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes).
Docs Viewer and Analytics/Data Sharing are sibling local apps with their own route shells.

## Shared Runtime Modules

Shared Studio runtime and wiring currently live in:

- `studio/app/frontend/js/studio-config.js`
  loads the configured runtime URL from `meta[name="dlf-studio-config-url"]`, resolves root-relative paths against the current site base path, and builds configured Studio route URLs while preserving existing query state. Local Studio views use `/studio/runtime-config.json`, which the app server builds from checked-in Studio config plus local runtime endpoints.
- `studio/app/frontend/js/studio-app.js`
  owns the browser-rendered Studio shell and route script import for active Studio-local routes
- `studio/app/frontend/js/studio-route-templates.js`
  fetches and validates configured static route templates before route scripts boot
- `studio/app/frontend/js/studio-navigation.js`
  resolves local Studio route URLs, public preview links, and modal event dispatch
- `studio/app/frontend/js/studio-data.js`
  provides shared JSON loading and common shaping helpers for Studio pages
- `studio/app/frontend/js/studio-transport.js`
  provides local-write endpoint definitions, health probing, and shared JSON POST transport
- `studio/app/frontend/js/studio-route-state.js`
  provides the shared route-root `data-studio-ready` and `data-studio-busy` helpers used by adopted Studio pages for browser smoke tests and future automation
- `studio/app/frontend/routes/*.html`
  own stable route body markup for template-backed Studio routes before the route controllers boot; see [Studio Static Route Template](/docs/?scope=studio&doc=studio-static-route-template)
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

Studio pages participate in the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state) contract.
`studio/app/frontend/js/studio-route-state.js` owns Studio helper functions, and `studio/app/frontend/js/studio-static-route.js` owns static landing/reference readiness.
The route inventory and audit details live in [Route Ready State](/docs/?scope=studio&doc=route-ready-state).

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

- Detailed runner behavior lives in [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio).
- Local server ownership lives in [Local Studio App](/docs/?scope=studio&doc=local-studio-app).
- Endpoint ownership lives in [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis).
