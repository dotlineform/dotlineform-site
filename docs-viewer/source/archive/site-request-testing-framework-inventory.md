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
This document is archived and is no longer maintained.

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
| `studio-smoke` profile | Studio browser smoke, route shell, module contracts | keep | Studio-owned smoke profile. Docs Viewer-owned public read-only and HTML import module checks belong only to `docs-viewer-smoke`. |
| `full` profile | broad local verification | keep | Still matches the opt-in model because it expands `quick`, `catalogue`, `docs`, and `studio-smoke`. It does not include `docs-viewer-smoke`; Docs Viewer browser behavior is checked explicitly through that profile. |

## Coverage Classification

| area | classification | triage | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| Docs Viewer Python service tests | generated-data contract, local-service contract, management write authority, import/export product regression | keep | Docs Viewer services | No immediate rewrite. Keep focused on service APIs and source model behavior. |
| Docs Viewer app-shell/module smokes | architecture guard, public read-only behavior, management write authority | keep | Docs Viewer frontend app | Preserve tests that assert current app context, access projection, app session domains, service-context authority, and lack of broad runtime handle bridges. |
| Docs Viewer route smokes | product regression, browser routing, public read-only behavior | keep | Docs Viewer frontend app | Split into focused route navigation, index-panel, and search/missing/hash entrypoints, with `docs_viewer_routes.py` kept as an aggregate wrapper. |
| Docs Viewer management UI smokes | management write authority, user-visible workflow | consolidate | Docs Viewer management UI | Several retained scripts cover management modal/actions/import/move/scope/workflow surfaces. Keep current profile subset, then map extra entrypoints to named focused roles before adding more profile coverage. |
| Studio Python service tests | product regression, generated-data contract, local write-service contract | keep | Studio service owners | Current tests mostly assert owner modules rather than route/controller internals. |
| Studio route/module smokes | route behavior, architecture guard, public read-only behavior | keep | Studio frontend route owners | Route-ready and module-level checks align with current smoke guidance. |
| Studio broad route workflow smokes | route behavior, local-service contract, environment smoke | defer | Studio route owners | Some scripts are intentionally outside default profiles. Review route by route before retiring because many need live service or mock-service setup. |
| Docs logs index tests | generated-data contract | keep | Studio docs/change-log workflow | Keep current structured docs-log index coverage for per-entry JSON records and generated indexes. |
| Catalogue media-section schema tests | generated-data contract, source schema guard | keep | Catalogue source model | Keep current target-schema checks that match Studio-surfaced media-section fields. Retire old migration-planner test coverage. |
| Docs Viewer viewability mutation tests | management write authority, source schema guard | keep | Docs Viewer management mutations | Current tests assert `viewable` writes; `hidden` is no longer a source or mutator input. |
| Data Sharing legacy-operation rejection test | architecture guard | keep | Studio Data Sharing registry | This is not preserving old behavior; it asserts the retired operation names stay rejected. |

## Stale Compatibility Audit

The highest-value compatibility lesson is already represented by `docs_viewer_app_shell_modules.py`: `assert_app_boot_start_is_single_start` checks that the app handle only exposes `appShellRefs`, `initialLoadPromise`, `root`, and `routeContext`, and that broad state, composition, session, management, and route-workflow bridges are absent.

Retain that assertion as an architecture guard. It should fail if a future test helper or runtime change tries to bring back a broad `app.state`, `app.appComposition`, `app.appSession`, `loadManagementController`, `applyCurrentRoute`, `loadIndex`, or `loadDoc` bridge.

Compatibility rows that need later cleanup are narrower:

| test surface | triage | reason | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| `test_metadata_viewable_plan_writes_current_viewability` | keep | Current source docs and management mutations use `viewable`; `hidden` is no longer a named input path. | Docs Viewer management mutations | No compatibility cleanup remains for this test. |
| `test_catalogue_media_section_migration.py` | retire | The media-section migration is old history; current source behavior is the target schema surfaced in Studio. | Catalogue source model | Removed the migration test file; keep `test_catalogue_source_media_section_schema.py` for current schema coverage. |
| `test_docs_logs_migration.py` | retire | The old Docs Viewer Markdown changelog docs are gone and the migration path is no longer part of current workflow coverage. | Change-log workflow | Removed the legacy migration test file; keep current structured docs-log index tests. |
| `test_registry_rejects_legacy_operation_names` | keep | Explicit guard against retired Data Sharing operations. | Studio Data Sharing registry | No cleanup needed unless operation names are removed from documented risk. |
| route-config fallback removal checks | keep | These assert the legacy inline/root dataset fallback is gone. | Docs Viewer frontend app | Keep as current architecture guard. |

## Broad State Coupling Audit

Python tests generally target service modules, planners, source models, and route registries. The main broad-state coupling risk is in smoke scripts that build in-page JS fixtures and inspect state objects. Most of those are module-level smokes for current owner modules rather than route-controller state.

Recommended classification:

| surface | triage | reason | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| Docs Viewer app session/domain assertions | keep | They assert named domain facades and cross-domain mutation blocking. | Docs Viewer frontend app | Keep as architecture guard. |
| Docs Viewer route smoke slices | keep | The former broad route smoke now has focused navigation, index-panel, and search/missing/hash entrypoints. | Docs Viewer frontend app | Keep the aggregate wrapper only for compatibility with existing references. |
| Tag route shell module smoke | defer | It exercises many current tag route shell state transitions. | Analytics/tag route | Rewrite only during a tag route owner split, otherwise it is high-churn but useful regression coverage. |
| Catalogue editor route boot module smoke | keep | It verifies current shared boot/readiness helpers and lookup contracts. | Catalogue frontend route owners | No immediate change. |
| Studio app route smokes not in profiles | defer | They may be intentional local checks for routes that need service setup. | Studio app route owners | Add profile membership or retirement rationale during route-specific work. |

## Smoke Responsibility Audit

Current smoke conventions are sound: scripts suppress HTTP server access logs, use loopback ephemeral ports for module tests, use Playwright Chromium, and profile-level browser checks build into `/tmp/dlf-jekyll-build` instead of the default Jekyll destination.

Findings:

- `studio-smoke` should not run Docs Viewer-owned smoke scripts. Public Docs Viewer read-only and Docs HTML import module checks are owned by `docs-viewer-smoke`.
- `docs-viewer/tests/smoke/` contains more scripts than `docs-viewer-smoke` runs. Keep this, but use the role map below before expanding the default profile.
- `studio/tests/smoke/` contains many route scripts outside `studio-smoke`. Keep them as opt-in route-specific checks; avoid adding all of them to default profiles.
- Browser and localhost checks should continue to be run with elevated localhost/browser permission in Codex sessions.
- Generated payload assumptions are mostly explicit: `run_checks.py` copies public Analysis/Library docs/search payloads after temp Jekyll builds for public smoke tests.

Docs Viewer smoke role map:

| script | profile role | focused responsibility |
| --- | --- | --- |
| `docs_viewer_service_manage.py` | `docs-viewer-smoke` | Standalone Docs Viewer service manage shell and API base. |
| `public_docs_viewer_readonly.py` | `docs-viewer-smoke` | Public Library and Analysis installs stay read-only. |
| `docs_viewer_index_panel_modules.py` | `docs-viewer-smoke` | Index-panel state, persistence migration, and projection helper contracts. |
| `docs_viewer_management_modal.py` | `docs-viewer-smoke` | Management modal semantics, action rows, focus behavior, and mobile sizing. |
| `docs_viewer_management_action_workflow_modules.py` | `docs-viewer-smoke` | Management action choices, payloads, and viewability target shaping. |
| `docs_html_import_modules.py` | `docs-viewer-smoke` | HTML import preview, replacement, write-failure fallback, and result rendering modules. |
| `docs_viewer_route_navigation.py` | focused opt-in | Route navigation, internal links, history, and Library route path behavior. |
| `docs_viewer_route_index_panel.py` | focused opt-in | Index-panel collapse/expand/restore behavior and expanded tree navigation. |
| `docs_viewer_route_search_missing_hash.py` | focused opt-in | Search-route state, missing-doc routing, history recovery, and hash-target behavior. |
| `docs_viewer_routes.py` | focused opt-in aggregate | Compatibility wrapper that runs the focused route smoke slices together. |

The focused route entrypoints need a target that serves `/docs/`. Temporary public Jekyll builds can omit that route while still serving public `/library/` and `/analysis/` pages.

## Output And Filesystem Noise

| surface | triage | notes |
| --- | --- | --- |
| `run_checks.py` console output | keep | Console output is concise: command index, command name, pass/fail log path, and summary path. Detailed output stays in logs. |
| `var/test-runs/` | keep | Ignored by git and correct for local run logs. |
| `.pytest_cache/` and `__pycache__/` | keep | Both are ignored by git. Current worktree had ignored bytecode directories under test trees, which should not dirty the worktree. |
| temp Python repos | keep | Python tests mostly use `tempfile.TemporaryDirectory()`. One Data Sharing adapter check uses `tempfile.mkdtemp()` and should be converted to a context-managed temp dir during a related touch. |
| Jekyll smoke destination | keep | `/tmp/dlf-jekyll-build` avoids racing a running default `_site` serve. `run_checks.py` now removes any existing temp build before `jekyll-temp-build` and removes the temp build again after smoke profiles finish unless `--keep-temp-build` is passed. |
| docs watcher side effects | keep | No test profile starts the docs watcher as a persistent background service. Docs profile writes generated docs/search by explicit command. |

## Quick Wins

| item | classification | triage | owner | follow-up slice |
| --- | --- | --- | --- | --- |
| Add a smoke script role map to this inventory or the smoke docs | docs-only validation | done | Testing docs | Added a Docs Viewer smoke role map that separates `docs-viewer-smoke` profile coverage from focused opt-in route entrypoints. |
| Convert `test_data_sharing_adapters.py` `mkdtemp()` helper to a context-managed temp dir | filesystem noise | done | Studio Data Sharing tests | Replaced the leaking `mkdtemp()` helper with a context-managed temporary registry repo. |
| Split `docs_viewer_routes.py` by responsibility | smoke responsibility | done | Docs Viewer frontend app | Added focused route navigation, index-panel, and search/missing/hash smoke entrypoints; kept `docs_viewer_routes.py` as an aggregate wrapper. |
| Keep Docs Viewer-owned smoke checks out of `studio-smoke` | output/profile clarity | done | Testing docs | `studio-smoke` now runs Studio-owned smoke checks only; Docs Viewer public read-only and HTML import module checks remain in `docs-viewer-smoke`. |
| Add runner `--list` docs note that `full` omits `docs-viewer-smoke` | profile docs clarity | done | Run Checks docs | Documented that `full` runs `quick`, `catalogue`, `docs`, and `studio-smoke`, and that `docs-viewer-smoke` must be run explicitly for Docs Viewer browser behavior. |

## Deferred Rewrites

| item | status | reason |
| --- | --- | --- |
| Retire legacy `hidden` input handling | done | Source docs use `viewable`; source readers, builders, and management mutators no longer read `hidden` as an input. |
| Retire catalogue media-section migration tests and runner | done | Removed the old media-section migration test and one-time runner because current behavior is the Studio-surfaced target schema. |
| Retire docs-log migration tests | done | Removed the legacy Docs Viewer changelog migration tests because old Markdown changelog docs are no longer current workflow inputs. |
| Prune unprofiled Studio route smokes | deferred | Requires route-by-route ownership review to avoid losing valuable local-only checks. |
| Merge smoke profiles | deferred | Not needed for current ownership. Keep Docs Viewer and Studio smoke profiles separate unless a future common smoke ownership surface is introduced. |

## Verification

This pass includes runner and test cleanup: `studio-smoke` no longer runs Docs Viewer-owned smoke scripts, Docs Viewer route smokes have focused entrypoints, Data Sharing adapter tests use context-managed temp repos, legacy Docs Viewer changelog migration tests and old catalogue media-section migration tests were retired, the one-time catalogue media-section migration runner was removed, and smoke-profile Jekyll temp builds clean up by default.

Checks run:

- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --list`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/commands/run_checks.py`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/tests/python/test_data_sharing_adapters.py docs-viewer/tests/smoke/docs_viewer_route_smoke_helpers.py docs-viewer/tests/smoke/docs_viewer_routes.py docs-viewer/tests/smoke/docs_viewer_route_navigation.py docs-viewer/tests/smoke/docs_viewer_route_index_panel.py docs-viewer/tests/smoke/docs_viewer_route_search_missing_hash.py`
- `$HOME/miniconda3/bin/python3 -m pytest -q studio/tests/python/test_data_sharing_adapters.py`
- `$HOME/miniconda3/bin/python3 -m pytest -q docs-viewer/tests/python/test_docs_management_mutations.py docs-viewer/tests/python/test_docs_source_model.py docs-viewer/tests/python/test_docs_import.py docs-viewer/tests/python/test_docs_import_service.py docs-viewer/tests/python/test_docs_management_service.py`
- `$HOME/miniconda3/bin/python3 -m pytest -q studio/tests/python/test_docs_logs_indexes.py`
- `$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_source_media_section_schema.py`
- `$HOME/miniconda3/bin/python3 studio/tests/python/test_data_sharing_adapters.py`
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/python/test_docs_management_mutations.py`
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/python/test_docs_source_model.py`
- `$HOME/.rbenv/shims/ruby -c docs-viewer/build/build_docs.rb`
- created a small `/tmp/dlf-jekyll-build` sentinel and verified `run_checks.clean_jekyll_destination()` removed it
- `git diff --check`
- generated docs JSON parse check
- current docs source scan found no `hidden:` front matter
- focused changed-doc sanitization scan for local absolute paths and sensitive terms
- removed existing `/tmp/dlf-jekyll-build` and `/tmp/dlf-jekyll-build-stsr-012` directories, then confirmed both paths no longer exist

A focused route browser smoke was attempted against `/tmp/dlf-jekyll-build`, but that temporary public build did not include `/docs/`, so the route smoke target was invalid. No full browser smoke profile was run.
