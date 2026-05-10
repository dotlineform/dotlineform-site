---
doc_id: site-request-js-config-structural-review-docs-viewer-boundary
title: Docs Viewer Boundary Spec Slice
added_date: 2026-05-10
last_updated: "2026-05-10 14:45"
ui_status: done
parent_id: site-request-js-config-structural-review
sort_order: 20
hidden: false
---
# Docs Viewer Boundary Spec Slice

Status:

- implemented

## Purpose

This child doc tracks the second implementation slice from the [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review).

The goal is to turn the current large Docs Viewer browser controller into a clear extraction plan before any module split begins.
This slice should define ownership boundaries, public internal contracts, and representative smoke checks for the read-only and management surfaces.

## Problem

The Docs Viewer is an important shared runtime for Studio, Library, and other documentation scopes.
Its current browser entry point has accumulated several responsibilities:

- route/query parsing and active-scope state
- generated docs index and content reads
- navigation tree rendering and document selection
- in-document search and aggregate search behaviors
- favourites/bookmark state
- management-mode controls and modal wiring
- metadata save, publish/unpublish, move, undo, and rebuild interactions
- generated-data read helpers and local-service transport calls

Those responsibilities are related, but they do not all need to live in one controller.
Extraction should be planned carefully because the Docs Viewer is a cross-scope shell and a frequent Studio support tool.

## Target Boundary Questions

This slice should answer:

1. Which functions are pure state/query helpers and can move without DOM coupling?
2. Which functions are generated-data loaders and should become a small data client?
3. Which functions are management-mode service actions and should sit behind a Docs management client?
4. Which functions are rendering-only helpers and should remain owned by the viewer shell?
5. Which search and favourites behaviors are generic Docs Viewer concerns versus browser-storage concerns?
6. Which public internal contracts must stay stable for the entry controller after extraction?
7. Which smoke checks are required before each extraction step is considered safe?

Answers:

- [Docs Viewer Function Inventory](/docs/?scope=studio&doc=site-request-js-config-structural-review-docs-viewer-inventory) records the current function ownership groups and mixed-responsibility hotspots.
- [Docs Viewer Extraction Plan](/docs/?scope=studio&doc=site-request-js-config-structural-review-docs-viewer-extraction-plan) records target modules, import direction, public internal contracts, implementation slices, and smoke checks.

## Candidate Module Boundaries

The final module list should be confirmed by inventory before implementation, but likely boundaries are:

- `docs-viewer-state.js`
  query parameters, active scope/doc normalization, viewer mode, and selected-document state shaping
- `docs-viewer-data.js`
  generated docs index/content reads, content URL resolution, scope metadata, and error shaping
- `docs-viewer-search.js`
  local document search, aggregate result shaping, normalization, and search result highlighting decisions
- `docs-viewer-favourites.js`
  favourites/bookmarks persistence, migration/defaulting, and UI-facing state summaries
- `docs-viewer-management-client.js`
  local docs-management endpoints, metadata save, publish/unpublish, move, undo, import/export, and rebuild calls
- `docs-viewer-render.js`
  navigation tree, document body, search results, status, and management control rendering helpers
- `docs-viewer.js`
  route composition, event binding, lifecycle orchestration, and cross-module coordination

The exact names can change if the inventory shows a cleaner split.
The important point is that route orchestration, data access, management transport, search, favourites, and rendering should not remain indistinguishable.

Inventory result:

- start with `docs-viewer-tree.js` for pure tree and visibility helpers
- then extract `docs-viewer-search.js` for pure search and recently-added helpers
- then extract `docs-viewer-favourites.js` for bookmark record/storage helpers
- then extract `docs-viewer-data.js` for asset-versioned generated-data reads and retry helpers
- then extract `docs-viewer-management-client.js` for local-service capability and write endpoint wrappers
- defer rendering, metadata modal, status pill, context menu, and drag/drop modules until the pure/data/client boundaries are stable

## Implementation Tasks

1. Inventory `assets/js/docs-viewer.js` by function owner.
   - Group functions under state/query, data loading, rendering, search, favourites, management transport, modal wiring, and lifecycle orchestration.
   - Record functions that mix owners and therefore need smaller preparatory cleanup before extraction.

2. Define the target module list and import direction.
   - Keep the entry controller as the top-level coordinator.
   - Avoid circular imports.
   - Keep browser storage and local-service calls behind narrow helpers.

3. Define public internal contracts for the first extraction.
   - State helpers should accept and return plain objects where practical.
   - Data helpers should return normalized success/error shapes.
   - Management helpers should hide endpoint paths and transport details from render/event code.
   - Rendering helpers should not initiate fetches or service writes.

4. Map representative smoke checks.
   - Read-only docs load from a direct `scope` and `doc` URL.
   - Search returns results and selects a result.
   - Favourites/bookmarks persist across reload.
   - Manage mode opens metadata controls.
   - Metadata save posts the expected payload and updates visible status.
   - Move/undo behavior remains available where supported.
   - Generated-data reads still load the docs index and selected content.

5. Decide the extraction order.
   - Prefer low-risk pure helpers first.
   - Defer modal and mutation paths until transport and smoke checks are explicit.
   - Avoid changing UI composition during boundary extraction unless a small interface cleanup is needed for a stable contract.

6. Write follow-up implementation slices.
   - Each extraction slice should have a narrow write set, targeted tests or smoke checks, and an explicit rollback boundary.
   - Do not combine a large file split with behavior changes.

## Implementation Notes

This slice produced planning documentation only.
No Docs Viewer runtime files were split.

The first recommended implementation slice is documented as Slice A in [Docs Viewer Extraction Plan](/docs/?scope=studio&doc=site-request-js-config-structural-review-docs-viewer-extraction-plan):

- add `assets/js/docs-viewer-tree.js`
- move only pure tree and visibility helpers
- keep the entry controller as lifecycle owner
- verify read-only Studio docs and Library docs still load

## Acceptance Checks

- a function inventory exists in this doc or a linked child doc
- target modules and import direction are named
- the first extraction slice is small enough to implement and verify independently
- read-only, search, favourites, manage-mode, metadata-save, move/undo, and generated-data smoke checks are listed
- no Docs Viewer runtime files are split before the boundary spec is accepted
- `./scripts/build_docs.rb --scope studio --write` is run after this doc changes
- `./scripts/build_search.rb --scope studio --write` is run after Studio docs search output changes

## Benefits

- reduces risk before splitting a shared Docs Viewer runtime
- makes later extraction tasks easier to assign, review, and test
- separates route orchestration from data, search, favourites, rendering, and management transport concerns
- gives future Docs Viewer changes a clearer place to land

## Risks

- the inventory may reveal more mixed responsibilities than the first target module list suggests
- over-splitting could make the viewer harder to follow if contracts are not kept small
- management-mode smoke tests may need local service interception or a running docs-management service

## Out Of Scope

- no Docs Viewer runtime extraction in this slice
- no UI redesign
- no generated docs schema changes
- no search ranking changes
- no local docs-management endpoint changes
- no browser-storage migration unless the inventory shows an existing compatibility issue that must be documented
