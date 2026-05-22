---
doc_id: local-studio-app
title: Local Studio App
added_date: "2026-05-22 08:06"
last_updated: "2026-05-22 08:06"
parent_id: ""
sort_order: 21000
published: true
viewable: true
---
# Local Studio App

This section describes the development of a local studio web app, separating studio from public dotlineform.com site.

This is a holding space for documentation while migration is underway.

Change request: [Studio Local Vanilla Web App Request](/docs/?scope=studio&mode=manage&doc=site-request-studio-local-vanilla-web-app)

Implementation plan: [Local Studio App Implementation Plan](/docs/?scope=studio&mode=manage&doc=local-studio-app-implementation-plan)

Public surface: [Public Published Surface](/docs/?scope=studio&mode=manage&doc=local-studio-app-public-surface)

## Current App Server

Phase 1 added the first Python local Studio app server:

```bash
./scripts/studio/studio_app_server.py --port 8765
```

`bin/dev-studio` now starts this app server by default during the transition.
Use `STUDIO_APP_ENABLED=0` to skip it, or `STUDIO_APP_PORT=<port>` to move it when `8765` is already in use.
Docs management is handled by this app server by default; `bin/dev-studio` no longer starts `scripts/docs/docs_management_server.py` unless `DOCS_MANAGEMENT_SERVER_ENABLED=1` is set for a fallback/debug run.
Jekyll still starts through `bin/dev-studio` for public-site preview and unmigrated Studio routes until the route migration is complete.
`bin/dev-studio` is a bridge launcher, not the long-term product boundary.
The intended end state is a local Studio app command for Studio workflows and the normal Bundler/Jekyll serve/build commands for public-site preview and publishing.

Current mounted views:

- `/studio/`
- `/docs/`
- `/studio/catalogue/?mode=manage`
- `/studio/analytics/?mode=manage`
- `/studio/analytics/tag-groups/`
- `/studio/analytics/tag-registry/`
- `/studio/analytics/tag-aliases/`
- `/studio/analytics/series-tags/`
- `/studio/analytics/series-tag-editor/?series=<series_id>`
- `/studio/audits/?mode=manage`
- `/studio/project-state/?mode=manage`
- `/studio/thumbnail-quality/?mode=manage`
- `/studio/bulk-add-work/?mode=manage`
- `/studio/activity/?mode=manage`
- `/studio/data-sharing/?mode=manage`
- `/studio/data-sharing/prepare/?mode=manage`
- `/studio/data-sharing/review/?mode=manage`
- `/studio/catalogue-field-registry/?mode=manage`
- `/studio/catalogue-status/?mode=manage`
- `/studio/studio-works/?mode=manage`
- `/studio/catalogue-series/?mode=manage`
- `/studio/catalogue-work/?mode=manage`
- `/studio/catalogue-work-detail/?mode=manage`
- `/studio/catalogue-moment/?mode=manage`

The local app owns `/studio/`.
The old Jekyll `/studio/` landing shell has been retired, so Studio home navigation now comes from the local runtime view registry rather than Jekyll/Liquid page data.
The local home intentionally exposes a plain navigation list for active local views and filters out internal non-nav views such as the per-series tag editor.
The Catalogue dashboard route shell is hosted by the local app at `/studio/catalogue/?mode=manage`.
It reuses the existing dashboard metric module and grouped Catalogue link layout with manage-mode links to the migrated local Catalogue routes.
The old Jekyll `/studio/catalogue/` shell has been retired.
The Analytics dashboard route shell is hosted by the local app at `/studio/analytics/?mode=manage`.
It reuses the existing dashboard metric module and links to the local Analytics tag routes.
The old Jekyll `/studio/analytics/` shell was already retired; the local app now owns the root Analytics entry point.

Current app endpoints:

- `/health`
- `/studio/runtime-config.json`
- `/studio/api/analytics/tag-registry`
- `/studio/api/analytics/tag-aliases`
- `/studio/api/analytics/tag-assignments`
- `/studio/api/analytics/tag-groups`
- `POST /studio/api/analytics/import-tag-assignments-preview`
- `POST /studio/api/analytics/import-tag-assignments`
- `POST /studio/api/analytics/import-tag-aliases`
- `POST /studio/api/analytics/delete-tag-alias`
- `POST /studio/api/analytics/mutate-tag-alias-preview`
- `POST /studio/api/analytics/mutate-tag-alias`
- `POST /studio/api/analytics/promote-tag-alias-preview`
- `POST /studio/api/analytics/promote-tag-alias`
- `POST /studio/api/analytics/demote-tag-preview`
- `POST /studio/api/analytics/demote-tag`
- `POST /studio/api/analytics/import-tag-registry`
- `POST /studio/api/analytics/mutate-tag-preview`
- `POST /studio/api/analytics/mutate-tag`
- `POST /studio/api/analytics/save-tags`
- `/studio/api/docs/capabilities`
- `/studio/api/docs/docs/generated/...`
- `/studio/api/docs/docs/...` management GET/POST routes migrated from the Docs management server
- `/studio/api/docs/data-sharing/...` package preparation, returned-package listing, review, and apply routes

The Tag Groups view reuses the existing Studio CSS, `assets/studio/js/tag-groups.js`, and the route-ready data attributes.
In the local app it reads group-description data through `/studio/api/analytics/tag-groups`.
The shared Studio data loader now requires local analytics read endpoints for tag groups, registry, aliases, and assignments on migrated local-only tag views; it no longer falls back to static `assets/studio/data/tag_*.json` paths for those views, and `studio_config.json` no longer advertises those static tag-data paths as browser data sources.
The public Jekyll config already excludes `assets/studio/`; the dev Studio Jekyll overlay also excludes the four tag source JSON files so legacy Jekyll-side static reads fail during local development.
The analytics write routes now include `POST /studio/api/analytics/save-tags`, tag assignment import preview/apply, tag alias import/delete/edit preview/apply, tag registry import/edit/delete preview/apply, and cross-artifact promote/demote preview/apply.
They reuse the existing tag assignment, alias mutation, registry mutation, promotion/demotion, alias rewrite, assignment rewrite, atomic JSON write, backups, compact script logging, and Studio activity helpers from the analytics tag domain modules.
The legacy tag-server `POST /build-docs` route is deprecated and intentionally not migrated; Docs rebuilds belong to the Docs management API.
The browser transport now requires these local runtime endpoints for `saveTags`, assignment import, alias import/delete/edit/promote/demote, registry import/edit/delete, demote, and analytics health.
The old `127.0.0.1:8787` tag write-server fallback endpoints have been removed from the browser runtime.
Tag registry, tag aliases, series-tags, and the per-series tag editor route shells are now also hosted by the local app with their existing browser modules and DOM contracts.
They use local runtime config and local analytics API reads/writes when served from the local app.
The old Jekyll analytics tag route files have been retired, and `bin/dev-studio` no longer starts `scripts/analytics/tag_write_server.py` by default.
The standalone `scripts/analytics/tag_write_server.py` HTTP entrypoint has been removed; `scripts/studio/studio_analytics_api.py` is the active local HTTP owner for tag writes.
The Studio Audits route shell is also hosted by the local app at `/studio/audits/?mode=manage`.
It reuses `assets/studio/js/studio-audits.js` and the existing audit service on `127.0.0.1:8790`; that audit service remains a sibling process until the audit API itself is migrated.
The old Jekyll `/studio/audits/` shell has been retired.
The Project State route shell is hosted by the local app at `/studio/project-state/?mode=manage`.
It reuses `assets/studio/js/project-state.js` and the existing sibling catalogue/docs service probes on `127.0.0.1:8788` and `127.0.0.1:8789`; those API calls remain unchanged until a later route-family API consolidation slice.
The old Jekyll `/studio/project-state/` shell has been retired.
The Thumbnail Quality route shell is hosted by the local app at `/studio/thumbnail-quality/?mode=manage`.
It reuses `assets/studio/js/thumbnail-quality.js`, checked-in preview JSON/image data, and the existing sibling catalogue refresh endpoint on `127.0.0.1:8788`.
The old Jekyll `/studio/thumbnail-quality/` shell has been retired.
The Bulk Add Work route shell is hosted by the local app at `/studio/bulk-add-work/?mode=manage`.
The Data Sharing dashboard, package preparation, and returned-package review route shells are hosted by the local app at `/studio/data-sharing/?mode=manage`, `/studio/data-sharing/prepare/?mode=manage`, and `/studio/data-sharing/review/?mode=manage`.
They reuse the existing Data Sharing browser modules and now call Data Sharing through `/studio/api/docs/data-sharing/...` on the local app server.
The old Jekyll route files under `studio/data-sharing/` have been retired.
It reuses `assets/studio/js/bulk-add-work.js`, the existing workflow helper module, the configured workbook path from `_data/pipeline.json`, and the existing sibling catalogue import preview/apply endpoints on `127.0.0.1:8788`.
The old Jekyll `/studio/bulk-add-work/` shell has been retired.
The Studio Activity route shell is hosted by the local app at `/studio/activity/?mode=manage`.
It reuses `assets/studio/js/activity-log.js`, `assets/studio/js/activity-log-modals.js`, and the existing sibling catalogue activity-feed read endpoint on `127.0.0.1:8788`.
The old Jekyll `/studio/activity/` shell has been retired.
The Catalogue Field Registry route shell is hosted by the local app at `/studio/catalogue-field-registry/?mode=manage`.
It reuses `assets/studio/js/catalogue-field-registry-review.js` and the checked-in `assets/studio/data/catalogue_field_registry.json` read-only data source.
The old Jekyll `/studio/catalogue-field-registry/` shell has been retired.
The Catalogue Drafts route shell is hosted by the local app at `/studio/catalogue-status/?mode=manage`.
It reuses `assets/studio/js/catalogue-status.js` and the existing sibling catalogue read service on `127.0.0.1:8788`.
The old Jekyll `/studio/catalogue-status/` shell has been retired.
The Studio Works route shell is hosted by the local app at `/studio/studio-works/?mode=manage`.
It reuses `assets/studio/js/studio-works.js`, checked-in works/series indexes, and the Studio-only work storage index.
The old Jekyll `/studio/studio-works/` shell has been retired.
Its work and series links now resolve through the configured public-site preview base rather than staying on the Studio app host.
The Catalogue Series, Work, Work Detail, and Moment editor route shells are hosted by the local app at their `?mode=manage` routes.
They reuse the existing vanilla editor modules and existing sibling catalogue service endpoints on `127.0.0.1:8788`.
The old Jekyll shells for `/studio/catalogue-series/`, `/studio/catalogue-work/`, `/studio/catalogue-work-detail/`, and `/studio/catalogue-moment/` have been retired.
This slice changes route hosting only; catalogue write/API ownership remains a later route-family API consolidation task.
The old Jekyll `/studio/` landing shell has also been retired.
This removes another public-site Studio page and keeps the local app as the only active Studio home surface during migration.
Migrated views can opt into the local runtime config endpoint with `meta[name="dlf-studio-config-url"]`.
The endpoint exposes the local app runtime contract for migrated views:

- view ids, labels, paths, docs links, and shell navigation groups
- local service endpoints such as `/studio/api/docs` and `/studio/api/analytics`
- generated data, search, and UI-text paths from the checked-in Studio config
- media and thumbnail bases used by Studio previews
- pipeline variant metadata from `_data/pipeline.json`
- modal and transitional state constants

`assets/studio/js/studio-navigation.js` provides the first helper layer over that contract.
Migrated links can declare `data-studio-navigate="<view-id>"` while retaining a real `href` fallback.
The same module exposes `navigateTo(view, params)`, `readStudioInitialState()`, return-context helpers backed by `sessionStorage`, and `openModal(name, params)` dispatch through the `studio:open-modal` event.
This adapter is deliberately small and does not introduce a route framework.
`assets/studio/js/studio-config.js` also exposes `buildStudioRouteUrl(config, key, params)`.
Use it when a browser module needs to append record parameters to a configured Studio route, because configured local routes may already contain transition state such as `?mode=manage`.
Studio-to-public-content links need an explicit second boundary once Studio and the public Jekyll preview are separate local servers.
The target contract is:

- Studio app routes open on the local Studio app server
- Docs management routes open on the local Studio app server
- public content routes such as `/works/...`, `/series/...`, `/library/`, and `/analysis/` open against the local Jekyll preview when it is running
- production `https://dotlineform.com` links are used only for explicit live-site actions

The runtime config should eventually expose a public-site preview base URL and, separately, the production site base URL.
Studio navigation helpers should resolve public-content links through that configured public preview base rather than relying on relative URLs that stay on the Studio app host or silently default to dotlineform.com.
The runtime config now exposes `app.runtime.sites.public_preview.base` and `app.runtime.sites.production.base`, and `assets/studio/js/studio-navigation.js` exposes `buildPublicSiteUrl(config, path, params, options)`.
Route migrations should use that helper when they touch public-content links; existing links are not rewritten automatically.
The migrated per-series tag editor now uses this resolver for its header links to the public series page and primary work page, so those links open on the configured public preview host during local Studio sessions.
The local `/docs/` route hosts the Docs Viewer management shell through the Python app server while still using the existing Docs Viewer JavaScript, CSS, config, and generated docs payloads.
Its management API base is `/studio/api/docs`; this now exposes live configured-scope availability and Docs management capabilities, serves generated docs read endpoints, and calls the existing Docs management domain functions directly for migrated management routes.
The main management API workflow routes are covered through a temporary fixture repo smoke that exercises create, metadata edit, move, archive, delete, source-config settings, import listing, rebuild, and scope lifecycle paths through the local app server without touching real docs.
Browser-level fixture smokes cover local `/docs/` manage-mode workflows through the actual UI: create, metadata edit, settings save, archive, delete preview/apply, staged import, drag/drop move, scope create/delete, and generated data reloads after each source mutation.
Data-sharing UI behavior is intentionally deferred to a later cross-Studio adapter consolidation slice.
Public `/library/` and `/analysis/` are covered by a separate read-only smoke against the public Jekyll build.
That check verifies management CSS, management controls, management base URLs, and Studio-only assets are absent.
The server is still intentionally narrow and does not yet own catalogue, audit API, or app-wide navigation APIs.
The app server is split before broader route migration: `studio_app_server.py` owns request dispatch and process startup, `studio_app_config.py` owns local runtime/view config, `studio_app_views.py` owns shared HTML shells, `studio_catalogue_views.py` owns catalogue route shells, `studio_docs_api.py` owns the Docs Viewer API adapter, and `studio_analytics_api.py` owns the first analytics API adapter.
New route families should follow that module-boundary pattern rather than expanding the server entrypoint.

Current focused checks:

- `tests/python/test_studio_app_server.py`
- `tests/smoke/local_studio_navigation_adapter.py`
- `tests/smoke/local_studio_app_analytics_dashboard_route.py`
- `tests/smoke/local_studio_app_catalogue_dashboard_route.py`
- `tests/smoke/local_studio_app_tag_groups.py`
- `tests/smoke/local_studio_app_tag_routes.py`
- `tests/smoke/local_studio_app_audits_route.py`
- `tests/smoke/local_studio_app_project_state_route.py`
- `tests/smoke/local_studio_app_thumbnail_quality_route.py`
- `tests/smoke/local_studio_app_bulk_add_work_route.py`
- `tests/smoke/local_studio_app_activity_route.py`
- `tests/smoke/local_studio_app_catalogue_field_registry_route.py`
- `tests/smoke/local_studio_app_catalogue_status_route.py`
- `tests/smoke/local_studio_app_studio_works_route.py`
- `tests/smoke/local_studio_app_catalogue_editor_routes.py`
- `tests/smoke/local_studio_app_docs_viewer.py`
- `tests/smoke/local_studio_docs_management_workflows.py`
- `tests/smoke/local_studio_docs_management_ui.py`
- `tests/smoke/local_studio_docs_management_import_ui.py`
- `tests/smoke/local_studio_docs_management_move_ui.py`
- `tests/smoke/local_studio_docs_management_scope_ui.py`
- `tests/smoke/public_docs_viewer_readonly.py`
