---
doc_id: site-request-risk-evidence-producers-task-7-tests
title: Risk Evidence Producers Task 7 Tests
added_date: 2026-06-08
last_updated: 2026-06-10
ui_status: done
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 7 Tests

This is the delivery specification for Batch 7 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 7: Add focused tests and verification commands

Summary: Add targeted verification for the checks config, runner, producers, API, and route behavior.

| ID | status | action |
| --- | --- | --- |
| 7.1 | done | Add Python tests for target-map auditing, config validation, orchestrator dry-run/write-run behavior, safe path handling, and `files` report output. |
| 7.2 | done | Add API tests for health, metadata, run creation, safe summary/report reads, snapshot deletion, and invalid id rejection. |
| 7.3 | done | Add a focused Admin route smoke only if the UI behavior cannot be covered cheaply through lower-level tests. |
| 7.4 | done | Add the narrowest relevant `admin-app/commands/run_checks.py` profile entry only after the focused tests exist. |

## Steer for these tasks

- Verification should stay focused; do not add broad browser smokes where lower-level tests cover the contract.
- Add a check profile only after the underlying focused tests exist.
- Use strict safe-path and invalid-id tests for local artifact access.

## Batch 6 handoff

- `/admin/checks/` is registered in the Admin route config, server route table, runtime config, home navigation, static policy, and UI text paths.
- `admin-app/app/frontend/js/admin-checks.js` renders metadata-driven report, scope, family, area, route, and report-option controls from the checks API.
- The UI run action always sends `write: true`; no dry-run control exists in Batch 6.
- The run list is a top-level folder list from `var/admin/checks/`, starts with no selected folder, and selecting a run loads the selected report markdown as escaped preformatted text.
- Delete remains a confirmed UI action against the validated checks API. Browser smoke verified the enabled Delete control, but the in-app browser automation surface could not accept the native `confirm` dialog; Batch 7 should cover reset-after-delete either with a focused browser route smoke that can handle dialogs or a cheaper frontend/module test if the harness supports it.

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

- `$HOME/miniconda3/bin/python3 -m pytest -q admin-app/tests/python/test_target_map_resolver.py admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_run_reports.py admin-app/tests/python/test_files_report.py admin-app/tests/python/test_admin_checks_api.py` - 24 passed.
- `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile admin-checks --run-id batch-7-admin-checks` - passed; summary: `var/admin/test-runs/batch-7-admin-checks/summary.md`.
- No focused Admin route smoke was added. The remaining Batch 6 delete/reset concern is covered at the validated API boundary by safe run snapshot deletion and invalid-id rejection tests.

## follow-on tasks

- Batch 8 reviews legacy risk capabilities and frames child requests for later reports.

## task close

- Batch 8 handoff note added.
- Batch status and front matter `ui_status` set to `done`.
