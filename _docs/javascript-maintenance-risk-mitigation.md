---
doc_id: javascript-maintenance-risk-mitigation
title: JavaScript Maintenance Risk Mitigation
added_date: 2026-05-21
last_updated: 2026-05-21
ui_status: done
parent_id: archive
sort_order: 87000
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
- `change-2026-05-21-pinned-catalogue-editor-route-state-projection`
- `change-2026-05-21-defined-score-moving-javascript-maintenance-slices`
- `change-2026-05-21-extracted-catalogue-editor-route-shell-state-and-event-owners`
- `change-2026-05-21-extracted-work-action-record-synchronization`
- `change-2026-05-21-added-shared-tag-route-save-session-helper`
- `change-2026-05-21-extracted-tag-registry-modal-workflow-owner`
- `change-2026-05-21-extracted-tag-studio-interaction-state-owner`
- `change-2026-05-21-extracted-tag-aliases-modal-workflow-owner`
- `change-2026-05-21-added-shared-operational-route-shell-helper`

Current stable follow-through:

- the JavaScript inventory guardrail is available at `scripts/checks/javascript_inventory_guardrail.py`
- the reusable JavaScript maintenance gate lives in [Development Workflow](/docs/?scope=studio&doc=development-workflow)
- the Docs Viewer index-panel state owner is in place at `assets/docs-viewer/js/docs-viewer-index-panel.js`
- focused Docs Viewer index-panel module and route smoke checks exist under `tests/smoke/`

## Next Action

Task A is implemented through the save, build, publication/prose-import, and bulk action presentation contract slices.
Task B is implemented through route-shell state factory and event binder slices for the Work, Work Detail, Series, and Moment editors, plus the conditional Work action record/store synchronization extraction.
Task C is implemented through shared Tag save-session, Registry modal workflow, Tag Studio interaction state, and Tag Aliases modal workflow slices.
The next maintenance-risk phase should start at Task D unless a regression exposes another repeated Catalogue or Tag route contract.

## Next Priorities After Docs Viewer

After the Docs Viewer index-panel boundary is in place, revisit the remaining score-6 and score-7 clusters by family:

1. Catalogue action workflows, especially work actions and cross-entity result contracts.
2. Tag route shells and modal controllers where event wiring, save/offline probing, and modal state still meet in broad route state.
3. Studio shared route helpers where high churn suggests an API contract needs direct checks before further extraction.
4. Public runtime only when a route-load or input-time cost is being changed, not for cosmetic splitting.

Each score-moving slice must have a focused owner, a small smoke check, and a rescore target before implementation starts.
Guardrail slices are allowed only when the same task defines the follow-on score-moving slice.

Concrete task definitions below are aligned with the stable maintenance gate in [Development Workflow](/docs/?scope=studio&doc=development-workflow).
The goal is measurable maintenance improvement, not waiting for future feature pressure.

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

**Status:** B1-B8 implemented on 2026-05-21.

Candidate files:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-editor-route-boot.js`
- `assets/studio/js/catalogue-work-route-state.js`

Current inventory scores:

- `assets/studio/js/catalogue-work-editor.js`: 7
- `assets/studio/js/catalogue-moment-editor.js`: 6
- `assets/studio/js/catalogue-series-editor.js`: 6
- `assets/studio/js/catalogue-work-detail-editor.js`: 6
- `assets/studio/js/catalogue-work-route-state.js`: 5
- `assets/studio/js/catalogue-editor-route-boot.js`: 4

The editor route shells should keep boot/config, required-element checks, event wiring, route-ready/busy handoff, and calls into focused owners.
They should not regain action result shaping, service endpoint naming, readiness item normalization, field normalization, dirty-state comparison, modal formatting, or embedded-item formatting now owned by focused modules.

#### B1: Route-State Projection Contract

Status:

- implemented

Owner:

- `assets/studio/js/catalogue-editor-route-boot.js`

Representative first adopter:

- `assets/studio/js/catalogue-work-editor.js`, because it is the remaining score-7 Catalogue editor route shell.

Scope:

- pin the shared mode, record-loaded, service, ready, and busy projection contract in the route-boot owner
- route-specific inputs should be explicit route-state options such as route id, bulk-id field, import-mode field, and busy-state fields
- keep record mutation, selection, URL updates, preview refresh, validation, and event wiring in the existing route-local owners
- leave `assets/studio/js/catalogue-work-route-state.js` as the Work-specific loaded/new/bulk state transition owner, but route-ready/busy detail should flow through the shared route-boot projection

Acceptance checks:

- `tests/smoke/catalogue_editor_route_boot_modules.py` covers shared route mode and record-loaded projections for single, bulk, import, and busy states
- `node --check` passes for `catalogue-editor-route-boot.js`, `catalogue-work-route-state.js`, and the four editor route shells
- focused route-boot smoke imports the four editor route shells without page errors
- inventory rows are revisited without lowering scores unless the route-shell ownership or focused checks materially improve

Implementation notes:

- `assets/studio/js/catalogue-editor-route-boot.js` now owns shared route-mode, record-loaded, service, ready, and busy detail projection helpers.
- `assets/studio/js/catalogue-work-detail-editor.js`, `assets/studio/js/catalogue-series-editor.js`, and `assets/studio/js/catalogue-moment-editor.js` now pass explicit route-state options instead of local mode/loaded projection helpers.
- `assets/studio/js/catalogue-work-route-state.js` still owns Work-specific loaded/new/bulk state transitions, but its ready/busy detail helpers delegate to the shared route-boot projection.

#### B2: Required-Element Boot Consistency

Status:

- implemented

Owner:

- `assets/studio/js/catalogue-editor-route-boot.js`

Representative first adopter:

- `assets/studio/js/catalogue-work-editor.js`

Scope:

- make the Work editor use the shared required-element collection helper instead of a route-local truthiness scan
- keep each route's element map in the route shell because DOM ownership and route-specific controls remain local
- avoid moving event wiring, state construction, or render-node ownership into route boot

Acceptance checks:

- `tests/smoke/catalogue_editor_route_boot_modules.py` continues to cover missing-required-element fallback and route-shell importability
- route files still fail closed when required DOM nodes are absent

Implementation notes:

- `assets/studio/js/catalogue-work-editor.js` now uses `collectRequiredElements` for its required DOM node map, aligning the score-7 Work route shell with the sibling editor shells.

#### B3: Stop And Rescore Decision

Status:

- implemented; no numeric score changes.

Scope:

- inspect the four editor route shells after B1-B2
- update `assets/studio/js` inventory notes for the route-state owner and any route shell touched by the slice
- lower scores only if future changes now have a clearer destination outside the editor shell and the focused smoke covers behavior that previously required route boot
- stop before extracting route-specific state transitions, selection/opening, or validation unless a repeated cross-route contract is visible

Decision:

- Inventory notes were updated for the four Catalogue editor route shells, `catalogue-work-route-state.js`, and `catalogue-editor-route-boot.js`.
- Scores were not lowered because the route shells still own broad route orchestration, event wiring, state construction, selection/opening handoff, and route-specific validation/update sequencing.
- This is a guardrail outcome, not a completed mitigation batch. Continue with B4 and B5 to move Work editor state construction and event binding out of the score-7 route shell.

#### B4: Work Editor State Factory

Status:

- implemented

Owner:

- new route-local owner `assets/studio/js/catalogue-work-editor-state.js`

Scope:

- move Work editor state construction, initial defaults, derived DOM section references, and route-state option construction out of `catalogue-work-editor.js`
- keep `catalogue-work-route-state.js` as the owner for loaded/new/bulk transitions
- keep field rendering, action calls, selection calls, and event wiring out of the new state factory

Expected score movement:

- `assets/studio/js/catalogue-work-editor.js`: target 7 -> 6 if the route shell no longer owns broad state construction and the new state factory has direct module smoke coverage
- no score reduction if the extracted module still reads global DOM directly or starts owning event/action behavior

Acceptance checks:

- add `tests/smoke/catalogue_work_editor_state_modules.py`
- prove the state factory returns required defaults, derived panel nodes, route-state options, and modal host wiring from explicit inputs
- `node --check` for Work editor and the new state module
- Work ready-state smoke with catalogue service blocked still reaches `data-studio-ready="true"`

Implementation notes:

- `assets/studio/js/catalogue-work-editor-state.js` now owns Work editor required-element collection, initial state construction, derived section panel nodes, media config/modal host wiring, and Work route-state option projection.
- `assets/studio/js/catalogue-work-editor.js` now consumes that state factory and keeps validation, route update coordination, rendering context construction, selection/action handoff, and calls into `catalogue-work-route-state.js`.

#### B5: Work Editor Event Binder

Status:

- implemented

Owner:

- new route-local owner `assets/studio/js/catalogue-work-editor-events.js`

Scope:

- move Work editor DOM event binding and async error wrappers out of the route shell
- keep handler implementations in existing owners: selection, action workflow, embedded-item modal owner, and section render/update helpers
- route shell should pass explicit context callbacks; the event binder should not mutate route state except through those callbacks

Expected score movement:

- `assets/studio/js/catalogue-work-editor.js`: target 6 -> 5 if event wiring leaves the shell and the remaining file is boot/config/handoff plus update-state coordination
- no score reduction if the binder becomes a second route controller with broad state logic

Acceptance checks:

- extend or add a focused module smoke to prove the binder attaches expected listeners with stubbed nodes and invokes injected callbacks
- Work ready-state smoke still passes with unavailable catalogue service
- one representative DOM-trigger smoke should activate a bound callback without using direct DOM activation for the behavior under test

Implementation notes:

- `assets/studio/js/catalogue-work-editor-events.js` now owns Work editor DOM listener attachment and async warning wrappers.
- Handler implementations remain in existing selection, embedded-item modal, action workflow, and route-state owners; the binder only invokes explicit callbacks.
- `tests/smoke/catalogue_work_editor_state_modules.py` covers the state factory and uses Playwright DOM actions to verify bound callback activation.

#### B6: Catalogue Sibling Route State Factories

Status:

- implemented

Owner:

- route-local state factory modules for Work Detail, Series, and Moment editors

Scope:

- apply the B4 state-factory pattern to the three remaining score-6 editor shells
- keep Moment import state in the Moment owner; do not force it into a generic Catalogue state model
- keep Series membership state in the Series membership owner

Expected score movement:

- `assets/studio/js/catalogue-work-detail-editor.js`: target 6 -> 5
- `assets/studio/js/catalogue-series-editor.js`: target 6 -> 5
- `assets/studio/js/catalogue-moment-editor.js`: target 6 -> 5
- no score reduction for any route that still owns both state construction and event/action orchestration after the slice

Acceptance checks:

- focused module smoke covers all three state factories
- route-boot smoke still imports all four editor shells
- representative route-ready smoke covers Work plus one sibling route

Implementation notes:

- `assets/studio/js/catalogue-work-detail-editor-state.js`, `assets/studio/js/catalogue-series-editor-state.js`, and `assets/studio/js/catalogue-moment-editor-state.js` now own required-element collection and initial state construction for their routes.
- The sibling route shells still own validation, route-specific loaded/new/bulk or import transitions, membership/import workflow handoff, and update coordination.

#### B7: Catalogue Sibling Event Binders

Status:

- implemented

Owner:

- route-local event binder modules for Work Detail, Series, and Moment editors

Scope:

- extract DOM event binding for Work Detail, Series, and Moment without moving domain behavior, validation, import, membership, or action orchestration into the binder
- each binder should accept explicit callback groups for selection, actions, membership/import, and render/update behavior

Expected score movement:

- `assets/studio/js/catalogue-work-detail-editor.js`, `assets/studio/js/catalogue-series-editor.js`, and `assets/studio/js/catalogue-moment-editor.js`: target 5 -> 4 only if the route shells become boot/config/handoff/update coordinators with focused binder tests
- if only one or two routes reach that shape, rescore only those routes

Acceptance checks:

- binder module smoke verifies attached listeners and callback invocation for each route
- route-ready smoke covers Work plus one sibling route
- inventory notes explain what remains in each route shell

Implementation notes:

- `assets/studio/js/catalogue-work-detail-editor-events.js`, `assets/studio/js/catalogue-series-editor-events.js`, and `assets/studio/js/catalogue-moment-editor-events.js` now own DOM listener attachment for the sibling Catalogue route shells.
- `tests/smoke/catalogue_sibling_editor_state_modules.py` covers the three state factories and three event binders with stubbed nodes and Playwright-triggered DOM events.
- Inventory rows were rescored to target 5 for the Work, Work Detail, Series, and Moment route shells. They did not move to score 4 because route-specific validation, loaded/new/bulk or import transitions, action context construction, and update coordination remain in the shells.

#### B8: Catalogue Action Workflow Revisit

Status:

- implemented

Owner:

- `assets/studio/js/catalogue-work-action-records.js`

Scope:

- revisited `assets/studio/js/catalogue-work-actions.js` after B4-B7 reduced route-shell noise
- moved Work action record projection and state-store synchronization for single save, bulk save, create, and publication responses into a focused owner
- left service request construction, action sequencing, confirmation flow, route refresh, delete navigation, and media refresh in the action coordinator
- did not reopen Task A presentation projections

Expected score movement:

- `assets/studio/js/catalogue-work-actions.js`: 7 -> 6

Acceptance checks:

- `tests/smoke/catalogue_editor_action_workflow_modules.py` covers Work action record projection, single mutation, and bulk mutation with stubbed state maps
- `node --check` passes for `catalogue-work-actions.js` and `catalogue-work-action-records.js`
- focused Catalogue action workflow module smoke imports the action modules without page errors

### Task C: Tag Route Save And Modal Coordination

**Status:** C1-C4 implemented on 2026-05-21.

Candidate files and current scores:

- `assets/studio/js/tag-studio.js`: 7
- `assets/studio/js/tag-registry.js`: 7
- `assets/studio/js/tag-aliases.js`: 6
- `assets/studio/js/tag-aliases-modals.js`: 6
- `assets/studio/js/tag-registry-modals.js`: 6
- `assets/studio/js/tag-modal-shell.js`: 4
- `assets/studio/js/tag-studio-save-controller.js`: 5

Do not treat previous modal-shell, render, import-mode, or route-state extractions as enough.
The score-moving target is route-shell responsibility reduction where save/offline probing, modal lifecycle, and user-facing fallback still meet.

#### C1: Shared Tag Save Session Contract

Status:

- implemented

Owner:

- `assets/studio/js/tag-route-save-session.js`

Scope:

- centralize tag save-mode probing, unavailable-server fallback state, patch/manual fallback result projection, restored-focus re-probing, and route-busy wrapping across Tag Studio, Registry, and Aliases
- route shells provide route-specific render/status callbacks; the save session owner returns explicit service, save-mode, import-availability, and patch-result view models
- keep Tag Studio offline-session staging in `tag-studio-save-controller.js`, because staged-series notification and baseline mutation remain route-specific

Expected score movement:

- `assets/studio/js/tag-studio.js`: 7 -> 6
- `assets/studio/js/tag-registry.js`: 7 -> 6
- `assets/studio/js/tag-aliases.js`: 6 -> 5

Acceptance checks:

- `tests/smoke/tag_route_shell_modules.py` covers unavailable-server fallback state, patch/manual result projection, focus/pageshow/visibility re-probe callbacks, route-busy projection, and route-shell importability without full route boot
- `node --check` passes for the shared save-session helper and adopting Tag route modules

#### C2: Tag Registry Modal Workflow Owner

Status:

- implemented

Owner:

- `assets/studio/js/tag-registry-modal-workflow.js`, separate from `tag-registry-modals.js` rendering/lifecycle and `tag-modal-shell.js` shared modal primitives

Scope:

- moved Registry create/edit/delete/demote modal state transitions, validation status projection, and apply-result handoff out of `tag-registry.js`
- keep modal HTML rendering in `tag-registry-modals.js`
- keep source mutation/service calls in existing mutation/service owners

Expected score movement:

- `assets/studio/js/tag-registry.js`: 6 -> 5
- `assets/studio/js/tag-registry-modals.js`: unchanged at 6 because it still owns modal lifecycle and event callback wiring, even though route workflow state moved out

Acceptance checks:

- `tests/smoke/tag_route_shell_modules.py` covers Registry modal workflow validation, demote selection state, edit apply-result handoff, and route-shell importability with stubbed state/callbacks
- `node --check` passes for `tag-registry.js` and `tag-registry-modal-workflow.js`

#### C3: Tag Studio Interaction State Owner

Status:

- implemented

Owner:

- `assets/studio/js/tag-studio-interactions.js`

Scope:

- moved selected work activation, tag entry add/remove/restore, weight cycling, metrics, and dirty-save enablement out of `tag-studio.js`
- kept rendering in `tag-studio-render.js`, save orchestration in `tag-studio-save-controller.js` plus the shared save-session owner, and route boot/event wiring in the route shell

Expected score movement:

- `assets/studio/js/tag-studio.js`: 6 -> 5

Acceptance checks:

- `tests/smoke/tag_route_shell_modules.py` covers selected-work changes, tag entry mutation, weight cycling, restore, metrics, and dirty-save enablement from explicit state inputs
- `tests/smoke/series_tag_editor_ready_state.py` verifies Tag Studio still loads and reaches the Studio ready state for a representative series

#### C4: Tag Alias Route Closeout

Status:

- implemented

Owner:

- `assets/studio/js/tag-aliases-modal-workflow.js`, separate from `tag-aliases-modals.js` rendering/lifecycle and the existing alias mutation/workflow owners

Scope:

- moved Tag Aliases create/edit, promote, and demote modal interaction state, validation projection, tag selection, and popup matching out of `tag-aliases.js`
- kept modal HTML rendering and event listener attachment in `tag-aliases-modals.js`
- kept import orchestration, delete confirmation, service calls, post-save list refresh, and route ready/busy handoff in the route shell and existing workflow/state owners

Expected score movement:

- `assets/studio/js/tag-aliases.js`: 5 -> 4

Acceptance checks:

- `tests/smoke/tag_route_shell_modules.py` covers Tag Aliases modal workflow create/edit validation, edit tag selection/removal, demote validation, demote tag selection, and promotion state with stubbed state/callbacks
- `tests/smoke/tag_aliases_ready_state.py` verifies the Tag Aliases route still loads and reaches the Studio ready state
- `node --check` passes for `tag-aliases.js` and `tag-aliases-modal-workflow.js`

### Task D: Studio Shared Route Helper Contracts

**Status:** D1-D4 implemented on 2026-05-21; Task E is the next score-moving slice.

Candidate files and current scores:

- `assets/studio/js/bulk-add-work.js`: 5
- `assets/studio/js/data-sharing-review.js`: 5
- `assets/studio/js/project-state.js`: 5
- `assets/studio/js/studio-audits.js`: 5
- `assets/studio/js/thumbnail-quality.js`: 5
- `assets/studio/js/studio-route-state.js`: shared helper
- `assets/studio/js/studio-transport.js`: shared helper

This task should not wait for new features.
The repeated pattern already exists: operational Studio routes duplicate route-state projection, required element collection, local-service transport status, result rendering, and run/apply button state.

#### D1: Operational Route Shell Helper

Status:

- implemented

Owner:

- `assets/studio/js/studio-operational-route.js`

First adopters:

- `assets/studio/js/bulk-add-work.js`
- `assets/studio/js/docs-broken-links.js` (later retired when Docs Broken Links moved into Docs Viewer reports)

Scope:

- provides explicit helper contracts for required element collection, ready/busy projection, service availability display, and run-button disabled state
- keeps route-specific validation, endpoint names, result rendering, and payload shaping in route-local modules

Expected score movement:

- `assets/studio/js/bulk-add-work.js`: 7 -> 6
- `assets/studio/js/docs-broken-links.js`: 6 -> 5 before the route was retired

Acceptance checks:

- `tests/smoke/studio_operational_route_modules.py` covers required-element collection, ready/busy projection, service availability display, run-button disabled projection, and first-adopter route imports
- `tests/smoke/operational_routes_ready_state.py` verified Bulk Add Work and Docs Broken Links reached the Studio ready state with local service probes blocked before Docs Broken Links moved into Docs Viewer reports

#### D2: Bulk Add Work Workflow Split

Status:

- implemented

Owner:

- `assets/studio/js/bulk-add-work-workflow.js`

Scope:

- move preview summary formatting, blocked-row rendering, result shaping, and apply/preview run-state projection out of `bulk-add-work.js`
- keep endpoint wrappers in transport/client owner and keep route shell as boot plus event handoff
- keep import endpoint calls, activity context construction, service probing, and DOM event wiring in `bulk-add-work.js`

Expected score movement:

- `assets/studio/js/bulk-add-work.js`: 6 -> 5

Acceptance checks:

- `tests/smoke/bulk_add_work_workflow_modules.py` covers preview summary rendering, blocked-row details, run-state view model, apply-blocked projection, and apply result/warning projection
- `tests/smoke/operational_routes_ready_state.py` verifies Bulk Add Work reaches the Studio ready state with local service probes blocked
- `node --check` passes for `bulk-add-work.js`, `bulk-add-work-workflow.js`, and `studio-operational-route.js`

#### D3: Data Sharing Review Apply Workflow Owner

Status:

- implemented

Owner:

- `assets/studio/js/data-sharing-review-workflow.js`

Scope:

- move scope/action normalization, apply-action menu state, selected-file/preview selection state, and result-button projection out of `data-sharing-review.js`
- keep rendering in `data-sharing-review-render.js` and modal confirmation in `data-sharing-review-modals.js`
- keep service request sequencing, preview result modal handoff, route-state projection, and route boot in `data-sharing-review.js`

Expected score movement:

- `assets/studio/js/data-sharing-review.js`: 6 -> 5

Acceptance checks:

- `tests/smoke/data_sharing_review_workflow_modules.py` covers action normalization, scope option projection, selected preview rows, control disabled state, result-button projection, and menu open/close state
- `node --check` passes for `data-sharing-review.js` and `data-sharing-review-workflow.js`

#### D4: Operational Audit Routes Closeout

Status:

- implemented

Owner:

- shared operational route helper from D1 plus route-local result projection modules where needed

Scope:

- apply the D1 helper to `project-state.js`, `studio-audits.js`, and `thumbnail-quality.js`
- extract result projection only when repeated list/table/result shaping remains mixed with route boot
- kept project-state summary rendering, audit result rendering, thumbnail payload rendering, and service request sequencing route-local because those flows are not repeated enough to justify a new projection owner in this slice

Expected score movement:

- `assets/studio/js/project-state.js`: 6 -> 5
- `assets/studio/js/studio-audits.js`: 6 -> 5
- `assets/studio/js/thumbnail-quality.js`: 6 -> 5
- route can move to 4 only if route boot, transport, and result projection are all separated and covered by focused checks

Acceptance checks:

- `tests/smoke/studio_operational_route_modules.py` imports all D1/D4 operational helper adopters and covers required-element collection, route-state projection, service-status rendering, and run-button disabled projection
- `tests/smoke/operational_routes_ready_state.py` verifies Bulk Add Work, Project State, Studio Audits, and Thumbnail Quality reach Studio ready state with local service probes blocked and primary action buttons disabled
- `node --check` passes for `project-state.js`, `studio-audits.js`, and `thumbnail-quality.js`

### Task E: Public Runtime Measurable Maintenance And Performance Follow-Up

**Status:** E1-E3 implemented on 2026-05-21.

Candidate files and current scores:

- `assets/js/catalogue-search.js`: 5
- `assets/js/work.js`: 4
- `assets/js/moment.js`: 4
- `assets/js/public-catalogue-runtime.js`: 4
- `assets/js/search/search-performance.js`: 4

Public runtime work must improve a measured route-load/input-time behavior or reduce maintenance risk in a user-visible runtime path.
Cosmetic file splitting is still out of scope.

#### E1: Catalogue Search Runtime Baseline And Hot-Path Split

Status:

- implemented

Owner:

- `assets/js/search/catalogue-search-runtime.js`

Scope:

- capture baseline metrics for initial load, first query, repeated query, result render count, and list expansion
- move query normalization/evaluation and result rendering hot-path decisions out of `catalogue-search.js` behind explicit inputs
- keep route DOM wiring and config/data loading in the route shell
- keep lazy policy/performance module loading, scoped index fetch, DOM event wiring, URL query resolution, and instrumentation recording in `catalogue-search.js`

Expected score movement:

- `assets/js/catalogue-search.js`: 6 -> 5
- target 6 -> 4 only if route shell becomes data-load/event-handoff plus explicit render owner, and measured input-time behavior is preserved or improved

Acceptance checks:

- `tests/smoke/catalogue_search_runtime_modules.py` covers entry normalization, query matching/order, render projection, cache reuse, no-result state, prompt state, and query metric projection without full route boot
- `tests/smoke/catalogue_search_performance.py` verifies the public `/catalogue/search/` route records scoped load and query metrics with `search-performance` instrumentation enabled
- `node --check` passes for `catalogue-search.js` and `search/catalogue-search-runtime.js`

#### E2: Public Work Runtime Projection Owner

Status:

- implemented

Owner:

- `assets/js/public-catalogue-runtime.js`

Scope:

- moved the current `work.js` projection surface: series work-id normalization, series title lookup, series-link visibility/target, back-link labeling/target, and prev/next navigation URL/counter projection
- kept DOM insertion, series-index loading, metadata refresh handoff, and keyboard navigation in `work.js`
- did not move metadata/detail/download projection because the current `work.js` no longer owns those decisions; the work layout owns that hydration path separately

Expected score movement:

- `assets/js/work.js`: 5 -> 4

Acceptance checks:

- `tests/smoke/public_work_runtime_modules.py` covers series id/title lookup, series-link projection, back-link projection, hidden/single-series fallbacks, and prev/next/counter projection
- `tests/smoke/public_work_route.py` verifies a representative public work page still renders primary title, back link, series link, series navigation, and prev/next targets
- `node --check` passes for `work.js` and `public-catalogue-runtime.js`

#### E3: Public Runtime Closeout

Status:

- implemented

Scope:

- compare `work.js`, `moment.js`, and `public-catalogue-runtime.js` after E1-E2
- if `moment.js` already remains at score 4 with coherent ownership, leave it alone
- update inventory only for files with measured runtime or focused-owner improvements
- comparison result: `work.js` reached score 4 after navigation projection moved to `public-catalogue-runtime.js`; `moment.js`, `public-catalogue-runtime.js`, and `search-performance.js` remain at score 4 without further code movement

Expected score movement:

- `assets/js/catalogue-search.js`: 6 -> 5 across Task E
- `assets/js/work.js`: 5 -> 4 across Task E
- no score change for `moment.js`, `public-catalogue-runtime.js`, or `search-performance.js`

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
