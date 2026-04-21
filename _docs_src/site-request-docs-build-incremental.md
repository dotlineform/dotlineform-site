---
doc_id: site-request-docs-build-incremental
title: "Docs Build Incremental Request"
last_updated: 2026-04-21
parent_id: site-docs
sort_order: 120
---
# Docs Build Incremental Request

Status:

- requested
- not yet implemented

## Summary

This change request tracks the docs-build work needed to stop local Jekyll and docs-viewer development from behaving as if the whole docs corpus changed when only a small number of source docs were edited.

It exists to keep the problem, the required task list, and the cleanup/stale-output concern in one place rather than letting them drift across conversational notes.

## Goal

Reduce unnecessary local docs rebuild churn while preserving correct docs-viewer output and safe cleanup behavior.

The desired end state is:

- docs rebuild actions can target the intended scope explicitly instead of always rebuilding both docs scopes
- `studio` and `library` remain separate docs corpora with separate rebuild targets
- the docs builder uses the same incremental-write behavior for every current docs scope
- unchanged generated docs payloads are not rewritten
- removed or unpublished docs do not leave stale generated JSON behind
- local entrypoints and docs reflect the same rebuild contract

## Why This Needs A Real Change Request

This is not only a small script tweak.

It affects:

- the docs builder write strategy
- local Jekyll watch behavior
- docs-management and Studio rebuild entrypoints
- generated docs index/search behavior
- cleanup semantics for removed or unpublished docs

The cleanup behavior is a real implementation concern, not just a warning note. If incremental writes are added without an explicit stale-output policy, the repo can quietly retain invalid generated docs payloads.

## Current Behaviour

Current implementation facts:

- `scripts/build_docs.rb --write` rebuilds the full selected docs scope and rewrites the full generated output set for that scope
- by default it selects both `studio` and `library` when `--scope` is omitted
- it deletes and recreates the scope `by-id/` output directory before writing payloads
- it always writes a fresh `generated_at` timestamp into the docs index
- `bin/dev-studio` runs the all-scope docs rebuild on startup
- the Studio `Rebuild docs` action also uses the all-scope rebuild path

Current effect:

- Jekyll sees a large change set in `assets/data/docs/scopes/...` even when only a few source docs changed
- local rebuild activity looks broader than the underlying source change
- no-op or near-no-op docs edits still trigger wide watcher churn

Important boundary:

- the problem is not that `studio` and `library` should be merged
- the two docs scopes should stay operationally separate
- the shared change is the rebuild mechanism, not the knowledge boundary

## Scope

Included:

- docs builder scope selection behavior
- docs builder write strategy for generated JSON payloads
- stale-output cleanup rules for removed or unpublished docs
- docs index metadata churn where it affects no-op writes
- local rebuild entrypoints that trigger docs rebuilds
- docs updates needed to describe the new behavior accurately

Excluded unless later promoted:

- a redesign of the docs-viewer runtime
- a redesign of docs search ranking or search record shape
- hosted deployment optimizations beyond the existing local workflow
- non-docs generated artifact behavior outside the docs pipeline

## End-To-End Task List

### Task 1. Define Scope-Rebuild Rules

Decide which local actions should rebuild which scope.

The intended model is:

- `studio` and `library` remain separate rebuild targets
- commands and local UI should make scope choice explicit
- all-scope rebuilds should be reserved for cases where both docs corpora are intentionally being refreshed

Minimum explicit command forms:

- `./scripts/build_docs.rb --scope studio --write`
- `./scripts/build_docs.rb --scope library --write`

Apply that rule to:

- `scripts/build_docs.rb`
- `bin/dev-studio`
- Studio docs rebuild endpoints
- any docs-management rebuild helpers

Reason:

- scope selection should stay clear to the operator and is the first avoidable source of unnecessary churn

### Task 2. Make Docs Payload Writes Incremental

Change the docs builder so it does not delete and recreate the entire generated scope output on every write.

This task should apply consistently to all current docs scopes that use the shared builder.

Required behavior:

- compare generated payloads against existing files
- write only changed files
- skip unchanged files cleanly
- preserve deterministic output formatting and ordering

Reason:

- Jekyll should only see the docs payloads that actually changed, regardless of which docs scope is being rebuilt

### Task 3. Define And Implement Stale-Output Cleanup

Add explicit cleanup behavior for generated docs payloads that should no longer exist.

Cases to handle:

- source doc deleted
- source doc changed to `published: false`
- `doc_id` changed
- scope-specific rebuild where a previously generated payload is now orphaned

Required outcome:

- stale generated JSON does not remain in `assets/data/docs/scopes/<scope>/by-id/`
- cleanup behavior is deliberate and verifiable, not an accidental side effect of full-directory deletion

Reason:

- this is the key safety concern introduced by incremental writes

### Task 4. Review Index-Metadata Churn

Decide whether the docs index should still force a write on no-op builds because of `generated_at`.

Options to evaluate:

- keep `generated_at` but write the index only when doc content or structure changed
- replace the current timestamp behavior with a content-version field
- keep the current field only when a real write occurs

Reason:

- index metadata currently guarantees at least one changed file even for no-op rebuilds

### Task 5. Align Local Rebuild Entry Points

Bring local tooling into line with the new rebuild contract.

Relevant surfaces:

- `bin/dev-studio`
- Studio `Rebuild docs`
- docs-management rebuild helpers
- any helper path that currently assumes full all-scope docs rewrites

Reason:

- the scripts and the entrypoints must not drift into different rebuild models

### Task 6. Align Search Follow-Through

Confirm when docs-search rebuilds are and are not required after docs rebuilds.

Questions to settle:

- should a docs rebuild endpoint optionally rebuild docs search for the same scope
- should `bin/dev-studio` continue to rebuild docs only on startup
- what is the intended contract when a new doc is added and should appear in inline docs search

Reason:

- docs-viewer data and docs-search data are related but not identical outputs

### Task 7. Update Docs And Operating Guidance

Update the relevant docs so the new behavior is visible and consistent.

Likely docs:

- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Site Docs](/docs/?scope=studio&doc=site-docs) if a broader site-docs note becomes useful
- `AGENTS.md` only if the repo workflow contract materially changes

Reason:

- local behavior should be documented where the rebuild workflow is already described

### Task 8. Verify And Close Out

Required verification:

- no-op docs rebuild writes nothing or only the minimum intended files
- single-doc and small-doc-set edits only rewrite the affected scope and affected payloads
- deleted or unpublished docs remove the corresponding generated payloads
- docs viewer still loads correctly for `studio` and `library`
- any intended docs-search follow-through still works

Close-out should also record:

- cleanup actually completed
- any redundant old rebuild code removed
- any remaining follow-on work or deferred decisions

## Risks And Dependencies

### Main Benefits

- less local Jekyll churn
- clearer relationship between source edits and generated docs changes
- safer long-term docs-build behavior once incremental writes are explicit rather than accidental

### Main Risks

- stale generated JSON if cleanup rules are weak
- partial alignment if the script changes but local rebuild entrypoints keep the old assumptions
- confusing search behavior if docs rebuild and docs-search rebuild responsibilities stay ambiguous

### Dependencies

- current docs-builder contract in [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- current docs-management rebuild helpers
- current local Jekyll/dev entrypoints

## Acceptance Criteria

This request is complete when:

- local docs rebuilds can run at the intended scope without unnecessary all-scope rebuilds
- `studio` and `library` remain separate rebuild targets with explicit commands or UI actions
- unchanged per-doc payloads are not rewritten
- removed or unpublished docs do not leave stale generated payloads behind
- index writes do not cause avoidable no-op churn
- local rebuild entrypoints match the same contract
- docs and operating guidance describe the implemented behavior accurately

## Open Decisions

- Should `bin/dev-studio` rebuild both docs scopes on startup, or only the scope most relevant to the local Studio workflow?
- Should the Studio `Rebuild docs` action stay all-scope, become current-scope only, or expose a choice?
- Should docs-search rebuild happen automatically for the same scope when docs content changes, or remain a separate explicit step?
- What should replace or constrain the current `generated_at` behavior so it does not force avoidable index writes?

## Open Issues

- Incremental writes require an explicit orphan/stale-file cleanup strategy before implementation is safe.
- Scope-specific rebuild rules must be aligned across scripts and local server endpoints, not changed in only one place.
- Shared incremental-write behavior must not blur the operational separation between the `studio` and `library` docs corpora.
- A no-op rebuild should be tested as a first-class verification case rather than assumed from code inspection.

## Related References

- [Site Docs](/docs/?scope=studio&doc=site-docs)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Architecture](/docs/?scope=studio&doc=architecture)
