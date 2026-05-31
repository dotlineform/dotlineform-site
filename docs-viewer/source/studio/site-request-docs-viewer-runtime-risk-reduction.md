---
doc_id: site-request-docs-viewer-runtime-risk-reduction
title: Docs Viewer Runtime Risk Reduction Request
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Runtime Risk Reduction Request

Status:

- draft

## Summary

Refresh Docs Viewer runtime risk-reduction work around the current app-owned inventory instead of the older broad app-shell requests.

Docs Viewer is both a local management tool and the runtime for public read-only installs such as `/library/` and `/analysis/`.
The next work should reduce controller/runtime risk and route-load cost through focused owner slices, while preserving the public/manage authority split.

## Goals

- choose small runtime slices from [Docs Viewer Risk Inventory](/docs/?scope=studio&doc=docs-viewer-risk-inventory)
- keep public-safe runtime behavior separate from management-only service and write authority
- reduce app runtime/controller growth by extending focused owners rather than broad route state
- use risk evidence packs before prioritising payload or route-load work
- keep Docs Viewer runtime, management UI, generated-data reads, and management endpoints documented together when contracts change

## Non-Goals

- reviving the older broad multi-panel request as a single implementation task
- adding a plugin system or third-party visualization framework
- changing source write authority from management endpoints
- replacing the Docs Viewer builder in this request; that belongs to [Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes)

## Evidence

[Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) currently has 62 focused Docs Viewer rows, with 14 above target score 4 and 7 at score 6 or higher.
The active rows are concentrated in app runtime coordination, management, bookmarks, scope lifecycle, import, config, search, document, reports, and router controllers.

Evidence pack `var/studio/risk/runs/codex-docs-viewer-runtime-smoke-2/summary.md` collected Docs Viewer static metrics, generated payload counts, git touch counts, and JavaScript inventory guardrail output.

Related request history:

- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell) remains a historical broad request that says remaining work should be split into smaller current requests.
- [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts) owns the durable current panel-host architecture.

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Run or review a focused Docs Viewer risk evidence pack for the specific runtime area being considered. |
| 2 | planned | Select one owner slice from the current high-risk rows, such as app runtime coordination, management actions, bookmarks, scope lifecycle, import, config, search, document, reports, or router behavior. |
| 3 | planned | Define the owner module, public/manage availability, backend/service contract, and behavior that must not move back into the app runtime coordinator. |
| 4 | planned | Implement the focused slice with module-level tests or browser smokes appropriate to the changed behavior. |
| 5 | planned | Update [Docs Viewer Risk Inventory](/docs/?scope=studio&doc=docs-viewer-risk-inventory), [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), and durable Docs Viewer owner docs after verification. |
| 6 | planned | Decide whether the completed slice changes the dashboard priority or opens a follow-on request. |

## Acceptance Criteria

- each implementation slice names a focused owner before code changes begin
- public read-only routes do not load or receive management-only authority unnecessarily
- management writes stay behind named management endpoints and server-side validation
- focused tests or smokes cover moved behavior
- inventory rows are updated only after verification supports the score or owner change
