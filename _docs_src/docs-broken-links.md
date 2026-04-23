---
doc_id: docs-broken-links
title: "Docs Broken Links"
last_updated: 2026-04-23
parent_id: studio
sort_order: 35
---
# Docs Broken Links

This page provides a Studio-facing audit for Docs Viewer links.

Route:

- `/studio/docs-broken-links/`

Use it to run a broken-links check for one docs scope at a time:

- `studio`
- `library`

## What It Checks

The page reports two problem types:

- `not found`
  the link points at a docs page that does not exist
- `wrong title`
  the link resolves to a real docs page, but the visible link text does not exactly match that page's current title

Current rule:

- `wrong title` is a strict exact-title check
- intentionally shortened labels such as `Overview` linking to `Docs Viewer Overview` are reported
- same-doc fragment links are ignored
- this includes `#section` and links back to the current docs page with a fragment

## Result Columns

The page shows:

- `problem`
- `linked page`
- `link`
- `from page`

Current behavior:

- `linked page`, `link`, and `from page` all open in a new tab
- when the problem is `not found`, the first two links intentionally point at the failing target so the broken case is visible directly

## Runtime Boundary

The page depends on the local Docs Management Server.

Current flow:

1. user selects a docs scope
2. page sends `POST /docs/broken-links` to the localhost docs-management service
3. service runs the shared docs broken-links audit logic for that scope
4. page renders the returned issue list

The page is therefore a Studio maintenance surface for a read-only docs audit, not a public hosted feature.

## Related References

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
