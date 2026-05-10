---
doc_id: site-request-catalogue-js-runtime-consistency
title: Catalogue JavaScript Runtime Consistency Request
added_date: 2026-05-10
last_updated: "2026-05-10 21:47"
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

## Implementation Progress

2026-05-10:

- Work Detail boundary review chose search, lookup, and selection as the first extraction because it matched the Work Editor route pattern and had a clear route-local ownership boundary.
- Added `assets/studio/js/catalogue-work-detail-selection.js` for detail query parsing, popup suggestions, single/bulk open flows, and initial route selection.
- Added `assets/studio/js/catalogue-work-detail-form.js` for form field rendering, readonly field rendering, field label refresh, field value synchronization, field availability, and validation message rendering.
- Kept `assets/studio/js/catalogue-work-detail-editor.js` responsible for route bootstrap, state assembly, field rendering, summary/readiness rendering, and save/build/publication/delete workflows.
- Kept form input mutation and validation decisions in the route controller so save/build/publication contracts remain unchanged.
- Added `assets/studio/js/catalogue-work-detail-sections.js` for current-detail preview rendering, readiness rows, new/single/bulk summary rendering, and shared Work Detail selection-list formatting.
- Kept Work Detail action workflow sequencing in the route controller for the next review slice because those paths still coordinate service responses, record hashes, route state, and status messaging.

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
| `assets/studio/js/catalogue-work-detail-editor.js` | selection/opening, form rendering/synchronization, and summary/readiness/preview extractions complete; remaining review area is action workflow sequencing |
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

Intent:

- compare `catalogue-series-editor.js` to the Work Editor splits without forcing identical modules
- focus on membership editing, save/build/publication, prose import, and selection behavior
- decide whether a route-local action helper or membership renderer is the first useful boundary

Acceptance checks:

- series membership behavior remains easy to trace
- create/edit mode and route query behavior remain stable
- public build preview/update behavior remains stable

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

Start with Slice A: Work Detail Editor Boundary Review.

The Work Detail Editor is closest to the Work Editor route and is the highest-priority remaining Catalogue controller in the long-JS inventory.
