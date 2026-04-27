---
doc_id: catalogue-new-work-link-editor
title: "New Catalogue Work Link"
added_date: 2026-04-18
last_updated: 2026-04-27
parent_id: user-guide
sort_order: 120
---
# New Catalogue Work Link

Route:

- `/studio/catalogue-new-work-link/`
- current work may be preselected with `?work=<work_id>`

This page is retired.

Work links are now work-owned `links` metadata in `assets/studio/data/catalogue/works.json`.
The old standalone create endpoint no longer writes `work_links.json`.

## Current Scope

Historical scope:

- enter parent `work_id`
- enter `url`
- enter `label`
- create one draft work-link record through the local catalogue write service
- redirect into the focused work-link editor after create

It does not validate external link targets beyond normal field presence checks.

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Link Editor](/docs/?scope=studio&doc=catalogue-work-link-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
