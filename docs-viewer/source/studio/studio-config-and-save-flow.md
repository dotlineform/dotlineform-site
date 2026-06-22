---
doc_id: studio-config-and-save-flow
title: Config and Save Flow
added_date: 2026-04-22
last_updated: 2026-06-06
parent_id: studio
viewable: true
---
# Studio Config and Save Flow

This document describes the current shared Studio config, data-loading boundary, and local/offline save behavior.

For file-level ownership of the current config artifacts, see:

- **[Config Files Inventory](/docs/?scope=studio&doc=config-files-inventory)**
- **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
- **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**
- **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**

## Shared Config

Studio configuration is defined in:

- `studio/app/frontend/config/studio-config.json`

It is loaded by:

- `studio/app/frontend/js/studio-config.js`

Current responsibilities:

- Local Studio route shell metadata under `app.routes`
- Studio data path lookup under `paths.data.studio`
- Studio UI-text bundle lookup under `paths.data.ui_text`
- route-local option lists are owned by their route modules rather than broad Studio bootstrap config

Current route/data-path responsibilities do not include Analytics, Data Sharing adapter behavior, or Docs Viewer scope and route policy.
Those contracts live in their own app config families:

- Analytics app config: `analytics-app/app/frontend/config/analytics-config.json`
- Data Sharing adapter config: `data-sharing/config/adapters.json`
- Docs Viewer config: `docs-viewer/config/...`

Known cleanup work remains for legacy public/content route keys and redundant path helpers.
That cleanup is tracked in [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json).

## Shared Data and Transport Modules

`studio/app/frontend/js/studio-data.js` centralizes shared read-side helpers for Studio pages.

Current shared responsibilities include:

- fetching Studio and site JSON payloads from config-derived paths
- fetching derived Studio catalogue lookup payloads plus focused per-record lookup JSON
- registry lookup building
- group-description normalization
- assignment and series data shaping used across Studio pages

`studio/app/frontend/js/studio-transport.js` centralizes the local write-service boundary.

Current responsibilities include:

- local endpoint definitions for both tag and catalogue services
- health probing for local write availability by service
- shared JSON POST transport

Current write endpoints include:

- `/health`
- `/save-tags`
- `/import-tag-assignments-preview`
- `/import-tag-assignments`
- `/import-tag-registry`
- `/mutate-tag`
- `/mutate-tag-preview`
- `/demote-tag`
- `/demote-tag-preview`
- `/import-tag-aliases`
- `/delete-tag-alias`
- `/mutate-tag-alias`
- `/promote-tag-alias`
- `/promote-tag-alias-preview`
- `/studio/api/catalogue/health`
- `/studio/api/catalogue/read`
- `/studio/api/catalogue/bulk-save`
- `/studio/api/catalogue/delete-preview`
- `/studio/api/catalogue/delete-apply`
- `/studio/api/catalogue/publication-preview`
- `/studio/api/catalogue/publication-apply`
- `/studio/api/catalogue/work/create`
- `/studio/api/catalogue/work/save`
- `/studio/api/catalogue/work-detail/create`
- `/studio/api/catalogue/work-detail/save`
- `/studio/api/catalogue/import-preview`
- `/studio/api/catalogue/import-apply`
- `/studio/api/catalogue/moment/import-preview`
- `/studio/api/catalogue/moment/import-apply`
- `/studio/api/catalogue/moment/preview`
- `/studio/api/catalogue/moment/save`
- `/studio/api/catalogue/series/create`
- `/studio/api/catalogue/series/save`
- `/studio/api/catalogue/build-preview`
- `/studio/api/catalogue/build-apply`
- `/studio/api/catalogue/prose/import-preview`
- `/studio/api/catalogue/prose/import-apply`

Current non-catalogue local action behavior also includes:

- the docs viewer manage-mode rebuild action uses the standalone Docs Viewer service and rebuilds the current docs scope plus that scope's docs search
- the legacy tag write-service `POST /build-docs` path is retired and was not migrated into the local Studio app

## Save Modes

The Tag Editor probes local write availability at page load.

Current mode selection:

- if the local app catalogue API responds successfully, Studio uses `Local server`
- otherwise Studio falls back to `Offline session`

### Local Server Mode

Current local save behavior:

- the editor sends `POST /save-tags` to the local app catalogue API
- only the current diff is persisted, not a full materialized export
- work rows are normalized before save
- inherited series tags are not persisted into work rows
- duplicate work tags are collapsed
- optional `alias` metadata is preserved when present in the editor state

Current write-service implementation notes:

- the local tag API owner is `analytics-app/app/server/analytics_app/analytics_api.py`
- writes are constrained to Studio-owned JSON files
- server writes use atomic replacement and in-process rollback without writing backup files
- write activity is logged to `var/studio/logs/studio_analytics_api.log`
- covered local-server writes also append unified Studio activity rows when the browser supplies valid activity context

Catalogue editor local save behavior:

- catalogue editor source and lookup reads go through `GET /studio/api/catalogue/read` when the local app catalogue API is available
- the work editor sends `POST /studio/api/catalogue/work/save` to the local app catalogue API
- the request includes `work_id`, a browser-computed record hash, a normalized work record patch, and optional `apply_build: true`
- the server validates the full catalogue source set before writing
- writes are constrained to allowlisted canonical catalogue source JSON
- derived lookup payloads under `site/assets/studio/data/catalogue_lookup/` are refreshed after canonical writes
- catalogue writes use atomic replacement and in-process rollback without writing backup bundles
- activity is logged to `var/studio/catalogue/logs/catalogue_service_context.log` and summarized into `var/admin/activity/activity_log.json`
- bulk mode on the same page sends `POST /studio/api/catalogue/bulk-save` with selected work ids, one expected hash per selected work, touched scalar field updates, optional series membership operations, and optional `apply_build: true`
- bulk work update still runs as a sequence of scoped work rebuilds, but that sequence can now be requested directly from the save endpoint
- single-record mode on the same page can also request `POST /studio/api/catalogue/delete-preview` and `POST /studio/api/catalogue/delete-apply`
- work delete removes the selected work plus dependent detail records and work-owned file/link metadata on that work record
- work delete is disabled while the work editor is in bulk mode

Catalogue work detail local save behavior:

- the detail editor sends `POST /studio/api/catalogue/work-detail/save` to the same local app catalogue API
- the request includes `detail_uid`, a browser-computed record hash, a normalized detail patch, and optional `apply_build: true`
- the server validates the parent work reference before writing
- the server writes the affected per-work detail source file under `studio/data/canonical/catalogue/work_details/` only after full-source validation succeeds
- bulk mode on the same page sends `POST /studio/api/catalogue/bulk-save` with selected detail ids, one expected hash per selected detail, the touched field updates, and optional `apply_build: true`
- bulk detail update still runs as a sequence of scoped parent-work rebuilds, but that sequence can now be requested directly from the save endpoint
- single-record mode on the same page can also request `POST /studio/api/catalogue/delete-preview` and `POST /studio/api/catalogue/delete-apply`
- work-detail delete is disabled while the detail editor is in bulk mode

Catalogue workbook import behavior:

- the bulk-add page sends `POST /studio/api/catalogue/import-preview` and `POST /studio/api/catalogue/import-apply`
- both endpoints read the configured bulk-import workbook path from `_data/pipeline.json`, currently `data/works_bulk_import.xlsx`
- preview/apply support two modes: `works` and `work_details`
- works import adds new work records only
- work-details import adds new detail records only
- imported records default to `draft`
- existing source records are reported as duplicates and skipped
- blocked workbook rows stop apply until the workbook is fixed
- the server writes only canonical source JSON and does not write back into Excel

Catalogue moment import behavior:

- the moments page sends `POST /studio/api/catalogue/moment/import-preview` and `POST /studio/api/catalogue/moment/import-apply`
- both endpoints resolve one explicit staged Markdown filename from `var/docs/catalogue/import-staging/moments/`
- the page collects moment metadata and sends it with the filename
- preview validates body-only staged prose, validates the required metadata, and reports current runtime/generated status
- apply writes prose to `_docs_catalogue/moments/<moment_id>.md` and metadata to `site/assets/studio/data/catalogue/moments.json`
- apply stages/generates local moment media when the source image exists, runs a targeted `generate_work_pages.py --only moments --moment-ids ... --write` flow, and then rebuilds catalogue search
- missing source images block local media generation for the moment but do not block prose/metadata import
- apply does not update moment source front matter
- browser-side media image upload/edit behavior remains out of scope for this moment import pass

Catalogue work-owned files and links behavior:

- the work editor saves `downloads` and `links` as arrays on the work record through `POST /studio/api/catalogue/work/save`
- standalone work-file and work-link routes and source JSON files are retired
- the local app catalogue API validates the complete work source payload before writing `works.json`

Catalogue series local save behavior:

- the series editor sends `POST /studio/api/catalogue/series/save` to the same local app catalogue API
- the request includes the current `series_id`, a browser-computed series record hash, the normalized series patch, only the changed work membership rows, and optional `apply_build: true`
- work membership writes preserve the edited `series_ids` order for each changed work
- the server validates `primary_work_id` membership and then writes `series.json` plus affected `works.json` atomically
- the same page can also request delete preview/apply for one series record

Catalogue scoped rebuild behavior:

- the work editor requests a scoped preview from `POST /studio/api/catalogue/build-preview`
- the detail editor requests the same scoped preview for the parent work
- the series editor requests a series-scoped preview from the same endpoint, including any removed member works that still need rebuild
- `POST /studio/api/catalogue/build-apply` runs JSON-source generation for one work or one series scope plus the affected work/series ids
- the apply step then rebuilds `site/assets/data/search/catalogue/index.json`
- unified Studio Activity records these JSON-source scoped rebuilds

## Operational Notes

Current operational constraints:

- `bin/local-studio` does not run startup docs/docs-search rebuilds or startup catalogue lookup export; use manual builders or write-service rebuild paths when generated data needs refreshing
- Studio route behavior depends on the Local Studio app server; public-link inspection also needs `bin/site-preview` when local preview links are being checked
- `admin-app/checks/audit_site_consistency.py` is the script-level check for assignment drift against series/work indexes

For command-level usage and script flags, keep **[Scripts](/docs/?scope=studio&doc=scripts)** aligned with Studio workflow changes.
