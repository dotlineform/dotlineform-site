---
doc_id: testing
title: Testing
added_date: 2026-05-01
last_updated: 2026-06-03
parent_id: ""
---
# Testing

This repo uses lightweight, opt-in checks rather than a mandatory full test suite.

The goal is to give Codex a standard place to put repeatable checks, run logs, and verification notes when a change is too broad for manual review alone.
The current Python checks are pytest-collected scripts under `studio/tests/python/`.
They use ordinary `assert` statements and are run by `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` through pytest.
Tests, checks, smoke helpers, and public-surface audits are Studio/Codex development infrastructure even when they validate public generated output.
See [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) for the maintained repo ownership boundary.

## When To Use Automated Checks

Run automated checks when the blast radius is large enough that manual checks are likely to miss something.

Good candidates:

- build planners and artifact selection
- schema or config contracts
- generated docs/search payloads
- source-data validation
- local write-server behavior
- Studio route behavior that can be smoke-tested reliably

Manual checks are still enough for small copy changes, narrow docs edits, and visual judgment that depends on feel, layout, or mobile ergonomics.

## Structure

- `studio/tests/python/`
  Deterministic Python checks. Files expose `test_*` functions for pytest collection; many can also run directly as scripts.
- `studio/tests/smoke/`
  Focused browser smoke scripts for Studio-owned route and module behavior.
- `docs-viewer/tests/python/`
  Deterministic Docs Viewer service, source-model, generated-read, management, import/export, rebuild, and activity checks.
- `docs-viewer/tests/smoke/`
  Playwright scripts for Docs Viewer public read-only behavior, management UI, browser modules, and the standalone service manage shell.
- `studio/tests/fixtures/`
  Small stable fixtures, only where existing repo data is not safe or sufficient.
- `var/test-runs/`
  Local check logs and summaries. This path is ignored by git.

## Ownership Boundaries

Tests should assert current owner contracts, not preserve historical compatibility surfaces.

Useful compatibility lessons should become explicit architecture guards when they protect the current design.
For example, Docs Viewer app-shell smokes may assert that the public runtime handle does not expose broad state, composition, session, management, or route-workflow bridges.
That is a current architecture guard, not a reason to keep old runtime APIs.

Config cleanup can leave durable tests when the surface matters.
Prefer positive owner-contract assertions such as:

- runtime config exposes only the current browser-facing data-path key set
- public config endpoints return whitelisted UI-needed fields, not source-write paths or adapter internals
- generated-default, route-registry, or activity-contract verifiers still run through pytest collection

Avoid permanent tests that only name every retired key.
If a retired-key assertion remains, pair it with the positive owner contract it protects, such as the allowed route surface, allowed browser payload shape, or server-only write boundary.

Retire or rewrite tests when the behavior they cover is obsolete, duplicated, or better expressed through a focused owner module.
Examples of current retired shapes include the old Docs visibility source input, Docs Viewer Markdown changelog migration, and catalogue media-section migration runners.

Keep Studio and Docs Viewer smoke responsibilities separate:

- `docs-viewer-smoke` owns Docs Viewer public read-only, management UI, browser-module, and standalone service checks.
- `studio-smoke` owns Studio browser workflows, UI Catalogue, Studio route/module checks, and data-sharing route checks.
- `studio-smoke` should not run Docs Viewer-owned smoke scripts.

## Runner

Use `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` to run one or more check profiles and write a local run summary.

Examples:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile catalogue
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile studio-smoke
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile full
```

Profiles are intentionally coarse. Choose the smallest profile that matches the risk.
The `docs` profile includes Docs Viewer-owned pytest checks from `docs-viewer/tests/python/` plus shared Data Sharing adapter checks that remain under `studio/tests/python/`.
The `docs-viewer-smoke` profile builds a temporary Jekyll site and runs Docs Viewer smoke checks from `docs-viewer/tests/smoke/`.
Run `docs-viewer-smoke`, or at minimum `public_docs_viewer_readonly.py` against a fresh temporary Jekyll build, when a Docs Viewer change touches the shared public runtime, route shell, public config, or management-only module boundary.
Do not use the repo root or a stale `_site` directory as evidence for public read-only behavior; those targets can mask public-build exclusions.
The `studio-smoke` profile builds a temporary Jekyll site and runs retained browser smoke scripts such as the UI Catalogue modal demo and data import route checks.
Those checks cover Studio-owned browser workflows, including the docs-management-unavailable state and a mocked Library import preview flow, but do not run Docs Viewer-owned smoke scripts.
The `full` profile runs `quick`, `catalogue`, `docs`, and `studio-smoke`; it does not include `docs-viewer-smoke`.
Smoke profiles clean `/tmp/dlf-jekyll-build` before and after the run by default.
Use `--keep-temp-build` only when inspecting the generated temp build after a failure.

## Smoke Roles

Default Docs Viewer smoke coverage:

| script | profile role | responsibility |
| --- | --- | --- |
| `docs_viewer_service_manage.py` | `docs-viewer-smoke` | Standalone Docs Viewer service manage shell and API base. |
| `public_docs_viewer_readonly.py` | `docs-viewer-smoke` | Public Library and Analysis installs stay read-only. |
| `docs_viewer_index_panel_modules.py` | `docs-viewer-smoke` | Index-panel state, persistence, and projection helper contracts. |
| `docs_viewer_management_modal.py` | `docs-viewer-smoke` | Management modal semantics, action rows, focus behavior, and mobile sizing. |
| `docs_viewer_management_action_workflow_modules.py` | `docs-viewer-smoke` | Management action choices, payloads, and viewability target shaping. |
| `docs_html_import_modules.py` | `docs-viewer-smoke` | HTML import preview, replacement, write-failure fallback, and result rendering modules. |

Focused Docs Viewer route smokes are opt-in unless a route-specific change needs them:

| script | responsibility |
| --- | --- |
| `docs_viewer_route_navigation.py` | Route navigation, internal links, history, and Library route path behavior. |
| `docs_viewer_route_index_panel.py` | Index-panel collapse, expand, restore, and expanded tree navigation behavior. |
| `docs_viewer_route_search_missing_hash.py` | Search-route state, missing-doc routing, history recovery, and hash-target behavior. |
| `docs_viewer_routes.py` | Aggregate wrapper for the focused route smoke slices. |

Focused route smokes need a target that serves `/docs/`.
Temporary public Jekyll builds can omit that route while still serving public `/library/` and `/analysis/` pages.

Studio route smoke scripts outside `studio-smoke` should stay opt-in until a route owner reviews setup requirements.
Do not add all unprofiled Studio route smokes to default profiles just to increase coverage.

## Python Test Style

Python tests should stay small, deterministic, and local.
Prefer direct module tests over broad end-to-end setup unless the integration boundary is the behavior being tested.

Current conventions:

- keep tests in `studio/tests/python/test_<area>.py`
- use plain `assert`
- run grouped profile checks through `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py`, which calls the same interpreter with `-m pytest -q`
- avoid network access
- use temporary directories or small fixtures when repo data would make the test brittle
- keep direct script execution working where practical for narrow opt-in checks
- when a direct verifier script belongs in `run_checks.py` or pytest, wrap it with a real `test_*` function so pytest collection cannot silently skip it
- add the test file to the smallest relevant pytest command in `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` when it covers a repeated risk

See [Pytest](/docs/?scope=studio&doc=testing-pytest) for focused command examples and local install notes.

## Expected Close-Out

When Codex runs checks, the final response should report:

- which profiles ran
- pass/fail status
- the `var/test-runs/.../summary.md` path
- any failed command log paths
- manual checks still needed

Example:

```text
Automated checks:
- quick: pass
- catalogue: pass

Logs:
- var/test-runs/20260501-171530/summary.md

Manual checks:
- Open /studio/catalogue-field-registry/
- Search downloads
- Clear search
```

## Current Scope

The MVP framework is deliberately small:

- pytest is the Python test collection layer, but `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` remains the top-level runner
- no CI contract
- no automatic full-suite run before every change
- no broad fixture duplication

Add a new check only when it captures repeatable risk that would otherwise be hard to verify.
