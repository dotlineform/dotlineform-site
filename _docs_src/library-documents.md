---
doc_id: library-documents
title: Library Documents
added_date: 2026-05-07
last_updated: "2026-05-07"
parent_id: library
sort_order: 20
---
# Library Documents

Route:

- `/studio/library-documents/`

Purpose:

- review generated Library Docs Viewer records in a dense sortable list

## Data Source

The page reads the generated Library docs index:

- `assets/data/docs/scopes/library/index.json`

The path is resolved through `studio_config.json` via the `docs.scopes.library.index` data path.
On the normal local Studio dev origin, the page tries the docs-management generated-index endpoint first because the dev Jekyll config excludes generated docs assets.
Static builds read the generated JSON asset first, then fall back to `GET /docs/generated/index?scope=library`.

## UI Contract

The page uses the shared dense list primitive:

- `tagStudioList`
- `tagStudioList--dense`
- `tagStudioList__head`
- `tagStudioList__sortBtn`
- `tagStudioList__sortIndicator`
- `tagStudioList__rows`
- `tagStudioList__row`
- `tagStudioList__cellLink`
- `tagStudioList__cellTitle`
- `tagStudioList__cellMeta`

Columns:

- `doc_id`
- `added_date`
- parent indicator
- `viewable`
- `title`

`doc_id`, `added_date`, and `title` are sortable columns.
`viewable` and parent are filter-only attributes.

## Filters

The page exposes two independent filter pills:

- `viewable`
- `parent`

`viewable` shows records where `viewable` is `true`.
`parent` shows records whose `doc_id` appears as another record's `parent_id` in the same generated Library index.

## Route Ready State

The route root `#libraryDocumentsRoot` follows the shared Studio route-ready contract:

- `data-studio-ready` is `false` while the config and Library docs index load, then `true` after rows or an error state render
- `data-studio-busy` is `true` during the initial load and `false` after render
- `data-studio-mode` is `list` when documents are available and `empty` when no records can be rendered
- `data-studio-record-loaded` is `true` when at least one document row is loaded

## Files

- `studio/library-documents/index.md`
- `assets/studio/js/library-documents.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
