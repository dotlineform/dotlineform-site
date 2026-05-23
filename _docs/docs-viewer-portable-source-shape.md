---
doc_id: docs-viewer-portable-source-shape
title: Docs Viewer Portable Source Shape
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: docs-viewer-portable-setup
sort_order: 3200
---
# Docs Viewer Portable Source Shape

## Source Docs Required Shape

Each scope has a source root, currently configured in `scripts/docs/docs_scopes.json`.

Current roots:

- `_docs/` for `studio`
- `_docs_library/` for `library`
- `_docs_analysis/` for `analysis`

Each source doc is Markdown with optional YAML front matter.
Important fields:

- `doc_id`: stable viewer id; defaults to the file stem when omitted
- `title`: display title; falls back to the first H1 or humanized filename
- `parent_id`: parent document id; blank means top-level
- `sort_order`: numeric sibling ordering
- `summary`: optional short summary
- `ui_status`: optional viewer status pill
- `published`: `false` removes the doc from generated viewer data
- `hidden`: `true` keeps the doc generated but hidden from read-only public views
- `last_updated`: display/search metadata
- `added_date`: recently-added metadata

A minimal root doc for a new Library-style scope looks like:

```md
---
doc_id: library
title: Library
added_date: 2026-05-11
last_updated: "2026-05-11"
parent_id: ""
sort_order: 10
viewable: true
---
# Library

Start writing here.
```
