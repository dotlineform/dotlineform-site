---
doc_id: catalogue-work-detail-editor
title: "Catalogue Work Detail Editor"
added_date: 2026-04-22
last_updated: 2026-04-29
parent_id: user-guide
sort_order: 50
---
# Catalogue Work Detail Editor

Route:

- `/studio/catalogue-work-detail/`
- focused record selection uses `?detail=<detail_uid>`
- parent-scoped draft create mode uses `?work=<work_id>&mode=new`

This page edits canonical work detail source records from `assets/studio/data/catalogue/work_details.json` and writes changes through the local catalogue write service. It now supports focused single-record edit, bulk edit, and parent-scoped draft create mode on the same route.

## Current Scope

The first implementation covers:

- search by `detail_uid`
- open one work detail record
- open multiple work detail records by comma-delimited detail ids and same-work detail ranges
- open the current search value either by pressing `Enter` in the search input or by using the `Open` button
- create a draft detail source record from the detail editor route when a parent work is supplied
- edit `project_subfolder`
- edit `project_filename`
- edit `title`
- show `status` with the Readonly Display treatment controlled by `Publish` / `Unpublish`
- bulk-edit those same fields across the selected detail records
- show read-only fields for ids, published date, and dimensions
- show detail media readiness, including the resolved expected source path and missing-state guidance
- refresh local detail image derivatives from the displayed source image path without changing source metadata
- show a compact current-record image preview at the top of the summary rail
- preview the public update impact for the parent work when the detail is published
- save source metadata, with published-detail saves updating the parent work output internally
- publish draft details through a dedicated `Publish` command
- unpublish public details through a dedicated `Unpublish` command
- delete one work-detail source record in single-record mode

The public update remains work-scoped. Saving a published detail updates the parent work outputs rather than introducing a separate detail-only planner.

Implementation note: the edit controller shares work-detail field definitions, id normalization, draft shaping, and save payload construction with the new-detail controller through `assets/studio/js/catalogue-work-detail-fields.js`.

## New Mode

New mode is entered with:

- `/studio/catalogue-work-detail/?work=<work_id>&mode=new`

In new mode:

- the parent work id is required in the URL
- the parent work is shown as locked read-only context
- the suggested next `detail_id` is prefilled when available
- `status` is visible and fixed to `draft` for create
- `project_subfolder`, `project_filename`, and `title` are editable
- publish, media refresh, and delete actions are disabled until the detail exists
- `Create` writes source JSON only through `POST /catalogue/work-detail/create`
- no public site update runs during create
- after create, the page opens the new detail in normal edit mode with `?detail=<detail_uid>`

## Bulk Mode

Bulk mode is entered by opening more than one detail from the search field.

Current bulk-selection rules:

- comma-delimited explicit `detail_uid` values are supported
- same-work detail ranges are supported as `00001-003-010`

Current bulk-edit behavior:

- untouched fields preserve per-record values
- an empty touched field clears that field across the selected details
- `Save` internally updates affected parent-work public output for selected details that are already published
- delete is disabled in bulk mode

## Save Boundary

Current action labels:

- `Save`
  writes detail source JSON; if the detail is already published, it also updates the parent work output internally
- `Publish`
  appears for saved draft details, requires the parent work to be published, and changes source status to `published` through the shared publication endpoint
- `Unpublish`
  appears for published details, ignores unsaved form edits after confirmation, changes source status back to `draft`, and cleans public detail output
- `Delete`
  removes the current detail source record in single-record mode after preview/confirmation

Current save/publication flow:

1. page loads the derived detail-search lookup, not the full canonical detail map
2. opening a detail fetches one focused lookup record from `assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`
3. browser uses the lookup-provided record hash for stale-write protection
4. user edits the current detail form
5. `POST /catalogue/work-detail/save` sends the current `detail_uid`, the expected record hash, the normalized detail patch, and `apply_build: true` only when the detail is already published
6. the local write server validates the full source set, writes `work_details.json`, refreshes derived lookup payloads, and returns the normalized saved record plus nested public-update status for published saves
7. the page reloads its focused detail lookup payload
8. `POST /catalogue/build-preview` reports the parent-work public update impact and the current detail media readiness for published details
9. the current-record rail resolves a compact detail preview from the generated detail thumb assets when they are available
10. `Publish` and `Unpublish` use `POST /catalogue/publication-preview` followed by `POST /catalogue/publication-apply`

The detail media readiness panel also exposes `Refresh media` when the configured source image exists. That action calls the same build endpoint with `media_only: true`, `force: true`, and the current `detail_uid`, so it refreshes thumbnails and staged primary variants from the displayed source path without saving metadata or rebuilding page/json/search outputs. The result message is `Thumbnails updated; primary variants staged for publishing.`

Bulk save flow:

1. page expands the requested detail selection in the browser
2. page loads focused lookup records for the selected details and tracks each record hash
3. `POST /catalogue/bulk-save` sends selected `detail_uid` values, expected hashes, touched field updates, and `apply_build: true` only when the selection includes published details
4. the local write server validates the combined source write, writes `work_details.json` once, refreshes lookup payloads, and returns changed counts plus parent-work rebuild targets
5. when `apply_build` is true, the same save response also reports the nested public-update result; draft-only bulk saves remain source-only

Delete flow:

1. single-record mode requests `POST /catalogue/delete-preview`
2. if preview is clean, the page confirms and sends `POST /catalogue/delete-apply`
3. the server deletes the detail source record, generated detail page/media artifacts, repo-local staged media, and the deleted detail from the parent work runtime JSON
4. the page returns to the parent work editor

## Current Editable Fields

- `project_subfolder`
- `project_filename`
- `title`

`status` is displayed in the form, but it is read-only. Use `Publish` and `Unpublish` to change publication state.

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
