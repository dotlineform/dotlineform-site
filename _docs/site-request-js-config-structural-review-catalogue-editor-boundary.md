---
doc_id: site-request-js-config-structural-review-catalogue-editor-boundary
title: Catalogue Editor Boundary Spec Slice
added_date: 2026-05-10
last_updated: "2026-05-10 15:27"
ui_status: done
parent_id: site-request-js-config-structural-review
sort_order: 30
hidden: false
---
# Catalogue Editor Boundary Spec Slice

Status:

- implemented boundary spec

## Purpose

This child doc tracks the third implementation slice from the [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review).

The goal is to define stable ownership boundaries for the catalogue editor route controllers before extracting shared runtime code.
This slice should start with `assets/studio/js/catalogue-work-editor.js`, then compare the work-detail, series, and moment editors for reusable domain and workflow helpers.

## Problem

The catalogue editor routes already have useful field modules, but the route controllers still own broad mixed workflows:

- record identity, hash, and route query behavior
- create, edit, bulk, publish, delete, and build-preview flows
- local service transport and generated-data reload decisions
- modal composition and confirmation copy
- embedded work files, links, detail rows, and media preview readiness
- dirty-field tracking, validation summaries, and save payload shaping
- route-specific rendering and Studio shell state

Those responsibilities are related, but they do not all need to remain in each route controller.
The boundary spec should identify what is Catalogue domain logic, what is Studio UI shell behavior, what is transport, and what must stay route-local.

## Target Boundary Questions

This slice should answer:

1. Which helpers are shared across work, work-detail, series, and moment editors?
2. Which helpers are specific to the work editor and should not become shared too early?
3. Which field-plan, dirty-state, validation, and payload-shaping helpers already have good owners?
4. Which modal and confirmation formatters can move without changing UI behavior?
5. Which local-service calls should sit behind a catalogue editor client built on `studio-transport.js`?
6. Which generated lookup or catalogue payload reads are route orchestration versus domain data access?
7. Which smoke checks are required before each extraction step is considered safe?

## Candidate Module Boundaries

The final module list should be confirmed by inventory before implementation, but likely boundaries are:

- `catalogue-editor-records.js`
  record identity, title/id labels, hash helpers, and selected-record summaries
- `catalogue-editor-dirty-state.js`
  dirty-field comparison, field-plan summaries, and unsaved-change state shaping
- `catalogue-editor-service-client.js`
  create, update, publish, delete, build-preview, and generated-data reload service calls
- `catalogue-editor-modal-formatters.js`
  publication/delete/build-preview modal text and summary rendering helpers
- `catalogue-editor-embedded-items.js`
  work file/link/detail embedded entry normalization and list helpers, if shared pressure is confirmed
- route entry modules
  DOM references, route binding, page-specific rendering, lifecycle sequencing, and cross-module coordination

The exact names can change if the inventory shows a cleaner split.
The important point is that route orchestration, domain normalization, service transport, and modal formatting should not remain indistinguishable.

## Implementation Tasks

1. Inventory the catalogue editor route controllers by responsibility.
   - Start with `assets/studio/js/catalogue-work-editor.js`.
   - Compare `catalogue-work-detail-editor.js`, `catalogue-series-editor.js`, and `catalogue-moment-editor.js`.
   - Record repeated helpers and workflows, not just repeated function names.

2. Identify existing field-module ownership.
   - Keep field-level normalization, validation, id suggestions, and payload shaping with existing field modules where they already fit.
   - Avoid moving logic only to create a larger generic catalogue module.

3. Define the first extraction boundary.
   - Prefer pure helpers or service-client wrappers before modal or route lifecycle code.
   - Keep create/edit/bulk mode behavior stable.
   - Keep route entry modules easy to locate.

4. Define public internal contracts.
   - Domain helpers should accept plain record/config objects and return shaped records or summaries.
   - Service helpers should hide endpoint names and transport details from route event handlers.
   - Modal helpers should format content but not perform service writes.
   - Route modules should own DOM reads, event binding, lifecycle, and user-triggered orchestration.

5. Map representative smoke checks.
   - Work editor loads a selected work and reaches ready state.
   - Safe field edit updates dirty state and save payload.
   - Create mode remains routable.
   - Bulk mode still lists selected records where supported.
   - Build-preview modal still renders the same summary.
   - Publish/delete confirmations still post the expected payloads when intercepted.

6. Write follow-up implementation slices.
   - Each extraction slice should have a narrow write set, targeted checks, and an explicit rollback boundary.
   - Do not combine a route-controller split with behavior changes.

## Inventory Result

Route controller sizes at review time:

| Controller | Approx. lines | Primary modes |
| --- | ---: | --- |
| `assets/studio/js/catalogue-work-editor.js` | 3,181 | search/open, create, bulk, save, build, publish, delete, prose import |
| `assets/studio/js/catalogue-work-detail-editor.js` | 1,853 | search/open, create, bulk, save, build, publish, delete |
| `assets/studio/js/catalogue-series-editor.js` | 1,627 | search/open, create, save, build, publish, delete, membership editing, prose import |
| `assets/studio/js/catalogue-moment-editor.js` | 1,425 | search/open, import, save, build, publish, delete, prose import |

Shared controller responsibilities:

- route bootstrap through `loadStudioConfig`, local catalogue health probing, route-ready state, save-mode text, and config-backed UI copy
- selected-record identity, route query/hash synchronization, open/search popup rendering, and current-record summaries
- stable record hashing for dirty detection, draft comparison, changed-field calculation, validation summaries, and save button state
- create/edit mode switching, readonly/current-record panels, form rendering, field input events, field-level error messages, and save payload orchestration
- build-preview loading, readiness item rendering, generated-output reload decisions, and build-apply status handling
- publication and delete preview/apply flows that share the same endpoint family and confirmation shape
- local service writes through `CATALOGUE_WRITE_ENDPOINTS` plus `postJson`, with repeated `activity` context payloads
- generated lookup reads through `loadStudioLookupJson` and focused `loadStudioLookupRecordJson`

Existing field-module ownership is already useful and should be preserved:

- `catalogue-work-fields.js` owns work normalization, embedded entry normalization, draft/record shaping, create payload shaping, series-id parsing, and next-id suggestion
- `catalogue-work-detail-fields.js` owns detail id normalization, draft/record shaping, save/create payload shaping, sort-order normalization, create validation, and next-id suggestion
- `catalogue-series-fields.js` owns series id normalization, draft/record shaping, save/create payload shaping, series type options, create/edit validation, and next-id suggestion
- the moment editor still defines its field list, normalization, draft read, validation, and payload shaping locally; that is a later candidate for a small `catalogue-moment-fields.js`, not part of the first shared extraction

Work-editor-specific behavior should stay route-local until stronger reuse pressure exists:

- series picker search, selected-series draft management, and bulk series add/remove/replace semantics
- current-work detail grouping, detail rows, and work-detail editor links
- embedded work file and link modal editing
- work primary image plus detail thumbnail preview composition
- work-specific prose import and media readiness summaries

Series-editor-specific behavior should stay route-local:

- membership diffing, primary member selection, work-to-series updates, and member list rendering
- changed-work update generation for membership saves

Moment-editor-specific behavior should stay route-local:

- source-file import mode, import preview/apply state, import metadata forms, and moment-file session query handling

## Target Module Shape

Recommended extraction targets:

- `assets/studio/js/catalogue-editor-records.js`
  Pure record helpers shared by editor controllers: stable stringify, record hashing, display-value helpers, changed-field summaries, and small identity label helpers that accept route-specific callbacks.
- `assets/studio/js/catalogue-editor-dirty-state.js`
  Draft-vs-record comparison helpers, changed-field list shaping, field-plan summary helpers, and unsaved-change summary records. This module should not know DOM ids or endpoints.
- `assets/studio/js/catalogue-editor-service-client.js`
  A thin client over `studio-transport.js` for catalogue create, save, bulk save, build preview/apply, publication preview/apply, delete preview/apply, prose import, media refresh, and moment import. It should hide endpoint names from route event handlers while preserving current payload contracts.
- `assets/studio/js/catalogue-editor-modal-formatters.js`
  Pure HTML/text formatters for build-preview, publication, delete, and field-plan confirmation content. Modal opening, button wiring, and write orchestration stay route-local.
- `assets/studio/js/catalogue-editor-readiness.js`
  Readiness item normalization, tone selection, fallback generated/source text helpers, and compact readiness summary shaping.
- Route entry modules
  `catalogue-work-editor.js`, `catalogue-work-detail-editor.js`, `catalogue-series-editor.js`, and `catalogue-moment-editor.js` continue to own DOM references, event binding, route/query state, lifecycle sequencing, selected-mode state, and route-specific rendering.

Deferred targets:

- `assets/studio/js/catalogue-editor-embedded-items.js`
  Only extract after another route needs work-file/link-style embedded list behavior.
- `assets/studio/js/catalogue-moment-fields.js`
  Useful as a route-local field-module parity slice before trying to share moment editor logic.

## Import Direction

Allowed direction:

- route controllers import shared catalogue editor helpers
- shared catalogue editor helpers may import `studio-transport.js` only in the service-client module
- pure helpers receive plain records, drafts, config text callbacks, or small option objects
- field modules remain domain owners for field normalization, validation, id suggestions, and payload shaping

Avoid:

- shared helpers importing route controllers
- shared helpers reading DOM nodes, `window.location`, or the route state singleton
- modal formatters performing service writes
- service-client helpers formatting user-facing confirmation copy
- a generic catalogue editor base class or merged mega-controller

## First Extraction Slice

Slice A should be `catalogue-editor-service-client.js`.

Scope:

- add wrapper functions for the endpoint families already used by all or most controllers:
  - build preview/apply
  - publication preview/apply
  - delete preview/apply
  - prose import preview/apply
  - create/save/bulk save where each wrapper keeps the existing payload shape
- keep the route controllers responsible for when calls happen, how activity contexts are built, how returned lookup data updates route state, and how modals render
- leave field modules and UI rendering untouched

Why this first:

- it creates a clear transport boundary without changing route state or DOM behavior
- it removes endpoint-string knowledge from event handlers in small call-site edits
- it can be rolled back by restoring imports and direct `postJson(CATALOGUE_WRITE_ENDPOINTS.*)` calls
- it prepares later modal and build-preview extraction without moving user-facing workflows at the same time

Do not include in Slice A:

- no field-plan refactor
- no modal HTML extraction
- no create/edit mode state refactor
- no embedded work file/link refactor
- no generated lookup read strategy changes

## Follow-Up Slices

Recommended sequence after Slice A:

1. Extract shared readiness helpers used by work, work-detail, series, and moment build-preview sections.
2. Extract pure record hashing and display helpers into `catalogue-editor-records.js`.
3. Extract modal formatter helpers for build-preview, publication, and delete confirmations.
4. Add `catalogue-moment-fields.js` for moment field-module parity if moment editor changes continue.
5. Reassess dirty-state extraction only after the service and modal seams reduce route-controller noise.

Each slice should update this request or a linked implementation child doc with the exact write set and checks before runtime edits begin.

## Verification Map

Representative smoke checks before accepting each runtime extraction:

- work editor loads a selected work and reaches ready state
- work-detail editor loads a selected detail and reaches ready state
- series editor loads a selected series and reaches ready state
- moment editor loads a selected moment and reaches ready state
- safe field edit updates dirty state and produces the same save payload when intercepted
- create mode remains routable for work, work detail, and series
- bulk mode still parses and lists selected work/work-detail records
- build-preview modal renders equivalent artifact/readiness summaries
- publish and delete confirmations post the same intercepted payloads
- generated-data reload after save/build still refreshes the expected lookup or catalogue data

For this boundary-spec slice, no runtime smoke is required because no catalogue editor runtime files were split.

## Acceptance Checks

- a function/workflow inventory exists in this doc or a linked child doc
- target modules and import direction are named
- the first extraction slice is small enough to implement and verify independently
- work, work-detail, series, and moment editor overlap is explicitly assessed
- create/edit/bulk modes are listed as stability constraints
- representative load, edit/save, build-preview, publish/delete, and generated-data checks are listed
- no catalogue editor runtime files are split before the boundary spec is accepted
- `./scripts/build_docs.rb --scope studio --write` is run after this doc changes
- `./scripts/build_search.rb --scope studio --write` is run after Studio docs search output changes

## Benefits

- gives catalogue editor work a clearer home before more requirements are added
- reduces duplicate workflow policy across catalogue routes
- separates Catalogue domain behavior from Studio shell behavior and transport concerns
- creates smaller, safer follow-up extraction tasks

## Risks

- the work editor may have route-specific complexity that looks reusable but should stay local
- over-generalizing too early could make smaller editors harder to follow
- smoke tests may need local service interception to verify save, publish, delete, and build-preview flows without writing source data

## Out Of Scope

- no catalogue editor runtime extraction in this slice
- no generated catalogue schema changes
- no service endpoint changes
- no UI redesign
- no source data writes
- no merge of all catalogue editors into one controller
