---
doc_id: catalogue-new-work-file-editor
title: "New Catalogue Work File"
added_date: 2026-04-18
last_updated: 2026-04-26
parent_id: user-guide
sort_order: 100
---
# New Catalogue Work File

Route:

- `/studio/catalogue-new-work-file/`
- current work may be preselected with `?work=<work_id>`

This page creates one draft `WorkFiles` source record in `assets/studio/data/catalogue/work_files.json`.

## Current Scope

The first implementation covers:

- enter parent `work_id`
- enter `filename`
- enter `label`
- create one draft work-file record through the local catalogue write service
- redirect into the focused work-file editor after create

It does not copy or upload files. File placement remains in the existing source-path workflow.

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work File Editor](/docs/?scope=studio&doc=catalogue-work-file-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
