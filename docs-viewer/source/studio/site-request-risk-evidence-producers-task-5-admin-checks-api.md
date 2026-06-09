---
doc_id: site-request-risk-evidence-producers-task-5-admin-checks-api
title: Risk Evidence Producers Task 5 Admin Checks API
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: done
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 5 Admin Checks API

This is the delivery specification for Batch 5 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 5: Add Admin checks API

Summary: Add the local Admin API for metadata, runs, safe artifact reads, and snapshot deletion.

| ID | status | action |
| --- | --- | --- |
| 5.1 | done | Add `/admin/api/checks/health`. |
| 5.2 | done | Add `/admin/api/checks/reports` for configured scopes, target layers, reports, and safe option metadata. |
| 5.3 | done | Add `/admin/api/checks/runs` for recent run listing and validated run creation. |
| 5.4 | done | Add safe reads for `/admin/api/checks/runs/<run-id>/summary` and `/admin/api/checks/runs/<run-id>/reports/<report-id>`. |
| 5.5 | done | Return raw markdown strings from safe reads, following `/admin/risk/`; do not return rendered HTML. |
| 5.6 | done | Add safe deletion for `/admin/api/checks/runs/<run-id>` that removes one local snapshot under `var/admin/checks/`. |
| 5.7 | done | Use strict run-id and report-id validation before reading local artifacts. |
| 5.8 | done | Use the same strict run-id validation before deleting local artifacts and reject paths outside the checks runs root. |
| 5.9 | done | Do not add Activity rows in v1; leave Activity integration for a later Admin Activity review. |

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

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/app/server/admin_app/admin_checks_api.py admin-app/app/server/admin_app/admin_app_server.py admin-app/tests/python/test_admin_checks_api.py`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_checks_api.py admin-app/tests/python/test_admin_app_server.py admin-app/tests/python/test_run_reports.py admin-app/tests/python/test_files_report.py admin-app/tests/python/test_admin_checks_config.py`
- Real config smoke through `checks_get_payload()` and `checks_post_response()` confirmed health, metadata, and a dry-run plan with `files.limit: 20`.

Focused pytest result: 26 passed.

## follow-on tasks

- Batch 6 consumes this API in the `/admin/checks/` UI.
- Batch 6 should use these endpoints:

```text
GET    /admin/api/checks/health
GET    /admin/api/checks/reports
GET    /admin/api/checks/runs
POST   /admin/api/checks/runs
GET    /admin/api/checks/runs/<run-id>/summary
GET    /admin/api/checks/runs/<run-id>/reports/<report-id>
DELETE /admin/api/checks/runs/<run-id>
```

- Run creation accepts the same JSON shape as `admin-app/checks/run_reports.py`.
- Summary reads return `summary` and raw `summary_markdown`.
- Report reads return `report`, raw `report_markdown`, and optional CSV metadata such as `report_csv_path`.
- The UI should display markdown as escaped preformatted text and should not render markdown as HTML.
- Activity integration remains out of scope.

## task close

- Batch 5 is complete.
- Added `admin-app/app/server/admin_app/admin_checks_api.py`.
- Registered `/admin/api/checks/...` in `admin-app/app/server/admin_app/admin_app_server.py`.
- Added focused API tests in `admin-app/tests/python/test_admin_checks_api.py`.
