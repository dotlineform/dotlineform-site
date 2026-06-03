---
doc_id: docs-viewer-panel-hosts
title: Panel Hosts
added_date: 2026-05-28
last_updated: 2026-06-03
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
- main-view shell and rendered-document/search/recent mounts
- info panel shell
- management action shell and management-only modal/context-menu hosts
- route config and access projection
- view-state skeleton for index, main-view, and info slots
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
| main-view host state and switch validation | `docs-viewer/runtime/js/docs-viewer-main-view-host.js` |
| selected-document hosted-view context | `docs-viewer/runtime/js/docs-viewer-view-context.js` |
| info-panel lifecycle | `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` |
| info-panel chrome | `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js` |
| read-only metadata info view | `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` |

## Implemented Ownership Areas

### App-Shell Boot And Shell Rendering

`docs-viewer-app-shell.js` renders the browser-owned Docs Viewer shell regions: header controls, index panel mount, main-view mount, management shell hosts, and info-panel mount.
It also projects shell state such as index layout, main-view visibility, info panel state, and toolbar controls.

Improvement needed:

- keep adding shell chrome through explicit projection helpers rather than route-local DOM mutations
- avoid putting feature workflow logic into the shell renderer

### Route Config Resolution

`docs-viewer-route-config.js` normalizes route config for public and manage routes.
It reads panel defaults and hosted-view records from route config and normalizes hosted-view capability metadata.

Improvement needed:

- route config can describe available hosted views, but it does not make arbitrary module loading available
- future view records need clear schema and ownership before adding new fields

### Access Projection

`docs-viewer-access.js` projects public, manage, and manage-local access intent for browser controls.
Hosted-view records use this projection to decide whether a view is available to the current route.

Improvement needed:

- client access projection must remain a visibility and UX helper only
- backend endpoints must still enforce write/read capability server-side

### App Context

`docs-viewer-app-context.js` centralizes current route/app context passed to controllers.
It prevents each feature from re-reading broad global state in its own way.

Improvement needed:

- future hosted views should receive narrow context objects rather than importing broad runtime state

### View-State Skeleton

`docs-viewer-view-state.js` stores browser-only panel state for the index, main-view, and info panels.
It tracks active view ids and mounted/visible state, but it does not own feature rendering.

Current limitation:

- main-view active view state exists, but rendered document/search/recent are still rendered by existing controllers rather than independent mounted hosted-view modules
- report rendering remains on the existing document payload/report path pending a later report-specific decision

Improvement needed:

- finish explicit main-view lifecycle before adding source editor or other main-view modules

### Panel Layout Projection

`docs-viewer-panel-layout.js` projects panel layout from view state and hosted-view capabilities.
It currently drives index panel normal/collapsed/expanded state, index view switching, main-view projection, info-panel projection, and layout attributes.

Current limitation:

- expanded behavior is proven through a manage-only placeholder index view, not a real graph or workspace module

Improvement needed:

- preserve capability-driven layout decisions rather than checking view ids directly
- define persistence/URL policy before expanding panel-state behavior

### Hosted-View Registry

`docs-viewer-hosted-views.js` normalizes hosted-view records, applies access/availability checks, lists views by panel, and registers built-in hosted views.
Built-in records currently include `index-tree`, `rendered-document`, `search-results`, `recent-results`, and `metadata-info`.

Current limitation:

- main-view records update active main-view state through `docs-viewer-main-view-host.js`, but rendered/search/recent rendering still delegates to existing controllers
- route-config records can describe placeholders and capabilities, but the current runtime is not a generic module loader

Improvement needed:

- finish the main-view hosted-view lifecycle before adding source editor or richer main-view modules
- keep this as repo module hosting, not a plugin system

### Selected-Document Hosted-View Context

`docs-viewer-view-context.js` builds a public-safe selected-document context for hosted views.
The metadata info view uses this context to render document metadata and parent trail information.

Improvement needed:

- future info views should request only the context/data they need
- management-only views may receive additional services, but only through explicit capability-gated inputs

### Info-Panel Lifecycle And Chrome

`docs-viewer-info-panel-host.js` is the only implemented lifecycle host for actual load/mount/update/unmount/dispose view modules.
`docs-viewer-info-panel-renderer.js` owns the info-panel chrome, toolbar, status, close button, and hosted-view body mount.
`docs-viewer-info-panel-controller.js` binds the document info toggle, close behavior, selected-document updates, and hosted-view context projection.

Current implemented view:

- `metadata-info`

Improvement needed:

- support additional info views only after each has a data contract and access decision
- keep info-panel lifecycle failures graceful and local to the panel

### Metadata Info View

`docs-viewer-metadata-info-view.js` is the first implemented hosted info view.
It is read-only and public-safe.
It renders selected-document metadata such as title, doc id, scope, summary, parent path, dates, UI status, visibility, and route.

Improvement needed:

- do not add edit/save behavior to this view
- use separate manage-only views or workflows for metadata mutation

The current panel projection still preserves existing two-panel behavior where needed.
The index panel projects collapsed, normal, and expanded states from the active index hosted view’s capabilities.
The built-in `index-tree` view supports normal and collapsed states, while the management-route `index-graph` placeholder opts into expanded mode.
The management toolbar exposes the available index-view switch as a single projected icon pill when more than one index hosted view is available.
The main-view shell still owns rendered document payload rendering plus search and recent surfaces through the existing document/search controllers.
Reports remain on the existing document payload/report path for now.
The info panel is a real app-shell panel with a selected-document metadata hosted view.

## Panel Model

Docs Viewer has three conceptual panel regions:

- index
- main
- info

The selected document is app state, not just main-view visibility.
The info panel can render selected-document context without moving document payload loading or metadata editing into the info view.

Current DOM projection uses panel-related data attributes such as:

- `data-index-panel-state`
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

Current hosted-view record shape:

```text
id
label
panel
access
availability
renderer
placeholderText
capabilities
load()
mount()
update()
unmount()
dispose()
```

The normalized record shape exists today in `docs-viewer-hosted-views.js`.
Access and availability checks also exist today.
Capabilities for index layout are implemented and documented in [View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract).

Current lifecycle implementation:

- info-panel views can load, mount, update, unmount, and dispose through `docs-viewer-info-panel-host.js`
- `metadata-info` is the only real mounted hosted-view module
- index hosted-view records drive renderer selection and layout capabilities, but the actual tree and placeholder renderers are app-shell/index-panel render paths rather than mounted lifecycle modules
- main-view hosted-view records exist for `rendered-document`, `search-results`, and `recent-results`; `docs-viewer-main-view-host.js` validates and projects active main-view state, while existing document/search/recent controllers still own rendering
- `report-host` is not part of the main-view migration yet

The implemented lifecycle shape for info-panel hosted views is:

```text
load()
mount(context)
update(context)
unmount(context)
dispose(context)
```

The context currently contains the `mount` element plus selected-document and route/scope metadata.

What still needs implementation:

- a full main-view hosted-view lifecycle that can mount independent main-view modules without breaking current rendered-document/search/recent route behavior
- a clear module-loading policy for route-config hosted-view records beyond built-in and explicitly imported repo modules
- toolbar/view-switching projection for main and info panels when more than one view is available
- a data/context contract for each new info or main-view hosted view before adding the view

Do not interpret route-config hosted-view records as a completed generic extension system.
The current implementation supports configured records, capability projection, access checks, and the info-panel lifecycle.
It does not yet provide a generic view-module loader for arbitrary `module` strings.

For future hosted modules, the host should provide:

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

The current foundation is usable, but the items below need clearer implementation requests before more panel work continues.

### Document-Panel View Switching

Current state:

- document/search/recent/report are represented as hosted-view records and active document-panel view state
- actual rendering still flows through existing document, search, recent, and report controllers
- there is no document-panel host equivalent to `docs-viewer-info-panel-host.js`

What this means:

- a future source editor cannot yet plug into a clean document-panel view lifecycle
- route state for search/recent/report still has to be preserved while any view-switching model is introduced

Request owner:

- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)

### Markdown Source Editor

Current state:

- no source editor is implemented
- source read/write/rebuild endpoints and revision checks are not part of the panel host

What this means:

- source editing should be implemented as a manage-only document-panel view after the document-panel view-switching model is clear enough
- source writes must remain backend-owned

Request owner:

- [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor)

### Semantic-Reference Token Tools

Current state:

- no semantic-token insertion UI is implemented
- no semantic-reference registry exists yet

What this means:

- semantic insertion should be layered on the Markdown editor, not combined with source read/write/rebuild
- the source editor should remain usable when semantic tools are absent

Request owners:

- [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)

### Panel Toolbars

Current state:

- index-panel controls are projected through the app shell
- info panel has close and view-option chrome
- document panel has existing document/search/report controls, but not a generalized panel-toolbar model

What this means:

- do not add ad hoc toolbar controls per feature
- define a small toolbar projection model before adding document-panel source editor controls, multiple info views, or graph/index controls

Request owner:

- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)

### Additional Info Views

Current state:

- only the public-safe metadata info view is implemented
- no activity, semantic-reference, relationship, source-status, or build-status info views exist

What this means:

- each new info view needs a data contract, access policy, lifecycle behavior, and failure state
- operational or write-adjacent views should start manage-only

Request owner:

- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell), until split into smaller view-specific requests

### Panel State Persistence And URL Policy

Current state:

- index collapsed/normal state uses current index-panel persistence behavior
- expanded state is capability-driven and normalized when unsupported by the active index view
- info-panel open/closed state and active view are browser state, not a durable route contract
- document-panel view state is not yet a public URL contract

What this means:

- do not add query/hash state for panel layout opportunistically
- decide which state is local preference, route state, or transient UI state before adding richer panels

Request owner:

- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)

### Optional Visualization Modules

Current state:

- the manage-only `index-graph` is a placeholder proving index-view capability projection
- no real graph, chart, relationship explorer, or external visualization library is implemented

What this means:

- choose the data contract and user workflow before choosing a visualization library
- heavy visualization code should be lazy-loaded only when the selected view needs it
- public exposure needs a separate decision

Request owner:

- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell), until a visualization-specific request exists

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract)
- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)
- [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
