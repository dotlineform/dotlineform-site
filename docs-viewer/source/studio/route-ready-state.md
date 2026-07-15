---
doc_id: route-ready-state
title: Route Ready State
added_date: 2026-06-25
last_updated: 2026-07-15
parent_id: dev-home
viewable: true
---
# Route Ready State

## Contract

Async local-app and Docs Viewer routes expose lifecycle state on one main route root so browser checks and automation know when the first stable render is inspectable.

- `ready="false"`: the root exists but startup has not settled.
- `ready="true"`: the route rendered a stable success, empty, unavailable, or error state.
- `busy="true"`: route-level work such as load, save, preview, publish, delete, import, report, or rebuild is in flight.
- `busy="false"`: no route-level blocking operation is in flight.

Ready does not mean every command is enabled. A route whose service is unavailable should become ready after it renders that state and disables affected commands.

Do not set busy for local-only focus, menus, or panels.

## App Prefixes

| App | Ready | Busy | Ready event | Helper authority |
| --- | --- | --- | --- | --- |
| Studio | `data-studio-ready` | `data-studio-busy` | `studio:ready` | `studio/app/frontend/js/studio-route-state.js` |
| Admin | `data-admin-ready` | `data-admin-busy` | `admin:ready` | `admin-app/app/frontend/js/admin-route-state.js` |
| Analytics | `data-analytics-ready` | `data-analytics-busy` | `analytics:ready` | `analytics-app/app/frontend/js/analytics-route-state.js` |
| Docs Viewer shell | `data-docs-viewer-ready` | `data-docs-viewer-busy` | Docs Viewer boot contract | `site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js` |

Optional prefixed detail attributes may describe route, mode, service availability, and whether a focused record loaded.

The nested Docs Import root currently uses Studio-prefixed attributes inside the Docs Viewer management runtime. Treat that as an explicit compatibility seam, not a reason to mix app prefixes on new route roots.

## Startup Workflow

1. The template declares one root with initial ready/busy values.
2. The route controller initializes optional lifecycle details.
3. Config, service probes, initial data, URL mode, and first render run.
4. Every success or stable failure path sets ready true.
5. Commands set busy true before work and clear it in a reliable final path.

Static Studio routes may use `studio-static-route.js`. Once a route gains async data, service checks, or commands, it needs a route-specific lifecycle owner.

## Testing Method

Tests should wait for:

1. the visible route root;
2. the app's ready attribute to equal `true`;
3. the busy attribute not to equal `true`.

DOM attributes are more reliable than attaching a late event listener. After the shared wait, a focused test may assert route-specific mode, service, record, status, or command state.

Do not maintain a second table of every route/root here. App route registries, templates, and the ready-state audit are the exact inventory.

## Audit

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict
```

The audit checks active Studio, Admin, Analytics, and Docs Viewer templates for missing or duplicate roots and invalid initial attributes. The quick check profile includes it.

Use [Testing](/docs/?scope=studio&doc=testing) for verification selection and [Route Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-route-ready-state) for the focused audit command. Route docs may name their root and meaningful busy operations but should not redefine this contract.
