---
doc_id: local-studio-apis
title: Local Studio APIs
added_date: 2026-06-02
last_updated: 2026-06-06
parent_id: studio
viewable: true
---
# Local Studio APIs

This document is the endpoint and adapter inventory for the Local Studio app server.
Use [Local Studio App](/docs/?scope=studio&doc=local-studio-app) for the server boundary and [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes) for route shell ownership.

## Ownership Rules

Local Studio APIs are loopback-only operational endpoints.
Browser requests should select from explicit local actions; they should not provide arbitrary command text, unchecked filesystem paths, environment values, or unvalidated script flags.

Endpoint ownership is split by adapter:

- `studio/app/server/studio/studio_app_server.py`
  owns request dispatch, health, runtime config routing, and process startup
- `studio/app/server/studio/studio_catalogue_api.py`
  owns Catalogue read/write/build/publication/import/report adapters

## App And Runtime Endpoints

Current app-level endpoints:

- `/health`
- `/studio/runtime-config.json`

## Catalogue API

Current Catalogue endpoints:

- `/studio/api/catalogue/health`
- `/studio/api/catalogue/read`
- `POST /studio/api/catalogue/import-preview`
- `POST /studio/api/catalogue/import-apply`
- `POST /studio/api/catalogue/project-state-report`
- `POST /studio/api/catalogue/project-state-open-report`
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

The local app adapter routes editor save, bulk save, build, publication, delete, prose import, and moment import flows through focused catalogue service modules.
`bin/local-studio` no longer starts a standalone catalogue write server; catalogue APIs are owned by the Local Studio app server.

Current local generated Studio feeds surfaced through this API:

- unified Studio activity via `GET /studio/api/catalogue/read?key=activity_log`

Current mutable catalogue data surfaced through this API:

- catalogue source records
- catalogue lookup/search records
- editor save/create/delete/publication/build/prose-import/moment API flows
- workbook import preview/apply flows
- project-state report generation and local report opening

Catalogue editors and Catalogue Drafts show their existing unavailable/load-failed states instead of reading stale static source JSON.

## Checks

Current focused API checks:

- `studio/tests/python/test_studio_app_server.py`
- route-level smoke checks listed in [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes)
- Docs Viewer service checks listed in [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
