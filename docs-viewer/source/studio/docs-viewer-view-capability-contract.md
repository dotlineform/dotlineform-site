---
doc_id: docs-viewer-view-capability-contract
title: Docs Viewer View Capability Contract
added_date: 2026-05-29
last_updated: 2026-05-29
ui_status: in-progress
parent_id: docs-viewer
viewable: true
---
# Docs Viewer View Capability Contract

**Status: to be implemented.**

This document records the intended model for Docs Viewer panel views, layout rules, and extensible view-specific UI capabilities.
The contract is not implemented yet.

Implement this in the config/runtime path rather than special-casing tree behavior: capabilities normalize from hosted views, panel layout uses the active index view’s capabilities, and manage mode gets a placeholder graph view plus a small switcher.

## Purpose

Docs Viewer panels should not hardcode behavior for individual views such as `index-tree`.
View behavior should come from one durable configuration contract so built-in views and future optional views can declare what they support.

The immediate reason for this contract is the index panel:

- the current `index-tree` view should support normal width and collapsed width
- the current `index-tree` view should not expose full-width expanded mode
- a manage-only placeholder `index-graph` view should be added so the capability contract can be tested against a second index view
- future index views such as a richer `index-graph` may support expanded mode, additional toolbars, filters, or alternate empty/loading states

The rule is view-specific, not panel-specific.
The index panel can host multiple views over time, and each hosted view may need different layout states and chrome.

## Contract Location

The durable source of truth should be the Docs Viewer route/view config.
It does not need to be user-editable, but it should live in one predictable config shape so view rules can be reviewed and changed without editing renderer code.

Current route config lives in:

- `docs-viewer/config/routes/docs-viewer-routes.json`

Runtime normalization currently flows through:

- `docs-viewer/runtime/js/docs-viewer-route-config.js`
- `docs-viewer/runtime/js/docs-viewer-hosted-views.js`
- `docs-viewer/runtime/js/docs-viewer-view-state.js`
- `docs-viewer/runtime/js/docs-viewer-panel-layout.js`
- `docs-viewer/runtime/js/docs-viewer-index-panel.js`

Built-in hosted-view defaults may still be defined in code, but they should use the same normalized record shape as config-provided hosted views.
The renderer should consume projected controls and should not know why a capability is available.

## Proposed Hosted View Shape

Hosted views should carry a `capabilities` object.
The object should be optional and defaulted during normalization.

Example tree index view:

```json
{
  "id": "index-tree",
  "label": "Index tree",
  "panel": "index",
  "access": "public",
  "availability": "available",
  "capabilities": {
    "layout_states": ["normal", "collapsed"],
    "toolbar": false
  }
}
```

Example future graph index view:

```json
{
  "id": "index-graph",
  "label": "Index graph",
  "panel": "index",
  "access": "manage",
  "availability": "available",
  "module": "/docs-viewer/runtime/js/index-graph-view.js",
  "capabilities": {
    "layout_states": ["normal", "collapsed", "expanded"],
    "toolbar": true,
    "toolbar_view": "index-graph-toolbar"
  }
}
```

## Capability Fields

Initial fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `layout_states` | string array | Allowed panel layout states for the view. For index views this controls whether collapse, restore, and full expanded mode are available. |
| `toolbar` | boolean | Whether the panel should expose a view-specific toolbar region. |
| `toolbar_view` | string | Optional hosted-view id or renderer key for toolbar content. |

Access rules remain separate from capabilities.
For the first implementation, `index-graph` should be `manage` access only so public `/library/` and `/analysis/` continue to expose only the document tree.

Initial `layout_states` values:

| State | Meaning |
| --- | --- |
| `normal` | Standard panel width with document panel visible. |
| `collapsed` | Compact index rail with document panel visible. |
| `expanded` | Full expanded index workspace that can hide document and info panels when the active view supports it. |

Future capability fields may describe:

- secondary toolbar actions
- filter regions
- minimap/legend regions
- drag/drop support
- selection behavior
- view-specific persistence keys
- route/query state participation

These should be added as explicit fields rather than inferred from a view id.

## Runtime Responsibilities

`docs-viewer-route-config.js` should normalize hosted-view capability records from route config.

`docs-viewer-hosted-views.js` should carry the normalized capability object for built-in and config-provided views.

`docs-viewer-view-state.js` should expose the active view id for each panel.
It should not decide view-specific behavior by id.

`docs-viewer-panel-layout.js` should resolve the active index view and pass its capabilities to index-panel projection.

`docs-viewer-index-panel.js` should project available state transitions from capabilities.
For example, when `layout_states` is `["normal", "collapsed"]`, it should hide or disable the full expand control and prevent `expanded` from becoming the persisted state.

`docs-viewer-index-panel-renderer.js` should only render the projected controls.
It should not contain view-specific rules.

CSS should define layouts for available states.
It should not decide whether a view is allowed to enter a state.

## Current Tree Index Rule

For `index-tree`, the intended capability contract is:

```json
{
  "layout_states": ["normal", "collapsed"],
  "toolbar": false
}
```

Behavior:

- normal state shows the tree at standard index width
- collapse changes to the compact rail
- restore returns to standard index width
- full expand is not offered
- document and info panels should not be hidden by tree-index actions

## Future Index View Rule

For the first implementation, add a placeholder `index-graph` view in manage mode.
The placeholder may render static text such as "Graph index placeholder" so the runtime can prove that the config-driven capability path works before a real graph implementation exists.

That view should explicitly opt into expanded mode:

```json
{
  "layout_states": ["normal", "collapsed", "expanded"],
  "toolbar": true,
  "toolbar_view": "index-graph-toolbar"
}
```

Behavior:

- full expand may hide document and info panels
- expanded mode can expose graph-specific controls later
- normal/collapsed behavior remains available unless the view declares otherwise
- public read-only routes should not expose `index-graph` until a separate public access decision is made

## Manage-Mode Index View Toggle

Manage mode should expose a small index-view toggle after the tree capability rule is in place.
The toggle is the practical test surface for the config-driven view contract.

Initial requirements:

- available only in management-enabled Docs Viewer routes
- switches the active index view between `index-tree` and `index-graph`
- does not appear on public `/library/` or `/analysis/` routes
- uses hosted-view access and availability projection rather than hardcoded route checks
- restores unsupported layout state when switching views; for example, switching from expanded `index-graph` back to `index-tree` should return the index panel to `normal`
- keeps the tree view as the default index view
- may use placeholder graph content only; no real graph layout is required for this implementation slice

The toggle should live in Docs Viewer app-shell or index-panel chrome, not inside the tree renderer.
This keeps view selection separate from tree rendering and allows future index views to add their own toolbar capabilities.

## Implementation Notes

The implementation should be split into testable steps:

1. Add capability normalization to hosted-view config records and built-in hosted-view defaults.
2. Pass active index-view capabilities into index-panel state projection.
3. Prevent unsupported layout states from being selected or persisted.
4. Hide the full expand control for `index-tree`.
5. Keep expanded CSS behavior available for future views that opt in.
6. Add a manage-only placeholder `index-graph` hosted view with expanded-mode capability.
7. Add a manage-only index-view toggle for switching between `index-tree` and `index-graph`.
8. Update focused index-panel module tests and route smoke expectations.

The implementation should avoid hardcoded checks such as `if viewId === "index-tree"` outside built-in default configuration.
