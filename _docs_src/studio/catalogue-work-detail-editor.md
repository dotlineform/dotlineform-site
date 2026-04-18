---
doc_id: catalogue-work-detail-editor
title: Catalogue Work Detail Editor
last_updated: 2026-04-18
parent_id: studio
sort_order: 35
---

# Catalogue Work Detail Editor

Route:

- `/studio/catalogue-work-detail/`
- focused record selection uses `?detail=<detail_uid>`

This page edits canonical work detail source records from `assets/studio/data/catalogue/work_details.json` and writes changes through the local catalogue write service. It now supports both focused single-record edit and bulk edit mode on the same route.

## Current Scope

The first implementation covers:

- search by `detail_uid`
- open one work detail record
- open multiple work detail records by comma-delimited detail ids and same-work detail ranges
- edit `project_subfolder`
- edit `project_filename`
- edit `title`
- edit `status`
- bulk-edit those same fields across the selected detail records
- show read-only fields for ids, published date, and dimensions
- preview the scoped rebuild impact for the parent work
- run `Save + Rebuild` through the local catalogue service
- delete one work-detail source record in single-record mode

The rebuild remains work-scoped. Saving a detail and rebuilding regenerates the parent work outputs rather than introducing a separate detail-only planner.

## Bulk Mode

Bulk mode is entered by opening more than one detail from the search field.

Current bulk-selection rules:

- comma-delimited explicit `detail_uid` values are supported
- same-work detail ranges are supported as `00001-003-010`

Current bulk-edit behavior:

- untouched fields preserve per-record values
- an empty touched field clears that field across the selected details
- `Save + Rebuild` runs one scoped parent-work rebuild per affected parent work
- delete is disabled in bulk mode

## Save Boundary

Current save/rebuild flow:

1. page loads the derived detail-search lookup, not the full canonical detail map
2. opening a detail fetches one focused lookup record from `assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`
3. browser uses the lookup-provided record hash for stale-write protection
4. user edits the current detail form
5. `POST /catalogue/work-detail/save` sends the current `detail_uid`, the expected record hash, and the normalized detail patch
6. the local write server validates the full source set, writes `work_details.json`, refreshes derived lookup payloads, and returns the normalized saved record
7. the page reloads its focused detail lookup payload
8. `POST /catalogue/build-preview` reports the parent-work rebuild impact
9. `POST /catalogue/build-apply` rebuilds the parent work scope from canonical JSON

Bulk save flow:

1. page expands the requested detail selection in the browser
2. page loads focused lookup records for the selected details and tracks each record hash
3. `POST /catalogue/bulk-save` sends selected `detail_uid` values, expected hashes, and the touched field updates
4. the local write server validates the combined source write, writes `work_details.json` once, refreshes lookup payloads, and returns changed counts plus parent-work rebuild targets
5. `Save + Rebuild` then runs one scoped rebuild per affected parent work

Delete flow:

1. single-record mode requests `POST /catalogue/delete-preview`
2. if preview is clean, the page confirms and sends `POST /catalogue/delete-apply`
3. the server deletes the detail source record and the page returns to the parent work editor

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
