---
doc_id: catalogue-work-editor
title: Catalogue Work Editor
last_updated: 2026-04-17
parent_id: studio
sort_order: 34
---

# Catalogue Work Editor

Route:

- `/studio/catalogue-work/`
- focused record selection uses `?work=<work_id>`

This page is the first end-to-end catalogue metadata editor in Studio. It edits one canonical work source record from `assets/studio/data/catalogue/works.json` and writes changes through the local catalogue write service.

## Current Scope

The first implementation covers:

- search by `work_id`
- open one work record
- edit core scalar metadata fields
- edit ordered `series_ids`
- show generated read-only fields (`work_id`, `width_px`, `height_px`)
- list the current work's detail records grouped by `project_subfolder`
- cap visible detail rows at 10 per section
- provide per-work detail search by `detail_uid`
- link into the dedicated work detail editor
- validate basic field format before save
- save source JSON only
- preview the scoped rebuild impact for the current work
- run `Save + Rebuild` through the local catalogue service
- show saved-state feedback and rebuild-needed state after save

It does not yet:

- edit work details inline on the work page
- edit series records directly
- update prose or media files
- paginate detail/member lists

## Save Boundary

Current save/rebuild flow:

1. page loads `works.json`, `work_details.json`, and `series.json`
2. browser computes a record hash for stale-write protection
3. user edits form fields
4. `POST /catalogue/work/save` sends the current work id, the expected record hash, and the normalized record patch
5. the local write server validates the full source set, writes `works.json`, creates backups, and returns the normalized saved record
6. the page advances its baseline and marks runtime rebuild as still pending
7. `POST /catalogue/build-preview` reports the scoped rebuild impact for the saved work record
8. `POST /catalogue/build-apply` runs scoped JSON-source generation plus catalogue search rebuild when the user chooses `Save + Rebuild`

The current rebuild scope is intentionally narrow:

- the current work page/json
- affected series pages
- aggregate series/works/recent indexes
- catalogue search

## Detail Navigation Surface

The work editor now includes a detail navigation section below the main editor.

Locked constraints for this phase:

- grouping follows `project_subfolder`
- each section shows at most 10 rows by default
- the detail search box searches within the current work by `detail_uid`
- works with multiple detail sections render as multiple grouped lists
- this area is navigation into the detail editor, not inline editing

## Current Editable Fields

- `status`
- `published_date`
- `series_ids`
- `project_folder`
- `project_filename`
- `title`
- `year`
- `year_display`
- `medium_type`
- `medium_caption`
- `duration`
- `height_cm`
- `width_cm`
- `depth_cm`
- `storage_location`
- `work_prose_file`
- `notes`
- `provenance`
- `artist`

## Related References

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
