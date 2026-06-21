---
doc_id: studio-ready-state
title: Route State
added_date: 2026-05-14
last_updated: 2026-05-15
parent_id: studio
viewable: true
---
# Studio Route State

This is the technical reference for the implemented Studio route-ready contract.

## Purpose

Studio pages render asynchronously and often depend on local services, generated lookup payloads, or route-specific module startup. Browser smoke tests and future automation need a stable machine-readable signal for when a route is ready for interaction.

The ready-state contract provides that signal without replacing visible status text. User-facing status copy remains route-specific; the ready-state attributes are for test code, local tooling, and route lifecycle checks.

## Current Status

The contract is implemented across current Studio route shells.

Current verification:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_studio_ready_state.py --strict
```

As of 2026-05-14, the strict audit reports:

- 31 Studio templates
- 31 ready roots
- 9 static routes
- 2 dashboard routes
- 0 errors
- 0 warnings

The Docs Import modal also implements the contract through the Docs Viewer shell, but it is not counted by the Studio route-shell audit because its root is owned by the Docs Viewer management modal rather than a Studio route shell.

## Contract

Each participating route exposes the shared attributes on its main route root.

Baseline attributes:

- `data-studio-ready="false"` while initial route data and first render are still loading
- `data-studio-ready="true"` after the route reaches its initial stable interaction state
- `data-studio-busy="true"` while a route-level command is running
- `data-studio-busy="false"` when no route-level command is running

Optional route detail attributes:

- `data-studio-route`
- `data-studio-mode`
- `data-studio-service`
- `data-studio-record-loaded`

`data-studio-ready="true"` does not mean every command is available. A route with a required service unavailable should still reach a stable ready state, usually with `data-studio-service="unavailable"` and affected controls disabled.

`data-studio-busy` is scoped to route-level work such as save, preview, publish, delete, import, audit, report, refresh, rebuild, or package commands. It should not be used for trivial local UI toggles.

## Helper Module

The shared implementation lives in:

- `site/assets/studio/js/studio-route-state.js`

It exports:

- `initializeStudioRouteState(target, detail)`
- `setStudioRouteBusy(target, busy, detail)`
- `setStudioRouteReady(target, ready, detail)`

`target` may be the root element or an object with a `root` element. The helper normalizes optional detail values, removes empty optional string attributes, writes boolean detail attributes as `"true"` or `"false"`, and dispatches `studio:ready` whenever `setStudioRouteReady` writes the route readiness value.

The event detail includes:

- `ready`
- `busy`
- `route`
- `mode`
- `service`
- `recordLoaded`

Tests should still prefer the DOM attributes because an event may already have fired before a test attaches a listener.

## Route-Specific Implementation

Async and service-backed routes should use `studio-route-state.js` directly.

Typical route startup:

1. the template declares `data-studio-ready="false"` and `data-studio-busy="false"` on the route root
2. the route module calls `initializeStudioRouteState(root, { route: "<route-id>" })`
3. the route performs required config, lookup, service, URL-mode, and initial render work
4. the route calls `setStudioRouteReady(root, true, detail)` after the first stable render, including empty and unavailable-service states
5. command flows call `setStudioRouteBusy(root, true, detail)` before starting and return it to `false` in a `finally` path after success or failure settles

Route modules usually keep a small `routeStateDetail(state)` helper so `ready`, `busy`, mode, service availability, and loaded-record state stay synchronized.

The Docs Import modal mirrors the same helper behavior inside `docs-viewer/runtime/js/import/docs-html-import.js` because that module is owned by the Docs Viewer bundle rather than the Studio route bundle.

## Static Routes

Static landing and reference routes use:

- `site/assets/studio/js/studio-static-route.js`

Their route roots declare:

- `data-studio-static-route="<route-id>"`
- `data-studio-mode="landing"` or `data-studio-mode="reference"`
- `data-studio-ready="false"`
- `data-studio-busy="false"`

`studio-static-route.js` initializes each static root after DOM load, sets `data-studio-record-loaded="true"`, and marks the route ready.

Use this only for static or reference shells. If a static page gains async data, local-service checks, route commands, or another route module, replace the static initializer with a route-specific ready/busy implementation and run the ready-state audit in strict mode.

## Dashboard Routes

Studio no longer has standalone dashboard route shells.
The former Catalogue, Analytics, and Data Sharing dashboards were retired in favor of the grouped `/studio/` home links and page-local metrics.

## Current Route Inventory

Route-specific Studio roots:

- `/studio/bulk-add-work/` with `#bulkAddWorkRoot`
- `/studio/catalogue-field-registry/` with `#fieldRegistryReviewRoot`
- `/studio/catalogue-moment/` with `#catalogueMomentRoot`
- `/studio/catalogue-series/` with `#catalogueSeriesRoot`
- `/studio/catalogue-status/` with `#catalogueStatusRoot`
- `/studio/catalogue-work/` with `#catalogueWorkRoot`
- `/studio/catalogue-work-detail/` with `#catalogueWorkDetailRoot`
- `/studio/project-state/` with `#projectStateRoot`
- `/studio/studio-works/` with `#worksStudioRoot`

Static Studio roots:

- `/studio/` with `#studioHomeRoot`
The legacy UI catalogue reference routes have been retired and do not expose the production `data-studio-ready` contract.

Analytics app route roots:

- `/analytics/data-sharing/prepare/` with `#dataSharingPrepareRoot`
- `/analytics/data-sharing/review/` with `#dataSharingReviewRoot`
- `/analytics/series-tag-editor/` with `#seriesTagEditorRoot`
- `/analytics/series-tags/` with `#series-tags`
- `/analytics/tag-aliases/` with `#tag-aliases`
- `/analytics/tag-groups/` with `#tag-groups`
- `/analytics/tag-registry/` with `#tag-registry`

Retired Studio Analytics, Data Sharing, UI Catalogue, and thumbnail-quality routes do not expose active ready-state roots.


Docs Viewer ready root:

- `/docs/?import=1` with `#docsHtmlImportRoot`

## Smoke Test Usage

Smoke tests should wait for the route root to be visible, ready, and not busy:

```python
def wait_for_studio_route_ready(page, root_selector):
    page.wait_for_selector(f"{root_selector}:not([hidden])")
    page.wait_for_selector(f"{root_selector}[data-studio-ready='true']")
    page.wait_for_function(
        "selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'",
        arg=root_selector,
    )
```

After the shared wait, route-specific tests may assert `data-studio-mode`, `data-studio-service`, `data-studio-record-loaded`, visible status text, rendered rows, or enabled command controls.

## Audit Coverage

The ready-state audit lives in:

- `admin-app/checks/audit_studio_ready_state.py`

Run it after changing Studio route shells, static/reference pages, dashboard shells, or route-ready helper scripts:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_studio_ready_state.py --strict
```

Strict mode fails on warnings as well as errors. It catches missing baseline attributes, static/dashboard marker mixups, missing static or dashboard helper scripts, dashboard metric markers on static routes, and static routes that start loading another module script.

The `quick` profile in `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` includes this audit.

## Related References

- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
