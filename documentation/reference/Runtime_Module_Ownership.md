---
draft: false
doc_id: d-20260605-125108-1d1ef3
title: Runtime Module Ownership
added_date: 2026-06-05 12:51:08
last_updated: "2026-11-18"
summary: Grouped browser-code owners and a practical trace order for Docs Viewer runtime changes.
parent_id: d-20260331-000000-c313fd
---

# Runtime Module Ownership

Docs Viewer has distinct public, Manage and Review compositions. Follow their dependencies from the active route when finding the owner of a failure or change. [Configuration](Configuration_And_Extension_Points.md)

## Entrypoints Define The Surface

| Surface | Entrypoint and route owner |
| --- | --- |
| Public | [`public/docs-viewer-public.js`](../../docs-viewer/runtime/js/public/docs-viewer-public.js), selected by `site/index.html` and the public route registry. |
| Manage | [`management/docs-viewer-manage.js`](../../docs-viewer/runtime/js/management/docs-viewer-manage.js), selected by the local `/docs/` shell. |
| Review | [`review/docs-viewer-review.js`](../../docs-viewer/runtime/js/review/docs-viewer-review.js), selected by the local `/docs-review/` shell and its separate service flag. |

The shared boot owner resolves the route registry, constructs context and composes the providers, views and controls contributed by the entrypoint. The public import graph carries its read-only authority. [Boot](../../docs-viewer/runtime/js/shared/docs-viewer-app-boot.js) · [Composition](../../docs-viewer/runtime/js/shared/docs-viewer-app-composition.js)

## Shared Reader Owners

| Responsibility | Start in `docs-viewer/runtime/js/shared/` |
| --- | --- |
| Boot and orchestration | `docs-viewer-app-boot.js`, `docs-viewer-app-composition.js`, `docs-viewer-app-session.js`, `docs-viewer-app-runtime.js`. |
| Route, access and service context | `docs-viewer-app-context.js`, `docs-viewer-route-config.js`, `docs-viewer-route-features.js`, `docs-viewer-access.js`, `docs-viewer-service-context.js`. |
| Configured data | `docs-viewer-workspace-provider.js` and `docs-viewer-generated-data-runtime.js`. |
| Document and hosted views | `docs-viewer-document-controller.js`, `docs-viewer-document-view-coordinator.js`, `docs-viewer-main-view-host.js`, `docs-viewer-info-panel-host.js`. |
| Navigation and discovery | `docs-viewer-route-workflow.js`, `docs-viewer-router.js`, `docs-viewer-sidebar.js`, `docs-viewer-tree.js`, `docs-viewer-search-controller.js`. |

Use the focused domain references for each workflow's current data and completion rules. [Reader discovery](Reader_Discovery_And_Return.md) · [Source editing](Source_Editing.md) · [Reports](Reports.md)

## Local Workflow Owners

Manage's `docs-viewer-management.js` coordinates local capabilities and controllers. `docs-viewer-action-definitions.js` decides availability from explicit targets. Focused owners handle Source, document mutations, checked collection actions and import. Transport lives in `docs-viewer-management-client.js`. The shared `docs-viewer-runtime-lazy-controller.js` keeps local orchestration behind the composition boundary. [Mutation owners](Source_Mutation_Endpoints.md) · [Import and packages](Document_Packages.md#implementation-boundary)

Local report loading and presentation live in `runtime/js/reports/`. Review's package provider and controllers live in `runtime/js/review/`. Python services own filesystem confinement, persistence, generation and transfers; the [local service map](Endpoint_Overview.md) follows HTTP dispatch into those operation owners. A report or helper becomes shared when a named public adopter needs it, with its canonical implementation and explicit public projection inventory updated together. [Report authority](Reports.md) · [Review](Docs_Review.md)

## Public Deployment Projection

Local services serve canonical code from `docs-viewer/`. Public preview and Pages read the manifest-selected copies from `site/docs-viewer/`. Change canonical shared/public code, project it with `bin/site-code-update`, inspect the delta, then check the projection and validate the site. Public-only shells and route records are edited at their tracked site owner. [Projection](Projection_Contract.md) · [Preview](Local_Setup.md#public-preview-and-projection)

## Trace A Failure

1. Identify the host and shell, then its entrypoint and app kind.
2. Inspect the served route record, selected browser config, enabled features and requested URLs.
3. Find the view/action/report registration and its provider or named service.
4. For a local operation, inspect the service flag and live capability result.
5. Follow the focused controller to the request and the server's exact operation owner.
6. Recover the failed phase, then reload the affected reader. Saved source or completed generated output can already exist. [Phase recovery](Local_Setup.md#recover-the-failed-owner)

The grouped map is maintained when responsibilities move. Exact module exports and request fields belong to their source owners.
