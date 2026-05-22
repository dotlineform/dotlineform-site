---
doc_id: local-studio-app-implementation-plan
title: Local Studio App Implementation Plan
added_date: 2026-05-22
last_updated: 2026-05-22
parent_id: local-studio-app
sort_order: 1000
published: true
viewable: true
---
# Local Studio App Implementation Plan

This plan implements [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app).

The target is a local Python-hosted, vanilla JavaScript Studio app that reuses existing browser modules and moves Studio away from Jekyll route hosting.
The public Jekyll site remains responsible for dotlineform.com publishing.

Status:

- proposed
- no implementation slices started

## Phase 0: Published Surface Cleanup

Outcomes:

- public builds reflect only what dotlineform.com should expose
- `/library/` and `/analysis/` remain public read-only Docs Viewer installs
- Studio routes, Studio app assets, and local-management docs output stop appearing in public output
- current local Studio remains available while migration work proceeds

| Task | Status |
| --- | --- |
| Document the public published-surface manifest. | pending |
| Keep `/library/` and `/analysis/` public read-only. | pending |
| Remove or exclude public `/studio/` output. | pending |
| Remove or exclude public `/docs/` output unless a curated read-only docs install is intentionally defined. | pending |
| Exclude Studio-only assets and generated Studio docs/search payloads from public output. | pending |
| Add or update checks so accidental public Studio output is visible. | pending |
| Decide whether `bin/dev-studio` can remain unchanged for this phase or needs a small config split. | pending |

Next steps:

Start with the published-surface manifest and build-output audit.
This phase should be behavior-preserving for public users and should not move canonical data.

## Phase 1: Local App Shell Foundation

Outcomes:

- a Python Studio app server can serve a local app shell without Jekyll
- existing Studio static assets can be served directly
- runtime config can be delivered as browser-safe JSON
- smoke tests can target the local app host separately from Jekyll

| Task | Status |
| --- | --- |
| Add a small Python Studio app server entrypoint. | pending |
| Serve a local Studio app shell. | pending |
| Serve existing Studio CSS and JavaScript assets. | pending |
| Expose browser-safe runtime config JSON for migrated views. | pending |
| Add a minimal health or readiness endpoint for the app server. | pending |
| Add a focused smoke-test harness that can target the local app host. | pending |

Next steps:

Keep this slice intentionally small.
The server should prove shell/static/config mechanics only; it should not yet absorb all local write services or redesign Studio navigation.

## Phase 1A: Tag Groups View Spike

Outcomes:

- `/studio/analytics/tag-groups/` becomes the first real Studio view mounted outside Jekyll
- existing `assets/studio/js/tag-groups.js` behavior is reused
- existing Studio CSS and DOM contracts remain intact
- the local app proves a low-risk review surface can run without Jekyll page generation

| Task | Status |
| --- | --- |
| Convert the current Tag Groups Jekyll shell into a local app view/template. | pending |
| Preserve the existing Tag Groups root ids, classes, and `data-role` hooks. | pending |
| Load the existing Tag Groups browser module from the local app shell. | pending |
| Provide any Tag Groups config/UI text through existing static config or the new runtime config JSON. | pending |
| Verify the view loads Studio data and renders the current review list. | pending |
| Add or update a smoke check for Tag Groups route-ready/rendered state on the local app host. | pending |

Next steps:

Use this as the first practical measure of how much Jekyll/Liquid glue must be replaced.
Do not introduce write-service proxying, route-family migration, or app-wide navigation redesign in this slice.

## Phase 2: Config And Navigation Adapter

Outcomes:

- migrated views receive config without Liquid
- navigation is expressed through app APIs rather than hardcoded page URLs
- current query-state behavior can be used as transitional input without becoming the long-term state owner

| Task | Status |
| --- | --- |
| Define the Studio runtime config shape for media bases, thumb bases, pipeline variants, UI text paths, docs links, and service endpoints. | pending |
| Add `navigateTo(view, params)` and related navigation helpers. | pending |
| Add `openModal(name, params)` and modal/context helpers where needed. | pending |
| Add return-context helpers that replace route-query return state over time. | pending |
| Add an initial-state adapter that can read current URL state during transition. | pending |
| Centralize app-shell nav labels and view ids outside Jekyll front matter. | pending |

Next steps:

Introduce adapters only where a migrated view needs them.
The adapter should support current route-like views first and can later support panels or modals where that improves workflow.

## Phase 3: Docs Viewer Manage Mode Migration

Outcomes:

- Docs Viewer `/docs/` manage mode becomes the first complex workflow hosted by the Python Studio app server
- public `/library/` and `/analysis/` stay read-only Docs Viewer installs
- local Docs management no longer requires Jekyll to serve the management shell
- Docs Viewer portability remains intact

| Task | Status |
| --- | --- |
| Mount the Docs Viewer management shell in the local Studio app. | pending |
| Provide Docs Viewer management runtime config through the Python app server. | pending |
| Move or adapt docs-management API routes into the Python Studio app server without default proxying. | pending |
| Reuse existing docs-management domain modules and response contracts. | pending |
| Preserve create, metadata edit, move, archive/delete, show hidden, rebuild, settings, and import workflows. | pending |
| Verify generated docs payload rebuilds and docs search rebuilds still run through the expected paths. | pending |
| Smoke `/docs/` manage mode on the local app host and public `/library/` plus `/analysis/` read-only behavior separately. | pending |

Next steps:

Start by hosting the shell and config, then migrate API ownership workflow by workflow.
Temporary sibling services are acceptable only as narrow scaffolding and should be retired as each management route moves into the app server.

## Phase 4: Local Service Consolidation

Outcomes:

- the Python Studio app server owns the local Studio HTTP surface
- old sibling HTTP services are retired as their workflows migrate
- domain modules preserve explicit write policies and response contracts
- `bin/dev-studio` becomes a launcher for the local app server and any remaining required background processes

| Task | Status |
| --- | --- |
| Define route modules for catalogue, docs, analytics, audit, and shared Studio app routes. | pending |
| Move endpoint ownership into the Python app server slice by slice. | pending |
| Reuse extracted Python domain modules instead of proxying to old services by default. | pending |
| Preserve loopback binding, CORS limits, write allowlists, backups, compact logs, and preview/apply boundaries. | pending |
| Update `bin/dev-studio` to start the app server and only necessary background tasks. | pending |
| Keep public Jekyll preview/build as an explicit separate action. | pending |

Next steps:

Use the docs-management migration to establish the pattern.
Avoid a broad service merge until one migrated workflow has proven the app-server route-module shape.

## Phase 5: Route Family Migration

Outcomes:

- active Studio workflows move out of Jekyll route pages
- user-facing workflow behavior remains stable
- old Jekyll route files are retired after local replacements are verified

| Task | Status |
| --- | --- |
| Migrate catalogue editors and dashboards. | pending |
| Migrate analytics/tag routes. | pending |
| Migrate data-sharing routes. | pending |
| Migrate audit and project-state routes. | pending |
| Retire Jekyll Studio route files after each replacement is verified. | pending |
| Keep temporary redirects only where useful for local transition ergonomics. | pending |

Next steps:

Batch by route family and workflow risk.
Do not migrate routes only for tidiness; each slice should end with a verified local app view and a clear retirement or compatibility decision for the Jekyll route.

## Phase 6: Projection And Build Contract

Outcomes:

- canonical source, public projections, Studio projections, and Docs Viewer payloads are clearly separated
- Jekyll public builds consume only intended public source/projection files
- source-only fields can remain in canonical data without leaking into public runtime artifacts

| Task | Status |
| --- | --- |
| Document canonical source families and their public projections. | pending |
| Distinguish public projections, Studio projections, and Docs Viewer payloads in docs and checks. | pending |
| Add checks for source-only fields leaking into public projections. | pending |
| Verify Jekyll consumes public projections rather than Studio-only data. | pending |
| Keep generated output paths explicit and boring. | pending |

Next steps:

Use this phase to prepare for a future repo split without requiring one.
The projection contract matters more than physical repo layout.

## Phase 7: Optional Repo Split Decision

Outcomes:

- repo split remains a separate decision after the local app boundary is proven
- any split is driven by concrete operational benefit, not tidiness
- the publish/export contract is already tested before files move between repos

| Task | Status |
| --- | --- |
| Review files that now belong to public site, Studio app, canonical data, Docs Viewer, and generated outputs. | pending |
| Decide whether to keep one repo, split public-site and Studio repos, or extract Docs Viewer first. | pending |
| Identify deployment, publishing, and local development benefits required to justify a split. | pending |
| If splitting, define the publish/export contract before moving files. | pending |

Next steps:

Defer this decision until Studio runs locally without Jekyll and public output has a stable manifest.
One repo remains acceptable while the boundary settles.

## Verification

For planning/docs-only slices:

- source review is enough unless generated docs payloads are intentionally rebuilt

For public build cleanup:

- run a Jekyll build to a separate destination
- inspect output for absence of `/studio/`, `assets/studio/`, public `/docs/`, and Studio docs/search payloads
- smoke intended public routes including `/library/` and `/analysis/`

For local app slices:

- run syntax/import checks for touched JavaScript modules
- run focused Playwright smoke tests against the local app host
- verify route-ready state for migrated views
- verify affected save/build/read workflows against existing local service contracts
- keep public Jekyll build checks separate from Studio app checks

For projection-contract slices:

- add focused leak checks for source-only fields
- verify generated public JSON/search payloads
- verify representative public pages consume public projections only

## Related Docs

- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer Management Current State](/docs/?scope=studio&doc=docs-viewer-management-current)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
