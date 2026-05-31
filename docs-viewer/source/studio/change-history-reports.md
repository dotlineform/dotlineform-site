---
doc_id: change-history-reports
title: Change History Reports
added_date: 2026-05-19
last_updated: 2026-05-31
parent_id: dev-home
viewable: true
---
# Change History Reports

Manage-only report pages for structured project change history.

The source of truth is `studio/workflows/change-requests/logs/entries/*.json`.
Generated report data under `studio/workflows/change-requests/generated/` and `studio/workflows/change-requests/reports/` is local build output and is not tracked.

## Change History

Viewer report: `change_history`<br>
Doc: [Change History](/docs/?scope=studio&doc=change-history&mode=manage)

- browse structured change-history entries by domain in manage mode
- filter entries with a report-local search box and domain selector
- show 20 entries per page with compact pagination controls in the filter row and below the entry list
- `viewer_report_access: manage` The report tree root is listed in the Studio scope's `manage_only_tree_root_ids`, so these report pages stay out of public navigation and public docs search.

The report reads the local generated docs-log search projection through the Docs Viewer service:

- `studio/workflows/change-requests/generated/search-index.json`
- `GET /docs/generated/docs-log?scope=studio&projection=search-index`

The projection is generated from `studio/workflows/change-requests/logs/entries/*.json`.<br>
Run `./studio/workflows/change-requests/services/docs_logs/build_indexes.py --write` after changing entries.

**Files**

- `docs-viewer/source/studio/change-history-reports.md`
- `docs-viewer/source/studio/change-history.md`
- `studio/workflows/change-requests/logs/entries/*.json`
- `studio/workflows/change-requests/services/docs_logs/build_indexes.py`
- `studio/workflows/change-requests/services/docs_logs/migrate_legacy_logs.py`
- `docs-viewer/runtime/js/reports/change-history-report.js`

---
