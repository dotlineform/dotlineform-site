---
doc_id: site-request-risk-evidence-producers-task-4-report-producers
title: Risk Evidence Producers Task 4 Files Report Producer
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 4 Files Report Producer

This is the delivery specification for Batch 4 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 4: Implement `files` report producer

Summary: Implement the v1 proof-of-concept `files` report.

| ID | status | action |
| --- | --- | --- |
| 4.1 | planned | Add `admin-app/checks/reports/files.py`. |
| 4.2 | planned | Read the selected scope from resolved config rather than duplicating path rules. |
| 4.3 | planned | Apply selected family, area, and route filters through the shared target resolver. |
| 4.4 | planned | Count included files, lines, and bytes. |
| 4.5 | planned | Produce `report.json` and `report.md`. |
| 4.6 | planned | Support the initial `files` options `limit` and `sort`. |
| 4.7 | planned | Include focused unit tests for path inclusion/exclusion, line/byte counting, sorting, and markdown rendering. |

## Steer for these tasks

- Each report script owns artifacts for one report only.
- The target resolver should be shared with the target-map audit and orchestrator.
- `files` is the only v1 report; `target-map` is deferred to [Target Map Report Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-target-map).

## Deliverables

- `admin-app/checks/reports/files.py`
- report JSON and markdown outputs
- focused producer tests

## Implementation and policy guidance

- Keep markdown rendering simple: scripts write `.md`; API/browser display is handled later.
- Keep generated payloads, dependencies, caches, and local run outputs excluded by config.
- Do not duplicate path rules inside producers.

## Proposed verification set

- Focused producer tests for `files`.
- Orchestrator write run for `files` after Batch 3 is available.

## completed verification

- Not started.

## follow-on tasks

- Batch 5 exposes these reports through the Admin checks API.

## task close

- Add a handoff note to Batch 5.
- Set this batch status and front matter `ui_status` to `done`.
