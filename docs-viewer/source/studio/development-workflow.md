---
doc_id: development-workflow
title: Development Workflow
added_date: 2026-05-19
last_updated: 2026-07-14
parent_id: dev-home
viewable: true
---
# Development Workflow

This document is the repo-specific lifecycle guide for major new features, behavior changes, refactors, and meaningful documentation changes.

- Use it to decide what to read, what to update, and how to close work out. It is intentionally a router to focused docs rather than a replacement for them.
- Detailed implementation rules live in [Development Checklist](/docs/?scope=studio&doc=development-checklist).

## Fast Path

For any non-trivial change:

1. Classify the work: feature, bugfix, refactor, documentation, generated-data change, UI change, or workflow change. Read the owning section docs before editing.
2. Separate broad concept work from delivery. Put complete outcomes and their sequence on the owning roadmap.
3. Create a [Change Request](/docs/?scope=studio&doc=change-requests) only when one roadmap outcome is ready to implement and finish.
4. Add a task tracker only when coordination inside that bounded request genuinely needs one.
5. Keep implementation scoped to the owning runtime, script, data model, or UI primitive.
6. Run targeted verification proportional to the blast radius.
7. Update the one durable owner whose behavior or navigation changed.
8. Close the request only when its complete outcome has shipped.

## 1. Classify The Work

Use the smallest owning area that explains the change:

- Site architecture or route/runtime behavior: [Architecture](/docs/?scope=studio&doc=architecture)
- Studio route behavior: [Studio](/docs/?scope=studio&doc=studio)
- Docs Viewer behavior: [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- Docs Viewer frontend-app architecture work: [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- Search behavior, schema, ranking, or build flow: [Search](/docs/?scope=studio&doc=search)
- Scripts, local services, and command behavior: [Scripts](/docs/?scope=studio&doc=scripts)
- Source tree ownership or source/public boundary behavior: [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)
- Local setup, dependency, or environment behavior: [Local Setup](/docs/?scope=studio&doc=local-setup) and [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)
- Test strategy and check profiles: [Testing](/docs/?scope=studio&doc=testing), [Run Checks](/docs/?scope=studio&doc=scripts-run-checks), and [Pytest](/docs/?scope=studio&doc=testing-pytest)

## 2. Move From Concept To Delivery

Use a concept document when the problem is useful but the outcome, tradeoffs, or delivery shape are still being explored. Concept documents may be broad. They do not imply priority and should not turn discussion directly into an implementation checklist.

For a substantial feature, use one short parent under [Change Requests](/docs/?scope=studio&doc=change-requests) to group separate concept, proposed architecture, and promoted delivery documents. The feature parent routes between them; it does not repeat them. The architecture child may explain intended ownership and pressure points, but shipped current behavior still belongs to durable owner documents and the code.

Use the owning product roadmap to split a concept into independently finishable outcomes. The roadmap owns:

- delivery order and importance
- prerequisite relationships
- current status
- the active request link, when a row is ready

Then create one [Change Request](/docs/?scope=studio&doc=change-requests) for one complete roadmap outcome. Its in-scope work may cross several modules, but all of it must contribute to the same verifiable result.

A request is not ready while an open decision could fundamentally change its outcome. Resolve the decision in the concept or make investigation itself a small, explicit deliverable.

Small bugfixes, narrow docs edits, and mechanical cleanup usually do not need either a roadmap row or a request.

Keep concepts, roadmaps, and requests manually curated. None is the durable implementation log.

## 3. Shape The Implementation

Use existing repo boundaries:

- Extend shared modules and primitives before creating one-off route-local patterns.
- Use a package or directory namespace when a helper surface has multiple responsibilities, is likely to grow, or is becoming an explicit architecture boundary.
- Keep UI shell, validation, data mutation, and generated-output behavior separate.
- Keep config ownership in checked-in config docs and loader modules.
- Keep generated data flowing from source records through scripts; do not edit generated payloads as source.
- Keep source docs under the owning scope and use Docs Viewer links for published doc references.

### Suggested References

This is a list of the most common references within the documenattion:

- For local Studio route migration, public-link resolver adoption, Studio route URL builders, and UI Catalogue demo visibility, use [Development Checklist](/docs/?scope=studio&doc=development-checklist).
- For UI work, start with [UI](/docs/?scope=studio&doc=ui) and child documents.
- For search work, start with [Search](/docs/?scope=studio&doc=search) and update search child docs when schema, ranking, normalization, UI, build flow, or validation changes materially.
- For scripts or local services, use [Scripts](/docs/?scope=studio&doc=scripts) and the script-specific child doc.
- For browser JavaScript maintenance-risk work, use [Risk Analysis Policy](/docs/?scope=studio&doc=risk-analysis-policy) for scoring.
- For Docs Viewer frontend-app architecture work, start with [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview).

When coordination inside one request genuinely needs a task tracker, create one from [Tasks Tracker Template](/docs/?scope=studio&doc=tasks-tracker-template). If the tracker contains independently useful outcomes, split the request on the roadmap instead.

Implementation slices must move frontend app concepts and backend/service contracts together rather than treating server changes as incidental follow-through.

### Config Cleanup Gate

Use this gate before pruning, moving, or widening checked-in app config, UI-text config, generated-default config, or browser-visible runtime config.

Before editing, classify each key or payload field under review:

- browser bootstrap config
- browser-safe static fallback read
- runtime-injected server config
- server-only source, write, adapter, or path contract
- generated output or report projection
- UI text or operation-owned workflow copy
- historical, transitional, or unconsumed key

## Default rules

- Start every cleanup slice with active call-site scans across code, config loaders, server routes, services, tests, and generated-default pipelines. Historical request docs can explain why a key existed, but they are not proof of current ownership.
- Remove a key only when no active route, service, test, generated-default pipeline, or documented operator workflow consumes it.
- Do not move server-only source paths, write targets, adapter path contracts, output patterns, metadata contracts, activity emit metadata, or source-write scope into browser bootstrap config.
- Keep browser public/config endpoints on explicit whitelists when they project domain config. Passing through nested source config is not an acceptable shortcut.
- Keep UI copy in frontend route modules unless the string is operation-owned workflow metadata.
- When a cleanup preserves a browser-visible surface, use a positive owner-contract test that asserts the allowed key set or whitelisted payload shape.
- Update the owning config doc in the same slice with removed keys, retained keys, owner, and reason.

Good cleanup outcomes include a narrower browser-facing payload, a clearer static-fallback contract, a server-only config path removed from public projection, or a focused test that prevents the surface from widening silently.

Poor cleanup outcomes include compatibility aliases for retired paths, hiding active paths in unowned constants, deleting keys based only on historical docs, or keeping a broad payload because tests or fixtures still depend on it.

### JavaScript Maintenance Gate

Use this gate before changing browser JavaScript files:

Before editing, answer:

- What complete responsibility is being added, changed, or moved?
- Which module owns that responsibility after the change?
- Does the route shell keep only orchestration, config handoff, event wiring, ready/busy projection, and calls into focused owners?
- Is there a focused module smoke check for behavior that moved out of route boot?

Refactoring: default rules:

- Do not add a new complete responsibility to a file unless the same slice creates or extends the focused owner for that responsibility.
- Use explicit input/output helpers over helper functions that read or mutate a broad route `state` object directly.
- Define the owning surface before adding new UI behavior; do not let the current renderer or route shell become the owner by default.
- When refactoring, extract around stable ownership boundaries such as rendering, modal lifecycle, service orchestration, result shaping, validation, import/export flow, route-state projection, or domain logic.

Refactoring: batch sizing:

- Work by route family or coherent runtime surface
- A good batch usually moves one complete responsibility out of one route shell, applies one shared route-family pattern across sibling files, or installs one shared helper plus the routes that already need it.
- A batch is too small when it only moves local helpers without changing ownership, testability, route-load behavior, or future-change destination.
- A batch is too large when it spans unrelated route families, mixes public runtime and Studio-only risk, or requires several independent browser workflows to verify safely.

Task definition checklist:

- responsibility being added, moved, pinned, or deliberately left in place
- focused owner module after the slice
- route/controller responsibilities that should remain local
- behavior that must not be reintroduced into the high-risk file
- acceptance checks and smoke-test file names
- owning docs and generated-payload follow-through

Useful checks and follow-through:

- Use browser smokes only for integration behavior that needs a browser, such as route boot, service-backed route reads, and representative user workflows. Keep helper contracts in cheaper focused tests; do not create broad browser module-contract suites with duplicated runtime fixtures.

### Docs Viewer App Architecture Gate

Use this gate before changing Docs Viewer runtime/app architecture, especially work related to app session, state domains, service adapters, app composition, public/manage context, controller lifecycle, panels, hosted views, or management/backend contracts.

The current architecture is documented in:
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary),
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)

Use durable owner docs for current rules and follow-up notes, not a change request document.

Before editing, answer:

- What frontend app concept is being introduced or clarified?
- Which app context, state domain, service adapter, controller, or view owns it after the change?
- What backend capability, generated-data contract, service endpoint, browser storage contract, or local-only read/write boundary does it consume?
- Is the backend/service contract already clean enough, or does the child task need paired backend/service cleanup?
- Did the review find a compatibility path, broad callback, broad state dependency, legacy storage migration, or temporary alias? If yes, remove it in this slice when the owner contract is clear.
- If code removal is not safe, stop and create a named follow-up task with owner, removal/narrowing target, reason it cannot be removed now, and verification requirement before adding adjacent feature behavior.
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
- Keep implementation detail in the code or an optional task tracker; keep the request focused on one complete outcome, its boundaries, and proof of completion.

## 4. Implement In A Focused Slice

Keep the implementation slice small enough to verify and summarize.

During implementation:

- use structured parsers or config APIs and not ad hoc string manipulation
- report potential refactors
- use direct browser reads for browser-safe repo/generated artifacts; do not add local server read endpoints merely to preserve a module boundary when the data is already safe and available as static JSON/config
- reserve local service reads for source files, protected or local-only data, external workspace roots, capability checks, and data that cannot or should not be exposed as browser assets
- validate dry-run behavior for generators before write runs
- keep user-specific paths, tokens, and local credentials out of tracked docs and source

Before implementation, split any request whose result cannot be completed coherently. During implementation, do not widen a request when another useful outcome appears: add that outcome to the roadmap.

If unexpected work prevents completion, stop at a safe working boundary. Close the current request only if what remains is still a complete useful outcome in its own right; otherwise the request remains open and the roadmap must be reshaped before more implementation begins.

## 5. Verify Proportionally

Choose the smallest useful check set:

- Docs-only source changes: source review is usually enough unless generated payloads or docs search need to be rebuilt.
- Python changes: run a syntax check or focused pytest with the configured Python interpreter.
- Script/generator changes: run dry-run behavior and summarize what would be written.
- Data model or generated contract changes: verify the owning builder, generated output shape, and affected docs.
- UI/layout changes: verify desktop behavior when practical. Only verify mobile behavior where public pages on the site (dotlineform.com) will be affected.
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
  --glob '!docs-viewer/source/studio/site-request-*.md'
```

Run a separate targeted docs sweep only when needed, against current owning docs such as `docs-viewer.md`, `scripts-*.md`, `local-setup.md`, or `source-tree-ownership.md`.

### Defensive Tests During Refactors

- Temporary defensive tests are only useful while a migration or extraction is in progress, especially to catch accidental compatibility shims, proxy paths, or retired write surfaces.
- Before closeout, remove those tests unless they enforce a current architecture contract.
- When a defensive assertion remains, it must still assert the positive architecture that must hold, such as the owning service boundary, allowed route surface, capability model, or write contract.
- Do not create permanent tests that enumerate historical "do not restore this old path" cases.

## 6. Update Docs And Generated Artifacts

- When behavior changes, update the owning durable reference doc in the same change.
- Update one durable owner by default. Touch another document only when its own workflow, contract, or navigation changed.
- Use an inline link when it identifies an authority, prerequisite, or actual next step. Avoid generic related-document lists that add link maintenance without helping the workflow.
- Do not treat the parent change request or task plan as a durable doc.

## 7. Close Out The Work

A close-out should include:

- changed files and the purpose of the change
- verification run and result
- generated payloads updated or intentionally not rebuilt
- remaining risks and any separately finishable follow-up roadmap rows
- request status updates when the work was driven by a change request
- mark completed tasks clearly
- mark an owning change request `done` only when its whole outcome works, durable docs contain the shipped behavior, verification is recorded, and remaining risks are explicit
- do not leave unfinished phases inside a completed request; later capability belongs on the roadmap

## Documentation Review Candidates

This workflow exposes a few areas where the docs are useful but may need later review.
These are not part of the current implementation task.

- AGENTS.md still carries detailed procedural guidance that could move into this workflow doc once the workflow is stable.
- State routing and module-dependency guidance exists across route, runtime, and script docs but may need a shorter “where to look first” index.
