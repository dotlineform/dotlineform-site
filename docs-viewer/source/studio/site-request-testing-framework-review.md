---
doc_id: site-request-testing-framework-review
title: Testing Framework Review Request
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: in-progress
parent_id: change-requests
sort_order: 16000
viewable: true
---
# Testing Framework Review Request

This request tracks a review of the repo's testing framework after recent Docs Viewer and Studio migrations.

- The goal is to identify old baggage, stale compatibility assertions, duplicated smoke coverage, and tests that now constrain retired architecture.
- It is not a request to rewrite the full test suite by default. But it should provide meaningful recommendations for improvement, which may point to a wider rewrite.
- It should also check whether test output and filesystem side effects are quiet enough for Codex sessions, docs watchers, and focused local development.

Useful owning docs:

- [Testing](/docs/?scope=studio&doc=testing)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture)

## Status

### steer for this request

- Run this after the current Docs Viewer app architecture request lands.
- Treat tests as evidence of existing behavior, not as permanent architecture constraints.
- Keep useful regression coverage, especially for route behavior, generated-data contracts, local write services, public read-only behavior, and management write authority.
- Tests must assert current owner contracts instead of historical compatibility surfaces.
- If a Docs Viewer test asserts a legacy compatibility or fence and it passes, this means that the code being tested does not conform to the latest app development standard and needs to be fixed and the test corrected.
- Remove or rewrite a test when its covered risk is obsolete, duplicated, or better expressed through a focused owner contract.
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

For rewrite, consolidate, retire, or defer items, record the reason, the owner and the follow-up slice.

## First-Pass Review Result

The first-pass inventory is recorded in [Testing Framework Inventory](/docs/?scope=studio&doc=site-request-testing-framework-inventory).

Summary:

- Current tests already mostly follow the newer Docs Viewer and Studio ownership boundaries.
- The most important Docs Viewer app-handle lesson is now covered by an intentional architecture guard: the app boot smoke asserts the runtime handle does not expose broad `state`, composition, session, management, or route-workflow bridges.
- Retained compatibility tests are narrow and should be treated as explicit migration or retired-behavior guards, not permanent architecture surfaces.
- The clearest consolidation candidate is smoke-profile overlap: both `docs-viewer-smoke` and `studio-smoke` run public Docs Viewer read-only and Docs HTML import module checks.
- The clearest rewrite candidate is the broad Docs Viewer route smoke, which mixes route/history/search/index-panel/missing-doc/hash concerns.
- The runner output is already concise enough for Codex-oriented debugging: command progress and log paths go to console, detailed output goes to `var/test-runs/`.
- Cache and bytecode side effects are ignored by git; temp repos are generally created under `tempfile.TemporaryDirectory()`.
- Deferred rewrites have named owners and reasons in the inventory.

No test code, smoke helper, runner behavior, or durable testing policy changed in this first pass.

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
| 1 | done | Inventory current testing entrypoints, check profiles, Docs Viewer smokes, Studio smokes, Python tests, fixtures, and generated-output assumptions. Deliverable: [Testing Framework Inventory](/docs/?scope=studio&doc=site-request-testing-framework-inventory). |
| 2 | done | Classified test coverage by purpose in the inventory: product regression, architecture guard, migration compatibility, generated-data contract, local-service contract, public read-only behavior, management write authority, environment smoke, and docs-only validation. |
| 3 | done | Audited stale compatibility assertions. The Docs Viewer app-handle lesson is recorded as an intentional architecture guard: tests should reject broad state or runtime bridges unless they are named current app contracts. |
| 4 | done | Audited broad route/controller state coupling. Main rewrite candidate is `docs-viewer/tests/smoke/docs_viewer_routes.py`; deferred route-shell smokes need owner-specific slices. |
| 5 | done | Audited smoke tests for mixed responsibilities, duplicated coverage, localhost/browser setup, generated-payload assumptions, and watcher side effects. |
| 6 | done | Identified quick wins in the inventory: smoke role map, one temp-dir cleanup, Docs Viewer route smoke split, duplicate smoke coverage note, and `full` profile docs clarity. |
| 7 | done | Identified deferred rewrites with owners and reasons: legacy hidden input handling, catalogue media-section migration, docs-log migration, unprofiled Studio route smokes, and smoke-profile merging. |
| 8 | done | Reviewed `run_checks.py` profiles. Current grouping still supports the lightweight opt-in model; the main docs drift risk is that `full` omits `docs-viewer-smoke`. |
| 9 | done | Reviewed pytest and runner noise. Runner output is concise; logs are written under ignored `var/test-runs/`; `.pytest_cache` and `__pycache__` are ignored; temp files are mostly contained. |
| 10 | done | No durable testing policy, profile behavior, cache handling, or smoke convention changed in this pass, so Testing, Run Checks, and Studio Smoke Testing did not need policy edits beyond this request/inventory record. |
| 11 | done | Ran the smallest warranted verification for docs-only review: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --list`, `git diff --check`, and a focused changed-doc sanitization scan. |
| 12 | deferred | No structured docs-log entry was created because this first pass did not change durable testing policy, retire significant coverage, or change check profile behavior. |

The closeout for this request should confirm:

- old migration/compatibility baggage has been inventoried
- retained compatibility tests have intentional and documented purpose to expose compatibility layers
- broad state and runtime-handle assertions are not preserving retired architecture
- Docs Viewer and Studio smoke responsibilities are clear enough for future migrations
- check profiles still match the repo's lightweight opt-in testing model
- pytest and smoke outputs are concise enough for Codex-oriented debugging
- cache, bytecode, temporary file, generated-log, and watcher side effects are intentionally handled
- any deferred rewrites have a named reason and owner
