---
doc_id: studio-risk-priority-dashboard
title: Studio Risk Priority Dashboard
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: review
parent_id: audit
viewable: true
---
# Studio Risk Priority Dashboard

This dashboard is the short app-level decision surface for risk-reduction work.
Use it before reading the inventories.

The policy is [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).
Operational ownership is [Studio Risk Operations](/docs/?scope=studio&doc=studio-risk-operations): risk dashboards, app inventories, audits, activity, and risk-related local artifacts belong in Local Studio rather than a separate server.
Risk evidence packs can be run and reviewed from `/studio/risk/?mode=manage` in Local Studio.

## Current Message

Risk work should now be organised by app.
Frontend, backend, docs, generated-data, and workflow evidence can all support the same priority, but the action must improve the app rather than follow a separate technical queue.

The first reconciliation pass has moved the active technical-inventory evidence into app-owned inventories under this dashboard.
The older JavaScript and Python/Ruby inventories remain detailed transition evidence until the retirement/reduction task decides their final shape.

## Current Priorities

| # | App | Area | Risk summary | Change request |
| ---: | --- | --- | --- | --- |
| 1 | All apps | Risk analysis inventory redesign | Planning / evidence: current evidence is split across technical inventories, making app-level action selection harder than it should be. | [Risk Analysis Inventory Redesign Request](/docs/?scope=studio&doc=site-request-risk-analysis-inventory-redesign) |
| 2 | Public Site and app runtimes | Rubyless app runtime boundary | Architectural fit: Ruby/Jekyll should remain public-site preview/build tooling only; app-facing builders and local runtimes should consolidate around Python and JavaScript. | [Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes) |
| 3 | Studio | Catalogue save/build path | Workflow and performance / cost: catalogue saves can touch source JSON, backups, lookup refreshes, generated public data, search, media, publication state, and activity rows. Diagnostics are needed before scope-reduction work becomes actionable. | [Catalogue Save Build Diagnostics Request](/docs/?scope=studio&doc=site-request-catalogue-save-build-diagnostics) |
| 4 | Docs Viewer | Runtime, public read-only installs, and management UI | Structural and performance / cost: Docs Viewer is both a frequently used local tool and a public read-only runtime, so controller boundaries, payload cost, and UI structure should be prioritised together. | [Docs Viewer Runtime Risk Reduction Request](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-risk-reduction) |
| 5 | Analytics | Analytics and Data Sharing growth path | Architectural fit and structural: future visualisation, analytical dimensions, and LLM data-sharing work need an app-owned inventory before new feature work creates another broad route family. | [Analytics Data Sharing Growth Path Request](/docs/?scope=studio&doc=site-request-analytics-data-sharing-growth-path) |

## App Inventories

The app inventories are child documents of this dashboard.
They should contain both frontend and backend evidence where that evidence affects the app.

- [Public Site Risk Inventory](/docs/?scope=studio&doc=public-site-risk-inventory)
- [Studio App Risk Inventory](/docs/?scope=studio&doc=studio-app-risk-inventory)
- [Analytics Risk Inventory](/docs/?scope=studio&doc=analytics-risk-inventory)
- [Docs Viewer Risk Inventory](/docs/?scope=studio&doc=docs-viewer-risk-inventory)
- [Studio Risk Operations](/docs/?scope=studio&doc=studio-risk-operations)
- [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack)

Reduced transition evidence:

- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)

## Update Rules

Update this dashboard when:

- an app inventory changes its top priority
- a change request is opened, paused, completed, or replaced
- diagnostics change whether a performance or workflow concern is actionable
- a technical inventory row changes app-level priority

Keep this page short.
Detailed evidence belongs in the app inventory or the change-request document that owns the work.
