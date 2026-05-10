---
doc_id: site-request-js-payload-runtime-cleanup
title: JavaScript Payload And Runtime Cleanup Request
added_date: 2026-05-10
last_updated: "2026-05-10 20:55"
ui_status: draft
parent_id: site-request-js-config-structural-review
sort_order: 70
hidden: false
---
# JavaScript Payload And Runtime Cleanup Request

Status:

- request captured
- Slice A implemented
- Slice B implemented
- Slice C implemented
- Slice D implemented
- Slice E implemented
- Slice F implemented
- Slice G implemented
- follow-on work-editor slice H documented

## Purpose

This request follows the completed [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review).

The prior extraction work improved boundaries, but current payload and route-controller sizes still show architectural debt.
This request makes that debt an active cleanup target rather than a passive future risk.

The immediate focus is:

- `assets/studio/js/catalogue-work-editor.js`
- route startup reads for the Catalogue Work Editor
- long Studio route controllers that exceed a defensible ownership boundary

## Position

Be aggressive.

Do not wait for an emergency before refactoring large browser controllers or avoidable payload reads.
Refactors that are deferred because they look risky usually become more risky later as more workflow policy accumulates around the same files.

A route controller over 1,000 lines is not automatically wrong, but it must justify its shape.
If a file needs to stay over that threshold, the architecture should explain why the UI workflow genuinely requires one large controller instead of smaller route-local modules with clear ownership.

The goal is not line-count reduction for its own sake.
The goal is to make workflow ownership visible:

- route shell and DOM binding
- draft state and validation
- generated-data reads
- search and lookup behavior
- save/build/publish/delete orchestration
- summary and section rendering
- modal composition
- service transport

When those concerns are mixed in one controller, the file length is a symptom of unclear workflow interpretation.

## Current Evidence

Recent local review found:

- `assets/studio/js/catalogue-work-editor.js` is 3,043 lines, about 125 KB raw and 23 KB gzip.
- The Catalogue Work Editor route loads 16 transitive JS modules, about 212 KB raw and 45 KB gzip.
- The largest remaining blocks in the work editor are `init`, `saveCurrentWork`, `validateDraft`, `updateSummary`, and `applyPublicationChange`.
- `init` is a clear cleanup target because it combines DOM lookup, state construction, config/text application, server probing, initial data loading, event binding, route-query handling, and fallback error handling.
- Before Slice B, the work editor startup read `catalogue_lookup_work_search`, full `catalogue_works`, and `catalogue_lookup_series_search`.
- `assets/studio/data/catalogue/works.json` is about 1.29 MB raw before transfer compression.

The `catalogue_works` startup read needs to be addressed.
If the work search payload can support open/search/existence checks and per-record lookup payloads can supply edit records, the full source payload should not be loaded during route startup.

## Goals

- Split `catalogue-work-editor.js` around real workflow ownership, starting with `init`.
- Remove or defer the full `catalogue_works` startup read from the Catalogue Work Editor route.
- Define a policy for long JS route files so files over 1,000 lines require explicit architectural justification.
- Prefer behavior-preserving extraction slices that reduce future risk before more features land.
- Keep route entry modules easy to find while moving route-local responsibilities into named helper modules.
- Keep generated JSON schemas and local service endpoint contracts stable unless a later slice explicitly scopes a schema change.

## Non-Goals

- do not introduce a frontend framework just to solve file size
- do not add a bundler or transpiler unless a later payload/cache decision proves it is worth the added build step
- do not merge route controllers into a generic base controller
- do not change user workflows as part of mechanical extraction
- do not split files by arbitrary line ranges without naming the workflow responsibility being moved

## Required Slices

### Slice A: Work Editor Init Split

Status: implemented.

Target:

- `assets/studio/js/catalogue-work-editor.js`

Intent:

- split `init` into named helpers for DOM collection, state creation, text/config binding, server mode setup, initial data loading, event binding, and route parameter handling
- keep behavior and DOM ids stable
- keep the route entry module as the orchestration owner

Acceptance checks:

- work editor reaches route-ready state online and offline
- selected work route query still opens the expected record
- new mode remains routable
- bulk selection still parses and loads selected records
- no visible UI copy, button state, or ready-state behavior changes

Implementation notes:

- `assets/studio/js/catalogue-work-editor.js` now keeps `init` as a short route orchestrator.
- DOM collection, initial state creation, initial field rendering, config/text binding, server probing, startup data loading, event binding, initial route selection, loaded-state marking, and init error rendering are named helpers.
- This slice intentionally preserves the existing startup data contract, including the full `catalogue_works` read, so Slice B can address payload behavior separately.
- `init` dropped from about 330 lines to 28 lines.

Targeted verification:

- `node --check assets/studio/js/catalogue-work-editor.js` passed.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed against the temporary build with the catalogue service blocked; the work editor reached ready state with `service=unavailable`.
- Static Playwright smoke passed against the temporary build with the existing catalogue service available; `?work=00001` loaded as `mode=single` with `recordLoaded=true`.
- Focused Playwright checks passed for `?mode=new` and `?work=00001,00002`, confirming new mode and bulk mode still become route-ready.
- Runtime payload was effectively unchanged by design: the route still loads 16 transitive JS modules, about 212 KB raw and 45 KB gzip, and the `catalogue_works` startup read remains for Slice B.

### Slice B: Remove Full `catalogue_works` Startup Read

Status: implemented.

Target:

- `assets/studio/js/catalogue-work-editor.js`
- generated lookup payload usage, if needed

Intent:

- confirm which workflows still require the full `catalogue_works` payload at startup
- use `catalogue_lookup_work_search` for search, known-id, and duplicate-id checks where sufficient
- use per-work lookup payloads for actual edit records
- keep local-service reads and static generated-data fallback behavior equivalent

Acceptance checks:

- initial work editor startup no longer fetches `assets/studio/data/catalogue/works.json` when the full payload is not needed
- opening a single work still loads the canonical editable record
- bulk open still loads all requested records
- duplicate-id validation in new mode remains reliable
- save, publish, delete, and build-preview flows still refresh the correct generated lookup data

Implementation notes:

- `assets/studio/js/catalogue-work-editor.js` no longer loads `catalogue_works` during initial route startup.
- Startup now reads `catalogue_lookup_work_search` for known-id, search, duplicate-id, and next-id behavior, plus `catalogue_lookup_series_search` for series picker behavior.
- Opening a single work or bulk selection continues to fetch per-work lookup payloads through `catalogue_lookup_work_base`; those payloads provide the editable work records.
- Session-local save/create/publish responses still update `sourceWorkRecordsById`, so refreshed records remain available after writes without a full source reload.
- The removed startup payload is about 1.29 MB raw before transfer compression.

Targeted verification:

- `node --check assets/studio/js/catalogue-work-editor.js` passed.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright network check against the temporary build confirmed initial `/studio/catalogue-work/` startup fetched no `catalogue_works` / `works.json` payload.
- Static Playwright smoke passed with the catalogue service blocked; the work editor reached ready state with `service=unavailable`.
- Static Playwright smoke passed with the existing catalogue service available; `?work=00001` loaded as `mode=single` with `recordLoaded=true`.
- Focused Playwright checks passed for `?mode=new` and `?work=00001,00002`, confirming new mode and bulk mode still become route-ready.

### Slice C: Long JS File Policy And Inventory

Status: implemented.

Intent:

- inventory browser JS files over 1,000 lines
- classify each one as route shell, mixed route controller, domain module, or generated/runtime utility
- require a short justification or extraction plan for each long mixed controller

Acceptance checks:

- each file over 1,000 lines has either an extraction slice or an explicit reason to stay large
- mixed route controllers are prioritized ahead of pure domain modules
- the inventory distinguishes maintenance risk from transfer-size risk

Policy:

- Any browser JavaScript file over 1,000 lines must be classified as one of:
  - route shell
  - mixed route controller
  - domain module
  - generated/runtime utility
- Any mixed route controller over 1,000 lines must have either:
  - a named extraction slice in the owning request or implementation plan
  - an explicit reason to stay large for the next implementation period
- Prioritize long mixed controllers that combine mutation orchestration, modal composition, generated-data reads, and rendering.
- Treat transfer-size risk separately from maintenance risk. A large file is not automatically a runtime problem unless it is eagerly loaded on a high-traffic route or brings avoidable transitive payload.
- Re-run the inventory after material Studio or Docs Viewer JavaScript refactors.

Inventory:

- [JavaScript Payload And Runtime Cleanup Inventory](/docs/?scope=studio&doc=site-request-js-payload-runtime-cleanup-inventory)

Runtime measurement:

- This slice changed docs only.
- Transitive JS payload before/after: unchanged.
- Startup JSON payloads before/after: unchanged.
- Route-ready behavior online/offline: unchanged; no route runtime code was edited.
- Maintenance risk changed because the long-file policy and priority order are now explicit.
- Runtime cost did not change.

Implementation notes:

- The inventory found no over-threshold pure domain modules and no over-threshold generated/runtime utilities.
- All over-threshold files are mixed route or shared viewer controllers, so the cleanup priority is maintenance-driven rather than payload-size-driven.
- The nine over-threshold files total about 647.8 KiB raw and 122.8 KiB gzip, but no route loads all nine together.
- The largest transfer-size risk remains the work-editor entry module because it is the largest file and owns the route already targeted by this request.
- The measured inventory now lives in a separate child doc so the work-editor implementation slices can stay focused while the broader priority list remains available.

Targeted verification:

- Inventory command was run against `assets/**/*.js`.
- Raw and gzip byte measurements were recorded for each file over 1,000 lines.
- Studio docs payloads and Studio docs search were rebuilt after this docs update.

### Slice D: Route Section Renderer Boundaries

Status: implemented.

Intent:

- after the `init` split, evaluate whether work-editor details, files, links, summary, readiness, and preview rendering should move into route-local section modules
- keep route state mutation and write orchestration in the route entry module unless a cleaner boundary appears

Acceptance checks:

- extracted render helpers accept plain state slices or option objects where practical
- section modules do not perform service writes
- modal opening and save/build sequencing remain easy to trace from the route entry module

Target:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-sections.js`

Implementation notes:

- Added `assets/studio/js/catalogue-work-sections.js` as the work-editor route-local section renderer module.
- Moved current-record preview rendering, readiness rendering, work-detail section rendering, work-owned file/link section rendering, summary rail rendering, detail grouping/search helpers, and compact work-summary helpers out of the route entry controller.
- Kept create/save/bulk-save/build/publish/delete/prose/media orchestration in `catalogue-work-editor.js`.
- Kept build-preview modal opening and confirmation modal sequencing in `catalogue-work-editor.js`.
- The section module receives route-owned behavior through a small option object: text lookup, dirty-state checks, changed-field detection, publication-state checks, build-preview activation, and `setTextWithState`.
- Section helpers perform DOM rendering and event binding for rendered section controls, but do not call write services.

Runtime measurement:

- `assets/studio/js/catalogue-work-editor.js` changed from 3,100 lines, 125,204 bytes raw, and about 22,636 bytes gzip to 2,622 lines, 101,094 bytes raw, and about 17,879 bytes gzip.
- New `assets/studio/js/catalogue-work-sections.js` is 582 lines, 27,973 bytes raw, and about 5,768 bytes gzip.
- The work-editor transitive JS module count changed from 16 to 17.
- The measured work-editor transitive JS payload changed from about 211,997 bytes raw / 44,472 bytes gzip to about 215,860 bytes raw / 45,483 bytes gzip.
- Startup JSON payloads are unchanged.
- Route-ready behavior should be unchanged because initial data loading and route-state marking remain in the route entry controller.
- This slice primarily reduces maintenance risk. Transfer-size cost increases slightly because the section renderer is a new module transfer without a bundler.

Targeted verification:

- `node --check assets/studio/js/catalogue-work-editor.js` passed.
- `node --check assets/studio/js/catalogue-work-sections.js` passed.
- Work-editor transitive JS payload was measured before and after the extraction.
- Studio docs payloads and Studio docs search were rebuilt after this docs update.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed for the work editor empty route with the catalogue service blocked.
- Static Playwright smoke passed with the existing catalogue service available for `?work=00001`, `?mode=new`, and `?work=00001,00002`.

### Slice E: Work Form Renderer Boundary

Status: implemented.

Intent:

- move editable field rendering, read-only field rendering, series picker UI, field value get/set helpers, and field-message rendering out of the route controller
- keep validation rules, dirty-state interpretation, route mode decisions, and save/build orchestration in the route controller or existing domain modules
- make the editor entry module read as route flow rather than form construction

Acceptance checks:

- scalar work fields render with the same labels, values, disabled states, and validation message placement
- series picker search, selected-series chips, add/remove behavior, and bulk raw `series_ids` behavior remain unchanged
- read-only fields keep the same display and mode availability behavior
- `node --check` passes for the route entry module and the new form module
- work-editor route-ready smoke checks pass for empty/offline, single work, new mode, and bulk mode

Target:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-form.js`

Risk removed:

- the densest remaining DOM-construction block leaves the route controller without changing service writes or route loading
- future form-field additions have a clear owner and do not need to modify route orchestration code

Implementation notes:

- Added `assets/studio/js/catalogue-work-form.js` as the work-editor route-local form module.
- Moved scalar field rendering, read-only field rendering, series picker DOM/event behavior, form text synchronization, field value get/set helpers, draft-to-input synchronization, read-only clearing, mode-specific field availability, and field validation message rendering out of `catalogue-work-editor.js`.
- Kept validation rules, dirty-state interpretation, route mode decisions, generated-data reads, save/build/publish/delete orchestration, and modal sequencing in `catalogue-work-editor.js`.
- The form module receives route-owned behavior through a small callback object for UI text lookup, field input handling, and route state refresh.

Runtime measurement:

- `assets/studio/js/catalogue-work-editor.js` changed from 2,622 lines, 101,094 bytes raw, and about 17,879 bytes gzip to 2,266 lines, 86,929 bytes raw, and about 15,461 bytes gzip.
- New `assets/studio/js/catalogue-work-form.js` is 408 lines, 16,081 bytes raw, and about 3,475 bytes gzip.
- The work-editor transitive JS module count changed from 17 to 18.
- The measured work-editor transitive JS payload changed from about 215,860 bytes raw / 45,483 bytes gzip to about 217,776 bytes raw / 46,540 bytes gzip.
- Startup JSON payloads are unchanged.
- Route-ready behavior is unchanged for offline empty, single work, new mode, and bulk routes.
- This slice reduces maintenance risk. Transfer-size cost increases slightly because the form renderer is a new module transfer without a bundler.

Targeted verification:

- `node --check assets/studio/js/catalogue-work-editor.js` passed.
- `node --check assets/studio/js/catalogue-work-form.js` passed.
- Work-editor transitive JS payload was measured after the extraction.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed for the work editor empty route with the catalogue service blocked.
- Static Playwright smoke passed with the existing catalogue service available for `?work=00001`, including rendered title value and selected series chip.
- Static Playwright smoke passed for `?mode=new`, including field-input validation message refresh for an invalid year.
- Static Playwright smoke passed for `?work=00001,00002`, including visible bulk `series_ids` input update.

### Slice F: Work Route Mode State Boundary

Status: implemented.

Intent:

- extract single-work, bulk-work, new-work, and empty-search loaded-state transitions into a route-local state module
- keep service fetching and URL synchronization in the route controller unless the extraction exposes a cleaner narrow boundary
- make mode transitions explicit enough that later action modules can call them without duplicating state mutation

Acceptance checks:

- opening a single work still sets `mode=single`, `recordLoaded=true`, baseline draft, source record, and URL state correctly
- bulk open still records selected ids, mixed fields, record hashes, and unavailable ids correctly
- new mode still seeds the suggested id and draft status correctly
- empty/offline mode still reaches route-ready with the same unavailable-service messaging
- save/create outcomes can still re-enter the correct loaded state

Target:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-route-state.js`

Risk removed:

- route mode transitions stop being implicit side effects scattered through the controller
- future workflow actions can reuse named state transitions instead of mutating route state directly

Implementation notes:

- Added `assets/studio/js/catalogue-work-route-state.js` as the route-local state transition module.
- Moved route-ready detail calculation, route busy/ready synchronization, URL synchronization, single-work loaded state, bulk-work loaded state, new-work mode, empty-search mode, and bulk draft aggregation out of `catalogue-work-editor.js`.
- Kept service fetching, lookup selection, validation, dirty-state interpretation, rendering refresh, and save/build/publish/delete orchestration in `catalogue-work-editor.js`.
- The route-state module receives route-owned behavior through a small callback object for UI text, status text updates, popup visibility, form synchronization, read-only field refresh, and editor-state refresh.
- Save/create/publication outcomes now re-enter loaded state through the route-state helper, leaving action workflow extraction prepared for Slice G.

Runtime measurement:

- `assets/studio/js/catalogue-work-editor.js` changed from 2,266 lines, 86,929 bytes raw, and about 15,461 bytes gzip to 2,061 lines, 80,247 bytes raw, and about 14,502 bytes gzip.
- New `assets/studio/js/catalogue-work-route-state.js` is 270 lines, 9,132 bytes raw, and about 2,254 bytes gzip.
- The work-editor transitive JS module count changed from 18 to 19.
- The measured work-editor transitive JS payload changed from about 217,776 bytes raw / 46,540 bytes gzip to about 220,226 bytes raw / 47,628 bytes gzip.
- Startup JSON payloads are unchanged, and static smoke confirmed initial startup still does not fetch `assets/studio/data/catalogue/works.json`.
- Route-ready behavior is unchanged for offline empty, single work, new mode, and bulk routes.
- This slice reduces maintenance risk. Transfer-size cost increases slightly because the route-state helper is a new module transfer without a bundler.

Targeted verification:

- `node --check assets/studio/js/catalogue-work-editor.js` passed.
- `node --check assets/studio/js/catalogue-work-route-state.js` passed.
- Work-editor transitive JS payload was measured after the extraction.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed for the work editor empty route with the catalogue service blocked.
- Static Playwright smoke passed with the existing catalogue service available for `?work=00001`, including route state `mode=single` and `recordLoaded=true`.
- Static Playwright smoke passed for `?mode=new`, including a seeded suggested work id.
- Static Playwright smoke passed for `?work=00001,00002`, including route state `mode=bulk` and `recordLoaded=true`.
- All smoke checks confirmed no `assets/studio/data/catalogue/works.json` startup fetch.

### Slice G: Work Action Workflow Boundary

Status: implemented.

Intent:

- extract save, create, build preview, build, prose import, publish/unpublish, media refresh, and delete workflows into a route-local action module
- keep low-level HTTP calls in `catalogue-editor-service-client.js`
- keep route state transitions delegated through the route-mode helper introduced by Slice F

Acceptance checks:

- single save, bulk save, create, build preview, build, publish, unpublish, prose import, media refresh, and delete behavior remain traceable from the route entry module
- action helpers receive an explicit route context rather than importing route globals
- confirmation modal sequencing and activity context remain unchanged
- service success and failure messages still update the same status nodes and dirty-state controls
- focused Playwright smoke covers at least non-mutating build-preview availability plus route-ready checks; mutating paths use the existing local-service preview/dry-run behavior where possible

Target:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-actions.js`

Risk removed:

- write orchestration becomes a named boundary instead of interleaving with rendering and route bootstrap
- future write workflows have one route-local owner while the service client remains transport-only

Implementation notes:

- Added `assets/studio/js/catalogue-work-actions.js` as the work-editor route-local action workflow module.
- Moved save, create, build-preview refresh, field-aware build preview, build, prose import, publish/unpublish, media refresh, and delete orchestration out of `catalogue-work-editor.js`.
- Kept low-level HTTP transport in `catalogue-editor-service-client.js`.
- Kept validation rules, form-message rendering, modal composition, route-state option construction, and search/open behavior in the route entry module.
- The action module receives an explicit route context for text lookup, status writing, validation, route-state transitions, current-preview rendering, build-preview modal opening, and create-mode record opening.
- The shared publication-state and bulk-build target helpers now live with the action workflow boundary and are imported by the route controller for button-state rendering.

Runtime measurement:

- `assets/studio/js/catalogue-work-editor.js` changed from 2,061 lines, 80,247 bytes raw, and about 14,502 bytes gzip to 1,231 lines, 45,068 bytes raw, and about 9,096 bytes gzip.
- New `assets/studio/js/catalogue-work-actions.js` is 913 lines, 39,452 bytes raw, and about 6,489 bytes gzip.
- The work-editor transitive JS module count changed from 19 to 20.
- The measured work-editor transitive JS payload changed from about 220,226 bytes raw / 47,628 bytes gzip to about 224,499 bytes raw / 48,885 bytes gzip.
- Startup JSON payloads are unchanged, and static smoke confirmed initial startup still does not fetch `assets/studio/data/catalogue/works.json`.
- Route-ready behavior is unchanged for offline empty, single work, new mode, and bulk routes.
- The field-aware build-preview button remains present and disabled when no unsaved published-work preview is available.
- This slice reduces maintenance risk. Transfer-size cost increases slightly because the action helper is a new module transfer without a bundler.

Targeted verification:

- `node --check assets/studio/js/catalogue-work-editor.js` passed.
- `node --check assets/studio/js/catalogue-work-actions.js` passed.
- Work-editor transitive JS payload was measured after the extraction.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed for the work editor empty route against the temporary build.
- Static Playwright smoke passed for `?work=00001`, `?mode=new`, and `?work=00001,00002`, including route-ready state, no page errors, no full `works.json` startup fetch, and non-mutating build-preview button availability for the single-work route.

### Slice H: Work Search And Selection Boundary

Status: planned.

Intent:

- extract work-id parsing, bulk range parsing, search-token matching, search result rendering, open-selection, and open-by-id helpers into a focused route-local module
- keep actual record loading delegated back to the route controller or route-state helper so search remains a selection concern
- preserve static generated-data fallback behavior and known-id checks from the Slice B payload cleanup

Acceptance checks:

- comma lists, numeric ranges, duplicate ids, invalid ids, and single ids parse exactly as before
- search results still cap at the configured limit and open the selected work
- new-mode duplicate-id validation still uses the same known-id source
- bulk open still reports unavailable ids correctly
- startup still avoids fetching full `catalogue_works`

Target:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-selection.js`

Risk removed:

- search and bulk-selection behavior becomes testable and reusable without reading the save/build/publish controller flow
- future selection improvements can be made without touching form rendering or write orchestration

## Runtime Measurement Requirements

Each implementation slice should record:

- transitive JS payload for the route before and after
- startup JSON payloads fetched before and after
- route-ready behavior online and offline
- whether the change affects maintenance risk, runtime cost, or both

For Slice B, fetch verification should specifically prove whether `catalogue_works` is still requested on initial load.

## Benefits

- faster Catalogue Work Editor startup when the full source payload is removed or deferred
- smaller and more understandable work-editor route entry module
- clearer boundary between UI workflow orchestration and route-local rendering
- lower future refactor risk because large mixed controllers are addressed before more behavior accumulates
- a repeatable standard for deciding when long JavaScript files are an architectural smell

## Risks

- splitting route controllers can obscure workflow order if helper names and import direction are weak
- removing `catalogue_works` startup reads may expose hidden dependencies on full source data
- bulk mode and duplicate-id validation need focused checks because they are likely to rely on broad lookup state
- aggressive refactoring needs disciplined smoke tests so behavior-preserving slices do not become untracked rewrites

## Recommended Next Step

Implement Slice H next.
It should extract work-id parsing, bulk range parsing, search-token matching, search result rendering, open-selection, and open-by-id helpers into a focused route-local module while keeping record loading delegated through the current route-state and action boundaries.

After Slices E-H, return to the broader [JavaScript Payload And Runtime Cleanup Inventory](/docs/?scope=studio&doc=site-request-js-payload-runtime-cleanup-inventory) for the next priority outside the Catalogue Work Editor.
