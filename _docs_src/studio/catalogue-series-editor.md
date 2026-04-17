---
doc_id: catalogue-series-editor
title: Catalogue Series Editor
last_updated: 2026-04-17
parent_id: studio
sort_order: 36
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
- edit core scalar metadata fields
- edit `sort_fields`
- edit `primary_work_id`
- list current member works
- cap visible member rows at 10 by default
- search current members by `work_id`
- add a work to the current series
- remove a work from the current series
- make the current series primary for a member work by moving it to the front of that work's `series_ids`
- preview the scoped rebuild impact for the current series
- run `Save + Rebuild` through the local catalogue service

## Membership Constraints

Locked constraints for this phase:

- each work's `series_ids` order is preserved exactly as edited
- membership save does not sort a work's series list
- the member list uses the same capped list pattern as the work-detail navigation surface
- long member lists stay navigable through member search rather than rendering every row by default

## Save Boundary

Current save/rebuild flow:

1. page loads derived series-search and work-search lookup payloads, not full canonical source maps
2. opening a series fetches one focused lookup record from `assets/studio/data/catalogue_lookup/series/<series_id>.json`
3. membership edits operate on affected work `series_ids` arrays in the browser, using lookup-provided work hashes for stale-write checks
4. `POST /catalogue/series/save` sends the current `series_id`, the expected series record hash, the normalized series patch, and only the changed work membership rows
5. the local write server validates the full source set, writes `series.json` and `works.json` atomically when needed, refreshes derived lookup payloads, and returns the normalized saved records
6. the page reloads its focused series lookup payload
7. `POST /catalogue/build-preview` reports the scoped rebuild impact for the series plus affected works
8. `POST /catalogue/build-apply` rebuilds the current series, affected works, aggregate indexes, and catalogue search from canonical JSON

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
