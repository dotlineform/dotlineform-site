---
doc_id: site-request-catalogue-delete-cleanup
title: Catalogue Delete Cleanup Request
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: change-requests
sort_order: 80
---
# Catalogue Delete Cleanup Request

Status:

- implemented

## Summary

This change request tracks the follow-up needed to make Studio deletes for works, work details, and series remove the same class of repo-owned public artifacts that moment delete now removes.

Moment delete now treats `Delete` as "delete the item from the repo-owned public surface": it removes the canonical source row, generated page/json artifacts, published thumbnails, repo-local staged media, aggregate public index entries, and the catalogue search record.

The older work, work-detail, and series delete paths previously followed the earlier source-record pattern. They removed canonical source rows and refreshed Studio lookup payloads, but did not clean all generated site artifacts and public search/index references.

## Goal

Make `POST /catalogue/delete-apply` mean "delete everything repo-owned for this item" across:

- works
- work details
- series

The implementation should preserve the current safety posture:

- preview before apply
- validation blockers before write
- record-hash conflict protection
- explicit write allowlists
- transaction-style backups for generated/index/media cleanup
- no remote media deletion
- no canonical source-image or prose deletion unless a future request explicitly adds it

## Previous Behavior

Before this request was implemented, `work`, `work_detail`, and `series` deletes in `scripts/studio/catalogue_write_server.py`:

- remove canonical catalogue source JSON records
- cascade work deletes to dependent detail/file/link source rows
- remove a deleted series id from affected work source records
- refresh Studio catalogue lookup payloads
- write a Catalogue Activity entry

The gap was:

- generated Jekyll stubs can remain
- generated per-record runtime JSON can remain
- published thumbnail assets can remain
- repo-local staged media under `var/catalogue/media/` can remain
- aggregate public index JSON can retain stale entries or stale relationship metadata
- catalogue search can retain stale records or stale related metadata until a later rebuild
- tag assignment rows or per-work overrides can retain stale references

## Implemented Behavior

`POST /catalogue/delete-preview` now reports generated cleanup for works, work details, and series in the same response shape used by moment delete.

`POST /catalogue/delete-apply` now removes or updates the repo-owned public surface for the deleted item in one transaction-style flow:

- writes the affected canonical source JSON files
- updates aggregate public indexes and affected per-record runtime JSON
- updates Studio-only companion data where relevant
- deletes generated stubs, runtime payloads, published thumbnails, and repo-local staged media that belong to the deleted item
- rebuilds catalogue search for work and series deletes
- refreshes Studio catalogue lookup payloads after successful writes
- restores backed-up touched files if generated cleanup or search rebuild fails

Work-detail delete updates the parent work runtime JSON and does not rebuild public catalogue search because work details are not first-class catalogue search records.

## Required Cleanup Scope

### Work Delete

A work delete should remove or update:

- canonical work source row in `assets/studio/data/catalogue/works.json`
- dependent work-detail source rows in `assets/studio/data/catalogue/work_details.json`
- dependent work-file source rows in `assets/studio/data/catalogue/work_files.json`
- dependent work-link source rows in `assets/studio/data/catalogue/work_links.json`
- `_works/<work_id>.md`
- `assets/works/index/<work_id>.json`
- `assets/works/img/<work_id>-thumb-*`
- repo-local staged work media under `var/catalogue/media/works/`
- dependent `_work_details/<detail_uid>.md` files
- dependent `assets/work_details/img/<detail_uid>-thumb-*`
- dependent repo-local staged detail media under `var/catalogue/media/work_details/`
- `assets/data/works_index.json`
- `assets/data/series_index.json`
- affected `assets/series/index/<series_id>.json` records
- `assets/data/recent_index.json`
- `assets/studio/data/work_storage_index.json`
- per-work tag overrides in `assets/studio/data/tag_assignments.json`
- `assets/data/search/catalogue/index.json`

Work delete should continue to block when the work is still used as `primary_work_id` by a series. The operator should reassign those series before deleting the work.

### Work-Detail Delete

A work-detail delete should remove or update:

- canonical detail source row in `assets/studio/data/catalogue/work_details.json`
- `_work_details/<detail_uid>.md`
- `assets/work_details/img/<detail_uid>-thumb-*`
- repo-local staged detail media under `var/catalogue/media/work_details/`
- parent `assets/works/index/<work_id>.json`
- `assets/data/works_index.json` if the parent work's lightweight detail/card metadata changes

Work details are not currently first-class catalogue search records, so this flow does not need to remove a detail search entry from public catalogue search. It may still need to rebuild catalogue search when parent work search metadata changes as a side effect.

### Series Delete

A series delete should remove or update:

- canonical series source row in `assets/studio/data/catalogue/series.json`
- affected work source rows in `assets/studio/data/catalogue/works.json`
- `_series/<series_id>.md`
- `assets/series/index/<series_id>.json`
- `assets/data/series_index.json`
- affected `assets/works/index/<work_id>.json` records
- `assets/data/works_index.json`
- `assets/data/recent_index.json`
- the deleted series row in `assets/studio/data/tag_assignments.json`
- work override rows under that deleted series assignment row
- `assets/data/search/catalogue/index.json`

Series does not currently own distinct media. Series thumbnails are work-derived, so series delete should not delete work thumbnail assets.

## Implementation Direction

Prefer shared cleanup helpers over three independent copies of the moment branch.

Suggested helper shape:

- collect existing repo-owned paths to delete
- collect public JSON payloads that must be updated
- collect source JSON payloads that must be updated
- return preview-safe relative path lists and counts
- validate delete paths against narrow allowlisted roots
- back up all touched files before apply
- restore touched files if generated cleanup or search rebuild fails

The helper should keep the delete contract explicit by item kind rather than trying to infer arbitrary paths from user input.

## Generated Data Strategy

For aggregate public indexes, prefer deterministic payload updates or existing generator helpers rather than ad hoc text edits.

The apply path should ensure these public surfaces are current before returning success:

- `assets/data/works_index.json`
- `assets/data/series_index.json`
- `assets/data/recent_index.json`
- affected `assets/works/index/<work_id>.json`
- affected `assets/series/index/<series_id>.json`
- `assets/studio/data/work_storage_index.json`
- `assets/studio/data/tag_assignments.json`
- `assets/data/search/catalogue/index.json`

Catalogue search should be rebuilt after work and series deletes. For work-detail deletes, rebuild search only if the parent work search payload can change; otherwise refresh the parent work runtime payload and public indexes.

## Non-Goals

Do not delete:

- canonical work prose under `_docs_src_catalogue/works/`
- canonical series prose under `_docs_src_catalogue/series/`
- canonical moment prose under `_docs_src_catalogue/moments/`
- canonical source images under the external projects source tree
- remote uploaded media or R2 objects
- deprecated external staging paths under `DOTLINEFORM_MEDIA_BASE_DIR`

Do not reintroduce legacy local media staging cleanup. Current Studio media staging is repo-local under `var/catalogue/media/`.

## Acceptance Checks

Codex-run checks should include:

- syntax check for `scripts/studio/catalogue_write_server.py`
- dry-run delete preview for one representative work, work detail, and series
- dry-run delete apply for the same representative records when safe fixtures exist
- confirm preview cleanup payloads list generated artifacts and repo-local media paths only
- confirm stale search/index references are absent after an apply in a disposable test case
- `./scripts/build_docs.rb --scope studio --write` after docs updates
- `./scripts/build_search.rb --scope studio --write` when docs search output should remain current
- Jekyll build to a separate destination when generated public artifacts or layouts are touched

Manual checks should include:

- open the affected Studio editor after delete and confirm the record no longer appears in search/open flows
- open relevant public routes or JSON payloads and confirm the deleted item no longer resolves through normal index/search paths
- verify related work/series pages still show correct membership after a series or work delete

## Benefits

- makes Studio delete semantics consistent across catalogue types
- prevents stale public pages, runtime JSON, thumbnails, local staged media, and search records from surviving a source delete
- preserves the current explicit local-only media boundary
- reduces the need for follow-up manual cleanup after deleting catalogue records

## Risks

- the apply path will touch more files than the current source-only delete flow
- aggregate public index updates must remain deterministic
- restoring safely after a mid-apply failure is more important because deletes include file removal
- deleting work details as part of a work delete can remove more generated files than the operator may expect unless preview is clear
- search rebuild failures should block or roll back the delete rather than leave the repo in a half-cleaned state
