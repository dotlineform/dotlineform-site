---
doc_id: docs-viewer-panel-hosts
title: Docs Viewer Panel Hosts
added_date: 2026-05-28
last_updated: 2026-05-28
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Panel Hosts

Docs Viewer now has a JavaScript-owned app-shell foundation for coordinated panel regions and hosted views.

This document records the durable design and implemented ownership boundaries.

## Current Shape

The current app shell provides:

- header controls
- index panel shell and index-panel chrome
- document shell and document/search/recent/report mounts
- info panel shell
- management action shell and management-only modal/context-menu hosts
- route config and access projection
- view-state skeleton for index, document, and info slots
- hosted-view registration and lifecycle helpers
- selected-document context for hosted views
- read-only metadata info view

Core ownership:

| area | owner |
| --- | --- |
| app-shell boot and shell rendering | `docs-viewer/runtime/js/docs-viewer-app-shell.js` |
| route config resolution | `docs-viewer/runtime/js/docs-viewer-route-config.js` |
| public/manage access projection | `docs-viewer/runtime/js/docs-viewer-access.js` |
| current route/app context | `docs-viewer/runtime/js/docs-viewer-app-context.js` |
| view-state skeleton | `docs-viewer/runtime/js/docs-viewer-view-state.js` |
| current panel projection | `docs-viewer/runtime/js/docs-viewer-panel-layout.js` |
| hosted-view records and access checks | `docs-viewer/runtime/js/docs-viewer-hosted-views.js` |
| selected-document hosted-view context | `docs-viewer/runtime/js/docs-viewer-view-context.js` |
| info-panel lifecycle | `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` |
| info-panel chrome | `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js` |
| read-only metadata info view | `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` |

The current panel projection still preserves existing two-panel behavior where needed.
The index panel projects collapsed, normal, and expanded states from the active index hosted view’s capabilities.
The built-in `index-tree` view supports normal and collapsed states, while the management-route `index-graph` placeholder opts into expanded mode.
The management toolbar exposes the available index-view switch as a single projected icon pill when more than one index hosted view is available.
The document shell still owns document payload rendering plus search, recent, and report surfaces through the existing document/search/report controllers.
The info panel is a real app-shell panel with a selected-document metadata hosted view.

## Panel Model

Docs Viewer has three conceptual panel regions:

- index
- document
- info

The selected document is app state, not just document-panel visibility.
The info panel can render selected-document context without moving document payload loading or metadata editing into the info view.

Current DOM projection uses panel-related data attributes such as:

- `data-index-panel-state`
- `data-document-panel-state`
- `data-info-panel-state`
- `data-viewer-layout`

These attributes are the CSS and route-shell boundary.
Feature code should update panel state through the app-shell/panel helpers rather than mutating layout attributes directly.

## Hosted Views

Panel bodies can host named view modules.
This is a modular hosted-view architecture, not a plugin architecture.

Hosted-view modules are ordinary repo JavaScript modules.
They are not independent packages, sandboxes, or marketplace plugins.
Repo-specific modules may know about repo-specific generated data and local service contracts.

Expected view-module shape:

```text
id
label
panel
access
load()
mount(container, context)
update(context)
unmount()
dispose()
```

The host provides:

- a stable container element
- selected document and scope context
- route mode and access information
- generated-data helpers where available
- management/backend client context only when the route and capabilities allow it
- lifecycle cleanup when views change or close

Modules must render inside their assigned container.
They should not mutate unrelated panel chrome, route controls, or global document structure.

## Public And Manage Access

Panels are not public-only or manage-only.
Individual views and actions are gated.

Public routes can use public-safe panel views such as read-only metadata.
Manage mode can expose additional views or actions only after route access and backend capability checks allow them.

The browser app must not gain direct write authority.
Source Markdown writes, metadata saves, move/delete/import workflows, source opening, rebuilds, filesystem allowlists, and validation remain backend-owned.

Management-only modules should not be loaded or shown on public read-only routes.
Backend endpoints must still enforce capability server-side even when client controls are hidden.

## Metadata Info View

The first implemented hosted info view is the read-only metadata view.

It is public-safe and selected-document scoped.
It can be shown in public routes and manage mode.
It complements the existing document metadata and sidebar display; it does not replace the metadata edit modal or create a save path.

The metadata info view may show values such as:

- title
- doc id
- scope
- parent/path context
- summary
- added and updated dates
- UI status
- visibility derived from `viewable`

## Optional Future Modules

Future modules may include:

- source editor views
- semantic-reference helper views
- relationship/reference explorers
- generated report dashboards
- graph or visualization modules
- scope health or build-status views

Heavier or uncertain modules should start as manage-only.
Promotion to public presentation should be a separate product decision based on usefulness, data stability, performance, accessibility, and portable-install expectations.

Optional modules should be registered explicitly.
If a module is absent or disabled, the app shell should omit that view or action rather than failing route boot.

## Not A Plugin System

Do not add plugin-system machinery for the current panel host.

Avoid:

- package manifests
- marketplace assumptions
- generic adapter layers
- sandbox protocols
- automatic third-party asset bundling
- route-wide imports for optional modules

The current contract is simpler:

- core Docs Viewer owns panel regions, view selection, access checks, registration, lifecycle, and cleanup
- view modules own their own UI, data shaping, optional library imports, and repo-specific integration logic

## Remaining Design Gaps

The current foundation does not yet provide:

- a generalized panel toolbar model across index, document, and info panels
- explicit document-panel view switching for document/search/recent/report/source views
- a source editor or semantic-reference editor
- activity or generated relationship info views
- URL or persistence policy for panel layout state beyond current panel behavior
- a public contract for optional visualization modules

Those items should be specified as concrete change requests before implementation.

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)
