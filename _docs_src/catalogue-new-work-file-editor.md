---
doc_id: catalogue-new-work-file-editor
title: "New Catalogue Work File"
added_date: 2026-04-18
last_updated: 2026-04-27
parent_id: user-guide
sort_order: 100
---
# New Catalogue Work File

Route:

- `/studio/catalogue-new-work-file/`
- current work may be preselected with `?work=<work_id>`

This page is retired.

Work files are now work-owned `downloads` metadata in `assets/studio/data/catalogue/works.json`.
The old standalone create endpoint no longer writes `work_files.json`.

## Current Scope

Historical scope:

- enter parent `work_id`
- enter `filename`
- enter `label`
- create one draft work-file record through the local catalogue write service
- redirect into the focused work-file editor after create

It did not copy or upload files. File placement remains outside this metadata migration.

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work File Editor](/docs/?scope=studio&doc=catalogue-work-file-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
