---
doc_id: site-request-admin-app-structure-batch-6
title: Admin App Structure Batch 6
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: planned
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Durable Docs, Verification, and Closeout

This is the delivery specification for Batch 6 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 6: Durable Docs, Verification, and Closeout

Summary: update durable docs, run final focused verification, record moved ownership, and close the request.

| ID | status | action |
| --- | --- | --- |
| 6.1 | planned | Update durable ownership docs for Admin, Studio, UI Catalogue, testing, local setup, route ownership, scripts, output paths, and fixture ownership. |
| 6.2 | planned | Update request and task docs with final statuses, moved paths, verification results, and any remaining follow-on work. |
| 6.3 | planned | Run focused final verification for Admin home, Admin routes, Admin runner, Admin UI Catalogue, retained Studio routes, and moved fixtures/checks. |
| 6.4 | planned | Record final check summaries and run-log locations under `var/admin/test-runs/` when runner verification writes logs. |
| 6.5 | planned | Close the parent request when durable docs contain the current ownership contract and the planned migration is complete. |

## Steer for these tasks

- Durable docs should describe the final current-state boundary rather than the migration history.
- Final tests should assert that current Admin and retained Studio behavior works.
- Verification should include runner output paths and route behavior owned by Admin.

## Deliverables

- Updated durable docs.
- Final request and tracker status updates.
- Final verification summary.
- Closeout notes for moved source, routes, scripts, tests, and fixtures.

## Implementation and policy guidance

- Keep docs source updates in `docs-viewer/source/studio/`.
- Regenerate Docs Viewer payloads only if the implementation task explicitly includes that follow-through.
- Record remaining risks or follow-on work in the request docs before marking them done.

## Proposed verification set

- Admin server/config pytest
- Admin route smokes for moved route families
- Admin UI Catalogue smoke
- Admin runner/profile pytest and representative small profile run
- focused retained Studio route smokes
- syntax checks for changed Python and JavaScript
- docs/source review for updated route and command references

## completed verification

- pending

## follow-on tasks

- pending implementation findings

## task close

- Set `ui_status` to `done` for this batch, the tracker, and the parent request after closeout is complete.
