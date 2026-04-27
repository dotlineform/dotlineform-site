---
doc_id: catalogue-work-detail-editor
title: "Catalogue Work Detail Editor"
added_date: 2026-04-22
last_updated: 2026-04-26
parent_id: user-guide
sort_order: 50
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
- open the current search value either by pressing `Enter` in the search input or by using the `Open` button
- edit `project_subfolder`
- edit `project_filename`
- edit `title`
- edit `status`
- bulk-edit those same fields across the selected detail records
- show read-only fields for ids, published date, and dimensions
- show detail media readiness, including the resolved expected source path and missing-state guidance
- show a compact current-record image preview at the top of the summary rail
- preview the scoped rebuild impact for the parent work
- save with an optional `Update site now` path through the local catalogue service
- when `Update site now` runs, stage the resolved detail source image under `var/catalogue/media/`, generate local srcset derivatives, and copy thumbnails into `assets/work_details/img/`
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
- `Save` can optionally run one scoped parent-work rebuild per affected parent work
- delete is disabled in bulk mode

## Save Boundary

Current action labels:

- `Save`
  writes detail source JSON and can optionally also update the parent work output immediately
- `Update site now`
  appears only when source has been saved but the parent work output is still pending
- `Delete`
  removes the current detail source record in single-record mode after preview/confirmation

Current save/rebuild flow:

1. page loads the derived detail-search lookup, not the full canonical detail map
2. opening a detail fetches one focused lookup record from `assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`
3. browser uses the lookup-provided record hash for stale-write protection
4. user edits the current detail form
5. `POST /catalogue/work-detail/save` sends the current `detail_uid`, the expected record hash, the normalized detail patch, and optional `apply_build: true`
6. the local write server validates the full source set, writes `work_details.json`, refreshes derived lookup payloads, and returns the normalized saved record plus nested build status when requested
7. the page reloads its focused detail lookup payload
8. `POST /catalogue/build-preview` reports the parent-work rebuild impact and the current detail media readiness
9. the current-record rail resolves a compact detail preview from the generated detail thumb assets when they are available
10. `POST /catalogue/build-apply` remains available for explicit follow-up update actions; it stages source media under `var/catalogue/media/`, generates local primary and thumbnail derivatives, copies thumbnails into `assets/work_details/img/`, and leaves primary derivatives staged for remote publishing

Bulk save flow:

1. page expands the requested detail selection in the browser
2. page loads focused lookup records for the selected details and tracks each record hash
3. `POST /catalogue/bulk-save` sends selected `detail_uid` values, expected hashes, touched field updates, and optional `apply_build: true`
4. the local write server validates the combined source write, writes `work_details.json` once, refreshes lookup payloads, and returns changed counts plus parent-work rebuild targets
5. when `apply_build` is true, the same save response also reports the nested site-update result; otherwise the page leaves `Update site now` available as a follow-up action

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
