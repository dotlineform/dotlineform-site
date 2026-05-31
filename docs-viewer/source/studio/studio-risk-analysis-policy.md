---
doc_id: studio-risk-analysis-policy
title: Studio Risk Analysis Policy
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: review
parent_id: audit
viewable: true
---
# Studio Risk Analysis Policy

This document defines how Studio risk analysis is classified, scored, prioritised, and closed.

Use this policy with:

- [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard) for the short current priority order
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) for browser JavaScript rows
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) for Docs Viewer browser JavaScript follow-up
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory) for script and backend-service families

## Purpose

Risk analysis is an action-selection tool.
It should identify where a focused improvement will reduce future-change risk, route cost, local-service cost, or planning uncertainty.

It is not:

- a leaderboard of largest files
- a mandate to split every long module
- a substitute for route-family judgement
- a reason to create generic frameworks before repeated mechanics are proven identical

The expected output is a concrete improvement action with evidence that the risk moved.

## Review Units

Choose the smallest unit that matches the risk.

| Unit | Use when | Example |
| --- | --- | --- |
| File | One module has a coherent risk surface. | A browser route controller owns too many lifecycle concerns. |
| File family | Several files form one route, controller, service, or workflow boundary. | Docs Viewer search, management, bookmark, or config modules. |
| Script family | A backend workflow spans command wrappers, services, generators, and helpers. | Catalogue save/build, docs build/import/export, media derivation. |
| Cross-cutting family | Several services share mechanics but not domain behavior. | Local-server JSON parsing, CORS, request limits, compact logs. |
| Inventory quality | The risk report itself is stale or contradictory. | Full JavaScript rows disagree with the Docs Viewer-specific rows. |

Do not mix file-level and family-level conclusions in the same action unless the evidence names both.
The dashboard should describe the improvement unit explicitly.

## General Risk Categories

### Maintenance Risk

Maintenance risk is the cost and danger of changing behavior later.

Useful indicators:

- mixed responsibilities such as rendering, validation, service calls, state mutation, modal lifecycle, data normalization, and workflow rules in one owner
- broad state reads or hidden contracts instead of explicit inputs
- repeated recent touches to the same module or workflow
- hard-to-test behavior that only runs through route boot, DOM events, or local service startup
- fallback paths where post, patch, offline, dry-run, write, and manual modes are interleaved

### Ownership Boundary Risk

Ownership boundary risk covers current structural shape and future architectural drift.

At dashboard level, treat structural and architectural risk as one priority category unless the action clearly addresses only one of them.
In this repo, most useful improvements reduce both: moving a complete responsibility to a focused owner improves current structure and makes the next related change less likely to drift back into a broad coordinator.

Use the terms separately only when the distinction is measurable:

- Structural risk asks: is the code currently shaped according to the intended ownership model?
- Architectural risk asks: will the next related change naturally land in the right place?

Evidence of improvement:

- a complete responsibility has a focused owner
- route or service coordinators receive explicit inputs instead of broad state or broad request context
- future related changes have an obvious destination
- sibling route or service families now follow the same boundary pattern
- focused checks cover behavior that previously required full route or service boot

### Performance Risk

Performance risk is avoidable cost in route load, interaction, local-service work, rebuild work, or external-command work.
It is not raw file size alone.

Useful indicators:

- public or shared routes eagerly load code that is not needed for the initial view
- heavy boot-time work runs before route-ready
- repeated full-list rendering or expensive input-time filtering
- repeated JSON loads, joins, full scans, subprocess calls, or media freshness checks
- conservative full rebuilds where field-aware metadata could safely narrow the scope

Evidence of improvement:

- route payload, boot work, or input-time work is reduced
- diagnostics show counts, elapsed time, skipped work, and fallback reasons
- a measured broad path becomes a narrower path with equivalent dry-run/write behavior
- media or rebuild reports identify slow stages before optimization is attempted

### Planning Risk

Planning risk applies when the inventory or dashboard is stale, contradictory, or too scattered to support action.

Use this category sparingly.
It should lead to reconciliation work, not to code refactoring by guesswork.

Evidence of improvement:

- active paths, scores, current owners, and priority rows agree across source inventories
- stale retired paths are clearly marked as retired
- the dashboard points to the current evidence document instead of duplicating long tables

## Frontend Policy

Frontend risk analysis applies to browser JavaScript and route-facing UI modules.

Current active roots include:

- Local Studio: `studio/app/frontend/js/`
- Local Analytics and Data Sharing: `analytics-app/app/frontend/js/`
- UI Catalogue: `ui-catalogue-app/app/assets/js/`
- public site/shared assets: `assets/js/` and route-specific public assets
- Docs Viewer runtime: `docs-viewer/runtime/js/`

Do not treat retired `assets/studio/js/...` paths as active owners when planning new work.

### Frontend Scoring

Browser JavaScript uses four 0-3 category scores:

- Maintenance
- Structural
- Performance
- Architectural

The total score is the sum of those category scores.
The normal target is 4 or lower.
A score of 4 means every category may still be present, but each is low.

Use 0 carefully.
It means the category is materially absent or inapplicable in the file's current role, not merely that the file seems easy.

| Risk | Score 0: absent or inapplicable | Score 1: low risk | Score 2: medium risk | Score 3: high risk |
| --- | --- | --- | --- | --- |
| Maintenance | Isolated, stable, generated, declarative, or mechanically owned file with no direct maintenance surface. | Focused role, explicit inputs, stable behavior, directly testable or small enough to review. | Some mixed concerns, recurring touches, broad reads, or moderate test friction. | Many mixed concerns, broad reads/writes, frequent edits, fallback paths, or hard-to-test behavior. |
| Structural | No meaningful structural ownership decision exists beyond keeping the file isolated in its current role. | Module shape matches its role and established route-family boundaries. | Partial split exists, but ownership or contracts remain incomplete. | Route/controller owns layers that belong in domain, service, render, modal, route-state, or workflow modules. |
| Performance | No material runtime performance requirement for the file's current route exposure, data volume, and interaction pattern. | Lazy, rare, small, public-cost-neutral, or no meaningful boot/input cost. | Route-local exposure, moderate size, repeated list work, or occasional input-time cost. | Public/shared eager exposure, large initial payload, heavy boot work, repeated full renders, or expensive input-time operations. |
| Architectural | No plausible future-responsibility drift because the file is isolated or future work has a clearly separate owner. | Clear owner exists for future changes and the file reinforces durable patterns. | Future changes may drift into the file because ownership is only partly clear. | Current shape is likely to attract unrelated future work, diverge from sibling patterns, or require unrelated concerns to be reviewed together. |

Risk bands:

- 0-3: below the normal target; acceptable only when one or more category scores are legitimately absent or inapplicable
- 4: normal target state
- 5: low-priority watch item; improve opportunistically when changing nearby behavior
- 6-7: medium priority; schedule as part of the relevant route-family batch
- 8-12: high priority; plan a focused mitigation slice before adding more behavior to that file

Priority should be based on current risk and concrete improvement evidence, not ease alone.

### Frontend Improvement Rules

Prefer slices that remove a complete responsibility from a mixed controller and leave a clearer ownership boundary.

Good frontend score-moving slices:

- move rendering, modal lifecycle, workflow, state projection, service calls, or route commands to a focused owner
- narrow broad state handoffs to explicit owner inputs
- keep route entry modules as orchestration shells
- lazy-load management-only, report-only, import-only, or modal-heavy behavior where route exposure makes that meaningful
- add focused module checks for behavior that previously required full route boot

Poor frontend slices:

- move tiny helpers without changing ownership
- split a file only because it is large
- add generic abstractions before sibling route families show the same need
- lower a score merely because code moved elsewhere

Rescore downward only when at least one category has materially changed.
Record whether the slice was score-moving or only a guardrail.

## Backend Policy

Backend risk analysis applies to Python and Ruby scripts, local service handlers, generators, builders, import/export tools, audit scripts, and media scripts.

Backend work uses family-level classification rather than a four-score file table because the main risk often sits in workflow breadth, rebuild scope, service mechanics, write safety, and cross-language contracts.

### Backend Classifications

Classify each script or service family as high, medium, or low for:

- Maintenance risk
- Structure and consistency risk
- Performance risk

Backend policy intentionally combines structural and architectural concerns as **Structure and consistency risk**.
Splitting them into separate backend categories would usually double-count the same evidence: module ownership, command shape, testability, logging, backup behavior, write allowlists, response envelopes, and service mechanics.

High means the area should be considered for near-term improvement when related work is opened.
Medium means watch it and improve opportunistically.
Low means no immediate structural or performance action is recommended.

### Backend Improvement Rules

Start with visibility when performance or rebuild scope is uncertain.
Do not optimize broad rebuilds, media work, or local-service paths until diagnostics show which path is expensive or repeated.

Good backend score-moving or classification-moving slices:

- add counts, elapsed time, skipped work, and fallback reasons to save/build/rebuild/media responses or logs
- move generated artifact behavior into existing generation, lookup, source-model, or media owners rather than HTTP service handlers
- keep service handlers as transport/orchestration and preserve explicit write allowlists
- standardize identical local-service mechanics, such as request-size limits, JSON parse errors, CORS headers, compact log fields, and response envelopes
- group broad audit checks by source family and report section

Poor backend slices:

- create a broad local-service framework before contracts are identical
- hide service-specific write allowlists behind generic helpers
- optimize unmeasured fallback paths
- add generated artifact shaping directly to orchestration scripts
- treat smaller files as lower risk when the workflow still requires broad local knowledge

## Dashboard Policy

The dashboard is the short decision surface.
It should not duplicate full inventory tables.

Dashboard rows must include:

- priority
- area
- unit
- main risk
- next action
- evidence of improvement

Use combined category labels when they better match action:

- `Maintenance`
- `Ownership boundary`
- `Performance`
- `Planning`
- `Structure and consistency`

Only split structural and architectural dashboard rows when the action and evidence are distinct.

## Close-Out Rules

A risk-reduction action closes only when the evidence has changed.

Examples:

- a frontend row is rescored because a complete responsibility moved to a focused owner
- a backend family classification changes because diagnostics or ownership boundaries materially improved
- a performance priority changes because measured diagnostics identify or eliminate a repeated broad path
- a planning-risk item closes because active paths and scores agree across inventories

If the work only adds tests, docs, or guardrails, record it as a guardrail unless it also changes the underlying ownership, performance, or planning evidence.
