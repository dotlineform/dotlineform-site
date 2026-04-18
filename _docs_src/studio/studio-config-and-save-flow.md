---
doc_id: studio-config-and-save-flow
title: Studio Config and Save Flow
last_updated: 2026-04-18
parent_id: studio
sort_order: 20
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
- catalogue route lookup such as `catalogue_status`, `catalogue_activity`, `catalogue_work_editor`, `catalogue_work_detail_editor`, `catalogue_work_file_editor`, `catalogue_work_link_editor`, and `catalogue_series_editor`
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
- `http://127.0.0.1:8788/health`
- `http://127.0.0.1:8788/catalogue/work/create`
- `http://127.0.0.1:8788/catalogue/work/save`
- `http://127.0.0.1:8788/catalogue/work-detail/create`
- `http://127.0.0.1:8788/catalogue/work-detail/save`
- `http://127.0.0.1:8788/catalogue/work-file/create`
- `http://127.0.0.1:8788/catalogue/work-file/save`
- `http://127.0.0.1:8788/catalogue/work-file/delete`
- `http://127.0.0.1:8788/catalogue/work-link/create`
- `http://127.0.0.1:8788/catalogue/work-link/save`
- `http://127.0.0.1:8788/catalogue/work-link/delete`
- `http://127.0.0.1:8788/catalogue/series/create`
- `http://127.0.0.1:8788/catalogue/series/save`
- `http://127.0.0.1:8788/catalogue/build-preview`
- `http://127.0.0.1:8788/catalogue/build-apply`

## Save Modes

The Tag Editor probes local write availability at page load.

Current mode selection:

- if the local write service responds successfully, Studio uses `Local server`
- otherwise Studio falls back to `Offline session`

### Local Server Mode

Current local save behavior:

- the editor sends `POST /save-tags` to the local write service
- only the current diff is persisted, not a full materialized export
- work rows are normalized before save
- inherited series tags are not persisted into work rows
- duplicate work tags are collapsed
- optional `alias` metadata is preserved when present in the editor state

Current write-service implementation notes:

- the local service is `scripts/studio/tag_write_server.py`
- writes are constrained to Studio-owned JSON files
- server writes create timestamped backups in `var/studio/backups/`
- write activity is logged to `var/studio/logs/tag_write_server.log`

Catalogue editor local save behavior:

- the work editor sends `POST /catalogue/work/save` to the catalogue local write service
- the request includes `work_id`, a browser-computed record hash, and a normalized work record patch
- the server validates the full catalogue source set before writing
- writes are constrained to allowlisted canonical catalogue source JSON
- derived lookup payloads under `assets/studio/data/catalogue_lookup/` are refreshed after canonical writes
- backup bundles are written under `var/studio/catalogue/backups/`
- activity is logged to `var/studio/catalogue/logs/catalogue_write_server.log` and summarized into `assets/studio/data/catalogue_activity.json`

Catalogue work detail local save behavior:

- the detail editor sends `POST /catalogue/work-detail/save` to the same local catalogue write service
- the request includes `detail_uid`, a browser-computed record hash, and a normalized detail patch
- the server validates the parent work reference before writing
- the server writes `work_details.json` only after full-source validation succeeds

Catalogue work file local save behavior:

- the file editor sends `POST /catalogue/work-file/save` to the same local catalogue write service
- the request includes `file_uid`, a browser-computed record hash, and a normalized file patch
- draft create uses `POST /catalogue/work-file/create`
- delete uses `POST /catalogue/work-file/delete`
- the server validates the parent work reference before writing
- the server writes `work_files.json` only after full-source validation succeeds

Catalogue work link local save behavior:

- the link editor sends `POST /catalogue/work-link/save` to the same local catalogue write service
- the request includes `link_uid`, a browser-computed record hash, and a normalized link patch
- draft create uses `POST /catalogue/work-link/create`
- delete uses `POST /catalogue/work-link/delete`
- the server validates the parent work reference before writing
- the server writes `work_links.json` only after full-source validation succeeds

Catalogue series local save behavior:

- the series editor sends `POST /catalogue/series/save` to the same local catalogue write service
- the request includes the current `series_id`, a browser-computed series record hash, the normalized series patch, and only the changed work membership rows
- work membership writes preserve the edited `series_ids` order for each changed work
- the server validates `primary_work_id` membership and then writes `series.json` plus affected `works.json` atomically

Catalogue scoped rebuild behavior:

- the work editor requests a scoped preview from `POST /catalogue/build-preview`
- the detail editor requests the same scoped preview for the parent work
- the series editor requests a series-scoped preview from the same endpoint, including any removed member works that still need rebuild
- `POST /catalogue/build-apply` runs JSON-source generation for one work or one series scope plus the affected work/series ids
- the apply step then rebuilds `assets/data/search/catalogue/index.json`
- Studio build activity now records these JSON-source scoped rebuilds alongside the older workbook-led pipeline runs

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
- editor routes now prefer derived lookup JSON under `assets/studio/data/catalogue_lookup/` instead of loading full canonical source maps into the browser
- work, detail, file, link, and series editors now read focused derived lookup records rather than full canonical source maps
- Studio writes only through the local save service
- detailed payload shape belongs in [Data Models](/docs/?scope=studio&doc=data-models), not here

Use these references for the contracts:

- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Config](/docs/?scope=studio&doc=config)

## Operational Notes

Current operational constraints:

- `bin/dev-studio` rebuilds Docs Viewer data and derived catalogue lookup artifacts, but not docs-search artifacts
- Studio route behavior depends on the current site build being present under Jekyll
- `scripts/audit_site_consistency.py` is the script-level check for assignment drift against series/work indexes

For command-level usage and script flags, keep **[Scripts](/docs/?scope=studio&doc=scripts)** aligned with Studio workflow changes.
