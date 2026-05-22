---
doc_id: studio-runtime
title: Studio Runtime
added_date: 2026-04-24
last_updated: 2026-05-22
parent_id: studio
sort_order: 2000
---
# Studio Runtime

This document describes the current Studio route shell, shared runtime modules, and the way Studio pages connect into the scoped Docs Viewer.
Studio route hosting is migrating from Jekyll shells to the local Python Studio app server.

## Route Shell

Legacy Jekyll-hosted Studio pages use:

- `layout: studio`
- `_layouts/studio.html`

The local Studio app server now owns many active Studio route shells directly.
For migrated routes, `scripts/studio/studio_app_views.py` renders the shell, `scripts/studio/studio_app_config.py` advertises the runtime view registry, and `scripts/studio/studio_app_server.py` dispatches the route.

The legacy Studio route shell provides the shared admin-facing navigation model for any pages not yet migrated. On Studio and Studio Docs routes, `_layouts/default.html` switches the top header nav to:

- `Catalogue`
- `Analytics`
- `Docs`

Search is no longer a standalone Studio navigation domain. Catalogue search administration should be reached from the Catalogue dashboard, while document search administration should stay inside Docs Viewer manage mode.

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

Legacy Jekyll route entry modules are loaded through `_includes/studio_module_script.html`, for example:

```liquid
{% include studio_module_script.html src='/assets/studio/js/catalogue-work-editor.js' %}
```

The include appends the same `site.time`-derived asset-version query used by the default layout's shared assets.
Route pages own which entry module they load; route controllers do not own cache-busting for their own entry script.

## Studio Pages

Current Jekyll route inventory is shrinking as local app views replace route shells.
Active migrated shells include `/studio/`, `/docs/`, analytics tag routes, operational Studio routes, Studio Works, Catalogue Field Registry, and the four catalogue editor routes.

Remaining Jekyll route inventory:

- `studio/catalogue/index.md`
- `studio/analytics/index.md`
- `studio/catalogue-status/index.md`
- `studio/docs-broken-links/index.md`
- `studio/data-sharing/index.md`
- `studio/data-sharing/prepare/index.md`
- `studio/data-sharing/review/index.md`
- `studio/ui-catalogue/demos/index.md`

Current page-level doc links:

- Tag Groups -> `/docs/?scope=studio&doc=tag-groups`
- Studio Activity -> `/docs/?scope=studio&doc=studio-activity`
- Docs Broken Links -> `/docs/?scope=studio&doc=docs-broken-links`
- Studio Audits -> `/docs/?scope=studio&doc=studio-audits`
- Bulk Add Work -> `/docs/?scope=studio&doc=bulk-add-work`
- Catalogue Moment Editor -> `/docs/?scope=studio&doc=catalogue-moment-editor`
- Catalogue Work Editor -> `/docs/?scope=studio&doc=catalogue-work-editor`
- Catalogue Work Detail Editor -> `/docs/?scope=studio&doc=catalogue-work-detail-editor`
- Catalogue Series Editor -> `/docs/?scope=studio&doc=catalogue-series-editor`
- Tag Registry -> `/docs/?scope=studio&doc=tag-registry`
- Tag Aliases -> `/docs/?scope=studio&doc=tag-aliases`
- Series Tags -> `/docs/?scope=studio&doc=series-tags`
- Series Tag Editor -> `/docs/?scope=studio&doc=tag-editor`
- Studio Works -> `/docs/?scope=studio&doc=studio-works`
- Studio landing and dashboards -> phased-plan and domain-plan docs
- Library Import -> `/docs/?scope=studio&doc=user-guide-docs-html-import`

## Shared Runtime Modules

Shared Studio runtime and wiring currently live in:

- `assets/studio/js/studio-config.js`
  loads `assets/studio/data/studio_config.json`, merges defaults, resolves root-relative paths against the current site base path, and builds configured Studio route URLs while preserving existing query state
- `assets/studio/js/studio-data.js`
  provides shared JSON loading and common shaping helpers for Studio pages
- `assets/studio/js/studio-transport.js`
  provides local-write endpoint definitions, health probing, and shared JSON POST transport
- `assets/studio/js/studio-route-state.js`
  provides the shared route-root `data-studio-ready` and `data-studio-busy` helpers used by adopted Studio pages for browser smoke tests and future automation
- `assets/studio/js/studio-dashboard.js`
  hydrates lightweight dashboard metrics for the new domain landing pages
- `assets/studio/js/studio-audits.js`
  powers `/studio/audits/` by probing the local audit service, listing allowlisted audits, running selected audits, and rendering structured findings
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
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/studio-audits.js`
- `assets/docs-viewer/js/docs-html-import.js`
- `assets/studio/js/bulk-add-work.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/tag-groups.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/studio-works.js`

Retired catalogue create routes:

- `/studio/catalogue-new-work/`, `/studio/catalogue-new-work-detail/`, and `/studio/catalogue-new-series/` are no longer published Studio pages.
- The old standalone controllers `assets/studio/js/catalogue-new-work-editor.js`, `assets/studio/js/catalogue-new-work-detail-editor.js`, and `assets/studio/js/catalogue-new-series-editor.js` have been removed.
- Active create behavior now lives in `assets/studio/js/catalogue-work-editor.js`, `assets/studio/js/catalogue-work-detail-editor.js`, and `assets/studio/js/catalogue-series-editor.js`.

Controller splits that are already live:

- Tag Editor:
  - `tag-studio.js`
  - `tag-studio-domain.js`
  - `tag-studio-save.js`
- Tag Registry:
  - `tag-registry.js`
  - `tag-registry-domain.js`
  - `tag-registry-save.js`
  - `tag-registry-service.js`
- Tag Aliases:
  - `tag-aliases.js`
  - `tag-aliases-domain.js`
  - `tag-aliases-save.js`
  - `tag-aliases-service.js`
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

Dashboard routes use `assets/studio/js/studio-dashboard.js` to set `data-studio-busy="true"` while metric hydration runs, then mark the route ready after the metric reads settle. Static landing and reference routes use `assets/studio/js/studio-static-route.js` to mark the page ready after DOM load with `data-studio-mode="landing"` or `data-studio-mode="reference"`. These static route attributes are intentionally small framework markers for future route development.

## Relation to `/docs/`

Studio no longer owns a separate documentation route. Its docs are served by the shared Docs Viewer, which also serves other docs scopes.

Current Studio usage of the Docs Viewer:

- Studio section docs live in `_docs/`
- `scripts/build_docs.rb` builds the Studio docs payload into the Studio docs scope
- `/docs/?scope=studio&doc=<doc_id>` opens those docs in the shared Docs Viewer shell
- Studio page `i` links use those scoped URLs directly
- the Studio docs page uses the same top header nav and also renders a `Rebuild docs` action beside the docs search input

This means Studio documentation changes must stay aligned with the shared Docs Viewer behavior documented in **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** and **[Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)**.

## Local Development Boundary

`bin/dev-studio` is the current Studio route runner.

What it runs before starting long-lived services:

- required port preflight for Jekyll and the local write services
- optional docs/docs-search rebuilds for scopes listed in `DOCS_STARTUP_REBUILD_SCOPES`
- `./scripts/catalogue/export_catalogue_lookup.py --write`

What it starts:

- `bundle exec jekyll serve --host 127.0.0.1 --port 4000`
- `scripts/studio/studio_app_server.py`
- `scripts/catalogue/catalogue_write_server.py`
- `scripts/studio/audit_service.py`
- `scripts/docs/docs_live_rebuild_watcher.py`

What it does not start:

- catalogue/search regeneration scripts
- the retired standalone tag write server
- the standalone Docs management server unless explicitly enabled for fallback/debug use

Current local generated Studio feeds surfaced through this runtime:

- unified Studio activity via `GET /catalogue/read?key=activity_log`

Current mutable catalogue data surfaced through this runtime:

- catalogue source records and catalogue lookup/search records are read from `scripts/catalogue/catalogue_write_server.py`
- Jekyll excludes `assets/studio/data/catalogue/`, `assets/studio/data/catalogue_lookup/`, `var/`, and local `logs/` from the served site so local source/lookup/activity writes do not trigger an extra Jekyll regeneration pass
- catalogue editors, Catalogue Drafts, and Studio Activity show their existing unavailable/load-failed states instead of falling back to stale static source JSON

Current localhost docs-maintenance integration surfaced through this runtime:

- `POST /docs/broken-links`

Current localhost audit integration surfaced through this runtime:

- `GET /audits`
- `POST /audits/run`
- `POST /docs/rebuild`

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
