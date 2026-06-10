---
doc_id: risk-ownership
title: Risk Ownership
added_date: 2026-06-07
last_updated: 2026-06-10
parent_id: admin
viewable: true
---
# Risk Ownership

Risk operations belong in the Admin app. Admin is the central home for:

- risk dashboards and app inventories
- audit launcher UI
- checks report UI
- unified activity review
- allowlisted audit execution adapters
- allowlisted checks report execution adapters
- risk-related local read APIs
- risk-related generated review artifacts that need to be inspected locally

The current Admin app hosts:

- `/admin/audits/`
- `/admin/checks/`
- `/admin/activity/`
- `/admin/testing/`
- `/admin/api/audits/...`
- `/admin/api/checks/...`
- narrow Admin activity and testing APIs

The Admin app shell provides the correct boundary:

- JavaScript owns the route UI
- Python owns local APIs, filesystem access, process execution, and allowlists
- browser code never sends command text, shell flags, arbitrary paths, or environment values

## Ownership

| Surface | Owner | Notes |
| --- | --- | --- |
| Risk policy, dashboard, app inventories | Docs Viewer Studio docs | Source docs live under `docs-viewer/source/studio/` and are rendered by Docs Viewer. |
| Risk/audit/check scripts | `admin-app/checks/` | Deterministic repo-scope checks and standalone audits live here unless a domain-specific service owns the behavior. |
| Audit runner and API adapter | `admin-app/app/server/admin_app/` | `audit_runner.py` owns the allowlist; `admin_audit_api.py` exposes the Admin browser API. |
| Audit UI | Admin app shell | `/admin/audits/` is the launch/read surface. |
| Checks report API adapter | `admin-app/app/server/admin_app/` | `admin_checks_api.py` exposes report metadata, validated report runs, recent runs, summary/report reads, and snapshot deletion. |
| Checks report UI | Admin app shell | `/admin/checks/` is the run/review/delete surface for checks reports. |
| Activity UI | Admin app shell | `/admin/activity/` is the unified activity review surface. |
| Unified activity writer/helpers | `studio/shared/python/studio_activity.py` and fixed activity paths | Domain services emit compact activity rows through shared helper contracts. The helper owns `var/admin/activity/activity_log.jsonl`, `var/admin/activity/activity_log.json`, and the checked-in activity contract path. |
| Local checks reports/artifacts | `var/admin/checks/` by default | Use for ignored local reports, metric snapshots, profiling exports, and review artifacts that should not be checked in. |
| Checked-in risk configuration | `admin-app/checks/` or `admin-app/data/config/` | Use `admin-app/checks/` for check-owned config and `admin-app/data/config/` for app/runtime-visible config. |

The current report system is [Checks](/docs/?scope=studio&doc=admin-checks).

## Server Boundary

Risk operations use the Admin app server.

Allowed:

- add new allowlisted audit IDs to `admin-app/app/server/admin_app/audit_runner.py`
- add narrow Admin API adapters under `admin-app/app/server/admin_app/`
- add route-local JavaScript UI under `admin-app/app/frontend/js/`
- read checked-in or generated risk summaries through explicit read keys or narrow endpoints
- write local reports under `var/admin/checks/` from trusted Python code

Not allowed:

- browser-controlled command text
- browser-controlled filesystem paths for audits or risk scripts
- a generic "run command" API
- a generic "read any risk file" API

## Activity Boundary

Risk-related actions that a user initiates from Admin should write unified activity rows when they produce meaningful local side effects or reports.

Examples:

- running an audit
- generating a risk report
- refreshing an app risk inventory from deterministic inputs
- applying a risk-reduction change that writes generated review output

Background watchers and purely informational route loads should not produce activity rows.

## Route Shape

The current `/admin/audits/`, `/admin/checks/`, and `/admin/activity/` routes live in Admin.
They use:

- route-local shell/body modules
- focused frontend modules for rendering and filtering
- Admin API adapters with allowlisted behavior
- app inventories and change requests as the source of priority state
