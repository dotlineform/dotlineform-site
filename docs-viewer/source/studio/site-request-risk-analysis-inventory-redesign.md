---
doc_id: site-request-risk-analysis-inventory-redesign
title: Risk Analysis Inventory Redesign Request
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Risk Analysis Inventory Redesign Request

Status:

- in progress

## Summary

Redesign risk analysis so priorities are selected by app rather than by separate frontend, backend, or script tables.

The dashboard should show the active app-level priority order and the change request that owns each active improvement.
The app inventories should sit under [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard) and contain both frontend and backend evidence where that evidence affects the app.

## Goals

- keep [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy) as the shared vocabulary
- keep [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard) short and app-level
- create app-owned inventory documents under the dashboard
- keep older technical inventories as transition evidence until their useful rows have been reconciled into app inventories
- make change requests the owner for active risk-reduction work

## Non-Goals

- rescoring every JavaScript file in this request
- rewriting every script-family inventory row in this request
- changing application code as part of the inventory redesign
- treating frontend and backend as separate priority queues when they affect the same app

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Replace the old maintenance-oriented risk policy with actual risks, observable indicators, and app priority order. |
| 2 | done | Reshape the dashboard around app, area, risk summary, and change request ownership. |
| 3 | done | Add app inventory child documents under the dashboard. |
| 4 | planned | Reconcile the older JavaScript and Python/Ruby inventories into the app inventories without losing current useful evidence. |
| 5 | planned | Open or refresh change requests for dashboard priorities that still say `Needs change request`. |
| 6 | planned | Retire or reduce the old technical inventory pages once the app inventories carry the active evidence. |

## Close-Out Evidence

- dashboard priorities point to active change requests or explicitly say that a change request is needed
- each app has a child risk inventory under the dashboard
- old technical inventories no longer act as the primary priority surface
- policy, dashboard, and app inventories use the same indicator vocabulary
