---
doc_id: site-request-docs-viewer-public-index-slimming-batch-3a
title: Docs Viewer Public Index Slimming Batch 3a
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: done
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 3a: Smoke Test Diet

This is the delivery specification for Batch 3a in [Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 3a: Smoke Test Diet

Summary: Replace and retire the high-maintenance Docs Viewer mega-smoke pattern before Batch 4 adds more runtime and rendering changes.

| ID | status | action |
| --- | --- | --- |
| 3a.1 | done | Retire `docs_viewer_app_shell_modules.py` as a required smoke target; do not modularize or preserve the 4,500-line mega-smoke as the default path. |
| 3a.2 | done | Replace the retired mega-smoke with a small set of focused browser smokes that prove public `/library/`, public `/analysis/`, and manage `/docs/` boot and load a selected doc through route-appropriate generated payloads. |
| 3a.3 | done | Move valuable low-level contracts out of browser smoke where practical, especially route config normalization, generated-data URL selection, compact tree/recent adapters, and management generated-read endpoints. |
| 3a.4 | done | Delete brittle assertions that check implementation trivia, exact callback ordering, duplicated fixture object shape, or negative requests not tied to a concrete regression risk. |
| 3a.5 | done | Aggressively rationalize other Docs Viewer smoke files using the same standard: keep only durable end-to-end checks, move focused contracts to cheaper tests, and delete the rest. |
| 3a.6 | done | Update the Docs Viewer verification guidance so future batches require focused tests and minimal end-to-end smoke checks instead of broad module-contract browser tests. |

## Steer for these tasks

- The goal is lower maintenance cost, not lower confidence.
- Keep browser checks only where a browser is actually proving integration that unit or Python tests cannot prove cheaply.
- Negative assertions need a concrete regression they protect against; otherwise remove them.
- Do not preserve the mega-smoke just because it already exists.
- Do not change runtime code or runtime behavior in this batch; this batch is limited to smoke tests, focused test coverage, fixtures, and verification guidance.
- `docs_viewer_app_shell_modules.py` is too large and too fixture-heavy to be a healthy smoke test. The preferred end state is replacement and removal from required verification, not splitting the same bad pattern into smaller files.
- Fallbacks to broad browser module-contract tests, duplicated inline route configs, or large assertion collections are not acceptable end states.

## Deliverables

- Replacement smoke coverage with a small number of durable browser checks.
- `docs_viewer_app_shell_modules.py` removed from required smoke execution, deleted if practical, or left only as clearly deprecated non-required reference during the transition.
- Focused non-browser coverage for contracts that do not need Playwright.
- Updated source documentation for Docs Viewer verification expectations.

## Implementation and policy guidance

- Keep the public index slimming Batch 3 route contract intact: public route boot must use `index-tree.json`, recently-added must use `recently-added.json`, and public route loading must not depend on public docs `index.json`.
- Preserve at least one public and one manage route boot check.
- Prefer small fixtures only when they reduce repeated contract shape; do not create another abstraction layer that preserves the mega-smoke pattern under a new name.
- Runtime source changes are out of scope. If a test exposes a runtime bug, stop and record it as a follow-on implementation task instead of fixing it inside Batch 3a.
- When deleting assertions, record the reason in the implementation notes or verification update if the deletion is non-obvious; do not weaken the new test strategy to keep old assertions alive.

## Proposed verification set

- Syntax check changed Python smoke/test files.
- Run the reduced browser smoke set that remains after the diet.
- Run focused Python/JS checks that replace deleted browser assertions.
- Run `git diff --check`.

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile studio/commands/run_checks.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py docs-viewer/tests/smoke/docs_viewer_service_manage.py docs-viewer/tests/smoke/docs_viewer_routes.py docs-viewer/tests/smoke/docs_viewer_route_smoke_helpers.py`
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke`

## follow-on tasks

- Batch 3 handoff: `docs_viewer_app_shell_modules.py` is about 4,500 lines long and contains many duplicated inline route-config and browser-config records, making route contract changes expensive and failure-prone.
- Batch 3 handoff: keep the route-loading guarantees from Batch 3, but prove them with narrower tests.
- Batch 4 should proceed after this test diet so info-panel hydration changes do not compound the current smoke-test maintenance burden.
- `docs_viewer_app_shell_modules.py` was deleted.
- `docs-viewer-smoke` now runs the Jekyll temp build, standalone service manage smoke, and public read-only smoke only.
- Public read-only and service manage smokes now assert compact `index-tree.json` and `recently-added.json` loading without carrying the old broad module-contract assertion set.
- Module smoke scripts that still exist are not required profile targets; use them only for deliberate, focused follow-up work or delete them when their covered behavior has cheaper coverage.

## task close

- Batch 4 handoff added.
- Tracker row can be marked `done`.
