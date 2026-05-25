---
doc_id: library-documents
title: Library Documents
added_date: 2026-05-07
last_updated: 2026-05-13
ui_status: report
parent_id: docs-viewer-scopes
sort_order: 1500
viewable: true
viewer_report: docs_index_table
viewer_report_access: manage
viewer_report_preset: library_documents_admin
viewer_report_scope: library
---
# Library Documents

Viewer report:

- `docs_index_table`

Purpose:

- review generated Library Docs Viewer records in a dense sortable list inside the Docs Viewer document pane

## Data Source

The report reads the generated Library docs index:

- `assets/data/docs/scopes/library/index.json`

The report uses `viewer_report_scope: library`, so it reads Library docs even though this request document lives in the Studio docs scope.
When local generated-data reads are available, the report can read the generated Library index through the Docs Viewer service.
Otherwise, it reads the static generated JSON asset.

## UI Contract

The report uses Docs Viewer-owned report styles and behavior.

It does not depend on Studio route state or Studio list primitives.

Columns:

- `title`
- `doc_id`
- `hidden`

All displayed columns are sortable.

Both the `doc_id` and `title` links open the `/docs/` management shell with `scope=library` for that document.

## Filters

The page exposes one filter pill:

- `hidden`

`hidden` shows records where `viewable` is `false`.

## Availability

The report is manage-only:

- `viewer_report_access: manage`

If this document is opened in a public read-only Docs Viewer route, the document pane should show an unavailable state rather than rendering the management report.

## Files

- `docs-viewer/source/studio/library-documents.md`
- `docs-viewer/runtime/js/docs-viewer-reports.js`
- `docs-viewer/runtime/js/reports/docs-index-table-report.js`
- `docs-viewer/static/css/docs-viewer-reports.css`
