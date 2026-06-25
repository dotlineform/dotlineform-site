---
doc_id: testing
title: Testing
added_date: 2026-05-01
last_updated: 2026-06-25
parent_id: ""
---
# Testing

Use this page to choose practical verification for a change request.

The repo uses lightweight, opt-in checks rather than a mandatory full test suite. The standard runner is:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick
```

Choose the smallest profile or focused command that gives evidence for the risk you changed. Do not run broad profiles just to produce more output.

## Test Policy

Permanent automated tests should protect data flows, server responses, generated contracts, parser behavior, ownership boundaries, and route/module integration points.

Do not add or expand permanent tests just to prove UI choreography: modal timing, button placement, cursor changes, hover state, focus movement, labels, copy tone, layout, and ordinary user click paths are better covered by manual or temporary in-app verification. If a UI change exposes a real product contract, test the underlying server response, request payload, generated data shape, or shared component contract instead of the full screen workflow.

Browser smoke checks are allowed when the durable risk is route boot, module wiring, public/private asset boundaries, local API reachability, request/response agreement, or a shared ready/busy contract. Existing UI-heavy smoke scripts are legacy cleanup targets; do not extend them for routine UI work.

## What To Run

Use this as the first-pass decision table.

| change area | usual evidence |
| --- | --- |
| narrow docs copy | manual read-through, then `git diff --check` |
| generated Studio docs/search contracts | `--profile docs` or focused docs builder/tests |
| Docs Viewer services, config, or generated data | `--profile docs` or focused `docs-viewer/tests/python/...` |
| Docs Viewer public runtime or management route boundary | focused route/module smoke only when boot, public/private assets, payload reads, or local API reachability changed |
| catalogue source, build, or publication behavior | `--profile catalogue`, focused `studio/tests/python/...`, or a narrow catalogue build preview |
| Admin app checks, reports, risk, or operations pages | focused `admin-app/tests/python/...`; add `--profile admin-smoke` only for route boot or API reachability |
| Analytics tags or data sharing | focused `analytics-app/tests/python/...`; add `--profile analytics-smoke` only for route/API boundaries |
| public site or Studio-owned route behavior | `--profile studio-smoke` or a focused script under `studio/tests/smoke/` when the public route contract changed |
| shared server, config, runner, or ownership boundary | `--profile quick`, then add owner-specific focused checks |

Manual checks are still expected when the behavior depends on layout judgment, pointer feel, mobile ergonomics, or copy tone.

## Runner Profiles

`admin-app/commands/run_checks.py` writes logs under `var/admin/test-runs/` and prints the summary path.

Common profiles:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile catalogue
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs-viewer-smoke
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile admin-smoke
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile analytics-smoke
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile studio-smoke
```

Profile roles:

| profile | role |
| --- | --- |
| `quick` | whitespace, Python syntax, core pytest checks, projection contract, Studio ready-state audit, and key JSON parsing. |
| `catalogue` | focused catalogue pytest checks plus a narrow field-aware build preview. |
| `docs` | Docs Viewer pytest checks, Analytics Data Sharing adapter checks, and Studio docs/search rebuilds. |
| `docs-viewer-smoke` | `site/` validation plus Docs Viewer public read-only and standalone manage-service smoke checks. |
| `admin-smoke` | local Admin home and operations route smoke checks. |
| `analytics-smoke` | local Analytics tag APIs, route shells, ready-state, and Data Sharing route/API boundary smoke checks. |
| `studio-smoke` | `site/` validation plus public-site and Studio-owned catalogue smoke checks. |
| `full` | runs `quick`, `catalogue`, `docs`, `admin-smoke`, and `studio-smoke`; it does not include `docs-viewer-smoke` or `analytics-smoke`. |

Smoke profiles that need public-site files validate and read the checked-in `site/` root.

## App Ownership

Keep checks with the app that owns the behavior.

Docs Viewer:

- Python checks: `docs-viewer/tests/python/`
- Browser smoke checks: `docs-viewer/tests/smoke/`
- Fixtures: `docs-viewer/tests/fixtures/`
- Typical profiles: `docs`, `docs-viewer-smoke`
- Use `docs-viewer-smoke`, or at least `public_docs_viewer_readonly.py` against `site/`, when a change touches the public runtime, route shell, public config, payload-loading contract, or management-only module boundary.

Admin app:

- Python checks: `admin-app/tests/python/`
- Browser smoke checks: `admin-app/tests/smoke/`
- Typical profiles: `quick`, `admin-smoke`

Analytics app:

- Python checks: `analytics-app/tests/python/`
- Browser and API smoke checks: `analytics-app/tests/smoke/`
- Typical profiles: `quick`, `docs` for Data Sharing adapter coverage, `analytics-smoke`
- Tag management now belongs to Analytics. New Analytics checks should not use `tagStudio` naming.

Studio and public site:

- Python checks: `studio/tests/python/`
- Browser smoke checks: `studio/tests/smoke/`
- Typical profiles: `quick`, `catalogue`, `studio-smoke`
- Studio-owned smokes cover public-site behavior and retained catalogue/public-route behavior. They should not absorb Docs Viewer, Admin, or Analytics smoke responsibilities.

Cross-app checks:

- Runner, audit, risk, activity, and inventory checks live under `admin-app/` when they are development infrastructure rather than product behavior.
- See [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) for the maintained ownership boundary.

## Browser Smoke Testing

Browser smokes are useful when code changes affect route loading, module wiring, local services, public payload reads, public/private asset boundaries, or shared ready/busy state.

They should not be expanded to prove routine modal behavior or other UI choreography. Use manual verification, temporary scripts, or shared component tests for that work, and keep permanent checks focused on durable route and data contracts.

Do not use a raw `file://` URL for routes that depend on module imports, same-origin asset paths, or local APIs. Use a running local app, the checked-in `site/` root through a static server, or the route-specific setup expected by the smoke script.

See [Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing) for Playwright readiness, click, setup, and manual-check guidance.

## Python Test Style

Python checks should stay small, deterministic, and local.

Current conventions:

- keep tests under the owning app test directory
- use plain `assert`
- prefer direct module tests over broad end-to-end setup unless the integration boundary is the behavior being tested
- test server responses, request payloads, and data transformations before browser-visible UI outcomes
- run grouped checks through `admin-app/commands/run_checks.py`, which invokes pytest with the same Python interpreter
- run focused checks with `$HOME/miniconda3/bin/python3 -m pytest <test-path>`
- avoid network access
- use temporary directories or small fixtures when repo data would make the test brittle
- keep direct script execution working where practical for narrow opt-in checks
- wrap reusable verifier scripts with real `test_*` functions so pytest collection cannot silently skip them
- add the test to the smallest relevant runner profile when it protects a repeated risk

See [Pytest](/docs/?scope=studio&doc=testing-pytest) for focused command examples and local install notes.

## Close-Out

When Codex runs checks, the final response should report:

- which profiles or focused commands ran
- pass/fail status
- the `var/admin/test-runs/.../summary.md` path when `run_checks.py` was used
- any failed command log paths
- manual checks still needed

Example:

```text
Automated checks:
- quick: pass
- catalogue: pass

Logs:
- var/admin/test-runs/20260610-171530/summary.md

Manual checks:
- Open /studio/catalogue-field-registry/
- Search downloads
- Clear search
```

## Current Gaps

The testing framework is intentionally incomplete.

Known gaps:

- there is no CI contract
- there is no automatic full-suite run before every change
- several smoke scripts are still opt-in because their setup requirements need owner review
- profile names still preserve some historical Studio terminology
- cross-app route coverage is uneven
- not every route exposes the same ready/busy contract
- several legacy smoke scripts still test UI choreography and should be pruned or split toward API/module coverage

Treat these gaps as work to plan, not as permission to make new tests vague. Add a check only when it captures repeatable risk that would otherwise be hard to verify.
