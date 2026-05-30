---
doc_id: studio-runtime
title: Studio Runtime
added_date: 2026-04-24
last_updated: 2026-05-30
parent_id: studio
---
# Studio Runtime

This document describes the current Studio route shell, shared runtime modules, and the way Studio pages connect into the scoped Docs Viewer.
Studio route hosting now runs through the local Python Studio app server for active operational routes.

## Route Shell

Legacy Jekyll-hosted Studio pages use:

- `layout: studio`
- `_layouts/studio.html`

The local Studio app server owns active Studio route shells directly.
For local app routes, `studio/app/server/studio/studio_app_views.py` renders the shell, `studio/app/server/studio/studio_app_config.py` validates the route registry and advertises the runtime view list, and `studio/app/server/studio/studio_app_server.py` dispatches the route.

The legacy Studio route shell provides the shared admin-facing navigation model for any pages not yet migrated. On Studio and Studio Docs routes, `_layouts/default.html` switches the top header nav to:

- `Catalogue`
- `Docs`

Search is no longer a standalone Studio navigation domain.
Analytics and Data Sharing are served by the standalone Local Analytics app, not by Local Studio navigation.
Catalogue search administration should be reached from the Catalogue dashboard, while document search administration should stay inside Docs Viewer manage mode.

The Studio page layout then renders:

- the page title
- the page body content
- an optional `i` link when `page.studio_page_doc` is present

The public site uses the user-facing `Works` / `Library` header nav. The only intended crossover points are:

- the site title at top left, which returns to the public site
- the footer `studio` link, which enters `/studio/`

Studio-originated Library management links should open `/docs/?scope=library&mode=manage` so local management controls are available during admin workflows.

The `i` link is the page-to-doc bridge for Studio. Each page now points to a scoped Docs Viewer URL in the form:

```text
/docs/?scope=studio&doc=<doc_id>
```

This keeps Studio implementation notes in the shared `/docs/` module rather than on page-local routes.

Legacy Jekyll Studio route entry modules no longer use a shared Liquid include.
Operational Studio route shells are hosted by the local app, and remaining Studio-owned Jekyll-shaped demo pages are cleanup targets for the source-tree move.

## Route Registry

Studio route shell metadata lives in `studio/app/frontend/config/studio-config.json` under `app.routes`.
`app.runtime.routes` is not the route registry; it is reserved for local runtime endpoints such as `/health` and `/studio/runtime-config.json`.

Each registered route uses these fields:

- `label`
- `title`
- `path`
- `script` for shell-rendered routes
- `doc_id`
- `nav`
- `shell_type`
- `ready_state_route_id`

Current shell types are:

- `external` for configured peer routes such as Docs Viewer
- `python` for active Studio routes whose route-specific shell HTML is still rendered by Python
- `javascript` for future routes rendered by the browser shell

`studio/app/server/studio/studio_app_config.py` validates the registry before exposing runtime config.
Validation catches duplicate paths, missing required fields, missing scripts for shell-rendered routes, missing `doc_id` values, unsupported shell types, Studio route metadata left in `paths.routes`, and shell-route IDs/paths that do not match a current Local Studio route.

The runtime config exposes the same records as `app.runtime.views` for existing navigation helpers and smoke tests.
Docs Viewer page links are built from `external_links.docs_viewer` plus each route's `doc_id`; `external_links.docs_viewer` must not duplicate per-route doc IDs.

`studio/app/frontend/js/studio-route-registry.js` is the browser-side shell contract helper for the migration.
It resolves the active route from `window.location.pathname`, normalizes route fields for the future shell, and returns a shell contract without rendering or mounting any route.

## Studio Pages

Operational Studio route shells are hosted by the local app.
Active local shells include `/studio/`, operational Studio routes, Studio Works, Catalogue Field Registry, Catalogue Drafts, and the four catalogue editor routes.
Docs Viewer, Analytics/Data Sharing, and UI Catalogue are sibling local apps with their own route shells.

Remaining Jekyll route inventory:

- `ui-catalogue-app/source/demos/index.md`

UI Catalogue demo routes are standalone reference surfaces under `/ui-catalogue/demos/` and are not Studio route shells.

Current page-level doc links:

- Studio Activity -> `/docs/?scope=studio&doc=studio-activity`
- Studio Audits -> `/docs/?scope=studio&doc=studio-audits`
- Bulk Add Work -> `/docs/?scope=studio&doc=bulk-add-work`
- Catalogue Moment Editor -> `/docs/?scope=studio&doc=catalogue-moment-editor`
- Catalogue Work Editor -> `/docs/?scope=studio&doc=catalogue-work-editor`
- Catalogue Work Detail Editor -> `/docs/?scope=studio&doc=catalogue-work-detail-editor`
- Catalogue Series Editor -> `/docs/?scope=studio&doc=catalogue-series-editor`
- Studio Works -> `/docs/?scope=studio&doc=studio-works`
- Studio landing and dashboards -> phased-plan and domain-plan docs
- Library Import -> `/docs/?scope=studio&doc=user-guide-docs-html-import`

## Shared Runtime Modules

Shared Studio runtime and wiring currently live in:

- `assets/studio/js/studio-config.js`
  loads the configured runtime URL from `meta[name="dlf-studio-config-url"]`, resolves root-relative paths against the current site base path, and builds configured Studio route URLs while preserving existing query state. Local Studio views use `/studio/runtime-config.json`, which the app server builds from checked-in Studio config plus local runtime endpoints.
- `assets/studio/js/studio-data.js`
  provides shared JSON loading and common shaping helpers for Studio pages
- `assets/studio/js/studio-transport.js`
  provides local-write endpoint definitions, health probing, and shared JSON POST transport
- `assets/studio/js/studio-route-state.js`
  provides the shared route-root `data-studio-ready` and `data-studio-busy` helpers used by adopted Studio pages for browser smoke tests and future automation
- `assets/studio/js/studio-audits.js`
  powers `/studio/audits/` by probing the local app audit API, listing allowlisted audits, running selected audits, and rendering structured findings
- `assets/studio/js/docs-rebuild-button.js`
  wires the docs rebuild action beside the Studio docs search input
- `assets/studio/js/catalogue-work-fields.js`
  provides shared work-editor field metadata, id normalization, series parsing, draft shaping, and source-record payload helpers for work create/edit surfaces
- `assets/studio/js/catalogue-work-form.js`
  provides Catalogue Work Editor route-local form rendering, series picker behavior, field value synchronization, field availability, and field validation message rendering
- `assets/studio/js/catalogue-work-sections.js`
  provides Catalogue Work Editor route-local rendering for the current-record preview, readiness panel, detail sections, work-owned file/link sections, and summary rail
- `assets/studio/js/catalogue-work-actions.js`
  provides Catalogue Work Editor route-local save, create, build-preview, build, prose import, publication, media-refresh, and delete workflow orchestration
- `assets/studio/js/catalogue-work-selection.js`
  provides Catalogue Work Editor route-local work-id parsing, search matching, suggestion rendering, selection control binding, initial URL selection, and selected-record opening orchestration
- `assets/studio/js/catalogue-series-fields.js`
  provides Catalogue Series Editor route-local field definitions, id normalization, draft shaping, payload shaping, and validation
- `assets/studio/js/catalogue-series-membership.js`
  provides Catalogue Series Editor route-local member-list state, current-member entry shaping, membership dirty checks, changed work-update shaping, saved lookup membership shaping, member row/list rendering, and add/remove/make-primary mutations
- `assets/studio/js/catalogue-moment-fields.js`
  provides Catalogue Moment Editor route-local field definitions, id/filename normalization, draft shaping, source-record payload shaping, and validation
- `assets/studio/js/catalogue-moment-actions.js`
  provides Catalogue Moment Editor route-local save, build-preview, publication, delete, staged prose import, media refresh, public-update outcome, confirmation, and activity-context workflow sequencing
- `assets/studio/js/catalogue-moment-selection.js`
  provides Catalogue Moment Editor route-local search matching, suggestion rendering, selection control binding, Open button resolution, and initial route selection
- `assets/studio/js/catalogue-moment-form.js`
  provides Catalogue Moment Editor route-local field DOM construction, field value reads/writes, readonly value display, and validation message rendering
- `assets/studio/js/catalogue-moment-sections.js`
  provides Catalogue Moment Editor route-local normal edit summary rendering, readiness rendering, and build-impact text rendering
- `assets/studio/js/catalogue-moment-import.js`
  provides Catalogue Moment Editor route-local staged-file URL state, import metadata reads, preview seeding, import preview/apply sequencing, import detail rendering, and import control state

Current page controllers:

- `assets/studio/js/activity-log.js`
- `assets/studio/js/studio-audits.js`
- `docs-viewer/runtime/js/docs-html-import.js`
- `assets/studio/js/bulk-add-work.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/studio-works.js`

Analytics and Data Sharing route controllers now live under `analytics-app/app/frontend/js/` and are served by the standalone Local Analytics app.

Retired catalogue create routes:

- `/studio/catalogue-new-work/`, `/studio/catalogue-new-work-detail/`, and `/studio/catalogue-new-series/` are no longer published Studio pages.
- The old standalone controllers `assets/studio/js/catalogue-new-work-editor.js`, `assets/studio/js/catalogue-new-work-detail-editor.js`, and `assets/studio/js/catalogue-new-series-editor.js` have been removed.
- Active create behavior now lives in `assets/studio/js/catalogue-work-editor.js`, `assets/studio/js/catalogue-work-detail-editor.js`, and `assets/studio/js/catalogue-series-editor.js`.

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

`assets/studio/js/studio-route-state.js` owns the helper functions for setting these attributes and dispatching the optional `studio:ready` event. The current route inventory and implementation rules are documented in [Studio Ready State](/docs/?scope=studio&doc=studio-ready-state).

Static landing and reference routes use `assets/studio/js/studio-static-route.js` to mark the page ready after DOM load with `data-studio-mode="landing"` or `data-studio-mode="reference"`. These static route attributes are intentionally small framework markers for future route development.

## Relation to `/docs/`

Studio no longer owns a separate documentation route. Its docs are served by the shared Docs Viewer, which also serves other docs scopes.

Current Studio usage of the Docs Viewer:

- Studio section docs live in `docs-viewer/source/studio/`
- `docs-viewer/build/build_docs.rb` builds the Studio docs payload into the Studio docs scope
- `<DOCS_VIEWER_BASE_URL>/docs/?scope=studio&doc=<doc_id>` opens those docs in the standalone Docs Viewer service
- Studio page `i` links use those scoped URLs directly
- the Docs Viewer service owns manage-mode actions such as rebuild beside the docs search input

This means Studio documentation changes must stay aligned with the shared Docs Viewer behavior documented in **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** and **[Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)**.

## Local Development Boundary

`bin/local-studio` is the current Studio route runner.

What it runs before starting long-lived services:

- required port preflight for the local Studio app
- optional docs/docs-search rebuilds for scopes listed in `DOCS_STARTUP_REBUILD_SCOPES`
- `$HOME/miniconda3/bin/python3 studio/services/catalogue/export_catalogue_lookup.py --write`

What it starts:

- `studio/app/server/studio/studio_app_server.py`
- `docs-viewer/services/docs_live_rebuild_watcher.py`

What it does not start:

- catalogue/search regeneration scripts
- the retired standalone tag write server
- the standalone Docs Viewer service; use `docs-viewer/bin/docs-viewer` directly or `bin/local-all` for all local services
- the retired standalone Audit Service HTTP wrapper

Current local generated Studio feeds surfaced through this runtime:

- unified Studio activity via `GET /studio/api/catalogue/read?key=activity_log`

Current mutable catalogue data surfaced through this runtime:

- catalogue source records and catalogue lookup/search records are read through Local Studio catalogue API routes backed by `studio/app/server/studio/studio_catalogue_api.py`
- Jekyll excludes `assets/studio/data/catalogue/`, `assets/studio/data/catalogue_lookup/`, `var/`, and local `logs/` from the served site so local source/lookup/activity writes do not trigger an extra Jekyll regeneration pass
- catalogue editors, Catalogue Drafts, and Studio Activity show their existing unavailable/load-failed states instead of reading stale static source JSON

Current Docs Viewer service integration surfaced through this runtime:

- `POST <DOCS_VIEWER_BASE_URL>/docs/broken-links`
- `POST <DOCS_VIEWER_BASE_URL>/docs/rebuild`

Current localhost audit integration surfaced through this runtime:

- `GET /studio/api/audits/audits`
- `POST /studio/api/audits/audits/run`

Current catalogue integration surfaced through this runtime:

- `GET /studio/api/catalogue/health`
- `GET /studio/api/catalogue/read`
- editor save/create/delete/publication/build/prose-import/moment API routes under `/studio/api/catalogue/...`
- workbook import routes under `/studio/api/catalogue/import-preview` and `/studio/api/catalogue/import-apply`
- `POST /studio/api/catalogue/project-state-report`

The runner is therefore sufficient for route-shell and write-flow testing, but not a full content-generation pipeline.

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
