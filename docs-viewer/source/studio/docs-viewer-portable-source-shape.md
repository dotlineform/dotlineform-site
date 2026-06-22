---
doc_id: docs-viewer-portable-source-shape
title: Portable Source Shape
added_date: 2026-05-19
last_updated: 2026-06-22
parent_id: docs-viewer-portable-setup
viewable: true
---
# Docs Viewer Portable Source Shape

## Source Docs Required Shape

Each scope has a source root, configured in `docs-viewer/config/scopes/docs_scopes.json`.
Repo-backed scopes use repo-relative source roots.
External local scopes use `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/<scope>/`, with the central scope config storing the `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer` marker instead of a user-specific absolute path.

Current roots:

- `docs-viewer/source/studio/` for `studio`
- `docs-viewer/source/library/` for `library`
- `docs-viewer/source/analysis/` for `analysis`

Each source doc is Markdown with optional YAML front matter.
Important fields:

- `doc_id`: stable viewer id; defaults to the file stem when omitted
- `title`: display title; falls back to the first H1 or humanized filename
- `parent_id`: parent document id; blank means top-level
- `summary`: optional short summary
- `ui_status`: optional viewer status pill
- `viewable`: `false` keeps the doc generated but excluded from read-only public views
- `last_updated`: display/search metadata
- `added_date`: recently-added metadata

The generated `index-tree.json` payload sorts root siblings and each parent’s children case-insensitively by `title`, with `doc_id` as a stable tie-breaker.

A minimal root doc for a new Library-style scope looks like:

```md
---
doc_id: library
title: Library
added_date: 2026-05-11
last_updated: "2026-05-11"
parent_id: ""
viewable: true
---
# Library

Start writing here.
```
