---
doc_id: risk-ownership
title: Risk Ownership
added_date: 2026-06-07
last_updated: 2026-06-07
ui_status: review
parent_id: admin
viewable: true
---
# Risk Ownership

This document records the previous Studio risk decision and the current Admin ownership boundary for risk-related audits, activity, scripts, reports, and local artifacts.

## Decision

Risk operations now belong in the Admin app.

Admin is the central home for:

- risk dashboards and app inventories
- audit launcher UI
- unified activity review
- allowlisted audit execution adapters
- risk-related local read APIs
- risk-related generated review artifacts that need to be inspected locally

Local Studio remains focused on catalogue/public-site data maintenance and should not recreate audit, risk, activity, testing, or UI Catalogue routes.

## Rationale

Risk work is operational maintenance for the whole repo, so the active user surface is Admin.
The current Admin app hosts:

- `/admin/audits/`
- `/admin/risk/`
- `/admin/activity/`
- `/admin/testing/`
- `/admin/api/audits/...`
- `/admin/api/risk/...`
- narrow Admin activity and testing APIs

The Admin app shell provides the correct boundary:

- JavaScript owns the route UI
- Python owns local APIs, filesystem access, process execution, and allowlists
- browser code never sends command text, shell flags, arbitrary paths, or environment values

This is the same boundary risk operations need.

## Ownership

| Surface | Owner | Notes |
| --- | --- | --- |
| Risk policy, dashboard, app inventories | Docs Viewer Studio docs | Source docs live under `docs-viewer/source/studio/` and are rendered by Docs Viewer. |
| Risk/audit/check scripts | `admin-app/checks/` | Deterministic repo-scope checks and standalone audits live here unless a domain-specific service owns the behavior. |
| Audit runner and API adapter | `admin-app/app/server/admin_app/` | `audit_runner.py` owns the allowlist; `admin_audit_api.py` exposes the Admin browser API. |
| Audit UI | Admin app shell | `/admin/audits/` is the launch/read surface. |
| Risk evidence API adapter | `admin-app/app/server/admin_app/` | `admin_risk_api.py` exposes producer listing, validated risk evidence runs, recent runs, summary reads, snapshot deletion, and Activity rows. |
| Risk evidence UI | Admin app shell | `/admin/risk/` is the run/review/delete surface for risk evidence packs. |
| Activity UI | Admin app shell | `/admin/activity/` is the unified activity review surface. |
| Unified activity writer/helpers | `studio/shared/python/studio_activity.py` and fixed activity paths | Domain services emit compact activity rows through shared helper contracts. The helper owns `var/admin/activity/activity_log.jsonl`, `var/admin/activity/activity_log.json`, and the checked-in activity contract path. |
| Local risk reports/artifacts | `var/admin/risk/` by default | Use for ignored local reports, metric snapshots, profiling exports, and review artifacts that should not be checked in. |
| Checked-in risk configuration | `admin-app/checks/` or `admin-app/data/config/` | Use `admin-app/checks/` for check-owned config and `admin-app/data/config/` for app/runtime-visible config. |

The concrete run-directory and artifact contract is [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack).

## Server Boundary

Risk operations use the Admin app server.

Allowed:

- add new allowlisted audit IDs to `admin-app/app/server/admin_app/audit_runner.py`
- add narrow Admin API adapters under `admin-app/app/server/admin_app/`
- add route-local JavaScript UI under `admin-app/app/frontend/js/`
- read checked-in or generated risk summaries through explicit read keys or narrow endpoints
- write local reports under `var/admin/risk/` from trusted Python code

Not allowed:

- browser-controlled command text
- browser-controlled filesystem paths for audits or risk scripts
- a generic "run command" API
- a generic "read any risk file" API
- a sibling localhost risk server for ordinary Admin risk work

## Activity Boundary

Risk-related actions that a user initiates from Admin should write unified activity rows when they produce meaningful local side effects or reports.

Examples:

- running a Studio audit
- generating a risk report
- refreshing an app risk inventory from deterministic inputs
- applying a risk-reduction change that writes generated review output

Background watchers and purely informational route loads should not produce activity rows unless a future workflow needs an explicit review trail.

## Route Shape

The current `/admin/audits/`, `/admin/risk/`, and `/admin/activity/` routes live in Admin.
They use:

- route-local shell/body modules
- focused frontend modules for rendering and filtering
- Admin API adapters with allowlisted behavior
- app inventories and change requests as the source of priority state
