---
doc_id: site-request-docs-viewer-view-mode-registry
title: Docs Viewer View And Mode Registry
added_date: 2026-06-17
last_updated: 2026-06-18
parent_id: change-requests
viewable: true
---
# Docs Viewer View And Mode Registry

## Request

Centralize Docs Viewer decisions about views, display modes, and view toolbar controls.

This request is not a rewrite of Docs Viewer architecture.
It is a targeted cleanup of decisions that are currently spread across route config, hosted-view records, display-mode setup, toolbar renderers, and management-only modules.

The first implementation should keep current behavior but make the source of truth easier to find and change.

## Problem

Docs Viewer already has a view/mode structure:

- a panel hosts a view
- a view can have display modes
- the active view or mode should determine which toolbar controls are visible
- public and manage access decide which views, modes, and controls are available
- scope config should be able to hide additional public controls for that scope

Markdown source is a document display mode inside the document view.
It is not a peer main view.
The current code can support this, but the decisions are not centralized.
That makes simple changes expensive, such as:

- make `bookmark` manage-only everywhere
- hide both `bookmark` and `info` on the public `moments` scope
- add a new mode to an existing view and define its toolbar controls without adding view-specific conditionals

## Scope And Authority

There is no higher authority than `/docs/` in manage mode.
The `/docs/` route can inspect every scope with management access and should see the full views, modes, and controls available to the active view/mode.

Public scopes get the public presentation their config allows.
In practice, a public scope has one public route:

- `library` -> `/library/`
- `analysis` -> `/analysis/`
- `moments` -> `/moments/`

Do not design this registry around one scope being surfaced through multiple public routes.
`/moments-copy/` could be hardcoded to use the `moments` scope, but that is not a supported product requirement and should not shape this work.

## Current Decision Points

The implementation should not start with a new audit.
The decisions that need to be centralized are currently split across these code areas:

### Panel Views

Current owner:

- `site/docs-viewer/runtime/js/shared/docs-viewer-hosted-views.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-composition.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-panel-layout.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-host.js`

Current behavior:

- built-in panel views are declared in `createDocsViewerBuiltInHostedViews()`
- route-config hosted-view records are merged in app composition
- panel layout and main-view host resolve views through the hosted-view registry

Required change:

- keep this behavior but make it part of the same view/mode/control availability projection used by toolbar controls
- do not create a second, parallel list of supported main views

### Document Display Modes

Current owner:

- `site/docs-viewer/runtime/js/shared/docs-viewer-document-display-mode-host.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js`
- `docs-viewer/runtime/js/management/docs-viewer-manage.js`

Current behavior:

- `rendered-document` is a built-in display mode inside the display-mode host
- `markdown-source` is supplied separately through the management entrypoint
- display modes are not currently part of the panel hosted-view registry

Required change:

- register document display modes under the document view in the central projection
- keep `markdown-source` management-only
- keep direct mode requests rejected when the mode is unavailable in the current access context

### Document View Toolbar Controls

Current owner:

- `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-bookmarks.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js`
- `docs-viewer/runtime/js/management/docs-viewer-management.js`
- `docs-viewer/runtime/js/management/source-editor/source-editor.js`

Current behavior:

- `bookmark` and `info` buttons are created in the shared main-view renderer
- bookmark visibility is controlled by bookmark runtime state
- info visibility is controlled by info-panel/controller state
- `edit`, `markdown-source`, and `save-markdown-source` are injected by the management document-actions renderer
- management runtime separately hides/disables edit/source/source-save based on selected document, busy state, and active Markdown mode
- source-editor runtime separately hides bookmark/info while Markdown source is active

Required change:

- define document-view toolbar controls in one central projection: at minimum `bookmark`, `info`, `edit`, `markdown-source`, and `save-markdown-source`
- keep each existing runtime handler where it is unless moving the handler is mechanically simpler
- move visibility eligibility into the projection layer so adding or removing a control does not require hardcoded view-specific show/hide branches
- preserve runtime state updates that are not pure availability decisions, such as bookmark active state, info pressed state, and disabled state while management is busy

### Shared View Registry Config And Public Shell Attributes

Current owner:

- `site/docs-viewer/runtime/js/shared/docs-viewer-viewer-toolbar-renderer.js`
- `docs-viewer/templates/public-route/index.html`
- `site/library/index.html`
- `site/analysis/index.html`
- `site/moments/index.html`
- `docs-viewer/shell/docs-viewer-shell.html`
- `site/docs-viewer/config/views/docs-viewer-view-registry.json`
- `site/docs-viewer/config/defaults/docs-viewer-public-config.json`
- `site/docs-viewer/config/routes/docs-viewer-public-routes.json`

Current behavior:

- search placeholder and aria label are shell data attributes
- public routes map one-to-one to public scopes through route config
- there is no shared browser-visible config that defines supported views, modes, and toolbar controls
- public runtime and manage mode both need to know which public-safe views and modes are defined

Required change:

- add `site/docs-viewer/config/views/docs-viewer-view-registry.json` as the shared source of truth for public-safe view, mode, toolbar-control, and public toolbar-policy definitions
- have both public runtime and manage mode read this same `site/` config file
- keep management-only view, mode, and control contributions in `docs-viewer/runtime/js/management/` and merge them only when manage mode starts
- add only the minimum policy fields needed for global public toolbar policy and per-scope public toolbar policy
- do not put public-safe view/mode/control definitions in `docs-viewer/` only, because public runtime cannot depend on manage-mode files
- do not require the browser to read `docs-viewer/config/scopes/docs_scopes.json`
- avoid adding display decisions to public route shells
- keep public routes one-to-one with public scopes

### Tests

Current owners that should be updated with the implementation:

- `docs-viewer/tests/python/test_docs_viewer_service.py`
- `docs-viewer/tests/smoke/public_docs_viewer_readonly.py`
- `docs-viewer/tests/smoke/docs_viewer_service_manage.py`

Required change:

- replace assertions that only prove hardcoded button strings with assertions that prove registry/config-driven presence and absence
- keep static import boundary assertions proving public entrypoints do not import management modules
- add focused coverage for global public policy hiding `bookmark`
- add focused coverage for `moments` public policy hiding `bookmark` and `info` without affecting `/docs/?scope=moments`

## Target Model

Introduce a small central runtime owner for view/mode/control availability.
The exact file and shape can follow existing Docs Viewer patterns, but the model should preserve these relationships:

```text
panel -> view -> display mode
view or display mode -> toolbar controls
toolbar control -> runtime handler or target
global public policy -> public defaults
scope public policy -> public scope-specific overrides
management contribution -> manage-only modes and controls
manage mode -> full active-view controls unless explicitly restricted
```

The registry should answer:

- is this view available here?
- is this mode available here?
- which toolbar controls should this active view/mode render here?
- is this control available, hidden, disabled, or relabelled by global public policy or scope public policy?
- what handler or target should run when this control is invoked?

Config can hide or narrow registered controls.
Config must not invent executable handlers or module loaders.
Runtime code still provides the implementation.
The shared `site/` registry can name a lifecycle or handler id, but the JavaScript runtime must still own the actual implementation.
Public runtime must ignore or reject unavailable management-only modes such as Markdown source.

## Toolbar Policy

The first useful policy layers are:

1. built-in registered defaults
2. management contributions, when manage mode is active
3. global public defaults
4. scope public overrides
5. active view/mode toolbar definition

Current behavior should be expressible as config:

- only manage mode sees the manage toolbar and Actions menu
- all scopes can use the docs-view toolbar shape for the active view/mode
- public scopes currently see public document-view controls such as `bookmark` and `info`
- manage mode sees management document-view controls such as `edit` and `markdown-source`

New behavior should also be expressible as config:

- hide `bookmark` for all public scopes
- hide `bookmark` and `info` for the public `moments` scope
- if every docs-view toolbar control is hidden for a public scope, do not render an empty docs-view toolbar
- still show the `moments` scope with full active-view controls in `/docs/` manage mode

Initial shared registry config shape:

```js
{
  panels: {
    main: {
      views: {
        "rendered-document": {
          modes: {
            "rendered-document": { access: "public" }
          },
          toolbarControls: ["bookmark", "info"]
        }
      }
    }
  },
  controls: {
    bookmark: { access: "public", handler: "runtime:bookmark-toggle" },
    info: { access: "public", handler: "runtime:toggle-info-panel" }
  },
  publicToolbarPolicy: {
    controls: {
      bookmark: { hidden: true }
    }
  },
  scopes: {
    moments: {
      publicToolbarPolicy: {
        controls: {
          bookmark: { hidden: true },
          info: { hidden: true }
        }
      }
    }
  }
}
```

## Implementation Direction

Implementation steps:

- add `site/docs-viewer/config/views/docs-viewer-view-registry.json`
- add `site/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js`
- have public boot and manage boot load the shared `site/` registry config
- have manage boot merge management-only contributions for `edit`, `markdown-source`, and `save-markdown-source`
- add a central lookup/projection layer used by existing modules for availability decisions
- migrate document-view controls first: `bookmark`, `info`, `edit`, `markdown-source`
- keep management toolbar commands such as Actions, New, Import, Delete, Settings, Rebuild, Publish, New Scope, Delete Scope, scope selector, and theme toggle in their existing workflow unless they are already controls for an active view/mode
- keep route config declarative; it may carry policy but must not become a plugin/module-loader surface
- move public shell display attributes into config where they are part of the same availability/visibility decision

## Required Behavior

- Current public scopes continue to render as they do now unless config says otherwise.
- Current manage mode continues to render management controls.
- Public runtime and manage mode both read the same shared `site/` view registry config.
- Public runtime rejects or omits unavailable management-only modes such as Markdown source.
- The document-view toolbar is projected from registry/config rather than hardcoded per control.
- Global public policy can hide `bookmark` across public scopes.
- `moments` public policy can hide both `bookmark` and `info`, causing `/moments/` to render no docs-view toolbar if no controls remain.
- `/docs/?scope=moments` can still show the `moments` scope with full controls for the active view/mode.
- Adding a new view or mode should require adding its supported controls to the registry/config, not adding scattered toolbar visibility conditionals.

## Acceptance Checks

- Public `/library/` and `/analysis/` render without management action buttons and without source-editor imports.
- Document-view toolbar controls are rendered from central projection, including `edit`, `bookmark`, `info`, and `markdown-source`.
- Global public policy can hide `bookmark` from public scopes without adding a hardcoded runtime branch.
- Public `moments` policy can hide `bookmark` and `info` so `/moments/` has no empty docs-view toolbar.
- `/docs/?scope=moments` still shows full active-view controls.
- Clicking Markdown source changes document display mode, not main view.
- Toolbar controls can be hidden by global or scope policy without view-specific runtime conditionals.
- Existing management toolbar actions still render and execute through their current workflows, including New Scope and Delete Scope.
- Existing static import boundary tests still prove public entrypoints do not import management modules.
- Tests assert registry/config-driven absence and presence instead of hardcoded button strings only.
- `bin/site-validate` passes after any public runtime file changes.
