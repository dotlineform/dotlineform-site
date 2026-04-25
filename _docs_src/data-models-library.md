---
doc_id: data-models-library
title: "Library Scope"
added_date: 2026-03-31
last_updated: 2026-04-25
parent_id: data-models
sort_order: 40
---

# Library Scope

This document covers the current checked-in data model for the Library scope.

## Scope Boundary

The Library scope is currently docs-only.

Current checked-in artifacts:

- source docs:
  - `_docs_library_src/*.md`
- generated docs data:
  - `assets/data/docs/scopes/library/index.json`
  - `assets/data/docs/scopes/library/by-id/<doc_id>.json`
- Library docs search:
  - `assets/data/search/library/index.json`

Current public route:

- `/library/`

## Source Model

### `_docs_library_src/*.md`

Purpose:

- canonical authored content for the Library docs scope

Current design:

- same front-matter model as the Studio docs scope
- same Markdown-or-raw-HTML authoring model
- separate source root so Library can grow without being folded into Studio docs
- Library import/create defaults new docs to `published: true`, `viewable: false` so they are generated for manage-mode review without appearing on the public/default `/library/` route
- optional `summary` front matter stores a concise plain-text document summary; the shared Docs Viewer metadata editor can maintain it, blank values remove the field, and whitespace is normalized to one paragraph

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
- identity, added/update dates, optional `summary`, ordering, `published`, `viewable`, viewer URL, and per-doc content URL
- `viewer_options` declaring `_archive` as a non-loadable, manage-only tree root and hiding document-view updated dates

Current site mapping:

- the nav/tree layer on `/library/`
- public/default `/library/` hides `_archive` and descendants; `/library/?mode=manage` shows that branch for local management
- Library document view does not display the `last_updated` metadata row; recently-added still uses `added_date`, and search still uses `last_updated`

### `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Purpose:

- per-doc rendered payload for one Library doc

Current content families:

- doc identity metadata
- optional `summary` metadata when the source front matter defines it
- rendered `content_html`

Current site mapping:

- the content pane on `/library/`

## Library Search Data

### `assets/data/search/library/index.json`

Purpose:

- search-owned flattened index for published Library docs

Current content families:

- one `doc` entry per public-viewable Library doc after applying viewability and manage-only tree-root filtering
- identity, viewer URL, last-updated metadata, and normalized search text

Library recently-added lists use `added_date` from the generated docs index. Library search continues to use `last_updated`.
Library search does not currently consume `summary`.

Current site mapping:

- inline Library docs search on `/library/`

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

- duplicate `doc_id` values and invalid `parent_id` references are rejected by the docs builder before Library docs data is written
- `published: false` docs are excluded before Library docs data is generated
- `viewable: false` docs remain in generated docs data for manage-mode review, but are excluded from Library search and public/default viewer discovery
- `_archive` and its descendants remain generated for manage mode but are excluded from public/default Library tree discovery and Library search

## Performance Notes

The current Library scope inherits the same performance model as Studio docs:

- one lightweight docs index for tree/navigation
- one per-doc payload for heavier rendered content
- one flattened search artifact for inline search

This is arguably overbuilt for one doc today, but it is the right current implementation because it prevents a second structural migration when Library grows.

## Practical Update Rule

If the Library scope gains new artifact families beyond docs and docs search, add them here rather than burying them only in Docs Viewer or Search docs.
