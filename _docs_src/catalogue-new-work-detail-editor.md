---
doc_id: catalogue-new-work-detail-editor
title: "New Catalogue Work Detail"
added_date: 2026-04-18
last_updated: 2026-04-29
parent_id: user-guide
sort_order: 60
---
# New Catalogue Work Detail

Route:

- `/studio/catalogue-new-work-detail/`
- focused create flow accepts `?work=<work_id>`

This legacy page redirects to the unified work-detail editor route.

When `?work=<work_id>` is supplied, the page redirects to `/studio/catalogue-work-detail/?work=<work_id>&mode=new`.

When no parent work is supplied, the page redirects to `/studio/catalogue-work/` so the user can choose the parent work first.

## Current Scope

The active create implementation now lives in [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor).

The old standalone page exists only as a compatibility redirect for bookmarked links and stale dashboard/work-page links.

The old `assets/studio/js/catalogue-new-work-detail-editor.js` controller has been removed, and the compatibility route is not represented by an active route key or UI text block in `studio_config.json`.

## Media Boundary

The compatibility redirect does not upload or copy media.

It only captures the source metadata fields that point at the existing detail media conventions such as:

- `project_subfolder`
- `project_filename`

## Related References

- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
