---
doc_id: site-request-js-config-structural-review-catalogue-editor-boundary
title: Catalogue Editor Boundary Spec Slice
added_date: 2026-05-10
last_updated: "2026-05-10 15:24"
ui_status: in-progress
parent_id: site-request-js-config-structural-review
sort_order: 30
hidden: false
---
# Catalogue Editor Boundary Spec Slice

Status:

- planned

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
