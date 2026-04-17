---
doc_id: catalogue-work-detail-editor
title: Catalogue Work Detail Editor
last_updated: 2026-04-17
parent_id: studio
sort_order: 35
---

# Catalogue Work Detail Editor

Route:

- `/studio/catalogue-work-detail/`
- focused record selection uses `?detail=<detail_uid>`

This page edits one canonical work detail source record from `assets/studio/data/catalogue/work_details.json` and writes changes through the local catalogue write service.

## Current Scope

The first implementation covers:

- search by `detail_uid`
- open one work detail record
- edit `project_subfolder`
- edit `project_filename`
- edit `title`
- edit `status`
- show read-only fields for ids, published date, and dimensions
- preview the scoped rebuild impact for the parent work
- run `Save + Rebuild` through the local catalogue service

The rebuild remains work-scoped. Saving a detail and rebuilding regenerates the parent work outputs rather than introducing a separate detail-only planner.

## Save Boundary

Current save/rebuild flow:

1. page loads `works.json` and `work_details.json`
2. browser computes a record hash for stale-write protection
3. user edits the current detail form
4. `POST /catalogue/work-detail/save` sends the current `detail_uid`, the expected record hash, and the normalized detail patch
5. the local write server validates the full source set, writes `work_details.json`, creates backups, and returns the normalized saved record
6. `POST /catalogue/build-preview` reports the parent-work rebuild impact
7. `POST /catalogue/build-apply` rebuilds the parent work scope from canonical JSON

## Current Editable Fields

- `project_subfolder`
- `project_filename`
- `title`
- `status`

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
