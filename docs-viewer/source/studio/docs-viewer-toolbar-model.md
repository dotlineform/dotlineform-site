---
doc_id: docs-viewer-toolbar-model
title: Toolbar Model
added_date: 2026-05-31
last_updated: 2026-07-14
summary: Placement and ownership rules for viewer, active-main-view, management, and context-panel controls.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Toolbar Model

This document answers one question: where should a Docs Viewer control live?

The placement owner does not decide whether a control is available or what operation it performs. The view registry projects eligibility; focused renderers place controls; controllers and action definitions own behaviour.

## Top Bar

```text
top bar
  +-- viewer toolbar
  +-- active main-view toolbar
  +-- manage toolbar
```

The top bar is a responsive layout container. It provides ordered mounts and may wrap whole toolbar groups on narrow screens. It owns no commands.

## Viewer Toolbar

Use the viewer toolbar for collection-reading and top-level index-view selection controls that are not tied to the selected document or a write workflow.

Current examples are search, recently added, and the index-view toggle. Panel-local collapse and expand controls remain in index-panel chrome. A control can appear only on manage routes and still belong here when its purpose is changing the reading surface rather than performing management.

Owner: `site/docs-viewer/runtime/js/shared/docs-viewer-viewer-toolbar-renderer.js`

## Main-View Toolbar

Use the main-view toolbar for controls belonging to the active central view or its current display mode.

For `rendered-document`, this includes its breadcrumb, info/bookmark controls, and manage-only document actions such as edit or Markdown source. Mode-specific controls such as source save remain here because the mode is owned by the document view.

The shared renderer creates the public-safe surface. The manage entrypoint composes eligible manage-owned document controls into the same action mount.

Owners: `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js` and `docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js`

## Manage Toolbar

Use the manage toolbar for scope-wide, write, workflow, and local-administration commands: the Actions menu, scope selection, import, rebuild, publish, export, settings, and scope lifecycle.

Its mount exists only when route access allows management UI. Individual operations remain capability-gated and server-authorized.

Owner: `docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js`

## Context Panel Chrome

The info/context panel owns only panel chrome such as status and close. The outside document or mode context chooses the hosted info view; do not add an internal toolbar merely to switch context.

A hosted view may render controls inside its own body when they operate on that view's content. Those are view UI, not top-bar controls.

## Placement Test

1. Does it change collection reading or select the active index view? Put it in the viewer toolbar.
2. Does it resize, collapse, or otherwise operate on one panel? Put it in that panel's chrome.
3. Does it act on the active main view, selected document, or document mode? Put it in the main-view toolbar.
4. Does it start a scope-wide, write, import/export, or local-admin workflow? Put it in the manage toolbar.
5. Does it operate only inside one hosted view? Let that view render it inside its mount.

Do not choose placement based on which module currently has convenient DOM access.

## Weak Spots

- The main-view toolbar is composed by shared and manage-owned renderers, so ordering must be projected deliberately rather than left to incidental DOM insertion.
- Some commands appear in more than one surface, such as a direct shortcut plus the Actions menu. They must resolve the same action definition and handler.
- Responsive layout should wrap toolbar groups before interleaving unrelated controls.
- Visibility, pressed state, dirty state, and busy state still come from focused controllers; the toolbar model is not a global UI-state owner.

[Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts) owns the registry, context, and lifecycle model behind these surfaces.
