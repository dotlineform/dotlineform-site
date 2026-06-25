---
doc_id: route-ready-state
title: Route Ready State
added_date: 2026-06-25
last_updated: 2026-06-25
parent_id: change-requests
viewable: true
---
# Route Ready State

This is the canonical route lifecycle contract for Studio, Admin, Analytics, and Docs Viewer route shells.
Other docs may name a route root or app helper, but they should link here instead of redefining ready/busy semantics.

## Purpose

Routes render asynchronously and often depend on local services, generated payloads, browser modules, or route-specific startup.
Browser smokes and local tooling need a stable signal for when a route is safe to inspect or interact with.

The route ready-state contract provides that signal without replacing visible status text.
User-facing copy remains route-specific; ready/busy attributes are for test code, local tooling, and lifecycle checks.

## Contract

Each participating route exposes readiness on one main route root.

Canonical meanings:

- `ready="false"` means the route root exists, but initial data, config, module startup, or first render is not stable yet.
- `ready="true"` means the route reached a stable initial state. This includes empty states and stable unavailable/error states after the route has rendered its fallback UI.
- `busy="true"` means route-level work is in flight, such as initial load, save, preview, publish, delete, import, audit, report, refresh, rebuild, or package commands.
- `busy="false"` means no route-level blocking work is in flight.

`ready="true"` does not mean every command is available.
When a required service is unavailable, the route should still become ready once it renders the unavailable state and disables affected controls.

`busy` should not be used for trivial local UI toggles such as opening a menu, changing focus, or showing a local-only panel.

## Attribute Names

The current implementation uses app-prefixed attributes.
Keep these names until a deliberate migration replaces them; adding generic aliases would create a second contract to maintain.

| app | ready attribute | busy attribute | ready event |
| --- | --- | --- | --- |
| Studio | `data-studio-ready` | `data-studio-busy` | `studio:ready` |
| Admin | `data-admin-ready` | `data-admin-busy` | `admin:ready` |
| Analytics | `data-analytics-ready` | `data-analytics-busy` | `analytics:ready` |
| Docs Viewer | `data-docs-viewer-ready` | `data-docs-viewer-busy` | `docs-viewer:ready` |

Optional detail attributes follow the same prefix:

- `data-<app>-route`
- `data-<app>-mode`
- `data-<app>-service`
- `data-<app>-record-loaded`

Tests should prefer DOM attributes over ready events because an event may have fired before the test attaches a listener.

## App Helpers

Current helper modules:

- Studio: `studio/app/frontend/js/studio-route-state.js`
- Admin: `admin-app/app/frontend/js/admin-route-state.js`
- Analytics: `analytics-app/app/frontend/js/analytics-route-state.js`
- Docs Viewer shell boot: `site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js`
- Docs Viewer import modal: `docs-viewer/runtime/js/import/docs-html-import.js`

Each app helper should provide the same behavior:

- initialize route details and set `ready=false`, `busy=false`
- set busy state with optional route details
- set ready state with optional route details
- dispatch the app-specific ready event when ready is written

Studio currently exports:

- `initializeStudioRouteState(target, detail)`
- `setStudioRouteBusy(target, busy, detail)`
- `setStudioRouteReady(target, ready, detail)`

Admin and Analytics helpers should match that shape for route lifecycle behavior.
`target` may be the root element or an object with a `root` element.
Helpers should normalize optional detail values, remove empty optional string attributes, write boolean detail attributes as `"true"` or `"false"`, and dispatch the app-specific ready event whenever ready is written.

## Route Startup

Async and service-backed route startup should follow this order:

1. Template declares the route root with initial ready/busy attributes.
2. Controller initializes route state after mount.
3. Controller performs required config, lookup, service, URL-mode, and first-render work.
4. Controller sets `ready=true` after the first stable render, including empty and unavailable states.
5. Command flows set `busy=true` before starting and return it to `false` in a `finally` path after success or failure settles.

Every route should avoid leaving `ready=false` forever on fetch, config, module, or service failure.

Static or home routes may mark ready immediately, but they should still expose the same baseline unless the route owner has a documented reason not to.

## Static Routes

Studio static landing and reference routes use:

- `studio/app/frontend/js/studio-static-route.js`

Their route roots declare:

- `data-studio-static-route="<route-id>"`
- `data-studio-mode="landing"` or `data-studio-mode="reference"`
- `data-studio-ready="false"`
- `data-studio-busy="false"`

`studio-static-route.js` initializes each static root after DOM load, sets `data-studio-record-loaded="true"`, and marks the route ready.

Use this only for static or reference shells.
If a static page gains async data, local-service checks, route commands, or another route module, replace the static initializer with a route-specific ready/busy implementation and run the ready-state audit in strict mode.

## Current Route Roots

Studio route roots:

| route | root | attributes |
| --- | --- | --- |
| `/studio/` | `#studioHomeRoot` | `data-studio-*` |
| `/studio/bulk-add-work/` | `#bulkAddWorkRoot` | `data-studio-*` |
| `/studio/catalogue-field-registry/` | `#fieldRegistryReviewRoot` | `data-studio-*` |
| `/studio/catalogue-moment/` | `#catalogueMomentRoot` | `data-studio-*` |
| `/studio/catalogue-series/` | `#catalogueSeriesRoot` | `data-studio-*` |
| `/studio/catalogue-status/` | `#catalogueStatusRoot` | `data-studio-*` |
| `/studio/catalogue-work/` | `#catalogueWorkRoot` | `data-studio-*` |
| `/studio/catalogue-work-detail/` | `#catalogueWorkDetailRoot` | `data-studio-*` |
| `/studio/project-state/` | `#projectStateRoot` | `data-studio-*` |
| `/studio/studio-works/` | `#worksStudioRoot` | `data-studio-*` |

Admin route roots:

| route | root | attributes |
| --- | --- | --- |
| `/admin/` | `[data-admin-home]` | `data-admin-*` |
| `/admin/activity/` | `#studioActivityRoot` | `data-admin-*` |
| `/admin/audits/` | `#studioAuditsRoot` | `data-admin-*` |
| `/admin/checks/` | `#studioChecksRoot` | `data-admin-*` |
| `/admin/testing/` | `#adminTestingRoot` | `data-admin-*` |

Analytics route roots:

| route | root | attributes |
| --- | --- | --- |
| `/analytics/` | `#analyticsHomeRoot` | `data-analytics-*` |
| `/analytics/data-sharing/prepare/` | `#dataSharingPrepareRoot` | `data-analytics-*` |
| `/analytics/data-sharing/review/` | `#dataSharingReviewRoot` | `data-analytics-*` |
| `/analytics/series-tag-editor/` | `#seriesTagEditorRoot` | `data-analytics-*` |
| `/analytics/series-tags/` | `#series-tags` | `data-analytics-*` |
| `/analytics/tag-aliases/` | `#tag-aliases` | `data-analytics-*` |
| `/analytics/tag-groups/` | `#tag-groups` | `data-analytics-*` |
| `/analytics/tag-registry/` | `#tag-registry` | `data-analytics-*` |

Docs Viewer route roots:

| route | root | attributes |
| --- | --- | --- |
| `/library/` | `#docsViewerRoot` | `data-docs-viewer-*` |
| `/analysis/` | `#docsViewerRoot` | `data-docs-viewer-*` |
| `/docs/` | `#docsViewerRoot` | `data-docs-viewer-*` |
| `/docs/?import=1` | `#docsHtmlImportRoot` | `data-studio-*` currently, because the import modal mirrors the Studio helper behavior inside the Docs Viewer bundle |

Docs Viewer public and manage shells now expose route-level ready/busy state on `#docsViewerRoot`.
The Docs Import modal keeps its nested import-specific ready state on `#docsHtmlImportRoot`.

## Smoke Wait Pattern

Smoke tests should use the app-specific attributes through one helper shape:

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

After the shared wait, route-specific tests may assert mode, service, record-loaded state, visible status text, rendered rows, or enabled command controls.

## Audit Coverage

Current audit coverage is Studio-only:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_studio_ready_state.py --strict
```

Strict mode fails on warnings as well as errors.
The current Studio audit catches missing baseline attributes, static/dashboard marker mixups, missing static or dashboard helper scripts, dashboard metric markers on static routes, and static routes that start loading another module script.
The `quick` profile includes this audit.

The gap to close is cross-app enforcement.
Either add Admin, Analytics, and Docs Viewer audits or replace the Studio-only script with a general route-ready audit that uses app-specific config for roots, attribute prefixes, static routes, and known exceptions.

Definition of done:

- every active app route has one documented root
- every participating route starts with ready/busy attributes
- route controllers reach `ready=true` on success or stable failure
- route-level commands clear `busy` reliably
- template loading validates the ready/busy baseline
- audits cover Studio, Admin, Analytics, and Docs Viewer route templates
- browser smokes wait on the shared helper shape rather than route-specific timing guesses

## Related Documents

Testing and audit references:

- [Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing)
- [Testing](/docs/?scope=studio&doc=testing)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Audit Runner](/docs/?scope=studio&doc=audit-runner)
- [Audits](/docs/?scope=studio&doc=audits)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)

Route-level docs may name their local root and busy triggers, but they should not redefine this contract.
