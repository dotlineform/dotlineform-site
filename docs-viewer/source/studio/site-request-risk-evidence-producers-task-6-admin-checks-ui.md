---
doc_id: site-request-risk-evidence-producers-task-6-admin-checks-ui
title: Risk Evidence Producers Task 6 Admin Checks UI
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 6 Admin Checks UI

This is the delivery specification for Batch 6 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 6: Add `/admin/checks/` UI

Summary: Build the Admin route for selecting targets/reports, running checks, reading markdown artifacts, and deleting snapshots.

| ID | status | action |
| --- | --- | --- |
| 6.1 | planned | Add the Admin route shell, frontend module, route config, and UI text bundle. |
| 6.2 | planned | Render scope, file-family, functional-area, route, and report selection from API metadata. |
| 6.3 | planned | Render report-specific controls from allowlisted option metadata. |
| 6.4 | planned | Support dry run and write run actions. |
| 6.5 | planned | List recent runs and display run summary markdown. |
| 6.6 | planned | Display selected report markdown. |
| 6.7 | planned | Provide confirmed deletion for a selected local run snapshot. |
| 6.8 | planned | Keep the UI dense and operational; avoid explanatory landing-page copy. |

## Steer for these tasks

- This is an operational Admin UI, not a landing page.
- Markdown is displayed as escaped preformatted text.
- The UI can create validated runs and delete validated local snapshots only.

## Deliverables

- `/admin/checks/` route shell
- frontend JS module
- Admin config entries
- UI text bundle

## Implementation and policy guidance

- Follow existing Admin route patterns.
- Use allowlisted metadata from the checks API for controls.
- Do not let route config imply write authority beyond validated API endpoints.

## Proposed verification set

- Focused UI smoke if lower-level tests do not cover route behavior.
- Browser verification for route boot, metadata rendering, run action, artifact display, and snapshot deletion where practical.

## completed verification

- Not started.

## follow-on tasks

- Batch 7 adds focused tests and check-profile integration.

## task close

- Add a handoff note to Batch 7.
- Set this batch status and front matter `ui_status` to `done`.
