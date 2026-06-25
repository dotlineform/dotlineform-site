---
doc_id: docs-viewer-static-route-template
title: Docs Viewer Static Route Template
added_date: 2026-06-25
last_updated: 2026-06-25
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Static Route Template

Docs Viewer uses static route shells, but its shape differs from Studio, Admin, and Analytics.
Those apps load route body templates inside a local app shell.
Docs Viewer route shells are whole-page shells that expose stable mount points for the shared Docs Viewer runtime.

The model is:

- public Docs Viewer routes are tracked static HTML files under `site/`
- the local manage route is served from `docs-viewer/shell/docs-viewer-manage.html`
- new public read-only route shells are rendered from `docs-viewer/templates/public-route/index.html`
- route config records select the active scope, generated payload URLs, access mode, UI text, and panel settings
- public and manage entrypoints load the shared runtime and attach behavior to stable shell mounts
- management, import, report, and write-capable behavior stays out of public route shells

## Structure

```text
docs-viewer/
  shell/
    docs-viewer-manage.html
  templates/
    public-route/
      index.html
  runtime/js/
    public/
      docs-viewer-public.js
    management/
      docs-viewer-manage.js
    shared/
      docs-viewer-app-boot.js
      docs-viewer-app-composition.js
      docs-viewer-route-workflow.js

site/
  library/
    index.html
  analysis/
    index.html
  docs-viewer/
    config/routes/docs-viewer-public-routes.json
```

Public route shells identify the public route registry:

```html
<section
  class="docsViewer"
  id="docsViewerRoot"
  data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"
  data-include-scope-param="false"
>
  <div id="docsViewerHeaderControlsMount" data-docs-viewer-header-controls-mount></div>
  <div id="docsViewerIndexPanelMount" data-docs-viewer-index-panel-mount></div>
  <div id="docsViewerMainViewMount" data-docs-viewer-main-view-mount></div>
  <div id="docsViewerInfoPanelMount" data-docs-viewer-info-panel-mount></div>
</section>
```

The local manage shell identifies the local/manage route registry:

```html
<section
  class="docsViewer"
  id="docsViewerRoot"
  data-route-id="docs-manage"
  data-route-config-url="/docs-viewer/config/routes/docs-viewer-routes.json"
  data-include-scope-param="false"
>
  <div id="docsViewerManagementShellMount" data-docs-viewer-management-shell-mount></div>
</section>
```

## Route Boundary

Docs Viewer route shells own stable DOM:

- `#docsViewerRoot`
- `[data-docs-viewer-header-controls-mount]`
- `[data-docs-viewer-index-panel-mount]`
- `[data-docs-viewer-main-view-mount]`
- `[data-docs-viewer-info-panel-mount]`
- `[data-docs-viewer-management-shell-mount]` for the manage shell only

The route config owns scope, access, payload, and feature settings.
The runtime owns behavior:

- `docs-viewer/runtime/js/public/docs-viewer-public.js` for public read-only routes
- `docs-viewer/runtime/js/management/docs-viewer-manage.js` for the local manage route
- `docs-viewer/runtime/js/shared/docs-viewer-app-boot.js` and related shared modules for composition, route workflow, generated-data reads, search, document rendering, bookmarks, info panels, and hosted views

Docs Viewer public route shell creation is documented separately in [Docs Viewer Public Route Shell Template](/docs/?scope=studio&doc=docs-viewer-public-route-shell-template).
That document covers the lifecycle renderer, render inputs, New Scope flow, Delete Scope flow, and maintenance rules for tracked public `site/<route>/index.html` files.

## Ready State

Docs Viewer public and manage shells participate in the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state) contract with Docs Viewer attributes on `#docsViewerRoot`.

Current state:

- `#docsViewerRoot` uses `data-docs-viewer-ready` and `data-docs-viewer-busy`
- boot writes `data-docs-viewer-busy="true"` while initial route config, app shell, config, index, and startup work are in flight
- boot writes `data-docs-viewer-ready="true"` after initial startup reaches a stable success or error state
- `/docs/?import=1` uses `#docsHtmlImportRoot` with Studio-style ready/busy attributes inside the Docs Viewer bundle

Docs Viewer smokes should prefer `#docsViewerRoot[data-docs-viewer-ready="true"]` and `data-docs-viewer-busy!="true"` before asserting route-specific loaded markers or stable rendered content.

## Public And Manage Split

Public route shells must not load or expose:

- management runtime modules
- import runtime modules
- write-capable controls
- localhost service URLs
- source-editing controls
- scope lifecycle actions

The manage shell may expose local management mounts and management runtime modules because it is served by the standalone Docs Viewer service.
Public route shells are deploy-root source files, not local service routes.
