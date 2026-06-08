---
doc_id: site-request-risk-evidence-producers-task-8-legacy-risk-review
title: Risk Evidence Producers Task 8 Legacy Risk Review
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 8 Legacy Risk Review

This is the delivery specification for Batch 8 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 8: Review legacy `/admin/risk/` capabilities and frame child requests

Summary: Review legacy risk producers after v1 works and create child requests for subsequent reports.

| ID | status | action |
| --- | --- | --- |
| 8.1 | planned | Review `/admin/risk/` runner, API, UI, and tests after `/admin/checks/` can run `files`. |
| 8.2 | planned | Do not migrate additional legacy producers into v1. |
| 8.3 | planned | Confirm subsequent report candidates after the v1 implementation is working. |
| 8.4 | planned | Write child requests for subsequent reports, such as static searches, generated payload inventory, git churn, JavaScript inventory guardrail, runtime profile results, or subjective notes. |
| 8.5 | planned | Note any legacy inventory behavior that does not appear to map to an active risk policy or report. |
| 8.6 | planned | Do not add compatibility aliases for old artifact paths. |
| 8.7 | planned | For each child request, record report id, source artifact or producer, expected metrics, likely target layers, and verification needs. |

## Steer for these tasks

- This is a post-v1 review step, not a migration batch.
- Subsequent reports should become child requests with their own specs.
- Legacy paths should not be preserved through compatibility aliases.

## Deliverables

- Review notes for legacy `/admin/risk/`
- child requests for subsequent report producers where warranted
- list of legacy behavior to discard or defer

## Implementation and policy guidance

- Only `files` is a v1 report; `target-map` is deferred to [Target Map Report Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-target-map).
- Treat `/admin/risk/` as reusable prior art, not the new contract.
- Keep child requests specific enough to implement later without rediscovering source artifacts.

## Proposed verification set

- Source review of legacy risk runner, API, UI, and tests.
- Confirm child request docs link back to the parent request.

## completed verification

- Not started.

## follow-on tasks

- Batch 9-12 handles docs, cleanup, final verification, and closeout.

## task close

- Add a handoff note to Batch 9-12.
- Set this batch status and front matter `ui_status` to `done`.
