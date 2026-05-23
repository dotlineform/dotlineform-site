---
doc_id: local-studio-app-implementation-plan
title: Local Studio App Implementation Plan
added_date: 2026-05-22
last_updated: 2026-05-23
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

- active migration plan; completed work is marked `done` and remaining work is marked `planned`
- Phase 0, Phase 1, and Phase 1A are implemented
- Phase 2 is implemented
- Phase 3 is implemented for Docs Viewer manage mode and the Docs Broken Links report replacement
- Phase 4 active service consolidation is done for the current Local Studio route scope; direct launcher cleanup remains a planned follow-up
- Phase 5 operational route migration is implemented for the current route scope; UI Catalogue demo visibility remains a planned first-class local Studio follow-up

## Remaining Work Snapshot

Next suitable slices, in dependency order:

1. Make UI Catalogue demos visible from Local Studio as first-class non-mutating Studio surfaces.
2. Start the projection contract work now that route and service ownership is less fluid.
3. Defer the optional repo split decision until the publish/export contract is stable.

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
- keep route shell modules split by ownership when the shared view module starts collecting a whole route family
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
- Phase 3 now hosts Docs Broken Links as a Docs Viewer report and has retired the old `/studio/docs-broken-links/` route shell
- Phase 3 Docs management now uses `scripts/docs/docs_management_service.py` as a dispatcher over focused Docs management workflow modules; the local Studio app imports that module through `scripts/studio/studio_docs_api.py` instead of loading the standalone HTTP server entrypoint
- Phase 4 added the local app server to `bin/dev-studio` and retired the separate Docs management HTTP process from default startup
- Phase 4 now has the first analytics API route module, serving tag read data through the local app server
- Phase 4 now has the first analytics write route, `POST /studio/api/analytics/save-tags`, through the local app server
- Phase 4 now routes tag assignment import preview/apply through the local app server
- Phase 4 now routes tag registry import and mutate-tag preview/apply through the local app server
- Phase 4 now routes tag alias import, delete, and mutate-alias preview/apply through the local app server
- Phase 4 now routes tag alias promotion and tag demotion preview/apply through the local app server
- the active tag write route surface is now accounted for in the local analytics adapter; the deprecated tag-server `/build-docs` route is intentionally not migrated
- Phase 4 now mounts the tag registry, tag aliases, series-tags, and per-series tag editor route shells in the local app so those pages use local runtime config and local analytics endpoints
- Phase 4 has retired the Jekyll analytics tag route shells, removed the old `127.0.0.1:8787` browser fallbacks, and stopped launching the standalone tag write server from `bin/dev-studio`
- Phase 4 has removed the standalone `scripts/analytics/tag_write_server.py` HTTP entrypoint; `scripts/studio/studio_analytics_api.py` is the active local HTTP owner for tag writes
- Phase 5 has mounted `/studio/catalogue/?mode=manage`, `/studio/analytics/?mode=manage`, `/studio/audits/?mode=manage`, `/studio/project-state/?mode=manage`, `/studio/thumbnail-quality/?mode=manage`, `/studio/bulk-add-work/?mode=manage`, `/studio/activity/?mode=manage`, `/studio/catalogue-field-registry/?mode=manage`, `/studio/catalogue-status/?mode=manage`, `/studio/studio-works/?mode=manage`, `/studio/catalogue-series/?mode=manage`, `/studio/catalogue-work/?mode=manage`, `/studio/catalogue-work-detail/?mode=manage`, and `/studio/catalogue-moment/?mode=manage` in the local app, retired the old Jekyll shells, and moved their browser-facing catalogue APIs under `/studio/api/catalogue/...`
- the old Jekyll `/studio/` landing shell is retired; `/studio/` is now the local app home during Studio sessions
- Studio route URL building now preserves configured route query state such as `?mode=manage` while appending record parameters for migrated catalogue editor links
- The per-series tag editor now shares the catalogue public-link helper for its public series/work header links
- Migrated catalogue editor summary links for public work, series, work detail, and moment pages now resolve through the configured public preview base instead of staying relative to the Studio app host
- Studio Works now shares the catalogue public-link helper for public work and series links, and the helper fails closed instead of falling back to the Studio app host when a public-site base is missing
- Catalogue moment save, publication preview/apply, and delete apply now run through focused catalogue service modules rather than the legacy in-process HTTP handler bridge
- Catalogue bulk save now runs through a focused catalogue service module, and `studio_catalogue_api.py` no longer constructs fake legacy HTTP handlers for Local Studio catalogue writes
- The standalone `scripts/catalogue/catalogue_write_server.py` wrapper has been retired; `bin/dev-studio` no longer exposes `CATALOGUE_WRITE_SERVER_ENABLED` or `CATALOGUE_WRITE_PORT`
- Docs Broken Links moved into Docs Viewer reports rather than becoming another migrated Studio route shell
- Data Sharing dashboard, prepare, and review route shells are now local-app hosted and call Data Sharing through the local Docs API adapter instead of the old standalone docs-management service URL
- Studio Audits now calls `/studio/api/audits/...` through the local app server instead of requiring the old standalone audit service URL
- Project State now calls `/studio/api/catalogue/project-state-report` and the local Docs API through the local app server instead of requiring the old catalogue/docs sibling service URLs
- Thumbnail Quality now calls `/studio/api/catalogue/thumbnail-quality-preview` through the local app server instead of requiring the old catalogue sibling service URL
- Local Studio and public-site launchers are now split into explicit commands: `bin/local-studio`, `bin/public-site-preview`, and `bin/public-site-build`; `bin/dev-studio` remains a transition bridge with `JEKYLL_ENABLED=0` support
- future non-Docs write/manage APIs should be added through the same local app route-module and domain-service pattern; detailed future-proofing rules live in [Development Checklist](/docs/?scope=studio&doc=development-checklist)

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
| Add a shared Studio route URL builder that safely appends params to configured route paths with existing query state. | done |
| Add `openModal(name, params)` and modal/context helpers where needed. | done |
| Add return-context helpers that replace route-query return state over time. | done |
| Add an initial-state adapter that can read current URL state during transition. | done |
| Centralize app-shell nav labels and view ids outside Jekyll front matter. | done |

Next steps:

Phase 2 is implemented.
`/studio/runtime-config.json` now exposes the local app runtime contract for views, navigation, service endpoints, data/UI-text paths, media/thumb bases, pipeline variants, modal dispatch, and transitional state.
`assets/studio/js/studio-navigation.js` now owns the first local app adapter layer: view lookup, URL building, `navigateTo(view, params)`, URL initial-state parsing, `sessionStorage` return-context helpers, and `openModal(name, params)` dispatch through the `studio:open-modal` event.
`assets/studio/js/studio-config.js` now owns `buildStudioRouteUrl(config, key, params)` for callers that need to append route-specific params to configured Studio routes that may already include `?mode=manage`.
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
| Move Docs Broken Links into Docs Viewer reports instead of migrating `/studio/docs-broken-links/` as a standalone Studio route. | done |

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
`bin/dev-studio` now treats Docs management as owned by the local Studio app server and has no standalone Docs Management server startup path.
Data-sharing-specific UI behavior remains a later adapter-consolidation slice; the Phase 3 claim is Docs Viewer manage-mode parity for the ordinary source/edit/import/scope workflows.
Docs Broken Links is also a Docs Viewer concern because it is a scope-based report over generated docs links.
It now lives on the `docs-broken-links` Studio docs page through `viewer_report: docs_broken_links`, calls the local Docs API endpoint `POST /docs/broken-links`, and replaces the retired `/studio/docs-broken-links/` shell.
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
| Define route modules for catalogue, docs, analytics, audit, and shared Studio app routes. | done for current active Local Studio routes; future route families should follow [Development Checklist](/docs/?scope=studio&doc=development-checklist) |
| Move endpoint ownership into the Python app server slice by slice. | done for current active browser endpoints; Docs management, Data Sharing, analytics tag reads/writes, Studio audit routes, Project State report, Thumbnail Quality preview, active catalogue editor APIs, and operational route shells are local-app owned |
| Reuse extracted Python domain modules instead of proxying to old services by default. | done for current active Local Studio APIs; future APIs should keep using focused domain modules rather than old sibling HTTP services |
| Preserve loopback binding, CORS limits, write allowlists, backups, compact logs, and preview/apply boundaries. | done for current active write/run endpoints; Docs/Data Sharing writes, analytics tag writes, Studio audit runs, Project State report runs, Thumbnail Quality preview refreshes, and catalogue editor writes preserve existing guardrails, compact logs, and activity attachment where applicable |
| Update `bin/dev-studio` to start the app server and only necessary background tasks. | done as a transition bridge; standalone Docs management, tag write, audit, and catalogue write siblings are retired from default startup |
| Keep public Jekyll preview/build as an explicit separate action. | done |
| Define the final launcher split while keeping `bin/dev-studio` as a bridge command during migration. | done; planned cleanup is to make `bin/local-studio` independent or move shared runner internals before retiring the bridge command |

Next steps:

Phase 4 active service consolidation is implemented for the current route scope.
Future route families should use [Development Checklist](/docs/?scope=studio&doc=development-checklist) for route-module ownership, public-link resolver adoption, shared route URL builder use, and Local Studio visibility expectations.
`bin/dev-studio` now starts the local app server as a bridge step, and it can still start Jekyll for transition sessions.
The command boundary is now explicit: `bin/local-studio` starts local Studio without Jekyll, while `bin/public-site-preview` and `bin/public-site-build` run public Jekyll preview/build with `_config.yml` by default.
Route migration and public-link resolver work are now settled for the current active scope, so `bin/dev-studio` should be treated as planned launcher cleanup rather than required architecture.
`bin/local-studio` currently delegates to `bin/dev-studio`, so remove that dependency or move shared runner behavior into a neutral helper before deleting the bridge command.
Keep `studio_app_server.py` as the active local Studio service owner and use plain `bin/public-site-preview` / `bin/public-site-build` for public Jekyll preview/build.
The first analytics-owned slices established read and write ownership separately: `studio_analytics_api.py` serves tag registry, aliases, assignments, and groups through `/studio/api/analytics/...`, and it now handles save-tags, tag assignment import preview/apply, tag alias import/delete/mutate preview/apply, tag registry import/mutate preview/apply, tag alias promotion preview/apply, and tag demotion preview/apply by calling the existing tag assignment, alias mutation, registry mutation, promotion/demotion, alias rewrite, assignment rewrite, atomic-write, logging, and Studio activity helpers directly.
The migrated local-only tag views now require local analytics read endpoints instead of falling back to static `assets/studio/data/tag_*.json` paths, and `studio_config.json` no longer exposes those static tag-data paths as browser data sources.
The dev Studio Jekyll overlay now excludes the four tag source JSON files as well, so local Jekyll cannot accidentally satisfy a legacy static read.
The browser transport now requires the local runtime `save_tags`, assignment import, alias import/delete/edit/promote/demote, registry import/mutation, demote, and analytics `health` endpoints for tag writes; old tag write-server URLs are no longer browser fallbacks.
The deprecated tag-server `POST /build-docs` path is intentionally not migrated and should not be exposed through runtime config.
The tag registry, tag aliases, series-tags, and per-series tag editor shells now run in the local app and are covered by `tests/smoke/local_studio_app_tag_routes.py`, which verifies local analytics API reads and no `8787` fallback requests.
The old Jekyll analytics tag route files have been removed, so `bin/dev-studio` no longer starts the standalone tag write server by default.
The standalone tag write server HTTP entrypoint has been removed; reusable tag domain modules remain under `scripts/analytics/`.
Studio Audits now uses `scripts/studio/studio_audit_api.py` for local app `GET /studio/api/audits/audits` and `POST /studio/api/audits/audits/run`.
The adapter reuses the allowlisted registry and run logic from `scripts/studio/audit_runner.py`.
The standalone audit HTTP wrapper has been retired; Codex can call the runner directly, while browser audit runs go through the local app API.
Project State now uses `scripts/studio/studio_catalogue_api.py` for local app `POST /studio/api/catalogue/project-state-report`.
The adapter reuses `scripts/catalogue/project_state_report.py`, reads the served repo's local environment for `DOTLINEFORM_PROJECTS_BASE_DIR`, preserves Studio activity logging, and lets the browser use local Docs API source opening instead of the old standalone docs-management URL.
Thumbnail Quality now uses the same narrow catalogue adapter for `POST /studio/api/catalogue/thumbnail-quality-preview`.
The adapter reuses `scripts/media/build_thumbnail_quality_preview.py`, keeps initial page loads on the checked-in preview JSON, and removes the browser dependency on `127.0.0.1:8788` for refresh availability.
Catalogue Drafts and Studio Activity now read through local-app `GET /studio/api/catalogue/read`.
Bulk Add Work now uses local-app `POST /studio/api/catalogue/import-preview` and `POST /studio/api/catalogue/import-apply`; the adapter reuses the existing workbook import planner/apply helpers and preserves Studio Activity logging.
The catalogue editor write/build/publication/delete/prose-import/moment-import endpoints now run through `/studio/api/catalogue/...` on the local app server.
Migrated catalogue editor endpoints call focused catalogue service modules directly; no active Local Studio catalogue write endpoint uses the legacy in-process handler bridge.
`bin/dev-studio` no longer starts or offers a fallback flag for a standalone catalogue write server.
The catalogue write service extraction inventory is captured in [Catalogue Write Service Extraction](/docs/?scope=studio&doc=scripts-catalogue-write-service-extraction).
The callable catalogue service slices now route bulk save, delete preview/apply, publication preview/apply, build preview/apply, moment preview/save, prose import preview/apply, moment import preview/apply, work create/save, work-detail create/save, and series create/save through `scripts/catalogue/catalogue_write_service.py`.
`catalogue_write_service.py` is only the dispatcher; ownership lives in focused modules such as `catalogue_bulk_service.py`, `catalogue_work_service.py`, `catalogue_work_detail_service.py`, `catalogue_series_service.py`, `catalogue_build_service.py`, `catalogue_delete_service.py`, `catalogue_moment_service.py`, and `catalogue_prose_import_service.py`, with shared plumbing in `catalogue_service_context.py`.
The standalone `scripts/catalogue/catalogue_write_server.py` wrapper has been removed now that Local Studio no longer depends on its handler methods.
Active Local Studio Docs browser transport now uses `/studio/api/docs/...`; `127.0.0.1:8789` is no longer a browser fallback for migrated routes.
The standalone Docs Management server entrypoint has been removed; Local Studio imports `scripts/docs/docs_management_service.py` as the dispatcher for focused Docs management modules covering context, reads, capabilities, source mutations, import, Data Sharing, source opening, and broken-links audit behavior.
The launcher split is now explicit: `bin/local-studio` starts the local Studio app path with Jekyll disabled, `bin/public-site-preview` runs public Jekyll preview with `_config.yml`, and `bin/public-site-build` runs public Jekyll builds with `_config.yml`.
`bin/dev-studio` remains a bridge command for transition sessions and now has a `JEKYLL_ENABLED=0` switch for local-Studio-only runs.
Its remaining role is planned cleanup, because normal development should use `bin/local-studio` for Studio and `bin/public-site-preview` for public Jekyll.

Transition cleanup backlog:

| Cleanup Item | Trigger | Status |
| --- | --- | --- |
| Remove old `127.0.0.1:8787` tag write-server fallbacks from `assets/studio/js/studio-transport.js`. | All tag editor/import routes are hosted by the local app shell and use local runtime config. | done |
| Stop `bin/dev-studio` from starting `scripts/analytics/tag_write_server.py` by default. | The local app server owns save-tags, assignment import, registry import/mutation, alias import/mutation, and promote/demote; the deprecated `/build-docs` path is excluded rather than migrated; all active tag editor pages are local-app hosted. | done |
| Retire or archive `scripts/analytics/tag_write_server.py` as an HTTP entrypoint while keeping reusable analytics domain modules. | No migrated UI or fallback/debug workflow needs the standalone tag write HTTP process. | done |
| Stop `bin/dev-studio` from starting `scripts/studio/audit_service.py` by default. | The local app server owns the active Studio audit HTTP endpoints. | done |
| Remove old `127.0.0.1:8789` Docs Management fallbacks from active Studio browser transport and route smokes. | Local Studio Docs management and Data Sharing routes are served through `/studio/api/docs/...`. | done |
| Extract Docs Management reusable behavior out of the standalone HTTP server entrypoint. | The local Studio app needs Docs management behavior without depending on an old sibling server module. | done; `scripts/docs/docs_management_service.py` dispatches to focused `docs_management_*_service.py` workflow modules |
| Remove the standalone Docs Management HTTP entrypoint. | No active workflow needs to exercise Docs management outside Local Studio. | done |
| Remove hardcoded old tag write URLs from tests and browser module fixtures. | Runtime-config endpoints cover the migrated routes and fallback compatibility is no longer required. | done; remaining 8787 references are negative assertions only |
| Remove static JSON fallbacks for analytics tag data from migrated local-only views where the fallback no longer serves a Jekyll-hosted page. | The corresponding view no longer runs in Jekyll and public output has no Studio shell for it. | done |
| Retire migrated Jekyll Studio route files or replace them with local-only transition redirects. | Each route family has a verified local app view and no public build dependency. | done for operational Studio routes in current scope; remaining UI Catalogue demo pages are intentionally retained until their Local Studio visibility path exists |
| Retire the Jekyll `/studio/` landing shell once the local app owns `/studio/`. | The public site no longer publishes Studio, and the local app home exposes the runtime navigation list. | done |
| Recheck `main.css` and Studio CSS ownership after route retirements. | Migrated Studio surfaces no longer rely on public-site route CSS. | done; retired Docs Broken Links route CSS removed, local activity styles moved to `assets/studio/css/studio.css`, and still-public catalogue search/shared Studio shell styles left in `main.css` where their pages still load them |
| Remove compatibility docs that describe old sibling-service startup as the normal path. | `bin/dev-studio` starts only the local app server plus genuinely required background tasks. | done for default workflow docs; planned cleanup remains for direct `bin/local-studio` implementation and any retired bridge references |
| Extract remaining catalogue write behavior out of the standalone HTTP handler. | Local Studio no longer reuses `catalogue_write_server.Handler` in-process for active catalogue writes. | done; focused service modules now own bulk save, delete preview/apply, publication preview/apply, build preview/apply, moment preview/save, prose/moment import apply, work create/save, work-detail create/save, and series create/save |
| Make `bin/local-studio` independent from `bin/dev-studio` or move shared runner behavior into a neutral helper. | Normal Studio work should be served by `studio_app_server.py`, with public preview handled by plain Jekyll preview/build commands. | planned |
| Retire the standalone `scripts/studio/audit_service.py` HTTP wrapper while keeping reusable audit logic plus direct script/module calls. | The local app owns browser audit endpoints, and Codex does not need a sibling localhost audit service. | done; reusable logic moved to `scripts/studio/audit_runner.py` |

## Phase 5: Route Family Migration

Outcomes:

- active Studio workflows move out of Jekyll route pages
- user-facing workflow behavior remains stable
- old Jekyll route files are retired after local replacements are verified

| Task | Status |
| --- | --- |
| Migrate catalogue editors and dashboards. | done for current scope; Catalogue dashboard, Bulk Add Work, Studio Activity, Catalogue Field Registry, Catalogue Drafts, Studio Works, and the catalogue editor shells are local-app hosted with browser-facing catalogue APIs under `/studio/api/catalogue/...` |
| Migrate analytics/tag routes. | done for current scope; analytics dashboard, tag groups, registry, aliases, series-tags, and per-series tag editor are local-app hosted and use local Analytics APIs |
| Migrate data-sharing routes. | done; dashboard, prepare, and review shells are local-app hosted and use local Docs API Data Sharing endpoints |
| Migrate audit and project-state routes. | done for current scope; Studio Audits shell/API, Project State shell/report API, and Thumbnail Quality shell/refresh API are local-app hosted |
| Add an explicit public-site link resolver for Studio links to works, series, moments, `/library/`, and `/analysis/`. | done for currently migrated local Studio routes; runtime config exposes public-preview and production bases, `studio-navigation.js` has `buildPublicSiteUrl(...)`, per-series tag editor, catalogue editor summaries, and Studio Works share `catalogue-public-links.js` for public catalogue links, and the audited migrated surfaces do not expose `/library/` or `/analysis/` public-content links |
| Replace ad hoc Studio route query concatenation with the shared route URL builder as routes are migrated. | done for current migrated record-param links; fixed dashboard/nav links may remain static when they do not append dynamic params |
| Retire Jekyll Studio route files after each replacement is verified. | done for operational Studio routes in current scope; remaining `studio/ui-catalogue/demos/` pages are isolated UI reference surfaces rather than retired workflow shells |
| Retire the Jekyll `/studio/` landing shell after the local app owns `/studio/`. | done |
| Retire `/studio/docs-broken-links/` only after the Docs Viewer report replacement exists. | done |
| Keep temporary redirects only where useful for local transition ergonomics. | done; no transition redirects were needed for current route retirement |
| Make UI Catalogue demos visible in Local Studio. | planned; demos should be treated as first-class non-mutating Studio reference surfaces and exposed from local Studio because they are not public-site pages |

Next steps:

Batch by route family and workflow risk.
Do not migrate routes only for tidiness; each slice should end with a verified local app view and a clear retirement or compatibility decision for the Jekyll route.
When future route families include links to public content, resolve those links through a configured local Jekyll preview base.
Do not let relative public-content links stay on the Studio app host, and do not default them to dotlineform.com except for explicit live-site actions.
The current migrated route audit is complete; future migrated routes should use `buildPublicSiteUrl(...)` or `catalogue-public-links.js` when they introduce public-content links.
Detailed implementation rules for future route migrations, public-link resolver use, route URL builder use, and UI Catalogue visibility live in [Development Checklist](/docs/?scope=studio&doc=development-checklist).
Catalogue dashboard, Studio Audits, Project State, Thumbnail Quality, Bulk Add Work, Studio Activity, Catalogue Field Registry, Catalogue Drafts, Studio Works, and the Catalogue Series/Work/Work Detail/Moment editor shells are the first operational route shells moved in Phase 5.
They keep the existing vanilla browser modules and unavailable-service behavior, and only change the host shell from Jekyll to the local app.
The catalogue API calls behind Catalogue dashboard counts, Catalogue Drafts, Bulk Add Work, Studio Activity, and the catalogue editors are now consolidated into the local app server.
The Catalogue dashboard keeps the existing `studio-dashboard.js` metric hydration and now links to manage-mode local Catalogue routes.
The Analytics dashboard also uses `studio-dashboard.js` and links to the local Analytics tag routes.
Catalogue Field Registry is read-only and uses checked-in Studio data, so it does not add a new write/API consolidation dependency.
Catalogue Drafts reads draft record data through the local app catalogue read API.
Studio Works is read-only and uses checked-in index data, but it also adopts the public-site link resolver so work and series links open against the configured public Jekyll preview host.
Studio Works now uses the same catalogue public-link helper as the catalogue editors and per-series tag editor, so missing public-site base config fails closed instead of silently building Studio-host-relative public links.
The per-series tag editor now uses the same catalogue public-link helper for public series/work header links instead of maintaining a route-local resolver.
Catalogue editor summaries now share `assets/studio/js/catalogue-public-links.js` for public work, series, work detail, and moment links.
Those links resolve through the configured public preview base during local Studio sessions, while editor-to-editor links continue to use local Studio routes.
The catalogue editor API consolidation keeps behavior aligned with the existing catalogue write handler by invoking it in-process from `scripts/studio/studio_catalogue_api.py`.
Catalogue route shells are split into `scripts/studio/studio_catalogue_views.py` so `studio_app_views.py` remains a shared shell module rather than absorbing every route family.
The Jekyll `/studio/` landing shell is now retired because the local app owns `/studio/` and public builds should not expose Studio.
The local app home is intentionally a simple runtime navigation list rather than a preserved Jekyll dashboard design; it filters out non-nav internal views such as the per-series tag editor and marks the home root ready for smoke checks.
Configured catalogue editor routes now keep `?mode=manage` in runtime/static config.
Browser callers that add `work=`, `detail=`, `series=`, or `moment=` parameters use the shared route URL builder instead of string concatenation, so the migration can preserve manage mode without depending on Jekyll-style query assembly.
The UI Catalogue demo routes remain visible only through the Jekyll route source today.
They should be exposed as first-class local Studio reference surfaces even though they do not mutate catalogue data.
They should keep their isolated demo namespace and ready-state contract rather than being treated as production Studio workflow routes.

## Phase 6: Projection And Build Contract

Outcomes:

- canonical source, public projections, Studio projections, and Docs Viewer payloads are clearly separated
- Jekyll public builds consume only intended public source/projection files
- source-only fields can remain in canonical data without leaking into public runtime artifacts

| Task | Status |
| --- | --- |
| Document canonical source families and their public projections. | planned |
| Distinguish public projections, Studio projections, and Docs Viewer payloads in docs and checks. | planned |
| Add checks for source-only fields leaking into public projections. | planned |
| Verify Jekyll consumes public projections rather than Studio-only data. | planned |
| Keep generated output paths explicit and boring. | planned |

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
| Review files that now belong to public site, Studio app, canonical data, Docs Viewer, and generated outputs. | planned |
| Decide whether to keep one repo, split public-site and Studio repos, or extract Docs Viewer first. | planned |
| Identify deployment, publishing, and local development benefits required to justify a split. | planned |
| If splitting, define the publish/export contract before moving files. | planned |

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
