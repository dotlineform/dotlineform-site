---
doc_id: risk-runtime-browser-evidence-plan
title: Risk Runtime Browser Evidence - Plan
added_date: 2026-05-31
last_updated: 2026-06-07
ui_status: draft
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Runtime Browser Evidence - Plan

This document defines how runtime, Playwright, browser-devtools, and Lighthouse evidence should enter the [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack).

## Current Status

Status: partially implemented.

Implemented:

- `admin-app/checks/risk_evidence_pack.py --include-runtime`
- allowlisted `admin-app/commands/run_checks.py` profiles through `--runtime-profile`
- `runtime-checks.json` summary records with profile names, exit codes, and linked `var/admin/test-runs/.../summary.md` paths

Not done:

- Lighthouse execution
- browser performance trace capture
- browser console/network/performance summaries outside existing smoke profiles
- named browser target configuration

## Evidence Types

| Evidence type | Use when | Current owner | Artifact |
| --- | --- | --- | --- |
| Run-check profile | The question is whether an existing app smoke/check profile passes. | `admin-app/commands/run_checks.py` | `runtime-checks.json` plus `var/admin/test-runs/<run-id>/summary.md` |
| Focused Playwright smoke | The question needs route boot, UI state, module import, or browser interaction evidence. | Existing smoke scripts under app test roots | Linked from run-check profile output or future targeted runtime producer |
| Browser console/network summary | The question is about runtime errors, failed assets, request count, or payload size. | Future browser target producer | `runtime-checks.json` and optional `artifacts/browser/<target>/` |
| Lighthouse | The question is public-route performance, accessibility, best-practices, SEO, layout shift, or load cost. | Future Lighthouse producer | `runtime-checks.json` and `artifacts/lighthouse/<target>/` |
| Manual browser-devtools note | The question needs judgement from a human inspection. | Subjective notes producer | `subjective-notes.jsonl` |

## Lighthouse Integration Contract

Lighthouse must not run against arbitrary browser-provided URLs. Before implementation, define an allowlisted target contract.

Recommended target config shape:

```json
{
  "target_id": "public-catalogue-search",
  "app": "public-site",
  "url_path": "/catalogue/search/",
  "server_mode": "public-preview-or-temp-static",
  "categories": ["performance", "accessibility", "best-practices", "seo"],
  "form_factor": "desktop",
  "required_services": [],
  "budgets": {
    "performance_min": 0.8,
    "accessibility_min": 0.9
  }
}
```

Implementation rules:

- target ids are checked into repo config, not supplied as raw URLs from the browser
- the Python producer resolves the URL server-side from a named target and known local server mode
- the browser UI may request a target id and category set only from the allowlist
- reports write under `var/admin/risk/runs/<run-id>/artifacts/lighthouse/<target-id>/`
- machine-readable Lighthouse JSON is the primary artifact
- HTML reports are optional detailed artifacts and should stay in the ignored run directory
- no credentials, local environment values, or full browser profiles should be recorded

## URL And Server Modes

Supported modes should be explicit:

| Mode | Purpose | Notes |
| --- | --- | --- |
| `existing-local-url` | Use a user-started local app or public preview route. | Requires a configured base URL and health/readiness check. |
| `temp-static-public-build` | Serve an isolated static build for public-route checks. | Use when route behavior does not require local write services. |
| `admin-route` | Inspect local Admin routes. | Prefer Playwright smoke evidence over Lighthouse unless accessibility/layout is the question. |
| `docs-viewer-route` | Inspect Docs Viewer public/manage routes. | Keep public read-only and manage-mode targets separate. |

Do not add a generic URL input.
If a new route needs Lighthouse, add a named target first.

## Runtime Artifact Shape

`runtime-checks.json` should keep a compact summary:

```json
{
  "status": "passed",
  "profiles": [
    {
      "profile": "docs-viewer-smoke",
      "exit_code": 0,
      "summary_path": "var/admin/test-runs/risk-example/summary.md"
    }
  ],
  "browser_targets": [],
  "lighthouse": {
    "status": "omitted",
    "targets": []
  }
}
```

Detailed artifacts should live below:

```text
var/admin/risk/runs/<run-id>/artifacts/browser/<target-id>/
var/admin/risk/runs/<run-id>/artifacts/lighthouse/<target-id>/
```

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Wrap allowlisted `admin-app/commands/run_checks.py` profiles through the evidence pack. |
| 2 | planned | Add a checked-in browser target config for public-site, Studio, Analytics, Docs Viewer, and UI Catalogue target ids. |
| 3 | planned | Add a runtime producer path that can collect browser console errors, failed requests, request counts, and basic route readiness for named targets. |
| 4 | planned | Choose the Lighthouse runner dependency and invocation method. Do not use network `npx` installs at runtime. |
| 5 | planned | Implement `--lighthouse-target <target-id>` or equivalent allowlisted target selection instead of a broad `--include-lighthouse` boolean. |
| 6 | planned | Write Lighthouse JSON and optional HTML artifacts under `artifacts/lighthouse/<target-id>/`, then summarize scores in `runtime-checks.json`. |
| 7 | planned | Add focused tests for target validation, arbitrary URL rejection, missing dependency handling, failed route handling, and summary shape. |
| 8 | planned | Update the Admin risk route UI to show target choices only after the backend exposes the allowlisted target list. |

## Open Decisions

- Whether Lighthouse should be a local Node dependency, a documented globally installed tool, or replaced by a Playwright/Chrome DevTools Protocol metric collector.
- Which public routes deserve initial Lighthouse targets.
- Whether mobile Lighthouse should be supported in the first implementation or deferred until desktop public-route checks are stable.
- Whether thresholds should be hard failures, warnings, or evidence-only observations.
