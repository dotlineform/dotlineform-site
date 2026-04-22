---
doc_id: catalogue-series-editor
title: "Catalogue Series Editor"
last_updated: 2026-04-22
parent_id: studio
sort_order: 120
---
# Catalogue Series Editor

Route:

- `/studio/catalogue-series/`
- focused record selection uses `?series=<series_id>`

This page edits one canonical series source record from `assets/studio/data/catalogue/series.json` and can also write affected work membership records in `assets/studio/data/catalogue/works.json`.

## Current Scope

The first implementation covers:

- search by series title with `series_id` shown in results
- open one series record
- open the current search value either by pressing `Enter` in the search input or by using the `Open` button
- edit core scalar metadata fields
- edit `sort_fields`
- edit `primary_work_id`
- list current member works
- cap visible member rows at 10 by default
- search current members by `work_id` when the list is truncated
- add a work to the current series
- remove a work from the current series
- make the current series primary for a member work by moving it to the front of that work's `series_ids`
- preview the scoped rebuild impact for the current series
- show series prose readiness, including the resolved primary-work prose path or the metadata dependency blocking it
- run a narrow `Import prose + rebuild` action when the configured series prose file is ready
- save with an optional `Update site now` path through the local catalogue service
- delete one series source record and remove its membership from affected works

Draft/publish rule:

- draft series may be saved without `primary_work_id`
- published series must have a valid `primary_work_id` that belongs to the series
- scoped rebuild is blocked until the series is publishable

## Membership Constraints

Locked constraints for this phase:

- each work's `series_ids` order is preserved exactly as edited
- membership save does not sort a work's series list
- the member list uses the same capped list pattern as the work-detail navigation surface
- long member lists stay navigable through member search rather than rendering every row by default
- the member search box sits below the section heading and is only shown when the member list is truncated
- the `work_id` link is the navigation affordance for opening a member work; row action buttons stay focused on membership changes

## Save Boundary

Current action labels:

- `Save`
  writes series source JSON and any changed work membership rows, and can optionally also update the public catalogue immediately
- `Update site now`
  appears only when source has been saved but publication is still pending
- `Delete`
  removes the current series source record and its membership from affected work records after preview/confirmation

Current save/rebuild flow:

1. page loads derived series-search and work-search lookup payloads, not full canonical source maps
2. opening a series fetches one focused lookup record from `assets/studio/data/catalogue_lookup/series/<series_id>.json`
3. membership edits operate on affected work `series_ids` arrays in the browser, using lookup-provided work hashes for stale-write checks
4. `POST /catalogue/series/save` sends the current `series_id`, the expected series record hash, the normalized series patch, only the changed work membership rows, and optional `apply_build: true`
5. the local write server validates the full source set, writes `series.json` and `works.json` atomically when needed, refreshes derived lookup payloads, and returns the normalized saved records plus nested build status when requested
6. the page reloads its focused series lookup payload
7. `POST /catalogue/build-preview` reports the scoped rebuild impact for the series plus affected works and now also carries series prose readiness
8. `POST /catalogue/build-apply` remains available for explicit follow-up update actions and `Import prose + rebuild`

Delete flow:

1. page requests `POST /catalogue/delete-preview`
2. preview reports affected member works and any validation blockers
3. if preview is clean, the page confirms and sends `POST /catalogue/delete-apply`
4. the server deletes the series source record and removes that `series_id` from affected work records in one atomic write bundle

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
