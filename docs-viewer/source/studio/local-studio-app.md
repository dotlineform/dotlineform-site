---
doc_id: local-studio-app
title: Local Studio App
added_date: "2026-05-22 08:06"
last_updated: 2026-06-12
parent_id: studio
viewable: true
---
# Local Studio App

This document defines the operational boundary for the Local Studio app server.

- Use [Studio Runtime](/docs/?scope=studio&doc=studio-runtime) for the browser shell, route registry, shared runtime modules, and sibling-app boundary.
- Use [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes) for the mounted route inventory and route-local shell ownership.
- Use [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis) for endpoint groups and server adapter ownership.

Local Studio is intentionally separate from the public dotlineform.com site.

- Use `bin/local-studio` for Studio authoring and `bin/public-site-preview` or `bin/public-site-build` for public static preview/build work.

The public publishing boundary is documented in [Projection Contract](/docs/?scope=studio&doc=data-models-projection-contract).

## Server Boundary

The Python local Studio app server can be started directly:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/studio_app_server.py --port 8765
```

`bin/local-studio` starts this app server without Jekyll.
Use `STUDIO_APP_ENABLED=0` to skip it, or `STUDIO_APP_PORT=<port>` to move it when `8765` is already in use.
HTTP access logging is quiet by default so normal browser use does not flood the terminal.
Set `STUDIO_APP_ACCESS_LOG=1` for `bin/local-studio`, or pass `--access-log` to `studio_app_server.py`, when detailed request logging is needed.

The app server owns:

- `/studio/` and active Local Studio catalogue route shells
- `/studio/runtime-config.json`
- Catalogue read/write APIs under `/studio/api/catalogue/...`
- local report-opening adapters for Studio-owned workflows

The app server does not own:

- public static preview/build routes
- Docs Viewer management routes or Docs Viewer static/runtime assets
- Local Analytics routes or `/analytics/api/...`
- Local Admin routes or `/admin/api/...`
- UI Catalogue routes
- retired audit, risk, activity, testing, Analytics/Data Sharing, or UI Catalogue Studio aliases
- retired standalone catalogue write, tag write, audit-service, or thumbnail-quality route shims

## Runtime Config

Local app views declare the runtime config endpoint with `meta[name="dlf-studio-config-url"]`.
`/studio/runtime-config.json` exposes the local app runtime contract for migrated views:

- `app.routes` route ids, labels, paths, scripts, shell types, ready-state route IDs, and navigation visibility
- runtime view records derived from `app.routes`
- local service endpoints such as `/studio/api/catalogue`
- generated data, search, and UI-text paths from checked-in Studio config
- media and thumbnail bases used by Studio previews
- pipeline variant, encoding, and workbook metadata from `_data/pipeline.json`
- modal event constants

The browser-side route and navigation contract is documented in [Studio Runtime](/docs/?scope=studio&doc=studio-runtime).

## Sibling Services

Docs Viewer is a standalone developer resource handled by the standalone Docs Viewer service.
Local Studio does not expose Docs Viewer route metadata, Docs Viewer external-link config, Docs Viewer static/runtime assets, Docs Viewer generated-data passthroughs, or Docs Viewer API adapters.
Use the standalone Docs Viewer service directly when developer documentation is needed.

Analytics and Data Sharing routes are handled by the standalone Local Analytics app, not Local Studio.
The active route shells are served by `bin/local-analytics` under `/analytics/...`.
The active tag APIs are under `/analytics/api/...`, and active Data Sharing APIs are under `/analytics/api/data-sharing/...`.
Retired Studio paths such as `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, and `/studio/api/data-sharing/...` intentionally have no aliases, proxies, or static shims.

Public-site preview and public builds have explicit commands: `bin/public-site-preview` and `bin/public-site-build`.
`bin/public-site-preview` builds and serves the static public artifact and does not start Studio services.

## Server Modules

The app server is split by ownership:

- `studio/app/server/studio/studio_app_server.py`
  owns request dispatch and process startup
- `studio/app/server/studio/studio_app_config.py`
  owns local runtime/view config loading and validation
- `studio/app/server/studio/studio_app_views.py`
  owns the shared HTML bootstrap
- `studio/app/server/studio/studio_catalogue_api.py`
  owns the Catalogue API adapter

Ordinary Studio route body markup is owned by route-local browser shell modules that run inside `studio-app.js`.
New route families should follow that module-boundary pattern rather than expanding the server entrypoint.

## Current Checks

Current focused Local Studio checks are grouped by ownership:

- server and config: `studio/tests/python/test_studio_app_server.py`
- navigation/runtime adapter: `studio/tests/smoke/local_studio_navigation_adapter.py`
- route shells: see [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes)
- Docs Viewer boundary: `studio/tests/smoke/local_studio_app_docs_viewer.py`
- Local Analytics sibling routes and APIs: `analytics-app/tests/python/test_analytics_app_server.py`, `analytics-app/tests/python/test_analytics_data_sharing_api.py`, `analytics-app/tests/smoke/local_analytics_app_tag_routes.py`, and `analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py`
