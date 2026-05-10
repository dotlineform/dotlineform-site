---
doc_id: site-request-js-payload-runtime-cleanup
title: JavaScript Payload And Runtime Cleanup Request
added_date: 2026-05-10
last_updated: "2026-05-10 19:23"
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

Status: not started.

Intent:

- inventory browser JS files over 1,000 lines
- classify each one as route shell, mixed route controller, domain module, or generated/runtime utility
- require a short justification or extraction plan for each long mixed controller

Initial candidates:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/js/docs-viewer.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/data-import.js`

Acceptance checks:

- each file over 1,000 lines has either an extraction slice or an explicit reason to stay large
- mixed route controllers are prioritized ahead of pure domain modules
- the inventory distinguishes maintenance risk from transfer-size risk

### Slice D: Route Section Renderer Boundaries

Status: not started.

Intent:

- after the `init` split, evaluate whether work-editor details, files, links, summary, readiness, and preview rendering should move into route-local section modules
- keep route state mutation and write orchestration in the route entry module unless a cleaner boundary appears

Acceptance checks:

- extracted render helpers accept plain state slices or option objects where practical
- section modules do not perform service writes
- modal opening and save/build sequencing remain easy to trace from the route entry module

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

Start with Slice A.

`init` is the lowest-risk cleanup because it can be split without changing payload contracts.
Then run Slice B while the startup data-loading boundary is fresh and easy to measure.
