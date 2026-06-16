---
doc_id: site-request-work-detail-status-workflow-removal
title: Work Detail Status Workflow Removal
added_date: 2026-06-16
last_updated: 2026-06-16
ui_status: planned
parent_id: change-requests
---
# Work Detail Status Workflow Removal

Status: `planned`

## Scope

Remove the independent publish/draft workflow from work detail records, and remove the preview/refresh panel from `/studio/catalogue-work-detail/`.

## Product Rule

- Publishing is owned by the parent work record.
- A published work publishes all of its detail records as part of the work output.
- A draft work has no public work page, so its detail records are not public in practice.
- Detail records do not have independent publish/draft state and should not read, write, display, or act on detail `status`.

## Task List

- Remove detail `status` from the work detail data contract.
- Remove any detail-only `published_date` handling.
- Remove existing `status` and `published_date` fields from `studio/data/canonical/catalogue/work_details.json` during the cleanup.
- Remove generated `status` and `published_date` fields from `studio/data/generated/catalogue-lookup/work_details/*.json`.
- Remove generated detail `status` fields from the detail sections in `studio/data/generated/catalogue-lookup/works/*.json`.
- Update consumers of generated work-detail and work lookup payloads so they no longer require, display, or act on those removed fields.
- Remove detail status normalization, validation, defaults, and save/create payload handling from the local catalogue write service.
- Update work-detail save/build behavior so public output decisions are based on the parent work status, not detail status.
- Remove detail publish and unpublish actions from `/studio/catalogue-work-detail/`.
- Remove frontend state, labels, button wiring, confirmation text, and API calls for detail publish/unpublish.
- Remove detail status from readonly fields, form metadata, bulk-edit metadata, dirty-state logic, and validation.
- Remove the current-record preview/media readiness/refresh panel from `/studio/catalogue-work-detail/`.
- Remove `Refresh media` behavior for detail records from the detail editor UI.
- Remove publication preview/apply callers for `work_detail` once no frontend path uses them.
- Update catalogue status/draft views so they no longer list work details as independently publishable records.
- Update Studio docs and UI text keys that still describe detail publish/unpublish, detail status, media readiness, or refresh media.
- Remove or update tests and fixtures that reference detail `status` or detail-only publish/draft behavior.
- Do not create negative assertion tests to verify the absence of these fields, UI and workflows.

## Basic Testing Needed

- Run JavaScript syntax checks for touched catalogue work-detail editor modules.
- Run `git diff --check`.
- Run focused Python tests or smoke checks for catalogue source mutation/write-service behavior touched by the cleanup.
- Run the existing work-detail editor route smoke, if available.
- Run the work editor smoke that covers the detail list/link flow.
- Manually check `/studio/catalogue-work-detail/?detail=<detail_uid>`:
  - no detail publish/unpublish action is present
  - no status field is shown
  - no current-record preview/refresh panel is shown
  - saving a detail for a published parent updates the parent work output
  - saving a detail for a draft parent writes source only
- Manually check `/studio/catalogue-work/` for a work with details:
  - detail links still open existing detail records
  - work publish/draft behavior remains work-scoped
