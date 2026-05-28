---
doc_id: site-request-testing-framework-review
title: Testing Framework Review Request
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
sort_order: 16000
viewable: true
---
This document is archived and is no longer maintained.

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
Durable testing guidance has been moved into [Testing](/docs/?scope=studio&doc=testing), so this request and its inventory can be archived as implementation history.

Summary:

- Current tests already mostly follow the newer Docs Viewer and Studio ownership boundaries.
- The most important Docs Viewer app-handle lesson is now covered by an intentional architecture guard: the app boot smoke asserts the runtime handle does not expose broad `state`, composition, session, management, or route-workflow bridges.
- Retained architecture-guard and current-contract tests are narrow and should not preserve retired behavior.
- Legacy Docs Viewer changelog migration tests were removed because the old Markdown changelog docs are no longer current workflow inputs.
- Current Library and Analysis source docs were normalized from legacy `hidden` front matter to `viewable` front matter.
- Docs source readers, builders, imports, and management mutators now use `viewable` as the only source visibility input.
- Catalogue media-section migration tests were removed because current behavior is the Studio-surfaced target media-section schema.
- The old catalogue media-section migration runner was removed because the one-time migration is complete and no longer represents current Studio behavior.
- The previous smoke-profile overlap has been removed: `studio-smoke` no longer runs Docs Viewer-owned public read-only or HTML import module checks.
- The broad Docs Viewer route smoke has been split into focused navigation, index-panel, and search/missing/hash entrypoints.
- The runner output is already concise enough for Codex-oriented debugging: command progress and log paths go to console, detailed output goes to `var/test-runs/`.
- Cache and bytecode side effects are ignored by git; temp repos are generally created under `tempfile.TemporaryDirectory()`, and smoke-profile Jekyll temp builds now clean up by default.
- Deferred rewrites have named owners and reasons in the inventory.

Runner profile behavior changed after review: `studio-smoke` now stays Studio-owned, and Docs Viewer-owned browser checks stay in `docs-viewer-smoke`.

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
| 4 | done | Audited broad route/controller state coupling. Split `docs-viewer/tests/smoke/docs_viewer_routes.py` into focused route smoke entrypoints while keeping an aggregate wrapper for existing references. |
| 5 | done | Audited smoke tests for mixed responsibilities, duplicated coverage, localhost/browser setup, generated-payload assumptions, and watcher side effects. Removed Docs Viewer-owned smoke commands from `studio-smoke`. |
| 6 | done | Implemented quick wins in the inventory: smoke role map, Data Sharing temp-dir cleanup, Docs Viewer route smoke split, profile ownership clarity, and `full` profile docs clarity. |
| 7 | done | Identified deferred rewrites with owners and reasons: unprofiled Studio route smokes and smoke-profile merging. Retired legacy Docs Viewer changelog migration tests, old catalogue media-section migration tests, the one-time catalogue media-section migration runner, and legacy Docs `hidden` source input handling because those old shapes are no longer current workflow inputs. |
| 8 | done | Reviewed and adjusted `run_checks.py` profiles. Current grouping still supports the lightweight opt-in model; `studio-smoke` now excludes Docs Viewer-owned checks. |
| 9 | done | Reviewed pytest and runner noise. Runner output is concise; logs are written under ignored `var/test-runs/`; `.pytest_cache` and `__pycache__` are ignored; temp files are mostly contained; smoke-profile Jekyll temp builds now clean up by default. |
| 10 | done | Updated Testing and Run Checks docs for the `studio-smoke` profile ownership change. Studio Smoke Testing already describes Docs Viewer and Studio smoke scripts as separate owning boundaries. |
| 11 | done | Ran the smallest warranted verification for the runner/profile and quick-win changes: Python syntax checks for changed runner/test/smoke files, focused Data Sharing adapter pytest, focused Docs Viewer mutation/source/import/management pytest, target catalogue media-section schema validation, `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --list`, `git diff --check`, JSON parse checks for generated docs payloads, and a focused sanitization scan. A focused route browser smoke was attempted against `/tmp/dlf-jekyll-build`, but that target does not serve `/docs/`. |
| 12 | done | Created structured docs-log entries `change-2026-05-28-separated-studio-smoke-from-docs-viewer-smoke`, `change-2026-05-28-implemented-testing-framework-quick-wins`, `change-2026-05-28-added-smoke-temp-build-cleanup`, `change-2026-05-28-retired-legacy-docs-log-migration-tests`, `change-2026-05-28-retired-catalogue-media-section-migration-tests`, `change-2026-05-28-retired-catalogue-media-section-migration-runner`, `change-2026-05-28-normalized-docs-source-viewability-front-matter`, and `change-2026-05-28-retired-docs-hidden-source-input` because check profile behavior and test-framework structure changed. |

The closeout for this request should confirm:

- old migration/compatibility baggage has been inventoried
- retained architecture guards and current-contract tests have intentional documented purpose
- broad state and runtime-handle assertions are not preserving retired architecture
- Docs Viewer and Studio smoke responsibilities are clear enough for future migrations
- check profiles still match the repo's lightweight opt-in testing model
- pytest and smoke outputs are concise enough for Codex-oriented debugging
- cache, bytecode, temporary file, generated-log, and watcher side effects are intentionally handled
- any deferred rewrites have a named reason and owner
