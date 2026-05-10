---
doc_id: site-request-js-config-structural-review-catalogue-editor-extraction-plan
title: Catalogue Editor Extraction Plan
added_date: 2026-05-10
last_updated: "2026-05-10 16:50"
ui_status: done
parent_id: site-request-js-config-structural-review-catalogue-editor-boundary
sort_order: 20
hidden: false
---
# Catalogue Editor Extraction Plan

Status:

- planned execution sequence
- Slice A implemented
- Slice B implemented
- Slice C implemented
- Slice D implemented
- Slice E implemented
- Slice F implemented
- Slice G implemented
- catalogue editor extraction sequence complete

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
| A | implemented | `catalogue-editor-service-client.js` | Local-service wrapper functions over existing catalogue write endpoints |
| B | implemented | `catalogue-editor-readiness.js` | Shared build/readiness item normalization and tone helpers |
| C | implemented | `catalogue-editor-records.js` | Stable record hashing, display helpers, identity summaries, and changed-field summaries |
| D | implemented | `catalogue-editor-modal-formatters.js` | Pure build-preview, publication, delete, and field-plan confirmation formatters |
| E | implemented | `catalogue-moment-fields.js` | Route-local moment field module parity before sharing more moment editor behavior |
| F | implemented | `catalogue-editor-dirty-state.js` | Shared dirty-state and field-plan helpers after service/modal boundaries are cleaner |
| G | implemented | `catalogue-editor-embedded-items.js` | Work file/link embedded item helpers only if another route needs the pattern |

## Slice A: Service Client

Status:

- implemented

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
- route controllers still own state transitions and returned lookup-data application
- no modal HTML, field validation, or mode-state behavior changes are included

Implementation notes:

- `assets/studio/js/catalogue-editor-service-client.js` now owns named wrappers over the existing catalogue write endpoints.
- Work, work-detail, series, and moment editors import the service client for create/save/bulk-save, build preview/apply, publication preview/apply, delete preview/apply, prose import, and moment import/preview calls.
- `studio-transport.js` remains the low-level endpoint and `postJson` owner.
- Route controllers still build payloads, activity contexts, modal copy, state transitions, and generated-data reload decisions.
- Direct `CATALOGUE_WRITE_ENDPOINTS` and `postJson` usage was removed from the migrated route controllers.

Targeted verification:

- `node --check` passed for the new service client and the four migrated route controllers.
- A targeted search found no remaining `postJson(` or `CATALOGUE_WRITE_ENDPOINTS` references in the migrated route controllers.
- Jekyll build passed.
- Static Playwright smoke passed for selected work, work-detail, series, and moment editor routes against `_site`; all four reached route-ready state with no page errors and no failed Studio JS module requests.
- The first Playwright launch failed inside the Codex sandbox; the same check passed when rerun with escalated permissions as required by the local validation guidance.

## Slice B: Readiness Helpers

Status:

- implemented

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

Implementation notes:

- `assets/studio/js/catalogue-editor-readiness.js` now owns shared readiness item selection, item summary normalization, status tone selection, media-preview fallback state/text shaping, and compact generated-status text formatting.
- Work, work-detail, series, and moment editors import the helper while keeping DOM rendering, route state, action enablement, and config-backed copy local.
- Detail readiness keeps its route-specific `detail_media` filtering through an injected key filter.
- Moment readiness preserves its stricter `missing_file` error tone through an injected tone option and keeps import-mode behavior route-local.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-editor-readiness.js` and the four migrated catalogue editor controllers.
- A targeted search found no remaining local `toneForReadinessStatus`, `getReadinessItems`, `getReadinessItem`, `previewFallback`, or `generatedStatusText` helpers in the migrated route controllers.
- Studio docs payloads and the Studio search index were rebuilt.
- Jekyll build passed.
- Static Playwright smoke passed for work, work-detail, series, and moment editor routes against `_site`; all four reached route-ready state with no page errors and no failed Studio JS module requests.

## Slice C: Record Helpers

Status:

- implemented

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

Implementation notes:

- `assets/studio/js/catalogue-editor-records.js` now owns deterministic record stringification, record hashing, display-value fallback formatting, record equality, and injected changed-field name comparison.
- Work, work-detail, series, and moment editors import the shared record helpers instead of carrying duplicate local hash/stringify implementations.
- Work editor changed-field summaries now use the injected comparison helper while preserving route-local field definitions, scalar canonicalization, and embedded downloads/links comparison.
- Series editor still owns membership semantics and imports shared stable stringification for member-series comparisons.
- Moment editor preserves its existing hyphen fallback display text by passing an explicit `emptyText` option.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-editor-records.js` and the four migrated catalogue editor controllers.
- A targeted search found no remaining local `stableStringify`, `computeRecordHash`, or `recordsEqual` helper definitions in the migrated route controllers.
- Studio docs payloads and the Studio search index were rebuilt.
- Jekyll build passed.
- Static Playwright smoke passed for work, work-detail, series, and moment editor routes against `_site`; with the local catalogue service unavailable, all four reached offline route-ready state with no page errors and no failed Studio JS module requests.

## Slice D: Modal Formatters

Status:

- implemented

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

Implementation notes:

- `assets/studio/js/catalogue-editor-modal-formatters.js` now owns pure formatting for catalogue build-preview summary text, work build-preview modal HTML, field-plan lists, unpublish confirmation text, and delete confirmation text.
- Work, work-detail, series, and moment editors import the formatter helpers while keeping modal shell rendering, `window.confirm`, request payloads, route state mutation, and write endpoint calls in the route controllers.
- The formatter module receives a route text callback so existing `studio_config.json` UI copy remains the source for labels and confirmation text.
- Moment build-preview formatting keeps its moment-specific `moment_ids` template through an explicit formatter target option.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-editor-modal-formatters.js` and the four migrated catalogue editor controllers.
- A targeted search found no remaining local `formatBuildPreview`, `fieldPlanList`, or `formatBuildPreviewModalHtml` helper definitions in the migrated route controllers.
- Formatter extraction stayed pure: the new module does not call catalogue service endpoints, `window.confirm`, or route-state mutation helpers.
- Studio docs payloads and the Studio search index were rebuilt.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build` because local `bin/dev-studio` was already running.
- Static Playwright smoke passed for work, work-detail, series, and moment editor routes against the built site; all four reached route-ready state with no page errors and no failed Studio JS module requests.
- The first Playwright launch failed inside the Codex sandbox; the same check passed when rerun with escalated permissions as required by the local validation guidance.

## Slice E: Moment Field Module

Status:

- implemented

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

Implementation notes:

- `assets/studio/js/catalogue-moment-fields.js` now owns moment field definitions, moment id and filename normalization, record normalization, draft reads, save payload shaping, and draft validation.
- `assets/studio/js/catalogue-moment-editor.js` imports the moment field module while keeping import-mode workflow control, service calls, route state, readiness rendering, and publication/delete behavior local.
- Moment record shaping preserves the existing default source-image behavior: an explicit `source_image_file` is omitted when it matches `{moment_id}.jpg`.
- The save request is still assembled by the route controller with the same activity context; the field module shapes only the moment-specific payload fields.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-moment-fields.js` and `assets/studio/js/catalogue-moment-editor.js`.
- `node --check` also passed for the other catalogue editor controllers: work, work-detail, and series.
- A targeted search found no remaining local `normalizeRecord`, `DATE_RE`, `normalizeText`, `normalizeMomentId`, or `normalizeMomentFilename` definitions in the moment editor controller.
- A direct module check confirmed moment id and filename normalization, default source-image omission, save payload shaping, and validation behavior for a representative published moment draft.
- Studio docs payloads were rebuilt for the Studio scope and the Studio search index rebuild was checked.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed for the built moment editor selected-record route; `?moment=keys` reached `single` mode with `recordLoaded` true, no page errors, and no failed Studio JS module requests.
- The first Playwright launch failed inside the Codex sandbox; the same check passed when rerun with escalated permissions as required by the local validation guidance.

## Slice F: Dirty State

Status:

- implemented

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

Implementation notes:

- `assets/studio/js/catalogue-editor-dirty-state.js` now owns pure dirty-field comparison, shared new/bulk/single dirty-state branching, dirty-warning text shaping, and common save/delete disabled-state predicates.
- Work, work-detail, and series editors import the helper for draft dirty checks, warning copy, and save/delete control state while keeping field normalization, validation, payload shaping, build-preview behavior, and publication rules route-local.
- Work editor still injects embedded downloads/links comparison, and series editor still injects membership comparison, so route-specific semantics remain outside the shared helper.
- Moment editor uses only the shared warning/delete predicates because moment save enablement intentionally remains route-specific.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-editor-dirty-state.js` and the four catalogue editor controllers.
- A direct module check confirmed unchanged single-record drafts stay clean, changed drafts become dirty, touched bulk fields become dirty, warning text is suppressed only for new mode, and common save/delete disabled predicates preserve representative enabled/disabled outcomes.
- Studio docs payloads and the Studio search index were rebuilt for the Studio scope.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed for work, work-detail, series, and moment editor routes against the built site on desktop and mobile viewports; all routes reached route-ready state with no page errors and no failed Studio JS module requests.
- The first Playwright launch failed inside the Codex sandbox; the same checks passed when rerun with escalated permissions as required by the local validation guidance.

## Slice G: Embedded Items

Status:

- implemented

Target file:

- `assets/studio/js/catalogue-editor-embedded-items.js`

Scope:

- extract work file/link embedded item normalization or list helpers only if another catalogue route starts using the same pattern
- keep current work-editor embedded modal behavior route-local until reuse pressure exists

Acceptance checks:

- no extraction unless there is a second caller or a meaningful reduction in work-editor complexity
- embedded work files and links preserve current add/edit/delete behavior

Implementation notes:

- `assets/studio/js/catalogue-editor-embedded-items.js` now owns work download/link field definitions, row HTML formatting, modal descriptor construction, add/edit entry shaping, delete-confirmation text shaping, and embedded download/link validation.
- `assets/studio/js/catalogue-work-editor.js` imports the helper while keeping DOM section ownership, modal host rendering, keyboard/click event wiring, draft assignment, dirty-state updates, and save/build behavior route-local.
- The helper imports the existing work field normalization utilities so embedded entry normalization stays consistent with work source payload shaping.
- No other route currently consumes the work file/link pattern; the extraction was kept work-owned and did not introduce a generic catalogue embedded-item workflow.

Targeted verification:

- `node --check` passed for `assets/studio/js/catalogue-editor-embedded-items.js` and the four catalogue editor controllers.
- A direct module check confirmed download/link modal descriptors, row action attributes, disabled row actions, add-entry shaping, validation messages, delete-confirmation copy, and embedded validation error keys.
- Studio docs payloads and the Studio search index were rebuilt for the Studio scope.
- Jekyll build passed with `--destination /tmp/dlf-jekyll-build`.
- Static Playwright smoke passed for work, work-detail, series, and moment editor routes against the built site; all routes reached route-ready state with no page errors and no failed Studio JS module requests, and the work editor loaded `catalogue-editor-embedded-items.js`.
- Focused mobile Playwright smoke passed for the work editor route, including `catalogue-editor-embedded-items.js` loading.

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

Catalogue editor extraction is complete.
Return to the parent [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review) for the next top-level slice.

Benefits:

- Slice G removes work file/link embedded item formatting and validation details from the route controller without changing modal or save orchestration.
- The work editor keeps route-specific ownership where it matters: DOM sections, modal host lifecycle, draft mutation timing, and dirty-state updates.
- The full Catalogue editor extraction sequence now has explicit owners for service calls, readiness, record helpers, modal formatters, moment fields, dirty state, and embedded work items.

Risks:

- moment import mode remains route-specific and should stay out of shared catalogue editor helpers
- save payload equivalence should continue to be checked if validation helpers are extracted later
- embedded work files and links should remain work-owned unless a second caller appears
