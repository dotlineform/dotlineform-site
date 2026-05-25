---
doc_id: site-change-log
title: Site Change Log
added_date: 2026-04-24
last_updated: 2026-05-19
parent_id: archive
sort_order: 81000
---

# Site Change Log

This log has been deprecated. Use the manage-only [Change History](/docs/?scope=studio&doc=change-history&mode=manage) report for date and domain browsing across migrated entries. The change log process is described in [Development Workflow](/docs/?scope=studio&doc=development-workflow)

---

## Current Source Model

- canonical detailed entries: `_docs_logs/entries/*.json`
- generated local projections: `_docs_logs/generated/*.json`
- migration diagnostics: `_docs_logs/reports/migration-review.json`
- entry helper: `./studio/workflows/change-requests/services/log_entry.py`
- index builder: `./studio/workflows/change-requests/services/build_indexes.py --write`

Generated projections and reports are ignored local build output.

## Archives

The old long-form archive pages are retained as compact migration stubs so existing links stay stable:

- [Site Change Log Archive: May 2026](/docs/?scope=studio&doc=site-change-log-2026-05)
- [Site Change Log Archive: April 2026](/docs/?scope=studio&doc=site-change-log-2026-04)
- [Site Change Log Archive: March 2026 And Earlier](/docs/?scope=studio&doc=site-change-log-2026-03-and-earlier)

## Migration Summary

The migration converted dated site and Search change-log sections into structured per-entry JSON records.

Migrated source files:

- `docs-viewer/source/studio/site-change-log.md`
- `docs-viewer/source/studio/site-change-log-2026-05.md`
- `docs-viewer/source/studio/site-change-log-2026-04.md`
- `docs-viewer/source/studio/site-change-log-2026-03-and-earlier.md`
- `docs-viewer/source/studio/search-change-log.md`

Migrated entries now live as flat files under `_docs_logs/entries/change-YYYY-MM-DD-entry-slug.json`.
