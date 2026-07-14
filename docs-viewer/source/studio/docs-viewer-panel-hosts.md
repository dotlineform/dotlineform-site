---
doc_id: docs-viewer-panel-hosts
title: Panel Hosts
added_date: 2026-05-28
last_updated: 2026-07-14
summary: Stable panel, view, mode, control, context, lifecycle, and extension model for Docs Viewer browser modules.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Panel Hosts

Docs Viewer has three panel regions—index, main, and info—and a code-owned registry describing which views, modes, and controls may appear in them.

The app shell owns regions and mount points. Registries own definitions and eligibility. Hosts own switching and lifecycle. A hosted module owns only the UI inside its assigned mount.

## The Model

```text
shared definitions + entrypoint contributions
                    |
                    v
             view registry
       app kind + route feature
       + capability + route policy
                    |
                    v
       panel layout / document-view coordinator
                    |
                    v
          index, main or info host
                    |
                    v
        renderer or lifecycle module in its mount
```

Route config may enable features and hide known ids. It cannot define views, load arbitrary modules, or widen app/capability access.

## Views, Modes, Controls, And Actions

| concept | meaning | example |
| --- | --- | --- |
| View | Content occupying one panel region. | `index-tree`, `rendered-document`, `metadata-info` |
| Mode | A presentation or editing mode owned by one main view. | `markdown-source` belongs to `rendered-document` |
| Control | A visible command surface owned by a view and optionally limited to particular modes. | bookmark, info, edit, source toggle |
| Action | The operation and target/cardinality rule behind a control or menu item. | edit the primary selection, move all selected docs |

`docs-viewer-view-registry.js` owns view, mode, and control definitions and eligibility. Manage-owned `docs-viewer-action-definitions.js` separately owns action targeting. Keeping them separate prevents visual placement from becoming workflow authority.

## The Three Panels

### Index

The index panel currently renders the document tree or the manage-only graph placeholder through app-shell/index-panel render paths. It is registry-driven for view choice and layout capability, but it is not a generic mounted-module host.

The effective view capability today is `layoutStates`:

- `index-tree`: `normal`, `collapsed`
- manage-only `index-graph` placeholder: `normal`, `collapsed`, `expanded`

Panel layout normalizes persisted state against the active view. Switching to a view that cannot expand restores a supported state instead of leaving incompatible layout behind.

`toolbar` and `toolbarView` are normalized on capability records but do not currently drive an independent mounted toolbar. Do not build documentation or extensions around them until a real consumer exists.

### Main

The main panel represents `rendered-document`, `search-results`, and `recent-results`. The main-view host owns switch validation, active-view state, context creation, toolbar projection, and optional lifecycle loading.

The model is still hybrid:

- existing document, search, recent, and report controllers render the established views
- independently loaded main-view modules can use the host lifecycle
- `markdown-source` is a manage-only display mode inside `rendered-document`, not a peer main view

The document-view coordinator keeps main view, document mode, eligible controls, and the default info view synchronized.

### Info

The info panel is the clearest hosted-view implementation. Its host loads, mounts, updates, unmounts, and disposes the active view inside a dedicated body mount while the renderer owns status and close chrome.

Current views include public-safe document metadata and the manage-only semantic token picker. The outside document/mode context chooses the info view; the info panel does not need its own view-switching toolbar.

[Info Panel](/docs/?scope=studio&doc=docs-viewer-info-panel) owns the current metadata and context-selection behaviour.

## Lifecycle

An independently hosted module may implement:

```text
load() -> mount(context) -> update(context) -> unmount(context) -> dispose(context)
```

Main views and document modes may also implement `beforeLeave(context)` to keep dirty or incomplete work from being discarded.

Use lifecycle only when the module owns mounted resources or state. Stateless rendering and projection helpers should stay stateless.

The host must localize failures: an unavailable or failed view shows a panel warning and must not prevent route boot or damage another panel.

## Context And Authority

Hosted modules receive projected context rather than importing broad runtime state. The shared context can include:

- app kind and route/service availability
- selected document and public-safe payload metadata
- canonical URL, parent trail, scope, and status label
- collection-provider reads
- a mount element and host-mediated view/mode/toolbar requests

Source-editor services are included only when the app context exposes the source service. Registration, visibility, or receiving a client handle still does not authorize a write; server endpoints remain authoritative.

Public context deliberately projects less metadata than manage/review context. A new hosted view should request the smallest context it needs rather than widening the shared object for convenience.

## Adding A View Or Control

1. Decide whether the change is a panel view, a mode inside an existing view, a control, or a separate action.
2. Register the definition in shared code only when it is public-safe; otherwise contribute it from the manage or review entrypoint.
3. Declare its app kinds, route features, and required backend capabilities.
4. Use a renderer key for shell-owned presentation or a lazy lifecycle for an independently mounted module.
5. Keep handlers and live busy, dirty, pressed, and disabled state in the focused controller or view—not in the registry record.
6. If management code is involved, preserve the public entrypoint import boundary.

This is a repo module-hosting pattern, not a plugin system. It has no package manifests, arbitrary module URLs, third-party sandbox, or automatic asset loading.

## Why This Structure Exists

- Panel regions stay stable while their content changes.
- Code-owned definitions make executable extensions allowlisted and testable.
- Entrypoint contributions keep manage/review modules out of public routes.
- Explicit context makes data and service dependencies visible.
- Host-mediated switching and cleanup stop modules from mutating unrelated chrome or global layout.
- Separate controls and actions let toolbar, menu, context-menu, and selection surfaces share operation rules without sharing DOM ownership.

## Weak Spots

- The implementation is intentionally hybrid: info views use the full lifecycle, main views mix lifecycle modules with established controllers, and index views are shell renderers.
- Adding a control can still touch a definition, renderer, event binding, handler, and capability projection. The registry is not a complete action framework.
- `toolbar` and `toolbarView` capability fields are normalized but currently unused.
- The `index-graph` view proves layout switching but is not a real graph or evidence of a generic visualization extension point.
- The shared hosted-view context is broader than some modules need and should be narrowed when a stable per-view contract becomes clear.
- “Info panel” and “context panel” describe the same current region; renaming code without a functional reason would create churn.

## Code Pointers

- definitions and eligibility: `site/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js`
- panel state and layout: `site/docs-viewer/runtime/js/shared/docs-viewer-panel-layout.js`
- main/mode/info coordination: `site/docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js`
- main and info hosts: `site/docs-viewer/runtime/js/shared/docs-viewer-main-view-host.js` and `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js`
- public-safe context projection: `site/docs-viewer/runtime/js/shared/docs-viewer-view-context.js`
- manage definitions: `docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js`

[Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model) owns where eligible controls are placed. [Runtime Architecture](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) owns public/manage/review delivery and authority.
