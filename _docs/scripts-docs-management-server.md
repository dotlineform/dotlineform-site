---
doc_id: scripts-docs-management-server
title: Docs Management Server
added_date: 2026-04-24
last_updated: "2026-05-11"
parent_id: docs-viewer
sort_order: 45
---
# Docs Management Server

Script:

```bash
./scripts/docs/docs_management_server.py
```

## Optional Flags

- `--port 8789`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--dry-run`: validate and return responses without writing source docs

## Endpoints And Behavior

Exposed endpoints:

- `GET /health`
- `GET /capabilities`
- `GET /docs/generated/index`
- `GET /docs/generated/payload`
- `GET /docs/generated/search`
- `GET /docs/index`
- `GET /docs/doc`
- `GET /docs/search`
- `GET /docs/import-source-files`
- `GET /docs/import-html-files`
- `GET /docs/import/files`
- `POST /docs/import-source`
- `POST /docs/import-html`
- `POST /docs/export`
- `POST /docs/import/preview`
- `POST /docs/import/apply`
- `POST /docs/broken-links`
- `POST /docs/rebuild`
- `POST /docs/open-source`
- `POST /docs/update-metadata`
- `POST /docs/update-viewability`
- `POST /docs/update-viewability-bulk`
- `POST /docs/create`
- `POST /docs/move`
- `POST /docs/restore-move`
- `POST /docs/archive`
- `POST /docs/delete-preview`
- `POST /docs/delete-apply`

Current behavior:

- local-only write service for the shared Docs Viewer
- endpoint path constants are owned by `scripts/docs/docs_management_routes.py`; the server handler uses explicit GET and POST dispatch tables
- docs source-model helpers are owned by `scripts/docs/docs_source_model.py`
- generated Docs Viewer JSON read helpers are owned by `scripts/docs/docs_generated_reads.py`
- docs-specific Studio Activity row construction is owned by `scripts/docs/docs_activity.py`
- docs payload/search rebuild command shapes and watcher-suppression follow-through are owned by `scripts/docs/docs_write_rebuild.py`
- staged source import orchestration for `/studio/docs-import/` is owned by `scripts/docs/docs_import_source_service.py`; the server binds the existing backup, log, and rebuild helpers and keeps activity append timing
- management mutation planners for create, metadata, viewability, move, restore, archive, and delete flows are owned by `scripts/docs/docs_management_mutations.py`; the server still parses requests, performs backups, calls source write/rebuild helpers, logs completed writes, and returns endpoint responses
- structured import/export adapter orchestration remains server-owned for now and is tracked separately from the Docs Management Server restructuring request
- used by `/docs/?scope=studio&mode=manage`, `/docs/?scope=library&mode=manage`, and `/docs/?scope=analysis&mode=manage`
- also used by `/studio/docs-broken-links/` for a read-only docs link audit
- also used by `/studio/docs-import/` for staged-file listing and source import writes
- also used by `/studio/export/` to read the generated Library docs index locally and write configured Library export artifacts
- also used by `/studio/import/` to list staged JSON/JSONL data files, write Markdown previews, apply selected Library summary updates, and apply selected Library hierarchy updates
- appends unified Studio activity rows for covered docs import/export/import-apply and broken-links audit actions when valid activity context is supplied
- serves generated docs index, per-doc payload, and docs-search JSON to the shared Docs Viewer while `bin/dev-studio` is running
- creates, archives, and deletes source docs under the current scope root
- creates Studio docs as `published: true`, `viewable: true`
- creates Analysis docs as `published: true`, `viewable: false`
- creates Library docs as `published: true`, `viewable: false`
- writes new or changed docs with minute-precision `added_date` and `last_updated` values in `YYYY-MM-DD HH:MM` form while preserving existing date-only values
- rebuilds scope-owned docs payloads after successful writes
- runs targeted docs-search updates after successful writes when affected doc ids are explicit
- coordinates successful source writes with the docs live watcher so `bin/dev-studio` does not immediately run a redundant second same-scope rebuild for the same changed source file

Unified activity coverage:

- `POST /docs/import-source` writes `import source data` rows after a source doc is created or overwritten; preview, replacement-required, and confirmation-only responses are excluded
- `POST /docs/export` writes `export data` rows only when an export artifact is written
- `POST /docs/import/apply` writes `update docs source` rows only for confirmed summary or hierarchy apply writes
- `POST /docs/broken-links` writes `run audit` rows with checked and broken-link counts

Search update behavior:

- create/import targets the new doc id
- import overwrite and metadata title edits target the changed doc id plus direct children because child search entries include `parent_title`
- metadata parent/order edits, move, archive, and delete target the changed doc id
- bulk viewability targets changed doc ids only
- internal targeted calls pass `--remove-missing` so missing and non-viewable ids can be reconciled safely
- `POST /docs/rebuild` remains a full same-scope docs-search rebuild

`GET /capabilities` reports:

- whether docs management is available
- whether docs export is available
- whether Library import is available
- which scopes are writable
- whether the current scope has `archive` for the Archive command
- whether generated docs/search reads are available for each scope

Read-only generated-data endpoints:

- `GET /docs/generated/index?scope=<scope>`
- `GET /docs/generated/payload?scope=<scope>&doc_id=<doc_id>`; `doc=<doc_id>` is also accepted
- `GET /docs/generated/search?scope=<scope>`

Compatibility aliases:

- `GET /docs/index?scope=<scope>`
- `GET /docs/doc?scope=<scope>&doc_id=<doc_id>`
- `GET /docs/search?scope=<scope>`

Generated-read behavior:

- `scope` must be `studio`, `analysis`, or `library`
- responses return the raw generated JSON unchanged
- all JSON responses include `Cache-Control: no-store`
- index reads resolve only `assets/data/docs/scopes/<scope>/index.json`
- payload reads require a safe `doc_id`, require that `doc_id` to be present in the generated scope index, and then resolve only `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`
- payload reads allow non-viewable docs when those docs are present in the generated index, because local manage mode needs to inspect and update non-viewable docs
- search reads resolve only `assets/data/search/<scope>/index.json`
- missing scope, unsupported scope, missing generated files, and non-indexed payload ids return validation or 404 errors rather than filesystem paths chosen by the browser
- these endpoints are read-only and do not write source or generated files

`POST /docs/create` expects:

```json
{
  "scope": "studio",
  "title": "New Doc",
  "after_doc_id": "docs-viewer-management"
}
```

Request behavior:

- `scope` must be `studio`, `analysis`, or `library`
- `title` defaults to `New Doc` when omitted or blank
- new docs write `added_date` and `last_updated` to the current minute in `YYYY-MM-DD HH:MM` form
- new Studio docs write `published: true`, `viewable: true`
- new Analysis docs write `published: true`, `viewable: false`
- new Library docs write `published: true`, `viewable: false`
- `doc_id` and filename stem are generated from the title and made unique with `-2`, `-3`, and so on
- `after_doc_id`, when present, inserts the new doc after the referenced doc and reuses that doc's `parent_id`
- `parent_id`, when present without `after_doc_id`, must resolve inside the same scope
- `sort_order` appends as the last sibling when both `after_doc_id` and explicit `sort_order` are omitted

`GET /docs/import-source-files` returns:

- the current supported staged source files under `var/docs/import-staging/`
- filename, repo-relative path, source format, size, and modified time for each staged file
- a read-only listing intended for the Studio import page

Supported source formats:

- `html`: `.html`, `.htm`
- `markdown`: `.md`, `.markdown`
- `text`: `.txt`
- `svg`: `.svg`
- `image`: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`
- `file`: `.pdf`, `.zip`, `.csv`, `.tsv`, `.json`, `.jsonl`, `.docx`, `.xlsx`, `.pptx`

`GET /docs/import-html-files` remains a compatibility alias for older callers and returns the same source-file listing.

`POST /docs/import-source` expects:

```json
{
  "scope": "studio",
  "staged_filename": "example 1.html",
  "include_prompt_meta": false,
  "overwrite_doc_id": "",
  "confirm_overwrite": false,
  "replacement_doc_id": "",
  "replacement_title": "",
  "preview_only": false
}
```

Import behavior:

- `scope` must be `studio`, `analysis`, or `library`
- `staged_filename` must resolve inside `var/docs/import-staging/`
- accepts the supported staged source formats listed above
- parses full staged HTML files through the shared converter
- imports staged Markdown as the source body without predefined front matter
- imports staged text as plain Markdown prose and converts plain URLs to Markdown autolinks
- imports standalone SVG as a wrapper Markdown doc with sanitized inline SVG
- imports raster images as wrapper Markdown docs pointing at <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code>
- imports downloadable files as wrapper Markdown docs pointing at <code>&#91;&#91;media:docs/&lt;scope&gt;/files/&lt;filename&gt;&#93;&#93;</code>
- extracts Markdown-image-form inline raster data URLs from HTML and Markdown imports into generated staged media files under `var/docs/import-staging/`
- escapes literal pipe characters from source text so mathematical notation such as `I(X;Y|Z)` does not become an accidental Markdown table
- converts plain-text `http://` and `https://` URLs in prose into Markdown autolinks while leaving existing anchors and code/preformatted text alone
- applies the same SVG safety rules to HTML inline SVG and standalone SVG files
- validates the generated Markdown through the repo's Jekyll renderer helper before returning success
- supports the prompt/meta include toggle already defined by the import spec for HTML imports
- derives the proposed `doc_id` and new Markdown filename stem from the staged source filename, not from the imported document title
- derives Markdown import titles from the first `# H1` when present, then falls back to the staged filename
- derives replacement `doc_id` values from `replacement_doc_id` when the initial staged filename stem collides
- keeps `replacement_title` as a compatibility fallback for older callers
- creates a new Markdown source doc immediately when the generated import target does not collide
- new imported docs write `added_date` and `last_updated` to the current minute in `YYYY-MM-DD HH:MM` form
- new Studio imports write `published: true`, `viewable: true`
- new Analysis imports write `published: true`, `viewable: false`
- new Library imports write `published: true`, `viewable: false`
- preserves blank `parent_id` and appends the new imported doc at the end of the root-level `sort_order`
- reports `media_plan` for standalone image and file-media imports, including the expected R2 key and generated media token
- reports `media_plans` for extracted inline raster images, including staged filenames, expected R2 keys, generated media tokens, MIME type, and decoded byte sizes
- reports collision details when the generated import target already matches an existing `doc_id` or source filename stem
- asks browser callers to provide `replacement_doc_id` for normal collision recovery
- requires both `overwrite_doc_id` and `confirm_overwrite: true` before overwriting an existing doc through the low-level overwrite path
- the Studio filename-conflict modal uses `overwrite_doc_id` plus `confirm_overwrite: true` for its explicit Replace action
- preserves the overwritten doc's `doc_id`, filename, `added_date`, `parent_id`, `sort_order`, and existing `published`/`viewable` state
- refreshes the overwritten doc's `last_updated` to the current minute
- creates an import-specific backup before overwrite using a light-touch same-day replacement rule
- writes decoded inline raster media files only during create or overwrite, not during preview-only responses
- `preview_only: true` forces a non-writing preview response even when the server is not running with `--dry-run`
- successful create/overwrite writes rebuild the same-scope docs payloads and run targeted docs-search updates for affected ids

`POST /docs/import-html` remains a compatibility alias for older callers through route dispatch and delegates to the same source import handler.

`POST /docs/rebuild` expects:

```json
{
  "scope": "studio"
}
```

Rebuild behavior:

- `scope` must be `studio`, `analysis`, or `library`
- rebuilds generated docs payloads for the requested scope
- rebuilds the docs-search artifact for the requested scope
- is intended for local manage mode rather than the public hosted site

`POST /docs/broken-links` expects:

```json
{
  "scope": "studio"
}
```

Broken-links behavior:

- `scope` must be `studio` or `library`
- runs the shared docs broken-links audit for that scope
- reports missing target issues only
- does not write source docs or generated outputs
- is intended for the Studio audit page and terminal-backed local maintenance

`POST /docs/export` expects:

```json
{
  "data_domain": "library",
  "config_id": "library-document-summaries",
  "target_format": "jsonl",
  "doc_ids": ["library"],
  "select_all": false,
  "missing_summary_only": true
}
```

Export behavior:

- `data_domain` must resolve through `assets/studio/data/export_import_adapters.json`; the first implemented domain is `library`
- stub adapters and planned capabilities fail closed before the endpoint runs document-specific export behavior
- `config_id` must resolve in the adapter-declared export config file
- `target_format` may be `json`, `jsonl`, or omitted; omitted uses the config's default `target.format`
- `doc_ids` is an explicit list used by configs that support explicit selection
- `select_all: true` asks the export engine to select every doc matching the config filters
- `missing_summary_only` may be `true`, `false`, or `null`; unsupported configs ignore `true`
- unsupported config/format combinations return the export engine's structured validation report without writing
- the endpoint calls `./scripts/docs/docs_export.py`'s shared export engine in-process
- output paths are validated by the export engine and must stay under the adapter-declared export root
- normal server mode writes the export file and returns `output_written: true`
- server `--dry-run` mode validates and reports the target path without writing
- failed validation returns the same report shape with `ok: false`, `errors`, `warnings`, `issue_counts`, and `output_written: false`
- logs include data domain, adapter id, scope, config id, counts, target format, dry-run state, issue counts, and whether output was written; logs do not include document body content or export payloads

Runtime role:

- Studio uses this endpoint as the only browser-to-filesystem boundary for Library exports
- the endpoint does not accept arbitrary output paths from the browser
- config-defined paths are resolved and allowlisted by the shared export engine
- generated export files are local working artifacts for Studio reporting or manual external use

`GET /docs/import/files` accepts:

```text
?data_domain=library
```

Import file listing behavior:

- `data_domain` must resolve exactly one adapter through `assets/studio/data/export_import_adapters.json`
- the first implementation maps `data_domain=library` to the `documents` adapter
- stub adapters and planned capabilities fail closed before the endpoint runs document-specific import behavior
- lists staged `.json` and `.jsonl` files under the adapter-declared staging root
- returns filename, repo-relative path, format, size, and modified time
- does not parse or log file content

`POST /docs/import/preview` expects:

```json
{
  "data_domain": "library",
  "staged_filename": "library-document-summaries.jsonl"
}
```

Import preview behavior:

- `data_domain` must resolve exactly one adapter with `import_preview` capability
- stub adapters and planned capabilities fail closed before the endpoint runs document-specific preview behavior
- `staged_filename` must resolve inside the adapter-declared staging root
- parses the staged data file through `./scripts/docs/docs_import.py`
- loads current generated docs index and payload state through the shared import engine for the adapter-declared docs scope
- writes Markdown previews under the adapter-declared preview root in normal server mode
- reports planned preview paths without writing when the server runs with `--dry-run`
- returns the same structured report shape as the import CLI, including `counts`, `issues`, `records`, `current_library`, `preview_files`, and `preview_written`
- logs include scope, staged filename, dry-run state, import type, counts, issue counts, and preview paths; logs do not include document body content or staged payload content

Runtime role:

- this endpoint is the browser-to-filesystem boundary for import preview files
- it does not mutate `_docs_library/*.md`
- it does not apply summaries, relationship recommendations, or full-content changes to canonical source
- generated preview files are local working artifacts for Studio review
- unconfigured data domains fail closed instead of falling back to document parsing

`POST /docs/import/apply` expects for summary updates:

```json
{
  "data_domain": "library",
  "operation": "summary_apply",
  "staged_filename": "library-document-summaries.jsonl",
  "record_indices": [0, 3, 4],
  "confirm": false
}
```

Library import summary-apply behavior:

- `data_domain` and `operation` must resolve the `documents` adapter
- `staged_filename` must resolve inside the adapter-declared staging root
- `record_indices` must be a non-empty list of selected staged record indexes
- `confirm: false` runs a non-writing preflight and reports selected rows, updates, skipped rows, warnings, errors, and counts
- `confirm: true` applies the selected summary updates when the preflight has no blocking errors
- selected rows map back to parsed staged records by `record_index`, then to current source docs loaded from `_docs_library/`
- only selected missing target source docs are blocking errors
- selected rows with missing staged records, missing `doc_id`, duplicate `doc_id`, missing summary text, or unchanged summary text are skipped
- source writes update only `summary`, preserve or initialize `added_date`, and refresh `last_updated`
- successful writes create a timestamped `documents-summary-apply` backup bundle under `var/docs/backups/` before writing source files
- successful writes rebuild Library docs payloads and run targeted docs-search updates for changed ids
- server `--dry-run` mode validates and reports without writing even when `confirm: true`

Runtime role:

- this endpoint is the browser-to-filesystem boundary for summary-only Library import writes
- it does not accept browser-supplied source paths and does not write outside the Library source-doc scope
- it does not apply full content, `parent_id`, `sort_order`, or other relationship changes
- backups use the existing docs-management backup root so Studio backup retention can manage them with the other docs source-write backups

`POST /docs/import/apply` expects for hierarchy updates:

```json
{
  "data_domain": "library",
  "operation": "hierarchy_apply",
  "staged_filename": "library-parent-child-relationships.json",
  "record_indices": [0, 3, 4],
  "confirm": false
}
```

Library import hierarchy-apply behavior:

- `data_domain` and `operation` must resolve the `documents` adapter
- `staged_filename` must resolve inside the adapter-declared staging root
- `record_indices` must be a non-empty list of selected staged record indexes
- `confirm: false` runs a non-writing preflight and reports selected rows, changed rows, unchanged rows, skipped rows, warnings, errors, and counts
- `confirm: true` applies the selected `parent_id` updates when the preflight has no blocking errors
- selected rows map back to parsed staged records by `record_index`, then to current source docs loaded from `_docs_library/`
- only selected missing target source docs are blocking errors
- selected rows with missing staged records, missing `doc_id`, duplicate `doc_id`, or self-parent ids are skipped
- unknown non-empty staged `parent_id` values are warnings and are allowed
- source writes update only `parent_id`, preserve current `sort_order`, preserve or initialize `added_date`, and refresh `last_updated`
- successful writes create a timestamped `documents-hierarchy-apply` backup bundle under `var/docs/backups/` before writing source files
- successful writes rebuild Library docs payloads and run targeted docs-search updates for changed ids
- server `--dry-run` mode validates and reports without writing even when `confirm: true`

Runtime role:

- this endpoint is the browser-to-filesystem boundary for parent-id-only Library import writes
- it does not accept browser-supplied source paths and does not write outside the Library source-doc scope
- it does not apply summaries, full content, `sort_order`, or other future relationship fields
- unresolved parent ids are preserved in source but normalized to root-level relationships in generated Library docs data
- backups use the existing docs-management backup root so Studio backup retention can manage them with the other docs source-write backups

`POST /docs/open-source` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management",
  "editor": "default"
}
```

Open-source behavior:

- resolves the source Markdown path for the current doc within the current scope
- `editor: "default"` opens the file in the preferred Markdown app for the local machine
- the server first checks `DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP` from `var/local/site.env` for local runs
- if that key is unset, it currently prefers `MarkEdit`, then `Typora`, then `Marked 2`, then `Marked` when installed
- if none of those apps are present, it falls back to plain `open`, which follows macOS Launch Services defaults
- `editor: "vscode"` opens the file in Visual Studio Code
- intended for use from the manage-mode right-click menu on doc rows

`POST /docs/update-metadata` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management",
  "title": "Docs Viewer Management",
  "summary": "Manage-mode source editing contract.",
  "ui_status": "done",
  "viewable": true,
  "parent_id": "ui-requests",
  "sort_order": 21
}
```

Metadata-update behavior:

- updates only front matter; body content and filename remain unchanged
- currently supports `title`, `summary`, `ui_status`, `viewable`, `parent_id`, and `sort_order`
- title changes do not mutate `doc_id` or filename
- `added_date` is preserved; `last_updated` is refreshed to the current minute after a successful metadata write
- blank `summary` removes the front matter field
- blank `ui_status` removes the front matter field
- non-blank `ui_status` is stored as the raw status key supplied by the client; the write server does not validate it against Docs Viewer config
- `viewable` is stored as a boolean when supplied; the Docs Viewer Edit modal uses this to map `status = draft` to `viewable: false` and any non-draft status to `viewable: true`
- responses include `changes.status_changed` and `changes.viewable_changed` alongside the other metadata change flags
- `parent_id` may be blank for root, but must otherwise resolve inside the same scope
- `parent_id` cannot point at the current doc or any of its descendants
- `sort_order` accepts a non-negative integer, blank, or `append`
- `append` stores the next available sparse `sort_order` under the requested `parent_id`
- always rebuilds docs payloads for the scope
- runs a targeted same-scope docs-search update for affected ids after a successful write
- skips docs-search updates when `ui_status` is the only changed field, because status emoji are viewer-only metadata
- keeps docs-search updates enabled for `viewable` changes so non-viewable docs are removed from search and newly viewable docs are added back

`POST /docs/update-viewability` expects:

```json
{
  "scope": "library",
  "doc_id": "example-doc",
  "viewable": true
}
```

`POST /docs/update-viewability-bulk` expects:

```json
{
  "scope": "library",
  "doc_ids": ["example-doc", "example-parent"],
  "viewable": true,
  "include_descendants": false
}
```

Viewability-update behavior:

- updates only the source doc's `viewable`, `published`, and `last_updated` front matter
- preserves `doc_id`, title, parent, sort order, body content, and `added_date`
- writes `published: true` alongside `viewable` so the doc stays in generated docs payloads
- the single-doc endpoint is preserved for callers that already use `doc_id`
- the bulk endpoint accepts explicit `doc_ids`; `include_descendants: true` expands each requested doc to include its descendants from canonical docs source data
- no-op requests write no files, create no backup, and do not rebuild docs/search
- changed bulk requests copy only changed source files into the backup bundle, then run one docs rebuild and one targeted docs-search update for the scope
- the Docs Viewer manage-mode `Make viewable` action now uses the bulk endpoint so it can include required ancestors and optional descendants in one write/rebuild

`POST /docs/move` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management",
  "target_doc_id": "scripts-docs-management-server",
  "position": "after"
}
```

Move behavior:

- `position: "after"` places the dragged doc immediately after the target doc and adopts the target doc's `parent_id`
- `position: "inside"` places the dragged doc as the last child of the target doc
- only leaf docs can move; docs with child docs are rejected
- moves rewrite front matter only and never move files on disk
- moves update the dragged doc's `parent_id` and normalize the destination sibling set to sparse unique `sort_order` values
- moves preserve `added_date`
- moves refresh `last_updated` on each source doc whose placement front matter is rewritten
- moves may rewrite multiple sibling docs when normalization changes their order values
- successful move responses include `undo_records` for every doc whose placement changed
- successful moves rebuild the current scope docs payloads and run a targeted docs-search update for the moved doc

`POST /docs/restore-move` expects:

```json
{
  "scope": "studio",
  "focus_doc_id": "docs-viewer-management",
  "records": [
    {
      "doc_id": "docs-viewer-management",
      "parent_id": "ui-requests",
      "sort_order": 21
    }
  ]
}
```

Restore-move behavior:

- restores one client-side move history step by rewriting all supplied placement records
- validates each restored `parent_id` against the current scope and rejects self-parent or descendant-parent cycles
- accepts integer or blank `sort_order`
- writes only records whose current placement differs from the supplied restore record
- refreshes `last_updated` on each restored source doc whose placement front matter is rewritten
- rebuilds the current scope docs payloads and runs targeted docs-search updates for changed doc ids

`POST /docs/archive` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Request behavior:

- moves the doc into the Archive section by setting `parent_id = archive`
- appends the archived doc as the last sibling under `archive`
- does not move the file on disk
- preserves `added_date` and refreshes `last_updated` to the current minute
- fails when `archive` is not defined for the scope

`POST /docs/delete-preview` expects:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Preview behavior:

- reports blockers such as child docs that still depend on the target
- reports inbound markdown references as warnings
- returns the file path that would be removed

`POST /docs/delete-apply` accepts the same shape plus:

```json
{
  "confirm": true
}
```

Apply behavior:

- requires explicit confirmation
- re-runs preview validation before delete
- deletes the Markdown source file when no blockers remain
- rebuilds the current scope docs payloads and runs a targeted docs-search removal/update after delete

## Security Constraints

- binds to loopback only
- CORS allows loopback origins only
- write targets are allowlisted to:
  - `_docs/*.md`
  - `_docs_analysis/**/*.md`
  - `_docs_library/*.md`
  - `var/docs/backups/`
  - `var/studio/export-import/<data-domain>/exports/`
  - `var/studio/export-import/<data-domain>/import-preview/`
  - `var/docs/logs/`
  - `var/docs/watch-suppressions/`
- timestamped backup bundles are created under `var/docs/backups/` before each non-dry-run write batch
- backups are operation-scoped rather than full-scope:
  - `create` writes a manifest-only backup bundle
  - `archive` backs up only the touched doc before rewrite
  - `delete` backs up only the deleted doc before removal

## Operational Notes

- `bin/dev-studio` starts this service on `http://127.0.0.1:8789`
- the shared Docs Viewer probes `GET /capabilities` for generated-data reads on normal local loads and for write capability when `?mode=manage` is present
- if the local service is unavailable, the viewer falls back to static generated JSON for normal public-style reads; manage mode stays read-only and shows a manage-mode unavailable message
- successful source writes now leave short-lived suppression markers under `var/docs/watch-suppressions/` so the docs live watcher can skip duplicate same-scope rebuilds for the exact files already rebuilt by the server
- `var/` is excluded from Jekyll because docs-management backups, logs, staged imports, and watcher-suppression markers are local operational files rather than publishable site input
- `bin/dev-studio` also uses a local-only Jekyll overlay so generated docs/search JSON can be read from this server without making Jekyll watch those generated files

## Verification

Export/import adapter behavior is covered by focused checks:

- `tests/python/test_docs_export.py` verifies the Library export engine and service-facing output contracts.
- `tests/python/test_docs_import.py` verifies staged Library import parsing, preview rendering, and path allowlists.
- `tests/python/test_docs_import_service.py` verifies Library import staged-file listing, preview dry-run/write behavior, summary apply, hierarchy apply, backups, and confirmation gates.
- `tests/python/test_export_import_adapters.py` verifies active adapter resolution and future stub rejection.
- `tests/python/test_docs_activity.py` verifies Docs Management Studio Activity helper suppression, record groups, source refs, and warning status behavior.
- `tests/smoke/data_import.py` verifies the Studio import route, preview/apply UI flow with mocked service responses, unavailable-service state, and disabled future-adapter state.

The `docs` profile runs the parser, service, and adapter checks.
The `studio-smoke` profile builds a temporary site and runs the Studio import route smokes.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
