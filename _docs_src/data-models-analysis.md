---
doc_id: data-models-analysis
title: "Analysis Scope"
added_date: 2026-04-26
last_updated: 2026-04-26
parent_id: data-models
sort_order: 35
---

# Analysis Scope

This document covers the current checked-in data model for the public Analysis docs scope.

## Scope Boundary

The Analysis scope is currently docs-only.

Current checked-in artifacts:

- source docs:
  - `_docs_src_analysis/**/*.md`
- generated docs data:
  - `assets/data/docs/scopes/analysis/index.json`
  - `assets/data/docs/scopes/analysis/by-id/<doc_id>.json`
- Analysis docs search:
  - `assets/data/search/analysis/index.json`

Current public route:

- `/analysis/`

## Source Model

### `_docs_src_analysis/**/*.md`

Purpose:

- canonical authored content for the public Analysis docs scope

Current design:

- same front-matter tree model as Studio and Library docs
- same Markdown-or-raw-HTML authoring model
- separate source root so Analysis does not bleed into Library or Studio docs
- nested source folders are allowed for Analysis source files
- viewer organisation still comes from `doc_id`, `parent_id`, and `sort_order`, not from source folders

Expected future source-folder conventions:

- `_docs_src_analysis/series/series-<series_id>.md`
- `_docs_src_analysis/works/work-<work_id>.md`

Those folders are a source-organisation affordance for future UI lookup and generation helpers. They are not the primary viewer navigation model.

## Generated Docs Data

### `assets/data/docs/scopes/analysis/index.json`

Purpose:

- lightweight tree/index payload for the Analysis docs corpus

Current content families:

- one row per generated Analysis doc
- identity, added/update dates, optional `summary`, ordering, `published`, `viewable`, viewer URL, and per-doc content URL
- `viewer_options` using the shared docs-scope option shape

Current site mapping:

- the nav/tree layer on `/analysis/`

### `assets/data/docs/scopes/analysis/by-id/<doc_id>.json`

Purpose:

- per-doc rendered payload for one Analysis doc

Current content families:

- doc identity metadata
- optional `summary` metadata when the source front matter defines it
- rendered `content_html`

Current site mapping:

- the content pane on `/analysis/`

## Analysis Search Data

### `assets/data/search/analysis/index.json`

Purpose:

- search-owned flattened index for public-viewable Analysis docs

Current content families:

- one `doc` entry per public-viewable Analysis doc
- identity, viewer URL, last-updated metadata, parent metadata, and normalized search text

Current site mapping:

- inline Analysis docs search on `/analysis/`

## Dependencies And Enforcement

Current dependencies:

- Analysis docs data is written by [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- Analysis docs search is derived from the generated Analysis docs index as documented in [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)

Current enforcement:

- duplicate `doc_id` values and invalid `parent_id` references are rejected by the docs builder before Analysis docs data is written
- `published: false` docs are excluded before Analysis docs data is generated
- `viewable: false` docs remain in generated docs data for manage-mode review, but are excluded from Analysis search and public/default viewer discovery

## Practical Update Rule

If Analysis gains generated families beyond docs and docs search, add them here rather than burying them only in Docs Viewer or Search docs.
