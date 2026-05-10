---
doc_id: site-request-catalogue-js-runtime-consistency
title: Catalogue JavaScript Runtime Consistency Request
added_date: 2026-05-10
last_updated: "2026-05-10 22:59"
ui_status: draft
parent_id: site-request-js-config-structural-review
sort_order: 80
hidden: false
---
# Catalogue JavaScript Runtime Consistency Request

Status:

- request captured
- Slice A completed for Work Detail Editor
- Slice B first extraction completed for Work Detail selection/opening
- Slice B second extraction completed for Work Detail form rendering/synchronization
- Slice B third extraction completed for Work Detail summary/readiness/preview rendering
- Slice B fourth extraction completed for Work Detail action workflow sequencing
- Slice C boundary review completed for Series Editor
- Slice C1 implemented for Series membership editing
- Slice C2 implemented for Series action workflow sequencing
- Slice C3 implemented for Series selection/opening
- Slice C4 implemented for Series form and section rendering

## Implementation Progress

2026-05-10:

- Work Detail boundary review chose search, lookup, and selection as the first extraction because it matched the Work Editor route pattern and had a clear route-local ownership boundary.
- Added `assets/studio/js/catalogue-work-detail-selection.js` for detail query parsing, popup suggestions, single/bulk open flows, and initial route selection.
- Added `assets/studio/js/catalogue-work-detail-form.js` for form field rendering, readonly field rendering, field label refresh, field value synchronization, field availability, and validation message rendering.
- Kept `assets/studio/js/catalogue-work-detail-editor.js` responsible for route bootstrap, state assembly, validation, and cross-module coordination.
- Kept form input mutation and validation decisions in the route controller so save/build/publication contracts remain unchanged.
- Added `assets/studio/js/catalogue-work-detail-sections.js` for current-detail preview rendering, readiness rows, new/single/bulk summary rendering, and shared Work Detail selection-list formatting.
- Added `assets/studio/js/catalogue-work-detail-actions.js` for save/create/build/publication/media/delete workflow sequencing, status/result messaging, build preview refresh, publication controls, activity context, and service transport coordination.
- Kept route-owned validation, loaded-record replacement, and post-create opening behind explicit callbacks so the action helper does not take over route state ownership.
- Series Editor boundary review chose membership editing as the first useful extraction because it is the route's distinctive domain boundary and it currently feeds dirty-state comparison, validation, save deltas, rendered member rows, and saved lookup rebuilding.
- Proposed `assets/studio/js/catalogue-series-membership.js` as the route-local owner for member list state, member row rendering, add/remove/primary mutations, membership dirty checks, changed-work update shaping, and saved lookup membership shaping.
- Kept Series save/create/build/publication/delete/prose workflows in `assets/studio/js/catalogue-series-editor.js` for the next slice so the membership API can settle before extracting action sequencing.
- Added `assets/studio/js/catalogue-series-membership.js` for stored membership reads, current-member entry shaping, membership dirty checks, focused lookup membership shaping, changed-work update shaping, member row/list rendering, add/remove/make-primary mutations, and first-member `primary_work_id` autofill.
- Kept Series route bootstrap, query handling, mode transitions, validation orchestration, save/create/build/publication/delete/prose command sequencing, public build preview, and final status/result copy in `assets/studio/js/catalogue-series-editor.js`.
- `assets/studio/js/catalogue-series-editor.js` is still above the long-file review threshold after C1, so the next useful Series slice is action workflow extraction rather than stopping at the first split.
- Added `assets/studio/js/catalogue-series-actions.js` for Series save/create/build preview/build/publication/delete/prose import workflow sequencing, public update outcome handling, activity context shaping, service transport coordination, and save-result status copy.
- Kept Series route state transitions, initial route selection, field rendering, validation ownership, and membership mutation UI in `assets/studio/js/catalogue-series-editor.js`, with the action module using route callbacks for those responsibilities.
- `assets/studio/js/catalogue-series-editor.js` is now below the long-file review threshold after C2; the next useful decision is whether Series selection/opening is still noisy enough to justify Slice C3 before moving toward Moment Editor.
- Added `assets/studio/js/catalogue-series-selection.js` for Series title/id search matching, popup result rendering, search-input behavior, open-button behavior, popup-click behavior, focused-series opening, and initial route selection.
- Kept new-mode state construction in `assets/studio/js/catalogue-series-editor.js` and save/create sequencing in `assets/studio/js/catalogue-series-actions.js`, with the selection module calling route callbacks for those transitions.
- `?mode=new` now takes precedence during initial route selection and uses the optional `?series=<series_id>` value as the draft `series_id`, matching the C3 acceptance target.
- Slice C4 review found the remaining Series controller still mixed display concerns with route orchestration, specifically editable field rendering, readonly field rendering, field synchronization, field availability, validation message display, summary HTML, and readiness HTML.
- Added `assets/studio/js/catalogue-series-form.js` for Series field DOM construction, type-option refresh, field value reads/writes, readonly value refresh, mode-specific field availability, and validation message rendering.
- Added `assets/studio/js/catalogue-series-sections.js` for Series record summaries, new/edit summary rendering, runtime/build impact display updates, and prose readiness rendering.
- Kept `assets/studio/js/catalogue-series-fields.js` as the owner for field definitions, normalization, payload shaping, and validation, while `assets/studio/js/catalogue-series-editor.js` remains the route coordinator for lifecycle, state transitions, service reads, validation orchestration, membership coordination, and action/selection contexts.

## Purpose

This request continues the Catalogue-side cleanup after [JavaScript Payload And Runtime Cleanup Request](/docs/?scope=studio&doc=site-request-js-payload-runtime-cleanup) completed the planned Catalogue Work Editor slices.

The goal is to apply a consistent, concept-first JavaScript ownership approach across the remaining Catalogue Studio routes.

The immediate remaining scope is:

- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- adjacent Catalogue route code where the same boundary problem appears

## Position

Stay in Catalogue before switching to the shared Docs Viewer controller if near-term work remains Catalogue-heavy.

The Work Editor cleanup created useful local patterns:

- route entry owns lifecycle, state assembly, and cross-module coordination
- route-state helpers own mode transitions and route-ready attributes
- form helpers own field rendering and form synchronization
- section helpers own route-local display rendering
- action helpers own write/build/publication/prose/media/delete workflow sequencing
- selection helpers own search input, suggestions, route query selection, and selected-record opening
- service clients remain transport-only

Those patterns should be reused where they fit, not forced where the route shape is different.

The 1,000-line policy from the payload cleanup request is a review trigger, not a finish line.
It should prompt an ownership review, but the reason to extract code must be a real conceptual boundary.
Likewise, do not stop a route split only because the entry module drops below 1,000 lines if another clear boundary remains.

## Goals

- Make Catalogue editor route boundaries consistent where the workflows are genuinely similar.
- Prefer route-local modules over premature generic abstractions.
- Keep shared helpers only for behavior that is actually shared across route families.
- Keep service transport, route state, action workflows, form rendering, section rendering, and selection behavior visibly separate.
- Reduce maintenance risk before more Catalogue workflow policy accumulates in route controllers.
- Keep existing generated-data contracts and local service endpoint contracts stable unless a later slice explicitly scopes a behavior change.

## Non-Goals

- do not split files by arbitrary line count
- do not make all Catalogue editors share one generic base controller
- do not force Work Editor helper names onto routes that have different responsibilities
- do not change user workflows as part of extraction
- do not move public generated JSON schema cleanup into this request unless a route runtime boundary requires it
- do not switch to the Docs Viewer cleanup before the Catalogue route scope has a clear stopping point

## Current Evidence

Post Work Editor cleanup, the remaining Catalogue route controllers over the long-file review threshold are:

| File | Current disposition |
| --- | --- |
| `assets/studio/js/catalogue-work-detail-editor.js` | selection/opening, form rendering/synchronization, summary/readiness/preview, and action workflow sequencing extractions complete; below long-file review threshold |
| `assets/studio/js/catalogue-series-editor.js` | medium priority; series has fewer sections but owns membership, save/build/publication, and prose workflows |
| `assets/studio/js/catalogue-moment-editor.js` | medium priority; focus on import/prose/media/action workflow boundaries rather than line-count reduction |

`assets/studio/js/catalogue-work-editor.js`, `assets/studio/js/catalogue-work-actions.js`, and `assets/studio/js/catalogue-work-selection.js` are now below the review threshold, but the important outcome is the ownership split, not the number itself.

## Candidate Catalogue Boundaries

Use the Work Editor splits as reference patterns:

- route shell and bootstrap
- route state and loaded-mode transitions
- field/form rendering and field synchronization
- summary/readiness/section rendering
- action workflow sequencing
- search, lookup, and selection behavior
- modal composition and confirmation formatting
- service transport
- domain normalization and payload shaping

For each remaining route, decide which of those boundaries are real in that route.
Some routes may only need one or two narrow extractions.

## Proposed Slices

### Slice A: Work Detail Editor Boundary Review

Intent:

- inventory `catalogue-work-detail-editor.js` against the Work Editor module pattern
- identify whether detail field rendering, detail section/readiness rendering, action workflows, or selection behavior are the clearest first boundary
- avoid extracting route-local code only because the file is long

Acceptance checks:

- first extraction slice has a named responsibility and narrow write set
- route-ready behavior remains stable for empty, single detail, new mode, and bulk mode where supported
- startup reads remain equivalent
- save/build/publication/delete behavior remains traceable from the route entry module or named action module

### Slice B: Work Detail First Extraction

Intent:

- implement the clearest Work Detail boundary found in Slice A
- prefer the boundary that most improves future safety before new detail behavior lands

Likely candidates:

- route-local form renderer
- route-local section/readiness renderer
- route-local action workflow helper
- route-local selection/open helper

### Slice C: Series Editor Boundary Review

Status:

- completed

Intent:

- compare `catalogue-series-editor.js` to the Work Editor splits without forcing identical modules
- focus on membership editing, save/build/publication, prose import, and selection behavior
- decide whether a route-local action helper or membership renderer is the first useful boundary

Review outcome:

- use membership editing as the first Series extraction boundary
- add `assets/studio/js/catalogue-series-membership.js`
- keep action workflow sequencing in `catalogue-series-editor.js` until membership deltas and lookup rebuilding have a clearer route-local API
- defer search/open extraction because Series selection is simpler than Work Detail selection and is not the current risk center
- defer form/summary extraction because Series field definitions and payload shaping already live in `catalogue-series-fields.js`, while the membership save contract still crosses more responsibilities

Proposed membership module responsibilities:

- derive stored work `series_ids` from work-search lookup records
- expose editable and current-member entry lists
- compare current membership against the baseline for dirty-state checks
- initialize member state from a focused series lookup record
- shape changed work membership updates with expected record hashes
- shape saved focused-series lookup membership data after save/publication responses
- render capped member rows and member search results
- manage member-list disabled state and summary metadata
- apply add, remove, and make-primary mutations while preserving `series_ids` order
- preserve the first-member auto-fill rule for blank `primary_work_id`
- block removal of the current primary work until `primary_work_id` changes

Keep route-owned during the membership extraction:

- route bootstrap, generated lookup reads, and route-ready state
- `?series=<series_id>` and `?mode=new` query handling
- `setLoadedSeries`, `setNewSeriesMode`, and `setEmptySearchMode`
- save/create/build/publication/delete/prose orchestration
- validation orchestration and field status rendering
- public build preview and readiness refresh
- service-client calls and activity context construction
- final status/result copy for command outcomes

Acceptance checks:

- series membership behavior remains easy to trace
- create/edit mode and route query behavior remain stable
- public build preview/update behavior remains stable

Implementation acceptance checks:

- `node --check` passes for `assets/studio/js/catalogue-series-editor.js` and `assets/studio/js/catalogue-series-membership.js`
- empty, focused `?series=<series_id>`, and `?mode=new` route modes still reach `data-studio-ready="true"`
- adding the first member work still fills blank `primary_work_id`
- adding later member works does not overwrite an existing `primary_work_id`
- make-primary preserves the work's `series_ids` order except for moving the current series to the front
- removing the current primary work is still blocked until `primary_work_id` changes
- save payload interception shows only changed work membership rows in `work_updates`
- published-series save/build preview still includes removed-member extra work ids when a public update remains pending

Recommended next extraction:

- Slice C1: Series Membership Module

### Slice C1: Series Membership Module

Status:

- implemented

Target file:

- `assets/studio/js/catalogue-series-membership.js`

Scope:

- extract member-list state, current-member entry derivation, member row/list rendering, membership dirty checks, changed-work update shaping, focused lookup membership shaping, and add/remove/make-primary mutations
- preserve `series_ids` order exactly as edited
- preserve first-member `primary_work_id` autofill and current-primary removal blocking
- keep route mode transitions, validation orchestration, service calls, build preview, and action workflow sequencing route-owned

Implementation notes:

- `catalogue-series-membership.js` now owns membership state derivation from focused series lookups and work-search lookup records.
- The module returns only changed work membership rows for save payloads, including expected record hashes from lookup records or computed record hashes.
- The module renders the capped member list and member search results while preserving the existing row actions and work-editor links.
- The route controller calls the module through a small text/status/field-value context and still decides when to refresh validation, dirty state, summary, and route busy state.
- `catalogue-series-editor.js` now imports the membership module but still owns create/edit query behavior and all command workflow sequencing.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-series-editor.js` and `assets/studio/js/catalogue-series-membership.js`.
- Focused module checks covered current-member derivation, dirty membership detection, first-member `primary_work_id` autofill, make-primary ordering, primary removal blocking, changed-work update shaping, saved focused lookup shaping, and capped member-list rendering.
- Static route smoke passed for empty, focused `?series=<series_id>`, and `?mode=new` Series Editor routes against a separate Jekyll build destination.
- Studio docs payloads and Studio search were rebuilt for the Studio scope after documentation updates.

### Slice C2: Series Action Workflow Module

Status:

- implemented

Target file:

- `assets/studio/js/catalogue-series-actions.js`

Scope:

- extract Series save/create/build-preview/build/publication/delete/prose-import sequencing after the membership API has been established
- keep route state transitions, initial route selection, form rendering, and membership mutations out of the action module
- pass membership update shaping into the action module through the membership helper rather than duplicating membership rules

Acceptance checks:

- save payloads remain equivalent for clean metadata edits, membership-only edits, and mixed metadata plus membership edits
- create mode still opens the created series in normal edit mode
- published-series save still performs the internal public update and preserves pending removed-member build targets on partial update failure
- publish/unpublish/delete confirmations and request payloads remain equivalent
- staged prose import still requires a clean saved series and refreshes build preview after import

Implementation notes:

- `catalogue-series-actions.js` now owns Series save/create/build-preview/build/publication/delete/prose-import sequencing.
- The action module builds Series activity contexts and calls the Catalogue service client directly, keeping service transport out of the route controller.
- The route controller supplies callbacks for text lookup, validation, field-message rendering, dirty checks, mode reloads, route-busy sync, and readiness rendering.
- Membership update shaping still flows through `catalogue-series-membership.js`; the action module calls the membership helper rather than recreating membership comparison rules.
- The controller keeps initial route selection, search/open behavior, new/edit mode transitions, field rendering, and membership row mutations.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-series-editor.js` and `assets/studio/js/catalogue-series-actions.js`.
- Static route smoke passed for empty, focused `?series=001`, and `?mode=new` Series Editor routes against the running local Studio route after a separate Jekyll build succeeded.

### Slice C3: Series Selection/Open Module

Status:

- implemented

Target file:

- `assets/studio/js/catalogue-series-selection.js`

Scope:

- extract title/id search matching, popup rendering, open-button behavior, search-keyboard behavior, popup click handling, and initial `?series=<series_id>` route selection if the controller remains noisy after C2
- keep new-mode query handling and created-series opening in the route or action context unless the extraction shows a clean shared boundary

Acceptance checks:

- empty mode still renders after `/studio/catalogue-series/`
- focused mode still opens from `?series=<series_id>`, the search popup, Enter, and the Open button
- `?mode=new` still routes to create mode and treats the top input as the new `series_id`
- unknown ids still show the same popup/status feedback

Implementation notes:

- `catalogue-series-selection.js` now owns Series title/id search matching, search suggestion rendering, focused-series opening, and selection control event binding.
- Initial route selection moved into the selection module, with new-mode query handling kept as a route callback to `setNewSeriesMode`.
- The route still owns field rendering, validation, mode construction, membership UI coordination, readiness rendering, and action workflow callback construction.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-series-editor.js`, `assets/studio/js/catalogue-series-selection.js`, and `assets/studio/js/catalogue-series-actions.js`.
- Static route smoke passed for empty, focused `?series=001`, `?mode=new&series=777`, popup click, Enter-open, Open-button, and unknown `?series=zzzzzz` feedback against the running local Studio route after a separate Jekyll build succeeded.

### Slice C4: Series Form And Section Rendering Review

Status:

- implemented

Target files:

- `assets/studio/js/catalogue-series-form.js`
- `assets/studio/js/catalogue-series-sections.js`

Scope:

- review whether editable field rendering, readonly field rendering, summary rendering, and readiness rendering still create a real controller boundary after C1-C3
- extract only if the remaining route controller still mixes display concerns with route orchestration
- keep `catalogue-series-fields.js` as the owner for field definitions, normalization, payload shaping, and validation

Acceptance checks:

- field values, readonly status display, field availability, and validation messages remain unchanged
- new-mode summary and focused-series summary remain equivalent
- readiness rows still show staged prose import availability and disabled-state notes correctly
- no generic Series/Work form abstraction is introduced unless a real shared contract appears

Implementation notes:

- `catalogue-series-form.js` owns Series field DOM construction, `series_type` option refresh, field value reads/writes, readonly value refresh, mode-specific field availability, and validation message rendering.
- `catalogue-series-sections.js` owns Series summary and readiness rendering, including staged prose import action availability and runtime/build impact copy updates.
- The route controller passes narrow callbacks for UI text lookup, dirty-state checks, field input handling, and status text updates rather than giving helpers route lifecycle or service ownership.
- `catalogue-series-fields.js` continues to own field definitions, normalization, payload shaping, and validation.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-series-editor.js`, `assets/studio/js/catalogue-series-form.js`, and `assets/studio/js/catalogue-series-sections.js`.
- A separate Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static route smoke passed for empty, focused `?series=001`, and `?mode=new&series=777` Series Editor routes with mocked Catalogue read/build endpoints, covering summary rendering, readonly series id display, staged prose readiness rendering, and no page errors.
- Mobile-width field-message smoke passed for the focused Series Editor route, covering validation message rendering for a required `year` field and clearing the message after restoring the value.
- `catalogue-series-editor.js` is now 605 lines after C4; the remaining route entry responsibilities are route lifecycle, data loading, mode transitions, validation orchestration, membership event coordination, action context wiring, and selection context wiring.

### Slice C5: Series Stop/Continue Decision

Status:

- proposed

Scope:

- measure the Series controller after C2-C4
- either document why the remaining route entry file is an acceptable coordinator or define one final Series-specific extraction
- decide whether to proceed to Moment Editor or complete one more Series slice first

Acceptance checks:

- remaining Series route responsibilities are named and intentional
- helper modules have clear import direction and no transport writes outside action/service layers
- next Catalogue priority is explicit

### Slice D: Moment Editor Boundary Review

Intent:

- compare `catalogue-moment-editor.js` to the Work Editor and Series route patterns
- focus on import/prose/media/action workflows before line-count reduction
- avoid abstracting Moment behavior into Work/Series helpers unless the shared contract is real

Acceptance checks:

- moment import/open behavior remains stable
- prose and media readiness behavior remains stable
- save/build/publication/delete behavior remains traceable

### Slice E: Catalogue Scope Stop Point

Intent:

- decide when Catalogue route consistency is good enough to move to the Docs Viewer controller
- update the long-JS inventory with current measured line counts and dispositions

Acceptance checks:

- remaining Catalogue files over the review threshold have either a named slice or a written reason to stay large
- extracted helper modules have clear owners and import direction
- the next non-Catalogue priority is explicit

## Verification Standard

Each implementation slice should define proportional checks:

- `node --check` for touched JavaScript files
- route-ready smoke for affected route modes
- focused browser smoke for the extracted behavior
- startup payload check when generated-data reads are in scope
- Jekyll build when route templates or docs are updated

Docs-only changes should rebuild the Studio docs payloads and Studio docs search.

## Benefits

- keeps Catalogue editor architecture consistent while the Work Editor patterns are still fresh
- reduces future feature risk in the remaining Catalogue editors
- avoids a premature context switch to Docs Viewer work
- makes the long-file policy more precise: review because ownership may be unclear, not because a number was crossed

## Risks

- copying Work Editor module shapes too literally could create unnecessary abstractions
- splitting routes can obscure workflow order if callbacks and helper names are weak
- repeated route-local modules may look duplicative, but that is acceptable until real shared contracts emerge
- deferring Docs Viewer work leaves the largest remaining shared controller untouched for now

## Recommended Next Step

Start with Slice C5: Series Stop/Continue Decision.

The Series membership, action, selection, form, and section extractions are now in place.
The next useful step is to decide whether the remaining Series route controller is an acceptable coordinator or whether one final Series-specific extraction is justified before moving to Moment Editor.
