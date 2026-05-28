---
doc_id: site-request-testing-framework-inventory
title: Testing Framework Inventory
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
parent_id: site-request-testing-framework-review
sort_order: 16010
viewable: true
---
# Testing Framework Inventory

This is the first-pass inventory and triage for [Testing Framework Review Request](/docs/?scope=studio&doc=site-request-testing-framework-review).

## Scope

Reviewed surfaces:

- `studio/commands/run_checks.py`
- `studio/tests/python/`
- `studio/tests/smoke/`
- `docs-viewer/tests/python/`
- `docs-viewer/tests/smoke/`
- testing owner docs: [Testing](/docs/?scope=studio&doc=testing), [Run Checks](/docs/?scope=studio&doc=scripts-run-checks), and [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)

Counts from the active tree:

| area | files | collected test functions | primary purpose |
| --- | ---: | ---: | --- |
| `docs-viewer/tests/python/` | 13 | 158 | Docs Viewer service, source-model, generated-read, management, import/export, rebuild, and activity contracts. |
| `docs-viewer/tests/smoke/` | 16 | 0 | Playwright scripts for Docs Viewer public read-only behavior, management UI, browser modules, and service manage shell. |
| `studio/tests/python/` | 49 | 247 | Studio service contracts, catalogue/tag/data-sharing generation and write contracts, local env, activity, R2, and app-server behavior. |
| `studio/tests/smoke/` | 50 | 0 | Playwright route/module smokes for Studio routes, catalogue/tag editors, UI Catalogue, data sharing, and public route runtime. |

The smoke scripts are direct executable checks rather than pytest-collected tests, so they intentionally report zero `test_*` functions.

## Entry Points

| entrypoint | classification | triage | notes |
| --- | --- | --- | --- |
| `quick` profile | product regression, architecture guard, local-service contract, generated-data contract | keep | Good default for lightweight Codex verification. It runs whitespace, syntax, focused pytest, projection, ready-state, and JSON parsing checks. |
| `catalogue` profile | product regression, generated-data contract | keep | Focused and short. The field-aware preview remains useful as a representative generator contract. |
| `docs` profile | Docs Viewer service, generated-data contract, management write authority | keep | Correctly owns Docs Viewer pytest under `docs-viewer/tests/python/` and keeps shared Data Sharing checks under Studio. It does write generated Studio docs/search payloads by design, so it should stay opt-in. |
| `docs-viewer-smoke` profile | public read-only, management UI, browser module, service smoke | keep | Focused Docs Viewer smoke profile. It prepares a temp Jekyll build and copies public generated payloads needed by public smoke checks. |
| `studio-smoke` profile | Studio browser smoke, public read-only, route shell, module contracts | consolidate | It intentionally overlaps public Docs Viewer read-only and HTML import module coverage with `docs-viewer-smoke`. Keep for now, but consider extracting shared browser smokes into a named common smoke slice if profile runtime becomes a problem. |
| `full` profile | broad local verification | keep | Still matches the opt-in model because it expands explicit profiles and deduplicates command names. |

## Coverage Classification

| area | classification | triage | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| Docs Viewer Python service tests | generated-data contract, local-service contract, management write authority, import/export product regression | keep | Docs Viewer services | No immediate rewrite. Keep focused on service APIs and source model behavior. |
| Docs Viewer app-shell/module smokes | architecture guard, public read-only behavior, management write authority | keep | Docs Viewer frontend app | Preserve tests that assert current app context, access projection, app session domains, service-context authority, and lack of broad runtime handle bridges. |
| Docs Viewer route smokes | product regression, browser routing, public read-only behavior | rewrite | Docs Viewer frontend app | Split `docs_viewer_routes.py` if it grows further: route/history/search checks, index-panel interaction checks, and missing-doc/hash checks are separable responsibilities. |
| Docs Viewer management UI smokes | management write authority, user-visible workflow | consolidate | Docs Viewer management UI | Several retained scripts cover management modal/actions/import/move/scope/workflow surfaces. Keep current profile subset, then map unprofiled scripts to named manual or follow-up roles before adding more. |
| Studio Python service tests | product regression, generated-data contract, local write-service contract | keep | Studio service owners | Current tests mostly assert owner modules rather than route/controller internals. |
| Studio route/module smokes | route behavior, architecture guard, public read-only behavior | keep | Studio frontend route owners | Route-ready and module-level checks align with current smoke guidance. |
| Studio broad route workflow smokes | route behavior, local-service contract, environment smoke | defer | Studio route owners | Some scripts are intentionally outside default profiles. Review route by route before retiring because many need live service or mock-service setup. |
| Docs logs migration/index tests | migration compatibility, generated-data contract | defer | Studio docs/change-log workflow | Keep until the docs-log migration history is fully quiet and no active workflow depends on migration readers. |
| Catalogue media-section migration tests | migration compatibility | defer | Catalogue source model | Keep until source records no longer need migration fallback. Then rewrite as schema rejection/current-shape tests or retire. |
| Legacy hidden/viewable mutation test | migration compatibility, management write authority | keep | Docs Viewer management mutations | This guards conversion away from legacy `hidden` front matter. Retain until old source docs have been fully normalized and the mutator no longer accepts `hidden`. |
| Data Sharing legacy-operation rejection test | architecture guard | keep | Studio Data Sharing registry | This is not preserving old behavior; it asserts the retired operation names stay rejected. |

## Stale Compatibility Audit

The highest-value compatibility lesson is already represented by `docs_viewer_app_shell_modules.py`: `assert_app_boot_start_is_single_start` checks that the app handle only exposes `appShellRefs`, `initialLoadPromise`, `root`, and `routeContext`, and that broad state, composition, session, management, and route-workflow bridges are absent.

Retain that assertion as an architecture guard. It should fail if a future test helper or runtime change tries to bring back a broad `app.state`, `app.appComposition`, `app.appSession`, `loadManagementController`, `applyCurrentRoute`, `loadIndex`, or `loadDoc` bridge.

Compatibility rows that need later cleanup are narrower:

| test surface | triage | reason | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| `test_metadata_hidden_plan_writes_viewable_and_removes_legacy_hidden` | defer | Still useful while source docs may include old `hidden` front matter. | Docs Viewer management mutations | After source normalization, remove legacy input acceptance and rewrite as current `viewable` contract. |
| `test_catalogue_media_section_migration.py` | defer | Migration fallback may still protect source records. | Catalogue source model | Once records are normalized, replace migration assertions with strict current schema assertions. |
| `test_docs_logs_migration.py` | defer | Docs-log source model still owns migration/index history. | Change-log workflow | Revisit after docs-log workflow no longer reads old shapes. |
| `test_registry_rejects_legacy_operation_names` | keep | Explicit guard against retired Data Sharing operations. | Studio Data Sharing registry | No cleanup needed unless operation names are removed from documented risk. |
| route-config fallback removal checks | keep | These assert the legacy inline/root dataset fallback is gone. | Docs Viewer frontend app | Keep as current architecture guard. |

## Broad State Coupling Audit

Python tests generally target service modules, planners, source models, and route registries. The main broad-state coupling risk is in smoke scripts that build in-page JS fixtures and inspect state objects. Most of those are module-level smokes for current owner modules rather than route-controller state.

Recommended classification:

| surface | triage | reason | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| Docs Viewer app session/domain assertions | keep | They assert named domain facades and cross-domain mutation blocking. | Docs Viewer frontend app | Keep as architecture guard. |
| Docs Viewer full route smoke | rewrite | It mixes route navigation, index-panel UI, search, missing-doc, hash, and browser reload assertions. | Docs Viewer frontend app | Split when next route behavior changes. |
| Tag route shell module smoke | defer | It exercises many current tag route shell state transitions. | Analytics/tag route | Rewrite only during a tag route owner split, otherwise it is high-churn but useful regression coverage. |
| Catalogue editor route boot module smoke | keep | It verifies current shared boot/readiness helpers and lookup contracts. | Catalogue frontend route owners | No immediate change. |
| Studio app route smokes not in profiles | defer | They may be intentional local checks for routes that need service setup. | Studio app route owners | Add profile membership or retirement rationale during route-specific work. |

## Smoke Responsibility Audit

Current smoke conventions are sound: scripts suppress HTTP server access logs, use loopback ephemeral ports for module tests, use Playwright Chromium, and profile-level browser checks build into `/tmp/dlf-jekyll-build` instead of the default Jekyll destination.

Findings:

- `docs-viewer-smoke` and `studio-smoke` both run public Docs Viewer read-only and Docs HTML import module checks. This overlap is intentional today because both profiles need to guard public/manage boundaries, but it is the clearest consolidation candidate.
- `docs-viewer/tests/smoke/` contains more scripts than `docs-viewer-smoke` runs. Keep this, but add a per-script role map before expanding the default profile.
- `studio/tests/smoke/` contains many route scripts outside `studio-smoke`. Keep them as opt-in route-specific checks; avoid adding all of them to default profiles.
- Browser and localhost checks should continue to be run with elevated localhost/browser permission in Codex sessions.
- Generated payload assumptions are mostly explicit: `run_checks.py` copies public Analysis/Library docs/search payloads after temp Jekyll builds for public smoke tests.

## Output And Filesystem Noise

| surface | triage | notes |
| --- | --- | --- |
| `run_checks.py` console output | keep | Console output is concise: command index, command name, pass/fail log path, and summary path. Detailed output stays in logs. |
| `var/test-runs/` | keep | Ignored by git and correct for local run logs. |
| `.pytest_cache/` and `__pycache__/` | keep | Both are ignored by git. Current worktree had ignored bytecode directories under test trees, which should not dirty the worktree. |
| temp Python repos | keep | Python tests mostly use `tempfile.TemporaryDirectory()`. One Data Sharing adapter check uses `tempfile.mkdtemp()` and should be converted to a context-managed temp dir during a related touch. |
| Jekyll smoke destination | keep | `/tmp/dlf-jekyll-build` avoids racing a running default `_site` serve. |
| docs watcher side effects | keep | No test profile starts the docs watcher as a persistent background service. Docs profile writes generated docs/search by explicit command. |

## Quick Wins

| item | classification | triage | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| Add a smoke script role map to this inventory or the smoke docs | docs-only validation | rewrite | Testing docs | Small docs slice; list default-profile scripts, route-specific opt-ins, and manual-only scripts. |
| Convert `test_data_sharing_adapters.py` `mkdtemp()` helper to a context-managed temp dir | filesystem noise | rewrite | Studio Data Sharing tests | Tiny Python cleanup when next touching Data Sharing tests. |
| Split `docs_viewer_routes.py` by responsibility | smoke responsibility | rewrite | Docs Viewer frontend app | Do during next Docs Viewer route behavior change. |
| Document the duplicate public read-only/HTML import smoke coverage | output/profile clarity | consolidate | Testing docs | If profile runtime becomes noisy, move shared smokes behind a common profile or keep one copy in `docs-viewer-smoke` and cite it from `studio-smoke`. |
| Add runner `--list` docs note that `full` omits `docs-viewer-smoke` | profile docs clarity | rewrite | Run Checks docs | Prevent users from assuming `full` includes every named smoke profile. |

## Deferred Rewrites

| item | status | reason |
| --- | --- | --- |
| Retire legacy `hidden` input handling | deferred | Needs source normalization and management mutator contract change. |
| Retire catalogue media-section migration tests | deferred | Needs confirmation that all source records use current media section schema. |
| Retire docs-log migration tests | deferred | Needs change-log workflow confirmation that old shapes are no longer read. |
| Prune unprofiled Studio route smokes | deferred | Requires route-by-route ownership review to avoid losing valuable local-only checks. |
| Merge smoke profiles | deferred | Current duplication is small and keeps profile intent clear. Revisit only if runtime/noise becomes a concrete problem. |

## Verification

This pass changed documentation only and did not modify test code, runner logic, or smoke helpers.

Checks run:

- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --list`
- `git diff --check`
- focused changed-doc sanitization scan for local absolute paths and sensitive terms

No test, runner, or smoke-helper verification was run because this pass only changed source documentation.
