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

Current mounted views:

- `/studio/`
- `/docs/`
- `/studio/analytics/tag-groups/`

Current app endpoints:

- `/health`
- `/studio/runtime-config.json`

The Tag Groups view reuses the existing Studio CSS, `assets/studio/js/tag-groups.js`, and the route-ready data attributes.
Migrated views can opt into the local runtime config endpoint with `meta[name="dlf-studio-config-url"]`.
The endpoint currently also exposes the local app view registry that powers the shell navigation.
`assets/studio/js/studio-navigation.js` provides the first helper over that registry: migrated links can declare `data-studio-navigate="<view-id>"` while retaining a real `href` fallback.
The local `/docs/` route hosts the Docs Viewer management shell through the Python app server while still using the existing Docs Viewer JavaScript, CSS, config, and generated docs payloads.
Its management API base is `/studio/api/docs`; this currently exposes real scope availability through `/studio/api/docs/capabilities` and serves generated docs read endpoints while keeping write capabilities disabled until those routes migrate into the app server.
This first server is intentionally narrow and does not yet own write-service APIs or app-wide navigation.
The app server is split before broader route migration: `studio_app_server.py` owns request dispatch and process startup, `studio_app_config.py` owns local runtime/view config, `studio_app_views.py` owns HTML shells, and `studio_docs_api.py` owns the Docs Viewer API adapter.
New route families should follow that module-boundary pattern rather than expanding the server entrypoint.
