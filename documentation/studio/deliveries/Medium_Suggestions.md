---
draft: false
doc_id: d-20261020-201901-6103f1
title: Medium Suggestions
added_date: "2026-10-20 20:19:01"
last_updated: "2026-10-20"
parent_id: d-20260428-000000-f5ff18
---
# Medium Suggestions

## Current And Next State

Implemented and reviewed on 2026-10-20; manual acceptance remains pending. Medium remains optional unrestricted text, with alphabetical case-insensitive substring suggestions after two characters. Current canonical records supply 61 values, adding 1,562 UTF-8 JSON bytes to the existing startup response. Restart Local Studio and force-reload the editor before normal-use review. [Catalogue Work Editor](../Catalogue_Work_Editor.md) owns authoring behavior; [Search List](../Search_List.md) owns the shared popup mode. This delivery is parented to [Planned Features](../Planned_Features.md).

## Requirements And Deliverables

- Show all matching saved Medium values in the existing scrollable popup after two query characters. Preserve exact suggestion text and keep unmatched free entry valid in single, New, bulk and batch creation modes.
- Click or Arrow navigation followed by Enter selects a suggestion. Tab retains typed text and moves focus; Escape closes suggestions without replacing text. Enter without an active suggestion leaves free text unchanged.
- Add the tiny distinct `medium_values` list to the existing Work-search startup response using canonical records already loaded by that operation. Return its replacement after Medium-affecting Work Save, create/batch create, bulk Save or delete using the supplied completed Work map; do not reread canonical files or update suggestions for unrelated definition/title/media changes.
- The browser prepares/sorts candidate matching values once per supplied list and filters locally. No per-keystroke request, new endpoint, generated index, persistent cache or dependency on Refresh Catalogue is introduced.
- Extend the existing Search List with an explicit free-entry mode while preserving the current default selection/reset behavior of existing pickers. Reuse shared search-field/popup presentation and actual disabled/control lifetimes.

## Process

Open the Work editor, type two or more characters into Medium, and choose a saved value or keep typing. Tab accepts free entry as the draft value. Save persists the draft through the existing owner; its completed response updates suggestions when Medium usage may have changed. Reloading the editor loads current saved values with its existing startup lookup.

## Delivery Steps

### MS-0 — Readiness

- [x] Confirm field/draft ownership, shared popup behavior, existing startup response and carried mutation records.

Record: ready. The browser owns matching, selection and draft feedback. Python only projects distinct saved values from already loaded records into existing responses. Credible blast radius is the Work field, optional popup mode and response data; no source schema, validation, publication or recovery changes are required. Existing pickers keep their default mode. Stop if this requires another source read, generated freshness boundary or free-text validation.

### MS-1 — Implementation And Focused Evidence

- [x] Implement source projection and bounded completion-response handoff.
- [x] Implement browser candidate preparation, field/popup integration and free-entry semantics.
- [x] Update durable docs and guardrails.
- [x] Complete the selected static/current-data checks.

Verification budget: explicit-path Python/JavaScript lint, Python syntax/import checks, whitespace review and one read-only invocation of production candidate preparation/matching over current canonical values. Expected cost is seconds with no server/browser startup, network or application writes; syntax may write ignored bytecode. Shared popup/default picker and mutation/late-completion behavior receive source review, with actual keyboard/pointer/focus/Save/delete/bulk/batch acceptance left to normal use. No tests, temporary regression scripts, fixtures or browser probes are authorized. Changed files are local-only; check the public runtime inventory before deciding whether projection is needed.

Record: complete. Python lint and compilation passed for `catalogue_lookup.py` and `catalogue_output_service.py`. JavaScript lint passed for `search-list.js`, both new `catalogue-work-medium` owners, editor state, form and editor; the field owner passed again after the scoped Tab-order review fix. A read-only production Work-search projection and browser matching invocation loaded 4,619 canonical Works and returned schema v3 with 61 values / 1,562 vocabulary bytes; `p` returned no matches, `pa` returned 36 and `PAP` returned paper values. Python response-owner imports and tracked/new-file whitespace checks passed. No tests, browser interaction, live mutations, canonical/generated/public writes, Build, Search, Refresh or Publish ran. No changed file is represented in the public runtime inventory, including the local-only Search List, so code projection is not required.

### MS-2 — Code Review

- [x] Review normal/empty/no-match, free entry and mutation-response paths.
- [x] Complete the mandatory Redundancy And Defensive Behavior Review, including reused popup, lookup and Save helpers.

Record: complete. Distinct post-evidence review traced startup lookup data, single/New/bulk/batch/delete response adoption, supplied completed maps, form input/draft feedback, shared popup default/free-entry branches and static/public ownership. It found that the shared clear button added an extra Tab stop; the Medium caller now keeps that clickable control outside its Tab order, with its lint repeated. Existing picker defaults are unchanged. Vocabulary projection performs one pass over already loaded records only at startup or after a Work creation/deletion/Medium change; typing and unrelated mutations perform no projection/read/request. Empty replacement arrays clear the last used value through the existing saved-response hook. Exact strings remain distinct, optional absence supplies no suggestion, and only derived query/candidate matching text is normalized. No schema/row audit, free-text validity requirement, source reread, stale generated input, endpoint, hash, persistent cache, repair, fallback or compatibility alias was added. JSON/response authority, safe option escaping, shared async revision/listener cleanup and actual disabled/blur/draft-replacement boundaries remain justified. New field rendering and pure candidate preparation are separate responsibilities; no speculative shared engine was introduced. No findings remain. Keyboard/pointer/blur/default-picker behavior, no-match/empty rendering and real Save/create/delete/bulk/batch replacement paths received source review only and remain manual acceptance.

### MS-3 — Closeout

- [x] Reconcile durable behavior, evidence, reload requirements and remaining manual scenarios.
- [ ] Record user manual acceptance.

Record: implementation closeout complete. Catalogue Work Editor, Search List and Development Checklist own lasting behavior and safeguards. Restart Local Studio and force-reload the editor, then review two-character matching, exact selection, one-Tab free entry, Escape, arbitrary unmatched values and saved vocabulary replacement in normal modes. Tests, browser automation and live mutation verification remain unrun; commit/push and publication are separate actions. Retain this delivery for normal-use acceptance and recent evidence; no separate concept/architecture documents were created.
