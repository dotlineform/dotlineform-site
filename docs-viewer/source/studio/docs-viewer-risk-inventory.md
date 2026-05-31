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
| Runtime and controller families | Structural | Docs Viewer has focused owners, but management, bookmark, search, config, and remaining runtime handoffs still need clear app-owned boundaries. | Reconcile active rows from [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory). |
| Public read-only installs | Performance / cost | `/library/` and `/analysis/` use Docs Viewer runtime on the public site, so frontend payload and interaction cost are public concerns, not only local tooling concerns. | Open or refresh a Docs Viewer runtime change request before further controller/performance work. |
| Docs generation/search | Architectural fit | Docs Viewer generation and search should move toward Python/JavaScript app tooling rather than app-facing Ruby/Jekyll builders. | Track in [Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes). |
| Management writes and rebuilds | Workflow | Source mutation, generated payloads, search, diagnostics, imports, and exports cross local service and builder boundaries. | Keep rebuild diagnostics and import/export evidence in this app inventory during reconciliation. |

## Transition Notes

The paused [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) is historical evidence but needs rewriting before it can own current risk-reduction work.
