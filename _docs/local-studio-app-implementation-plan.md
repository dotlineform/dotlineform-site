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

- in progress
- Phase 0, Phase 1, and Phase 1A are implemented
- Phase 2 is implemented
- Phase 3 is implemented for Docs Viewer manage mode

## Lifecycle Rules

This migration follows [Development Workflow](/docs/?scope=studio&doc=development-workflow).
It should be handled as a behavior-changing migration even when a slice is intended to preserve existing features.

Before editing a slice:

- classify the slice by owning surface: local runtime, Docs Viewer, Studio route behavior, public build surface, generated data, UI/CSS, or workflow documentation
- read the owning docs for that surface
- identify whether the change touches high-risk JavaScript, Python service boundaries, local write paths, generated payloads, public output, or CSS ownership
- keep the task small enough to verify and summarize in one close-out

While implementing:

- do not add complete responsibilities to large route controllers by default
- keep `studio_app_server.py` as dispatch/startup, with config, views, and route-family APIs in focused modules
- reuse extracted Python and JavaScript domain owners where they exist
- avoid default proxy compatibility layers to old sibling services
- preserve local write-service guardrails: loopback binding, CORS limits, write allowlists, backups, preview/apply boundaries, and compact logs
- keep public Jekyll output and local Studio behavior as separate verification surfaces

At close-out:

- update this plan and the change request when task status, behavior, risks, or next steps changed
- record generated docs/search payload status
- write or explicitly defer the structured `_docs_logs/` entry for the commit point
- include checks run, results, and the next suggested slice

## Commit Points And Change Log

Future sessions should assume the user may commit whenever Codex stops.
Do not leave a migration slice half-described if the code is otherwise ready.

Each meaningful commit point needs a structured docs-log entry under `_docs_logs/entries/`.
Use `_docs_logs/README.md` and set `change_request_doc_id` to `site-request-studio-local-vanilla-web-app`.

Commit points should be small and coherent:

- one phase completion
- one migrated route or route-family milestone
- one local API/workflow milestone
- one public build-surface or projection-contract milestone
- one service-consolidation milestone
- one behavior-changing documentation milestone

Each commit-point entry should capture:

- what behavior changed
- why it matters for the Jekyll-to-local-app migration
- related docs and files
- verification run
- generated docs/search payload status
- any remaining risks or next slice

Current commit point:

- Phase 0, Phase 1, and Phase 1A are complete
- Phase 2 is complete with runtime config, navigation, initial-state, return-context, and modal-dispatch helpers
- Phase 3 has started with the Docs Viewer shell and generated-read API adapter hosted by the local app server
- Phase 3 now routes Docs management GET/POST APIs through the local app server adapter
- Phase 3 now has fixture-backed API workflow smoke coverage for Docs create, metadata edit, move, archive, delete, source-config settings, import listing, rebuild, and scope lifecycle routes
- Phase 3 now has fixture-backed UI workflow smoke coverage for Docs create, metadata edit, settings save, archive, delete preview/apply, import, drag/drop move, scope create/delete, and generated reload behavior in the local `/docs/` shell
- Phase 3 now has public read-only smoke coverage for `/library/` and `/analysis/`
- Phase 4 has started by adding the local app server to `bin/dev-studio` and retiring the separate Docs management HTTP process from default startup
- Phase 4 now has the first analytics API route module, serving tag read data through the local app server
- Phase 4 now has the first analytics write route, `POST /studio/api/analytics/save-tags`, through the local app server
- Phase 4 now routes tag assignment import preview/apply through the local app server
- Phase 4 now routes tag registry import and mutate-tag preview/apply through the local app server
- non-Docs write/manage APIs are intentionally still disabled or partial where not yet migrated

## Phase 0: Published Surface Cleanup

Outcomes:

- public builds reflect only what dotlineform.com should expose
- `/library/` and `/analysis/` remain public read-only Docs Viewer installs
- Studio routes, Studio app assets, and local-management docs output stop appearing in public output
- current local Studio remains available while migration work proceeds

| Task | Status |
| --- | --- |
| Document the public published-surface manifest. | done |
| Keep `/library/` and `/analysis/` public read-only. | done |
| Remove or exclude public `/studio/` output. | done |
| Remove or exclude public `/docs/` output unless a curated read-only docs install is intentionally defined. | done |
| Exclude Studio-only assets and generated Studio docs/search payloads from public output. | done |
| Add or update checks so accidental public Studio output is visible. | done |
| Decide whether `bin/dev-studio` can remain unchanged for this phase or needs a small config split. | done |

Next steps:

Phase 0 is implemented.
Next work should begin Phase 1 with the Python local app shell foundation, then Phase 1A with the Tag Groups view spike.

## Phase 1: Local App Shell Foundation

Outcomes:

- a Python Studio app server can serve a local app shell without Jekyll
- existing Studio static assets can be served directly
- runtime config can be delivered as browser-safe JSON
- smoke tests can target the local app host separately from Jekyll

| Task | Status |
| --- | --- |
| Add a small Python Studio app server entrypoint. | done |
| Split app-server config, view rendering, and Docs API adapters out of the server entrypoint before broad route migration. | done |
| Serve a local Studio app shell. | done |
| Serve existing Studio CSS and JavaScript assets. | done |
| Expose browser-safe runtime config JSON for migrated views. | done |
| Add a minimal health or readiness endpoint for the app server. | done |
| Add a focused smoke-test harness that can target the local app host. | done |

Next steps:

Phase 1 foundation is implemented.
The server now exposes `/studio/runtime-config.json`, and migrated views can opt into it with `meta[name="dlf-studio-config-url"]` while unmigrated Jekyll-hosted pages continue to use the static Studio config fallback.
`studio_app_server.py` should stay a thin dispatcher and process entrypoint.
Local app growth should happen in focused modules such as config, view shells, route-family APIs, and reusable domain services.
The next slice should start Phase 2 by defining the stable runtime config shape and introducing narrow navigation helpers only where migrated views need them.

## Phase 1A: Tag Groups View Spike

Outcomes:

- `/studio/analytics/tag-groups/` becomes the first real Studio view mounted outside Jekyll
- existing `assets/studio/js/tag-groups.js` behavior is reused
- existing Studio CSS and DOM contracts remain intact
- the local app proves a low-risk review surface can run without Jekyll page generation

| Task | Status |
| --- | --- |
| Convert the current Tag Groups Jekyll shell into a local app view/template. | done |
| Preserve the existing Tag Groups root ids, classes, and `data-role` hooks. | done |
| Load the existing Tag Groups browser module from the local app shell. | done |
| Provide any Tag Groups config/UI text through existing static config or the new runtime config JSON. | done |
| Verify the view loads Studio data and renders the current review list. | done |
| Add or update a smoke check for Tag Groups route-ready/rendered state on the local app host. | done |

Next steps:

Phase 1A is implemented.
Use the Tag Groups spike findings to shape the dedicated runtime config and navigation adapter work in Phase 2.

## Phase 2: Config And Navigation Adapter

Outcomes:

- migrated views receive config without Liquid
- navigation is expressed through app APIs rather than hardcoded page URLs
- current query-state behavior can be used as transitional input without becoming the long-term state owner

| Task | Status |
| --- | --- |
| Define the Studio runtime config shape for media bases, thumb bases, pipeline variants, UI text paths, docs links, and service endpoints. | done |
| Add `navigateTo(view, params)` and related navigation helpers. | done |
| Add `openModal(name, params)` and modal/context helpers where needed. | done |
| Add return-context helpers that replace route-query return state over time. | done |
| Add an initial-state adapter that can read current URL state during transition. | done |
| Centralize app-shell nav labels and view ids outside Jekyll front matter. | done |

Next steps:

Phase 2 is implemented.
`/studio/runtime-config.json` now exposes the local app runtime contract for views, navigation, service endpoints, data/UI-text paths, media/thumb bases, pipeline variants, modal dispatch, and transitional state.
`assets/studio/js/studio-navigation.js` now owns the first local app adapter layer: view lookup, URL building, `navigateTo(view, params)`, URL initial-state parsing, `sessionStorage` return-context helpers, and `openModal(name, params)` dispatch through the `studio:open-modal` event.
This is intentionally not a route framework; it is a small compatibility surface for migrated vanilla modules.
Future route migrations should add only the adapter helpers they actually need, backed by focused smoke tests.

## Phase 3: Docs Viewer Manage Mode Migration

Outcomes:

- Docs Viewer `/docs/` manage mode becomes the first complex workflow hosted by the Python Studio app server
- public `/library/` and `/analysis/` stay read-only Docs Viewer installs
- local Docs management no longer requires Jekyll to serve the management shell
- Docs Viewer portability remains intact
- Docs Viewer route/API code is kept as a distinct module boundary inside the Studio app server

| Task | Status |
| --- | --- |
| Mount the Docs Viewer management shell in the local Studio app. | done |
| Provide Docs Viewer management runtime config through the Python app server. | done |
| Define Docs Viewer route/API modules inside the Python Studio app server rather than creating a separate default Docs server. | done |
| Move or adapt docs-management API routes into the Python Studio app server without default proxying. | done |
| Reuse existing docs-management domain modules and response contracts. | done |
| Keep Docs Viewer JS, CSS, UI text, scope config, payload contract, write policies, and import/rebuild/search behavior Docs-owned. | done |
| Preserve create, metadata edit, move, archive/delete, show hidden, rebuild, settings, import, and scope lifecycle workflows. | done |
| Verify generated docs payload rebuilds and docs search rebuilds still run through the expected paths. | done |
| Smoke `/docs/` manage mode on the local app host and public `/library/` plus `/analysis/` read-only behavior separately. | done |

Next steps:

Phase 3 is implemented for Docs Viewer manage mode by hosting the management shell at `/docs/` through the Python Studio app server.
The app-server Docs API routes live behind the dedicated `studio_docs_api.py` adapter instead of being embedded in the app-server dispatcher.
Capabilities now report configured scopes from the live docs scope config file, including user-created scopes that are eligible for scope lifecycle deletion.
The adapter calls existing docs-management domain functions directly for generated reads, source-config/settings reads, import listings, data-sharing package reads, and management POST routes such as settings, create, metadata update, move, archive/delete, rebuild, scope lifecycle, import, and data sharing.
`tests/smoke/local_studio_docs_management_workflows.py` now proves the main Docs management API workflow paths against a temporary fixture repo through the local app server.
It patches rebuild execution and Markdown validation inside the fixture so source writes are exercised without rebuilding real docs payloads, invoking Bundler/Jekyll validation, or touching real `_docs/` files.
`tests/smoke/local_studio_docs_management_ui.py` proves representative UI-level management workflows through the local `/docs/` shell against the same fixture pattern.
It covers create, metadata edit, settings save, archive, delete preview/apply, and browser reloads of generated docs index/payload data after each source mutation.
`tests/smoke/local_studio_docs_management_import_ui.py`, `tests/smoke/local_studio_docs_management_move_ui.py`, and `tests/smoke/local_studio_docs_management_scope_ui.py` cover the remaining managed UI workflows: staged import, drag/drop move, and scope create/delete.
`tests/smoke/public_docs_viewer_readonly.py` verifies that public `/library/` and `/analysis/` builds stay read-only, do not load management CSS, do not render management controls, and do not load Studio-only assets.
`bin/dev-studio` now treats Docs management as owned by the local Studio app server and does not start `scripts/docs/docs_management_server.py` by default.
Set `DOCS_MANAGEMENT_SERVER_ENABLED=1` only for fallback/debug runs that intentionally need the old standalone process.
Data-sharing-specific UI behavior remains a later adapter-consolidation slice; the Phase 3 claim is Docs Viewer manage-mode parity for the ordinary source/edit/import/scope workflows.
Do not add a separate always-running Docs Viewer server for normal Studio; keep a possible standalone Docs Viewer launcher as a later portability option over the same modules.

## Phase 4: Local Service Consolidation

Outcomes:

- the Python Studio app server owns the local Studio HTTP surface
- old sibling HTTP services are retired as their workflows migrate
- domain modules preserve explicit write policies and response contracts
- `bin/dev-studio` becomes a launcher for the local app server and any remaining required background processes
- Docs Viewer remains a module boundary within the app server rather than becoming a separate default process

| Task | Status |
| --- | --- |
| Define route modules for catalogue, docs, analytics, audit, and shared Studio app routes. | partial; docs and analytics modules started |
| Move endpoint ownership into the Python app server slice by slice. | partial; Docs management, analytics tag read routes, tag assignment write routes, and tag registry write routes moved |
| Reuse extracted Python domain modules instead of proxying to old services by default. | partial; Docs management, analytics tag assignment routes, and analytics registry routes use existing domain functions directly |
| Preserve loopback binding, CORS limits, write allowlists, backups, compact logs, and preview/apply boundaries. | partial; tag assignment and registry writes preserve write allowlists, backups, compact logs, activity attachment, and preview/apply split where applicable |
| Update `bin/dev-studio` to start the app server and only necessary background tasks. | partial; Docs management sibling retired from default startup |
| Keep public Jekyll preview/build as an explicit separate action. | pending |

Next steps:

Use the docs-management migration to establish the endpoint ownership pattern.
`bin/dev-studio` now starts the local app server as a bridge step, but it still starts Jekyll and existing sibling services for unmigrated workflows.
Avoid a broad service merge until one migrated workflow has proven the app-server route-module shape.
The first analytics-owned slices established read and write ownership separately: `studio_analytics_api.py` serves tag registry, aliases, assignments, and groups through `/studio/api/analytics/...`, and it now handles `POST /studio/api/analytics/save-tags`, `POST /studio/api/analytics/import-tag-assignments-preview`, `POST /studio/api/analytics/import-tag-assignments`, `POST /studio/api/analytics/import-tag-registry`, `POST /studio/api/analytics/mutate-tag-preview`, and `POST /studio/api/analytics/mutate-tag` by calling the existing tag assignment, registry mutation, alias rewrite, atomic-write, logging, and Studio activity helpers directly.
Static JSON fallbacks remain for unmigrated/Jekyll contexts.
The browser transport prefers the local runtime `save_tags`, assignment import, registry import, registry mutation, and analytics `health` endpoints when a migrated local app page has runtime config; old tag write-server URLs remain fallbacks for unmigrated Jekyll-hosted pages.
Next Phase 4 slices should migrate one endpoint family at a time, with tag alias mutations, promote/demote workflows, and route-page migration still treated as separate higher-risk steps.

Transition cleanup backlog:

| Cleanup Item | Trigger | Status |
| --- | --- | --- |
| Remove old `127.0.0.1:8787` tag write-server fallbacks from `assets/studio/js/studio-transport.js`. | All tag editor/import routes are hosted by the local app shell and use local runtime config. | pending |
| Stop `bin/dev-studio` from starting `scripts/analytics/tag_write_server.py` by default. | The local app server owns save-tags, assignment import, registry import/mutation, alias import/mutation, promote/demote, and any remaining tag write endpoints. | pending |
| Retire or archive `scripts/analytics/tag_write_server.py` as an HTTP entrypoint while keeping reusable analytics domain modules. | No migrated UI or fallback/debug workflow needs the standalone tag write HTTP process. | pending |
| Remove hardcoded old tag write URLs from tests and browser module fixtures. | Runtime-config endpoints cover the migrated routes and fallback compatibility is no longer required. | pending |
| Remove static JSON fallbacks for analytics tag data from migrated local-only views where the fallback no longer serves a Jekyll-hosted page. | The corresponding view no longer runs in Jekyll and public output has no Studio shell for it. | pending |
| Retire migrated Jekyll Studio route files or replace them with local-only transition redirects. | Each route family has a verified local app view and no public build dependency. | pending |
| Recheck `main.css` and Studio CSS ownership after route retirements. | Migrated Studio surfaces no longer rely on public-site route CSS. | pending |
| Remove compatibility docs that describe old sibling-service startup as the normal path. | `bin/dev-studio` starts only the local app server plus genuinely required background tasks. | pending |

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
- [Development Workflow](/docs/?scope=studio&doc=development-workflow)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- `_docs_logs/README.md`
- [Docs Viewer Management Current State](/docs/?scope=studio&doc=docs-viewer-management-current)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
