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
- `/studio/analytics/tag-groups/`

Current app endpoints:

- `/health`
- `/studio/runtime-config.json`

The Tag Groups view reuses the existing Studio CSS, `assets/studio/js/tag-groups.js`, and the route-ready data attributes.
Migrated views can opt into the local runtime config endpoint with `meta[name="dlf-studio-config-url"]`.
The endpoint currently also exposes the local app view registry that powers the shell navigation.
This first server is intentionally narrow and does not yet own write-service APIs or app-wide navigation.
