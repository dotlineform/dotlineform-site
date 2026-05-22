---
doc_id: data-models-library
title: Library Scope
added_date: 2026-03-31
last_updated: 2026-05-11
parent_id: library
sort_order: 1000
---
# Library Scope

This document covers the current checked-in data model for the Library scope.

## Scope Boundary

The Library scope is currently docs-only.

Current source and generated artifacts:

- source docs:
  - `_docs_library/*.md`
- generated docs data:
  - `assets/data/docs/scopes/library/index.json`
  - `assets/data/docs/scopes/library/by-id/<doc_id>.json`
- Library docs search:
  - `assets/data/search/library/index.json`
- Library export configs:
  - `assets/studio/data/library_export_configs.json`
  - `assets/studio/data/library_export_configs.schema.json`
- export/import adapter dispatch:
  - `assets/studio/data/data_sharing_adapters.json`
  - `assets/studio/data/data_sharing_adapters.schema.json`
- local generated export artifacts:
  - `var/studio/data-sharing/library/exports/<export_id>-<timestamp>.json`
  - `var/studio/data-sharing/library/exports/<export_id>-<timestamp>.jsonl`
- local import staging artifacts:
  - `var/studio/data-sharing/library/import-staging/<filename>.json`
  - `var/studio/data-sharing/library/import-staging/<filename>.jsonl`
- local import preview artifacts:
  - `var/studio/data-sharing/library/import-preview/<filename>.md`

Current public route:

- `/library/`

## Source Model

### `_docs_library/*.md`

Purpose:

- canonical authored content for the Library docs scope

Current design:

- same front-matter model as the Studio docs scope
- same Markdown-or-raw-HTML authoring model
- separate source root so Library can grow without being folded into Studio docs
- Library import/create defaults new docs to `published: true`, `viewable: false` so they are generated for manage-mode review without appearing on the public/default `/library/` route
- Docs Viewer management writes new `added_date` and changed `last_updated` values with minute precision, while existing date-only Library docs remain valid
- optional `summary` front matter stores a concise plain-text document summary; the shared Docs Viewer metadata editor can maintain it, blank values remove the field, and whitespace is normalized to one paragraph
- optional `ui_status` front matter stores a Docs Viewer status key that is carried into generated docs payloads and interpreted against scope-specific viewer config
- Library export configs are defined separately from source docs by `assets/studio/data/library_export_configs.json` and `assets/studio/data/library_export_configs.schema.json`; v1 export configs should read Library Docs Viewer source/generated fields without mutating them

Current implementation note:

- the Library source corpus is still small, but it now contains multiple imported docs
- the route still uses the same docs-scope contract as Studio rather than a Library-specific runtime

That is not a special-case runtime model. It is simply a small corpus using the same docs-scope contract as Studio.

## Generated Docs Data

### `assets/data/docs/scopes/library/index.json`

Purpose:

- lightweight tree/index payload for the Library docs corpus

Current content families:

- one row per generated Library doc
- identity, added/update dates, optional `summary`, optional `ui_status`, ordering, `published`, `viewable`, viewer URL, per-doc content URL, and `content_text_length`
- `viewer_options` for scope-level display behavior such as hiding document-view updated dates

Current site mapping:

- the nav/tree layer on `/library/`
- public/default `/library/` hides docs with `viewable: false`; `/docs/?scope=library&mode=manage` can show those generated docs for local management
- Library document view does not display the `last_updated` metadata row; recently-added still uses `added_date`, and search still uses `last_updated`
- `/studio/data-sharing/prepare/?mode=manage` uses `content_text_length` to filter docs whose rendered body has no text after plain-text extraction and title stripping

### `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Purpose:

- per-doc rendered payload for one Library doc

Current content families:

- doc identity metadata
- optional `summary` and `ui_status` metadata when the source front matter defines them
- rendered `content_html`

Current site mapping:

- the content pane on `/library/`

## Library Search Data

### `assets/data/search/library/index.json`

Purpose:

- search-owned flattened index for published Library docs

Current content families:

- one `doc` entry per public-viewable Library doc after applying `viewable` filtering
- identity, viewer URL, last-updated metadata, and normalized search text

Library recently-added lists use `added_date` from the generated docs index. Library search continues to use `last_updated`.
Library search does not currently consume `summary`.

Current site mapping:

- inline Library docs search on `/library/`

## Library Export Data

Library export configs are source-controlled Studio data, but export files themselves are local generated artifacts.

Config files:

- `assets/studio/data/library_export_configs.json`
- `assets/studio/data/library_export_configs.schema.json`

Generated output:

- `var/studio/data-sharing/library/exports/<export_id>-<timestamp>.json`
- `var/studio/data-sharing/library/exports/<export_id>-<timestamp>.jsonl`

Current model:

- configs read generated Library Docs Viewer index and per-doc payload data
- configs do not mutate `_docs_library/*.md`
- export files are ignored by git and are safe to delete
- export files are reproducible from generated Library docs data, the selected config, and the selected document ids
- document body export uses plain text derived from rendered `content_html`; default exports should not expose raw rendered HTML

Current consumers:

- `/studio/data-sharing/prepare/?mode=manage`
- `POST /studio/api/docs/data-sharing/prepare` on the local Studio app server
- `./scripts/docs/docs_export.py`

Current limits:

- Library is the only configured v1 export scope
- batching and long-document chunking are deferred
- direct LLM API calls are out of scope
- markdown target files and raw Markdown exports are future config extensions

## Library Import Data

Library import files are local working artifacts copied into a staging folder for preview-first review.

Staged input:

- `var/studio/data-sharing/library/import-staging/<filename>.json`
- `var/studio/data-sharing/library/import-staging/<filename>.jsonl`

Preview output:

- `var/studio/data-sharing/library/import-preview/<filename>.md`

Current model:

- staged files are ignored by git and are safe to delete
- import v1 reads staged data files but does not mutate `_docs_library/*.md`
- the read-only parser accepts Library export-shaped data and minimal document-like JSON/JSONL rows
- unknown file-level and record-level metadata is preserved in parser reports
- parser reports compare staged records with the current generated Library docs index and generated payload filenames
- Markdown preview files are generated only when `./scripts/docs/docs_import.py --write-previews` is used
- summary and full-content imports write one preview file per parsed document
- relationship imports write one whole-tree preview file per staged relationships file
- summary apply can update selected source `summary` values through the docs-management service after preflight and confirmation
- hierarchy apply can update selected source `parent_id` values through the docs-management service after preflight and confirmation; current `sort_order` values are preserved
- hierarchy apply allows unresolved imported `parent_id` values as warnings; generated Library docs data treats those unresolved parents as root-level relationships

Current consumers:

- `./scripts/docs/docs_import.py`
- `GET /docs/import/files` on the docs-management server
- `POST /docs/import/preview` on the docs-management server
- `POST /docs/import/apply` on the docs-management server
- `/studio/data-sharing/review/?mode=manage`

Current limits:

- Library is the only supported v1 import scope
- full-content apply and imported `sort_order` apply are out of scope until explicitly specified

## Why The Library Model Is Valuable Even While Small

The current Library scope is intentionally using the same generated-docs and generated-search model as Studio even though its content is still minimal.

Why:

- it proves the shared Docs Viewer is genuinely scope-owned rather than Studio-only with renamed routes
- it gives Library a clean growth path without another data-model refactor
- it keeps builder, viewer, and search logic shared across docs scopes

## Dependencies And Enforcement

Current dependencies:

- Library docs data is written by [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- Library docs search is derived from the generated Library docs index as documented in [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)

Current enforcement:

- duplicate `doc_id` values are rejected by the docs builder before Library docs data is written
- unresolved Library `parent_id` references are allowed for imported hierarchy staging and are emitted as root-level generated relationships
- `published: false` docs are excluded before Library docs data is generated
- `viewable: false` docs remain in generated docs data for manage-mode review, but are excluded from Library search and public/default viewer discovery
- `archive` and its descendants remain generated; public/default Library tree discovery and Library search include only docs whose own `viewable` value permits it

## Performance Notes

The current Library scope inherits the same performance model as Studio docs:

- one lightweight docs index for tree/navigation
- one per-doc payload for heavier rendered content
- one flattened search artifact for inline search

This is arguably overbuilt for one doc today, but it is the right current implementation because it prevents a second structural migration when Library grows.

## Practical Update Rule

If the Library scope gains new artifact families beyond docs and docs search, add them here rather than burying them only in Docs Viewer or Search docs.
