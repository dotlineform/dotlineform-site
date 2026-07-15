---
doc_id: smoke-testing
title: Browser Smoke Testing
added_date: 2026-05-01
last_updated: 2026-07-15
parent_id: testing
viewable: true
---
# Browser Smoke Testing

## When A Smoke Is Appropriate

Use a permanent browser smoke only when the durable risk exists in the browser integration boundary:

- route shell/config/template/controller boot;
- browser module loading and public/private asset separation;
- local service reachability and request/response agreement;
- shared ready/busy state;
- public read-only versus management capability separation.

Use pure/service/API tests for deterministic data behavior. Use manual or temporary browser checks for copy, layout, hover/focus, modal timing, pointer feel, and mobile ergonomics.

## Ownership

| Owner | Location | Profile |
| --- | --- | --- |
| Docs Viewer | `docs-viewer/tests/smoke/` | `docs-viewer-smoke` |
| Admin | `admin-app/tests/smoke/` | `admin-smoke` |
| Analytics | `analytics-app/tests/smoke/` | `analytics-smoke` |
| Studio/public catalogue | `studio/tests/smoke/` | `studio-smoke` |

Keep niche/expensive/recent-fix scripts focused rather than adding everything to a profile. A retained smoke should have a clear trigger for when to run it.

## Correct Runtime Target

- local app route: owning local server/API;
- public site or public Docs Viewer: checked-in `site/` served over HTTP;
- module-contract smoke: explicit source-module fixture root;
- route-specific fixture: only when the script owns its setup.

Do not use `file://`, repo root, or a stale `_site` as public evidence. A pass proves only the target/profile actually run.

## Readiness And Interaction

1. Navigate and wait for DOM content.
2. For participating routes, call `tests/smoke/route_ready_helpers.py::wait_for_route_ready` with the app root and ready/busy attributes.
3. Assert the route-specific mode/service/data condition that makes the next action meaningful.
4. Use a real pointer click for the action under test; scroll/hit-test first if async layout may cover it.
5. DOM activation is acceptable only for setup that is not the behavior under test.

Do not add arbitrary sleeps in place of an owned readiness condition. A short settle window is acceptable only for layout after semantic readiness.

## Public Docs Viewer Contract

Public Library/Analysis/Moments smokes should prove public payload reads and absence of management assets/services. They should use the configured public tree/recent/by-id/search contracts rather than local management indexes.

## Ready-State Audit

Template-level ready/busy structure is cheaper to prove with:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict
```

The audit does not replace a smoke when runtime controller behavior is the risk.

## Manual Pairing

When the result also depends on visual fit or tactile behavior, state the manual follow-up separately. Automated evidence should not claim to prove what it did not inspect.

## Weak Spots

- Browser fixtures can duplicate runtime config/data and drift from production owners.
- Profile names do not imply exhaustive app coverage.
- UI-heavy legacy smokes impose maintenance cost and should be pruned when touched rather than expanded.
- Local ports/process cleanup can create false failures unrelated to the product contract.
