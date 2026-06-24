---
doc_id: library-documents
title: Library Documents
added_date: 2026-05-07
last_updated: 2026-06-06
ui_status: report
parent_id: docs-viewer
viewer_report: docs_index_table
viewer_report_access: local
viewer_report_preset: library_documents_admin
viewer_report_scope: library
---
# Library Documents

Viewer report:

- `docs_index_table`

Purpose:

- review generated Library Docs Viewer records in a dense hierarchical list inside the Docs Viewer document pane

## Data Source

The report reads the generated Library docs index tree:

- `site/assets/data/docs/scopes/library/index-tree.json`

The report uses `viewer_report_scope: library`, so it reads Library docs even though this request document lives in the Studio docs scope.
When local generated-data reads are available, the report can read the generated Library index tree through the Docs Viewer service.
Otherwise, it reads the static generated JSON asset.

## UI Contract

The report uses Docs Viewer-owned report styles and behavior.

It does not depend on Studio route state or Studio list primitives.

Rows follow the `index-tree.json` hierarchy by default, with child documents indented under their parent rows.

Columns:

- `title`
- `doc_id`
- `viewable`

All displayed columns are sortable.

Both the `doc_id` and `title` links open the `/docs/` management shell with `scope=library` for that document.

## Filters

The page exposes one filter pill:

- `non_viewable`

`non_viewable` shows records where `viewable` is `false`.

## Availability

The report is local-only:

- `viewer_report_access: local`

If this document is opened in a public read-only Docs Viewer route, the document pane should show an unavailable state rather than rendering the local report.

## Files

- `docs-viewer/source/studio/library-documents.md`
- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `docs-viewer/runtime/js/reports/docs-index-table-report.js`
- `docs-viewer/static/css/docs-viewer-reports.css`
