---
doc_id: studio-risk-priority-dashboard
title: Studio Risk Priority Dashboard
added_date: 2026-05-31
last_updated: 2026-05-31
parent_id: admin
---
# Studio Risk Priority Dashboard

This dashboard is the short app-level decision surface for risk-reduction work.
Use it before reading the inventories.

- The policy is [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).
- Operational ownership is [Risk Ownership](/docs/?scope=studio&doc=risk-ownership): risk dashboards, app inventories, audits, activity, and risk-related local artifacts belong in Admin.
- Risk evidence packs can be run and reviewed from `/admin/risk/` in Admin.

## Current Message

Risk work should now be organised by app.
Frontend, backend, docs, generated-data, and workflow evidence can all support the same priority, but the action must improve the app rather than follow a separate technical queue.

The first reconciliation pass has moved the active technical-inventory evidence into app-owned inventories under this dashboard.
The older JavaScript and Python/Ruby inventories remain detailed transition evidence until the retirement/reduction task decides their final shape.

## App Inventories

The app inventories are child documents of this dashboard.
They should contain both frontend and backend evidence where that evidence affects the app.

- [Public Site Risk Inventory](/docs/?scope=studio&doc=public-site-risk-inventory)
- [Studio App Risk Inventory](/docs/?scope=studio&doc=studio-app-risk-inventory)
- [Analytics Risk Inventory](/docs/?scope=studio&doc=analytics-risk-inventory)
- [Docs Viewer Risk Inventory](/docs/?scope=studio&doc=docs-viewer-risk-inventory)
- [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack)

Reduced transition evidence:

- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)

## Update Rules

Update this dashboard when:

- an app inventory changes its top priority
- a change request is opened, paused, completed, or replaced
- diagnostics change whether a performance or workflow concern is actionable
- a technical inventory row changes app-level priority

Keep this page short.
Detailed evidence belongs in the app inventory or the change-request document that owns the work.
