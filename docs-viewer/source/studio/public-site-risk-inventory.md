---
doc_id: public-site-risk-inventory
title: Public Site Risk Inventory
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: studio-risk-priority-dashboard
viewable: true
---
# Public Site Risk Inventory

This inventory records risk evidence for the public site as a user-facing catalogue of artwork and text hosted on GitHub Pages.

Policy: [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).
Dashboard: [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard).

## Priority Order

1. Performance / cost
2. Architectural fit
3. Structural
4. Workflow
5. Planning / evidence

## Current Evidence

| Area | Indicator | Evidence | Current action |
| --- | --- | --- | --- |
| Public route and media payloads | Performance / cost | Public pages are media-heavy and user-facing, so route payload, image derivation, and runtime responsiveness are more important here than in local-only tools. | Use this inventory to collect public-route performance evidence before opening optimisation work. |
| Jekyll/public-build boundary | Architectural fit | Jekyll remains the public preview/build layer, while app-facing runtimes are moving toward Python and JavaScript. | Track app-facing Ruby removal in [Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes). |
| Catalogue taxonomy | Structural | Catalogue structure is complex but relatively stable, with modest record growth. | Treat taxonomy changes as deliberate app-level changes rather than opportunistic refactors. |

## Transition Notes

Older frontend and script inventories contain public-site evidence but are not the priority surface.
Move only actionable public-site evidence into this document.
