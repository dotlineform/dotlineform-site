---
doc_id: site-request-risk-evidence-producers-task-7-tests
title: Risk Evidence Producers Task 7 Tests
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 7 Tests

This is the delivery specification for Batch 7 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 7: Add focused tests and verification commands

Summary: Add targeted verification for the checks config, runner, producers, API, and route behavior.

| ID | status | action |
| --- | --- | --- |
| 7.1 | planned | Add Python tests for target-map auditing, config validation, orchestrator dry-run/write-run behavior, safe path handling, and `files` report output. |
| 7.2 | planned | Add API tests for health, metadata, run creation, safe summary/report reads, snapshot deletion, and invalid id rejection. |
| 7.3 | planned | Add a focused Admin route smoke only if the UI behavior cannot be covered cheaply through lower-level tests. |
| 7.4 | planned | Add the narrowest relevant `admin-app/commands/run_checks.py` profile entry only after the focused tests exist. |

## Steer for these tasks

- Verification should stay focused; do not add broad browser smokes where lower-level tests cover the contract.
- Add a check profile only after the underlying focused tests exist.
- Use strict safe-path and invalid-id tests for local artifact access.

## Deliverables

- Python tests for target map, config, orchestrator, producers, and API
- optional focused Admin route smoke
- optional run-check profile entry

## Implementation and policy guidance

- Tests should validate current owner contracts, not preserve legacy `/admin/risk/` compatibility.
- Keep generated payload rebuild out of scope unless implementation changes require it.

## Proposed verification set

- Focused pytest paths added in this batch.
- Narrow run-check profile only if added.

## completed verification

- Not started.

## follow-on tasks

- Batch 8 reviews legacy risk capabilities and frames child requests for later reports.

## task close

- Add a handoff note to Batch 8.
- Set this batch status and front matter `ui_status` to `done`.
