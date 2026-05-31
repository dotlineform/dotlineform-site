---
doc_id: analytics-risk-inventory
title: Analytics Risk Inventory
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: studio-risk-priority-dashboard
viewable: true
---
# Analytics Risk Inventory

This inventory records risk evidence for the Analytics app, analytical dimensions, and Data Sharing workflows.

Policy: [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).
Dashboard: [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard).

## Priority Order

1. Architectural fit
2. Structural
3. Workflow
4. Planning / evidence
5. Performance / cost

## Current Evidence

| Area | Indicator | Evidence | Current action |
| --- | --- | --- | --- |
| Analytics growth path | Architectural fit | Future work is likely to include richer analytical dimensions, third-party visualisation libraries, and LLM-oriented data-sharing flows. | Open a change request before adding another broad route family. |
| Analytics/Data Sharing route families | Structural | Analytics has been decoupled from Studio, but future features need app-owned boundaries so tag, scoring, visualisation, and sharing work do not drift back into Studio-owned surfaces. | Reconcile active Analytics rows from [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory). |
| Data Sharing packages | Workflow | Data Sharing workflows cross app data, exported packages, review/apply steps, and source writes. | Keep workflow evidence app-owned rather than treating it as a generic backend queue. |

## Transition Notes

Local performance is lower priority until visualisation, data volume, or package workflow behavior makes it user-visible or development-blocking.
