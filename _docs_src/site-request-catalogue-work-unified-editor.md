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

The existing `/studio/catalogue-new-work/` route should remain temporarily as a compatibility entry point. It can either redirect to `/studio/catalogue-work/?mode=new` or render a lightweight link/redirect page until dashboard and docs references are fully migrated.

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

## New Mode Behavior

In new mode:

- the top input label and placeholder should describe a new work id, not search
- the search popup should be hidden
- bulk syntax should be invalid
- the input should default to the suggested next work id when available
- duplicate work ids should be rejected before create
- title should remain required for create unless this requirement is explicitly changed
- new works should still be saved as `status = draft`
- `published_date` should default to blank/null
- `Create` should replace `Save` as the primary mutation command
- create should call the existing `POST /catalogue/work/create` endpoint
- after a successful create, the page should load the new work in edit mode

Edit-only surfaces should be hidden or disabled while no created record exists:

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

The first implementation should avoid a third copy of field definitions.

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

### Create Validation Versus Edit Validation

Create mode currently requires a title and blocks duplicate work ids. Edit mode allows broader source maintenance and does not require title in the same way.

Discussion points:

- Should title remain required for new draft works?
- Should any other field become required at create time?
- Should create mode expose `status`, or should `draft` remain implicit until the record exists?

### Hidden Versus Disabled Controls

Some controls do not apply until a record exists. Hiding them keeps new mode clean, while disabling them makes the full workflow more discoverable.

Discussion point:

- For each edit-only surface, should new mode hide it, disable it, or show a readonly placeholder?

### Compatibility And Navigation

Existing docs, dashboard links, and config route keys point to `/studio/catalogue-new-work/`.

Discussion points:

- Should the old route redirect immediately?
- Should dashboard copy collapse `Create New Work` and `Edit Work` into a single `Work Editor` entry?
- Should `catalogue_new_work_editor` remain in config during a transition?

### Testing Blast Radius

The change touches a high-use Studio route and a local write flow.

Discussion points:

- Should the first implementation keep `/studio/catalogue-new-work/` functional until the unified route has been smoke-tested?
- Should the create endpoint behavior remain unchanged in the first pass?
- Should unified create mode avoid automatic site update until after the first save in edit mode?

## Proposed Implementation Tasks

### Task 1. Decide Mode Contract

Status:

- ready for discussion

Decide the route and UI contract before editing code:

- supported query shape for new mode, such as `?mode=new`
- initial no-query behavior
- `New` and `Open` control behavior
- hidden versus disabled edit-only surfaces
- compatibility behavior for `/studio/catalogue-new-work/`

Acceptance checks:

- mode transitions are documented before implementation
- risks above have explicit decisions or accepted follow-up tasks

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

### Task 3. Add New Mode To Work Editor

Status:

- proposed

Add new mode to `/studio/catalogue-work/`.

Expected behavior:

- `New` switches the top input to work-id entry
- suggested next id is prefilled when available
- `Create` appears as the primary mutation action
- edit-only panels are hidden or disabled according to the decided contract
- successful create loads the created work into edit mode on the same route

Acceptance checks:

- duplicate ids are blocked
- missing work id is blocked
- missing title is blocked if title remains required
- successful create writes a draft work through the existing endpoint
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

Acceptance checks:

- docs viewer generated payloads are rebuilt for the Studio scope
- old route behavior is documented
- dashboard links match the chosen workflow

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
- changing `POST /catalogue/work/create`
- adding remote media upload
- editing prose directly in the browser
- creating work details inline during work create
- adding multi-record create
- changing delete cleanup behavior
- changing catalogue search behavior

## Benefits

Expected benefits:

- one normal place to create and continue editing a work
- less duplication between new and edit field definitions
- fewer opportunities for label, validation, and ordering drift
- clearer route model for work maintenance
- easier future refactors around shared catalogue editor fields

## Open Questions

- Should `New` be a persistent mode toggle or a one-shot command that clears the editor into create mode?
- Should new mode reuse the top search input exactly, or should it visually relabel the field with a mode-specific label?
- Should the suggested next id be auto-filled or shown as a selectable suggestion?
- Should create mode expose `status`, or should status be fixed to draft until the work is created?
- Should the old `/studio/catalogue-new-work/` route redirect, stay as a compatibility wrapper, or remain fully functional for one release window?
- Should this pattern later apply to series and work-detail create/edit flows?
- How should the pattern adapt to moments, where staged import and routine metadata editing are related but not identical workflows?

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [New Catalogue Work](/docs/?scope=studio&doc=catalogue-new-work-editor)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
