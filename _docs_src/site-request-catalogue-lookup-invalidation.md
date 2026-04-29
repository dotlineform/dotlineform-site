---
doc_id: site-request-catalogue-lookup-invalidation
title: Catalogue Lookup Invalidation Request
added_date: 2026-04-22
last_updated: 2026-04-22
parent_id: change-requests
sort_order: 30
---
# Catalogue Lookup Invalidation Request

Status:

- implemented

## Summary

This change request tracks follow-on work to stop the catalogue write server from refreshing the full derived lookup corpus after every successful catalogue write, while still preserving the current full-refresh path for complex or uncertain cases.

The preferred direction is not "incremental everywhere". It is:

- take the obvious field-level and record-level quick wins
- keep full lookup refresh as the safe fallback
- only widen incremental invalidation when dependency rules are explicit and verified

## Goal

Reduce unnecessary lookup refresh churn after simple catalogue saves without introducing stale derived lookup data.

The desired end state is:

- simple record edits refresh only the affected lookup outputs
- cross-record dependencies are handled by a small explicit invalidation model
- invalidation rules live in one explicit registry/config contract rather than only in prose docs
- complex operations still use full lookup refresh
- the chosen invalidation mode is visible in local logs

## Current Behavior

Current implementation facts at request start:

- successful canonical catalogue writes call `_refresh_lookup_payloads()` in the catalogue write server
- `_refresh_lookup_payloads()` runs `build_and_write_catalogue_lookup(...)`
- that builder re-derives the full lookup corpus under `assets/studio/data/catalogue_lookup/`
- this happens even for narrow edits such as one work field changing on one record
- Task 1 now adds the first explicit work-field invalidation registry in server code, but refresh behavior still defaults to full lookup refresh until later tasks route writes through that registry
- Task 2 now explicitly includes moments as part of the catalogue invalidation surface, even though moment artifacts are generated outside `assets/studio/data/catalogue_lookup/`

Current effect:

- logs can report broad lookup regeneration even when one record changed
- saves with obviously local consequences do not yet benefit from incremental write savings
- the implementation gets safety from simplicity, but gives up easy optimization wins

## Why This Needs A Separate Request

This is related to the catalogue write server, but it is a distinct problem from:

- docs incremental rebuild
- site page generation
- the `Save` plus `Update site now` UI wording change

It needs its own task list because it affects:

- lookup payload dependency rules
- write-server invalidation behavior
- logging and operator expectations
- verification strategy for stale derived data

## Initial Invalidation Model

The intended model should be tiered rather than binary.

Target invalidation classes:

- `single-record`
  rewrite only the focused derived record for the mutated source record family
- `targeted-multi-record`
  rewrite one focused record plus a small explicit dependency set such as search payloads or related series/work summaries
- `full`
  rebuild the full lookup corpus as the fallback when dependency scope is broad, mixed, or not yet implemented

This request does not assume a `no refresh` class. The first optimization pass should preserve current lookup contracts unless a later change explicitly narrows those payload contracts.

## Field Scoping Hypothesis

This section is only a starting hypothesis for Task 1. It is not yet the locked implementation contract.

The eventual source of truth should be an explicit invalidation registry in code or config, not this prose list alone.

### Work Save Fields Likely To Stay Below Full Refresh

Likely `single-record` candidates:

- `published_date`
- `project_folder`
- `project_filename`
- `year`
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

Reason:

- these fields primarily affect the focused work record payload
- they do not obviously change work search, series member summaries, or sibling record summaries

Likely `targeted-multi-record` candidates:

- `title`
- `year_display`
- `status`
- `series_ids`

Reason:

- `title`, `year_display`, and `status` appear in search and record-summary surfaces beyond the focused work payload
- `series_ids` changes membership and can affect old/new related series records as well as work search and the focused work record

### Operations Likely To Remain Full Refresh Initially

Likely `full` fallback candidates for the first implementation phase:

- `POST /catalogue/bulk-save`
- `POST /catalogue/delete-apply`
- `POST /catalogue/import-apply`
- `POST /catalogue/work/create`
- `POST /catalogue/work-detail/create`
- `POST /catalogue/work-file/create`
- `POST /catalogue/work-link/create`
- `POST /catalogue/series/create`
- saves where parent/child membership changes are not yet explicitly scoped
- saves where changed fields span both simple and complex dependency classes

Reason:

- these operations can affect multiple lookup families or introduce/remove ids
- the first incremental pass should keep complexity bounded

### Moment Dependency Notes

Moments are part of the public catalogue surface even though they do not live in Studio catalogue lookup payloads.

Current moment-derived artifact families:

- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`
- catalogue search entries built from `assets/data/moments_index.json`

Current dependency notes:

- `title`, `date`, and `date_display` affect the focused moment record, `moments_index.json`, and current catalogue search entries
- `status`, `published_date`, `image_alt`, and `source_image_file` currently affect only the focused moment record
- moments currently have no cross-record dependency set comparable to work/series membership
- likely future search expansion is moment full-text search, so the registry must remain explicit and updatable rather than relying on today's narrower search field set

## Task List

### Task 1. Define The Invalidation Registry

Status:

- implemented

Define one explicit invalidation registry that the write server can use as the canonical contract.

For each saveable record family, map changed fields to:

- `single-record`
- `targeted-multi-record`
- `full`

The registry should be explicit enough to survive future search/lookup expansion.

Start with:

- work saves
- detail saves
- file saves
- link saves
- series saves

Required output:

- one explicit field-to-invalidation registry
- one clear ownership point for that registry in code or config
- one explicit list of operations that still default to `full`

Implemented outcome:

- the first invalidation registry now lives in `scripts/studio/catalogue_write_server.py`
- it currently covers work-save fields only
- it also defines the initial full-refresh fallback operation set
- no write-routing behavior changed yet; later tasks will make the server use this registry to choose refresh scope

### Task 2. Map Lookup/Search Dependencies Into The Registry

Status:

- implemented

Document which source fields appear in which lookup or search payloads and use that mapping to populate the registry.

Minimum payload families:

- `work_search.json`
- `series_search.json`
- `work_detail_search.json`
- `works/<work_id>.json`
- `work_details/<detail_uid>.json`
- `work_files/<file_uid>.json`
- `work_links/<link_uid>.json`
- `series/<series_id>.json`
- `assets/moments/index/<moment_id>.json`
- `assets/data/moments_index.json`
- catalogue search moment entries built from `assets/data/moments_index.json`

Reason:

- incremental invalidation should be based on actual payload dependencies, not intuition alone
- fields that do not currently affect search may do so later, so dependency expansion should update the registry rather than rely on remembered prose rules
- moments are part of the catalogue surface and should not be left outside the dependency model just because their artifacts are generated outside Studio lookup JSON

Current Task 2 progress:

- the server now contains an initial explicit moment-field invalidation registry alongside the work-field registry
- current moment mapping treats `title`, `date`, and `date_display` as affecting the focused moment record, `moments_index.json`, and catalogue search
- current moment mapping treats `status`, `published_date`, `image_alt`, and `source_image_file` as affecting the focused moment record only

Implemented outcome:

- work save fields now map to actual downstream lookup dependencies, including title-driven summaries in related detail/file/link lookup records
- detail save fields now map to `work_details/<detail_uid>.json`, `work_detail_search.json`, and related work lookup records where detail sections are embedded
- work-file save fields now map to `work_files/<file_uid>.json` and related work lookup records where file summaries are embedded
- work-link save fields now map to `work_links/<link_uid>.json` and related work lookup records where link summaries are embedded
- series save fields now map to `series/<series_id>.json`, `series_search.json`, and related work lookup records where `series_summary` embeds the current series title
- moment fields now map to per-moment JSON, `assets/data/moments_index.json`, and current catalogue search entries
- unknown fields still collapse to `full`, preserving the current safe fallback

### Task 3. Define First-Phase Incremental Scope

Status:

- implemented

Choose the first safe implementation slice.

Recommended first slice:

- single-record work saves only
- simple work fields first
- simple moment writes immediately after work, because moments have no cross-record dependency graph
- full fallback for everything else

Reason:

- this gives immediate wins for common edits such as `notes`, dimensions, and storage fields without widening risk too early

Locked first-phase scope:

- route only `POST /catalogue/work/save` through incremental invalidation first
- allow `single-record` incremental behavior only for these work fields:
  - `published_date`
  - `project_folder`
  - `project_filename`
  - `year`
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
- keep `title`, `year_display`, `status`, and `series_ids` on `full` fallback for the first live pass even though they are already mapped in the registry
- keep detail, file, link, and series writes on `full` fallback for the first live pass
- keep moment routing deferred to the next pass after work-save incremental routing lands

Why this scope is locked:

- it captures the highest-confidence quick wins
- it avoids needing scoped writers for search, related series records, or embedded child summaries in the first implementation
- it keeps the first runtime verification slice small enough to trust

### Task 4. Add Scoped Lookup Writers

Status:

- implemented

Extend the lookup build/write layer so it can write:

- one focused work record
- one focused search payload
- one focused series record

without requiring a full-corpus rewrite.

Reason:

- the invalidation model needs concrete writer targets, not just field classification

Current Task 4 progress:

Implemented outcome:

- the lookup layer can now build and write one focused work lookup record without rewriting the full corpus
- it can also now build and write:
  - focused `work_search.json`
  - focused `series/<series_id>.json`
  - focused `work_details/<detail_uid>.json`
  - focused `work_files/<file_uid>.json`
  - focused `work_links/<link_uid>.json`
- full refresh remains available as the fallback path

### Task 5. Route Work Save Through Invalidation Rules

Status:

- implemented

Update `POST /catalogue/work/save` so it chooses:

- `single-record`
- `targeted-multi-record`
- `full`

from the changed work field set through the explicit registry rather than ad hoc endpoint logic.

Reason:

- work save is the clearest source of quick wins and the easiest place to validate the model

Current Task 5 progress:

Implemented outcome:

- `POST /catalogue/work/save` now routes through the work invalidation registry
- locked first-pass `single-record` work-field saves use focused `works/<work_id>.json` refresh
- `targeted-multi-record` work-field saves now use focused writers for:
  - `work_search.json`
  - related `series/<series_id>.json`
  - related `work_details/<detail_uid>.json`
  - related `work_files/<file_uid>.json`
  - related `work_links/<link_uid>.json`
- unknown or broader cases still fall back to `full`

### Task 6. Add Invalidation Logging

Status:

- implemented

Local logs should report:

- invalidation mode chosen
- changed field set
- targeted lookup artifacts when not using `full`

Reason:

- local operators need to understand why one save caused a narrow or broad refresh

Current Task 6 progress:

Implemented outcome:

- `catalogue_work_save` logs now include:
  - changed field set
  - chosen lookup refresh mode
  - targeted artifact list
- `catalogue_lookup_refresh` logs now include:
  - refresh mode
  - targeted artifact list
  - written count
- changed work-save responses now include a `lookup_refresh` object with mode, invalidation class, targeted artifacts, and written count

### Task 7. Verify Representative Field Edits

Status:

- implemented

Verify at least:

- `notes` edit on one work
- dimension change on one work
- `title` change on one work
- `series_ids` change on one work
- one bulk operation still using `full`

Reason:

- incremental invalidation is only useful if it is both narrower and still correct

Current Task 7 progress:

- verified live `notes` edit on work `00001`:
  - used `single-record`
  - rewrote only `works/00001.json`
  - left `work_search.json` unchanged
- verified live `width_cm` edit on work `00001`:
  - used `single-record`
  - rewrote only `works/00001.json`
  - left `work_search.json` and related series lookup unchanged
- verified live `title` edit on work `00160`:
  - used `targeted-multi-record`
  - rewrote the focused work lookup record, `work_search.json`, related series lookup record, related detail lookup records, and related file lookup records
- verified live `series_ids` edit on work `00160`:
  - used `targeted-multi-record`
  - rewrote the focused work lookup record, `work_search.json`, and old/new related series lookup records
- verified live work bulk save on `00001`:
  - still used the full refresh path
  - rewrote the focused work lookup record, unrelated work lookup records, `work_search.json`, and unrelated series lookup records

Implemented outcome:

- representative `single-record`, `targeted-multi-record`, and bulk `full` cases are now verified live
- source records used during the smoke tests were restored afterward

### Task 8. Extend Or Freeze

Status:

- implemented

After work-save invalidation is stable, decide whether to:

- extend incremental invalidation to detail/file/link/series saves
- or stop at the current win and keep the rest on `full`

Reason:

- the project should not pay for more invalidation complexity than the actual workflow needs

Implemented outcome:

- extended incremental invalidation to:
  - `POST /catalogue/work-detail/save`
  - `POST /catalogue/work-file/save`
  - `POST /catalogue/work-link/save`
  - `POST /catalogue/series/save`
- current targeted behavior now covers:
  - detail record plus `work_detail_search.json` plus parent work lookup
  - file record plus parent work lookup
  - link record plus parent work lookup
  - series record plus `series_search.json` plus related work lookups when series title changes
- parent/id move-style cases still stay on `full` for this pass:
  - work-file `work_id` change
  - work-link `work_id` change
  - series save requests that also update member work records
- detail moves remain effectively blocked by the `detail_uid` contract, so there is no separate incremental move path for details

Verification notes:

- verified live detail title save on `00001-001` used `targeted-multi-record`
- verified live file label save on `00008:nerve` used `targeted-multi-record`
- verified live link label save on `00457:bandcamp` used `targeted-multi-record`
- verified live series title save on `104` used `targeted-multi-record`
- verified live work-file `work_id` change still used `full`, then restored the original parent work id

### Task 9. Reassess Code Registry vs JSON Config

Status:

- implemented

Decide whether the invalidation registry should remain in code or move into JSON/config after the dependency model stabilizes.

Decision:

- keep the registry in code for the current implementation phase

Reason:

- the registry currently has one real consumer: the catalogue write server
- the dependency model is still evolving at the edges, especially around full-fallback cases
- code is easier to evolve safely while artifact targeting rules are still changing
- externalizing now would add schema and indirection without a clear second consumer

Revisit trigger:

- only reconsider JSON/config externalization if a second consumer appears, such as:
  - a validation or audit tool
  - a build/report surface
  - a Studio/debug UI surface
  - shared runtime logic outside the catalogue write server

## Completion Criteria

This request is complete when:

- changed fields are explicitly scoped by invalidation class in one canonical registry/config contract
- work-save invalidation no longer defaults to full refresh for obvious single-record edits
- full refresh remains available for complex cases
- logs make the chosen invalidation mode visible
- representative verification confirms no stale lookup outputs

## Related References

- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
