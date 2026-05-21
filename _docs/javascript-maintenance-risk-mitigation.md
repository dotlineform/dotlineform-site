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
This document should not duplicate the durable rules or completed task history; it records the current mitigation queue and the next concrete task definitions.

## Completed Work

Completed implementation history is recorded in `_docs_logs/`:

- `change-2026-05-21-added-javascript-maintenance-guardrails-and-docs-viewer-index-panel-boundary`
- `change-2026-05-21-added-javascript-maintenance-gate-workflow-guidance`
- `change-2026-05-21-shared-catalogue-save-outcome-presentation-projection`

Current stable follow-through:

- the JavaScript inventory guardrail is available at `scripts/checks/javascript_inventory_guardrail.py`
- the reusable JavaScript maintenance gate lives in [Development Workflow](/docs/?scope=studio&doc=development-workflow)
- the Docs Viewer index-panel state owner is in place at `assets/docs-viewer/js/docs-viewer-index-panel.js`
- focused Docs Viewer index-panel module and route smoke checks exist under `tests/smoke/`

## Next Action

Task A is implemented through the save, build, publication/prose-import, and bulk action presentation contract slices.
The next implementation step is to define Task B against the remaining Catalogue editor route shell responsibilities.

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

**Status:** A1-A8 implemented on 2026-05-21.

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

Implemented boundary:

- A1 moved the single-work save outcome presentation decision into `assets/studio/js/catalogue-editor-action-workflow.js`.
- A2 adopted the same projection for the work bulk-save branch.
- A3 adopted the projection in series and work-detail save flows, including the work-detail bulk-save branch.
- A4 aligned moment save/build outcome normalization with `resolveCatalogueSaveBuildOutcome` and the shared presentation projection.
- A5 revisited the inventory rows and updated owner notes without lowering numeric scores.
- A6 added shared action presentation projection for build/public-update success and failure result shaping.
- A7 adopted the shared action presentation projection for publication and prose-import result/status view models, while leaving preview, confirmation, focus restoration, and route-specific mutations in the route modules and existing modal owner.
- A8 added shared bulk pending-build-target projection and routed bulk save/build status/result view models through the shared action presentation owner.

Implemented acceptance checks:

- `tests/smoke/catalogue_editor_action_workflow_modules.py` covers save outcome projection for unchanged, saved, unpublished, applied, partial public-update failure, no-public-artifacts skip cases, generic action presentation projection, and pending build target projection.
- The smoke keeps import checks for `catalogue-work-actions.js`, `catalogue-work-detail-actions.js`, `catalogue-series-actions.js`, and `catalogue-moment-actions.js`.
- Touched JavaScript files passed `node --check`.
- The focused Catalogue action workflow module smoke passed after implementation.

Completed Task A slices:

- A1: single-work save path adopted the projection.
- A2: work bulk-save branch adopted the projection.
- A3: series and work-detail save flows adopted the projection.
- A4: moment save/build normalization was aligned with the shared outcome helper.
- A5: inventory notes were updated.
- A6: build/public-update result shaping adopted the shared action presentation projection.
- A7: publication and prose-import result/status view models adopted the shared action presentation projection; delete preview blockers and confirmations continue to use the existing shared blocker and modal helpers.
- A8: bulk save/build status/result view models and pending build target selection adopted shared action workflow projections.

Remaining route-local responsibilities after A8:

- action availability rules, validation, and dirty-state checks
- service request construction and activity context
- record mutation, lookup refresh, selected id ownership, and search-record updates
- route-specific preview refresh functions and DOM node ownership
- post-delete navigation

These remaining responsibilities are coherent route orchestration rather than cross-route action presentation contracts.
They should be revisited only when Task B defines the route-shell boundary or when a new repeated action contract appears.

### Task B: Catalogue Editor Route Shell Boundaries

**Status:** Pending definition after Task A completed the shared action workflow presentation contracts.

Candidate files:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-editor-route-boot.js`
- `assets/studio/js/catalogue-work-route-state.js`

Define this task only after the action workflow contracts are clear.
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
