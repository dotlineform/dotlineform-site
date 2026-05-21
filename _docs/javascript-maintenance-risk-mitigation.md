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
It sits between the policy and implementation-plan documents: the policy defines the scoring model, the implementation plan tracks completed batches, and this document defines the next mitigation rules and helper infrastructure.

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

## Operating Rules

Use these rules before starting another JavaScript risk-reduction batch.

1. Do not add new complete responsibilities to a file with maintenance score 2 unless the same slice creates or extends the focused owner for that responsibility.
2. Treat `assets/docs-viewer/js/docs-viewer.js` as the first script priority because upcoming index-panel work would otherwise add more layout and interaction state to the shared entry runtime.
3. Prefer explicit input/output helpers over helper functions that read or mutate the route's broad `state` object directly.
4. Keep route entry modules as orchestration shells: route boot, config handoff, event wiring, ready/busy projection, and calls into focused owners.
5. A score should drop only when future changes have a clearer destination, behavior has focused checks, or route/input-time work was actually reduced.
6. Score-5 files with only maintenance above the floor are watch items; improve them opportunistically when nearby behavior is already changing.
7. For new UI surface work, define the owning surface first. Do not let the current renderer or route shell become the owner by default.

## Helper Infrastructure First

Before the next feature/refactor batch, add small infrastructure that makes the rules repeatable.

### Inventory Guardrail

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

Add a short checklist to use before changing any file with maintenance score 2:

- What complete responsibility is being added or changed?
- Which module owns that responsibility after the change?
- Does the route shell keep only orchestration and handoff?
- Is there a focused module smoke check for behavior that moved out of route boot?
- Does the inventory score need updating after the slice?

This checklist can live in this document first.
If it proves useful, move it into a reusable script prompt or check profile later.

### Focused Module Smoke Pattern

Standardize the smoke-test pattern already used by existing module checks:

- serve the site root through a temporary local static server
- import the browser module directly in Playwright
- stub config, data, service, and DOM inputs
- assert helper contracts without full route boot
- import affected route shells only to catch syntax and dependency regressions

Use this pattern for new owners before running broader browser route smoke tests.

### Controller Contract Notes

When a score-6 or score-7 controller is touched, leave a short owner note in the relevant inventory or child doc:

- what remains in the controller
- what moved to a focused owner
- what future changes should use that owner
- what should not be reintroduced into the controller

This is intentionally lightweight.
The goal is to prevent the next related feature from rediscovering the same boundary.

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

Replace the current sidebar state wiring in `docs-viewer.js` with the new panel owner.
Keep this slice limited to state, persistence, labels, and shell data attributes.

The tree renderer should remain in `docs-viewer-sidebar.js`.
Tree clicks should keep their current behavior in all three panel states.
No graph or semantic index code should be added in this slice.

### Slice 3: Layout CSS

Update the Docs Viewer CSS so the shell responds to the panel state:

- `collapsed`: current collapsed panel behavior
- `normal`: current non-collapsed sidebar behavior
- `expanded`: panel occupies the content area and the document/search pane is hidden

Keep the CSS state names aligned with the JavaScript projection.
Avoid naming that implies the tree itself is expanded.

### Slice 4: Focused Smoke Coverage

Add a browser smoke check for the panel owner and route wiring:

- initial state migration from legacy stored values
- toggle sequence through `collapsed`, `normal`, and `expanded`
- document/search pane hidden in expanded mode and restored outside it
- tree item click behavior unchanged
- mobile behavior unchanged for the first slice

Use `tests/smoke/docs_viewer_index_panel_modules.py` for the state owner and `tests/smoke/docs_viewer_index_panel_route.py` for the route wiring.

### Slice 5: Inventory And Follow-Through

After the Docs Viewer slice is implemented and verified:

- update [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- update this document if the panel boundary changes
- update generated Docs Viewer payloads through the normal docs workflow rather than by hand
- re-parent the durable risk-scoring and maintenance-gate guidance under [Development Workflow](/docs/?scope=studio&doc=development-workflow), editing it from current implementation planning into stable workflow guidance

The target is not necessarily to move `docs-viewer.js` directly to score 4 in one slice.
The target is to prevent the next index/graph feature from increasing shared entry-runtime risk.

## Next Priorities After Docs Viewer

After the Docs Viewer index-panel boundary is in place, revisit the remaining score-6 and score-7 clusters by family:

1. Catalogue action workflows, especially work actions and cross-entity result contracts.
2. Tag route shells and modal controllers where event wiring, save/offline probing, and modal state still meet in broad route state.
3. Studio shared route helpers where high churn suggests an API contract needs direct checks before further extraction.
4. Public runtime only when a route-load or input-time cost is being changed, not for cosmetic splitting.

Each slice should have a focused owner, a small smoke check, and an inventory rescore.

## Exit Criteria

The next maintenance-risk phase is successful when:

- the inventory guardrail can show maintenance-score-2 count, line share, churn, and overlap risk on demand
- new feature work has a checklist that prevents responsibility drift into maintenance-2 controllers
- `docs-viewer.js` no longer owns index panel state directly
- the index panel is a generic workspace boundary, with the tree as current content rather than the panel's identity
- future graph or semantic index work has an obvious lazy-loaded owner outside the entry runtime
- inventory scores are updated only after behavior, ownership, or testability actually improves
