---
doc_id: site-request-catalogue-lookup-invalidation
title: "Catalogue Lookup Invalidation Request"
last_updated: 2026-04-22
parent_id: site-docs
sort_order: 130
---
# Catalogue Lookup Invalidation Request

Status:

- planned

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

## Task List

### Task 1. Define The Invalidation Registry

Status:

- planned

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

### Task 2. Map Lookup/Search Dependencies Into The Registry

Status:

- planned

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

Reason:

- incremental invalidation should be based on actual payload dependencies, not intuition alone
- fields that do not currently affect search may do so later, so dependency expansion should update the registry rather than rely on remembered prose rules

### Task 3. Define First-Phase Incremental Scope

Status:

- planned

Choose the first safe implementation slice.

Recommended first slice:

- single-record work saves only
- simple work fields first
- full fallback for everything else

Reason:

- this gives immediate wins for common edits such as `notes`, dimensions, and storage fields without widening risk too early

### Task 4. Add Scoped Lookup Writers

Status:

- planned

Extend the lookup build/write layer so it can write:

- one focused work record
- one focused search payload
- one focused series record

without requiring a full-corpus rewrite.

Reason:

- the invalidation model needs concrete writer targets, not just field classification

### Task 5. Route Work Save Through Invalidation Rules

Status:

- planned

Update `POST /catalogue/work/save` so it chooses:

- `single-record`
- `targeted-multi-record`
- `full`

from the changed work field set through the explicit registry rather than ad hoc endpoint logic.

Reason:

- work save is the clearest source of quick wins and the easiest place to validate the model

### Task 6. Add Invalidation Logging

Status:

- planned

Local logs should report:

- invalidation mode chosen
- changed field set
- targeted lookup artifacts when not using `full`

Reason:

- local operators need to understand why one save caused a narrow or broad refresh

### Task 7. Verify Representative Field Edits

Status:

- planned

Verify at least:

- `notes` edit on one work
- dimension change on one work
- `title` change on one work
- `series_ids` change on one work
- one bulk operation still using `full`

Reason:

- incremental invalidation is only useful if it is both narrower and still correct

### Task 8. Extend Or Freeze

Status:

- planned

After work-save invalidation is stable, decide whether to:

- extend incremental invalidation to detail/file/link/series saves
- or stop at the current win and keep the rest on `full`

Reason:

- the project should not pay for more invalidation complexity than the actual workflow needs

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
