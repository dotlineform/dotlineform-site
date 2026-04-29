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

- proposed

## Summary

This change request covers replacing save-time publication checkboxes in Studio catalogue editors with explicit publication commands.

The immediate series-editor issue showed that a checkbox labelled `Update site now` can imply that saving a draft record and publishing public artifacts are one combined action. That is the wrong model for the catalogue workflow. Saving source metadata, changing public visibility, and rebuilding already-published runtime artifacts are separate operations with different validation, side effects, and recovery expectations.

This pattern should be defined once and then replicated across catalogue works, work details, series, and moments where applicable.

## Goal

Make catalogue publication actions explicit.

The target model:

- `Save` writes canonical source metadata only
- `Publish` changes a draft or otherwise non-published record into a public record and runs the required public artifact update
- `Unpublish` changes a public record back to draft or non-public state and removes or disables public artifacts
- `Rebuild` or `Update site now` recomputes public artifacts only for records that are already published

The interface should stop using checkboxes for operations that change public visibility.

## Current Problem

Current catalogue editors use variations of save-time `apply_build` behavior:

- a checkbox can make `Save` also run a public update
- the checkbox can remain checked while status fields are edited
- status changes and runtime artifact changes can appear to happen as one ambiguous action
- draft saves can look publishable even when validation or generator behavior later blocks them

The series editor now has a guardrail that disables save-time public update while the form status is not `published`, but that is a defensive correction rather than the desired long-term interaction model.

## Proposed Direction

Adopt explicit command buttons for public visibility changes.

Suggested command model:

- `Save`
  source-only save for all catalogue record states
- `Publish`
  visible when the loaded source record is not public and the current draft can pass publish validation
- `Unpublish`
  visible when the loaded source record is public
- `Rebuild`
  visible when a published source record has saved changes or explicit runtime drift

`Publish`, `Unpublish`, and `Rebuild` should be separate commands, not checkbox options on `Save`.

## Shared Behaviour Contract

Across catalogue editors:

- source save never implies publication
- publish and unpublish actions should show a preview of public artifact impact before mutating source or generated outputs
- publish and unpublish responses should update the active editor state from the write response
- public artifact cleanup should be deterministic and id-scoped
- public index, recent index, lookup, and catalogue search follow-through should be part of the command outcome
- stale public artifacts should not remain discoverable after unpublish
- Build Activity and Catalogue Activity should record visibility-changing commands distinctly from source saves

## Record-Specific Rules

Works:

- `Publish` requires the work to pass public work validation
- `Publish` should run the normal work-scoped media/page/json/search update path
- `Unpublish` should remove or disable the work public page, per-work JSON, public index/search entries, and dependent public surfaces as needed

Work details:

- `Publish` requires the parent work to exist and be compatible with publishing the detail
- `Publish` should update the parent work runtime payload as well as the detail artifact
- `Unpublish` should remove or disable the detail page/json/search entry and update the parent work runtime payload

Series:

- `Publish` requires `status: published`, a valid `primary_work_id`, at least one published member work, and a published primary work
- `Publish` should write the series public stub, per-series JSON, public series index, recent index when appropriate, and catalogue search
- `Unpublish` should make the series route non-public and remove the series from public aggregate index/search surfaces while preserving canonical source and Studio lookup access

Moments:

- `Publish` requires valid moment metadata and any required media/prose readiness for the public moment surface
- `Unpublish` should remove or disable the moment page/json/search entry and update `assets/data/moments_index.json`

## UX Principles

- Visibility-changing commands should be verbs, not options.
- A disabled `Publish` command should explain the blockers near the command surface.
- A successful `Publish` or `Unpublish` should leave the form showing the new source status immediately.
- `Rebuild` should not be shown for draft records.
- `published_date` handling should be explicit:
  - first publish may set it when blank
  - unpublish should not silently destroy historical date data without a documented decision
  - republish should either preserve or intentionally refresh it according to the record-family rule

## Implementation Tasks

### Task 1. Define Shared Publication Vocabulary

Status:

- proposed

Define the shared command names, state labels, Activity operation names, and result text for source save, publish, unpublish, and rebuild.

Acceptance checks:

- Studio config owns the UI copy
- source save and visibility changes use distinct result/status language
- docs describe when each command appears

### Task 2. Add Shared Preview/Apply Server Shape

Status:

- proposed

Add or formalize publication preview/apply endpoints that can be used by works, work details, series, and moments.

Acceptance checks:

- preview reports source changes, generated artifact changes, public index/search changes, and blockers
- apply revalidates immediately before writing
- apply is id-scoped and records backups for source writes

### Task 3. Convert Series Editor First

Status:

- proposed

Use the series editor as the first implementation because it exposed the checkbox problem and already has a narrow public-build guardrail.

Acceptance checks:

- `Save` is source-only
- `Publish` and `Unpublish` are explicit commands
- `Rebuild` is available only for published series
- draft series cannot leave public index/search artifacts behind after unpublish

### Task 4. Extend To Work And Work Detail Editors

Status:

- proposed

Apply the same command model to work and work-detail editors, including parent-runtime follow-through for details.

Acceptance checks:

- work and detail editors no longer use save-time publication checkboxes
- unpublishing a work or detail cleans up public artifacts and search/index references
- publish blockers are surfaced before apply

### Task 5. Extend To Moment Editor And Imports

Status:

- proposed

Align moment editing and file-driven moment import flows with the same publication vocabulary and preview/apply model.

Acceptance checks:

- moment publish/unpublish actions use the shared command language
- moment index/search cleanup is part of unpublish
- import flows do not imply publication unless they explicitly run a publish command

### Task 6. Update Docs And E2E Checklist

Status:

- proposed

Update editor docs, script docs, and the Studio E2E checklist after the command model is implemented.

Acceptance checks:

- each catalogue editor doc names `Save`, `Publish`, `Unpublish`, and `Rebuild` behavior where applicable
- script docs describe the build/cleanup paths used by publish and unpublish
- manual E2E checks cover publish and unpublish for each record family

## Benefits

- reduces accidental public changes
- makes draft, published, rebuild-needed, and unpublished states easier to reason about
- gives unpublish a real cleanup contract instead of treating it as a status edit
- creates one catalogue-wide interaction pattern instead of per-editor save/build variations

## Risks

- the implementation touches high-value source and generated artifact paths
- unpublish cleanup must be carefully scoped so it does not delete unrelated media or source prose
- `published_date` semantics need a clear decision before broad rollout
- work/detail dependencies can create more complex previews than series

## Open Questions

- Should unpublish preserve `published_date`, clear it, or move it to a separate historical field?
- Should `Publish` directly set `status: published`, or should status remain an editable field with `Publish` validating the current field value?
- Should republishing after unpublish create a new recent-index entry?
- Should media upload or remote publication ever be part of the same command, or remain a separate handoff?

