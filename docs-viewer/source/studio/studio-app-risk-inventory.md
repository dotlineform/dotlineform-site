---
doc_id: studio-app-risk-inventory
title: Studio App Risk Inventory
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: studio-risk-priority-dashboard
viewable: true
---
# Studio App Risk Inventory

This inventory records risk evidence for the Local Studio app that manages data published on the public site.

Policy: [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).
Dashboard: [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard).

## Priority Order

1. Structural
2. Workflow
3. Architectural fit
4. Planning / evidence
5. Performance / cost

## Evidence Intake

Record deterministic evidence with the command, source, or report that produced it.
Record subjective review and user feedback with the source, symptom, confidence level, and proposed change request.

## Current Evidence

| Area | Indicator | Evidence | Current action |
| --- | --- | --- | --- |
| Catalogue save/build path | Workflow | A save can touch source JSON, backups, lookup refreshes, generated public data, catalogue search, media derivatives, publication state, and activity rows. | Open a change request for save/build diagnostics before narrowing rebuild scope. |
| Catalogue route/controller families | Structural | Studio is still completing its move from a broad historical codebase toward route shells, focused frontend owners, and focused Python service owners. | Reconcile active Studio rows from [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory). |
| Rubyless local runtime | Architectural fit | Studio should run as Python services plus JavaScript frontend, without app-facing Ruby/Jekyll dependencies. | Track in [Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes). |

## Transition Notes

Performance concerns are not ignored, but local-only performance should not outrank structural and workflow clarity unless it affects development speed, repeated broad work, or visible user interaction.
