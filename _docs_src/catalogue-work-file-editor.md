---
doc_id: catalogue-work-file-editor
title: "Catalogue Work File Editor"
added_date: 2026-04-22
last_updated: 2026-04-27
parent_id: user-guide
sort_order: 90
---
# Catalogue Work File Editor

Route:

- `/studio/catalogue-work-file/`
- focused record selection uses `?file=<file_uid>`

This page is retired.

Work files are now work-owned `downloads` metadata in `assets/studio/data/catalogue/works.json`.
The old local write endpoints for standalone work-file create/save/delete now return a retired-endpoint response instead of writing `work_files.json`.

Use the owning work record as the source boundary. A follow-up Studio UI pass will add file add/edit/delete modals to the work editor.

## Current Scope

Historical scope:

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

## Retired Save Boundary

Historical action labels:

- `Save`
  writes work-file source JSON and can optionally also update the public catalogue immediately
- `Update site now`
  appears only when source has been saved but publication is still pending
- `Delete`
  removes the current work-file source record and returns to the parent work editor

Historical save/rebuild flow:

1. opening a work-file record fetches one focused lookup record from `assets/studio/data/catalogue_lookup/work_files/<file_uid>.json`
2. browser uses the lookup-provided record hash for stale-write protection
3. user edits the current work-file form
4. `POST /catalogue/work-file/save` sends the current `file_uid`, the expected record hash, the normalized file patch, and optional `apply_build: true`
5. the local write server validates the full source set, writes `work_files.json`, refreshes derived lookup payloads, and returns the normalized saved record plus nested build status when requested
6. the page reloads its focused work-file lookup payload
7. `POST /catalogue/build-preview` reports the parent-work rebuild impact
8. `POST /catalogue/build-apply` remains available for explicit follow-up update actions

Historical delete flow:

1. `POST /catalogue/work-file/delete` sends `file_uid` and the expected record hash
2. the local write server validates the full source set after removal and writes `work_files.json`
3. the page returns to the parent work editor

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
