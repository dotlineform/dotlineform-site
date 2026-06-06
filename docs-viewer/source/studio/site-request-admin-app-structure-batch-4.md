---
doc_id: site-request-admin-app-structure-batch-4
title: Admin App Structure Batch 4
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: done
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Runner, Checks, Tests, and Fixtures

This is the delivery specification for Batch 4 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 4: Runner, Checks, Tests, and Fixtures

Summary: move repo-scope verification ownership to Admin, including runner output, checks, misplaced tests, and fixtures.

| ID | status | action |
| --- | --- | --- |
| 4.1 | done | Move `studio/commands/run_checks.py` to `admin-app/commands/run_checks.py` and update command docs, launcher references, and profile paths. |
| 4.2 | done | Move repo-scope checks from `studio/checks/` to `admin-app/checks/`, leaving catalogue-specific checks with Studio. |
| 4.3 | done | Move check run output from `var/test-runs/` to `var/admin/test-runs/`. |
| 4.4 | done | Review current app test folders and move tests to the app or Admin owner that matches the behavior being verified. |
| 4.5 | done | Review `studio/tests/fixtures/` and move fixtures with the tests or owner contracts that use them. |
| 4.6 | done | Add Admin runner/profile tests that verify profile expansion, output summary paths, and representative app-local test execution. |
| 4.7 | done | Add Admin testing route data/API behavior for reading Admin-owned run summaries, if the visible testing page is included in this batch. |

## Steer for these tasks

- Admin owns check profiles, repo-scope orchestration, run summaries, and cross-app verification views.
- App-local tests stay with the app when they verify that app's direct behavior.
- Misplaced tests and fixtures move to their correct owner during this batch.
- Tests should assert Admin runner behavior and Admin output paths.

## Batch 3 handoff

- Audit, risk, and activity routes now live under `/admin/audits/`, `/admin/risk/`, and `/admin/activity/`.
- Admin owns the moved browser APIs under `/admin/api/audits/...`, `/admin/api/risk/...`, and `/admin/api/activity/...`.
- Activity output now writes to `var/admin/activity/`; risk evidence runs write to `var/admin/risk/runs/`.
- Focused Admin operations tests live in `admin-app/tests/python/test_admin_operations.py` and `admin-app/tests/smoke/admin_operations_routes.py`.
- `studio/commands/run_checks.py` still references the retired Studio audit/risk modules and retired Studio route smoke names. Move or rewrite those profile entries with the runner in this batch.
- Durable docs still contain old Studio-hosted audit/risk/activity references; leave the broad docs cleanup for Batch 6 unless a runner/check doc must change to keep Batch 4 coherent.

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

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/commands/run_checks.py admin-app/app/server/admin_app/admin_app_config.py admin-app/app/server/admin_app/admin_app_server.py admin-app/app/server/admin_app/admin_app_views.py admin-app/app/server/admin_app/admin_testing_api.py admin-app/app/server/admin_app/admin_risk_api.py admin-app/app/server/admin_app/audit_runner.py admin-app/checks/*.py admin-app/tests/python/test_admin_runner_contract.py admin-app/tests/python/test_admin_app_server.py admin-app/tests/python/test_activity_contract.py admin-app/tests/python/test_javascript_inventory_guardrail.py admin-app/tests/python/test_risk_evidence_pack.py docs-viewer/tests/python/test_docs_viewer_v2_custom_token_fixtures.py docs-viewer/tests/python/test_generated_output_contract_fixtures.py analytics-app/tests/python/test_data_sharing_adapters.py analytics-app/tests/python/test_data_sharing_service.py analytics-app/tests/python/test_data_sharing_subsystem_scaffold.py analytics-app/tests/python/test_tags_data_sharing_adapter.py admin-app/tests/smoke/admin_home_route.py` passed.
- `$HOME/miniconda3/bin/python3 -m pytest -q admin-app/tests/python/test_admin_runner_contract.py admin-app/tests/python/test_admin_app_server.py admin-app/tests/python/test_activity_contract.py admin-app/tests/python/test_javascript_inventory_guardrail.py admin-app/tests/python/test_risk_evidence_pack.py docs-viewer/tests/python/test_docs_viewer_v2_custom_token_fixtures.py docs-viewer/tests/python/test_generated_output_contract_fixtures.py analytics-app/tests/python/test_data_sharing_adapters.py analytics-app/tests/python/test_data_sharing_service.py analytics-app/tests/python/test_data_sharing_subsystem_scaffold.py analytics-app/tests/python/test_tags_data_sharing_adapter.py` passed with 65 tests.
- `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile admin-smoke --run-id admin-batch-4-runner-smoke` passed; summary: `var/admin/test-runs/admin-batch-4-runner-smoke/summary.md`.
- `$HOME/miniconda3/bin/python3 admin-app/checks/audit_projection_contract.py` passed.
- `node --check admin-app/app/frontend/js/admin-testing.js` passed.
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/admin-config.json` passed.
- Source review for retired runner/check/fixture paths passed; only a deliberate negative assertion remains in `admin-app/tests/python/test_admin_runner_contract.py`.
- `git diff --check` passed.

## follow-on tasks

- Batch 5 cleans retained Studio routes, app scripts, and source references after Admin owns the moved surfaces.
- Batch 5 should still review launchers and Studio route cleanup; Batch 4 did not remove generated `__pycache__` directories left under old Studio paths.

## task close

- Add a handoff note to Batch 5.
- Set `ui_status` to `done` after runner, checks, tests, and fixture ownership are verified.
