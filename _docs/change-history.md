---
doc_id: change-history
title: Change History
added_date: 2026-05-19
last_updated: 2026-05-19
ui_status: report
parent_id: change-history-reports
sort_order: 1000
hidden: false
viewer_report: change_history
viewer_report_access: manage
---
# Change History

Viewer report:

- `change_history`

Purpose:

- browse structured `_docs_logs/` entries by domain in manage mode
- show 20 entries per page with pagination controls in the filter row and below the entry list

## Data Source

The report reads the local generated docs-log search projection through the Docs Management server:

- `_docs_logs/generated/search-index.json`
- `GET /docs/generated/docs-log?projection=search-index`

The projection is generated from `_docs_logs/entries/*.json`.
Run `./scripts/docs_logs/build_indexes.py --write` after changing entries.

## Availability

The report is manage-only:

- `viewer_report_access: manage`

The report tree root is listed in the Studio scope's `manage_only_tree_root_ids`, so these report pages stay out of public navigation and public docs search.

## Files

- `_docs/change-history-reports.md`
- `_docs/change-history.md`
- `_docs_logs/entries/*.json`
- `scripts/docs_logs/build_indexes.py`
- `scripts/docs_logs/migrate_legacy_logs.py`
- `assets/docs-viewer/js/reports/change-history-report.js`
