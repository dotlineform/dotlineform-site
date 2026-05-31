---
doc_id: docs-viewer-risk-inventory
title: Docs Viewer Risk Inventory
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: studio-risk-priority-dashboard
viewable: true
---
# Docs Viewer Risk Inventory

This inventory records risk evidence for Docs Viewer local management, Studio docs, document publishing, and public read-only installs.

Policy: [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).
Dashboard: [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard).

## Priority Order

1. Structural
2. Performance / cost
3. Architectural fit
4. Workflow
5. Planning / evidence

## Evidence Intake

Record deterministic evidence with the command, source, or report that produced it.
Record subjective review and user feedback with the source, symptom, confidence level, and proposed change request.

## Current Evidence

| Area | Indicator | Evidence | Current action |
| --- | --- | --- | --- |
| Runtime and controller families | Structural | Docs Viewer has focused owners, but management, bookmark, search, config, and remaining runtime handoffs still need clear app-owned boundaries. [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) currently has 62 focused Docs Viewer rows, with 14 above target score 4 and 7 at score 6 or higher. The active rows are concentrated in app runtime coordination, management, bookmarks, scope lifecycle, import, config, search, document, reports, and router controllers. | Open or refresh a Docs Viewer runtime change request before further controller/performance work. Future route/document workflow changes should extend focused runtime owners rather than adding responsibility back to the app runtime coordinator. |
| Public read-only installs | Performance / cost | `/library/` and `/analysis/` use Docs Viewer runtime on the public site, so frontend payload and interaction cost are public concerns, not only local tooling concerns. Evidence pack `var/studio/risk/runs/codex-docs-viewer-runtime-smoke-2/summary.md` collected Docs Viewer static metrics, generated payload counts, git touch counts, and JavaScript inventory guardrail output. | Use focused evidence packs before prioritising payload or route-load work, and keep public-safe hosted views separate from management-only surfaces. |
| Docs generation/search | Architectural fit | Docs Viewer generation and search should move toward Python/JavaScript app tooling rather than app-facing Ruby/Jekyll builders. The Python/Ruby inventory classifies `docs-viewer/` as high maintenance, medium structure, and medium performance risk across 30 files and 13,577 lines. | Track app-facing Ruby removal in [Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes). Keep builder, watcher, management response, and search contracts documented together when generated Docs Viewer schema changes. |
| Management writes and rebuilds | Workflow | Source mutation, generated payloads, search, diagnostics, imports, and exports cross local service and builder boundaries. The Python/Ruby inventory identifies docs build, import, export, management mutations, generated reads, live rebuild, and search coordination as cross-language risk where targeted docs payload rebuilds help but resolver-data fallbacks still need care. | Keep rebuild diagnostics, import/export evidence, and management write contracts in this app inventory. Do not move management writes, imports, settings, scope lifecycle, rebuilds, source opening, or local-only reads outside the named management service boundary. |

## Transition Notes

The detailed Docs Viewer frontend and backend rows stay in the old technical inventories until task 11 decides their final shape.
This app inventory is now the decision surface for Docs Viewer risk work.
The paused [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) is historical evidence but needs rewriting before it can own current risk-reduction work.
