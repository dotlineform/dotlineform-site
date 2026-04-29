---
doc_id: site-request-catalogue-work-detail-unified-editor
title: Catalogue Work Detail Unified Editor Request
added_date: 2026-04-28
last_updated: 2026-04-29
parent_id: change-requests
sort_order: 120
---
# Catalogue Work Detail Unified Editor Request

Status:

- implemented
- wider cleanup will be done after series implementation

## Summary

This change request covers merging the current new-work-detail and edit-work-detail Studio implementations into one shared detail editor route and controller.

Work details are different from works and series. A work detail is always understood through an existing parent work. The user should normally find, create, and edit details from the work page rather than searching for isolated detail records from the dashboard.

The goal is therefore not to copy the full work-editor `New` button pattern. The goal is to keep the parent-work navigation model while still gaining the implementation benefits of one form, one validation model, one route contract, and one UI design.

## Current State

Current edit route:

- `/studio/catalogue-work-detail/`
- focused record selection uses `?detail=<detail_uid>`
- source page: `studio/catalogue-work-detail/index.md`
- controller: `assets/studio/js/catalogue-work-detail-editor.js`
- docs: [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)

Current create route:

- `/studio/catalogue-new-work-detail/`
- focused create flow accepts `?work=<work_id>`
- source page: `studio/catalogue-new-work-detail/index.md`
- controller: `assets/studio/js/catalogue-new-work-detail-editor.js`
- docs: [New Catalogue Work Detail](/docs/?scope=studio&doc=catalogue-new-work-detail-editor)

The work page already provides the right user entry points:

- click `new work detail` from `/studio/catalogue-work/?work=<work_id>`
- click an existing detail row from the work page to edit it

## Proposed Direction

Keep work-detail workflows parent-context-first.

Target route contract:

- `/studio/catalogue-work-detail/?detail=<detail_uid>` opens existing detail edit mode
- `/studio/catalogue-work-detail/?work=<work_id>&mode=new` opens new detail mode for that parent work
- `/studio/catalogue-work-detail/` opens an empty exact-detail search surface for maintenance cases where the public work-detail page already exposes the detail id
- `/studio/catalogue-new-work-detail/?work=<work_id>` redirects to `/studio/catalogue-work-detail/?work=<work_id>&mode=new`

The direct empty state should include a clear navigation link back to the work editor. This keeps direct correction workflows available without turning detail creation into a dashboard-first global workflow.

## UX Principles

- The work page remains the normal place to choose or create a detail.
- New detail mode is entered with an existing parent work already known.
- The parent work context should be visible and locked in new mode.
- The detail editor should not require the user to search globally for a parent work during normal create.
- The route can still support focused edit loads by `detail_uid` for direct links and activity/status navigation.
- The direct empty route remains valid for exact-id maintenance edits because `detail_id` is surfaced on public work detail pages.
- The direct empty route should also provide an obvious path back to the parent work editor.
- The dashboard should not promote `Create New Detail` as a primary workflow once the parent-driven route is unified.

## New Mode Behavior

In new mode:

- parent `work_id` is required in the URL
- parent work identity is shown read-only
- the next available `detail_id` can be suggested or prefilled
- detail-specific source fields are editable
- `status` is visible and should default to `draft`
- edit-only panels and commands are disabled until the detail exists
- create writes source JSON only through the existing work-detail create endpoint
- after create, the page opens the created detail in normal edit mode

The new mode should not publish or rebuild the public site during create. Once the detail exists and the page is in edit mode, the normal save/update workflow can publish parent work output.

## Route Migration

Once the unified route is stable:

- retire `/studio/catalogue-new-work-detail/` as an active implementation route
- redirect old links immediately to the unified new-detail mode
- remove active `catalogue_new_work_detail_editor` UI text/config that only served the legacy route, if no remaining runtime needs it
- update the work editor's `new work detail` link to point at `/studio/catalogue-work-detail/?work=<work_id>&mode=new`
- update dashboard copy so detail creation is framed as parent-work navigation rather than a standalone create route

## Benefits

Expected benefits:

- one detail form and design surface
- less duplication between new and edit detail controllers
- consistent field ordering, labels, validation, and status handling
- simpler route model for links from the work page
- clearer path for testing work-detail create/edit without comparing legacy and new pages
- preserves the user workflow where details are found through their parent work

## Risks

Key risks:

- over-generalizing the work `New` mode pattern and making details feel like standalone records
- losing the parent-work context that makes detail creation understandable
- breaking existing links from the work page to detail edit/create flows
- changing bulk detail edit behavior while trying to merge create mode
- accidentally enabling build/update/delete actions before a new detail source record exists

The main mitigation is to treat route unification as an implementation consolidation, not a new global detail-discovery workflow.

## Task Implementation Plan

### Task 1. Define Detail Mode Contract

Status:

- specified

Lock the route and mode contract before code changes.

Expected outputs:

- `?detail=<detail_uid>` opens existing detail edit mode
- `?work=<work_id>&mode=new` opens parent-scoped create mode
- direct `/studio/catalogue-work-detail/` remains an empty exact-detail search mode for maintenance edits
- the direct empty route includes a navigation link to the work editor
- document disabled/read-only surfaces in new mode
- detail `status` is exposed and draft-defaulted during create

Acceptance checks:

- parent work context is required for new mode
- existing direct detail links remain valid
- direct exact-id maintenance editing remains available
- no global detail-create workflow is introduced

### Task 2. Factor Shared Detail Editor Helpers

Status:

- implemented

Extract shared detail field metadata, draft shaping, id normalization, validation, and create/save payload helpers before adding new mode.

Expected outputs:

- shared helper module for work-detail source fields
- existing new and edit controllers consume shared helpers without behavior change
- existing validation and payload shape stay equivalent

Acceptance checks:

- create and edit paths consume the same field definitions
- helper extraction does not change route behavior
- JS syntax checks pass

Implementation notes:

- `assets/studio/js/catalogue-work-detail-fields.js` now owns shared work-detail source field definitions, id normalization, draft shaping, create validation, next-detail-id suggestion, and create/save payload builders.
- `assets/studio/js/catalogue-work-detail-editor.js` and `assets/studio/js/catalogue-new-work-detail-editor.js` consume the shared helper while preserving their existing route behavior.

### Task 3. Add New Mode To Work Detail Editor

Status:

- implemented

Add parent-scoped new mode to `/studio/catalogue-work-detail/`.

Expected behavior:

- `/studio/catalogue-work-detail/?work=<work_id>&mode=new` opens a create form
- parent work context is shown read-only
- suggested detail id is shown or prefilled
- create writes a draft detail source record
- successful create loads `/studio/catalogue-work-detail/?detail=<detail_uid>`
- build/update/delete actions remain disabled before create

Acceptance checks:

- missing or unknown parent work is blocked clearly
- duplicate detail ids are blocked
- successful create opens normal edit mode
- create does not update the public site

Implementation notes:

- `/studio/catalogue-work-detail/?work=<work_id>&mode=new` now opens parent-scoped create mode on the main detail editor route.
- New mode shows the locked parent work, prefilled suggested `detail_id`, visible draft `status`, and editable detail source fields.
- `Create` writes through `POST /catalogue/work-detail/create` and then loads `/studio/catalogue-work-detail/?detail=<detail_uid>` in normal edit mode.

### Task 4. Migrate Links, Routes, And Config

Status:

- implemented

Move active navigation to the unified detail route.

Expected changes:

- work editor `new work detail` links to `/studio/catalogue-work-detail/?work=<work_id>&mode=new`
- existing detail rows continue to link to `/studio/catalogue-work-detail/?detail=<detail_uid>`
- `/studio/catalogue-new-work-detail/` redirects to the unified route when `work` is supplied
- Studio config retires legacy new-detail keys when no longer needed
- dashboard copy stops presenting detail creation as a standalone primary workflow

Acceptance checks:

- old route behavior is documented
- no active dashboard path points users into the retired implementation
- work-page create/edit navigation works without returning to the dashboard

Implementation notes:

- the work editor `new work detail` link now points at `/studio/catalogue-work-detail/?work=<work_id>&mode=new`
- `/studio/catalogue-new-work-detail/` is a compatibility redirect to the unified detail route when `work` is supplied, or to the work editor when missing
- active Studio config no longer includes the legacy `catalogue_new_work_detail_editor` route or UI text block
- the Catalogue dashboard no longer presents detail creation as a standalone create workflow

### Task 5. Update Documentation And Verification

Status:

- implemented

Update docs and verification around the unified detail route.

Expected docs:

- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [New Catalogue Work Detail](/docs/?scope=studio&doc=catalogue-new-work-detail-editor) as compatibility note or redirect documentation
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- Studio E2E checklist
- Studio UI rules if a reusable parent-scoped create/edit rule emerges

Acceptance checks:

- docs viewer generated payloads are rebuilt for the Studio scope
- search payload is rebuilt if needed
- browser smoke covers work page -> new detail -> created detail edit
- browser smoke covers work page -> existing detail edit
- sanitization scan passes

## Non-Goals

Out of scope:

- creating work details inline inside the work editor
- making work details first-class dashboard create records
- changing the canonical `work_details.json` schema
- changing detail media generation behavior
- changing bulk detail edit behavior
- changing parent work rebuild scope

## Open Questions

- Should new mode prefill the suggested next `detail_id`, or show it as a selectable suggestion?
- Should the legacy `/studio/catalogue-new-work-detail/` route preserve `?work=<work_id>` only, or also handle missing `work` by redirecting to the work editor?
- Should dashboard detail links move entirely under work editor guidance, or keep a secondary maintenance link to the detail editor?
- Should the same parent-scoped pattern later apply to other child records if they reappear?

## Related References

- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [New Catalogue Work Detail](/docs/?scope=studio&doc=catalogue-new-work-detail-editor)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
