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

Current mounted views:

- `/studio/`
- `/docs/`
- `/studio/analytics/tag-groups/`

Current app endpoints:

- `/health`
- `/studio/runtime-config.json`
- `/studio/api/analytics/tag-registry`
- `/studio/api/analytics/tag-aliases`
- `/studio/api/analytics/tag-assignments`
- `/studio/api/analytics/tag-groups`
- `POST /studio/api/analytics/import-tag-assignments-preview`
- `POST /studio/api/analytics/import-tag-assignments`
- `POST /studio/api/analytics/import-tag-registry`
- `POST /studio/api/analytics/mutate-tag-preview`
- `POST /studio/api/analytics/mutate-tag`
- `POST /studio/api/analytics/save-tags`
- `/studio/api/docs/capabilities`
- `/studio/api/docs/docs/generated/...`
- `/studio/api/docs/docs/...` management GET/POST routes migrated from the Docs management server

The Tag Groups view reuses the existing Studio CSS, `assets/studio/js/tag-groups.js`, and the route-ready data attributes.
In the local app it reads group-description data through `/studio/api/analytics/tag-groups`; unmigrated/Jekyll contexts still fall back to the static `assets/studio/data/tag_groups.json` path.
The shared Studio data loader also uses local analytics read endpoints for tag registry, aliases, and assignments when the local runtime config advertises them.
The first analytics write routes are `POST /studio/api/analytics/save-tags`, `POST /studio/api/analytics/import-tag-assignments-preview`, `POST /studio/api/analytics/import-tag-assignments`, `POST /studio/api/analytics/import-tag-registry`, `POST /studio/api/analytics/mutate-tag-preview`, and `POST /studio/api/analytics/mutate-tag`.
They reuse the existing tag assignment, registry mutation, alias rewrite, atomic JSON write, backups, compact script logging, and Studio activity helpers from the tag write-service domain modules.
The browser transport now prefers these local runtime endpoints for `saveTags`, assignment import, registry import, registry edit/delete, and analytics health when a migrated local app page has runtime config; old `127.0.0.1:8787` endpoints remain fallbacks for unmigrated Jekyll-hosted pages.
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
The local `/docs/` route hosts the Docs Viewer management shell through the Python app server while still using the existing Docs Viewer JavaScript, CSS, config, and generated docs payloads.
Its management API base is `/studio/api/docs`; this now exposes live configured-scope availability and Docs management capabilities, serves generated docs read endpoints, and calls the existing Docs management domain functions directly for migrated management routes.
The main management API workflow routes are covered through a temporary fixture repo smoke that exercises create, metadata edit, move, archive, delete, source-config settings, import listing, rebuild, and scope lifecycle paths through the local app server without touching real docs.
Browser-level fixture smokes cover local `/docs/` manage-mode workflows through the actual UI: create, metadata edit, settings save, archive, delete preview/apply, staged import, drag/drop move, scope create/delete, and generated data reloads after each source mutation.
Data-sharing UI behavior is intentionally deferred to a later cross-Studio adapter consolidation slice.
Public `/library/` and `/analysis/` are covered by a separate read-only smoke against the public Jekyll build.
That check verifies management CSS, management controls, management base URLs, and Studio-only assets are absent.
The server is still intentionally narrow and does not yet own catalogue, the broader analytics alias and promote/demote mutation set, audit, or app-wide navigation APIs.
The app server is split before broader route migration: `studio_app_server.py` owns request dispatch and process startup, `studio_app_config.py` owns local runtime/view config, `studio_app_views.py` owns HTML shells, `studio_docs_api.py` owns the Docs Viewer API adapter, and `studio_analytics_api.py` owns the first analytics API adapter.
New route families should follow that module-boundary pattern rather than expanding the server entrypoint.

Current focused checks:

- `tests/python/test_studio_app_server.py`
- `tests/smoke/local_studio_navigation_adapter.py`
- `tests/smoke/local_studio_app_tag_groups.py`
- `tests/smoke/local_studio_app_docs_viewer.py`
- `tests/smoke/local_studio_docs_management_workflows.py`
- `tests/smoke/local_studio_docs_management_ui.py`
- `tests/smoke/local_studio_docs_management_import_ui.py`
- `tests/smoke/local_studio_docs_management_move_ui.py`
- `tests/smoke/local_studio_docs_management_scope_ui.py`
- `tests/smoke/public_docs_viewer_readonly.py`
