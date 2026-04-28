---
doc_id: site-request-catalogue-work-unified-editor
title: "Catalogue Work Unified Editor Request"
added_date: 2026-04-28
last_updated: 2026-04-28
parent_id: site-docs
sort_order: 154
---
# Catalogue Work Unified Editor Request

Status:

- pending discussion

## Summary

This change request covers combining the current new-work and edit-work Studio flows into one work editor route with explicit page modes.

The current split creates two related but separate surfaces:

- `/studio/catalogue-work/` edits existing work source records and supports single-record mode, bulk mode, save/build/delete actions, previews, readiness panels, details, downloads, and links.
- `/studio/catalogue-new-work/` creates draft work source records with a smaller field set and redirects into the work editor after create.

The desired direction is a unified work editor where the user can switch between opening existing works and creating a new draft work without leaving the page.

If this works well for works, the intended follow-up direction is to reuse the same explicit mode pattern for series and moments rather than treating the work editor as a one-off.

## Goal

Unify the work create and edit workflows around `/studio/catalogue-work/`.

The page should support:

- `edit` mode for one existing work
- `bulk` mode for the current multi-work edit behavior
- `new` mode for creating one draft work

In the target interaction, a `New` button sits next to `Open`. When selected, the existing search input becomes the new work id input, ideally prefilled with the suggested next work id. The field structure remains shared with edit mode, while controls and panels that do not apply to the new-record state are disabled or hidden.

## Current State

Current edit route:

- `studio/catalogue-work/index.md`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/data/studio_config.json` key `catalogue_work_editor`
- docs in `_docs_src/catalogue-work-editor.md`

Current create route:

- `studio/catalogue-new-work/index.md`
- `assets/studio/js/catalogue-new-work-editor.js`
- `assets/studio/data/studio_config.json` key `catalogue_new_work_editor`
- docs in `_docs_src/catalogue-new-work-editor.md`

The two scripts currently duplicate several concepts:

- work id normalization
- series id normalization
- editable work field definitions
- number and series validation
- draft payload construction
- command status and result handling

The create route also has behavior that the edit route does not yet model:

- duplicate work id validation
- required title validation
- suggested next work id
- create endpoint submission through `POST /catalogue/work/create`
- redirect into the work editor after create

## Proposed Direction

Make `/studio/catalogue-work/` the normal work route for both create and edit.

The page mode should be explicit rather than inferred only from whether a current record exists.

Suggested mode transitions:

- opening the page with no query starts in an empty edit/search state
- opening `?work=<work_id>` loads edit mode for that work
- opening a comma/range selection enters bulk mode
- clicking `New` enters new mode
- clicking `Open` from new mode returns the input to open/search behavior
- creating a draft work loads the new record into edit mode on the same route

The existing `/studio/catalogue-new-work/` route should redirect immediately to the unified work editor once the implementation lands. The legacy new-work surface should not remain functional in parallel, so testing stays focused on the new surface rather than comparing new and legacy behavior.

Catalogue dashboard copy should collapse `Create New Work` and `Edit Work` into one work-editor entry after the unified route is available.

Because new mode creates source-only draft works without publishing them, the workflow also needs a clear way to reopen unpublished work later. Add a draft-works listing surface so draft records are visible even when they were created in an earlier session.

## Pattern Rollout

Works should be the proving ground for the explicit mode pattern.

After the work editor has a stable create/edit/bulk mode contract, the same approach should be considered for:

- series create/edit flows
- moment import/edit flows, if the product distinction between import and routine metadata editing remains clear

The rollout should not automatically merge every create route. Each catalogue family should first check whether `new` means the same thing as routine create, staged import, or a more specialized ingestion flow.

For example:

- series has a closer match to the work create/edit split and may be a straightforward candidate
- moments currently have a staged-import workflow as well as an edit route, so the mode pattern may need to distinguish `new` from `import`

The goal is to establish a shared Studio mode pattern without hiding meaningful workflow differences between catalogue record families.

## Draft Work Visibility

The unified create flow intentionally allows a work to be created as a draft and left unpublished.

That creates a workflow requirement: Studio should make draft works easy to find after the create session ends.

Add a draft-works list that:

- lists works where `status = draft`
- links each row to `/studio/catalogue-work/?work=<work_id>`
- shows enough context to identify the work, such as work id, title, year display, and series ids
- appears from the catalogue dashboard or another obvious Studio catalogue navigation point
- can later be reused or extended for draft series and draft moments if the mode pattern rolls out there

This should be treated as part of the unified workflow rather than a separate reporting nice-to-have. Otherwise source-only draft creation creates a risk that records are forgotten before they are completed, published, or deleted.

Implementation options:

- extend the existing Catalogue Status route with a draft-focused view/filter
- add a small dedicated Draft Works route
- add a draft section to the catalogue dashboard if the list stays compact

The preferred option should be decided during implementation based on which route gives the clearest workflow with the least duplicated list UI.

## New Mode Behavior

In new mode:

- the top input label and placeholder should describe a new work id, not search
- a single top input with a clear mode label is enough
- the search popup should be hidden
- bulk syntax should be invalid
- the input should default to the suggested next work id when available
- duplicate work ids should be rejected before create
- `title`, `year`, `year_display`, and `series_ids` are required
- `status` should be visible in the field structure, with `draft` as the create default
- the create action itself should still create a draft source record and should not update the public site
- `published_date` should default to blank/null
- `Create` should replace `Save` as the primary mutation command
- create should call the existing `POST /catalogue/work/create` endpoint
- after a successful create, the page should load the new work in edit mode
- publishing happens after create, in edit mode, through the normal save/update-site flow
- draft works can be deleted from edit mode

Edit-only surfaces should be disabled while no created record exists:

- `Delete`
- `Update site now`
- generated readonly dimensions
- public work link
- current preview
- work media readiness
- work prose readiness
- detail navigation
- download editing
- link editing

The page should still show focused next-step guidance in the summary rail so the user understands what will become available after create.

## Shared Field Contract

The first implementation should create the shared infrastructure before adding `new` mode, even if that makes the first change larger.

It should avoid a third copy of field definitions.

Preferred direction:

- extract or centralize the shared work field list
- keep mode-specific field rules alongside the shared list
- use one field renderer for work metadata
- use one normalization/payload mapping path where possible
- keep create-only validation separate from edit-only and bulk-only validation

The shared work metadata surface should include the current edit fields:

- `status`
- `published_date`
- `series_ids`
- `project_folder`
- `project_filename`
- `title`
- `year`
- `year_display`
- `medium_type`
- `medium_caption`
- `duration`
- `height_cm`
- `width_cm`
- `depth_cm`
- `storage_location`
- `notes`
- `provenance`
- `artist`

The work id should remain special:

- in edit and bulk mode it is selection context, not an editable metadata field
- in new mode it is the focused id input used to create the source record

Required work source fields:

- `work_id`
- `title`
- `year`
- `year_display`
- `series_ids`

The required-field rule should apply to create and edit saves. Bulk mode should not allow required fields to be cleared across selected records. The implementation should explicitly decide how to report any pre-existing records that are already missing required values.

## Accepted Decisions

Decisions from the initial review:

- build the shared work-editor helper infrastructure before adding `new` mode
- use one top input with clear mode labeling
- use `New` as a command button, not a segmented control
- keep bulk mode reachable from the same input
- require `work_id`, `title`, `year`, `year_display`, and `series_ids`
- expose `status` in new mode, with draft as the create default
- disable edit-only surfaces in new mode rather than hiding them
- redirect `/studio/catalogue-new-work/` immediately once the unified route is implemented
- collapse dashboard entries to one work-editor entry
- retire `catalogue_new_work_editor` from config rather than keeping a transition key
- do not keep the legacy new-work page functional for smoke testing
- keep new-mode create as source-only draft creation with no automatic site update
- add a draft-works listing surface so unpublished draft works remain visible after the create session

Endpoint decision:

- the `POST /catalogue/work/create` contract needs review during implementation because required fields and visible `status` may affect payload validation
- the preferred first-pass behavior is still draft-only creation followed by normal edit-mode save/update-site actions

## Risks For Discussion

### State Complexity

The current work editor already manages several states:

- no record loaded
- single-record edit
- bulk edit
- dirty source changes
- save in progress
- build pending
- build in progress
- delete in progress
- modal add/edit/delete flows for downloads and links

Adding new mode directly into this script could make the page harder to reason about unless the mode model is made explicit and the shared work-field logic is factored first.

Discussion point:

- Should the implementation first extract shared work-editor helpers before adding `new` mode, even if that makes the change larger?

Decision:

- yes; get the shared infrastructure done first

### Input Role Switching

The same top input would do different jobs:

- search/open existing work ids
- parse bulk selections
- accept a new work id

That supports the desired workflow, but it also raises UI clarity risks.

Discussion points:

- Is a single input with clear mode label enough?
- Should `New` be a mode toggle, a segmented control, or a command button?
- Should bulk mode remain reachable from the same input after this change?

Decisions:

- one input with a clear mode label is enough
- `New` should be a command button
- bulk mode should remain reachable from the same input

### Create Validation Versus Edit Validation

Create mode currently requires a title and blocks duplicate work ids. Edit mode allows broader source maintenance and does not require title in the same way.

Discussion points:

- Should title remain required for new draft works?
- Should any other field become required at create time?
- Should create mode expose `status`, or should `draft` remain implicit until the record exists?

Decisions:

- title should be required for all works, not only new draft works
- `work_id`, `title`, `year`, `year_display`, and `series_ids` should be required fields
- create mode should expose `status`
- new-mode create should still produce a draft and should not update the public site

### Hidden Versus Disabled Controls

Some controls do not apply until a record exists. Hiding them keeps new mode clean, while disabling them makes the full workflow more discoverable.

Discussion point:

- For each edit-only surface, should new mode hide it, disable it, or show a readonly placeholder?

Decision:

- disable edit-only surfaces in new mode

### Compatibility And Navigation

Existing docs, dashboard links, and config route keys point to `/studio/catalogue-new-work/`.

Discussion points:

- Should the old route redirect immediately?
- Should dashboard copy collapse `Create New Work` and `Edit Work` into a single `Work Editor` entry?
- Should `catalogue_new_work_editor` remain in config during a transition?

Decisions:

- redirect the old route immediately
- collapse the dashboard copy into a single work-editor entry
- retire `catalogue_new_work_editor` as soon as the unified route lands

### Testing Blast Radius

The change touches a high-use Studio route and a local write flow.

Discussion points:

- Should the first implementation keep `/studio/catalogue-new-work/` functional until the unified route has been smoke-tested?
- Should the create endpoint behavior remain unchanged in the first pass?
- Should unified create mode avoid automatic site update until after the first save in edit mode?

Decisions:

- do not keep `/studio/catalogue-new-work/` functional in parallel
- create endpoint behavior needs implementation review because of the required-field and visible-status decisions
- unified create mode should avoid automatic site update
- new mode only creates a draft, then switches to edit mode where the work can later be published through the normal save/update-site path

### Draft Follow-Up Visibility

Source-only create makes it possible to create a draft work and leave it unpublished.

Discussion point:

- How should Studio make those draft works visible after the original session?

Decision:

- provide a draft-works list that links back into the unified work editor
- decide during implementation whether this belongs in Catalogue Status, a dedicated Draft Works route, or the catalogue dashboard

## Proposed Implementation Tasks

### Task 1. Decide Mode Contract

Status:

- decisions recorded

Decide the route and UI contract before editing code:

- supported query shape for new mode, such as `?mode=new`
- initial no-query behavior
- `New` and `Open` control behavior
- hidden versus disabled edit-only surfaces
- compatibility behavior for `/studio/catalogue-new-work/`

Acceptance checks:

- mode transitions are documented before implementation
- risks above have explicit decisions or accepted follow-up tasks
- required-field and create-endpoint questions have implementation notes

### Task 2. Factor Shared Work Editor Logic

Status:

- proposed

Create a shared work-editor field/model layer before merging page behavior.

Candidate shared responsibilities:

- field definitions
- field rendering metadata
- work id and series id normalization
- series parsing
- scalar validation helpers
- create/edit payload shaping helpers

Acceptance checks:

- create and edit paths consume the same field definitions
- create-only and edit-only validation remain visibly separate
- no behavior changes are introduced beyond the refactor
- shared helpers land before `new` mode is added to the route

### Task 3. Add New Mode To Work Editor

Status:

- proposed

Add new mode to `/studio/catalogue-work/`.

Expected behavior:

- `New` switches the top input to work-id entry
- suggested next id is prefilled when available
- `Create` appears as the primary mutation action
- edit-only panels are disabled according to the decided contract
- successful create loads the created work into edit mode on the same route

Acceptance checks:

- duplicate ids are blocked
- missing work id is blocked
- missing `title`, `year`, `year_display`, or `series_ids` is blocked
- successful create writes a draft work through the create endpoint
- create does not update the public site
- the new work opens into normal edit mode after create

### Task 4. Migrate Route Entries And Docs

Status:

- proposed

Update route references after the unified page is stable:

- catalogue dashboard links
- `studio_config.json` route keys and UI text
- `_docs_src/catalogue-work-editor.md`
- `_docs_src/catalogue-new-work-editor.md` or a replacement compatibility note
- `_docs_src/studio-runtime.md`
- `_docs_src/user-guide.md`
- `_docs_src/studio-ui-rules.md` if a reusable Studio mode-toggle rule emerges
- draft-work list route or dashboard/status documentation, depending on the chosen implementation

Acceptance checks:

- docs viewer generated payloads are rebuilt for the Studio scope
- old route behavior is documented
- dashboard links match the chosen workflow
- `catalogue_new_work_editor` is retired from active config
- draft works are visible from an obvious Studio catalogue navigation point

### Task 4a. Add Draft Works Visibility

Status:

- proposed

Add a draft-focused list so source-only draft creates can be found after the current session.

Expected behavior:

- list work source records with `status = draft`
- show identifying fields such as `work_id`, `title`, `year_display`, and `series_ids`
- link each draft work into the unified work editor
- place the entry point where catalogue workflow users will naturally see it

Acceptance checks:

- a newly created draft work appears in the draft list after source data refresh
- selecting a row opens `/studio/catalogue-work/?work=<work_id>`
- published works do not appear in the draft-focused list
- the chosen location does not duplicate an existing list pattern unnecessarily

### Task 5. Verify Create/Edit/Bulk Paths

Status:

- proposed

Verification should cover all existing work editor paths plus new mode:

- empty route load
- `?work=<work_id>` load
- search and open
- bulk open
- single-record save
- bulk save
- create draft work
- post-create edit mode
- draft work list visibility
- detail/download/link panels after create
- desktop and mobile layout

Acceptance checks:

- existing edit and bulk behavior still works
- create mode does not expose build/delete/detail actions before record creation
- local write service failures leave clear status text
- docs and config sanitization scans pass

## Non-Goals

Out of scope for the first implementation:

- changing the canonical source schema
- adding remote media upload
- editing prose directly in the browser
- creating work details inline during work create
- adding multi-record create
- changing delete cleanup behavior
- changing catalogue search behavior

## Benefits

Expected benefits:

- one normal place to create and continue editing a work
- a visible queue of unpublished draft works that need completion, publishing, or deletion
- less duplication between new and edit field definitions
- fewer opportunities for label, validation, and ordering drift
- clearer route model for work maintenance
- easier future refactors around shared catalogue editor fields

## Open Questions

- Should `New` be a persistent mode toggle or a one-shot command that clears the editor into create mode?
- Should new mode reuse the top search input exactly, or should it visually relabel the field with a mode-specific label?
- Should the suggested next id be auto-filled or shown as a selectable suggestion?
- Should this pattern later apply to series and work-detail create/edit flows?
- How should the pattern adapt to moments, where staged import and routine metadata editing are related but not identical workflows?
- Does `POST /catalogue/work/create` need server-side validation updates for the required-field invariant?
- Should draft-work visibility live inside Catalogue Status, a dedicated route, or the catalogue dashboard?

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [New Catalogue Work](/docs/?scope=studio&doc=catalogue-new-work-editor)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
