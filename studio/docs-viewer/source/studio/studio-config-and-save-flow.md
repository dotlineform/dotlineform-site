---
doc_id: studio-config-and-save-flow
title: Studio Config and Save Flow
added_date: 2026-04-22
last_updated: "2026-05-09 21:45"
parent_id: config
sort_order: 1000
viewable: true
---
# Studio Config and Save Flow

This document describes the current shared Studio config, data-loading boundary, and local/offline save behavior.

For file-level ownership of the current config artifacts, see:

- **[Config](/docs/?scope=studio&doc=config)**
- **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
- **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**
- **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**

## Shared Config

Studio configuration is defined in:

- `assets/studio/data/studio_config.json`

It is loaded by:

- `assets/studio/js/studio-config.js`

Current responsibilities:

- public route paths used across Studio links
- public JSON paths used by Studio pages
- RAG analysis group and threshold settings
- Studio-owned UI copy used by the editor, registry, aliases, series tags, tag groups, and search surfaces

Current route/data-path responsibilities include:

- Studio route lookup such as `series_tags`, `series_tag_editor`, `tag_registry`, `tag_aliases`, and `tag_groups`
- catalogue route lookup such as `catalogue_status`, `activity_log`, `project_state`, `bulk_add_work`, `catalogue_moment_editor`, `catalogue_work_editor`, `catalogue_work_detail_editor`, and `catalogue_series_editor`
- shared docs/search route lookup such as `docs_page`, `library_page`, and `search`
- Studio-owned JSON paths
- shared catalogue index paths
- dedicated search policy and per-scope search index paths

The exact key inventory belongs in the [Config](/docs/?scope=studio&doc=config) section rather than here.

## Shared Data and Transport Modules

`assets/studio/js/studio-data.js` centralizes shared read-side helpers for Studio pages.

Current shared responsibilities include:

- fetching Studio and site JSON payloads from config-derived paths
- fetching derived Studio catalogue lookup payloads plus focused per-record lookup JSON
- registry lookup building
- group-description normalization
- assignment and series data shaping used across Studio pages

`assets/studio/js/studio-transport.js` centralizes the local write-service boundary.

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

- the docs viewer manage-mode rebuild action uses the separate docs-management service and rebuilds the current docs scope plus that scope's docs search
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

- the local tag API owner is `scripts/studio/studio_analytics_api.py`
- writes are constrained to Studio-owned JSON files
- server writes create timestamped backups in `var/studio/backups/`
- write activity is logged to `var/studio/logs/studio_analytics_api.log`
- covered local-server writes also append unified Studio activity rows when the browser supplies valid activity context
- backup retention is applied at `bin/local-studio` startup; see [Studio Backup Retention](/docs/?scope=studio&doc=scripts-studio-backup-retention)

Catalogue editor local save behavior:

- catalogue editor source and lookup reads go through `GET /studio/api/catalogue/read` when the local app catalogue API is available
- the work editor sends `POST /studio/api/catalogue/work/save` to the local app catalogue API
- the request includes `work_id`, a browser-computed record hash, a normalized work record patch, and optional `apply_build: true`
- the server validates the full catalogue source set before writing
- writes are constrained to allowlisted canonical catalogue source JSON
- derived lookup payloads under `assets/studio/data/catalogue_lookup/` are refreshed after canonical writes
- backup bundles are written under `var/studio/catalogue/backups/`
- activity is logged to `var/studio/catalogue/logs/catalogue_service_context.log` and summarized into `var/studio/activity/activity_log.json`
- backup retention is applied at `bin/local-studio` startup; see [Studio Backup Retention](/docs/?scope=studio&doc=scripts-studio-backup-retention)
- bulk mode on the same page sends `POST /studio/api/catalogue/bulk-save` with selected work ids, one expected hash per selected work, touched scalar field updates, optional series membership operations, and optional `apply_build: true`
- bulk work update still runs as a sequence of scoped work rebuilds, but that sequence can now be requested directly from the save endpoint
- single-record mode on the same page can also request `POST /studio/api/catalogue/delete-preview` and `POST /studio/api/catalogue/delete-apply`
- work delete removes the selected work plus dependent detail records and work-owned file/link metadata on that work record
- work delete is disabled while the work editor is in bulk mode

Catalogue work detail local save behavior:

- the detail editor sends `POST /studio/api/catalogue/work-detail/save` to the same local app catalogue API
- the request includes `detail_uid`, a browser-computed record hash, a normalized detail patch, and optional `apply_build: true`
- the server validates the parent work reference before writing
- the server writes `work_details.json` only after full-source validation succeeds
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
- apply writes prose to `_docs_catalogue/moments/<moment_id>.md` and metadata to `assets/studio/data/catalogue/moments.json`
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
- the apply step then rebuilds `assets/data/search/catalogue/index.json`
- unified Studio Activity records these JSON-source scoped rebuilds

### Offline Session Mode

Current offline behavior:

- the editor stages normalized series rows in browser `localStorage`
- staged rows preserve assignment objects, including `w_manual` and optional `alias`
- the editor advances its baseline after staging so the page behaves like a save flow
- local-only changes are surfaced back into the UI

Current session management surface:

- the Series Tags page is the session hub
- `Session` opens the offline-session modal
- `Import` opens the import-preview/apply flow when the local server is available

## Data Files and Ownership

Studio currently depends on four data families:

- Studio-owned tag data
- Studio-owned catalogue source data
- shared catalogue index data
- dedicated search policy/search-index data
- Studio docs data rebuilt by the docs builder

Current ownership boundary:

- Studio reads both Studio-owned JSON and shared site/search artifacts
- mutable catalogue editor reads are local-service-backed and should not fall back to stale static source JSON when the catalogue server is unavailable
- work, detail, file, link, and series editors read focused derived lookup records through the local catalogue service rather than full canonical source maps
- Studio writes only through the local save service
- detailed payload shape belongs in [Data Models](/docs/?scope=studio&doc=data-models), not here

Use these references for the contracts:

- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Config](/docs/?scope=studio&doc=config)

## Operational Notes

Current operational constraints:

- `bin/local-studio` runs startup docs/docs-search rebuilds only when `DOCS_STARTUP_REBUILD_SCOPES` is set, and derived catalogue lookup export only when `CATALOGUE_STARTUP_LOOKUP_REBUILD` is enabled
- Studio route behavior depends on the Local Studio app server; public-link inspection also needs `bin/public-site-preview` when local preview links are being checked
- `scripts/checks/audit_site_consistency.py` is the script-level check for assignment drift against series/work indexes

For command-level usage and script flags, keep **[Scripts](/docs/?scope=studio&doc=scripts)** aligned with Studio workflow changes.
