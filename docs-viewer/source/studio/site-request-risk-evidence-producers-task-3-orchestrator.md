---
doc_id: site-request-risk-evidence-producers-task-3-orchestrator
title: Risk Evidence Producers Task 3 Orchestrator
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 3 Orchestrator

This is the delivery specification for Batch 3 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 3: Build report orchestrator

Summary: Add the JSON-request runner that validates targets and executes allowlisted report scripts.

| ID | status | action |
| --- | --- | --- |
| 3.1 | planned | Add `admin-app/checks/run_reports.py`. |
| 3.2 | planned | Accept a JSON run request from `--request <path>` or standard input. |
| 3.3 | planned | Support dry-run and write-run modes. |
| 3.4 | planned | Validate scope, family ids, area ids, route ids, report ids, and report options through the registry. |
| 3.5 | planned | Create run-level artifacts under `var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/`. |
| 3.6 | planned | Invoke report scripts with explicit argv lists and record command metadata. |
| 3.7 | planned | Preserve per-report status so one failed report does not erase completed report output. |

## Steer for these tasks

- The orchestrator is the only supported multi-report entry point.
- Browser-provided command strings, shell flags, environment values, arbitrary paths, and output roots remain prohibited.
- Dry runs must resolve the execution plan without writing run artifacts.

## Deliverables

- `admin-app/checks/run_reports.py`
- run request validation
- run-level artifact writing
- command metadata recording

## Implementation and policy guidance

- Report scripts are invoked by path and argv list, not shell command text.
- Failed reports should remain visible in run summaries alongside completed reports.
- Run directories live only under ignored `var/admin/checks/`.

## Proposed verification set

- Focused orchestrator tests for dry-run, write-run, validation, failed-report behavior, and artifact shape.
- Python syntax check for `run_reports.py`.

## completed verification

- Not started.

## follow-on tasks

- Batch 4 plugs the `files` producer into the orchestrator.

## task close

- Add a handoff note to Batch 4.
- Set this batch status and front matter `ui_status` to `done`.
