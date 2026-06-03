---
doc_id: docs-data
title: Docs Data
added_date: 2026-04-19
last_updated: "2026-05-06 20:51"
parent_id: docs-viewer
viewable: true
---
# Docs Data

### `docs-viewer/source/studio/*.md`

Purpose:

- source corpus for the Studio docs scope served at `/docs/`

Current content families:

- front matter used as identity/tree metadata:
  - `doc_id`
  - `title`
  - `added_date`
  - `last_updated`
  - optional `summary`
  - optional `ui_status`
  - `parent_id`
  - optional `viewable`
- Markdown or raw HTML body content

Why Markdown is part of the data model here:

- for docs, the source Markdown is the canonical authored content
- the builder turns that content into the generated docs-viewer payloads

### `docs-viewer/generated/docs/studio/index.json`

Purpose:

- lightweight tree/index payload for the Studio docs corpus

Current content families:

- one row per generated Studio doc
- identity, title, added/update dates, optional `summary`, optional `ui_status`, optional non-empty `parent_id`, optional `viewable: false`, source path, viewer URL, and per-doc content URL
- `viewer_options` for scope-level display behavior such as keeping document-view updated dates visible

Current site mapping:

- left-hand tree and lookup layer for `/docs/`

Why it exists separately from the per-doc payload:

- the docs viewer needs tree metadata for many docs at once
- it should not load full rendered HTML for every doc on first page load

### `docs-viewer/generated/docs/studio/by-id/<doc_id>.json`

Purpose:

- per-doc rendered payload for one Studio doc

Current content families:

- the same identity metadata as the index row
- optional `summary` and `ui_status` metadata when the source front matter defines them
- rendered `content_html`

Current site mapping:

- right-hand document pane on `/docs/`

Why it is per-doc:

- docs bodies can be much larger than nav metadata
- loading them on demand keeps the shared viewer responsive

## Studio Docs Search Data

### `docs-viewer/generated/search/studio/index.json`

Purpose:

- search-owned flattened index for published Studio docs

Current content families:

- one `doc` entry per viewable Studio doc
- doc identity, title, viewer URL, last-updated metadata, parent context, and normalized search text

Search currently uses `last_updated`, not `added_date`. The docs-viewer recently-added list reads `added_date` from the generated docs index, but search review is intentionally separate.

Current site mapping:

- inline docs search on `/docs/`

Why it is derived from the docs index rather than the source Markdown directly:

- the canonical generated Studio docs corpus is the generated docs index, not every source file under `docs-viewer/source/studio/`
- docs with `viewable: false` can have generated payloads for manage mode, but are filtered out of public/default docs search

Current writer:

- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
