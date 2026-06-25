---
doc_id: smoke-testing
title: Browser Smoke Testing
added_date: 2026-05-01
last_updated: 2026-06-25
parent_id: testing
viewable: true
---
# Browser Smoke Testing

This page records practical harness rules for lightweight Codex-run browser smoke tests.

Treat this guidance as app-neutral: Docs Viewer, Admin, Analytics, Studio, and public-site smokes should follow the same readiness and interaction standards while staying under their owning app directories.

Use this page for browser-test mechanics. Use [Testing](/docs/?scope=studio&doc=testing) to choose which profile or focused command to run.

## When To Add A Smoke

Add or run a browser smoke when the risk is route or module integration, not just pure data transformation and not ordinary UI choreography.

Good candidates:

- public route loads and recovers from missing state
- local app route boots against its expected config
- browser modules expose the expected narrow public surface
- management-only modules stay out of public installs
- shared ready/busy state controls route availability
- local APIs and route shells must agree on request/response shape

Prefer Python module tests for deterministic service, parser, schema, and planner behavior. Do not add a browser smoke when a focused Python test would describe the risk more directly.

Poor candidates for permanent browser smokes:

- modal open/close timing
- cursor, hover, focus, and button disabled state
- copy, labels, and visual placement
- normal user workflows whose data flow can be tested through services or HTTP responses
- one-off UI regressions that can be verified manually or with a temporary script

Existing UI-heavy smoke scripts may stay until their owners prune them, but new work should not deepen that coverage.

Before adding or expanding a smoke, ask whether a pure function, service, or direct HTTP/API test would prove the same contract. Use a browser only when the behavior depends on route boot, module loading, public/private asset boundaries, ready-state wiring, or the route shell's request/response integration.

## Where Smokes Live

Keep each smoke with the app that owns the route or browser module.

| owner | location | profile |
| --- | --- | --- |
| Docs Viewer | `docs-viewer/tests/smoke/` | `docs-viewer-smoke` or focused script |
| Admin app | `admin-app/tests/smoke/` | `admin-smoke` |
| Analytics app | `analytics-app/tests/smoke/` | `analytics-smoke` |
| Studio and public site | `studio/tests/smoke/` | `studio-smoke` or focused script |

Do not put a smoke into `studio-smoke` just because it uses a browser. The profile should reflect the owner of the behavior.

## Profile Membership

Put a smoke in the owning app profile when it protects a durable boundary that should be checked during routine confidence runs. Good profile candidates cover route boot, module loading, public/private asset separation, API reachability, request/response agreement, or shared ready/busy state for routes that change often or carry broad operational risk.

Keep a smoke as a focused script when it protects a niche workflow, a recent fix, an expensive setup, or a route-specific contract that is only relevant to narrow changes. Name the focused script in close-out when it is the evidence that proves the changed contract.

Do not profile a smoke whose main value is UI choreography, visual fit, copy tone, hover/focus feel, modal timing, or mobile ergonomics. Use manual review or a temporary script for that evidence instead.

If a retained smoke has no clear trigger for when to run it, either add it to the owning app profile, document the trigger near the script or owning doc, or prune it.

## Runtime Setup

Use the target the route expects:

- local app server for Admin, Analytics, Docs Viewer manage-service, and operational app routes
- checked-in `site/` root for public-site behavior and public Docs Viewer Library/Analysis installs
- source module root for module-contract smokes that import frontend modules directly
- route-specific fixture server only when the script owns that setup explicitly

`docs-viewer-smoke` and `studio-smoke` validate and serve the checked-in `site/` root for public-site behavior.

Profile setup expectations:

| profile or command type | setup target | evidence limit |
| --- | --- | --- |
| `docs-viewer-smoke` | checked-in `site/` for public Docs Viewer installs, plus standalone Docs Viewer manage-service setup when the script owns it | proves public read-only installs and manage-service route boundaries; does not prove unrelated local app routes |
| `studio-smoke` | checked-in `site/` for public-site behavior and source module root for explicit module-contract smokes | proves public route/module boundaries selected by the profile; does not prove local Studio operational routes unless their scripts are run |
| `admin-smoke` | local Admin app route servers and app-owned fixtures | proves Admin route/runtime boundaries; does not prove public-build behavior |
| `analytics-smoke` | local Analytics app route/API servers, app-owned fixtures, and source module root for explicit module-contract smokes | proves Analytics route, API, ready-state, data-sharing, and module boundaries selected by the profile |
| focused smoke script | the target named or created by that script | proves only the route, module, or fixture boundary named by the script |

Treat profile results as evidence for the setup target they ran against. A passing local app smoke does not prove public-build behavior, and a passing public `site/` smoke does not prove local write-service or management-route behavior.

The default `full` profile is a broad confidence run, not an exhaustive run of every app smoke profile. Run `analytics-smoke` explicitly when Analytics route, API, ready-state, data-sharing, or module-browser evidence matters.

Do not use a raw `file://` URL for pages that depend on module imports, local services, or same-origin asset paths.

## Page Readiness

Do not interact with a page immediately after `domcontentloaded`.

For app route smokes, use the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state) helper in `tests/smoke/route_ready_helpers.py`.
It waits for the route root to be visible, ready, and not busy:

```python
def wait_for_route_ready(page, root_selector, ready_attr, busy_attr, timeout_ms=10_000):
    page.wait_for_selector(f"{root_selector}:not([hidden])", timeout=timeout_ms)
    page.wait_for_selector(f"{root_selector}[{ready_attr}='true']", timeout=timeout_ms)
    page.wait_for_function(
        """([selector, attr]) => document.querySelector(selector)?.getAttribute(attr) !== 'true'""",
        arg=[root_selector, busy_attr],
        timeout=timeout_ms,
    )
```

Use the app-specific attributes documented in Route Ready State.

Minimum readiness for route-level smoke tests:

1. wait with `wait_for_route_ready(...)` when the route participates in the contract
2. assert route-specific mode, service, record-loaded state, rendered rows, or enabled controls after the shared wait
3. allow a short settle window only when the next action depends on async-rendered layout

Use route-specific selectors and app-specific ready/busy attributes. Do not assume every app uses the same status id, loaded text, or root attribute names.

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

Run the ready-state audit after changing Studio, Admin, Analytics, or Docs Viewer route shells, route scripts, or route-ready helpers:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict
```

The `quick` profile includes this audit. The audit validates active route templates across Studio, Admin, Analytics, and Docs Viewer.
The shared cross-app contract is maintained in [Route Ready State](/docs/?scope=studio&doc=route-ready-state).

## Manual Check Pairing

Every Codex-run smoke test should still name the manual follow-up when behavior depends on tactile interaction, visual layout, copy tone, modal choreography, or mobile scrolling.

Example:

- Codex-run check: open the route, wait for readiness, trigger the request boundary, and confirm the mocked API response is surfaced
- manual check: repeat the user flow on desktop and mobile to confirm placement, timing, pointer behavior, and modal lifecycle feel correct
