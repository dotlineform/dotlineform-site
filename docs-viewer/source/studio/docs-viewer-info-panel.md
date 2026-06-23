---
doc_id: docs-viewer-info-panel
title: Info Panel
added_date: 2026-06-23
last_updated: 2026-06-23
parent_id: docs-viewer
viewable: true
---
# Info Panel

The Docs Viewer info panel is the secondary panel used for context-specific assistance beside the active document surface.

It is intentionally small:

- the shell title is `info`
- the shell does not contain its own view-switching toolbar
- the active outside context chooses which hosted view appears in the panel
- hosted views receive a projected context rather than reading broad app state directly

This keeps the panel usable in both public read-only routes and the local manage route without letting public routes inherit manage-only controls, service handles, or implementation assumptions.

## Current Views

Current hosted views:

- `metadata-info`: selected-document metadata
- `semantic-token-picker`: manage-only source-editor assistance for semantic-reference token insertion

Current context selection:

- rendered document mode selects `metadata-info`
- Markdown source mode selects `semantic-token-picker`

The panel should not add an internal tab bar or local buttons to switch between these views.
The owning outside context should project the active view because the outside context knows whether the user is reading a rendered document, editing Markdown source, or working in another future surface.

## Hosting Model

The info panel has three small shared owners:

- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js` renders the shell
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js` owns open/close state and shell lifecycle wiring
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js` mounts and updates the active hosted view inside the shell body

The host treats panel views like small modules with the same basic lifecycle shape used elsewhere in Docs Viewer:

- `mount(context)`
- `update(context)`
- `unmount(context)`
- `dispose(context)`

The shell is not the owner of feature behavior.
It provides a stable mount point and lifecycle boundary.
The hosted view owns its own rendering and any feature-specific interaction.

## Hosted-View Context

Shared hosted-view context projection lives in `site/docs-viewer/runtime/js/shared/docs-viewer-view-context.js`.

The context is deliberately explicit.
Hosted views should receive only the data and services they need, such as:

- selected document record
- selected document payload metadata
- route access flags
- viewer scope
- canonical URL when appropriate
- parent trail when appropriate
- status display label when appropriate
- manage-only source-editor services only when the route allows management

Public-safe hosted views must not reach for management clients, backend probes, write-capable service handles, local filesystem paths, or manage-only runtime modules.
Manage-only views may receive manage-only service adapters, but their availability should still be projected by route/view context rather than inferred from loose global state.

## Metadata Info View

`metadata-info` is implemented by `site/docs-viewer/runtime/js/shared/docs-viewer-metadata-info-view.js`.

It renders one selected-document metadata summary with the document title as the heading.
The visible field list is a renderer policy, not a payload-pruning side effect.
This distinction matters because public routes may receive or cache metadata that is useful to the runtime but should not be shown in the public info panel.

Current field policy:

| Route context | Visible fields |
| --- | --- |
| Public read-only | `Summary`, `Updated` |
| Manage/local | `Doc ID`, `Summary`, `Date`, `Added`, `Updated` |

The view chooses the field policy from `context.access.publicReadOnly`.
Public route tests should assert that public metadata does not leak manage-oriented fields such as `Doc ID`, `Date`, `Added`, `Scope`, `Parent path`, `UI status`, `Visibility`, or `Route`.

Manage/local routes can show more operational metadata because they are local authoring and maintenance surfaces.
Even there, the current info panel is intentionally compact; richer metadata editing belongs in the metadata modal and management workflows, not in the passive info panel.

## Public And Manage Separation

Public and manage differences enter through route access and hosted-view context, not through duplicated panel shells.

Public routes:

- use public route config and public UI text
- run as read-only document viewers
- expose only public-safe hosted views and public-safe metadata fields
- must not receive management services or write-capable adapters

The local `/docs/` manage route:

- uses manage/local route config and manage UI text
- can receive management service adapters after route capability checks
- can host manage-only views such as `semantic-token-picker`
- can show compact operational metadata useful while authoring

The same shell and host can serve both environments because the boundary is enforced by context projection and hosted-view registration.
Do not fork the info panel shell just to change public/manage field visibility.

## Semantic Token Picker

`semantic-token-picker` is a manage-only hosted view used by the Markdown source editor.

It lives under `docs-viewer/runtime/js/management/source-editor/` because it belongs to the manage source-editor feature, not to the public/shared info panel.
The info panel only provides the mount point.

The source editor supplies a narrow adapter for:

- reading the current selection
- subscribing to selection changes
- replacing the current selection or caret range
- returning focus to the source editor

The picker uses generated browser-safe semantic-target data and the semantic-reference registry.
It does not own source save/rebuild behavior, document mode switching, or rendered-document reload.

## Implementation Rules

Use these rules when changing or adding info-panel behavior:

- keep the shell simple and view-agnostic
- choose the active panel view from outside context
- pass explicit hosted-view context instead of broad app state
- make public/manage rendering differences deliberate field or capability policies
- keep public-safe views free of manage services and local-only runtime modules
- place manage-only hosted views under manage ownership, even when they mount inside the shared panel shell
- update focused smoke tests when the visible public/manage field policy changes

Related documents:

- [Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model)
- [Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership)
- [Config](/docs/?scope=studio&doc=config-docs-viewer)
