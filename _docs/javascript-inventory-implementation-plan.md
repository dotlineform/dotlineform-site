---
doc_id: javascript-inventory-implementation-plan
title: JavaScript Inventory Implementation Plan
added_date: 2026-05-21
last_updated: 2026-05-21
ui_status: in-progress
parent_id: studio-javascript-payload-inventory
sort_order: 7015
viewable: true
---
# JavaScript Inventory Implementation Plan

This document turns the scoring policy in [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory) and the current rows in [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) into implementation batches.
The target for normal browser JavaScript files is risk score 4.
`assets/docs-viewer/js/docs-viewer.js` is excluded from this plan because the shared Docs Viewer entry runtime is handled separately.

## Implementation Principles

Work by route family, not by strict inventory rank.
A single session should remove one coherent responsibility boundary or finish one family-level mitigation slice, then verify it and update the inventory.
Avoid many micro-slices that each require separate smoke testing and doc updates.
Also avoid oversized slices that touch unrelated route families and become hard to finish in one context window.

A good batch usually touches:

- one route shell plus one or two focused support modules, or
- one route-family pattern across sibling files, or
- one shared helper plus the routes that already use that helper

A batch is too small when it only moves a few local helpers without changing ownership.
A batch is too large when it changes more than one route family, requires multiple browser workflows to verify, or mixes public-route and Studio-only risk.

Each completed batch should update:

- the affected JavaScript files
- focused module smoke tests when behavior moved out of route boot
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) scores for changed files
- this implementation plan if the next batch order changes

## Current Batch Order

### Batch 1: Catalogue Editor Route Shells

**Status:** Guardrail phase completed on 2026-05-21; score-moving follow-through remains.
The shared route boot/readiness helper now owns required-element collection, config loading, save-mode projection, catalogue server probing, lookup-map loading, route busy/ready projection, and init-error copy fallback for the catalogue editor family.
The route shells still own entity-specific field rendering, selection contexts, validation, import, membership, and action handoff.
This batch should not be treated as closed for maintenance-score purposes until the score-moving slices in [JavaScript Maintenance Risk Mitigation](/docs/?scope=studio&doc=javascript-maintenance-risk-mitigation) move state construction and event binding out of the remaining score-6 and score-7 route shells.

**Primary files**

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- route-state and form helpers in the same catalogue family

**Why this batch comes first**

The catalogue editor routes are the largest remaining Studio-only route-shell risk after the recent tag/data-sharing extractions.
They share similar boot, lookup, route-state, dirty-state, form, and action handoff patterns, so one carefully scoped route-family slice can reduce repeated structural risk without touching public routes.

**Concrete tasks**

1. Extract shared editor boot/state assembly where the four editor shells still duplicate config loading, server probing, lookup loading, ref collection, and route-ready projection.
2. Keep entity-specific fields and section rendering in existing entity modules; do not flatten work/detail/series/moment differences into one abstract editor.
3. Add focused checks for the extracted boot/state helper using stubbed config, lookup, and server-availability inputs.
4. Rescore the four route shells and any affected route-state helpers.
5. Continue with route-local state factories and event binders where scores remain 6 or 7 after the shared guardrail extraction.

**Expected score movement**

The route shells should drop only after state construction, event binding, or another complete route-shell responsibility moves to a focused owner with direct checks.
The 2026-05-21 guardrail slice did not justify lowering scores by itself.
Most existing field, form, and section modules should stay at 4 or 5 unless their contracts change.

**Verification**

Focused helper/module smoke: `tests/smoke/catalogue_editor_route_boot_modules.py`.
The smoke imports the helper and the four refactored route shells, checks route ready/busy projection, and stubs config, lookup, and server-availability inputs.

### Batch 2: Catalogue Action Workflows

**Status:** Presentation-contract phase completed on 2026-05-21; action orchestration follow-through remains conditional.
The shared catalogue action workflow helper now owns save/build outcome normalization and preview blocker extraction for publication and delete flows.
The work, detail, series, and moment action modules still own entity-specific payload construction, local record updates, modal labels, and route handoff.
Focused module smoke coverage checks the shared save result contract, delete/publication preview blocker shaping, and imports of the four action modules.
This batch should be revisited only when a complete action responsibility such as service request/activity context construction or record mutation/reload follow-through can move to a focused owner with direct checks.

**Primary files**

- `assets/studio/js/catalogue-work-actions.js`
- `assets/studio/js/catalogue-work-detail-actions.js`
- `assets/studio/js/catalogue-series-actions.js`
- `assets/studio/js/catalogue-moment-actions.js`
- `assets/studio/js/catalogue-editor-service-client.js`
- `assets/studio/js/catalogue-editor-action-modals.js`
- `assets/studio/js/catalogue-editor-action-workflow.js`

**Why this batch is separate**

The action modules own save, delete, publication, build preview, import, hash, activity, and modal-confirmation behavior.
That is a different risk from route boot.
Trying to fix route shells and action workflows together would make verification broad and brittle.

**Concrete tasks**

1. Define a shared catalogue action result contract for preview, apply, failure, and activity metadata.
2. Move repeated confirmation/result shaping into a focused action-workflow helper only where at least two entity action modules use the same behavior.
3. Keep entity-specific payload construction in each entity's fields/actions owner when the data shape is genuinely different.
4. Add direct checks for save/delete/publication preview result shaping without full editor boot.

**Expected score movement**

`catalogue-work-actions.js` should drop from high risk once save/build/publication orchestration has clearer boundaries.
The detail/series/moment action modules should drop by 1 point if they share the same result contract without becoming harder to read.

**Verification**

Focused helper/module smoke: `tests/smoke/catalogue_editor_action_workflow_modules.py`.
Run representative catalogue editor smoke only for future workflow slices that change user-visible action behavior beyond this shared result contract.

### Batch 3: Tag Route Shells

**Status:** Completed on 2026-05-21.
Tag Aliases now has focused mutation-state projection and save/import workflow helpers for post-save state updates, patch fallback, and import/apply result shaping.
Tag Studio route-ready/busy detail projection now lives in a focused route-state helper, so save-mode and selected-work route state can be checked without full route boot.
Tag Registry and Series Tags were left to rescore follow-through because their recent render, workflow, import, and offline-session owners remain in place.

**Primary files**

- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/series-tags.js`
- focused tag render, state, save, workflow, and modal modules

**Why this batch matters**

Tag Registry and Series Tags already have recent focused owners and may primarily need rescore follow-through.
Tag Aliases and Tag Studio remain larger route shells with enough modal, validation, save-mode, and state coordination to attract future work.

**Concrete tasks**

1. For Tag Aliases, extract mutation-state projection and import/apply workflow if those responsibilities still live in the route shell rather than an explicit owner.
2. For Tag Studio, keep editor state, save controller, suggestions, render, and modal behavior separate; extract any remaining route-owned save-mode projection that is shared with existing helpers.
3. Keep Tag Registry and Series Tags changes limited to regression fixes or rescore updates unless new behavior has re-entered their route shells.
4. Add direct checks for state projection and fallback/manual-save transitions.

**Expected score movement**

Tag Aliases and Tag Studio should move from high risk toward medium risk.
Tag Registry, Data Sharing Prepare, and Series Tags may already be lower after their recent extractions and should be rescored before further work.

**Verification**

Focused helper/module smoke: `tests/smoke/tag_route_shell_modules.py`.
Existing overlap checks: `tests/smoke/tag_registry_modules.py` and `tests/smoke/tag_aliases_modal.py`.
Use broader browser smoke only for future slices that materially change modal behavior, route-ready behavior, or editor save interactions beyond these helper contracts.

### Batch 4: Large Modal Modules

**Status:** Completed on 2026-05-21.
Tag Aliases and Tag Registry now share a focused tag modal shell helper for open-modal detection, Escape/Tab focus lifecycle support, restore-focus handling, status projection, class composition, group-chip class projection, state attributes, and HTML escaping.
Family-specific rendering, modal state, validation, and route callbacks remain in the aliases and registry modal modules.
Docs Viewer transient confirm, text-input, choice, generic modal host, and focus-trap behavior now lives in a focused shell helper.
Docs Viewer metadata parent-picker matching, popup rendering, active-option navigation, selection, dismissal, and parent-id resolution now lives in a focused helper.
The remaining Docs Viewer management modal controller owns metadata modal lifecycle, import modal lifecycle, and settings modal lifecycle.

**Primary files**

- `assets/studio/js/tag-aliases-modals.js`
- `assets/studio/js/tag-registry-modals.js`
- `assets/studio/js/tag-modal-shell.js`
- `assets/docs-viewer/js/docs-viewer-management-modals.js`
- `assets/docs-viewer/js/docs-viewer-management-modal-shell.js`
- `assets/docs-viewer/js/docs-viewer-management-parent-picker.js`
- related small modal helpers where they share the same shell conventions

**Why this batch should follow route-shell work**

The large modal files are not automatically wrong: they are useful if they stay modal-focused.
They become risky when validation, workflow decisions, or service result shaping moves into the modal layer.
This batch should happen after route and workflow owners are clear enough to avoid splitting modal code in the wrong direction.

**Concrete tasks**

1. Split only modal families with independent state or validation rules, such as promotion/demotion/import families, not every dialog.
2. Keep the shared modal shell and focus lifecycle in the existing modal helper when it is genuinely reusable.
3. Move workflow or service decisions out of modal modules if found during review.
4. Add modal-focused smoke checks only for changed modal families.

**Expected score movement**

Large modal modules should drop by 1 to 2 points when family boundaries are explicit and workflow decisions stay outside modal rendering.
Small modal modules should remain at score 4.

**Verification**

Run the specific existing modal smoke script for the route family changed.
Avoid rerunning every modal smoke unless shared modal shell behavior changed.

### Batch 5: Docs Viewer Non-Entry Modules

**Status:** Completed on 2026-05-21.
Docs Viewer management action decision shaping now has a focused workflow helper for normalize-order choices, normalize-order payloads, descendant collection, non-viewable ancestor discovery, and make-viewable target resolution.
The management coordinator still owns lazy Docs Import and scope lifecycle boundaries, metadata modal payload collection, UI projection, and reload orchestration.
The action controller still owns command invocation, busy/status projection, modal invocation, write calls, and reload handoff.

**Primary files**

- `assets/docs-viewer/js/docs-html-import.js`
- `assets/docs-viewer/js/docs-viewer-management.js`
- `assets/docs-viewer/js/docs-viewer-management-actions.js`
- `assets/docs-viewer/js/docs-viewer-management-action-workflow.js`
- `assets/docs-viewer/js/docs-viewer-management-modals.js`
- `assets/docs-viewer/js/docs-viewer-scope-lifecycle.js`
- report/search/bookmark helpers that remain above score 4

**Scope boundary**

Do not include `assets/docs-viewer/js/docs-viewer.js` in this batch.
The shared entry runtime has separate feature-driven work around payload loading, index panel ownership, and management lazy boundaries.

**Concrete tasks**

1. Keep management-only work behind the dynamic management boundary.
2. Move command-specific write orchestration to action or workflow helpers when it gains state beyond a single action.
3. Keep Docs Import scope selection in the controller but preserve preview/write/result rendering boundaries.
4. Add focused checks for lazy management import behavior only when the lazy boundary changes.

**Expected score movement**

Docs Import and management support modules should move toward 4 or 5 as long as focused workflow/render/action owners remain stable.
The shared `docs-viewer.js` score is not part of this plan.

**Verification**

Focused helper/module smoke: `tests/smoke/docs_viewer_management_action_workflow_modules.py`.
Use Docs Viewer module smoke checks first.
Run `docs-viewer-smoke` only when route-level management, modal, import, or scope lifecycle behavior changes materially.

### Batch 6: Public Runtime And Search

**Status:** Completed on 2026-05-21.
Catalogue search now lazy-loads the opt-in performance instrumentation helper only when a query flag or local-storage setting enables it, leaving normal public search visits on the lighter JSON loader path.
Query rendering now computes normalized query tokens once per render, uses one reusable result collator, and reuses the sorted match set when the `more` control only expands the visible count.
`work.js` was left unchanged because the completed slice did not find a complete shared boundary to extract there.
`moment.js` stayed as a low-watch follow-through item and was handled in Batch 7.

**Primary files**

- `assets/js/catalogue-search.js`
- `assets/js/work.js`
- `assets/js/moment.js`
- `assets/js/public-catalogue-runtime.js`
- `assets/js/search/search-policy.js`
- `assets/js/search/search-performance.js`

**Why this batch is separate**

Public-route JavaScript has different performance exposure from Studio-only route code.
Even moderate-size modules can deserve attention when they run on public catalogue, work, or moment pages.

**Concrete tasks**

1. Review `catalogue-search.js` for boot-time data loading, input-time filtering/sorting, and lazy loading of search policy/performance helpers.
2. Keep public work/moment modules focused on page-local interaction; extract only if shared catalogue behavior is duplicated.
3. Avoid introducing Studio-only utilities into public runtime paths.
4. Add or update browser checks only for changed public workflows.

**Expected score movement**

`catalogue-search.js` should drop only after actual route-load or input-time cost is reduced, not just after helper movement.
`work.js` and `moment.js` should remain low watch items unless new public-page behavior lands there.

**Verification**

Use targeted public-route browser checks for search, work, or moment pages affected by the slice.
No Studio smoke run is needed for public-only changes.

### Batch 7: Low Watch Items And Opportunistic Cleanup

**Status:** Completed on 2026-05-21.
The public moment route now loads `public-catalogue-runtime.js` before `moment.js`, and `moment.js` consumes the shared public runtime for text coercion, baseurl trimming, positive-size normalization, payload fetches, moment payload URL construction, and generated image `src`/`srcset` assembly.
`public-catalogue-runtime.js` gained the matching `momentPayloadUrl` helper alongside the existing work and series payload URL helpers.
`work.js` remains a score-5 watch item because its current series navigation and keyboard navigation responsibilities are page-local and did not expose a clean shared boundary in this slice.

**Primary files**

Files scored 5 after the rescore, plus score-4 files touched as dependencies during higher-priority batches.

**Concrete tasks**

1. Do not schedule standalone work for score-5 files unless a nearby route-family batch already touches them.
2. When editing a score-5 support module, tighten explicit inputs and add direct tests if the behavior is shared.
3. Keep score-4 files at the floor unless new responsibilities are added.

**Expected score movement**

This batch is mostly opportunistic.
The goal is to prevent regression above 4 while higher-risk route families are reduced.

## Session Exit Criteria

A session should stop at a clean checkpoint when:

- one batch slice is implemented and verified, or
- the rescore shows that the next slice needs a different family owner, or
- verification reveals route behavior that needs product clarification

Before closing a session, update changed inventory rows and note any remaining files whose score could not be lowered because the next responsibility boundary is unclear.
