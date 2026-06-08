---
doc_id: site-request-risk-evidence-producers-task-5-admin-checks-api
title: Risk Evidence Producers Task 5 Admin Checks API
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 5 Admin Checks API

This is the delivery specification for Batch 5 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 5: Add Admin checks API

Summary: Add the local Admin API for metadata, runs, safe artifact reads, and snapshot deletion.

| ID | status | action |
| --- | --- | --- |
| 5.1 | planned | Add `/admin/api/checks/health`. |
| 5.2 | planned | Add `/admin/api/checks/reports` for configured scopes, target layers, reports, and safe option metadata. |
| 5.3 | planned | Add `/admin/api/checks/runs` for recent run listing and validated run creation. |
| 5.4 | planned | Add safe reads for `/admin/api/checks/runs/<run-id>/summary` and `/admin/api/checks/runs/<run-id>/reports/<report-id>`. |
| 5.5 | planned | Return raw markdown strings from safe reads, following `/admin/risk/`; do not return rendered HTML. |
| 5.6 | planned | Add safe deletion for `/admin/api/checks/runs/<run-id>` that removes one local snapshot under `var/admin/checks/`. |
| 5.7 | planned | Use strict run-id and report-id validation before reading local artifacts. |
| 5.8 | planned | Use the same strict run-id validation before deleting local artifacts and reject paths outside the checks runs root. |
| 5.9 | planned | Do not add Activity rows in v1; leave Activity integration for a later Admin Activity review. |

## Steer for these tasks

- The API projects safe metadata and artifacts; it does not expose arbitrary local file reads.
- Snapshot deletion is in v1 and must be constrained to ignored checks run directories.
- Activity integration is out of scope for v1.

## Deliverables

- Admin checks API adapter
- server route registration
- safe run/report id validation
- raw markdown payloads for summaries and reports

## Implementation and policy guidance

- Match the simple `/admin/risk/` markdown pattern.
- Keep command execution and artifact paths allowlisted.
- Use strict path containment checks before reads and deletes.

## Proposed verification set

- API tests for health, metadata, run creation, safe reads, snapshot deletion, and unsafe id rejection.
- Python syntax checks for new server modules.

## completed verification

- Not started.

## follow-on tasks

- Batch 6 consumes this API in the `/admin/checks/` UI.

## task close

- Add a handoff note to Batch 6.
- Set this batch status and front matter `ui_status` to `done`.
