---
doc_id: local-studio-app
title: Local Studio App
added_date: "2026-05-22 08:06"
last_updated: 2026-05-30
parent_id: studio
---
# Local Studio App

This section documents the current Local Studio app runtime: the app server, route shells, runtime configuration contract, local API ownership, and focused checks for Studio-only workflows.

Local Studio is intentionally separate from the public dotlineform.com site.
Use `bin/local-studio` for Studio authoring and `bin/public-site-preview` or `bin/public-site-build` for public Jekyll preview/build work.
The public publishing boundary is documented in [Projection Contract](/docs/?scope=studio&doc=data-models-projection-contract).

## Current App Server

The Python local Studio app server can be started directly:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/studio_app_server.py --port 8765
```

`bin/local-studio` starts this app server without Jekyll.
Use `STUDIO_APP_ENABLED=0` to skip it, or `STUDIO_APP_PORT=<port>` to move it when `8765` is already in use.
HTTP access logging is quiet by default so normal browser use does not flood the terminal.
Set `STUDIO_APP_ACCESS_LOG=1` for `bin/local-studio`, or pass `--access-log` to `studio_app_server.py`, when detailed request logging is needed.
Docs Viewer management is handled by the standalone Docs Viewer service.
Active Local Studio browser routes use plain external Docs Viewer links from `external_links.docs_viewer` in `studio/app/frontend/config/studio-config.json`.
Per-page Docs Viewer doc IDs live in `app.routes[*].doc_id` so user-guidance targets can be changed in the route registry without editing Python.
Local Studio renders Docs Viewer links without probing service availability; when the Docs Viewer service is stopped, the links fail like normal external links.
Analytics and Data Sharing routes are handled by the standalone Local Analytics app, not Local Studio.
Public-site preview and public builds now have explicit commands: `bin/public-site-preview` and `bin/public-site-build`.
`bin/public-site-preview` uses `_config.yml` by default and does not start Studio services.
Local Studio route shells load Studio-owned CSS from `/studio/app/assets/css/studio.css`.
They no longer depend on public `assets/css/main.css` for Studio base typography, spacing, shell layout, or Studio-only primitive classes.

Current mounted views:

- `/studio/`
- `/studio/audits/?mode=manage`
- `/studio/project-state/?mode=manage`
- `/studio/bulk-add-work/?mode=manage`
- `/studio/activity/?mode=manage`
- `/studio/catalogue-field-registry/?mode=manage`
- `/studio/catalogue-status/?mode=manage`
- `/studio/studio-works/?mode=manage`
- `/studio/catalogue-series/?mode=manage`
- `/studio/catalogue-work/?mode=manage`
- `/studio/catalogue-work-detail/?mode=manage`
- `/studio/catalogue-moment/?mode=manage`

The local app owns `/studio/`.
Studio home navigation is a local-app owned grouped column-links layout, not Jekyll/Liquid page data.
The local home exposes Studio-owned Catalogue and Admin links using static route targets so labels, order, and query-string defaults stay deliberate.
The shared Studio top navigation is separate from that home link list.
Every local Studio shell, including `/studio/`, shows the same compact top row: `dotlineform studio` on the left, with `docs` plus the light/dark toggle right-aligned.
The former Catalogue dashboard page is retired; its links now live on the `/studio/` home page, and metrics belong on the individual pages where they are relevant.

Current app endpoints:

- `/health`
- `/studio/runtime-config.json`
- `/studio/api/catalogue/health`
- `/studio/api/catalogue/read`
- `POST /studio/api/catalogue/import-preview`
- `POST /studio/api/catalogue/import-apply`
- `POST /studio/api/catalogue/project-state-report`
- `POST /studio/api/catalogue/bulk-save`
- `POST /studio/api/catalogue/work/create`
- `POST /studio/api/catalogue/work/save`
- `POST /studio/api/catalogue/work-detail/create`
- `POST /studio/api/catalogue/work-detail/save`
- `POST /studio/api/catalogue/series/create`
- `POST /studio/api/catalogue/series/save`
- `POST /studio/api/catalogue/delete-preview`
- `POST /studio/api/catalogue/delete-apply`
- `POST /studio/api/catalogue/publication-preview`
- `POST /studio/api/catalogue/publication-apply`
- `POST /studio/api/catalogue/build-preview`
- `POST /studio/api/catalogue/build-apply`
- `POST /studio/api/catalogue/prose/import-preview`
- `POST /studio/api/catalogue/prose/import-apply`
- `POST /studio/api/catalogue/moment/import-preview`
- `POST /studio/api/catalogue/moment/import-apply`
- `POST /studio/api/catalogue/moment/preview`
- `POST /studio/api/catalogue/moment/save`

Analytics tag and Data Sharing routes moved out of Local Studio.
The active route shells are served by `bin/local-analytics` under `/analytics/...`.
The active tag APIs are under `/analytics/api/...`, and active Data Sharing APIs are under `/analytics/api/data-sharing/...`.
Retired Studio paths such as `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, and `/studio/api/data-sharing/...` intentionally have no aliases, proxies, or static shims.
The Studio Audits route shell is hosted by the local app at `/studio/audits/?mode=manage`.
It is rendered through the JavaScript Studio app shell: Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/studio-audits-shell.js` renders the route body, and `studio/app/frontend/js/studio-audits.js` keeps the existing route boot and behavior.
It calls `/studio/api/audits/...` on the local app server.
`studio/app/server/studio/studio_audit_api.py` adapts the allowlisted audit functions from `studio/app/server/studio/audit_runner.py`, so normal Studio sessions no longer need a separate audit sibling service.
The old Jekyll `/studio/audits/` shell has been retired.
The Project State route shell is hosted by the local app at `/studio/project-state/?mode=manage`.
It is the first route rendered through the JavaScript Studio app shell: Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/project-state-shell.js` renders the route body, and `studio/app/frontend/js/project-state.js` keeps the existing route boot and behavior.
It calls Local Studio for both catalogue report generation and local report opening.
`studio/app/server/studio/studio_catalogue_api.py` owns the narrow `POST /studio/api/catalogue/project-state-report` and `POST /studio/api/catalogue/project-state-open-report` adapters and reuses `studio/services/catalogue/project_state_report.py`.
The old Jekyll `/studio/project-state/` shell and Python-rendered Project State body have been retired.
The Thumbnail Quality route shell is no longer an active Local Studio route.
`/studio/thumbnail-quality/?mode=manage`, `POST /studio/api/catalogue/thumbnail-quality-preview`, and static thumbnail-quality preview data under `/studio/data/generated/thumbnail-quality/` are retired and intentionally have no Studio aliases, proxies, or static-serving shims.
The retired implementation has been archived under `studio/retired/thumbnail-quality/` for reference outside public Jekyll output.
The Bulk Add Work route shell is hosted by the local app at `/studio/bulk-add-work/?mode=manage`.
It is rendered through the JavaScript Studio app shell: Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/bulk-add-work-shell.js` renders the route body, and `studio/app/frontend/js/bulk-add-work.js` keeps the existing route boot and behavior.
It reuses the existing workflow helper module, the configured workbook path from `app.runtime.pipeline.workbooks.bulk_import` derived from `_data/pipeline.json`, and local-app `POST /studio/api/catalogue/import-preview` and `POST /studio/api/catalogue/import-apply` endpoints.
The old Jekyll `/studio/bulk-add-work/` shell and Python-rendered Bulk Add Work body have been retired.
The Studio Activity route shell is hosted by the local app at `/studio/activity/?mode=manage`.
It is rendered through the JavaScript Studio app shell: Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/activity-log-shell.js` renders the route body, and `studio/app/frontend/js/activity-log.js` keeps the existing route boot and behavior.
It reuses `studio/app/frontend/js/activity-log-modals.js` and `GET /studio/api/catalogue/read?key=activity_log` on the local app server.
The old Jekyll `/studio/activity/` shell and Python-rendered Studio Activity body have been retired.
The Catalogue Field Registry route shell is hosted by the local app at `/studio/catalogue-field-registry/?mode=manage`.
It is rendered through the JavaScript Studio app shell: Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/catalogue-field-registry-shell.js` renders the route body, and `studio/app/frontend/js/catalogue-field-registry-review.js` keeps the existing route boot and behavior.
It reuses the checked-in `studio/data/config/catalogue/catalogue-field-registry.json` read-only data source.
The old Jekyll `/studio/catalogue-field-registry/` shell and Python-rendered Catalogue Field Registry body have been retired.
The Catalogue Drafts route shell is hosted by the local app at `/studio/catalogue-status/?mode=manage`.
It is rendered through the JavaScript Studio app shell: Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/catalogue-status-shell.js` renders the route body, and `studio/app/frontend/js/catalogue-status.js` keeps the existing route boot and behavior.
It reuses local-app catalogue read keys under `GET /studio/api/catalogue/read`.
The old Jekyll `/studio/catalogue-status/` shell and Python-rendered Catalogue Drafts body have been retired.
The Studio Works route shell is hosted by the local app at `/studio/studio-works/?mode=manage`.
It is rendered through the JavaScript Studio app shell: Python serves the generic `#studioApp` bootstrap, `studio/app/frontend/js/studio-app.js` renders the shared shell chrome, `studio/app/frontend/js/studio-works-shell.js` renders the route body, and `studio/app/frontend/js/studio-works.js` keeps the existing route boot and behavior.
It reuses checked-in works/series indexes and the Studio-only work storage index.
The Python-rendered Studio Works body has been retired.
The old Jekyll `/studio/studio-works/` shell has been retired.
Its work and series links now resolve through the configured public-site preview base rather than staying on the Studio app host.
The Catalogue Series, Work, Work Detail, and Moment editor route shells are hosted by the local app at their `?mode=manage` routes.
They reuse the existing vanilla editor modules and call local-app catalogue API endpoints under `/studio/api/catalogue/...`.
The old Jekyll shells for `/studio/catalogue-series/`, `/studio/catalogue-work/`, `/studio/catalogue-work-detail/`, and `/studio/catalogue-moment/` have been retired.
The local app adapter routes editor save, bulk save, build, publication, delete, prose import, and moment import flows through focused catalogue service modules.
`bin/local-studio` no longer starts a standalone catalogue write server; catalogue APIs are owned by the Local Studio app server.
The local app is the only active Studio home surface.
Local app views declare the runtime config endpoint with `meta[name="dlf-studio-config-url"]`.
The endpoint exposes the local app runtime contract for migrated views:

- `app.routes` route ids, labels, paths, scripts, doc IDs, shell types, ready-state route IDs, and navigation visibility
- runtime view records derived from `app.routes`
- local service endpoints such as `/studio/api/catalogue`
- plain external link config such as `external_links.docs_viewer`
- generated data, search, and UI-text paths from the checked-in Studio config
- media and thumbnail bases used by Studio previews
- pipeline variant and workbook metadata from `_data/pipeline.json`
- modal event constants

`studio/app/frontend/js/studio-navigation.js` provides the first helper layer over that contract.
Migrated links can declare `data-studio-navigate="<view-id>"` while retaining a real `href` target for normal link behavior.
The same module exposes `navigateTo(view, params)`, public-site URL helpers, and `openModal(name, params)` dispatch through the `studio:open-modal` event.
This adapter is deliberately small and does not introduce a route framework.
`studio/app/frontend/js/studio-config.js` also exposes `buildStudioRouteUrl(config, key, params)`.
Use it when a browser module needs to append record parameters to a configured Studio route, because configured local routes may already contain transition state such as `?mode=manage`.
Studio-to-public-content links use an explicit second boundary because Studio and the public Jekyll preview are separate local servers.
The contract is:

- Studio app routes open on the local Studio app server
- Docs management routes open through the configured Docs Viewer external link
- public content routes such as `/works/...`, `/series/...`, `/library/`, and `/analysis/` open against the local Jekyll preview when it is running
- production `https://dotlineform.com` links are used only for explicit live-site actions

The runtime config now exposes `app.runtime.sites.public_preview.base` and `app.runtime.sites.production.base`, and `studio/app/frontend/js/studio-navigation.js` exposes `buildPublicSiteUrl(config, path, params, options)`.
Studio route modules should use that helper when they touch public-content links.
Catalogue editor summaries and Studio Works use this resolver through `studio/app/frontend/js/catalogue-public-links.js` for public catalogue links.
Those links open on the configured public preview host during local Studio sessions; Local Analytics owns its own public-link helper for Analytics routes.
The catalogue helper requires the configured public-site base for public links instead of generating Studio-host-relative public URLs.
Editor-to-editor links remain local Studio routes.
The local `/docs/` route is no longer hosted by Local Studio.
The runtime config exposes the plain Docs Viewer link target for the top-level `docs` view.
Page implementation links render with `data-studio-doc-view`; the browser resolves those targets from the matching route record's `doc_id`.
The browser builds external Docs Viewer URLs from `external_links.docs_viewer` plus the route `doc_id`.
Data Sharing endpoints are no longer published by Local Studio runtime config.
The main management API workflow routes are covered through a fixture repo smoke that exercises create, metadata edit, move, delete, source-config settings, import listing, rebuild, and scope lifecycle paths through the standalone Docs Viewer service without touching real docs.
Docs Viewer fixture smokes cover `/docs/` manage-mode workflows through the Docs Viewer service UI: create, metadata edit, settings save, delete preview/apply, staged import, drag/drop move, scope create/delete, and generated data reloads after each source mutation.
Public `/library/` and `/analysis/` are covered by a separate read-only smoke against the public Jekyll build.
That check verifies management CSS, management controls, management base URLs, and Studio-only assets are absent.
The app server is split by ownership: `studio_app_server.py` owns request dispatch and process startup, `studio_app_config.py` owns local runtime/view config, `studio_app_views.py` owns shared HTML shells, `studio_catalogue_views.py` owns catalogue route shells, `studio_audit_api.py` owns the Studio audit API adapter, and `studio_catalogue_api.py` owns the Catalogue API adapter.
New route families should follow that module-boundary pattern rather than expanding the server entrypoint.

Current focused checks:

- `studio/tests/python/test_studio_app_server.py`
- `studio/tests/smoke/local_studio_navigation_adapter.py`
- `studio/tests/smoke/local_studio_app_audits_route.py`
- `studio/tests/smoke/local_studio_app_project_state_route.py`
- `studio/tests/smoke/local_studio_app_bulk_add_work_route.py`
- `studio/tests/smoke/local_studio_app_activity_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_field_registry_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_status_route.py`
- `studio/tests/smoke/local_studio_app_studio_works_route.py`
- `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`
- `studio/tests/smoke/local_studio_app_docs_viewer.py`
- `analytics-app/tests/python/test_analytics_app_server.py`
- `analytics-app/tests/python/test_analytics_data_sharing_api.py`
- `analytics-app/tests/smoke/local_analytics_app_tag_routes.py`
- `analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py`
- `docs-viewer/tests/smoke/docs_viewer_management_workflows.py`
- `docs-viewer/tests/smoke/docs_viewer_management_ui.py`
- `docs-viewer/tests/smoke/docs_viewer_management_import_ui.py`
- `docs-viewer/tests/smoke/docs_viewer_management_move_ui.py`
- `docs-viewer/tests/smoke/docs_viewer_management_scope_ui.py`
- `docs-viewer/tests/smoke/public_docs_viewer_readonly.py`
