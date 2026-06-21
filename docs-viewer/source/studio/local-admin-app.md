---
doc_id: local-admin-app
title: Local Admin App
added_date: 2026-06-06
last_updated: 2026-06-10
parent_id: admin
---
# Local Admin App

This document defines the operational boundary for the Local Admin app server.

## Server Boundary

The Python Admin app server can be started directly:

```bash
$HOME/miniconda3/bin/python3 admin-app/app/server/admin_app/admin_app_server.py --port 8768
```

`bin/local-admin` starts this app server.
`bin/local-all` supervises it as a sibling service when `ADMIN_APP_ENABLED` is not `0`.
Use `ADMIN_APP_PORT=<port>` to move it when `8768` is already in use.
Set `ADMIN_APP_ACCESS_LOG=1`, or pass `--access-log` to `admin_app_server.py`, when detailed request logging is needed.

The Admin app server owns:

- `/admin/`
- `/admin/audits/`
- `/admin/checks/`
- `/admin/activity/`
- `/admin/testing/`
- `/admin/runtime-config.json`
- `/admin/api/audits/...`
- `/admin/api/checks/...`
- `/admin/api/activity/...`
- `/admin/api/testing/...`
- Admin static assets under `/admin/app/...`

## Source Layout

Current Admin-owned source homes:

| Path | Owner / role |
| --- | --- |
| `admin-app/app/server/admin_app/` | Admin app server, Admin route views, runtime config projection, API dispatch, static serving, and audit allowlist. |
| `admin-app/app/frontend/` | Admin browser modules, route modules, route state helpers, transport helpers, route registry, and UI text config. |
| `admin-app/app/assets/css/admin.css` | Admin shell, navigation, route layout, and Admin-owned page styling. |
| `admin-app/checks/` | Repo-scope checks, report producers, source-boundary audits, public-surface audits, runtime audits, CSS/JS inventories, and projection contract checks. |
| `admin-app/commands/run_checks.py` | Top-level optional check runner and profile registry. |
| `admin-app/tests/python/` | Admin server, runner, audit/check contract, activity contract, and repo-scope deterministic tests. |
| `admin-app/tests/smoke/` | Admin route browser smoke scripts. |
| `var/admin/activity/` | Ignored local unified activity feed and journal. |
| `var/admin/checks/` | Ignored local Admin checks report runs and review artifacts. |
| `var/admin/test-runs/` | Ignored local check profile summaries and command logs. |

## Runtime Config

Local Admin views declare the runtime config endpoint with `meta[name="dlf-admin-config-url"]`.
`/admin/runtime-config.json` exposes:

- Admin route ids, labels, titles, paths, scripts, and navigation visibility from `admin-app/app/frontend/config/admin-config.json`
- service endpoints for activity, audits, checks, and testing
- UI text paths under `/admin/app/frontend/config/ui-text/...`
- local output paths for activity, checks runs, and testing run summaries
- sibling links to Studio, Analytics, and Docs Viewer

Admin routes do not use management query state.
There is no public Admin mode.
The `/admin/` home renders only Admin-owned route links; sibling app links can remain runtime config data without being surfaced in the top nav or home link groups.

## APIs

Admin APIs are loopback-only operational endpoints.
Browser requests select from explicit local actions and never send arbitrary shell commands, filesystem paths, unchecked environment values, or unvalidated script flags.

Endpoint ownership is split by adapter:

- `admin_audit_api.py` exposes audit health, allowlisted audit list, and allowlisted audit execution.
- `admin_checks_api.py` exposes report metadata, allowlisted report runs, recent run reads, summary/report reads, and deletion of local run snapshots.
- `admin_activity_api.py` exposes the unified Admin activity feed under `/admin/api/activity/feed`.
- `admin_testing_api.py` exposes local check-run summaries under `/admin/api/testing/runs`.

The allowlisted audit runner lives at `admin-app/app/server/admin_app/audit_runner.py`.
Admin Checks report producers live under `admin-app/checks/reports/`.
The check runner writes summaries under `var/admin/test-runs/`.

## Current Checks

Current focused Admin checks:

- server and config: `admin-app/tests/python/test_admin_app_server.py`
- operations routes and APIs: `admin-app/tests/python/test_admin_operations.py`
- runner/profile contract: `admin-app/tests/python/test_admin_runner_contract.py`
- checks route/API: `admin-app/tests/python/test_admin_checks_api.py`
- activity contract wrapper: `admin-app/tests/python/test_activity_contract.py`
- route smokes: `admin-app/tests/smoke/admin_home_route.py` and `admin-app/tests/smoke/admin_operations_routes.py`
