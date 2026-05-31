---
doc_id: docs-viewer-toolbar-model
title: Docs Viewer Toolbar Model
added_date: 2026-05-31
last_updated: 2026-05-31
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
- viewer toolbar: read, navigation, search, and layout/context controls
- manage toolbar: management, write, and admin controls
- document toolbar: controls for the current selected document
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

- scope selector when the route allows scope query
- recently added control
- search input
- index view toggle
- context/info panel toggle

The index view toggle and context/info panel toggle are layout/view controls.
They should not be treated as management actions, even if some hosted views or index modes are only available in management-enabled routes.
They render as a panel-controls group after the search control so they remain visibly part of the viewer toolbar.

Top-bar layout owner: `docs-viewer-top-bar-renderer.js`

## Manage Toolbar

The manage toolbar owns controls that imply management mode, write capability, or local admin behavior:

- Actions menu
- create, import, edit, delete, settings, rebuild, and scope actions
- viewability controls such as Show/hidden
- management status affordances when needed

The manage toolbar may sit next to the viewer toolbar in the same top bar.
Its presence must still depend on route access and management UI availability.

Owner: `docs-viewer-manage-toolbar-renderer.js`

## Document Toolbar

The document toolbar owns controls for the current selected document.

Example controls:

- bookmark toggle
- document status pills
- future document-specific actions that are not global viewer layout controls

Owner: `docs-viewer-document-toolbar-renderer.js`

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
- "toolbar" only when referring to one of the named toolbar surfaces in this document.
- "row" for layout only, not for ownership.