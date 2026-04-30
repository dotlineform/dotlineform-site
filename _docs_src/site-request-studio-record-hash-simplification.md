---
doc_id: site-request-studio-record-hash-simplification
title: Studio Record Hash Simplification Analysis
added_date: 2026-04-30
last_updated: 2026-04-30
parent_id: site-request-field-aware-build-scoping
sort_order: 6
---
# Studio Record Hash Simplification Analysis

Status:

- implemented

## Summary

This note captures the record-hash decision from the field-aware build scoping pre-analysis work.

Removing mutable metadata from Jekyll route stubs removes route-stub checksums from the public page path. The companion cleanup removed Studio `record_hash` data from lookup payloads and expected-hash checks from save requests.

The removed hashes were mostly optimistic concurrency tokens. In a multi-user editing environment, that can be useful: a save can cheaply reject stale writes without field-by-field conflict checks. In this local Studio workspace, the same protection is much less valuable because Studio is implicitly a local, one-user-at-a-time, service-backed editor.

The implemented direction is pragmatic:

- remove record hashes from broad list and lookup display payloads
- remove expected-hash enforcement from normal local save paths
- let the server apply requested changes against current source
- use simple local logic such as last-write-wins for stale-page and bulk cases
- keep validation, backups, and write allowlists as the real safety mechanisms

This should not replace hashes with another elaborate conflict-resolution system. The working assumption is that stale-tab, multi-editor, and concurrent-write cases are unlikely in normal use, and Studio is intentionally not designed as a multi-user editing environment.

## Former Purpose

`record_hash` was computed as a deterministic hash of a canonical source record. It was not a checksum of the lookup file and was not intended to describe public generated artifacts.

Former uses:

- focused work, detail, series, and moment edit payloads exposed a hash
- broad lookup/search payloads exposed hashes for convenience baselines
- save, publish, unpublish, and delete requests could include `expected_record_hash`
- the write server recomputed the current source record hash
- if the expected hash differed, the server returned `409 Conflict`

The visible UI message is a stale-page warning such as:

- source record changed since this page loaded
- reload before saving, deleting, or changing publication state

## Practical Value In Local Studio

In normal local use, a hash mismatch should be rare.

Realistic cases:

- the same record is open in two browser tabs, one tab saves, then the stale tab tries to save
- Codex or a script edits the source JSON while a Studio page is open
- the source JSON is edited manually while a Studio page is open
- a generated lookup payload is stale relative to canonical source JSON

These are valid stale-state cases, but they are not the common editing path. The current recovery is also blunt: reload the page and try again.

For the current Studio contract, the hash usually confirms a state that is already stable. It does not materially help ordinary create/edit/save flows.

## Current Cost

The cost is not mainly the hash computation. The cost is that hashes widen generated lookup churn and can create false conflicts.

Examples:

- `work_search.items[].record_hash` hashes the full work record even though the search row only needs display/open fields
- changing a work-only field can rewrite broad work-search lookup data solely because the row hash changed
- `series.<series_id>.member_works[].record_hash` hashes the full member work record
- a non-membership work edit can conflict with a series membership save even though the membership operation only intends to update `series_ids`

This undermines field-aware build scoping because broad display payloads change for reasons unrelated to their displayed fields.

## Implemented Contract

Studio uses local last-write-wins semantics for normal source saves.

The replacement for hashes should be pragmatic logic, not a new conflict framework. If the server receives a valid save request, it should apply that request to the current source state and return the resulting normalized record. Rare stale-page cases can be handled by the next save response, validation errors, backups, and Git review rather than by blocking the save before it happens.

The server:

- loads the current source record at request time
- applies the submitted patch or operation to that current record
- validates the resulting source set
- writes backups before mutation
- writes the updated source atomically
- returns the updated normalized record

The UI should:

- update its baseline from the save response
- reload focused data where needed for display
- show validation and write errors clearly
- not block saves solely because a stale hash token changed

For targeted operations, baseline checks should match the operation rather than the full source record. In the first simplification pass, even those operation-specific hashes can be omitted unless a real stale-write problem appears.

## Proposed Removals

Removed `record_hash` from broad display/read models:

- `work_search.items[]`
- `series_search.items[]`
- `series.<series_id>.member_works[]`
- any other list rows where the hash exists only as a convenience save baseline

Removed expected-hash enforcement from normal local write paths:

- single work save
- single work-detail save
- single series save
- single moment save
- bulk work save
- bulk work-detail save
- series membership save
- publish, unpublish, and save-published actions
- delete apply

After removal, request payloads should omit `expected_record_hash` and `expected_record_hashes`.

## Optional Diagnostics

If useful for debugging, the server can still return a record hash in focused read or save responses as diagnostic metadata. It should not be required for save acceptance.

Diagnostic hashes should not be present in broad generated lookup rows if they cause unrelated lookup rewrites.

## Acceptance Checks

- editing a work-only field does not rewrite broad work-search lookup rows solely because a hash changed
- editing a non-membership work field does not cause series member lookup rows to change solely because a hash changed
- single-record saves do not send `expected_record_hash`
- bulk saves do not send `expected_record_hashes`
- series membership saves apply against current source without full-record member hashes
- stale-tab saves use local last-write-wins behavior rather than `409 Conflict`
- validation failures, missing records, and write errors still block saves
- save responses still update the browser baseline from the server's normalized record

## Benefits

- Studio lookup payloads become less noisy and more field-aware
- save behavior matches the local one-user workspace contract
- broad generated lookup files stop changing for unrelated full-record hash reasons
- false conflicts are removed from membership and bulk workflows
- the system becomes easier to explain: validation and backups provide safety, not stale hash tokens

## Risks

- stale browser tabs can overwrite newer local edits
- manual source edits while Studio is open can be overwritten by a later Studio save
- removing hash checks may hide a class of accidental concurrent local edits

Mitigation:

- accept local last-write-wins as the explicit Studio contract
- keep source validation strict
- keep timestamped backups before writes
- ensure save responses reset the active browser baseline
- rely on Git diffs for review before committing
