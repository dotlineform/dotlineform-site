---
doc_id: scripts-docs-management-server-generated-reads
title: Docs Management Server Generated Reads
added_date: 2026-05-19
last_updated: 2026-05-22
parent_id: scripts-docs-management-server
sort_order: 15100
---
# Docs Management Server Generated Reads

## Endpoints And Behavior

Exposed endpoints:

- `GET /health`
- `GET /capabilities`
- `GET /docs/generated/index`
- `GET /docs/generated/payload`
- `GET /docs/generated/search`
- `GET /docs/generated/references`
- `GET /docs/generated/reference-target`
- `GET /docs/index`
- `GET /docs/doc`
- `GET /docs/search`
- `GET /docs/references`
- `GET /docs/reference-target`
- `GET /docs/source-config`
- `GET /docs/source-config-settings`
- `POST /docs/source-config-settings`
- `GET /docs/import-source-files`
- `GET /docs/import-html-files`
- `POST /docs/import-source`
- `POST /docs/import-html`
- `GET /studio/api/docs/data-sharing/returned-packages` through the local Studio app
- `POST /studio/api/docs/data-sharing/prepare` through the local Studio app
- `POST /studio/api/docs/data-sharing/review` through the local Studio app
- `POST /studio/api/docs/data-sharing/apply` through the local Studio app
- `POST /docs/broken-links`
- `POST /docs/rebuild`
- `POST /docs/open-source`
- `POST /docs/update-metadata`
- `POST /docs/update-viewability`
- `POST /docs/update-viewability-bulk`
- `POST /docs/create`
- `POST /docs/move`
- `POST /docs/archive`
- `POST /docs/delete-preview`
- `POST /docs/delete-apply`
- `POST /docs/scopes/create-preview`
- `POST /docs/scopes/create-apply`
- `POST /docs/scopes/delete-preview`
- `POST /docs/scopes/delete-apply`

Current behavior:

- local-only write service for the shared Docs Viewer
- endpoint path constants are owned by `scripts/docs/docs_management_routes.py`; the server handler uses explicit GET and POST dispatch tables
- docs source-model helpers are owned by `scripts/docs/docs_source_model.py`
- generated Docs Viewer JSON read helpers are owned by `scripts/docs/docs_generated_reads.py`
- source config report payloads are owned by `scripts/docs/docs_source_config_report.py`
- source config settings allowlist, validation payloads, and allowlisted source-config writes are owned by `scripts/docs/docs_source_config_settings.py`
- docs-specific Studio Activity row construction is owned by `scripts/docs/docs_activity.py`
- docs payload/search rebuild command shapes and watcher-suppression follow-through are owned by `scripts/docs/docs_write_rebuild.py`
- staged source import orchestration for the Docs Viewer import modal is owned by `scripts/docs/docs_import_source_service.py`; the server binds the existing backup, log, and rebuild helpers and keeps activity append timing
- management mutation planners for create, metadata, viewability, move, normalize-order, archive, and delete flows are owned by `scripts/docs/docs_management_mutations.py`; the server still parses requests, performs backups where configured, calls source write/rebuild helpers, logs completed writes, and returns endpoint responses
- Data Sharing HTTP endpoints are exposed through the local Studio app Docs API adapter, with neutral route constants and shared dispatch owned by `scripts/studio/` and Library document behavior owned by `scripts/docs/documents_data_sharing_adapter.py`
- used by `/docs/?scope=<scope>&mode=manage` for configured docs scopes
- also used by the `docs_broken_links` Docs Viewer report for a read-only docs link audit
- also used by the `/docs/` management import modal for staged-file listing and source import writes
- also used by `/studio/data-sharing/prepare/?mode=manage` to dispatch Library package preparation to the documents Data Sharing adapter
- also used by `/studio/data-sharing/review/?mode=manage` to dispatch staged-file listing, Markdown review generation, summary apply, and hierarchy apply to the documents Data Sharing adapter
- appends unified activity rows for covered docs import, Data Sharing package/apply, and broken-links audit actions when valid activity context is supplied
- serves generated docs index, per-doc payload, and docs-search JSON to the shared Docs Viewer while `bin/dev-studio` is running
- serves a read-only Docs Viewer source-config report payload to manage-mode report surfaces
- serves a source-config settings contract and allowlisted settings write endpoint for manage-mode settings controls
- creates, archives, and deletes source docs under the current scope root
- creates Studio docs as `published: true`, `viewable: true`
- creates Analysis docs as `published: true`, `viewable: false`
- creates Library docs as `published: true`, `viewable: false`
- writes new or changed docs with minute-precision `added_date` and `last_updated` values in `YYYY-MM-DD HH:MM` form while preserving existing date-only values
- rebuilds scope-owned docs payloads after successful writes, using targeted docs payload ids when the mutation planner can provide an explicit safe set
- runs targeted docs-search updates after successful writes when affected doc ids are explicit
- coordinates successful source writes with the docs live watcher so `bin/dev-studio` does not immediately run a redundant second same-scope rebuild for the same changed source file

Unified activity coverage:

- `POST /docs/import-source` writes `import source data` rows after a source doc is created or overwritten; preview, replacement-required, and confirmation-only responses are excluded
- `POST /studio/api/docs/data-sharing/prepare` writes package-preparation rows only when an outbound package artifact is written
- `POST /studio/api/docs/data-sharing/apply` writes update rows only for confirmed summary or hierarchy apply writes
- `POST /docs/broken-links` writes `run audit` rows with checked and broken-link counts

Search update behavior:

- create/import targets the new doc id
- import overwrite and metadata title edits target the changed doc id plus direct children because child search entries include `parent_title`
- metadata parent/order edits, move, archive, and delete target the changed doc id
- bulk viewability targets changed doc ids only
- internal targeted calls pass `--remove-missing` so missing and non-viewable ids can be reconciled safely
- `POST /docs/rebuild` remains a full same-scope docs-search rebuild

Docs payload rebuild behavior:

- create, source import create/overwrite, metadata, viewability, move, normalize order, archive, delete, and Library returned-package apply writes pass explicit docs payload ids into `./scripts/build_docs.rb --scope <scope> --write --only-doc-ids <ids>`
- source-config settings writes and explicit `POST /docs/rebuild` remain full same-scope docs payload rebuilds
- rebuild responses include `rebuild.docs.mode`, `rebuild.docs.doc_ids`, and `rebuild.docs.reason` alongside the existing `rebuild.search` object so callers can tell whether docs payloads used targeted mode or a full fallback

`GET /capabilities` reports:

- whether docs management is available
- whether docs export is available
- whether Library import is available
- which scopes are writable
- whether the current scope has `archive` for the Archive command
- whether generated docs/search reads are available for each scope
- whether source config report reads are available
- whether source config settings contract reads and writes are available
- whether scope lifecycle preview/apply actions are available
- whether each configured scope is manifest-recorded and delete-eligible

Read-only generated-data endpoints:

- `GET /docs/generated/index?scope=<scope>`
- `GET /docs/generated/payload?scope=<scope>&doc_id=<doc_id>`; `doc=<doc_id>` is also accepted
- `GET /docs/generated/search?scope=<scope>`
- `GET /docs/generated/references?scope=<scope>`
- `GET /docs/generated/reference-target?scope=<scope>&target_kind=<kind>&target_id=<id>`

Compatibility aliases:

- `GET /docs/index?scope=<scope>`
- `GET /docs/doc?scope=<scope>&doc_id=<doc_id>`
- `GET /docs/search?scope=<scope>`

Generated-read behavior:

- `scope` must be one of the configured scope ids in `scripts/docs/docs_scopes.json`
- responses return the raw generated JSON unchanged
- all JSON responses include `Cache-Control: no-store`
- index reads resolve only the configured scope output path plus `index.json`
- payload reads require a safe `doc_id`, require that `doc_id` to be present in the generated scope index, and then resolve only the configured scope output path plus `by-id/<doc_id>.json`
- payload reads allow non-viewable docs when those docs are present in the generated index, because local manage mode needs to inspect and update non-viewable docs
- search reads resolve only `assets/data/search/<scope>/index.json`
- references reads resolve only the configured scope output path plus `references/index.json`
- reference-target reads resolve only configured semantic-reference target buckets under the selected scope
- missing scope, unsupported scope, missing generated files, and non-indexed payload ids return validation or 404 errors rather than filesystem paths chosen by the browser
- these endpoints are read-only and do not write source or generated files

Source-config report endpoint:

- `GET /docs/source-config`

Source-config report behavior:

- reads only known Docs Viewer config files and generated scope indexes
- returns repo-relative paths only
- includes source scope config, browser config projection, generated output paths, generated viewer options, and per-scope warnings
- is intended for `/docs/` manage-mode report rendering
- is read-only and does not write source or generated files

Source-config settings endpoints:

- `GET /docs/source-config-settings`
- `GET /docs/source-config-settings?scope=<scope>`
- `POST /docs/source-config-settings`

Source-config settings behavior:

- reads only `scripts/docs/docs_scopes.json` and configured generated scope indexes
- returns the allowlisted source config fields that manage-mode settings controls may edit
- currently allowlists scoped `show_updated_date` only
- reports blocked install-time fields such as source roots, route bases, output roots, and import media storage
- reports deferred global fields such as `recently_added_limit`
- validates setting changes through `scripts/docs/docs_source_config_settings.py`
- writes only allowlisted source config fields back to `scripts/docs/docs_scopes.json`
- rebuilds the affected generated docs scope after a changed setting is saved; `show_updated_date` uses a docs-only rebuild because docs search output is unaffected
- warns when generated `viewer_options` are stale relative to source config or when a proposed change requires a generated docs rebuild
- rejects blocked, deferred, unsupported, malformed, or wrong-type fields

`POST /docs/source-config-settings` expects:

```json
{
  "scope": "studio",
  "changes": {
    "show_updated_date": false
  }
}
```
