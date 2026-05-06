---
doc_id: docs-broken-links
title: "Docs Broken Links"
added_date: 2026-04-23
last_updated: "2026-05-06 16:15"
parent_id: studio
sort_order: 35
---
# Docs Broken Links

This page provides a Studio-facing audit for Docs Viewer links that no longer resolve.

Route:

- `/studio/docs-broken-links/`

Use it to run a broken-links check for one docs scope at a time:

- `studio`
- `library`

## What It Checks

The page reports one problem type:

- `not found`
  the link points at a docs page that does not exist

Current rule:

- visible link text is not checked against the current target title
- changed or shortened link labels are allowed because they can be useful corrections to outdated titles
- links inside rendered code blocks are ignored
- same-doc fragment links are ignored
- this includes `#section` and links back to the current docs page with a fragment

## Result Columns

The page shows:

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

The page depends on the local Docs Management Server.

Current flow:

1. user selects a docs scope
2. page sends `POST /docs/broken-links` to the localhost docs-management service
3. service runs the shared docs broken-links audit logic for that scope
4. page renders the returned issue list

The page is therefore a Studio maintenance surface for a read-only docs audit, not a public hosted feature.

## Route Ready State

The page root `#docsBrokenLinksRoot` exposes the shared Studio route-ready contract:

- `data-studio-ready` is `false` during initial config and Docs Management Server checks, then `true` after the initial disabled or interactive state is rendered
- `data-studio-busy` is `true` while an audit request is running
- `data-studio-mode` is `idle` before results and `results` after issues are loaded
- `data-studio-service` reports whether the Docs Management Server is available
- `data-studio-record-loaded` is `true` when audit entries are loaded

## Related References

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
