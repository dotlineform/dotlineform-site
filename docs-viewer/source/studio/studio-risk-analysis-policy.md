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

This document defines how Studio risk analysis is classified, prioritised, and closed.

Use this policy with:

- [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard) for the short current priority order
- the dashboard child inventories for app-owned evidence: [Public Site Risk Inventory](/docs/?scope=studio&doc=public-site-risk-inventory), [Studio App Risk Inventory](/docs/?scope=studio&doc=studio-app-risk-inventory), [Analytics Risk Inventory](/docs/?scope=studio&doc=analytics-risk-inventory), and [Docs Viewer Risk Inventory](/docs/?scope=studio&doc=docs-viewer-risk-inventory)
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) for browser JavaScript evidence during the inventory transition
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) for Docs Viewer browser JavaScript evidence during the inventory transition
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory) for script and backend-service evidence during the inventory transition

## Purpose

Risk analysis is an action-selection tool.
It should identify where a focused improvement will reduce the chance of breakage, accumulated drift, costly repair, or strategic blockage.

It is not:

- a leaderboard of largest files
- a mandate to split every long module
- a substitute for app-level judgement
- a reason to create generic frameworks before repeated mechanics are proven identical
- an attempt to measure project-management, staffing, deadline, or future-skill risk

The expected output is a concrete app-improvement action with evidence that the relevant risk indicator moved.

## Actual Risks

The risk categories are observable indicators.
They are not the actual risks.

The actual risks this policy is trying to prevent are:

- the system breaks in a significant way
- many small breakages accumulate into a larger failure
- the fix requires major effort or broad refactor because the cause and ownership are unclear
- the system becomes too hard to understand, so it does not get maintained and failure risk increases
- the development strategy compounds risk because a foundational design choice is wrong or no longer suitable for the current apps

## Review Units

Choose the smallest unit that matches the risk evidence.

| Unit | Use when | Example |
| --- | --- | --- |
| App | The priority decision should improve one app as a usable system. | Docs Viewer public/runtime performance and local management structure. |
| File family | Several files form one route, controller, service, or workflow boundary. | Docs Viewer search, management, bookmark, or config modules. |
| File | One module has a coherent risk surface. | A browser route controller owns too many lifecycle concerns. |
| Workflow family | A backend workflow spans command wrappers, services, generators, and helpers. | Catalogue save/build, docs build/import/export, media derivation. |
| Cross-cutting family | Several services share mechanics but not domain behavior. | Local-server JSON parsing, CORS, request limits, compact logs. |
| Inventory quality | The risk report itself is stale or contradictory. | Full JavaScript rows disagree with the Docs Viewer-specific rows. |

Frontend and backend evidence should be reviewed together when they belong to the same app.
The action should improve the app, not send the work into a technical rabbit hole because one layer has a convenient table.

## Inventory Production Method

Risk inventories combine deterministic observations with subjective review.
Neither type of evidence is sufficient on its own.

Deterministic observations show what exists, changed, loaded, or ran.
Subjective review decides what that means for the app and whether it should become a priority.

Concrete deterministic evidence should be produced as a repeatable evidence pack.
The target artifact contract is [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack).

### Deterministic Inputs

Local scripts and command-line checks contribute repeatable observations.
They do not decide priorities by themselves.

Useful deterministic inputs include:

- file line counts and file-family totals
- import/export counts and dependency direction
- static code searches for ownership smells, stale paths, broad state handoffs, retired modules, service endpoints, config keys, generated paths, and TODO-like follow-up markers
- route exposure and public/local/runtime inclusion checks
- generated payload counts, index sizes, changed/removed records, and schema/version checks
- write-path diagnostics such as elapsed time, skipped work, fallback reasons, generated artifact groups, search updates, lookup refreshes, backup paths, and media work
- git history signals such as repeated recent touches to the same app surface
- syntax and contract checks such as `node --check`, Python `py_compile`, Ruby syntax checks where relevant, JSON validation, and focused pytest checks
- app smoke checks, especially Playwright/browser smokes for route readiness, public read-only behavior, and user-facing interactions

Current local inventory helpers are transition evidence.
For example, `studio/checks/javascript_inventory_guardrail.py` validates the old JavaScript inventory table and highlights legacy concentration patterns, but it should not remain the final app-priority mechanism.

When adding deterministic evidence to an app inventory, record the command, source, or report that produced it.
Avoid anonymous metrics such as "large", "slow", or "complex" when a local count, timing, path list, or diagnostic payload is available.
If the evidence came from a risk evidence pack, cite the run summary path and the specific artifact used.

### Static Analysis

Static analysis means reading checked-in files without exercising the app.
It is useful for finding surfaces that need review, not for proving user impact.

Typical static analysis includes:

- `rg` searches over app roots, scripts, docs, config, and tests
- file and line-count summaries grouped by app, route, service, or workflow family
- import/export scans for dependency direction and cross-app coupling
- checks for retired paths, stale route names, old endpoints, duplicated config keys, and generated-output assumptions
- table validation for inventory rows, parent/child docs, front matter, generated indexes, and source-tree ownership
- manual source reading to classify responsibilities, ownership boundaries, and architectural fit

Static analysis should be followed by either app-context review or runtime verification before it becomes a high-priority action.

### Runtime And External Tooling

Runtime tooling is used when the risk depends on route behavior, browser cost, local services, or public-route performance.

Available or appropriate tools include:

- browser dev tools for network, performance, console errors, layout inspection, and accessibility inspection
- Playwright for repeatable browser smoke checks and route interaction checks
- Node for JavaScript syntax and local helper execution
- Python test and smoke runners for local services, generated payload checks, and app contracts
- Ruby/Jekyll build checks where the public-site preview/build layer is directly relevant
- Lighthouse or equivalent browser performance tooling for public-facing pages when route payload, load, layout shift, accessibility, or best-practice evidence is needed

External tooling should be used to answer a specific app question.
Do not run Lighthouse, broad browser profiling, or large smoke profiles merely because a file is large.

### Subjective And User Evidence

Subjective evidence is allowed and important.
It should be clearly labelled so it does not look like deterministic measurement.

Useful subjective inputs include:

- user feedback about confusing workflows, slow interactions, hard-to-read UI, or unexpected behavior
- reviewer judgement that a design choice no longer fits the app direction
- repeated difficulty explaining where a change belongs
- code-reading notes that a file or family is hard to navigate even when it has not failed
- uncertainty about whether generated files, logs, backups, or local state are still needed

When incorporating subjective evidence, record:

- source of the feedback or review
- affected app and area
- observed symptom or concern
- whether it is confirmed, plausible, or speculative
- what deterministic check or change request would turn it into actionable work

Subjective evidence can raise a planning/evidence priority by itself.
It should only trigger implementation work directly when the user-facing problem is clear enough to define a concrete change request.

### Priority Establishment

Priorities are established in this order:

1. Select the app.
2. Apply that app's priority order.
3. Gather deterministic and subjective evidence for the highest relevant indicator categories.
4. Prefer actions with concrete close-out evidence.
5. Open or link the change request that owns the work.

A deterministic metric can move a priority up only when it matters for that app.
For example, high local-service elapsed time is not automatically a top Studio priority unless it affects development speed, hides repeated broad work, or blocks a higher-priority structural/workflow concern.

Likewise, subjective feedback can move a priority up when it describes an app-level problem, even before there is a perfect metric.
The next action should then be either a diagnostic slice or a focused change request, not an open-ended refactor.

## Observable Risk Indicators

### Architectural Fit Risk

Architectural fit risk asks whether foundational design, framework, hosting, or strategy choices still fit the app's purpose.

Useful indicators:

- the current framework is now mostly historical convenience rather than the best fit
- hosting or publishing constraints force awkward downstream behavior
- a major app direction has changed but the technical base still reflects the old direction
- future feature work repeatedly pushes against the same foundational boundary
- a route, app, or workflow has no credible long-term strategy beyond incremental patching

Examples:

- Jekyll/Ruby remains in a path mostly because it was once convenient, even if the current app now behaves more like generated static route stubs plus local JS tooling.
- Analytics is likely to grow toward richer data visualisation and LLM-sharing workflows, so weak app architecture has higher future impact than it would in a stable public page.

### Structural Risk

Structural risk asks whether the current organisation makes cause, ownership, and change boundaries clear enough.

Useful indicators:

- mixed responsibilities such as rendering, validation, service calls, state mutation, modal lifecycle, data normalization, and workflow rules in one owner
- broad state reads or hidden contracts instead of explicit inputs
- route/controller files own behavior that belongs in domain, service, render, modal, route-state, or workflow modules
- CSS or UI structure is tangled enough that changing one thing can break another without a clear cause/effect chain
- code is physically too long to navigate efficiently, increasing human context switching and AI token/context cost
- the same concept is updated in several places without a clear owner
- sibling route or service families use inconsistent patterns for the same responsibility

Evidence of improvement:

- a complete responsibility has a focused owner
- route or service coordinators receive explicit inputs instead of broad state or broad request context
- future related changes have an obvious destination
- sibling route or service families now follow the same boundary pattern
- focused checks cover behavior that previously required full route or service boot

### Workflow Risk

Workflow risk is most relevant to backend, local-service, generated-data, and operational paths.
It asks whether side effects, generated files, logs, backups, and chained operations are visible and controlled.

Useful indicators:

- one save/build path touches many outputs, backups, generated payloads, logs, search indexes, media derivatives, or activity rows
- generated files, `var/` files, backups, or logs can build up without being noticed
- it is not obvious why an output is being generated or whether it is still needed
- dry-run, write, fallback, manual, and offline modes are interleaved
- local-service response envelopes, request parsing, write allowlists, or log fields drift across services
- broad audit scripts grow by adding unrelated checks without grouping or machine-readable sections

Evidence of improvement:

- diagnostics show counts, elapsed time, skipped work, generated artifact groups, and fallback reasons
- write allowlists and backup behavior remain visible
- generated artifact behavior lives in generation, lookup, source-model, or media owners rather than HTTP handlers
- repeated local-service mechanics are standardized only where contracts are identical

### Performance / Cost Risk

Performance and cost risk is avoidable cost in public route load, interaction, local-service work, rebuild work, media work, or developer/AI navigation.

Useful indicators:

- public or shared routes eagerly load code that is not needed for the initial view
- heavy boot-time work runs before route-ready
- repeated full-list rendering or expensive input-time filtering
- repeated JSON loads, joins, full scans, subprocess calls, or media freshness checks
- conservative full rebuilds where field-aware metadata could safely narrow the scope
- large files or tangled surfaces increase review time, search time, token cost, or missed-change risk

Evidence of improvement:

- route payload, boot work, or input-time work is reduced
- diagnostics show counts, elapsed time, skipped work, and fallback reasons
- a measured broad path becomes a narrower path with equivalent dry-run/write behavior
- media or rebuild reports identify slow stages before optimization is attempted

### Planning / Evidence Risk

Planning and evidence risk applies when the inventory, dashboard, or diagnostics are stale, contradictory, missing, or too scattered to support action.

Use this category to make the decision surface reliable.
It should not be used as a reason to refactor code by guesswork.

Useful indicators:

- active paths, scores, current owners, and priority rows disagree across inventories
- retired paths remain mixed with active owners
- frontend and backend evidence is separated in a way that obscures the app-level priority
- a performance claim is plausible but unmeasured
- the dashboard duplicates long tables instead of pointing to evidence

Evidence of improvement:

- app-owned inventories agree with the dashboard
- stale retired paths are clearly marked as retired
- diagnostics exist before optimization work is prioritised
- the next action and close-out evidence are concrete

## App Priority Order

Each app has its own order of importance for the same indicator categories.
This is not a scoring formula.
It is a practical priority order for deciding what becomes actionable first.

A lower-ordered category is not ignored.
It simply should not become the next action unless it is causing visible breakage, blocking a higher-ordered category, or the higher-ordered categories have no current actionable evidence.
For example, a local server path can have high performance risk, but if performance is low in that app's priority order, the work should not repeatedly need to defend why that optimization is not next.

### Public Site

Purpose: catalogue artwork and text on GitHub Pages.

Priority order:

1. Performance / cost
2. Architectural fit
3. Structural
4. Workflow
5. Planning / evidence

Rationale:

- public payloads, media, responsiveness, and elegant UI matter directly
- static hosting and Jekyll/Ruby fit are strategic architecture concerns
- structure and taxonomy are complex but relatively stable
- data volumes are low to moderate and new-record volume is modest

### Studio

Purpose: local app for managing data published on the public site.

Priority order:

1. Structural
2. Workflow
3. Architectural fit
4. Planning / evidence
5. Performance / cost

Rationale:

- local runtime hides most user-visible performance problems
- performance work matters when it affects development speed or causes repeated broad work, but it is usually not the first app-level action
- the main risk is keeping a formerly large unmanaged codebase moving toward clear JS-app and service ownership
- Docs Viewer and Analytics decoupling has reduced but not removed structure pressure

### Analytics

Purpose: manage analytical dimensions over catalogue data and provide analytical tools and resources.

Priority order:

1. Architectural fit
2. Structural
3. Workflow
4. Planning / evidence
5. Performance / cost

Rationale:

- likely future growth includes third-party visualisation libraries and LLM data-sharing workflows
- weak architecture or unclear app boundaries will compound faster here than in stable public catalogue routes
- local performance is lower priority unless richer visualisation/data workflows make it user-visible or development-blocking

### Docs Viewer

Purpose: manage text/media documents for publishing and support read-only public installs, Studio docs, and Analytics-related data-sharing/documentation flows.

Priority order:

1. Structural
2. Performance / cost
3. Architectural fit
4. Workflow
5. Planning / evidence

Rationale:

- local Docs Viewer gets frequent interaction, so responsiveness is more noticeable than most local Studio paths
- read-only public installs make frontend JavaScript performance a public-site concern
- UI and document structure are under active refinement
- future Analytics integration and data-sharing support raise architecture pressure

## Frontend Evidence

Frontend risk evidence applies to browser JavaScript, CSS, route-facing UI modules, and public/runtime payloads.

Current active roots include:

- Local Studio: `studio/app/frontend/js/`
- Local Analytics and Data Sharing: `analytics-app/app/frontend/js/`
- UI Catalogue: `ui-catalogue-app/app/assets/js/`
- public site/shared assets: `assets/js/` and route-specific public assets
- Docs Viewer runtime: `docs-viewer/runtime/js/`

Do not treat retired `assets/studio/js/...` paths as active owners when planning new work.

The current JavaScript inventories still contain legacy frontend score columns: `Maint.`, `Struct.`, `Perf.`, and `Arch.`.
During the transition:

- treat `Maint.` evidence as structural, workflow, performance/cost, or planning/evidence evidence according to the specific note
- keep `Struct.`, `Perf.`, and `Arch.` as evidence columns, but prioritise them through the app priority order
- do not start a frontend action from the global table alone when an app-owned priority list gives clearer direction

Good frontend improvement slices:

- move rendering, modal lifecycle, workflow, state projection, service calls, or route commands to a focused owner
- narrow broad state handoffs to explicit owner inputs
- keep route entry modules as orchestration shells
- lazy-load management-only, report-only, import-only, or modal-heavy behavior where route exposure makes that meaningful
- reduce public payload, boot work, or input-time work where the app priority order makes performance actionable
- add focused module checks for behavior that previously required full route boot

Poor frontend slices:

- move tiny helpers without changing ownership
- split a file only because it is large
- add generic abstractions before sibling route families show the same need
- lower a score merely because code moved elsewhere
- optimise local-only route payloads when higher-priority structural or workflow work is blocking app clarity

## Backend Evidence

Backend risk evidence applies to Python and Ruby scripts, local service handlers, generators, builders, import/export tools, audit scripts, media scripts, generated payloads, backups, logs, and `var/` outputs.

Backend evidence should sit in the same app priority list as frontend evidence.
Separate backend inventories are useful as evidence stores, but they should not create a separate queue of technical actions detached from the app they affect.

Classify backend evidence with the same observable indicators:

- Architectural fit
- Structural
- Workflow
- Performance / cost
- Planning / evidence

Backend workflow risk is usually more important than frontend workflow risk because backend paths create source writes, backups, generated outputs, service responses, logs, and local state.

Good backend improvement slices:

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

The dashboard is the short app-level decision surface.
It should not duplicate full inventory tables.

Dashboard rows must include:

- priority
- app or app-facing area
- unit
- main risk indicator
- next action
- evidence of improvement

Frontend and backend evidence should appear in the same priority list when both affect the same app.
The dashboard should choose actions that improve the app, not actions that are merely convenient for one technology layer.

Use these indicator labels:

- `Architectural fit`
- `Structural`
- `Workflow`
- `Performance / cost`
- `Planning / evidence`

## Close-Out Rules

A risk-reduction action closes only when the evidence has changed.

Examples:

- a frontend controller family has a clearer owner and future related changes have an obvious destination
- a backend workflow shows counts, elapsed time, skipped work, and fallback reasons that did not exist before
- a public route payload or boot cost is reduced where public performance is an app priority
- an app-owned inventory agrees with the dashboard and retired paths are clearly marked

If the work only adds tests, docs, or guardrails, record it as a guardrail unless it also changes the underlying architectural, structural, workflow, performance/cost, or planning/evidence risk.
