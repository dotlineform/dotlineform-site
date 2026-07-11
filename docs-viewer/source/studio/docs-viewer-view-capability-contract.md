---
doc_id: docs-viewer-view-capability-contract
title: View Capability Contract
added_date: 2026-05-29
last_updated: 2026-07-11
ui_status: ""
summary: Current hosted-view layout capability fields and their route-config, registry, and panel-layout consumers.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer View Capability Contract

This is the model for Docs Viewer panel views, layout rules, and extensible view-specific UI capabilities. The implementation is in the config/runtime path:

- capabilities normalize from hosted views,
- panel layout uses the active index view’s capabilities, and
- management-enabled Docs Viewer routes get a placeholder graph view plus a single toolbar toggle.

This contract is limited to current hosted-view layout capabilities such as supported index-panel states and toolbar presence. It does not own the planned combined view, document-mode, or toolbar-control eligibility model. That work is code-owned by the Phase 4 [View, Mode, And Control Projection](/docs/?scope=studio&doc=site-request-docs-viewer-view-mode-registry) task; browser route config cannot invent executable definitions or widen app/capability access.

## Purpose

Docs Viewer panels should not hardcode behavior for individual views such as `index-tree`.
View behavior should come from one durable configuration contract so built-in views and future optional views can declare what they support.

The rule is view-specific, not panel-specific. The index panel can host multiple views over time, and each hosted view may need different layout states and chrome.

## Contract Location

Current route config lives in:

- `docs-viewer/config/routes/docs-viewer-routes.json`

Runtime normalization currently flows through:

- `site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-hosted-views.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-view-state.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-panel-layout.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-index-panel.js`

Built-in hosted-view defaults may still be defined in code, but they should use the same normalized record shape as config-provided hosted views.
The renderer should consume projected controls and should not know why a capability is available.

## Hosted View Shape

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

Example placeholder graph index view:

```json
{
  "id": "index-graph",
  "label": "Index graph",
  "panel": "index",
  "access": "manage",
  "availability": "available",
  "renderer": "index-placeholder",
  "placeholder_text": "Graph index placeholder",
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

`docs-viewer-route-config.js` normalizes hosted-view capability records from route config.

`docs-viewer-hosted-views.js` carries the normalized capability object for built-in and config-provided views.

`docs-viewer-view-state.js` exposes the active view id for each panel.
It does not decide view-specific behavior by id.

`docs-viewer-panel-layout.js` resolves the active index view and passes its capabilities to index-panel projection.

`docs-viewer-index-panel.js` projects available state transitions from capabilities.
For example, when `layout_states` is `["normal", "collapsed"]`, it should hide or disable the full expand control and prevent `expanded` from becoming the persisted state.

`docs-viewer-index-panel-renderer.js` renders the projected layout controls and placeholder/tree visibility.
`docs-viewer-management-actions-renderer.js` renders the management toolbar index-view toggle from panel-layout projection.
It does not decide layout-state availability.

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

For the first implementation, `docs-viewer/config/routes/docs-viewer-routes.json` adds a placeholder `index-graph` view to the management route.
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

Management-enabled Docs Viewer routes expose a small index-view toggle in the management toolbar, immediately to the left of the Actions button.
The toggle is the practical test surface for the config-driven view contract.

Initial implementation:

- available only in management-enabled Docs Viewer routes
- switches the active index view between `index-tree` and `index-graph`
- does not appear on public `/library/` or `/analysis/` routes
- uses hosted-view access and availability projection rather than hardcoded route checks
- restores unsupported layout state when switching views; for example, switching from expanded `index-graph` back to `index-tree` should return the index panel to `normal`
- keeps the tree view as the default index view
- uses a round icon pill: folder for tree view and web for graph view
- may use placeholder graph content only; no real graph layout is currently implemented.

The toggle lives in Docs Viewer app-shell management toolbar chrome, not inside the tree renderer or index panel body.
This keeps view selection separate from tree rendering and allows future index views to add their own toolbar capabilities.
