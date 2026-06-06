---
doc_id: site-request-admin-app-structure-batch-4
title: Admin App Structure Batch 4
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: planned
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Runner, Checks, Tests, and Fixtures

This is the delivery specification for Batch 4 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 4: Runner, Checks, Tests, and Fixtures

Summary: move repo-scope verification ownership to Admin, including runner output, checks, misplaced tests, and fixtures.

| ID | status | action |
| --- | --- | --- |
| 4.1 | planned | Move `studio/commands/run_checks.py` to `admin-app/commands/run_checks.py` and update command docs, launcher references, and profile paths. |
| 4.2 | planned | Move repo-scope checks from `studio/checks/` to `admin-app/checks/`, leaving catalogue-specific checks with Studio. |
| 4.3 | planned | Move check run output from `var/test-runs/` to `var/admin/test-runs/`. |
| 4.4 | planned | Review current app test folders and move tests to the app or Admin owner that matches the behavior being verified. |
| 4.5 | planned | Review `studio/tests/fixtures/` and move fixtures with the tests or owner contracts that use them. |
| 4.6 | planned | Add Admin runner/profile tests that verify profile expansion, output summary paths, and representative app-local test execution. |
| 4.7 | planned | Add Admin testing route data/API behavior for reading Admin-owned run summaries, if the visible testing page is included in this batch. |

## Steer for these tasks

- Admin owns check profiles, repo-scope orchestration, run summaries, and cross-app verification views.
- App-local tests stay with the app when they verify that app's direct behavior.
- Misplaced tests and fixtures move to their correct owner during this batch.
- Tests should assert Admin runner behavior and Admin output paths.

## Deliverables

- `admin-app/commands/run_checks.py`.
- Admin-owned repo-scope checks.
- `var/admin/test-runs/` output contract.
- Moved tests and fixtures.
- Admin runner/profile tests.
- Optional Admin testing route data/API behavior if implemented in this batch.

## Implementation and policy guidance

- Keep profile names and command ergonomics readable.
- Update references directly to the new runner command.
- Keep app-local test ownership visible in paths and profile definitions.
- Use fixtures local to the test owner where practical.

## Proposed verification set

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/commands/run_checks.py`
- focused pytest for Admin runner/profile behavior
- focused pytest for moved checks
- representative Admin runner invocation with a small profile
- source review for moved fixture references

## completed verification

- pending

## follow-on tasks

- Batch 5 cleans retained Studio routes, app scripts, and source references after Admin owns the moved surfaces.

## task close

- Add a handoff note to Batch 5.
- Set `ui_status` to `done` after runner, checks, tests, and fixture ownership are verified.
