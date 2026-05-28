---
doc_id: site-request-testing-framework-review
title: Testing Framework Review Request
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: planned
parent_id: change-requests
sort_order: 16000
viewable: true
---
# Testing Framework Review Request

This request tracks a lightweight review of the repo's testing framework after recent Docs Viewer and Studio migrations.

The goal is to identify old baggage, stale compatibility assertions, duplicated smoke coverage, and tests that now constrain retired architecture.
It is not a request to rewrite the full test suite by default.
It should also check whether test output and filesystem side effects are quiet enough for Codex sessions, docs watchers, and focused local development.

Useful owning docs:

- [Testing](/docs/?scope=studio&doc=testing)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture)

## Status

### steer for this request

- Run this after the current Docs Viewer app architecture request lands, but before the next large Studio or Docs Viewer migration.
- Treat tests as evidence of existing behavior, not as permanent architecture constraints.
- Prefer inventory, classification, and targeted quick wins over a broad rewrite.
- Keep useful regression coverage, especially for route behavior, generated-data contracts, local write services, public read-only behavior, and management write authority.
- Do not remove a test just because it is old; remove or rewrite it only when its covered risk is obsolete, duplicated, or better expressed through a focused owner contract.
- Preserve the lightweight opt-in testing model unless the review finds a concrete reason to change it.
- Keep test output concise enough for Codex to report failures without dumping long logs into the conversation.
- Keep pytest/cache/bytecode/temp-file side effects from dirtying the worktree or needlessly triggering watchers.

### review targets

- `studio/commands/run_checks.py`
- `studio/tests/python/`
- `studio/tests/smoke/`
- `docs-viewer/tests/python/`
- `docs-viewer/tests/smoke/`
- focused smoke helpers that start local servers, launch Playwright, or depend on generated payloads
- docs describing check profiles, smoke strategy, or expected close-out behavior

### audit points

- stale compatibility assertions that preserve old route, runtime, service, or state shapes
- tests coupled to broad route/controller state instead of focused owner APIs or DOM/user-visible behavior
- tests named for old architecture, retired routes, or old module ownership
- duplicated smoke coverage that slows feedback without adding meaningful risk coverage
- tests that verify implementation details better covered by smaller module tests
- tests that should become explicit architecture-guard tests
- fragile localhost, browser, generated-payload, watcher, or environment assumptions
- smoke tests that mix too many unrelated responsibilities
- generated payload or docs-watcher side effects that tests accidentally depend on
- docs that describe historical compatibility behavior as current testing policy
- noisy pytest output, repeated warnings, broad stack traces, or profile output that buries the actionable failure
- filesystem noise from `.pytest_cache`, `__pycache__`, temporary files, or generated logs outside ignored locations
- run profiles that should log detailed output to files while printing only a concise console summary

### expected deliverable

The first pass should produce a short inventory and triage table.
Each finding should be classified as one of:

- keep
- rewrite
- consolidate
- retire
- defer

For rewrite, consolidate, retire, or defer items, record the reason and the owner or follow-up slice.

## Baseline Verification

This request is mostly documentation and test-inventory work.
Run checks only when the review changes tests, runners, or smoke helpers.

Likely verification:

- docs-only review for tracker updates
- `git diff --check`
- focused syntax checks for changed Python or JavaScript helpers
- the smallest affected `studio/commands/run_checks.py --profile <profile>` run when a profile or test grouping changes
- focused Playwright smoke reruns when browser smoke logic changes

Codex sandbox note: browser and localhost smoke checks need elevated permissions even when product code is healthy.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current testing entrypoints, check profiles, Docs Viewer smokes, Studio smokes, Python tests, fixtures, and generated-output assumptions. Deliverable: concise map in this request or a sibling inventory doc if it grows. |
| 2 | planned | Classify test coverage by purpose: product regression, architecture guard, migration compatibility, generated-data contract, local-service contract, public read-only behavior, management write authority, environment smoke, or docs-only validation. |
| 3 | planned | Audit for stale compatibility assertions that preserve old runtime, route, state, service, or shell shapes. Include the explicit Docs Viewer app-handle lesson: tests should not keep broad state or runtime bridges alive unless they are intentional app contracts. |
| 4 | planned | Audit for tests coupled to broad route/controller state where focused owner APIs or DOM/user-visible behavior would better express the contract. |
| 5 | planned | Audit smoke tests for excessive responsibility mixing, duplicated coverage, fragile localhost/browser setup, generated-payload assumptions, and watcher side effects. |
| 6 | planned | Identify quick wins that can be safely rewritten, consolidated, renamed, or retired without reducing meaningful regression coverage. |
| 7 | planned | Identify deferred rewrites that need a product or architecture slice before they can be changed safely. |
| 8 | planned | Review `run_checks.py` profiles for stale grouping, unclear names, slow checks in common paths, missing focused checks, and profile docs drift. |
| 9 | planned | Review pytest and runner noise: default verbosity, repeated warnings, failure trace length, `.pytest_cache`, `__pycache__`, temporary files, generated logs, watcher side effects, and whether profile output should be summarized more aggressively for Codex. |
| 10 | planned | Update Testing, Run Checks, Studio Smoke Testing, and any affected owner docs if testing policy, profile purpose, output expectations, cache handling, or smoke conventions change. |
| 11 | planned | Run the smallest verification set warranted by any changed tests or runners and record pass/fail plus remaining risks. |
| 12 | planned | Create a structured docs-log entry if the review changes durable testing policy, retires significant old coverage, or changes check profile behavior. |

The closeout for this request should confirm:

- old migration/compatibility baggage has been inventoried
- retained compatibility tests are intentional and documented
- broad state and runtime-handle assertions are not preserving retired architecture
- Docs Viewer and Studio smoke responsibilities are clear enough for future migrations
- check profiles still match the repo's lightweight opt-in testing model
- pytest and smoke outputs are concise enough for Codex-oriented debugging
- cache, bytecode, temporary file, generated-log, and watcher side effects are intentionally handled
- any deferred rewrites have a named reason and owner
