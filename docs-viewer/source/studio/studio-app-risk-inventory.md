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
| Catalogue save/build path | Workflow | A save can touch source JSON, backups, lookup refreshes, generated public data, catalogue search, media derivatives, publication state, and activity rows. | Track diagnostics in [Catalogue Save Build Diagnostics Request](/docs/?scope=studio&doc=site-request-catalogue-save-build-diagnostics). |
| Catalogue route/controller families | Structural | Studio is still completing its move from a broad historical codebase toward route shells, focused frontend owners, and focused Python service owners. [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) currently has 86 Studio frontend modules, with 24 above target score 4 and 7 at score 6 or higher. The active high-risk rows are mainly catalogue action coordinators, editor shells, import helpers, sections, status, and works routes. | Keep new catalogue behavior inside the focused editor state, events, workflow, selection, action, and service modules already named by the JavaScript inventory. Use the JavaScript maintenance gate before touching score-6 Studio files. |
| Studio operational routes and shared runtime | Structural | The old JavaScript inventory keeps Studio operational rows for bulk add, project state, audits, activity, config, modal, route-state, transport, UI, app shell, route registry, navigation, and static route renderers. Many are already at target score 4 after shared operational route helper adoption. | Extend shared Studio primitives only when the contract is identical across routes; avoid pushing route-specific workflow back into shared shell modules. |
| Cross-service local server mechanics | Structural | The Python/Ruby inventory classifies local server mechanics as medium maintenance and medium structure risk across catalogue, Docs Viewer, Studio audit/risk adapters, logging, and Activity helpers. | Standardize request limits, JSON parse errors, CORS headers, compact logs, and activity append contracts only where the service contracts are identical. |
| Rubyless local runtime | Architectural fit | Studio runs as Python services plus JavaScript frontend. Docs Viewer docs/search generation, catalogue search, and catalogue prose rendering are Python-owned; Ruby/Jekyll remains public-site preview/build tooling only. | Keep future Studio app-runtime work inside Python/JavaScript boundaries and treat public-site Jekyll verification as a separate layer. |

## Transition Notes

The detailed Studio rows stay in the old JavaScript and Python/Ruby inventories until task 11 decides their final shape.
This app inventory is now the decision surface for Studio risk work.
Performance concerns are not ignored, but local-only performance should not outrank structural and workflow clarity unless it affects development speed, repeated broad work, or visible user interaction.
