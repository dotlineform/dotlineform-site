---
doc_id: site-request-catalogue-publication-workflow
title: Catalogue Publication Workflow Request
added_date: 2026-04-29
last_updated: 2026-04-29
parent_id: change-requests
sort_order: 135
---
# Catalogue Publication Workflow Request

Status:

- specified

## Summary

This change request covers replacing save-time publication checkboxes in Studio catalogue editors with a simpler user-facing publication model.

The UI should not expose the difference between canonical source data, generated public data, indexes, search, or rebuild mechanics. Those are implementation details. The user-facing model is:

- a work or series has been defined but is not on the public site: `draft`
- a draft has been published to the public site: `published`
- a published record can be removed from the public site by changing it back to `draft`

The immediate series-editor issue showed that a checkbox labelled `Update site now` makes publication look like an option on save. That is the wrong interaction. Saving metadata, publishing a draft, and unpublishing a public record are separate user intentions.

## Goal

Make catalogue publication behavior explicit without exposing rebuild as a UI concept.

The target user-facing commands are:

- `Save`
  saves metadata changes
- `Publish`
  changes a valid draft record to `published` and puts it on the public site
- `Unpublish`
  changes a published record to `draft` and removes it from the public site

There should be no visible `Rebuild`, `Update site now`, or save-time publication checkbox in the editor UI.

## User-Facing State Model

Editors should expose only these publication states:

- `draft`
  the record has been defined in Studio but is not published on the public site
- `published`
  the record is published on the public site

The status field is read-only in the form. The user changes publication state through the publication command button, not by typing into or selecting the status field.

The publication command is one button whose label and behavior are derived from the loaded record status:

- if status is `draft`, the button is `Publish`
- if status is `published`, the button is `Unpublish`
- if status is blank or otherwise invalid, the editor should guide the user into the supported state model rather than exposing another status as a normal workflow state

## Save Behavior

`Save` means "save my metadata changes."

Rules:

- `Save` is disabled when required fields are incomplete
- `Save` is disabled when there are no metadata changes
- `Save` does not change publication status
- if the record is `draft`, `Save` writes source metadata only
- if the record is `published`, `Save` writes metadata and then runs the internal public artifact update needed for those changes to appear on the site
- a successful `Save` leaves the editor on the same publication status
- if the internal public update fails after saving a published record, the UI should report that the metadata save succeeded but the site update failed

This keeps the user's mental model simple: if a published work or series is edited and saved, the public site should reflect the saved changes.

## Publish/Unpublish Behavior

`Publish` and `Unpublish` are the only user-facing publication commands.

`Publish`:

- is enabled when status is `draft` and required fields are complete
- is disabled when required fields or publication blockers are present
- changes status from `draft` to `published`
- runs the internal public artifact update needed to make the record visible on the site
- updates the active editor state from the write response

`Unpublish`:

- is enabled when status is `published`
- ignores dirty metadata currently on the form
- changes only publication status from `published` to `draft`
- runs the internal cleanup/update needed to remove the record from the public site
- updates the active editor state from the write response
- should make unsaved form edits visibly stale or reset the form from the response so the user does not confuse unpublish with a metadata save

Unpublish must remove the generated Markdown collection file for the record, such as `_series/<series_id>.md` or `_works/<work_id>.md`, so the public URL route to the draft record is no longer available. It must also remove or update public JSON, indexes, recent entries, and search records as needed for the record family.

## Current Problem

Current catalogue editors use variations of save-time `apply_build` behavior:

- a checkbox can make `Save` also run a public update
- the checkbox can remain checked while status fields are edited
- status changes and runtime artifact changes can appear to happen as one ambiguous action
- draft saves can look publishable even when validation or generator behavior later blocks them

Recent guardrails disabled save-time public update while work or series status is not `published`, but that is a defensive correction. The target interaction removes the checkbox and makes the state-changing command explicit.

## Shared Behavior Contract

Across catalogue editors:

- visible status is read-only
- source status changes happen only through `Publish` or `Unpublish`
- `Save` never changes status
- `Save` on a published record internally updates the public site
- `Publish` and `Unpublish` responses update the active editor state from the write response
- public artifact cleanup is deterministic and id-scoped
- public index, recent index, lookup, and catalogue search follow-through are internal command outcomes
- stale public artifacts must not remain discoverable after unpublish
- Build Activity and Catalogue Activity should record save, publish, and unpublish outcomes distinctly

The UI may show confirmation or impact text where useful, but should not require the user to understand generated artifact paths or a separate rebuild action.

## Record-Specific Rules

Works:

- `Publish` requires the work to pass public work validation
- `Save` on a published work runs the internal work-scoped update path
- `Unpublish` removes the work public page, per-work JSON, public index/search entries, recent entries, and dependent public surfaces as needed
- unpublishing a work with published dependent details should either block or make the dependent public cleanup explicit in the internal impact summary

Work details:

- detail publication should follow the same visible status model if work details remain independently publishable
- `Publish` requires the parent work to exist and be compatible with publishing the detail
- `Save` on a published detail updates the parent work runtime payload as needed
- `Unpublish` removes the detail page/search visibility and updates the parent work runtime payload

Series:

- `Publish` requires required series fields, a valid `primary_work_id`, at least one published member work, and a published primary work
- `Save` on a published series updates the public series stub, per-series JSON, public series index, recent index when appropriate, and catalogue search
- `Unpublish` removes `_series/<series_id>.md`, removes or updates `assets/series/index/<series_id>.json` according to the final generated-data contract, and removes the series from public aggregate index/search surfaces while preserving Studio access to the draft source record

Moments:

- moment publication should use the same `draft` and `published` model if moments gain first-class edit publication controls
- `Publish` requires valid moment metadata and any required media/prose readiness for the public moment surface
- `Save` on a published moment updates the public moment artifacts
- `Unpublish` removes the moment page/json/search entry and updates `assets/data/moments_index.json`

## UX Principles

- The UI should speak in terms of `draft`, `published`, `Save`, `Publish`, and `Unpublish`.
- The UI should not expose `canonical`, `generated`, `runtime`, or `rebuild` as user workflow concepts.
- Status should be visible but read-only.
- The publication command should be one button whose label follows the current status.
- Disabled commands should explain blockers near the command surface.
- A successful `Publish` or `Unpublish` should leave the form showing the new status immediately.
- A successful `Save` on a published record should make saved changes appear on the public site without asking for another visible rebuild action.
- `published_date` handling should be explicit:
  - first publish may set it when blank
  - unpublish should not silently destroy historical date data without a documented decision
  - republish should either preserve or intentionally refresh it according to the record-family rule

## Implementation Tasks

### Task 1. Define Shared Publication Vocabulary

Status:

- implemented

Define the shared command names, state labels, Activity operation names, and result text for source save, publish, and unpublish.

Acceptance checks:

- Studio config owns the UI copy
- source save and visibility changes use distinct result/status language
- no user-facing copy refers to `Rebuild` or `Update site now` as an editor command
- docs describe when `Save`, `Publish`, and `Unpublish` appear

### Task 2. Add Shared Preview/Apply Server Shape

Status:

- implemented

Add or formalize publication preview/apply behavior that can be used by works, work details, series, and moments.

Implemented server shape:

- `POST /catalogue/publication-preview`
- `POST /catalogue/publication-apply`

The shared request shape uses `kind`, `action`, the target id, optional stale-write hash, and optional save payload for published-record saves. Supported actions are `publish`, `unpublish`, and `save_published`.

Acceptance checks:

- preview can report blockers and internal public artifact impact
- apply revalidates immediately before writing
- apply is id-scoped and records backups for source and generated writes
- apply can represent "metadata saved, public update failed" for published-record saves

### Task 3. Convert Series Editor First

Status:

- implemented

Use the series editor as the first implementation because it exposed the checkbox problem and already has a narrow public-build guardrail.

Acceptance checks:

- status field is read-only
- `Save` is disabled for no-op saves and incomplete required metadata
- `Save` on a published series performs the internal site update
- one publication button shows `Publish` for draft series and `Unpublish` for published series
- `Publish` is enabled only when the draft can pass publication validation
- `Unpublish` ignores dirty metadata, changes status to `draft`, removes the public route file, and cleans public index/search visibility
- no `Update site now` checkbox remains

### Task 4. Extend To Work And Work Detail Editors

Status:

- implemented

Apply the same command model to work and work-detail editors, including parent-runtime follow-through for details.

Work-editor implementation:

- `/studio/catalogue-work/` no longer exposes save-time public update controls
- the work status field is read-only in single, bulk, and new modes
- published work saves request the internal public update path automatically
- bulk saves internally update public output only for changed published work records
- saved draft works expose `Publish`; published works expose `Unpublish`
- work `Publish` / `Unpublish` uses the shared publication preview/apply endpoints and surfaces blockers before apply

Work-detail implementation:

- `/studio/catalogue-work-detail/` no longer exposes save-time public update controls
- the detail status field is read-only in single, bulk, and new modes
- published detail saves request the internal parent-work public update path automatically
- bulk saves internally update public output only for changed published detail records
- saved draft details expose `Publish`; published details expose `Unpublish`
- work-detail `Publish` / `Unpublish` uses the shared publication preview/apply endpoints and surfaces blockers before apply

Acceptance checks:

- work and detail editors no longer use save-time publication checkboxes
- status fields are read-only
- published-record saves internally update the public site
- unpublishing a work or detail cleans up public artifacts and search/index references
- publish blockers are surfaced before apply

### Task 5. Extend To Moment Editor And Imports

Status:

- proposed

Align moment editing and file-driven moment import flows with the same publication vocabulary and preview/apply model where moments expose publication controls.

Acceptance checks:

- moment publish/unpublish actions use the shared command language
- published moment saves internally update public artifacts
- moment index/search cleanup is part of unpublish
- import flows do not imply publication unless they explicitly run a publish command

Moment implementation:

- `/studio/catalogue-moment/` no longer exposes save-time public update controls
- the moment status field is read-only in existing-record edit mode
- published moment saves request the internal public update path automatically
- saved draft moments expose `Publish`; published moments expose `Unpublish`
- moment `Publish` / `Unpublish` uses the shared publication preview/apply endpoints and surfaces blockers before apply
- `/studio/catalogue-moment/` now includes the staged-file import panel, so import, review, save, publish, and unpublish live on one Moment editor page
- `/studio/catalogue-moment-import/` is retained only as a compatibility bridge to the Moment editor and no longer owns a separate workflow

### Task 6. Update Docs And E2E Checklist

Status:

- proposed

Update editor docs, script docs, and the Studio E2E checklist after the command model is implemented.

Acceptance checks:

- each catalogue editor doc names `Save`, `Publish`, and `Unpublish` behavior where applicable
- script docs describe the internal build/cleanup paths used by save, publish, and unpublish
- manual E2E checks cover save-on-published, publish, and unpublish for each record family

## Benefits

- matches the user's actual mental model: defined draft records and public records
- removes the ambiguous save-time publication checkbox
- makes status changes intentional and auditable
- keeps published metadata edits simple: save means the public site should update
- gives unpublish a real cleanup contract instead of treating it as a status edit
- creates one catalogue-wide interaction pattern instead of per-editor save/build variations

## Risks

- published-record saves become higher impact because they trigger internal public updates
- unpublish cleanup must be carefully scoped so it does not delete unrelated media or source prose
- ignoring dirty metadata during unpublish can surprise users unless the UI clearly separates metadata save from publication status changes
- `published_date` semantics need a clear decision before broad rollout
- work/detail dependencies can create more complex previews than series

## Open Questions

- Should unpublish preserve `published_date`, clear it, or move it to a separate historical field?
- Should republishing after unpublish create a new recent-index entry?
- How should the UI show "metadata saved, public update failed" without exposing rebuild as a user command?
- Should unpublish reset the form to the saved source response immediately, or keep dirty values visible with an explicit unsaved-warning state?
- Should work-detail publication remain independent, or become part of the parent work publication model?
