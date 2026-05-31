---
doc_id: site-request-analytics-data-sharing-growth-path
title: Analytics Data Sharing Growth Path Request
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: change-requests
viewable: true
---
# Analytics Data Sharing Growth Path Request

Status:

- draft

## Summary

Define the next Analytics and Data Sharing growth path before adding richer analysis, visualization, or LLM-oriented package workflows.

Analytics is now separated from Studio, and Data Sharing is an Analytics-owned workflow.
The risk is future feature growth drifting back into broad route families, generic scripts, or Studio-owned surfaces.

## Goals

- define the app-owned boundary for future analytical dimensions, visualization, and data-sharing workflow growth
- keep tag route behavior inside Analytics frontend and backend owners
- keep Data Sharing prepare, review, apply, adapter, package, and artifact behavior app-owned
- choose visualization or LLM data contracts before adding libraries or UI surfaces
- keep Studio from becoming the default coordinator for Analytics or Data Sharing behavior

## Non-Goals

- adding a visualization library before the data contract is clear
- adding LLM workflow features in the planning slice
- reintroducing Studio tag routes, Studio tag source paths, or Studio Data Sharing artifact roots
- treating Data Sharing as a generic backend queue detached from the Analytics app

## Evidence

[Analytics Risk Inventory](/docs/?scope=studio&doc=analytics-risk-inventory) identifies the Analytics growth path as an architectural-fit priority.
[Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) currently has 54 Analytics frontend modules, with 14 above target score 4 and 4 at score 6 or higher.
The active rows are concentrated in tag editors, tag registry/aliases modals, Series Tags, and Data Sharing package routes.

[Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory) classifies `analytics-app/app/server/analytics_app/tag_services/` as medium maintenance, medium structure, and low performance risk across 10 files and 4,419 lines.
It also notes that Data Sharing and tag import/apply flows remain broad enough to watch.

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory the next likely Analytics and Data Sharing feature surfaces: analytical dimensions, visualizations, exported package review, apply workflows, and LLM-oriented data-sharing flows. |
| 2 | planned | Define the app-owned frontend and backend owner modules for each proposed feature surface. |
| 3 | planned | Define data contracts before choosing visualization libraries, LLM package shape, or new route UI. |
| 4 | planned | Identify route-family work that should be split before new features are added to existing high-risk modules. |
| 5 | planned | Add focused tests or smokes for any owner boundaries that are formalized in code. |
| 6 | planned | Update [Analytics Risk Inventory](/docs/?scope=studio&doc=analytics-risk-inventory), Data Sharing docs, and related app docs after the growth-path decision is durable. |

## Acceptance Criteria

- future Analytics feature work has named frontend and backend owners
- Data Sharing remains Analytics-owned while shared package mechanics stay in `data-sharing/`
- Studio does not regain tag route, tag source, or Data Sharing workflow ownership
- visualization and LLM work have explicit data contracts before implementation
- any implementation follow-up is split into focused requests rather than one broad route-family expansion
