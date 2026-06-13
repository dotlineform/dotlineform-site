---
doc_id: smoke-testing
title: Browser Smoke Testing
added_date: 2026-05-01
last_updated: 2026-06-13
parent_id: testing
viewable: true
---
# Browser Smoke Testing

This page records practical harness rules for lightweight Codex-run browser smoke tests.

Treat this guidance as app-neutral: Docs Viewer, Admin, Analytics, UI Catalogue, Studio, and public-site smokes should follow the same readiness and interaction standards while staying under their owning app directories.

Use this page for browser-test mechanics. Use [Testing](/docs/?scope=studio&doc=testing) to choose which profile or focused command to run.

## When To Add A Smoke

Add or run a browser smoke when the risk is route behavior, not just pure data transformation.

Good candidates:

- public route loads and recovers from missing state
- local app route boots against its expected config
- browser modules expose the expected narrow public surface
- management-only modules stay out of public installs
- ready/busy state controls whether commands can be used
- a modal, menu, or publish/confirm flow needs real DOM behavior
- local APIs and route shells must agree on request/response shape

Prefer Python module tests for deterministic service, parser, schema, and planner behavior. Do not add a browser smoke when a focused Python test would describe the risk more directly.

## Where Smokes Live

Keep each smoke with the app that owns the route or browser module.

| owner | location | profile |
| --- | --- | --- |
| Docs Viewer | `docs-viewer/tests/smoke/` | `docs-viewer-smoke` or focused script |
| Admin app | `admin-app/tests/smoke/` | `admin-smoke` |
| UI Catalogue | `admin-app/tests/smoke/` | `ui-catalogue-smoke` |
| Analytics app | `analytics-app/tests/smoke/` | `analytics-smoke` |
| Studio and public site | `studio/tests/smoke/` | `studio-smoke` or focused script |

Do not put a smoke into `studio-smoke` just because it uses a browser. The profile should reflect the owner of the behavior.

## Runtime Setup

Use the target the route expects:

- local app server for Admin, Analytics, Docs Viewer manage-service, and operational app routes
- checked-in `site/` root for public-site behavior and public Docs Viewer Library/Analysis installs
- source module root for module-contract smokes that import frontend modules directly
- route-specific fixture server only when the script owns that setup explicitly

`docs-viewer-smoke` and `studio-smoke` validate and serve the checked-in `site/` root for public-site behavior.

Do not use a raw `file://` URL for pages that depend on module imports, local services, or same-origin asset paths.

## Page Readiness

Do not interact with a page immediately after `domcontentloaded`.

For routes that have adopted a shared ready-state contract, wait for the route root to be visible and ready:

```python
def wait_for_route_ready(page, root_selector):
    page.wait_for_selector(f"{root_selector}:not([hidden])")
    page.wait_for_selector(f"{root_selector}[data-studio-ready='true']")
    page.wait_for_function(
        "selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'",
        arg=root_selector,
    )
```

The attribute names are still historically prefixed with `studio` in several route shells. That is a current implementation detail, not a naming model for new Analytics or Admin APIs.

Minimum readiness for route-level smoke tests:

1. wait for the route root to be visible
2. wait for the route's loaded marker, ready attribute, or stable loaded text
3. wait for busy state to clear when the route exposes it
4. allow a short settle window only when the next action depends on async-rendered layout

Use route-specific selectors. Do not assume every app uses the same status id, loaded text, or root attributes.

## Pointer Clicks

Use real pointer clicks for the control being tested.

Before clicking controls below async-rendered lists, scroll the target into view and confirm hit testing resolves to the target or one of its children.

```python
def click_when_hit_testable(page, selector):
    target = page.locator(selector)
    target.scroll_into_view_if_needed()
    page.wait_for_timeout(100)
    page.wait_for_function(
        """selector => {
            const el = document.querySelector(selector);
            if (!el) return false;
            const rect = el.getBoundingClientRect();
            const hit = document.elementFromPoint(
                rect.left + rect.width / 2,
                rect.top + rect.height / 2
            );
            return hit === el || el.contains(hit);
        }""",
        arg=selector,
    )
    target.click()
```

If hit testing does not resolve to the target, inspect the page geometry before treating the product as broken. A repeated failure may indicate a real overlap or stacking bug.

## Setup Actions

Use DOM activation only for setup actions that are not the behavior under test.

```python
page.evaluate("document.querySelector('#catalogueWorkNewFileLink').click()")
```

That is acceptable when the test goal is a later control, such as a publish preview modal, and the setup action only creates temporary in-browser draft state.

Do not use DOM activation for the primary action being verified. If the action being verified cannot be clicked with a real pointer after readiness and hit-test checks, report that as a UI issue.

## Public Builds

For public-read behavior, use the checked-in `site/` root through the smoke script's static server setup.

Do not use the repo root or a stale `_site` directory as evidence for public route behavior. Those targets can mask public-build exclusions, missing payloads, or local-only modules.

Docs Viewer public Library and Analysis checks should verify that public installs:

- stay read-only
- load public tree, recent, by-id, and search payloads
- do not require management-only generated payloads
- do not request public docs `index.json` when the public contract uses tree/recent/by-id/search files

## Ready-State Audit

Run the ready-state audit after changing Studio route shells, route scripts, or route-ready helpers:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_studio_ready_state.py --strict
```

The `quick` profile includes this audit. The audit is still Studio-specific because it validates the current Studio route templates; it does not prove Admin, Analytics, Docs Viewer, or UI Catalogue route readiness.

## Manual Check Pairing

Every Codex-run smoke test should still name the manual follow-up when behavior depends on tactile interaction, visual layout, copy tone, or mobile scrolling.

Example:

- Codex-run check: open the page, create draft state, click the target command, confirm modal text
- manual check: repeat the same flow on desktop and mobile to confirm placement, timing, and pointer behavior feel correct

## Current Gaps

Known smoke-testing gaps:

- several app routes do not yet expose a consistent ready/busy contract
- some smoke scripts are focused one-offs and are not part of a profile
- app smoke profiles have different setup expectations
- Analytics smoke coverage is broader than the default `full` profile
- browser smokes do not replace visual review for UI conformance

Call out these gaps in change close-out when they affect the confidence of the evidence.
