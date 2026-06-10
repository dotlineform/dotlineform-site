---
doc_id: risk-analysis-policy
title: Risk Analysis Policy
added_date: 2026-06-07
last_updated: 2026-06-10
parent_id: admin
---
# Risk Analysis Policy

This document defines how risk analysis is classified, prioritised, and closed.

- Risk analysis is an action-selection tool.
- It should identify where a focused improvement will reduce the chance of breakage, accumulated drift, costly repair, or strategic blockage.
- The expected output is a concrete app-improvement action with evidence that the relevant risk indicator moved.
- The current evidence implementation is [Checks](/docs/?scope=studio&doc=admin-checks), with planned producers tracked under [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Actual Risks

The actual risks this policy is trying to prevent are:

- the system breaks in a significant way
- many small breakages accumulate into a larger failure
- the fix requires major effort or broad refactor because the cause and ownership are unclear
- the system becomes too hard to understand, so it does not get maintained and failure risk increases
- the development strategy compounds risk because a foundational design choice is wrong or no longer suitable for the current apps

## Review Units

| Unit | Use when | Example |
| --- | --- | --- |
| App | The priority decision should improve one app as a usable system. | Docs Viewer public/runtime performance and local management structure. |
| File family | Several files form one route, controller, service, or workflow boundary. | Docs Viewer search, management, bookmark, or config modules. |
| File | One module has a coherent risk surface. | A browser route controller owns too many lifecycle concerns. |
| Workflow family | A backend workflow spans command wrappers, services, generators, and helpers. | Catalogue save/build, docs build/import/export, media derivation. |
| Cross-cutting family | Several services share mechanics but not domain behavior. | Local-server JSON parsing, CORS, request limits, compact logs. |
| Inventory quality | The risk report itself is stale or contradictory. | Full JavaScript rows disagree with the Docs Viewer-specific rows. |

- Frontend and backend evidence should be reviewed together when they belong to the same app.
- The action should improve the app, not send the work into a technical rabbit hole because one layer has a convenient table.

## Evidence Validity

Risk evidence must test whether scripts, config keys, generated config payloads, and generated artifacts have an active workflow purpose.
Ownership is necessary but not sufficient: a script, config key, or generated file can be correctly owned and still be harmful if its contract is speculative, unused, duplicated, or exposed to the wrong runtime surface.

For script, config, and generated-artifact evidence, risk analysis should distinguish:

- consumed by an active runtime, report, build, test, or documented operator workflow
- retained only as source-of-truth input
- browser-visible config or payload field with a current UI/runtime consumer
- server-only source path, write target, adapter contract, output pattern, metadata contract, or activity-emitter field
- transitional evidence with a retirement or migration task
- unconsumed output that should be removed, stopped at the producer, or replaced with a smaller contract
- for browser-visible config evidence, whether the field is part of an explicit whitelist or broad pass-through projection.
- Do not treat "has an owner" as proof that the artifact should continue to exist. Temporary generated artifacts still need a consumer or explicit cleanup path.

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

### Static Analysis

Static analysis means reading checked-in files without exercising the app. Typical static analysis includes:

- `rg` searches over app roots, scripts, docs, config, and tests
- file and line-count summaries grouped by app, route, service, or workflow family
- import/export scans for dependency direction and cross-app coupling
- checks for retired paths, stale route names, old endpoints, duplicated config keys, and generated-output assumptions
- table validation for inventory rows, parent/child docs, front matter, generated indexes, and source-tree ownership
- manual source reading to classify responsibilities, ownership boundaries, and architectural fit

Static analysis should be followed by either app-context review or runtime verification.

### Runtime And External Tooling

Runtime tooling is used when the risk depends on route behavior, browser cost, local services, or public-route performance. Available or appropriate tools include:

- browser dev tools for network, performance, console errors, layout inspection, and accessibility inspection
- Playwright for repeatable browser smoke checks and route interaction checks
- Node for JavaScript syntax and local helper execution
- Python test and smoke runners for local services, generated payload checks, and app contracts
- Ruby/Jekyll build checks where the public-site preview/build layer is directly relevant
- Lighthouse or equivalent browser performance tooling for public-facing pages when route payload, load, layout shift, accessibility, or best-practice evidence is needed

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
- app config, runtime config, generated defaults, UI text, and service/domain config disagree about which layer owns a route, path, payload field, or workflow copy

Evidence of improvement:

- a complete responsibility has a focused owner
- route or service coordinators receive explicit inputs instead of broad state or broad request context
- future related changes have an obvious destination
- sibling route or service families now follow the same boundary pattern
- focused checks cover behavior that previously required full route or service boot
- browser-facing config surfaces are narrowed to active owner contracts, with server-only config kept behind services or source loaders

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

## App Priority Order

Each app has its own order of importance for the same indicator categories. It is a practical priority order for deciding what becomes actionable first.

For example: local-service elapsed time is not automatically a priority indicator unless it affects development speed, hides repeated broad work, or blocks a higher-priority structural/workflow concern. A local server path can have high performance risk, but if performance is low in that app's priority order then other work may take priority.

### Public Site

Purpose: catalogue artwork and text on GitHub Pages.

Priority order:

1. Performance / cost
2. Architectural fit
3. Structural
4. Workflow

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
4. Performance / cost

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
4. Performance / cost

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

Rationale:

- local Docs Viewer gets frequent interaction, so responsiveness is more noticeable than most local Studio paths
- read-only public installs make frontend JavaScript performance a public-site concern
- UI and document structure are under active refinement
- future Analytics integration and data-sharing support raise architecture pressure

## Example improvement slices

Frontend:

- move rendering, modal lifecycle, workflow, state projection, service calls, or route commands to a focused owner
- narrow broad state handoffs to explicit owner inputs
- keep route entry modules as orchestration shells
- lazy-load management-only, report-only, import-only, or modal-heavy behavior where route exposure makes that meaningful
- reduce public payload, boot work, or input-time work where the app priority order makes performance actionable
- add focused module checks for behavior that previously required full route boot

Backend:

- move generated artifact behavior into existing generation, lookup, source-model, or media owners rather than HTTP service handlers
- keep service handlers as transport/orchestration and preserve explicit write allowlists
- standardize identical local-service mechanics, such as request-size limits, JSON parse errors, CORS headers, compact log fields, and response envelopes
- group broad audit checks by source family and report section
