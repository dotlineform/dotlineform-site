---
doc_id: catalogue-work-file-editor
title: "Catalogue Work File Editor"
last_updated: 2026-04-22
parent_id: studio
sort_order: 130
---
# Catalogue Work File Editor

Route:

- `/studio/catalogue-work-file/`
- focused record selection uses `?file=<file_uid>`

This page edits one canonical work-file source record from `assets/studio/data/catalogue/work_files.json` and writes changes through the local catalogue write service.

## Current Scope

The first implementation covers:

- search for a work-file record by file id, filename, label, or work id
- open one work-file record from either the dashboard route or the work editor
- open the current search value either by pressing `Enter` in the search input or by using the `Open` button
- edit `filename`
- edit `label`
- edit `status`
- edit `published_date`
- show read-only ids
- preview the scoped rebuild impact for the parent work
- save with an optional `Update site now` path through the local catalogue service
- delete one source record and return to the parent work editor

## Save Boundary

Current action labels:

- `Save`
  writes work-file source JSON and can optionally also update the public catalogue immediately
- `Update site now`
  appears only when source has been saved but publication is still pending
- `Delete`
  removes the current work-file source record and returns to the parent work editor

Current save/rebuild flow:

1. opening a work-file record fetches one focused lookup record from `assets/studio/data/catalogue_lookup/work_files/<file_uid>.json`
2. browser uses the lookup-provided record hash for stale-write protection
3. user edits the current work-file form
4. `POST /catalogue/work-file/save` sends the current `file_uid`, the expected record hash, the normalized file patch, and optional `apply_build: true`
5. the local write server validates the full source set, writes `work_files.json`, refreshes derived lookup payloads, and returns the normalized saved record plus nested build status when requested
6. the page reloads its focused work-file lookup payload
7. `POST /catalogue/build-preview` reports the parent-work rebuild impact
8. `POST /catalogue/build-apply` remains available for explicit follow-up update actions

Delete flow:

1. `POST /catalogue/work-file/delete` sends `file_uid` and the expected record hash
2. the local write server validates the full source set after removal and writes `work_files.json`
3. the page returns to the parent work editor

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
