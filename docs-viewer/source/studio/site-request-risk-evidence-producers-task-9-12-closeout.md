---
doc_id: site-request-risk-evidence-producers-task-9-12-closeout
title: Risk Evidence Producers Tasks 9-12 Closeout
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Tasks 9-12 Closeout

This is the delivery specification for Batch 9-12 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 9-12: Docs, cleanup, verification, and closeout

Summary: Update durable docs, clean legacy leftovers, run final verification, and close the request.

| ID | status | action |
| --- | --- | --- |
| 9.1 | planned | Update [Admin Checks](/docs/?scope=studio&doc=admin-checks) with stable config, route/API, runner, artifact, target-map audit, markdown display, and snapshot deletion contracts. |
| 9.2 | planned | Update [Admin Checks Files Report](/docs/?scope=studio&doc=admin-checks-report-files) after the `files` report artifact shape is stable. |
| 9.3 | planned | Keep [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack) unchanged unless `/admin/risk/` is deliberately retired. |
| 9.4 | planned | Document when maintainers should rerun the target-map audit, especially after new routes, feature areas, app layers, or significant file moves. |
| 9.5 | planned | Add child docs under [Admin Checks](/docs/?scope=studio&doc=admin-checks) for subsequent reports when those reports are implemented. |
| 9.6 | planned | Keep generated Docs Viewer payload rebuild out of scope unless explicitly requested. |
| 10.1 | planned | Remove unused legacy risk artifacts only after the new route has equivalent or intentionally narrowed capability. |
| 10.2 | planned | Confirm removed paths are not preserved through import aliases, copied files, static mount shims, or dual-read fallback logic. |
| 10.3 | planned | Keep ignored local run output out of source control. |
| 11.1 | planned | Run the target-map audit and review `_unclassified`, stale-pattern, multi-family, and likely-unmapped findings. |
| 11.2 | planned | Run focused Python tests for the orchestrator, report producer, API, and safe artifact reads. |
| 11.3 | planned | Run a dry run for `docs-viewer` / `files`. |
| 11.4 | planned | Run a write run for `docs-viewer` / `files` and inspect the artifact tree. |
| 11.5 | planned | Verify snapshot deletion removes only the selected checks run directory and rejects unsafe run ids. |
| 11.6 | planned | Run the narrowest Admin check profile that covers the changed route/API if one exists. |
| 11.7 | planned | Run browser smoke verification for `/admin/checks/` if the UI route is implemented in the slice. |
| 12.1 | planned | Update this request status and `ui_status`. |
| 12.2 | planned | Record the v1 target-map audit summary and any target-map findings deferred for later risk review. |
| 12.3 | planned | Record child requests written for subsequent reports, legacy behavior reviewed, verification results, and generated-payload status. |
| 12.4 | planned | Move durable command/API/report contracts into [Admin Checks](/docs/?scope=studio&doc=admin-checks) and its report child docs. |
| 12.5 | planned | Retire `/admin/risk/` only when the replacement is complete and the retirement has been verified. |

## Steer for these tasks

- This batch closes v1 and should not grow new report scope.
- Docs Viewer generated payload rebuild remains out of scope unless explicitly requested.
- `/admin/risk/` retirement is allowed only after replacement capability and verification are complete.

## Deliverables

- updated durable docs
- cleanup confirmation
- final verification results
- closeout notes in the parent request

## Implementation and policy guidance

- Move durable contracts out of the request and into [Admin Checks](/docs/?scope=studio&doc=admin-checks) and its report child docs.
- Record child requests for subsequent reports rather than extending v1.
- Do not preserve old paths through aliases or dual-read fallbacks.

## Proposed verification set

- Target-map audit.
- Focused Python tests.
- `docs-viewer` / `files` dry run and write run.
- Snapshot deletion safety check.
- Narrow Admin check profile and browser smoke only where warranted by implementation.

## completed verification

- Not started.

## follow-on tasks

- Subsequent report producer requests created by Batch 8.

## task close

- Set this batch status and front matter `ui_status` to `done`.
- Close out the parent request only after verification and durable-doc updates are recorded.
