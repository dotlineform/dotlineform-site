---
doc_id: javascript-maintenance-risk-mitigation
title: JavaScript Maintenance Risk Mitigation
added_date: 2026-05-21
last_updated: 2026-05-21
ui_status: in-progress
parent_id: studio-javascript-payload-inventory
sort_order: 7012
viewable: true
---
# JavaScript Maintenance Risk Mitigation

This document records the next course of action after the 2026-05-21 review of [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).
It sits between the policy and implementation-plan documents: the policy defines the scoring model, [Development Workflow](/docs/?scope=studio&doc=development-workflow) now carries durable maintenance-gate guidance, and this document tracks the current mitigation implementation queue.

The immediate priority is to reduce systemic maintenance risk before adding new interactive surface area to the largest route controllers.
The first script priority is the Docs Viewer entry runtime, especially the index panel boundary needed before future semantic or graph index work.

## Diagnosis

The maintenance score 2 cluster is a real risk cluster, not just a documentation artifact.
Maintenance-score-2 files are about one third of the browser JavaScript inventory, but they represent most of the browser JavaScript lines and most of the recent edit churn.

The recurring pattern is a post-refactor plateau:

- focused modules now exist for many domain, render, workflow, modal, and state responsibilities
- route/controller files still coordinate broad mutable `state` objects
- future changes can still drift back into those controllers because ownership rules are not yet enforced by helper infrastructure
- some files now look safer structurally than before, but remain costly to change because contracts are implicit and mostly route-boot driven

The next mitigation pass should therefore avoid broad "make files smaller" cleanup.
It should first install rules and helpers that keep future changes out of risky controllers, then use those helpers in the highest-priority script slices.

## Durable Guidance

The reusable JavaScript maintenance gate now lives in [Development Workflow](/docs/?scope=studio&doc=development-workflow).
Use that gate before changing browser JavaScript files with maintenance score 2, total risk score 6 or higher, or recent churn that suggests ownership drift.

[JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory) remains the scoring authority.
This document should not duplicate the durable rules; it records implementation-specific priorities, completed Docs Viewer slices, and the next concrete task definitions.

## Helper Infrastructure Status

The helper infrastructure from this mitigation pass is now in place or moved into durable workflow guidance.

### Inventory Guardrail

**Status:** Completed on 2026-05-21.

Create and use `scripts/checks/javascript_inventory_guardrail.py`.
It reads the source inventory table and reports:

- count of files by maintenance score
- total lines by maintenance score
- files where maintenance score 2 overlaps structural, performance, or architectural score 2
- recent file-touch count from `git log --since=90 days --name-only`
- top maintenance-risk files by combined line count and churn

The first version is report-only.
Do not fail checks until the output is stable enough to avoid blocking useful work.

Use:

```bash
./scripts/checks/javascript_inventory_guardrail.py
```

### Maintenance Gate Checklist

**Status:** Moved to [Development Workflow](/docs/?scope=studio&doc=development-workflow) on 2026-05-21.

Use the JavaScript maintenance gate in [Development Workflow](/docs/?scope=studio&doc=development-workflow) before changing maintenance-score-2 files, files with total risk score 6 or higher, or high-churn JavaScript route/controller files.

### Focused Module Smoke Pattern

**Status:** Pattern moved to [Development Workflow](/docs/?scope=studio&doc=development-workflow); Docs Viewer index-panel module and route smoke checks added.

Use the workflow pattern for new owners before running broader browser route smoke tests.

### Controller Contract Notes

**Status:** Moved to [Development Workflow](/docs/?scope=studio&doc=development-workflow) on 2026-05-21.

Use the workflow owner-note rule when touching score-6 or score-7 controllers.

## First Script Priority: Docs Viewer Entry Runtime

The first implementation priority is `assets/docs-viewer/js/docs-viewer.js`.
The Docs Viewer inventory already tracks it separately because it is the shared entry runtime and currently carries the highest browser JavaScript risk.

The unpublished design note `_docs/_tmp-index-space.md` gives the near-term product direction:

- the current binary sidebar state should become a tri-state index panel: `collapsed`, `normal`, and `expanded`
- the current tree remains the initial panel content and keeps its current document-navigation behavior
- expanded mode gives the panel the full content width and hides the document/search pane
- expanded mode is not "a bigger tree"; it is a generic index workspace that can host future tree, semantic, graph, or relationship surfaces
- mobile behavior should not change in the first slice
- existing persisted `expanded` values should migrate to `normal`, because today's value means "not collapsed"

This directly affects the risk mitigation work.
The index-panel requirement should not be implemented as more sidebar conditionals in `docs-viewer.js`.
It should create a focused panel/layout owner before the feature lands.

## Docs Viewer Refactor Steps

Implement the Docs Viewer priority in small slices.

### Slice 1: Index Panel State Owner

**Status:** Completed on 2026-05-21.

Create `assets/docs-viewer/js/docs-viewer-index-panel.js`.
The owner is about the panel/workspace, not the tree.

The module should own:

- valid panel states: `collapsed`, `normal`, `expanded`
- legacy persistence migration from binary sidebar state
- state transition order for the existing toggle control
- label/title text projection for collapse, restore, and expand actions
- data-attribute projection such as `data-index-panel-state`
- helpers that answer whether the document/search pane should be visible

`docs-viewer.js` should call this owner and apply the returned projection.
It should not retain separate ad hoc booleans for the same panel state.

### Slice 2: Entry Runtime Wiring

**Status:** Completed on 2026-05-21.

Replace the current sidebar state wiring in `docs-viewer.js` with the new panel owner.
Keep this slice limited to state, persistence, labels, and shell data attributes.

The tree renderer should remain in `docs-viewer-sidebar.js`.
Tree clicks should keep their current behavior in all three panel states.
No graph or semantic index code should be added in this slice.

### Slice 3: Layout CSS

**Status:** Completed on 2026-05-21.

Update the Docs Viewer CSS so the shell responds to the panel state:

- `collapsed`: current collapsed panel behavior
- `normal`: current non-collapsed sidebar behavior
- `expanded`: panel occupies the content area and the document/search pane is hidden

Keep the CSS state names aligned with the JavaScript projection.
Avoid naming that implies the tree itself is expanded.

### Slice 4: Focused Smoke Coverage

**Status:** Completed on 2026-05-21.

Add a browser smoke check for the panel owner and route wiring:

- initial state migration from legacy stored values
- toggle sequence through `collapsed`, `normal`, and `expanded`
- document/search pane hidden in expanded mode and restored outside it
- tree item click behavior unchanged
- mobile behavior unchanged for the first slice

Use `tests/smoke/docs_viewer_index_panel_modules.py` for the state owner and `tests/smoke/docs_viewer_index_panel_route.py` for the route wiring.
Tree item click behavior in expanded mode is covered by the route wiring smoke.

### Slice 5: Inventory And Follow-Through

**Status:** Partially completed on 2026-05-21.

After the Docs Viewer slice is implemented and verified:

- [x] update [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [x] update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [x] update this document for completed/pending task status
- [x] update generated Docs Viewer payloads through the normal docs workflow rather than by hand
- [x] add a focused tree-click behavior assertion for index-panel expanded mode
- [x] re-parent the durable risk-scoring and maintenance-gate guidance under [Development Workflow](/docs/?scope=studio&doc=development-workflow), editing it from current implementation planning into stable workflow guidance

The target is not necessarily to move `docs-viewer.js` directly to score 4 in one slice.
The target is to prevent the next index/graph feature from increasing shared entry-runtime risk.

## Next Action

The next implementation step is to implement Task A1, the Catalogue work save outcome projection slice.

## Next Priorities After Docs Viewer

After the Docs Viewer index-panel boundary is in place, revisit the remaining score-6 and score-7 clusters by family:

1. Catalogue action workflows, especially work actions and cross-entity result contracts.
2. Tag route shells and modal controllers where event wiring, save/offline probing, and modal state still meet in broad route state.
3. Studio shared route helpers where high churn suggests an API contract needs direct checks before further extraction.
4. Public runtime only when a route-load or input-time cost is being changed, not for cosmetic splitting.

Each slice should have a focused owner, a small smoke check, and an inventory rescore.

Concrete task definitions are needed before starting those families.
Define them against the stable maintenance gate in [Development Workflow](/docs/?scope=studio&doc=development-workflow), so the task definitions stay aligned with the durable workflow guidance rather than this implementation note.

### Task A: Catalogue Action Workflow Contracts

**Status:** Defined; next implementation task is Task A1.

Candidate files:

- `assets/studio/js/catalogue-work-actions.js`
- `assets/studio/js/catalogue-series-actions.js`
- `assets/studio/js/catalogue-work-detail-actions.js`
- `assets/studio/js/catalogue-moment-actions.js`
- `assets/studio/js/catalogue-editor-action-workflow.js`

First contract: source-save plus optional public-update outcome projection.

Current state:

- `assets/studio/js/catalogue-editor-action-workflow.js` already owns raw save/build outcome normalization through `resolveCatalogueSaveBuildOutcome`.
- `assets/studio/js/catalogue-work-actions.js`, `assets/studio/js/catalogue-series-actions.js`, and `assets/studio/js/catalogue-work-detail-actions.js` still translate the same outcome kinds into route-local status/result messages.
- `assets/studio/js/catalogue-moment-actions.js` still has its own local save/build outcome shape and should not be the first adopter.

The focused owner remains `assets/studio/js/catalogue-editor-action-workflow.js`.
Extend it with an explicit save outcome presentation projection that accepts a normalized outcome plus route-provided labels/tokens and returns a small view model for status text, result text, and UI tone.

Task A1 implementation boundary:

- first adopter: `assets/studio/js/catalogue-work-actions.js` single-work save path
- move only the repeated save outcome-to-message decision into the shared owner
- keep record mutation, lookup refresh, pending build target updates, and editor state updates in `catalogue-work-actions.js`
- do not change bulk work saves, series saves, detail saves, publication, delete, build, or prose-import flows in A1
- do not rescore inventory rows until at least one route/action module no longer owns the save outcome presentation contract directly

Task A1 acceptance checks:

- extend `tests/smoke/catalogue_editor_action_workflow_modules.py` to cover the save outcome presentation projection for unchanged, saved, unpublished, applied, and partial public-update failure cases
- keep the smoke import checks for `catalogue-work-actions.js`, `catalogue-work-detail-actions.js`, `catalogue-series-actions.js`, and `catalogue-moment-actions.js`
- run the focused Catalogue action workflow module smoke after implementation
- run a syntax check for the touched JavaScript files if using a JS checker remains practical for this repo

Task A follow-up slices:

- A2: adopt the same projection in the work bulk-save branch if A1 keeps the work route behavior stable
- A3: adopt the projection in series and work-detail save flows
- A4: align moment save/build outcome normalization with `resolveCatalogueSaveBuildOutcome` after the shared projection is proven
- A5: revisit inventory scores for `catalogue-work-actions.js`, `catalogue-series-actions.js`, `catalogue-work-detail-actions.js`, and `catalogue-moment-actions.js` only after ownership and smoke coverage actually reduce future-change risk

### Task B: Catalogue Editor Route Shell Boundaries

**Status:** Pending definition after Task A identifies the shared action contract surface.

Candidate files:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-editor-route-boot.js`
- `assets/studio/js/catalogue-work-route-state.js`

Define this task only after the action workflow contract is clear.
The editor route shells should keep boot/config, required-element checks, event wiring, and handoff to focused owners.

The task definition should specify:

- which route-state projection or readiness transition is being extracted or pinned
- whether the shared owner is route-boot, route-state, readiness, selection, or action workflow
- which editor route is the representative first adopter
- which smoke or module test proves the route still loads and projects ready/busy state correctly
- what should not be reintroduced into the editor shell

### Task C: Tag Route Save And Modal Coordination

**Status:** Pending definition after Task A.

Candidate files:

- `assets/studio/js/tag-studio.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/tag-aliases-modals.js`
- `assets/studio/js/tag-registry-modals.js`
- `assets/studio/js/tag-modal-shell.js`
- `assets/studio/js/tag-studio-save-controller.js`

Define this task around the remaining coordination points where route state, save/offline probing, modal lifecycle, and user-facing fallback still meet.
Do not reopen already completed modal-shell, render, import-mode, or route-state extractions unless the new slice depends on them.

The task definition should specify:

- whether the owner is a save workflow, modal workflow, offline/session workflow, or route-state projection
- which route shell should become thinner first
- which modal controller behavior is shared and which remains route-specific
- what focused smoke covers unavailable-server fallback, patch rendering, and restored focus/status behavior
- whether `tag-studio.js`, `tag-registry.js`, or `tag-aliases.js` can be rescored after the slice

### Task D: Studio Shared Route Helper Contracts

**Status:** Pending definition after the route-specific catalogue and tag slices reveal repeated patterns.

Candidate files:

- `assets/studio/js/bulk-add-work.js`
- `assets/studio/js/data-sharing-review.js`
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/project-state.js`
- `assets/studio/js/studio-audits.js`
- `assets/studio/js/thumbnail-quality.js`
- `assets/studio/js/studio-route-state.js`
- `assets/studio/js/studio-transport.js`

This task should not start as a broad shared-runtime refactor.
Define it around one repeated route-helper contract that is already used or clearly needed by at least two route families.

The task definition should specify:

- the repeated contract being pinned, such as ready/busy projection, local-service transport results, list rendering state, or route error display
- the first two routes that prove the shared helper is real
- the smallest module smoke that can pin the helper without full route boot
- whether any route-level browser smoke is needed
- which high-churn shared helper or route rows can be rescored

### Task E: Public Runtime Performance-Only Follow-Up

**Status:** Watch item; define only when public route-load or input-time behavior is being changed.

Candidate files:

- `assets/js/catalogue-search.js`
- `assets/js/work.js`
- `assets/js/moment.js`
- `assets/js/public-catalogue-runtime.js`
- `assets/js/search/search-performance.js`

Do not start this task for cosmetic module splitting.
Public runtime work should be tied to a measurable page-load, search-input, list-expansion, or media-route cost.

The task definition should specify:

- the measured runtime cost or user-visible behavior being changed
- the performance or route smoke baseline before the change
- the focused owner for the changed behavior
- the public routes affected by the slice
- whether the inventory score changes because load/input work was reduced, not merely because code moved

### Task Definition Exit Criteria

Before implementing any task above, add a compact task section to the owning request or inventory doc with:

- target files and current inventory scores
- responsibility being moved, pinned, or deliberately left in place
- focused owner module
- acceptance checks and smoke-test file names
- inventory rows to revisit after verification
- docs and generated-payload follow-through

## Exit Criteria

The next maintenance-risk phase is successful when:

- the inventory guardrail can show maintenance-score-2 count, line share, churn, and overlap risk on demand
- new feature work has a checklist that prevents responsibility drift into maintenance-2 controllers
- `docs-viewer.js` no longer owns index panel state directly
- the index panel is a generic workspace boundary, with the tree as current content rather than the panel's identity
- future graph or semantic index work has an obvious lazy-loaded owner outside the entry runtime
- inventory scores are updated only after behavior, ownership, or testability actually improves
