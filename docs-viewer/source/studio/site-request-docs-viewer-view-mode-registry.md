---
doc_id: site-request-docs-viewer-view-mode-registry
title: Docs Viewer View And Mode Registry
added_date: 2026-06-17
last_updated: 2026-06-17
parent_id: change-requests
viewable: true
---
# Docs Viewer View And Mode Registry

## Request

Implement a central Docs Viewer runtime registry that defines the available views and the display modes that belong to each view.

The registry should be the source of truth for:

- which panels exist
- which views exist in each panel
- which display modes exist inside a view
- which route/access context can use each view or mode
- which runtime lifecycle implements each view or mode
- which toolbar actions are rendered because a view or mode exists
- which public-scope display controls are shown by a route
- which existing management actions remain available outside view/mode action derivation

Runtime code still provides the implementation.
Config never makes a feature real by itself: if a view or mode has no registered lifecycle, it resolves unavailable.
Runtime code also should not expose user-facing controls by itself: if a view or mode is omitted from the registry, related UI actions are not rendered and direct requests are rejected.
Public route shells should be mount points and route-identity declarations only, not behavior definitions.

## Target Model

The top-level model is:

- panel: a region of the Docs Viewer shell, such as `index`, `main`, or `info`
- view: the broad kind of surface hosted by a panel, such as `rendered-document`, `search-results`, `recent-results`, future `node-tree`, or future `movie`
- display mode: an internal mode of a view, such as rendered HTML or Markdown source inside the document view
- action: a toolbar command derived from an available view or display mode

Markdown source is a document display mode inside the document view.
It is not a peer main view.

## Registry Shape

Use a single normalized registry shape for built-in, route-provided, and management-provided records.

Example target shape:

```js
{
  panels: [
    {
      id: "main",
      defaultView: "rendered-document",
      views: [
        {
          id: "rendered-document",
          label: "Document",
          kind: "document",
          access: "public",
          modes: [
            {
              id: "rendered-document",
              label: "Rendered document",
              access: "public"
            },
            {
              id: "markdown-source",
              label: "Markdown source",
              access: "manage",
              module: "repo:markdown-source",
              action: {
                id: "markdown-source",
                label: "Markdown source",
                icon: "☰"
              }
            }
          ]
        },
        {
          id: "search-results",
          label: "Search results",
          kind: "results",
          access: "public"
        },
        {
          id: "recent-results",
          label: "Recently added",
          kind: "results",
          access: "public"
        }
      ]
    }
  ]
}
```

The exact JavaScript object can differ, but it must preserve the hierarchy:

```text
panel -> view -> display mode -> action
```

Do not maintain separate hardcoded lists for mode records and toolbar buttons.
Toolbar buttons should be projected from available registry records.

## Implementation Direction

Create a central shared owner for registry normalization and lookup.

Expected owner:

- `site/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js`

This owner should:

- normalize built-in public-safe view records
- merge management-supplied view and mode records when the management entrypoint starts the app
- merge route-config records where route config is allowed to contribute records
- apply access and availability checks
- expose list/resolve helpers for panel views
- expose list/resolve helpers for display modes under a view
- expose available toolbar actions derived from available modes

Existing modules should then consume the registry:

- `docs-viewer-panel-layout.js` should read panel/view availability from the registry rather than from an independent hosted-view list.
- `docs-viewer-main-view-host.js` should resolve true main views through the registry.
- `docs-viewer-document-display-mode-host.js` should resolve modes under the active document view through the registry.
- `docs-viewer-management-document-actions-renderer.js` should render `Markdown source` from available mode actions rather than hardcoding the button.
- `docs-viewer-management-actions.js` should request the action target supplied by the rendered button or registry record.
- Public route shells such as `/library/` and `/analysis/` should stop carrying display decisions such as search label, search placeholder, visible controls, or mode/action availability. Move those values into route config, UI text config, or the view/mode registry as appropriate.

Management toolbar actions that are not view or mode actions must remain managed by the management toolbar/action workflow.
Do not accidentally convert broad management commands into document-mode actions.
Existing management functions that must continue to work include:

- Actions menu
- New
- Import
- Delete
- Settings
- Rebuild
- Publish
- New Scope
- Delete Scope
- viewability controls such as Show / non-viewable
- scope selector
- theme toggle

Shell-owned route data should be limited to:

- the root mount element
- route identity, such as `data-route-id`
- route config discovery, such as `data-route-config-url`
- no-JavaScript fallback content

If a shell attribute controls what the Docs Viewer displays, it should be treated as migration debt for this request and moved into the registry/config layer before the request is complete.

## Required Behavior

When `markdown-source` exists in the registry and management access is active:

- the Markdown source button is rendered
- clicking it requests the `markdown-source` document display mode
- the root state projects `data-document-display-mode="markdown-source"`
- returning from source projects `data-document-display-mode="rendered-document"`
- the main view remains the document view

When `markdown-source` is omitted from the registry:

- no Markdown source button is rendered
- direct requests for `markdown-source` are rejected as unavailable
- source-editor runtime is not loaded because no available mode references it

When `markdown-source` is present but its lifecycle cannot be loaded:

- the mode resolves unavailable or fails visibly
- no broken active toolbar button should remain usable
- public routes must not import source-editor runtime

When access is public read-only:

- management-only modes are unavailable
- management-only action buttons are absent
- public routes still render the document view in `rendered-document` mode

## Migration Steps

1. Add the central registry module and move built-in view/mode declarations into it.
2. Update app composition to create one registry instance and pass it to panel, main-view, document-mode, info-panel, and management renderers.
3. Move `markdown-source` from a separate management display-mode list into the central registry contribution passed by the management entrypoint.
4. Replace hardcoded `Markdown source` action rendering with registry-derived mode actions.
5. Keep route-config records declarative; route config may declare availability/capability metadata but must not become an arbitrary module loader.
6. Move public shell display attributes, including search labels/placeholders and control visibility flags, into route config, UI text config, or the registry.
7. Preserve the management toolbar/action workflow for commands that are not view or mode actions, especially New Scope and Delete Scope.
8. Delete compatibility lists, duplicated record shapes, and migrated shell display attributes once call sites read from the central registry/config layer.
9. Update focused tests so they assert registry-driven absence/presence and preserved management actions instead of testing hardcoded button strings only.

## Acceptance Checks

- Public `/library/` and `/analysis/` render without management action buttons and without source-editor imports.
- Management `/docs/?scope=studio&mode=manage` renders the Markdown source action only when the registry includes the mode.
- Clicking Markdown source changes document display mode, not main view.
- Removing the `markdown-source` registry contribution removes the button and rejects direct mode requests.
- Public route shells do not contain view, mode, action, search-label, search-placeholder, or visible-control decisions.
- Existing management toolbar actions still render and execute through their current workflows, including New Scope and Delete Scope.
- Existing static import boundary tests still prove public entrypoints do not import management modules.
- `bin/site-validate` passes after any public runtime file changes.
