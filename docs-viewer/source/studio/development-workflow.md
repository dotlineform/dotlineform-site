---
doc_id: development-workflow
title: Development Workflow
added_date: 2026-05-19
last_updated: 2026-05-28
parent_id: dev-home
viewable: true
---
# Development Workflow

This document is the repo-specific lifecycle guide for major new features, behavior changes, refactors, and meaningful documentation changes.

- Use it to decide what to read, what to update, and how to close work out.
- It is intentionally a router to focused docs rather than a replacement for them.
- Detailed implementation rules that are too specific for this lifecycle guide live in [Development Checklist](/docs/?scope=studio&doc=development-checklist).

## Fast Path

For any non-trivial change:

1. Classify the work: feature, bugfix, refactor, documentation, generated-data change, UI change, or workflow change. Read the owning section docs before editing.
2. Decide whether the work needs a change request. Change requests are documented under [Change Requests](/docs/?scope=studio&doc=change-requests).
3. Use [Tasks Template](/docs/?scope=studio&doc=tasks-template) as the template for tracking tasks. This becomes a child documemnt of the owning change request document.
4. Keep implementation scoped to the owning runtime, script, data model, or UI primitive.
5. Run targeted verification proportional to the blast radius.
6. Update owning docs and generated payloads when source docs or generated contracts change.
7. Close out with a concise summary, remaining risks, and follow-up tasks.
8. Write structured docs-log entries for meaningful completed work. More info: `studio/workflows/change-requests/README.md`.

## 1. Classify The Work

Use the smallest owning area that explains the change:

- Site architecture or route/runtime behavior: [Architecture](/docs/?scope=studio&doc=architecture)
- Studio route behavior: [Studio](/docs/?scope=studio&doc=studio)
- UI primitives, modal patterns, or layout behavior: [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start), [UI Framework](/docs/?scope=studio&doc=ui-framework), and [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- Generated/runtime data contracts: [Data Models](/docs/?scope=studio&doc=data-models)
- Checked-in config: [Config](/docs/?scope=studio&doc=config)
- Docs Viewer behavior: [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- Docs Viewer frontend-app architecture work: [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- Search behavior, schema, ranking, or build flow: [Search](/docs/?scope=studio&doc=search)
- Scripts, local services, and command behavior: [Scripts](/docs/?scope=studio&doc=scripts)
- Source tree ownership or source/public boundary behavior: [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- Local setup, dependency, or environment behavior: [Local Setup](/docs/?scope=studio&doc=local-setup) and [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)
- Test strategy and check profiles: [Testing](/docs/?scope=studio&doc=testing), [Run Checks](/docs/?scope=studio&doc=scripts-run-checks), and [Pytest](/docs/?scope=studio&doc=testing-pytest)

If the owning area is unclear, start with [Site Docs](/docs/?scope=studio&doc=dev-home), then narrow from there.

## 2. Decide Whether A Change Request Is Needed

Use [Change Requests](/docs/?scope=studio&doc=change-requests) for work that needs a visible product, workflow, or implementation plan before it is complete.

A change request is usually useful when the work:

- changes user workflow or operational behavior
- spans multiple files, modules, routes, or generated artifacts
- involves uncertain requirements or tradeoffs
- creates a new convention, data model, or local-service behavior
- should remain visible after the implementation conversation ends

Small bugfixes, narrow docs edits, and mechanical cleanup usually do not need a new request.

Keep change requests manually curated.
They are planning and close-out artifacts, not the durable implementation log.

## 3. Shape The Implementation

Prefer existing repo boundaries:

- Extend shared modules and primitives before creating one-off route-local patterns.
- Prefer a package or directory namespace over a growing set of same-level helper modules when a helper surface has multiple responsibilities, is likely to grow, or is becoming an explicit architecture boundary.
- Keep UI shell, validation, data mutation, and generated-output behavior separate.
- Keep config ownership in checked-in config docs and loader modules.
- Keep generated data flowing from source records through scripts; do not edit generated payloads as source.
- Keep source docs under the owning scope and use Docs Viewer links for published doc references.

For local Studio route migration, public-link resolver adoption, Studio route URL builders, and UI Catalogue demo visibility, use [Development Checklist](/docs/?scope=studio&doc=development-checklist).
For UI work, start with [UI](/docs/?scope=studio&doc=ui) and child documents.
For search work, start with [Search](/docs/?scope=studio&doc=search) and update search child docs when schema, ranking, normalization, UI, build flow, or validation changes materially.
For scripts or local services, use [Scripts](/docs/?scope=studio&doc=scripts) and the script-specific child doc.
For browser JavaScript maintenance-risk work, use [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy) for scoring, [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) for current rows, and the maintenance gate below before adding behavior to high-risk files.
For Docs Viewer frontend-app architecture work, start with [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).
If the work needs a task tracker, create one from [Tasks Template](/docs/?scope=studio&doc=tasks-template).
Implementation slices must move frontend app concepts and backend/service contracts together rather than treating server changes as incidental follow-through.

### JavaScript Maintenance Gate

Use this gate before changing browser JavaScript files with maintenance score 2, total risk score 6 or higher, or recent churn that suggests ownership drift.

Before editing, answer:

- What complete responsibility is being added, changed, or moved?
- Which module owns that responsibility after the change?
- Does the route shell keep only orchestration, config handoff, event wiring, ready/busy projection, and calls into focused owners?
- Is there a focused module smoke check for behavior that moved out of route boot?
- Does the inventory score need revisiting after the slice?

Default rules:

- Do not add a new complete responsibility to a maintenance-score-2 file unless the same slice creates or extends the focused owner for that responsibility.
- Prefer explicit input/output helpers over helper functions that read or mutate a broad route `state` object directly.
- Define the owning surface before adding new UI behavior; do not let the current renderer or route shell become the owner by default.
- Avoid cosmetic splits that only move tiny helpers. Extract around stable ownership boundaries such as rendering, modal lifecycle, service orchestration, result shaping, validation, import/export flow, route-state projection, or domain logic.
- Rescore only when future changes have a clearer destination, behavior has focused checks, or route-load/input-time work was actually reduced.

Batch sizing:

- Work by route family or coherent runtime surface, not by strict inventory rank.
- A good batch usually moves one complete responsibility out of one route shell, applies one shared route-family pattern across sibling files, or installs one shared helper plus the routes that already need it.
- A batch is too small when it only moves local helpers without changing ownership, testability, route-load behavior, or future-change destination.
- A batch is too large when it spans unrelated route families, mixes public runtime and Studio-only risk, or requires several independent browser workflows to verify safely.
- If a guardrail slice is needed first, define the follow-on score-moving slice, target score movement, and evidence required before rescoring.

Task definition checklist:

- target files and current inventory scores
- responsibility being added, moved, pinned, or deliberately left in place
- focused owner module after the slice
- route/controller responsibilities that should remain local
- behavior that must not be reintroduced into the high-risk file
- acceptance checks and smoke-test file names
- inventory rows to revisit after verification
- owning docs and generated-payload follow-through

For score-6 or score-7 controllers, leave a lightweight owner note in the relevant inventory or child doc when touched:

- what remains in the controller
- what moved to a focused owner
- what future changes should use that owner
- what should not be reintroduced into the controller

Useful checks and follow-through:

- Run `$HOME/miniconda3/bin/python3 studio/checks/javascript_inventory_guardrail.py` before or after a JavaScript risk-reduction batch to inspect maintenance-score counts, line share, churn, overlap risk, and top risk files.
- Use focused browser module smokes where practical: serve the site root through a temporary local static server, import browser modules directly in Playwright, stub config/data/service/DOM inputs, assert helper contracts without full route boot, and import affected route shells to catch syntax and dependency regressions.
- After material JavaScript risk-reduction work, update [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory), and update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) when Docs Viewer-specific rows or follow-up tasks changed.

### Docs Viewer App Architecture Gate

Use this gate before changing Docs Viewer runtime/app architecture, especially work related to app session, state domains, service adapters, app composition, public/manage context, controller lifecycle, panels, hosted views, or management/backend contracts.
The current architecture is documented in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).
Use durable owner docs for current rules and follow-up notes, not a change request document.

Before editing, answer:

- What frontend app concept is being introduced or clarified?
- Which app context, state domain, service adapter, controller, or view owns it after the change?
- What backend capability, generated-data contract, service endpoint, browser storage contract, or local-only read/write boundary does it consume?
- Is the backend/service contract already clean enough, or does the child task need paired backend/service cleanup?
- Did the review find a compatibility path, broad callback, broad state dependency, legacy storage migration, or temporary alias? If yes, remove it in this slice when the owner contract is clear. If removal is not safe, stop and create a named follow-up task with owner, removal/narrowing target, reason it cannot be removed now, and verification requirement before adding adjacent feature behavior.
- How does the slice preserve public read-only behavior without management assets or backend capability probes?
- How does the slice preserve manage-mode backend authority for writes, imports, settings, scope lifecycle, rebuilds, source opening, and local-only data?

Default rules:

- Compatibility paths are not an acceptable end state. A slice that finds one must remove it, rename it as a current owner contract because it is not actually compatibility, or create a named blocker/follow-up with removal criteria in the owning task tracker.
- Tests, smoke fixtures, helper convenience, or route config compatibility are not reasons to keep an old runtime field, alias, broad callback, or legacy handoff. Retarget tests and helpers to the current owner contract before or with runtime cleanup.
- Do not introduce frontend service adapters that merely hide unclear backend ownership.
- Do not move browser code closer to write authority; writes remain behind named backend endpoints with server-side validation.
- Do not let route config imply backend write capability. Static route/app context and backend capability truth are separate.
- Use explicit app context, state-domain, service-adapter, controller, hosted-view context, or view-model structures. Do not add repeated local checks against broad state flags when a named owner contract can provide the needed shape.
- If one UI slot has public-safe and manage-only meanings, model those as separate or separately-shaped view contracts. Do not implement the slot as one broad view with scattered mode checks.
- Public-safe hosted views must receive explicit selected-document, route/access, payload, viewer-scope, URL, trail, and display-label inputs from the hosted-view context, and must not receive management services, backend probes, local generated-read service base URLs, write-capable handles, or management assets.
- Manage-only hosted views may receive explicit management service or capability inputs, but visibility, registration, route config, or toolbar availability must not imply write authority.
- Feature-facing generated reads must go through `docs-viewer-generated-data-runtime.js`; direct `docs-viewer-data.js` imports stay limited to the generated-data runtime and config service owners.
- Management writes, imports, settings, scope lifecycle, rebuilds, source opening, and local-only data must go through `docs-viewer-management-client.js` and server-side management endpoints with validation.
- Do not add new feature lifecycle ownership to `docs-viewer-app-runtime.js`. It is the private app runtime coordinator for focused controller construction, event wiring, route-global updates, private management/startup callbacks, and the small returned app handle.
- Keep implementation details in child task documents; keep parent requests as policy, benefits, and slice-framing records.

## 4. Implement In A Focused Slice

Keep the implementation slice small enough to verify and summarize.

During implementation:

- preserve existing Jekyll, Liquid, JavaScript, CSS, and Python conventions
- prefer structured parsers or config APIs over ad hoc string manipulation
- keep unrelated refactors out of the change
- avoid widening local write-service paths or CORS behavior
- prefer direct browser reads for browser-safe repo/generated artifacts; do not add local server read endpoints merely to preserve a module boundary when the data is already safe and available as static JSON/config
- reserve local service reads for source files, protected or local-only data, external workspace roots, capability checks, and data that cannot or should not be exposed as browser assets
- use dry-run behavior for generators before write runs unless the task explicitly requires writing
- keep user-specific paths, tokens, and local credentials out of tracked docs and source

If a request grows beyond a single safe slice, stop at a checkpoint with completed work, checks run, risks, and the next slice.

## 5. Verify Proportionally

Choose the smallest useful check set:

- Docs-only source changes: source review is usually enough unless generated payloads or docs search need to be rebuilt.
- Python changes: run a syntax check or focused pytest with the configured Python interpreter.
- Script/generator changes: run dry-run behavior and summarize what would be written.
- Data model or generated contract changes: verify the owning builder, generated output shape, and affected docs.
- UI/layout changes: verify desktop and mobile behavior when practical.
- Broad behavior changes: use [Run Checks](/docs/?scope=studio&doc=scripts-run-checks) with the narrowest relevant profile.

Use explicit toolchain paths where the repo requires them.
See [Local Setup](/docs/?scope=studio&doc=local-setup), [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies), and [Testing](/docs/?scope=studio&doc=testing).

For checks that clearly bind loopback ports or launch browser smokes, run them with elevated localhost permissions immediately when working in the Codex sandbox.
This applies to local-service smokes, Playwright checks that start a temporary HTTP server, and run-check profiles whose purpose is browser or service verification.
Keep pure syntax checks, `git diff --check`, JSON parsing, and non-network pytest runs sandboxed.

When sweeping for stale references during verification, keep the scan focused on the surface that can regress:

- always scan active code, config, runtime assets, scripts, and tests relevant to the change
- scan current owning docs when documentation is part of the task
- scan active request or task docs when closing or updating that request
- exclude logs, historical change docs, and broad request-history docs by default
- only include historical logs when the active task is specifically to clean docs logs history.

Use this as the default shape for repo sweeps, replacing `PATTERN` with the retired path, symbol, or URL under review:

```bash
rg -n "PATTERN" \
  bin _config.yml docs-viewer studio scripts assets \
  --glob '!docs-viewer/source/studio/site-change-log*.md' \
  --glob '!docs-viewer/source/studio/site-request-*.md' \
  --glob '!studio/workflows/change-requests/logs/**'
```

Run a separate targeted docs sweep only when needed, against current owning docs such as `docs-viewer.md`, `scripts-*.md`, `local-setup.md`, or `source-tree-ownership.md`.

### Defensive Tests During Refactors

Temporary defensive tests are useful while a migration or extraction is in progress, especially to catch accidental compatibility shims, proxy paths, or retired write surfaces.
Before closeout, remove those tests unless they enforce a current architecture contract.

If a defensive assertion remains, phrase it around the positive architecture that must hold, such as the owning service boundary, allowed route surface, capability model, or write contract.
Avoid permanent tests that only enumerate historical "do not restore this old path" cases.

## 6. Update Docs And Generated Artifacts

When behavior changes, update the owning reference doc in the same change.

Common follow-through:

- Docs Viewer source changes under `docs-viewer/source/<scope>/` require same-scope docs-viewer payload follow-through when the generated payload update is part of the slice.
- Search behavior or schema changes require relevant Search child docs and search payload rebuilds.
- Script behavior changes require the script-specific child doc under [Scripts](/docs/?scope=studio&doc=scripts).
- Config behavior changes require the owning config doc under [Config](/docs/?scope=studio&doc=config).
- Data contract changes require the relevant child doc under [Data Models](/docs/?scope=studio&doc=data-models).

Do not assume Jekyll alone updates Docs Viewer content.
Generated docs/search payloads are separate artifacts.

## 7. Close Out The Work

A close-out should include:

- changed files and the purpose of the change
- verification run and result
- generated payloads updated or intentionally not rebuilt
- remaining risks or follow-up tasks
- request status updates when the work was driven by a change request
- mark completed tasks clearly
- mark an owning change request `done` only when durable docs contain the important decisions, verification is recorded, and remaining risks are explicit.

## 8. Record Durable Change History

The source model and authoring workflow for change logs are documented in `studio/workflows/change-requests/README.md`.

- create structured log entries under `studio/workflows/change-requests/logs/entries/` for meaningful completed changes
- include `change_request_doc_id` when a log entry implements or closes a request
- include related docs and files so Codex can trace decisions later
- let generated indexes and reports provide human browsing

Create structured docs-log entries when the work changes durable behavior or closes a meaningful request: runtime behavior, command or service contracts, public routes, generated-data schemas, material workflow/process decisions, or a completed change request that future sessions need to trace.
Do not create docs-log entries for routine task-row status updates, verification-only slices, small copy fixes, local smoke reruns, mechanical path-reference cleanup, or no-code/no-behavior confirmations.
For multi-task requests, prefer one close-out log entry at the closure slice instead of one log entry per verification or bookkeeping subtask.

## Documentation Review Candidates

This workflow exposes a few areas where the docs are useful but may need later review.
These are not part of the current implementation task.

- AGENTS.md still carries detailed procedural guidance that could move into this workflow doc once the workflow is stable.
- State routing and module-dependency guidance exists across route, runtime, and script docs but may need a shorter “where to look first” index.
