---
doc_id: risk-analysis-analytics
title: Risk Analysis - Analytics App
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: admin
---
# Risk Analysis - Analytics App

Risk analysis for the Analytics app, analytical dimensions, and Data Sharing workflows.

Policy: [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy).

## Priority Order

1. Architectural fit
2. Structural
3. Workflow
4. Performance / cost

## Risk Analysis

| Area | Indicator | Evidence | Current action |
| --- | --- | --- | --- |
| Analytics growth path | Architectural fit | Future work is likely to include richer analytical dimensions, third-party visualisation libraries, and LLM-oriented data-sharing flows. | Track the next planning slice in [Analytics Data Sharing Growth Path Request](/docs/?scope=studio&doc=site-request-analytics-data-sharing-growth-path). |
| Analytics tag route families | Structural | Analytics has been decoupled from Studio, but future features need app-owned boundaries so tag, scoring, visualisation, and sharing work do not drift back into Studio-owned surfaces. [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) currently has 54 Analytics frontend modules, with 14 above target score 4 and 4 at score 6 or higher. The active rows are concentrated in tag editors, tag registry/aliases modals, and Series Tags. | Keep route behavior in the current tag route owners, shared save session, modal shell, modal workflow, render, state, service, and domain modules. Open a change request before broadening the tag-route family. |
| Data Sharing package routes | Workflow | Data Sharing workflows cross app data, exported packages, review/apply steps, source writes, and package result review. The old JavaScript inventory keeps `data-sharing-prepare.js` at score 6 and `data-sharing-review.js` at score 5 while focused workflow/render/service modules sit at target score 4. | Keep package preparation, review, apply, modal, render, service, and workflow behavior app-owned. Do not move Data Sharing behavior back into Studio route or generic script queues. |
