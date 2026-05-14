---
doc_id: studio-smoke-testing
title: Studio Smoke Testing
added_date: 2026-05-01
last_updated: "2026-05-13"
parent_id: studio
sort_order: 40
---
# Studio Smoke Testing

This document records the practical harness rules for lightweight Codex-run Studio browser smoke tests.

It complements the broader [Testing](/docs/?scope=studio&doc=testing) guidance. Use this page for Studio browser-test mechanics, not for general check policy.

## Purpose

Studio pages are local-service-backed, async-rendered admin surfaces. Smoke tests should verify real route behavior without creating false failures from racing page load, async list rendering, or browser scroll heuristics.

Use these rules when a Codex-run check needs to open a Studio page, create temporary in-browser draft state, or click a Studio command.

## Runtime Setup

Prefer the normal local Studio stack when it is already running.

For one-off static review, use:

- a Jekyll build written to a temporary destination
- a local static HTTP server serving that build
- the catalogue write server when the page reads or writes catalogue source data

`./scripts/run_checks.py --profile docs-viewer-smoke` prepares the temporary Jekyll build used by the retained Docs Viewer route smoke.
`./scripts/run_checks.py --profile studio-smoke` prepares the same kind of temporary Jekyll build and runs broader retained Studio route smoke scripts.
Route-specific Playwright scripts should live under `tests/smoke/` when the scenario is worth keeping.

Do not use a raw `file://` URL for Studio pages that depend on module imports, local services, or same-origin asset paths.

## Page Readiness

Do not interact with a Studio page immediately after `domcontentloaded`.

For routes that have adopted the shared ready-state contract, prefer the route root attributes:

```python
def wait_for_studio_route_ready(page, root_selector):
    page.wait_for_selector(f"{root_selector}:not([hidden])")
    page.wait_for_selector(f"{root_selector}[data-studio-ready='true']")
    page.wait_for_function(
        "selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'",
        arg=root_selector,
    )
```

The route root may also expose `data-studio-mode`, `data-studio-service`, and `data-studio-record-loaded` for route-specific checks.

Minimum readiness for page-level smoke tests:

1. wait for the page root to be visible, such as `#catalogueWorkRoot:not([hidden])`
2. wait for the page's loaded status text or another route-specific loaded marker
3. allow a short settle window when the next action is below an async-rendered list or media preview

Example:

```python
def wait_for_studio_loaded(page, root_selector, loaded_text):
    page.wait_for_selector(f"{root_selector}:not([hidden])")
    page.wait_for_function(
        """([selector, text]) => document.querySelector(selector)?.textContent.includes(text)""",
        arg=["#catalogueWorkStatus", loaded_text],
    )
    page.wait_for_timeout(300)
```

The status selector and loaded text should be route-specific. Do not assume every Studio page uses the same ids. Use this status-text pattern only for routes that have not adopted the shared ready-state attributes yet, or as a fallback assertion for route-specific content.

## Pointer Clicks

Use real pointer clicks for the control being tested.

Before clicking controls below async-rendered lists, scroll the target into view and confirm hit testing resolves to the target or one of its children. This avoids false failures where Playwright's auto-scroll lands while a nearby row is still intercepting the click.

Example:

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

Use DOM activation only for setup-only actions that are not the behavior under test.

Example:

```python
page.evaluate("document.querySelector('#catalogueWorkNewFileLink').click()")
```

This is acceptable when the test goal is a later control, such as a public-update preview modal, and the setup action only creates temporary in-browser draft state.

Do not use DOM activation for the primary action being verified. If the action being verified cannot be clicked with a real pointer after readiness and hit-test checks, report that as a UI issue.

## Current Adoption

The shared route-ready contract is implemented on current Studio route shells. The canonical route inventory lives in [Studio Ready State](/docs/?scope=studio&doc=studio-ready-state).

The dashboard and reference-page routes use a minimal ready contract. For those routes, smoke tests should only treat the root attributes as initial page-shell readiness unless a future feature adds route-specific async behavior or commands.

The rollout history is tracked in [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract).

## Ready-State Audit

Run the ready-state audit after changing Studio route shells, route scripts, or route-ready helpers:

```bash
./scripts/checks/audit_studio_ready_state.py --strict
```

The audit is intentionally conservative. It fails when static and dashboard route markers are mixed, when a static route starts to expose dashboard metrics, when required ready/busy baseline attributes are missing, or when dashboard routes are not wired to the dashboard loader. In strict mode it also fails if a static route starts loading another module script, because that usually means the route needs a specific readiness contract before browser tests trust it.

The `quick` profile in `./scripts/run_checks.py` includes this audit so ready-state drift is caught during normal lightweight checks.

## Manual Check Pairing

Every Codex-run smoke test should still name the manual follow-up when behavior depends on tactile interaction, visual layout, or mobile scrolling.

For example:

- Codex-run check: open the page, create draft state, click the target command, confirm modal text
- manual check: repeat the same flow on desktop and mobile to confirm the control placement and pointer interaction feel natural
