---
doc_id: testing
title: Testing
added_date: 2026-05-01
last_updated: 2026-06-06
parent_id: ""
---
# Testing

This repo uses lightweight, opt-in checks rather than a mandatory full test suite.

The goal is to give Codex a standard place to put repeatable checks, run logs, and verification notes when a change is too broad for manual review alone.
The current Python checks are pytest-collected scripts under the owning app test directories.
They use ordinary `assert` statements and are run by `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` through pytest.
Tests, checks, smoke helpers, and public-surface audits are Admin/Codex development infrastructure when they span app boundaries.
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
  Deterministic Studio catalogue and public-site checks. Files expose `test_*` functions for pytest collection; many can also run directly as scripts.
- `studio/tests/smoke/`
  Focused browser smoke scripts for Studio-owned route and module behavior.
- `admin-app/tests/python/`
  Admin server, runner, risk/audit/check, and Admin-hosted UI Catalogue checks.
- `admin-app/tests/smoke/`
  Admin home, operational route, and Admin-hosted UI Catalogue smoke scripts.
- `analytics-app/tests/python/`
  Analytics server, tag, and Data Sharing checks.
- `docs-viewer/tests/python/`
  Deterministic Docs Viewer service, source-model, generated-read, management, import/export, rebuild, and activity checks.
- `docs-viewer/tests/smoke/`
  Playwright scripts for Docs Viewer public read-only behavior, management UI, browser modules, and the standalone service manage shell.
- `docs-viewer/tests/fixtures/`
  Small stable fixtures, only where existing repo data is not safe or sufficient.
- `var/admin/test-runs/`
  Local check logs and summaries. This path is ignored by git.

Fixtures should live with the owner that uses them.
`studio/tests/fixtures/` is not a shared fixture bucket for Admin, Analytics, Docs Viewer, UI Catalogue, or repo-scope checks.

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
- `admin-smoke` owns Admin home and Admin operational route checks.
- `studio-smoke` owns Studio browser workflows and Studio catalogue/public-site route/module checks.
- `ui-catalogue-smoke` owns Admin-hosted UI Catalogue route and demo checks.
- `studio-smoke` should not run Docs Viewer-owned smoke scripts.

## Runner

Use `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` to run one or more check profiles and write a local run summary.

Examples:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile catalogue
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs-viewer-smoke
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile studio-smoke
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile full
```

Profiles are intentionally coarse. Choose the smallest profile that matches the risk.
The `docs` profile includes Docs Viewer-owned pytest checks from `docs-viewer/tests/python/` plus Analytics-owned Data Sharing adapter checks.
The `docs-viewer-smoke` profile builds a temporary Jekyll site and runs Docs Viewer smoke checks from `docs-viewer/tests/smoke/`.
Run `docs-viewer-smoke`, or at minimum `public_docs_viewer_readonly.py` against a fresh temporary Jekyll build, when a Docs Viewer change touches the shared public runtime, route shell, public config, public payload-loading contract, or management-only module boundary.
Do not use the repo root or a stale `_site` directory as evidence for public read-only behavior; those targets can mask public-build exclusions.
The `studio-smoke` profile builds a temporary Jekyll site and runs retained browser smoke scripts for Studio catalogue/public-site behavior.
The `admin-smoke` profile runs Admin route smoke checks without the Jekyll temp build.
The `full` profile runs `quick`, `catalogue`, `docs`, `admin-smoke`, and `studio-smoke`; it does not include `docs-viewer-smoke`.
Smoke profiles clean `/tmp/dlf-jekyll-build` before and after the run by default.
Use `--keep-temp-build` only when inspecting the generated temp build after a failure.

## Smoke Roles

Default Docs Viewer smoke coverage:

| script | profile role | responsibility |
| --- | --- | --- |
| `docs_viewer_service_manage.py` | `docs-viewer-smoke` | Standalone Docs Viewer service manage shell, generated tree/recent/by-id/search reads, rich manage info-panel metadata, and representative management API base. |
| `public_docs_viewer_readonly.py` | `docs-viewer-smoke` | Public Library and Analysis installs stay read-only, load public tree/recent/by-id/search payloads, hydrate public info-panel metadata from by-id payloads, and do not request public docs `index.json`. |

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

- keep tests in the owning app test directory, such as `studio/tests/python/`, `admin-app/tests/python/`, `analytics-app/tests/python/`, or `docs-viewer/tests/python/`
- use plain `assert`
- run grouped profile checks through `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py`, which calls the same interpreter with `-m pytest -q`
- avoid network access
- use temporary directories or small fixtures when repo data would make the test brittle
- keep direct script execution working where practical for narrow opt-in checks
- when a direct verifier script belongs in `run_checks.py` or pytest, wrap it with a real `test_*` function so pytest collection cannot silently skip it
- add the test file to the smallest relevant pytest command in `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` when it covers a repeated risk

See [Pytest](/docs/?scope=studio&doc=testing-pytest) for focused command examples and local install notes.
See [Local Admin App](/docs/?scope=studio&doc=local-admin-app) for Admin route, API, output-path, and UI Catalogue ownership.

## Expected Close-Out

When Codex runs checks, the final response should report:

- which profiles ran
- pass/fail status
- the `var/admin/test-runs/.../summary.md` path
- any failed command log paths
- manual checks still needed

Example:

```text
Automated checks:
- quick: pass
- catalogue: pass

Logs:
- var/admin/test-runs/20260501-171530/summary.md

Manual checks:
- Open /studio/catalogue-field-registry/
- Search downloads
- Clear search
```

## Current Scope

The MVP framework is deliberately small:

- pytest is the Python test collection layer, but `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` remains the top-level runner
- no CI contract
- no automatic full-suite run before every change
- no broad fixture duplication

Add a new check only when it captures repeatable risk that would otherwise be hard to verify.
