---
doc_id: data-models-analysis
title: Analysis Scope
added_date: 2026-04-26
last_updated: 2026-06-05
parent_id: docs-viewer-scopes
viewable: true
---
# Analysis Scope

This document covers the current checked-in data model for the public Analysis docs scope.

## Scope Boundary

The Analysis scope is currently docs-only.

Current checked-in artifacts:

- source docs:
  - `docs-viewer/source/analysis/**/*.md`
- generated docs data:
  - `assets/data/docs/scopes/analysis/index-tree.json`
  - `assets/data/docs/scopes/analysis/recently-added.json`
  - `assets/data/docs/scopes/analysis/by-id/<doc_id>.json`
- Analysis docs search:
  - `assets/data/search/analysis/index.json`

Current public route:

- `/analysis/`

## Source Model

### `docs-viewer/source/analysis/**/*.md`

Purpose:

- canonical authored content for the public Analysis docs scope

Current design:

- same front-matter tree model as Studio and Library docs
- same Markdown-or-raw-HTML authoring model
- separate source root so Analysis does not bleed into Library or Studio docs
- nested source folders are allowed for Analysis source files
- viewer organisation still comes from `doc_id`, `parent_id`, and generated title ordering, not from source folders

Expected future source-folder conventions:

- `docs-viewer/source/analysis/series/series-<series_id>.md`
- `docs-viewer/source/analysis/works/work-<work_id>.md`

Those folders are a source-organisation affordance for future UI lookup and generation helpers. They are not the primary viewer navigation model.

## Generated Docs Data

### `assets/data/docs/scopes/analysis/index-tree.json`

Purpose:

- compact navigation tree payload for the Analysis docs corpus

Current content families:

- one row per generated Analysis doc
- identity, title, optional non-empty `parent_id`, optional `viewable: false`, optional `ui_status`, and per-doc content URL
- `viewer_options` using the shared docs-scope option shape

Current site mapping:

- the nav/tree layer on `/analysis/`

Retired route artifact:

- public `assets/data/docs/scopes/analysis/index.json` is not part of the Docs Viewer route contract and is not published for public route loading

### `assets/data/docs/scopes/analysis/by-id/<doc_id>.json`

Purpose:

- per-doc rendered payload for one Analysis doc

Current content families:

- reader-facing metadata: title, optional `summary`, and `last_updated`
- rendered `content_html`

Current site mapping:

- the content pane and public info panel on `/analysis/`

Public by-id payloads do not expose management fields such as `doc_id`, `source_path`, `viewer_url`, `ui_status`, `viewable`, `parent_id`, `added_date`, `content_text_length`, or report metadata.

### `assets/data/docs/scopes/analysis/recently-added.json`

Purpose:

- small recently-added payload for the public Analysis route

Current content families:

- schema `docs_recently_added_v1`
- configured result limit
- rows with doc identity, title, content URL, `added_date`, optional `parent_id`, and optional `parent_title`

Current site mapping:

- recently-added mode on `/analysis/`

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
- Analysis docs search is derived from Analysis source front matter as documented in [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture)

Current enforcement:

- duplicate `doc_id` values and invalid `parent_id` references are rejected by the docs builder before Analysis docs data is written
- `viewable: false` docs remain in generated docs data for manage-mode review, but are excluded from Analysis search and public/default viewer discovery

## Practical Update Rule

If Analysis gains generated families beyond docs tree/recent/by-id and docs search, add them here rather than burying them only in Docs Viewer or Search docs.
