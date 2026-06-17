---
doc_id: docs-viewer-toolbar-model
title: Toolbar Model
added_date: 2026-05-31
last_updated: 2026-06-17
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Toolbar Model

This is Docs Viewer-specific UI guidance, not a generic Studio toolbar primitive.

## Purpose

Docs Viewer now has enough controls that "row", "actions", "controls", and "toolbar" should not be used interchangeably.
The rendered view should be easy to describe, and the implementation should expose matching owner surfaces.

The model is:

- top bar: layout container for top-level toolbar groups
- viewer toolbar: read, navigation, search, and index-layout controls
- manage toolbar: management, write, and admin controls
- main-view toolbar: controls for the active central-panel view
- context panel toolbar: view switching inside the context/info panel

## Top Bar

The top bar is a visual layout container.
It can place the viewer toolbar and manage toolbar on the same row when space allows, then wrap one toolbar below the other on narrower screens.

The top bar should not own control behavior.
It should render or mount named toolbar surfaces and let those toolbar owners expose refs to the runtime.

Structure:

```text
top bar
  viewer toolbar
  manage toolbar
```

Responsive behavior should operate on toolbar groups first, then on individual controls inside each toolbar.
This keeps narrow layouts from interleaving unrelated controls.

## Viewer Toolbar

The viewer toolbar owns controls that apply to the viewer experience and remain conceptually read-safe:

- recently added control
- search input
- index view toggle

The index view toggle is a layout/view control.
It should not be treated as a management action, even if some index modes are only available in management-enabled routes.
It renders after the search control so it remains visibly part of the viewer toolbar.

Top-bar layout owner: `docs-viewer-top-bar-renderer.js`

## Manage Toolbar

The manage toolbar owns controls that imply management mode, write capability, or local admin behavior:

- Actions menu
- create, import, delete, settings, rebuild, and scope actions
- viewability controls such as Show / non-viewable
- scope selector for management-enabled docs routes
- management status affordances when needed

The manage toolbar may sit next to the viewer toolbar in the same top bar.
Its presence must still depend on route access and management UI availability.

Owner: `docs-viewer-management-actions-renderer.js`

## Main-View Toolbar

The main-view toolbar owns controls for the active central-panel view.
When the active view is `rendered-document`, it can contain document-specific controls.

Example controls:

- breadcrumbs for `rendered-document`
- context/info panel toggle for selected-document metadata
- bookmark toggle
- manage-mode `Edit` action for the current document
- manage-mode `Markdown source` action that requests `markdown-source`
- source-editor actions such as `Rebuild doc` and back when the editor view is active

Implemented owner:

- `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js` renders the `docsViewerMainViewToolbar` surface and keeps the current rendered-document breadcrumbs, bookmark toggle, and info-panel toggle in that toolbar.
- `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-host.js` exposes the main-view toolbar projection helper through the main-view module context.
- `site/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js` projects the toolbar hidden/visible state when switching between rendered-document, search-results, and recent-results.
- `docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js` composes manage-mode `Edit` and `Markdown source` actions into the same main-view toolbar action area.
- `docs-viewer/runtime/js/management/source-editor/source-editor.js` projects the source-editor toolbar/body state and hosts `Rebuild doc` plus back-to-rendered controls in the source view.

Current limitation:

- rendered-document, search-results, and recent-results still use existing controllers for content rendering; `markdown-source` is the first manage-only mounted main-view module.

## Context Panel Toolbar

The context panel toolbar owns switching between hosted views inside the context/info panel.

Examples:

- metadata
- references
- validation
- change history
- future selected-document context views

This toolbar belongs inside the context panel.
It should render available, unavailable, disabled, and access-blocked hosted views from the same hosted-view capability projection used by the panel host.

Target owner:

- current owner: `docs-viewer-info-panel-renderer.js`
- current controller: `docs-viewer-info-panel-controller.js`
- current hosted-view lifecycle owner: `docs-viewer-info-panel-host.js`

## Naming Notes

Use:

- "context panel" when describing the broader role. The current implementation may keep `infoPanel` names until a focused rename is worth the churn.
- "main view" for the central panel that can host rendered documents, search results, recent results, and future editor views.
- "document" only when the active view or controller specifically owns rendered document payload behavior.
- "toolbar" only when referring to one of the named toolbar surfaces in this document.
- "row" for layout only, not for ownership.
