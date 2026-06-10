---
doc_id: docs-viewer-public-scopes
title: Public Scopes
added_date: 2026-03-31
last_updated: 2026-06-10
parent_id: docs-viewer
---
# Public Scopes

Current public routes:

- `/library/`
- `/analysis/`

## Dependencies

- shared Docs Viewer management conventions
- Analytics Data Sharing service conventions for package preparation, review, and confirmed apply

## Scope Boundary

Source and generated artifacts:

- source docs:
  - `docs-viewer/source/<scope>/*.md`
- working generated docs data:
  - `docs-viewer/generated/docs/<scope>/index-tree.json`
  - `docs-viewer/generated/docs/<scope>/recently-added.json`
  - `docs-viewer/generated/docs/<scope>/by-id/<doc_id>.json`
- working docs search:
  - `docs-viewer/generated/search/<scope>/index.json`
- published docs data:
  - `assets/data/docs/scopes/<scope>/index-tree.json`
  - `assets/data/docs/scopes/<scope>/recently-added.json`
  - `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`
- published docs search:
  - `assets/data/search/<scope>/index.json`
- export configs:
  - `data-sharing/config/<scope>-export-configs.json`
  - `data-sharing/config/<scope>-export-configs.schema.json`
- export/import adapter dispatch:
  - `data-sharing/config/adapters.json`
  - `data-sharing/config/adapters.schema.json`
- local generated export artifacts:
  - `var/analytics/data-sharing/<scope>/exports/<export_id>-<timestamp>.json`
  - `var/analytics/data-sharing/<scope>/exports/<export_id>-<timestamp>.jsonl`
- local import staging artifacts:
  - `var/analytics/data-sharing/<scope>/import-staging/<filename>.json`
  - `var/analytics/data-sharing/<scope>/import-staging/<filename>.jsonl`
- local import preview artifacts:
  - `var/analytics/data-sharing/<scope>/import-preview/<filename>.md`

## Source Model

### `docs-viewer/source/<scope>/*.md`

Purpose: canonical authored content for the Library docs scope

Design:

- the route uses the same docs-scope contract as Studio rather than a scope-specific runtime
- same front-matter model as the Studio docs scope
- same Markdown-or-raw-HTML authoring model
- separate source root so scope can grow without being folded into Studio docs
- import/create defaults new docs to `viewable: false` so they are generated for manage-mode review without appearing on the public/default `/<scope>/` route
- optional `summary` front matter stores a concise plain-text document summary; the shared Docs Viewer metadata editor can maintain it, blank values remove the field, and whitespace is normalized to one paragraph
- optional `ui_status` front matter stores a Docs Viewer status key that is carried into generated docs payloads and interpreted against scope-specific viewer config
- export configs are defined separately from source docs by `data-sharing/config/<scope>-export-configs.json` and `data-sharing/config/<scope>-export-configs.schema.json`; export configs should read Docs Viewer source/generated fields without mutating them

## Generated Docs Data

### Working And Published Roots

Public scope source edits, live watcher rebuilds, and docs-management write follow-through rebuild working generated output under `docs-viewer/generated/`.
Public routes read only the published snapshots under `assets/data/`.

Publishing is a local management action:

- `GET /docs/publish/status?scope=<scope>` reports pending working-to-published changes
- `POST /docs/publish/confirm` reports the confirmation diff without writing
- `POST /docs/publish/apply` requires `confirm: true` and syncs working docs/search to the published snapshot roots, removing stale published files

The v1 publish gate is local and file-based.
It does not add persistent confirmation ids, rollback, unpublish, publish manifests, or durable publish summary artifacts.

### `assets/data/docs/scopes/<scope>/index-tree.json`

Purpose: compact navigation tree payload for the docs corpus

Current content families:

- one row per generated doc
- identity, title, optional non-empty `parent_id`, optional `viewable: false`, optional `ui_status`, and per-doc content URL
- `viewer_options` for scope-level display behavior such as hiding document-view updated dates

Current site mapping:

- the nav/tree layer on `/<scope>/`
- public/default `/<scope>/` hides docs with `viewable: false`; `/docs/?scope=<scope>&mode=manage` can show those generated docs for local management

### `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`

Purpose: per-doc rendered payload for one Library doc

Current content families:

- reader-facing metadata: title, optional `summary`, and `last_updated`
- rendered `content_html`

Current site mapping:

- the content pane and public info panel on `/<scope>/`

Public by-id payloads do not expose management fields such as `doc_id`, `source_path`, `viewer_url`, `ui_status`, `viewable`, `parent_id`, `added_date`, `content_text_length`, or report metadata.

### `assets/data/docs/scopes/<scope>/recently-added.json`

Purpose: small 'recently-added' payload for the public route.

Current content families:

- schema `docs_recently_added_v1`
- configured result limit
- rows with doc identity, title, content URL, `added_date`, optional `parent_id`, and optional `parent_title`

Current site mapping:

- recently-added mode on `/<scope>/`

## Search Data

### `assets/data/search/<scope>/index.json`

Purpose:

- search-owned flattened index for public-viewable docs

Current content families:

- one `doc` entry per public-viewable doc after applying `viewable` filtering
- identity, viewer URL, last-updated metadata, and normalized search text

Note:

- Recently-added lists use `added_date` from `recently-added.json`.
- Search uses `last_updated`.

Current site mapping:

- inline docs search on `/<scope>/`

## Export Data

Export configs are source-controlled Analytics data, but export files themselves are local generated artifacts.

Config files:

- `data-sharing/config/<scope>-export-configs.json`
- `data-sharing/config/<scope>-export-configs.schema.json`

Generated output:

- `var/analytics/data-sharing/<scope>/exports/<export_id>-<timestamp>.json`
- `var/analytics/data-sharing/<scope>/exports/<export_id>-<timestamp>.jsonl`

Current model:

- configs read generated Docs Viewer index and per-doc payload data
- configs do not mutate `docs-viewer/source/<scope>/*.md`
- export files are ignored by git and are safe to delete
- export files are reproducible from generated docs data, the selected config, and the selected document ids
- document body export uses plain text derived from rendered `content_html`; default exports should not expose raw rendered HTML

Current consumers:

- `/analytics/data-sharing/prepare/?mode=manage`
- `GET /analytics/api/data-sharing/selectable-records` on the Local Analytics app server
- `POST /analytics/api/data-sharing/prepare` on the Local Analytics app server
- `docs-viewer/services/docs_export.py`

Current limits:

- Library is the only configured v1 export scope
- no batching and long-document chunking
- markdown target files and raw Markdown exports are future config extensions

## Import Data

Import files are local working artifacts copied into a staging folder for preview-first review.

Staged input:

- `var/analytics/data-sharing/<scope>/import-staging/<filename>.json`
- `var/analytics/data-sharing/<scope>/import-staging/<filename>.jsonl`

Preview output:

- `var/analytics/data-sharing/<scope>/import-preview/<filename>.md`

Current model:

- staged files are ignored by git and are safe to delete
- import v1 reads staged data files but does not mutate `docs-viewer/source/<scope>/*.md`
- the read-only parser accepts Library export-shaped data and minimal document-like JSON/JSONL rows
- unknown file-level and record-level metadata is preserved in parser reports
- parser reports compare staged records with adapter-owned current document records and generated payload filenames
- Markdown preview files are generated only when `$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py --write-previews` is used
- summary and full-content imports write one preview file per parsed document
- relationship imports write one whole-tree preview file per staged relationships file
- summary apply can update selected source `summary` values through the Analytics Data Sharing API after preflight and confirmation
- hierarchy apply can update selected source `parent_id` values through the Analytics Data Sharing API after preflight and confirmation; retired `sort_order` front matter is removed when touched
- hierarchy apply allows unresolved imported `parent_id` values as warnings; generated Library docs data treats those unresolved parents as root-level relationships

Current consumers:

- `$HOME/miniconda3/bin/python3 docs-viewer/services/docs_import.py`
- `GET /analytics/api/data-sharing/returned-packages`
- `POST /analytics/api/data-sharing/review`
- `POST /analytics/api/data-sharing/apply`
- `/analytics/data-sharing/review/?mode=manage`

## Dependencies And Enforcement

Current dependencies:

- working docs data is written by [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- working docs search is derived from Library source front matter as documented in [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture)
- public snapshots are updated only through the Docs Viewer `Publish docs` management action

Current enforcement:

- duplicate `doc_id` values are rejected by the docs builder before docs data is written
- unresolved `parent_id` references are allowed for imported hierarchy staging and are emitted as root-level generated relationships
- `viewable: false` docs remain in generated docs data for manage-mode review, but are excluded from search and public/default viewer discovery

## Performance Notes

Public scopes inherit the same performance model as Studio docs:

- one compact docs tree payload for tree/navigation
- one small recently-added payload
- one per-doc payload for heavier rendered content
- one flattened search artifact for inline search
