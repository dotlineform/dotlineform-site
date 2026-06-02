---
doc_id: config-studio-config-json
title: Studio Config JSON
added_date: 2026-04-24
last_updated: 2026-06-02
parent_id: studio
viewable: true
---
# Studio Config JSON

Config file:

- `studio/app/frontend/config/studio-config.json`

See also:

- [Config Files Inventory](/docs/?scope=studio&doc=config-files-inventory)
- [Studio UI Text Config](/docs/?scope=studio&doc=config-studio-ui-text-json)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)

## Contract Role

`studio-config.json` is the source browser-facing manifest for the Local Studio app.
The local app server reads it, validates the Local Studio route registry, injects runtime details, and serves the combined payload as the Studio runtime config.

The file currently owns:

- Local Studio route shell metadata under `app.routes`
- Studio data path lookup under `paths.data.studio`
- Studio UI-text bundle path lookup under `paths.data.ui_text`

It does not own:

- Analytics app routes or Analytics tag runtime policy
- Data Sharing adapter behavior or source-write policy
- Docs Viewer scope, route, status, or UI-text configuration
- public catalogue route construction policy
- service endpoint contracts injected by the local app server
- generated payload schemas

## What Reads It

Current readers include:

- `studio/app/server/studio/studio_app_config.py`, which loads the file, validates `app.routes`, injects `app.runtime`, and serves the runtime config
- `studio/app/frontend/js/studio-config.js`, which fetches the served runtime config and exposes route, data-path, UI-text, and copy helpers
- `studio/app/frontend/js/studio-app.js`, `studio-navigation.js`, and `studio-route-registry.js`, which use `app.routes` for shell boot and navigation
- route modules that call `loadStudioConfigWithText(group)` and `getStudioText(...)`
- `studio/app/frontend/js/studio-data.js`, which uses Studio data paths for static fallback reads when catalogue server reads are unavailable
- `studio/services/catalogue/catalogue_field_registry.py`, which resolves the catalogue field registry path from `paths.data.studio.catalogue_field_registry`

## Runtime Shape

The source file is not the full runtime payload.
`studio_app_config.py` adds `app.runtime` at serve time.

Runtime-injected values include:

- local app host and asset version
- runtime endpoint paths such as `/studio/runtime-config.json`
- Local Studio service endpoint paths
- public preview and production site bases
- media and pipeline defaults
- resolved view records derived from `app.routes`
- navigation and modal runtime metadata

Do not add those injected values to the source JSON unless the server contract changes.

## Edit Class

This file is maintainer-editable code infrastructure.
It is not a user preference file.

Safe edits require matching code/tests when they change:

- route ids, paths, scripts, navigation flags, shell type, or ready-state ids
- data path keys used by route modules
- UI-text bundle path keys
- catalogue option lists used by route modules

## Active Sections

### `app.routes`

Local Studio route shell registry.
Each route entry must match a served Local Studio route and JavaScript route script.

Validation catches:

- missing required fields
- duplicate route paths
- unsupported shell types
- missing route scripts
- route ids or paths that do not match current served routes
- Studio route metadata left in `paths.routes`

### `paths.data.studio`

Studio data-path lookup.
The current primary use is catalogue static fallback data, catalogue lookup payloads, activity log data, and `catalogue_field_registry`.

Server-backed catalogue reads should prefer the Local Studio catalogue API when available.
Static paths are fallback/runtime asset paths, not write contracts.
`catalogue_lookup_meta` is not exposed because no active Local Studio route consumes the generated lookup metadata payload.

### `paths.data.ui_text`

Maps route UI-text group names to files under `studio/app/frontend/config/ui-text/`.
The text bundle contract is documented in [Studio UI Text Config](/docs/?scope=studio&doc=config-studio-ui-text-json).

## Cleanup Review

Completed cleanup:

- `paths.routes` has been removed from the source file
- stale public/content route keys such as `library_page`, `search`, `series_page_base`, `works_page_base`, `moments_page_base`, and stale `work_details_page_base` have been removed from Local Studio config
- unused `studio-config.js` helper exports for site data, Docs scope data, search scope indexes, and search policy paths have been removed
- public moment URL construction now lives with the public catalogue link helper instead of generic Studio route lookup
- focused tests assert that runtime `data_paths` exposes only `studio` and `ui_text`
- unused `paths.data.ui_text.site_series_index` and its orphaned `site-series-index.json` bundle have been removed
- unused `paths.data.studio.catalogue_lookup_meta` has been removed
- `catalogue.series_type_options` has been removed from broad Studio bootstrap config; the Series editor owns its current option list in `catalogue-series-fields.js`

Recommended verification for the cleanup pass:

- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py`
- focused browser/module smoke for Studio navigation and catalogue public links
