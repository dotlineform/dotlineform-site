---
doc_id: studio-risk-operations
title: Studio Risk Operations
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: review
parent_id: studio-risk-priority-dashboard
viewable: true
---
# Studio Risk Operations

This document finalises the runtime and source ownership decision for risk-related audits, activity, scripts, reports, and local artifacts.

## Decision

Risk operations belong in Local Studio.

Local Studio is the central home for:

- risk dashboards and app inventories
- audit launcher UI
- unified activity review
- allowlisted audit execution adapters
- risk-related local read APIs
- risk-related generated review artifacts that need to be inspected from Studio

Do not create a separate risk server for the current risk-analysis work.
A new server should be considered only if a future requirement cannot fit the Local Studio app server's allowlisted adapter model without weakening route ownership, write allowlists, or process boundaries.

## Rationale

Risk work is operational maintenance for the whole repo, but the active user surface is Local Studio.
The current Studio app already hosts:

- `/studio/audits/?mode=manage`
- `/studio/risk/?mode=manage`
- `/studio/activity/?mode=manage`
- `/studio/api/audits/...`
- `/studio/api/risk/...`
- Studio catalogue/admin read APIs used by operational pages

The Studio app shell also provides the correct boundary:

- JavaScript owns the route UI
- Python owns local APIs, filesystem access, process execution, and allowlists
- browser code never sends command text, shell flags, arbitrary paths, or environment values

This is the same boundary risk operations need.

## Ownership

| Surface | Owner | Notes |
| --- | --- | --- |
| Risk policy, dashboard, app inventories | Docs Viewer Studio docs | Source docs live under `docs-viewer/source/studio/` and are rendered by Docs Viewer. |
| Risk/audit/check scripts | `studio/checks/` | Deterministic checks and standalone audits live here unless a domain-specific service already owns the behavior. |
| Audit runner and API adapter | `studio/app/server/studio/` | `audit_runner.py` owns the allowlist; `studio_audit_api.py` exposes the Local Studio browser API. |
| Audit UI | Local Studio app shell | `/studio/audits/?mode=manage` remains the launch/read surface. |
| Risk evidence API adapter | `studio/app/server/studio/` | `studio_risk_api.py` exposes producer listing, validated risk evidence runs, recent runs, summary reads, and Activity rows. |
| Risk evidence UI | Local Studio app shell | `/studio/risk/?mode=manage` is the run/review surface for risk evidence packs. |
| Activity UI | Local Studio app shell | `/studio/activity/?mode=manage` remains the unified activity review surface. |
| Unified activity writer/helpers | `studio/shared/python/studio_activity.py` and fixed activity paths | Domain services emit compact activity rows through shared helper contracts. The helper owns `var/studio/activity/activity_log.jsonl`, `var/studio/activity/activity_log.json`, and the checked-in activity contract path. |
| Local risk reports/artifacts | `var/studio/risk/` by default | Use for ignored local reports, metric snapshots, profiling exports, and review artifacts that should not be checked in. |
| Checked-in risk configuration | `studio/checks/` or `studio/data/config/` | Use `studio/checks/` for check-owned config and `studio/data/config/` for app/runtime-visible config. |
| Studio-readable generated risk summaries | `studio/data/generated/risk/` only when needed | Use only for generated read models intentionally served by Local Studio. Most local artifacts should stay in `var/studio/risk/`. |

The concrete run-directory and artifact contract is [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack).

## Server Boundary

Risk operations use the Local Studio app server.

Allowed:

- add new allowlisted audit IDs to `studio/app/server/studio/audit_runner.py`
- add narrow Studio API adapters under `studio/app/server/studio/`
- add route-local JavaScript UI under `studio/app/frontend/js/`
- read checked-in or generated risk summaries through explicit read keys or narrow endpoints
- write local reports under `var/studio/risk/` from trusted Python code

Not allowed:

- browser-controlled command text
- browser-controlled filesystem paths for audits or risk scripts
- a generic "run command" API
- a generic "read any risk file" API
- a sibling localhost risk server for ordinary Studio risk work

## Activity Boundary

Risk-related actions that a user initiates from Studio should write unified activity rows when they produce meaningful local side effects or reports.

Examples:

- running a Studio audit
- generating a risk report
- refreshing an app risk inventory from deterministic inputs
- applying a risk-reduction change that writes generated review output

Background watchers and purely informational route loads should not produce activity rows unless a future workflow needs an explicit review trail.

## Route Shape

The current `/studio/audits/`, `/studio/risk/`, and `/studio/activity/` routes remain in Studio.

The risk route is tracked in [Studio Risk Route Request](/docs/?scope=studio&doc=site-request-studio-risk-route).
It uses:

- route-local shell/body modules
- focused frontend modules for rendering and filtering
- Local Studio API adapters with allowlisted behavior
- app inventories and change requests as the source of priority state

## Related References

- [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard)
- [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy)
- [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack)
- [Studio Risk Route Request](/docs/?scope=studio&doc=site-request-studio-risk-route)
- [Studio Audits](/docs/?scope=studio&doc=studio-audits)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Studio Audit Runner](/docs/?scope=studio&doc=scripts-studio-audit-service)
