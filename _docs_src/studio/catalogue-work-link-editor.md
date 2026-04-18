---
doc_id: catalogue-work-link-editor
title: Catalogue Work Link Editor
last_updated: 2026-04-18
parent_id: studio
sort_order: 38
---

# Catalogue Work Link Editor

Route:

- `/studio/catalogue-work-link/`
- focused record selection uses `?link=<link_uid>`

This page edits one canonical work-link source record from `assets/studio/data/catalogue/work_links.json` and writes changes through the local catalogue write service.

## Current Scope

The first implementation covers:

- open one work-link record from the work editor
- edit `url`
- edit `label`
- edit `status`
- edit `published_date`
- show read-only ids
- preview the scoped rebuild impact for the parent work
- run `Save + Rebuild` through the local catalogue service
- delete one source record and return to the parent work editor

## Save Boundary

Current save/rebuild flow:

1. opening a work-link record fetches one focused lookup record from `assets/studio/data/catalogue_lookup/work_links/<link_uid>.json`
2. browser uses the lookup-provided record hash for stale-write protection
3. user edits the current work-link form
4. `POST /catalogue/work-link/save` sends the current `link_uid`, the expected record hash, and the normalized link patch
5. the local write server validates the full source set, writes `work_links.json`, refreshes derived lookup payloads, and returns the normalized saved record
6. the page reloads its focused work-link lookup payload
7. `POST /catalogue/build-preview` reports the parent-work rebuild impact
8. `POST /catalogue/build-apply` rebuilds the parent work scope from canonical JSON

Delete flow:

1. `POST /catalogue/work-link/delete` sends `link_uid` and the expected record hash
2. the local write server validates the full source set after removal and writes `work_links.json`
3. the page returns to the parent work editor

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
