---
doc_id: local-admin-app
title: Local Admin App
added_date: 2026-06-06
last_updated: 2026-06-06
parent_id: studio
viewable: true
---
# Local Admin App

This document defines the operational boundary for the Local Admin app server.
Use [Local Runners](/docs/?scope=studio&doc=scripts-local-studio) for startup behavior and environment variables.
Use [Testing](/docs/?scope=studio&doc=testing) and [Run Checks](/docs/?scope=studio&doc=scripts-run-checks) for check profile ownership and run-log behavior.

Local Admin is a sibling local app, separate from Local Studio, Local Analytics, Docs Viewer, and public Jekyll preview/build.
It is the home for cross-repo operational review, risk and audit work, test-run review, and Admin-hosted UI Catalogue routes.

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
- `/admin/risk/`
- `/admin/activity/`
- `/admin/testing/`
- `/admin/ui-catalogue/...`
- `/admin/runtime-config.json`
- `/admin/api/audits/...`
- `/admin/api/risk/...`
- `/admin/api/activity/...`
- `/admin/api/testing/...`
- Admin static assets under `/admin/app/...`
- UI Catalogue demo assets under `/admin/ui-catalogue/...`

The Admin app server does not own:

- Studio catalogue routes or `/studio/api/catalogue/...`
- Analytics routes or `/analytics/api/...`
- Docs Viewer manage-mode routes or Docs Viewer management APIs
- public Jekyll preview/build routes
- retired Studio admin routes such as `/studio/audits/...`, `/studio/risk/...`, `/studio/activity/...`, or `/studio/ui-catalogue/...`
- the retired standalone `ui-catalogue-app` server

## Source Layout

Current Admin-owned source homes:

| Path | Owner / role |
| --- | --- |
| `admin-app/app/server/admin_app/` | Admin app server, Admin route views, runtime config projection, API dispatch, static serving, audit allowlist, and UI Catalogue route views. |
| `admin-app/app/frontend/` | Admin browser modules, route modules, route state helpers, transport helpers, route registry, and UI text config. |
| `admin-app/app/assets/css/admin.css` | Admin shell, navigation, route layout, and Admin-owned page styling. |
| `admin-app/checks/` | Repo-scope checks, risk evidence producers, source-boundary audits, public-surface audits, runtime audits, CSS/JS inventories, and projection contract checks. |
| `admin-app/commands/run_checks.py` | Top-level optional check runner and profile registry. |
| `admin-app/tests/python/` | Admin server, runner, risk/audit contract, UI Catalogue, activity contract, and repo-scope deterministic tests. |
| `admin-app/tests/smoke/` | Admin route and Admin-hosted UI Catalogue browser smoke scripts. |
| `admin-app/ui-catalogue/` | UI Catalogue demo source, scoped demo CSS/JS, palette/reference source, demo assets, and reference asset folders. |
| `var/admin/activity/` | Ignored local unified activity feed and journal. |
| `var/admin/risk/` | Ignored local risk evidence runs and review artifacts. |
| `var/admin/test-runs/` | Ignored local check profile summaries and command logs. |

## Runtime Config

Local Admin views declare the runtime config endpoint with `meta[name="dlf-admin-config-url"]`.
`/admin/runtime-config.json` exposes:

- Admin route ids, labels, titles, paths, scripts, and navigation visibility from `admin-app/app/frontend/config/admin-config.json`
- service endpoints for activity, audits, risk, and testing
- UI text paths under `/admin/app/frontend/config/ui-text/...`
- local output paths for activity, risk runs, and testing run summaries
- sibling links to Studio, Analytics, and Docs Viewer

Admin routes do not use `?mode=manage`.
There is no public Admin mode.

## APIs

Admin APIs are loopback-only operational endpoints.
Browser requests select from explicit local actions and never send arbitrary shell commands, filesystem paths, unchecked environment values, or unvalidated script flags.

Endpoint ownership is split by adapter:

- `admin_audit_api.py` exposes audit health, allowlisted audit list, and allowlisted audit execution.
- `admin_risk_api.py` exposes risk producer list, validated evidence runs, recent run reads, summary reads, deletion of local run snapshots, and Activity rows for user-initiated write runs.
- `admin_activity_api.py` exposes the unified Admin activity feed under `/admin/api/activity/feed`.
- `admin_testing_api.py` exposes local check-run summaries under `/admin/api/testing/runs`.

The allowlisted audit runner lives at `admin-app/app/server/admin_app/audit_runner.py`.
The risk evidence pack producers live under `admin-app/checks/`.
The check runner writes summaries under `var/admin/test-runs/`.

## UI Catalogue

UI Catalogue is Admin-hosted because it is a cross-app design and verification aid.
The route family is `/admin/ui-catalogue/...`.
Demo CSS and JavaScript stay UI Catalogue-scoped under `admin-app/ui-catalogue/` and are not merged into `admin.css`.

Do not recreate:

- `/studio/ui-catalogue/...`
- `/ui-catalogue/...`
- the standalone `ui-catalogue-app` server

## Current Checks

Current focused Admin checks:

- server and config: `admin-app/tests/python/test_admin_app_server.py`
- operations routes and APIs: `admin-app/tests/python/test_admin_operations.py`
- runner/profile contract: `admin-app/tests/python/test_admin_runner_contract.py`
- risk evidence pack: `admin-app/tests/python/test_risk_evidence_pack.py`
- activity contract wrapper: `admin-app/tests/python/test_activity_contract.py`
- UI Catalogue: `admin-app/tests/python/test_admin_ui_catalogue.py`
- route smokes: `admin-app/tests/smoke/admin_home_route.py`, `admin-app/tests/smoke/admin_operations_routes.py`, `admin-app/tests/smoke/admin_ui_catalogue_routes.py`, and `admin-app/tests/smoke/admin_ui_catalogue_modal_demo.py`

## Related Docs

- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Local Runners](/docs/?scope=studio&doc=scripts-local-studio)
- [Studio Risk Operations](/docs/?scope=studio&doc=studio-risk-operations)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
