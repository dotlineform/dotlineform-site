---
doc_id: change-history-reports
title: Change History Reports
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: dev-home
sort_order: 26000
viewable: true
---
# Change History Reports

Manage-only report pages for structured project change history.

The source of truth is `_docs_logs/entries/*.jsonl`.
Generated report data under `_docs_logs/generated/` and `_docs_logs/reports/` is local build output and is not tracked.

## Change History

Viewer report: `change_history`<br>
Doc: [Change History](/docs/?scope=studio&doc=change-history&mode=manage)

- browse structured `_docs_logs/` entries by domain in manage mode
- filter entries with a report-local search box and domain selector
- show 20 entries per page with compact pagination controls in the filter row and below the entry list
- `viewer_report_access: manage` The report tree root is listed in the Studio scope's `manage_only_tree_root_ids`, so these report pages stay out of public navigation and public docs search.

The report reads the local generated docs-log search projection through the Docs Management server:

- `_docs_logs/generated/search-index.json`
- `GET /docs/generated/docs-log?scope=studio&projection=search-index`

The projection is generated from `_docs_logs/entries/*.json`.<br>
Run `./scripts/docs_logs/build_indexes.py --write` after changing entries.

**Files**

- `_docs/change-history-reports.md`
- `_docs/change-history.md`
- `_docs_logs/entries/*.json`
- `scripts/docs_logs/build_indexes.py`
- `scripts/docs_logs/migrate_legacy_logs.py`
- `assets/docs-viewer/js/reports/change-history-report.js`

---
