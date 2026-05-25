---
doc_id: docs-broken-links
title: Docs Broken Links
added_date: 2026-04-23
last_updated: 2026-05-22
ui_status: report
parent_id: docs-viewer
sort_order: 18000
viewable: true
viewer_report: docs_broken_links
viewer_report_access: manage
---
# Docs Broken Links

This report audits Docs Viewer links that no longer resolve.

Route:

- `/docs/?scope=studio&doc=docs-broken-links&mode=manage`

Use it to run a broken-links check for one configured docs scope at a time.
The scope menu is rendered from the shared Docs Viewer config:

- `studio`
- `library`
- `analysis`

## What It Checks

The report shows one problem type:

- `not found`
  the link points at a docs page that does not exist

Current rule:

- visible link text is not checked against the current target title
- changed or shortened link labels are allowed because they can be useful corrections to outdated titles
- links inside rendered code blocks are ignored
- same-doc fragment links are ignored
- this includes `#section` and links back to the current docs page with a fragment

## Result Columns

The report table shows:

- `problem`
- `from page`
- `linked page`
- `link`

Current behavior:

- `linked page`, `link`, and `from page` all open in a new tab
- docs-viewer result links open with `mode=manage` so the target page can be inspected or edited directly
- when the problem is `not found`, the first two links intentionally point at the failing target so the broken case is visible directly
- all result columns are sortable
- the default sort is `from page` ascending

## Runtime Boundary

The report depends on the local Docs management API through the configured Docs Viewer service.

Current flow:

1. Docs Viewer loads this report-backed document in manage mode
2. the report module selects the current or requested docs scope
3. the report sends `POST <DOCS_VIEWER_BASE_URL>/docs/broken-links`
4. the Docs Viewer service runs the shared docs broken-links audit logic for that scope
5. the report renders the returned issue list

This is a Docs Viewer management report for a read-only docs audit, not a public hosted feature.

The old `/studio/docs-broken-links/` route shell and Studio page controller have been retired.
The reusable Python audit remains under `docs-viewer/services/docs_broken_links.py`, and the local Docs API endpoint remains `POST /docs/broken-links`.

## Related References

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Reports](/docs/?scope=studio&doc=docs-viewer-reports)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
