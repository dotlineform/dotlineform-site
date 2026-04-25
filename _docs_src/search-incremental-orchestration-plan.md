---
doc_id: search-incremental-orchestration-plan
title: "Incremental Search Orchestration Plan"
added_date: 2026-04-24
last_updated: 2026-04-25
parent_id: search
sort_order: 90
---
# Incremental Search Orchestration Plan

This document defines a staged plan for incremental search updates across docs-domain search and later heavier search sources such as body text, summaries, and bulk catalogue edits.

The core decision is that incremental search is primarily an orchestration concern. Search code should own record generation, normalization, schema shape, and version hashing. Server and watcher orchestration should own when a full rebuild is required, when a targeted update is safe, and which records are affected by a source change.

## Goals

- keep generated search artifacts correct during single-doc writes, bulk writes, and manual source edits
- avoid running one full search rebuild per source record during bulk operations
- preserve the current deterministic full-rebuild path as the correctness fallback
- define affected-record rules before docs search expands to body text or summaries
- make the first implementation useful without over-designing a general indexing service

## Non-Goals

- no new hosted search backend
- no browser-side write path for generated search artifacts
- no hidden-draft search surface in the first implementation
- no catalogue body/prose indexing in the first slice
- no replacement for the full `./scripts/build_search.rb --scope <scope> --write` command

## Current State

Docs-management writes currently run:

1. source write
2. same-scope docs payload rebuild
3. same-scope search rebuild

The live docs watcher uses the same broad pairing for manual source edits. This is correct and simple, but it becomes inefficient when many docs change in one operation.

The docs search builder reads the generated docs index, filters out rows where `viewable: false`, excludes `_archive`, and emits one search entry per viewable doc. This keeps search downstream of generated docs data rather than raw source files.

## Boundary Decision

Incremental search should be split across two layers:

- search layer:
  - build one search record from one generated docs-index row plus any required generated payload inputs
  - merge, remove, sort, and version a search artifact deterministically
  - provide a full rebuild command and a targeted update command or callable library surface
- orchestration layer:
  - know which source files were written
  - batch many source writes into one docs rebuild and one search update
  - decide whether changed records are safe for targeted update
  - fall back to a full rebuild when dependencies are ambiguous

This avoids making `build_search.rb` responsible for local write workflows, watcher behavior, or docs-management batching.

## Phase 1. Bulk-Orchestration Fix

Purpose:

Solve the urgent bulk-edit problem without introducing true incremental search yet.

Implementation shape:

- add server-side bulk operations where the UI or import flow needs to update many docs
- write all source files first, with one backup bundle for the operation
- run one same-scope docs rebuild after all writes
- run one same-scope search rebuild after the docs rebuild
- return a single operation summary with counts, changed ids, backup path, and rebuild steps

Candidate first uses:

- bulk make-viewable for selected Library docs
- bulk hide or show docs if that UI is added later
- bulk import finalization after reviewing staged Library docs

Benefits:

- removes repeated full rebuilds in bulk flows
- keeps the current proven full-rebuild correctness path
- keeps implementation small enough to ship before deeper search indexing work

Risks:

- still rebuilds the full search artifact once per bulk operation
- does not help manual edits detected one file at a time by the watcher
- requires the UI to call a bulk endpoint rather than loop over single-doc actions

Open decisions:

- resolved: bulk viewability should support both selected-doc and subtree operations
- resolved: parent selection should not always imply children; use explicit operation modes so `selected` affects only explicit ids, while `subtree` affects explicit ids plus descendants
- resolved: the server should expand subtree targets from canonical docs data, using a request shape such as explicit `doc_ids` plus `include_descendants: true`
- resolved: no-op means no source file content would change; no-op requests should write no files, create no backup, run no docs rebuild, run no search rebuild, and leave timestamps unchanged
- resolved: backup bundles should copy only source files that actually changed, while the manifest may record requested and skipped ids
- resolved: the first user-facing controls should keep one selected-doc command, but prompt when the action needs ancestor or descendant scope expansion

End-state viewability behavior:

- making a selected child viewable should detect every non-viewable ancestor in the chain, prompt that parent docs will also become viewable, and send the child plus those ancestors when confirmed
- making a selected parent, grandparent, or other ancestor viewable should prompt whether all docs under that selected doc should also become viewable
- if the user confirms the descendant prompt, the request should include the selected doc plus all descendants
- if the user declines the descendant prompt, the request should include only the selected doc
- cancelling either prompt should write nothing
- making any selected doc non-viewable should affect only that selected doc, without changing ancestors or descendants
- descendants under a non-viewable ancestor can look indeterminate in public/default mode because the hidden ancestor prevents discovery, but their stored `viewable` values remain explicit

Phase 1 can start with selected-doc `Make viewable` and later extend to a hide/non-viewable command if that UI is needed.

## Phase 2. Incremental Docs-Search Interface

Purpose:

Add a search-owned way to update only affected docs-domain search entries after the generated docs index has already been updated.

Implementation shape:

- keep `build_search.rb --scope <scope> --write` as the full rebuild command
- add targeted docs-mode flags to `build_search.rb`, using this first command shape:
  - `build_search.rb --scope <scope> --write --only-doc-ids id1,id2 --remove-missing`
- accept doc ids only for targeted updates; do not accept source paths in the first contract
- refuse targeted updates for `catalogue` until catalogue has its own dependency model
- load the existing generated search artifact
- load the generated docs index for the scope
- rebuild search entries for affected viewable docs
- remove affected ids that are missing, non-viewable, or `_archive`
- recompute header `version`, `generated_at_utc`, and `count`
- write only when the artifact content changes
- do not add a debug full-equivalence mode unless a real operational need appears
- report diagnostic counts for Codex/server use, including changed, removed, skipped, unchanged, and full-fallback counts

Search-owned responsibilities:

- field normalization
- `_archive` exclusion
- `viewable` filtering
- parent title lookup
- stable entry ordering
- search artifact version hashing

Orchestration-owned responsibilities:

- determining affected ids
- deciding full vs targeted update
- sequencing source write, docs rebuild, and search update

Benefits:

- gives docs-management and the watcher a cheaper update path
- keeps search schema logic centralized
- prepares for body/summary indexing by creating a narrower contract before the index gets heavier

Risks:

- patching a search artifact can hide bugs if affected-id calculation is wrong
- dependency rules must be explicit before this is used by default
- version and ordering must remain byte-stable compared with full rebuild output

Resolved decisions:

- targeted updates accept doc ids only
- targeted updates do not support source paths in the first contract
- no debug full-equivalence mode is required
- output should report full diagnostic counts for Codex/server use, not for routine human review
- targeted mode refuses catalogue scope until there is a catalogue-specific dependency model

Status: implemented for docs-domain scopes in `scripts/build_search.rb`.
Targeted mode currently supports `studio` and `library` by `doc_id`; `catalogue` still falls back to full rebuilds only.

### Manual checks needed:

 - run a real docs-management action that changes title, parent_id, or viewable, then confirm the response reports targeted search for the affected ids and inline docs search reflects the change without a full same-scope rebuild
 - confirm orchestration still uses full rebuild for catalogue until its dependency model is defined

## Phase 3. Affected-Record Orchestration

Purpose:

Make server and watcher orchestration smart enough to choose targeted search updates safely.

Affected-record rules for current docs search:

- source doc changed:
  - affected id is that doc's `doc_id`
- source doc deleted:
  - affected id is the deleted doc id
- `viewable` changed:
  - affected id is that doc id
- `title` changed:
  - affected id is that doc id
  - direct children are also affected because search entries include `parent_title`
- `parent_id` changed:
  - affected id is that doc id
  - old and new siblings are not affected unless future breadcrumbs or ordering metadata become searchable
- `doc_id` or filename changed:
  - treat as remove old id plus add new id
  - full fallback is acceptable until rename flows exist
- `_archive` changed:
  - remove or skip `_archive`
  - child docs are affected only if their `parent_title` changes

Server behavior:

- docs-management already knows the intended operation for create, update metadata, update viewability, move, archive, delete, import, and overwrite
- each write handler should return or pass an affected-search plan to the rebuild orchestrator
- bulk handlers should merge affected ids before one search update
- if an operation cannot describe affected ids confidently, run the full same-scope search rebuild

Watcher behavior:

- the watcher sees changed filenames rather than high-level operations
- targeted watcher updates must be based on a previous parsed filename-to-doc snapshot, not on deriving `doc_id` from filename
- the snapshot should be maintained per scope after successful watcher rebuilds and store, at minimum:
  - filename
  - `doc_id`
  - `title`
  - `parent_id`
  - `published`
  - `viewable`
- file added:
  - parse the new file
  - affected id is the new `doc_id`
- file content changed:
  - compare previous parsed row to the new parsed row
  - affected id is the new `doc_id`
  - if `doc_id` changed, affected ids are old `doc_id` plus new `doc_id`
  - if `title` changed, also include direct child doc ids because child entries include `parent_title`
  - if `parent_id` changed, the changed doc id is sufficient under the current search schema; old and new siblings are not affected
- file deleted:
  - use the previous snapshot row
  - affected id is the old `doc_id`
  - run targeted search with `--remove-missing`
- multiple changed files:
  - target the merged affected-id set only when the changed-file count is at or below the explicit threshold
  - above that threshold, run a full same-scope search rebuild
- parse failure, invalid docs tree, missing snapshot, or unknown state:
  - run a full same-scope search rebuild when possible
  - if the full rebuild fails, report the error and keep the previous snapshot

Benefits:

- keeps correctness decisions near the code that knows the write intent
- lets single-doc manual edits become cheaper over time
- creates clear fallback points for ambiguous changes

Risks:

- watcher state can lag source reality
- source edits outside docs-management can change front matter in ways the watcher cannot classify
- future search fields can add new dependencies that must be reflected here

Resolved decisions:

- docs-management server writes use targeted docs-search updates when the handler has explicit affected doc ids
- docs-management targeted calls always pass `--remove-missing`
- title-change child expansion happens in docs-management orchestration because child entries include `parent_title`
- watcher-targeted updates use a parsed previous snapshot rather than a filename equals `doc_id` assumption
- parent changes are safe to target by changed doc id under the current search schema
- filename equals `doc_id` is not a reliable operational rule, especially for imported Library docs that may need substantial post-import editing
- the initial watcher changed-file threshold is `5`; above that, watcher search falls back to a full same-scope rebuild
- missing parsed snapshots, parse failures, invalid docs trees, and unknown states fall back to full same-scope search rebuilds

Open decisions:

- whether the threshold should stay at `5` after more real Library import/edit sessions

Phase 3 can start after Phase 2 has a targeted update interface.

Status: server-side orchestration implemented for docs-management writes. Watcher orchestration is implemented for safe small source changes with full fallback for threshold overflow or ambiguous source state.

## Phase 4. Heavy-Index Readiness

Purpose:

Prepare the same orchestration model for search that includes body text, summaries, or other heavier generated content.

Likely future dependencies:

- docs body text from generated per-doc payloads
- Library summaries or LLM-generated summaries
- catalogue prose or generated work details
- tag labels and other shared registries

Design rules:

- every indexed field should declare its source artifact family
- every source artifact family should have a dependency rule
- shared dependency changes, such as tag label updates, should trigger full rebuild unless the affected set is cheap and explicit
- large bulk operations should batch writes before index updates
- full rebuild should remain the operational escape hatch

Benefits:

- avoids coupling heavier indexing work to the first bulk-viewability fix
- lets indexing scope expand without making every source save slow
- gives future summaries/body indexing a clear invalidation contract

Risks:

- source-dependency tracking can become more complex than the current project needs
- over-optimizing too early could make the pipeline harder to reason about
- partial updates across multiple artifact families increase stale-index risk

Open decisions:

- should source-dependency metadata live in search config, builder code, or docs?
- should body/summary indexing introduce per-record checksums?
- should generated search artifacts include build provenance for changed ids?
- should the site keep one combined search artifact per scope or split heavy text into sidecar payloads?

Phase 4 should wait until there is a concrete body or summary indexing requirement.

## Historical First Implementation Slice

The first implementation was Phase 1 plus a design stub for Phase 2. This section is retained as implementation history; Phase 2 and the server-side Phase 3 slice are now implemented.

Recommended slice:

1. add a docs-management bulk viewability endpoint
2. accept explicit `scope`, `doc_ids`, and `viewable`
3. validate every target before writing anything
4. create one backup bundle for changed docs
5. write only docs whose viewability actually changes
6. run one docs rebuild and one full same-scope search rebuild
7. return counts for requested, changed, skipped, and rebuilt
8. document that targeted search updates are still deferred

This gives immediate operational value while keeping search correctness simple.

## Manual Checks

For Phase 1:

- make two Library docs non-viewable
- run the bulk make-viewable endpoint
- confirm both source docs changed
- confirm one backup bundle was created
- confirm one docs rebuild and one search rebuild ran
- confirm both docs appear in the Library tree and inline search afterward

For later targeted search phases:

- compare targeted output against a full rebuild for the same changed ids
- test title changes that affect child `parent_title`
- test viewable false-to-true and true-to-false
- test deleted docs
- test changed docs with `_archive` as parent

## Close-Out Criteria Before Implementation

- open decisions for the selected phase are answered
- affected-record rules for that phase are written down
- fallback behavior is explicit
- dry-run behavior is defined if the operation writes source files
- docs-management and watcher responsibilities are separated from search-builder responsibilities
- validation covers source writes, generated docs data, generated search data, and browser behavior
