---
doc_id: site-request-catalogue-series-unified-editor
title: Catalogue Series Unified Editor Request
added_date: 2026-04-29
last_updated: 2026-04-29
parent_id: change-requests
sort_order: 130
---
# Catalogue Series Unified Editor Request

Status:

- specified
- task 1 locked
- task 2 implemented
- task 3 implemented
- task 4 implemented
- task 5 implemented
- task 6 paused

## Summary

This change request covers merging the current new-series and edit-series Studio implementations into one series editor route with explicit page modes.

Series is closer to works than work details:

- a series is a parent catalogue record, not a child record that must be created from another editor
- the current create route already creates a draft source record and then redirects into the main editor
- the main editor owns the richer workflow: member works, `primary_work_id`, staged prose import, scoped rebuild, save/build/delete, and publication validation

The desired direction is therefore to make `/studio/catalogue-series/` the normal route for creating and editing series records, while preserving the current publish boundary: a new series starts as draft and becomes publishable only after member works and a valid `primary_work_id` are set in edit mode.

## Goal

Unify series create and edit workflows around `/studio/catalogue-series/`.

The page should support:

- empty search/open state
- existing single-series edit mode
- `new` mode for creating one draft series

The target interaction should follow the work editor pattern:

- `New` sits near `Open`
- `?mode=new` opens create mode
- the top input becomes the new `series_id` input and is prefilled with the suggested next id when available
- shared field metadata, id normalization, validation, and payload shaping are factored before the route behavior changes
- successful create opens `/studio/catalogue-series/?series=<series_id>` in normal edit mode

Series does not need bulk mode in this request because the current series editor is single-record focused.

## Current State

Current edit route:

- `/studio/catalogue-series/`
- focused record selection uses `?series=<series_id>`
- source page: `studio/catalogue-series/index.md`
- controller: `assets/studio/js/catalogue-series-editor.js`
- docs: [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)

Current create route:

- `/studio/catalogue-new-series/`
- source page: `studio/catalogue-new-series/index.md`
- controller: `assets/studio/js/catalogue-new-series-editor.js`
- config route key: `catalogue_new_series_editor`
- docs: [New Catalogue Series](/docs/?scope=studio&doc=catalogue-new-series-editor)

The two scripts duplicate or partially duplicate:

- `series_id` normalization
- editable field metadata
- year validation
- draft record shaping
- create/save payload mapping
- local status and result handling

The create route currently supports:

- suggested next numeric series id
- duplicate series id validation
- required title validation
- draft-only creation through `POST /catalogue/series/create`
- redirect into the series editor after create

The edit route currently supports:

- search by id/title
- edit scalar series metadata
- edit membership by adding/removing works
- make a member work primary
- validate published series against `primary_work_id`
- staged prose readiness and import
- save with optional `Update site now`
- explicit follow-up update
- delete

## Proposed Direction

Make `/studio/catalogue-series/` the normal series route for both create and edit.

Locked route contract:

- `/studio/catalogue-series/` opens the unified editor in empty search/open state
- `/studio/catalogue-series/?series=<series_id>` opens existing series edit mode
- `/studio/catalogue-series/?mode=new` opens new-series mode
- `/studio/catalogue-new-series/` redirects immediately to `/studio/catalogue-series/?mode=new`
- clicking `New` enters new mode
- clicking `Open` from new mode exits new mode and interprets the input as normal series search/open input
- creating a draft series loads `/studio/catalogue-series/?series=<series_id>` in edit mode

The legacy `/studio/catalogue-new-series/` page should become a compatibility redirect after the unified route is stable. It should not remain a second functional implementation, so testing and documentation stay focused on the unified editor.

Catalogue dashboard copy should collapse `Create New Series` and `Edit Series` into one series-editor entry after the unified route lands.

## UX Principles

- Series is a top-level catalogue record, so global create from the series editor is appropriate.
- New mode creates source only; it does not publish or rebuild the public site.
- New mode should make the draft/publication boundary visible rather than implying that a new series can be published immediately.
- Member works, `primary_work_id`, staged prose import, delete, and build actions should remain disabled until the series source record exists.
- Existing series edit behavior should stay recognizably the same after the create-route migration.
- Active UI copy belongs in `studio_config.json` under `ui_text`.
- Route migration should prefer a redirect compatibility shell over keeping duplicate controllers alive.

## New Mode Behavior

In new mode:

- the top input label and placeholder describe new `series_id` entry, not search
- the input defaults to the suggested next series id when available
- duplicate series ids are rejected before create
- `title` is required
- `series_type` is visible, defaults to `primary`, and is required
- `series_type` renders as a config-backed Studio select with initial values `primary` and `holding`
- `series_type` is a client-side Studio constraint for now; the server remains permissive unless this becomes a formal data-model enum later
- `year` is required and must be a whole year
- `year_display` is required
- `status` is visible and fixed to `draft`
- `published_date` is blank and unavailable until edit mode
- `primary_work_id` is unavailable until the series exists and has member works
- member editing is disabled until the series exists
- staged prose import is disabled until the series exists
- `Delete`, `Update site now`, and `Import staged prose` are disabled until the series exists
- `Create` replaces `Save` as the primary mutation command
- create calls the existing `POST /catalogue/series/create` endpoint
- after create, the page opens the new series in edit mode

Publishing remains an edit-mode workflow:

- add member works
- choose or make a valid `primary_work_id`
- change status when ready
- save and update the site through the normal series editor flow

## Draft Series Visibility

The existing Catalogue Status page already lists non-published series records, but the work unification showed that draft create workflows benefit from an explicit recovery view.

Add draft-series visibility as part of this series unification unless the existing all-status list proves sufficient during implementation.

Preferred first implementation:

- extend Catalogue Status with `/studio/catalogue-status/?view=draft-series`
- add a `draft series` filter pill beside `draft works`
- link each row to `/studio/catalogue-series/?series=<series_id>`
- add a Catalogue dashboard review link if drafts need stronger discoverability

This should be implemented after the unified create flow, not before it, because the exact route and dashboard copy should settle first.

## Shared Field Contract

Create a shared series helper before adding `new` mode.

Preferred responsibilities:

- shared series field definitions
- mode-specific field sets
- `series_id` normalization
- work id normalization needed by membership and `primary_work_id`
- year/date/status validation helpers
- draft-from-record helper
- source-record payload mapping
- create payload mapping
- suggested next series id helper

The shared source field surface should include:

- `series_id`
- `title`
- `series_type`
- `status`
- `published_date`
- `year`
- `year_display`
- `primary_work_id`
- `sort_fields`
- `notes`

Mode rules:

- `series_id` is editable only in new mode
- `series_id` is read-only identity context in edit mode
- `series_type` should render as a select control using config-backed options
- `series_type` should default to `primary` in new mode
- `status` is fixed to `draft` during create
- `published_date` and `primary_work_id` are edit-mode fields
- published edit-mode saves require a valid `primary_work_id` that belongs to the series
- draft series may be saved without `primary_work_id`

Required create fields:

- `series_id`
- `title`
- `series_type`
- `year`
- `year_display`

Initial config values should reflect the two values currently present in source data:

- `primary`
- `holding`

Adding a future option should be a Studio config change. The write server does not currently enforce `series_type` as an enum, and that should remain acceptable for this phase because the field is rarely changed and can be made stricter later if needed.

## Accepted Decisions

Initial decisions for implementation:

- use `/studio/catalogue-series/?mode=new` as the unified create route
- keep `/studio/catalogue-series/?series=<series_id>` for edit mode
- add a `New` command next to `Open`
- prefill the suggested next `series_id` in new mode
- default `series_type` to `primary` in new mode
- require `title`, `series_type`, `year`, and `year_display` during create
- restrict Studio `series_type` entry to config-backed options, initially `primary` and `holding`
- create source-only draft series records
- do not update the public site during create
- keep member editing, prose import, build, and delete disabled until the series exists
- redirect `/studio/catalogue-new-series/` immediately after unified create mode is available
- retire `catalogue_new_series_editor` from active config once the legacy route is only a redirect
- update Catalogue Status with draft-series visibility unless implementation review shows the existing non-published series filter is sufficient

Endpoint decision:

- keep the existing `POST /catalogue/series/create` endpoint
- keep server-side `series_type` permissive for this phase; review only the required `series_type`, `year`, and `year_display` create-field contract if endpoint behavior needs adjustment

## Risks

Key risks:

- duplicating the work editor mode logic instead of extracting a clear series-specific helper
- accidentally enabling publish/build/prose/member actions before the new source record exists
- weakening the current rule that published series need a valid member `primary_work_id`
- losing the current membership editing behavior while refactoring the editor state model
- making the dashboard temporarily ambiguous if both create and edit links remain active
- adding draft-series status UI before the route model settles, causing another follow-up migration

Mitigations:

- factor helpers before new mode
- preserve the current edit-mode validation and membership tests
- make the retired route redirect rather than remain functional
- verify create, edit, membership, prose readiness, save/update, and delete paths separately

## Task Implementation Plan

### Task 1. Lock Series Mode Contract

Status:

- locked

Lock route and UI behavior before code changes.

Expected outputs:

- `/studio/catalogue-series/` opens empty search/open state
- `/studio/catalogue-series/?series=<series_id>` opens edit mode
- `/studio/catalogue-series/?mode=new` opens create mode
- `/studio/catalogue-new-series/` will redirect to `/studio/catalogue-series/?mode=new`
- `New` is a command button, not a separate dashboard-only workflow
- create is source-only and draft-only
- edit-only actions are disabled until a created record exists
- draft-series visibility scope is decided

Acceptance checks:

- mode contract is documented before implementation
- no current edit-mode behavior is removed from scope
- publish validation remains explicit

Implementation notes:

- Series follows the work-editor `New` command pattern because it is a top-level catalogue record.
- Series does not inherit the work-detail parent-scoped create pattern because it is not owned by a parent work.
- Series does not add bulk mode in this request; preserving the current single-series membership workflow is part of the locked scope.
- New mode creates only a draft source record. Publication readiness remains an edit-mode concern controlled by member works, `primary_work_id`, status, and the existing save/update flow.
- Draft-series visibility is in scope after unified create mode lands, with `/studio/catalogue-status/?view=draft-series` as the preferred first implementation unless implementation review shows the existing status page is enough.

### Task 2. Factor Shared Series Editor Helpers

Status:

- implemented

Extract shared series field metadata, normalization, validation, draft shaping, and payload helpers.

Expected outputs:

- new shared helper module for series source fields
- existing new-series and edit-series controllers consume shared helpers without behavior change
- create-only validation remains separate from edit-only publication validation
- membership-specific logic stays in the edit controller unless it is genuinely shared

Acceptance checks:

- create and edit paths consume the same field definitions where applicable
- helper extraction does not change routes or user-visible behavior
- JS syntax checks pass

Implementation notes:

- `assets/studio/js/catalogue-series-fields.js` now owns shared series field definitions, readonly field metadata, status/date constants, `series_id` and `work_id` normalization, draft shaping, create/save payload shaping, next-series-id suggestion, and create/edit validation helpers.
- `assets/studio/js/catalogue-new-series-editor.js` now consumes the shared new-series field list, create payload builder, id normalization, next-id suggestion, and create validation helper.
- `assets/studio/js/catalogue-series-editor.js` now consumes the shared edit field list, readonly field list, draft shaping, save payload builder, id normalization, and edit validation helper.
- This task intentionally preserves current route behavior and current create validation. The stricter required create fields and config-backed `series_type` select are specified for the unified new-mode implementation rather than this extraction pass.

### Task 3. Add New Mode To Series Editor

Status:

- implemented

Add `?mode=new` to `/studio/catalogue-series/`.

Expected behavior:

- `New` switches the top input to series-id entry
- suggested next id is prefilled
- create form uses the shared series field contract
- `status` is visible and draft-only
- member/prose/build/delete actions are disabled
- create writes through `POST /catalogue/series/create`
- successful create opens `/studio/catalogue-series/?series=<series_id>`

Acceptance checks:

- missing series id is blocked
- duplicate series id is blocked
- missing title is blocked
- missing or unknown `series_type` is blocked
- missing year is blocked
- invalid year is blocked
- missing `year_display` is blocked
- successful create writes a draft series source record
- create does not update the public site
- post-create edit mode allows member work assignment and normal publication preparation

Implementation notes:

- `/studio/catalogue-series/?mode=new` now opens draft-create mode in the main series editor.
- The editor has a `New` command beside `Open`.
- New mode uses the top input as the `series_id` input and pre-fills the suggested next id.
- `series_type` now renders as a config-backed select using `catalogue.series_type_options`, initially `primary` and `holding`.
- Create validation requires `series_id`, `title`, `series_type`, `year`, and `year_display`.
- `status` is visible and fixed to `draft`; `published_date`, `primary_work_id`, member editing, staged prose import, build, and delete remain disabled until the series exists.
- `Create` writes through `POST /catalogue/series/create` and then opens the created series in normal edit mode.
- Follow-up validation tightened edit-mode saves so existing series records also require `year` and `year_display` before `Save` is enabled.
- Follow-up fix: new-mode initialization now binds the member add button into editor state before refreshing the disabled member controls, so `/studio/catalogue-series/?mode=new` renders instead of falling through to the load-failed fallback.

### Task 4. Migrate Links, Routes, And Config

Status:

- implemented

Move active navigation to the unified series route.

Expected changes:

- Catalogue dashboard links to `/studio/catalogue-series/` as the single series editor entry
- the dashboard no longer presents `Create New Series` as a separate primary workflow
- `/studio/catalogue-new-series/` redirects to `/studio/catalogue-series/?mode=new`
- active config retires `catalogue_new_series_editor` route and UI text after the redirect is in place
- `catalogue-new-series-editor` docs become a compatibility note
- Studio Runtime, User Guide, and E2E checklist describe the unified route

Acceptance checks:

- old create route behavior is documented
- no active dashboard link points to a functional legacy create implementation
- direct edit links still open existing series records

Implementation notes:

- The Catalogue dashboard now uses one `Series Editor` entry at `/studio/catalogue-series/` instead of separate `Create New Series` and `Edit Series` entries.
- `/studio/catalogue-new-series/` is a compatibility redirect to `/studio/catalogue-series/?mode=new`.
- `catalogue_new_series_editor` was removed from the active Studio config route and UI text blocks.
- The New Catalogue Series doc now describes the redirect compatibility route rather than a standalone create implementation.
- Studio Runtime, User Guide, and the E2E checklist now point users and tests at the unified route.
- Follow-up fix: the save-time public update path is now disabled for draft series, and runtime series builds require the series and primary work to be published before public artifacts can be generated.

### Task 5. Add Draft Series Visibility

Status:

- implemented

Extend draft recovery to series if implementation review confirms the current status view is not enough.

Expected behavior:

- `/studio/catalogue-status/?view=draft-series` filters draft series records
- rows link to `/studio/catalogue-series/?series=<series_id>`
- the filter coexists cleanly with `?view=draft-works`
- dashboard review copy is updated if needed

Acceptance checks:

- newly created draft series can be found after source data refresh
- published series do not appear in the draft-series view
- non-series draft records remain available from the all-status view

Implementation notes:

- Catalogue Status now supports `/studio/catalogue-status/?view=draft-series`.
- The status filter bar includes a `draft series` pill beside `draft works`.
- Draft-series rows link directly to `/studio/catalogue-series/?series=<series_id>`.
- The Catalogue dashboard includes a `Review Draft Series` link in the Review group.

### Task 6. Update Documentation And Verification

Status:

- paused

Task 6 is paused rather than treated as complete. The remaining documentation and verification cleanup depends on the next catalogue-wide publication workflow pass, where save-time `Update site now` behavior is expected to become explicit publish/unpublish or rebuild commands.

Update docs and verification around the unified series route.

Expected docs:

- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [New Catalogue Series](/docs/?scope=studio&doc=catalogue-new-series-editor) as compatibility note or redirect documentation
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status), if draft-series visibility changes
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio E2E Checklist](/docs/?scope=studio&doc=studio-e2e-checklist)
- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules), if a reusable route-migration or create-mode rule changes
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

Verification should cover:

- empty route load
- `?series=<series_id>` load
- search and open
- `?mode=new` load
- create draft series
- post-create edit mode
- member add/remove
- make primary member
- save with and without update site
- explicit follow-up update
- staged prose readiness/import remains blocked or enabled correctly
- delete flow still works
- legacy create route redirect
- dashboard route entries
- draft-series visibility, if implemented

Acceptance checks:

- docs viewer payloads are rebuilt for Studio scope
- search payload is rebuilt if needed
- JS syntax checks pass
- browser smoke covers create/edit route migration
- sanitization scan passes

## Non-Goals

Out of scope:

- changing the canonical `series.json` schema
- editing series prose directly in the browser
- changing staged prose import source paths
- adding bulk series edit
- creating member works inline from the series editor
- changing work `series_ids` ordering semantics
- changing series delete cleanup behavior beyond preserving the existing flow

## Benefits

Expected benefits:

- one normal route for creating and continuing series work
- less duplication between new and edit series controllers
- consistent field labels, ordering, validation, and payload shaping
- clearer route model for dashboard and docs
- easier future catalogue-wide cleanup after work, detail, and series are unified

## Open Questions

- Should `title`, `series_type`, `year`, and `year_display` also become required for edit-mode saves, or only for create in this phase? Follow-up decision: `year` and `year_display` are now required for edit-mode saves; `title` and `series_type` remain unchanged in edit mode for this phase.
- If `series_type` becomes operationally important later, should the config-backed client options be promoted into a formal server-side data-model enum?
- Should `sort_fields` become required for create, or remain optional draft metadata?
- Should draft-series recovery get a dedicated `?view=draft-series` view immediately, or rely on the existing series status filter until usage proves it is needed?
- Should the series editor keep the suggested id as a prefilled input or present it as a selectable suggestion?
- Should the stale-after-save response-state rule fixed for work details also be applied to series during this implementation?

## Related References

- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [New Catalogue Series](/docs/?scope=studio&doc=catalogue-new-series-editor)
- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)
- [Catalogue Work Detail Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-detail-unified-editor)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
