---
doc_id: site-request-js-config-structural-review-catalogue-editor-extraction-plan
title: Catalogue Editor Extraction Plan
added_date: 2026-05-10
last_updated: "2026-05-10 15:36"
ui_status: in-progress
parent_id: site-request-js-config-structural-review-catalogue-editor-boundary
sort_order: 20
hidden: false
---
# Catalogue Editor Extraction Plan

Status:

- planned execution sequence
- next executable slice: Slice A

## Purpose

This plan turns the [Catalogue Editor Boundary Spec Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-catalogue-editor-boundary) into implementation slices.

The boundary spec is complete.
This plan is the work queue for actually extracting catalogue editor runtime code.

## Execution Rules

- Implement one slice at a time.
- Do not combine runtime extraction with UI redesign, service endpoint changes, source schema changes, or generated catalogue schema changes.
- Keep route entry modules easy to find.
- Preserve existing create, edit, bulk, build-preview, publish, delete, and import workflows.
- Before each slice, state the write set and targeted checks.
- After each slice, update this plan with status, implementation notes, and verification results.

## Slice Queue

| Slice | Status | Primary target | Scope |
| --- | --- | --- | --- |
| A | planned next | `catalogue-editor-service-client.js` | Local-service wrapper functions over existing catalogue write endpoints |
| B | planned | `catalogue-editor-readiness.js` | Shared build/readiness item normalization and tone helpers |
| C | planned | `catalogue-editor-records.js` | Stable record hashing, display helpers, identity summaries, and changed-field summaries |
| D | planned | `catalogue-editor-modal-formatters.js` | Pure build-preview, publication, delete, and field-plan confirmation formatters |
| E | planned | `catalogue-moment-fields.js` | Route-local moment field module parity before sharing more moment editor behavior |
| F | deferred | `catalogue-editor-dirty-state.js` | Shared dirty-state and field-plan helpers after service/modal boundaries are cleaner |
| G | deferred | `catalogue-editor-embedded-items.js` | Work file/link embedded item helpers only if another route needs the pattern |

## Slice A: Service Client

Status:

- planned next

Target file:

- `assets/studio/js/catalogue-editor-service-client.js`

Primary route updates:

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`

Scope:

- wrap existing `CATALOGUE_WRITE_ENDPOINTS` calls behind named catalogue editor client functions
- keep request payloads and response handling unchanged
- keep route controllers responsible for timing, state updates, activity context construction, modal opening, and generated-data reload decisions
- keep `studio-transport.js` as the low-level transport owner

Candidate functions:

- `previewCatalogueBuild`
- `applyCatalogueBuild`
- `previewCataloguePublication`
- `applyCataloguePublication`
- `previewCatalogueDelete`
- `applyCatalogueDelete`
- `previewCatalogueProseImport`
- `applyCatalogueProseImport`
- record-family helpers for work, work detail, series, and moment create/save/bulk save

Acceptance checks:

- direct endpoint names no longer appear in route event handlers for migrated calls
- intercepted requests keep the same URLs and payloads as before
- route controllers still own state transitions and returned lookup-data application
- no modal HTML, field validation, or mode-state behavior changes are included

Targeted verification:

- syntax or module import smoke for changed JS
- work editor selected-record load smoke
- work-detail selected-record load smoke
- intercepted build-preview request from at least one editor
- intercepted save request from at least one editor
- intercepted publish/delete preview request if practical

## Slice B: Readiness Helpers

Status:

- planned

Target file:

- `assets/studio/js/catalogue-editor-readiness.js`

Scope:

- extract shared readiness item access, status tone selection, source/generated fallback labels, and compact readiness summary helpers
- keep actual DOM rendering route-local unless a later render boundary is justified
- preserve current text lookup through route `t(...)` callbacks or config-backed copy

Candidate functions:

- `catalogueReadinessTone`
- `catalogueReadinessItems`
- `catalogueReadinessItem`
- `cataloguePreviewFallback`
- `catalogueGeneratedStatusText`

Acceptance checks:

- readiness panels render equivalent item counts, labels, and tones
- missing generated/source fallback copy still comes from the same route text keys
- work, work-detail, series, and moment build-preview flows still load

## Slice C: Record Helpers

Status:

- planned

Target file:

- `assets/studio/js/catalogue-editor-records.js`

Scope:

- extract pure stable stringify and record hashing helpers
- extract shared display helpers only where output expectations are consistent
- extract changed-field summary helpers only if route-specific field definitions can stay injected

Candidate functions:

- `stableStringify`
- `computeRecordHash`
- `displayValue`
- `buildChangedFieldNames`
- small record identity summary helpers with route-specific label callbacks

Acceptance checks:

- dirty-state behavior does not change for unchanged records
- save buttons still enable after safe field edits
- bulk draft comparison remains stable for work and work-detail editors
- no field-module normalization is moved into the shared record helper

## Slice D: Modal Formatters

Status:

- planned

Target file:

- `assets/studio/js/catalogue-editor-modal-formatters.js`

Scope:

- extract pure text/HTML formatting for build-preview, publication, delete, and field-plan confirmation summaries
- keep `studio-modal.js` as the modal shell owner
- keep route controllers responsible for opening modals and performing writes

Candidate functions:

- `formatCatalogueBuildPreview`
- `formatCatalogueBuildPreviewModalHtml`
- `formatCataloguePublicationPreview`
- `formatCatalogueDeletePreview`
- `formatCatalogueFieldPlanList`

Acceptance checks:

- build-preview modal output remains equivalent for representative work and detail records
- publish/delete confirmations still show the same target labels and warning text
- formatter functions do not call write endpoints or mutate route state

## Slice E: Moment Field Module

Status:

- planned

Target file:

- `assets/studio/js/catalogue-moment-fields.js`

Scope:

- move moment field definitions, id normalization, filename normalization, draft read/record shaping, payload shaping, and validation into a route-local field module
- align moment editor ownership with work, work-detail, and series field modules
- do not share moment-specific import mode behavior

Acceptance checks:

- moment editor loads a selected moment and reaches ready state
- moment save payload is unchanged when intercepted
- moment import mode still previews and applies through the existing route-local workflow

## Slice F: Dirty State

Status:

- deferred

Target file:

- `assets/studio/js/catalogue-editor-dirty-state.js`

Scope:

- extract shared draft-vs-record comparison and field-plan summary behavior only after Slices A-D reduce controller noise
- keep field canonicalization and validation in field modules
- keep route-specific mode decisions route-local

Acceptance checks:

- unchanged selected records remain clean
- safe field edits mark the expected fields dirty
- bulk drafts produce the same changed-field summaries
- save/build/publish controls keep their existing enabled/disabled behavior

## Slice G: Embedded Items

Status:

- deferred

Target file:

- `assets/studio/js/catalogue-editor-embedded-items.js`

Scope:

- extract work file/link embedded item normalization or list helpers only if another catalogue route starts using the same pattern
- keep current work-editor embedded modal behavior route-local until reuse pressure exists

Acceptance checks:

- no extraction unless there is a second caller or a meaningful reduction in work-editor complexity
- embedded work files and links preserve current add/edit/delete behavior

## Runtime Smoke Map

Use this map proportionally after runtime extraction slices:

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

## Current Recommendation

Execute Slice A next.

Benefits:

- creates the transport boundary with the lowest UI risk
- removes endpoint-string knowledge from route event handlers
- gives later modal and readiness slices a cleaner route/controller surface

Risks:

- wrapper names can become too generic if they hide important record-family differences
- a broad first pass could touch all four editors, so the initial write set should migrate only the common endpoint families needed for the slice
- intercepted request checks are important because behavior changes may otherwise be visually invisible
