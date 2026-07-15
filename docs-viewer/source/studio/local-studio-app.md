---
doc_id: local-studio-app
title: Local Studio App
added_date: "2026-05-22 08:06"
last_updated: 2026-07-15
summary: Operational boundary of the loopback Studio app server, runtime config, static serving, and catalogue API adapter.
parent_id: studio
viewable: true
---
# Local Studio App

## Server Boundary

The Local Studio app is a loopback Python server. It owns:

- registered `/studio/...` page shells
- `/studio/runtime-config.json`
- catalogue APIs under `/studio/api/catalogue/...`
- confined Studio-owned static and project-media reads

It does not serve the deployed public site or proxy Docs Viewer, Analytics, Data Sharing, or Admin.

Start it through `bin/local-studio`. Direct execution is useful for focused service work:

```bash
$HOME/miniconda3/bin/python3 studio/app/server/studio/studio_app_server.py --port 8765
```

`STUDIO_APP_PORT` changes the runner port, `STUDIO_APP_ENABLED=0` suppresses the server, and `STUDIO_APP_ACCESS_LOG=1` enables ordinary access logs.

## Runtime Config

The server reads and validates `studio/app/frontend/config/studio-config.json`, then builds `/studio/runtime-config.json` from:

- checked-in `app.routes` and `paths.data.studio`
- Python-owned service endpoint, media, modal, and production-site constants
- environment-backed public preview configuration
- pipeline variants, encoding, and workbook paths from `_data/pipeline.json`
- derived asset version and runtime view records

The source JSON is therefore not the complete runtime payload. [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json) owns the source and projection contract.

## Request Dispatch

- `studio_app_server.py` owns HTTP parsing, shell/static responses, runtime-config dispatch, catalogue prefix dispatch, containment, limits, and process startup.
- `studio_app_config.py` owns config loading, route validation, runtime projection, and asset versioning.
- `studio_catalogue_api.py` owns the HTTP-to-catalogue adapter and delegates mutations to focused services under `studio/services/catalogue/`.

The server entrypoint should remain a dispatcher. New catalogue behavior belongs in a domain service before it is exposed through the adapter.

## Sibling Services

- Docs Viewer serves `/docs/` and its own management APIs.
- Local Analytics serves `/analytics/...` and Analytics-hosted Data Sharing APIs.
- Local Admin serves `/admin/...` operational routes.
- `bin/site-preview` serves tracked `site/` output without Studio authority.

Retired `/studio/analytics/...`, `/studio/data-sharing/...`, and related API paths have no aliases or proxies.

## Safety And Failure

- The service is loopback-only and accepts explicit request shapes.
- Static and project-media paths are resolved beneath allowlisted roots.
- JSON bodies have a size limit and must be objects.
- Catalogue writes remain behind server-side validation and atomic source transactions.
- When the service is unavailable, Studio routes expose unavailable state; there is no offline write mode.

## Code And Test Authority

- server: `studio/app/server/studio/`
- catalogue domain: `studio/services/catalogue/`
- server/config tests: `studio/tests/python/test_studio_app_runtime_config.py` and route/API tests under `studio/tests/python/`
- route integration: focused checks under `studio/tests/smoke/`

[Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes) and [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis) hold the exact current inventories.
