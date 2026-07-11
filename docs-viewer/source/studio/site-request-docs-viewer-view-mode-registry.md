---
doc_id: site-request-docs-viewer-view-mode-registry
title: Docs Viewer View, Mode, And Control Projection
added_date: 2026-06-17
last_updated: 2026-07-11
ui_status: implemented
summary: Phase 4 implementation task for code-owned Docs Viewer view, document-mode, and toolbar-control definitions and eligibility projection.
parent_id: change-requests
viewable: true
---
# Docs Viewer View, Mode, And Control Projection

## Status

Implemented as Phase 4 of [Docs Viewer Foundation Refactor Implementation](/docs/?scope=studio&doc=site-request-docs-viewer-foundation-refactor-implementation).

This task replaces the earlier proposal for a browser JSON view registry. Built-in views, document modes, controls, lifecycle implementations, and handlers will be code-owned. Route policy may hide or narrow known definitions but cannot invent modules, lifecycles, handlers, or control ids.

The implementation uses the explicit app context, service authority, provider, and route-feature inputs established in phases 1-3.

## Outcome

Create one shared normalization, lookup, and eligibility owner for:

- panel views
- document display modes registered under the document main view
- toolbar controls associated with a view or display mode

The projection combines code-owned definitions with current runtime inputs:

```text
shared definitions
+ entrypoint contributions
+ app context
+ backend capabilities
+ route feature policy
+ active view and document mode
= eligible views, modes, and toolbar controls
```

Controllers keep executable handlers and live interaction state. Renderers consume projected records.

## Scope

First slice:

- normalize and resolve built-in panel views
- normalize and resolve `rendered-document` and `markdown-source` document modes
- project `bookmark`, `info`, `edit`, `markdown-source`, and `save-markdown-source` controls
- keep manage toolbar/admin actions outside this projection
- preserve current public and manage behavior

This task does not add a generic plugin system, browser module loader, review route, new public policy, or new control behavior.

## Authority Model

Definitions answer what exists and where it belongs.

Entrypoints answer which executable contributions are available to an app installation:

- shared/public-safe definitions are imported through the shared/public graph
- manage-only definitions and lifecycles are contributed by the manage entrypoint
- a future review entrypoint may contribute only review-authorized definitions after the readiness checkpoint

App context and backend capabilities answer which known definitions are eligible.

Route feature policy may hide or narrow an eligible definition. It cannot:

- add an unknown definition id
- name a JavaScript module
- name or select an executable handler
- grant service or backend authority
- override an app-context or backend-capability denial

Active view and document mode answer which eligible controls are relevant now.

Controllers own:

- event handlers
- bookmark pressed state
- info-panel pressed/open state
- dirty state
- pending/busy state
- disabled state derived from workflow readiness
- source-editor before-leave behavior

## Target Owner

Add a small shared code owner at:

```text
site/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js
```

It owns:

- definition normalization
- duplicate/reserved-id handling
- view-to-panel lookup
- document-mode-to-view lookup
- control-to-view/mode lookup
- eligibility projection from explicit context/capability/policy inputs
- active control projection

It does not own:

- lifecycle loading or mounting
- DOM creation
- event binding
- service calls
- mutable controller state
- route-config loading

Existing hosts continue to own lifecycle behavior while consuming normalized/projection results:

- `docs-viewer-main-view-host.js`
- `docs-viewer-document-display-mode-host.js`
- `docs-viewer-info-panel-host.js`

## Definition Shape

The exact object syntax may follow current JavaScript patterns, but definitions must preserve these relationships:

```text
panel: index | main | info
view: id + panel + allowed app kinds/features/capabilities
mode: id + owner view + allowed app kinds/features/capabilities
control: id + owner view/mode + allowed app kinds/features/capabilities
```

Definitions may carry presentation metadata such as a stable label or renderer role when that metadata is code-owned and not live state.

Definitions must not carry string handler ids or arbitrary module paths. Executable functions remain in entrypoint contributions or focused controllers.

## Current Decision Points To Migrate

### Panel Views

Former decision owners included `docs-viewer-hosted-views.js` and `docs-viewer-app-composition.js`.
- `docs-viewer-panel-layout.js`
- `docs-viewer-main-view-host.js`

Migration:

- retain current built-in and entrypoint-contribution behavior
- normalize panel-view definitions through the new owner
- remove route hosted-view records so route config cannot register definitions
- do not create a second panel-view list

### Document Display Modes

Current owners:

- `docs-viewer-document-display-mode-host.js`
- `docs-viewer-management-hosted-views.js`
- `docs-viewer-manage.js`

Migration:

- register `rendered-document` under the document main view as shared/public-safe
- contribute `markdown-source` through the manage entrypoint
- resolve mode eligibility through explicit app context, features, and capabilities
- keep direct requests for unavailable modes rejected by the display-mode host
- keep Markdown source as a mode, not a peer main view

### Document Toolbar Controls

Current owners:

- `docs-viewer-main-view-renderer.js`
- `docs-viewer-bookmarks.js`
- `docs-viewer-info-panel-controller.js`
- `docs-viewer-management-document-actions-renderer.js`
- `docs-viewer-management.js`
- `source-editor/source-editor.js`

Migration:

- define `bookmark` and `info` as shared document-view controls
- contribute `edit`, `markdown-source`, and `save-markdown-source` through the manage entrypoint
- project which controls belong to the active view/mode before rendering
- preserve bookmark, info, management, and source-editor handlers in their focused owners
- preserve pressed, dirty, busy, pending, and disabled projection as live controller state
- remove old scattered eligibility branches only after all callers consume the central projection

## Route Policy

Phase 4 may normalize a route feature-policy section that hides known controls. The policy is an allowlisted narrowing layer.

Examples the model must be capable of expressing:

- hide `bookmark` on a named public route
- hide both `bookmark` and `info` on a minimal public route
- omit the toolbar mount when no projected controls remain
- keep the same scope's full eligible controls when viewed through a manage context

No new product policy is introduced by the behavior-preserving first slice. Existing whole-toolbar route policy must continue to work until it is replaced in the same slice by equivalent projected-control policy.

## Implementation Sequence

1. Add pure definition normalization and duplicate/reserved-id checks.
2. Add pure eligibility projection from app context, backend capabilities, route policy, and active state.
3. Register current shared panel views and `rendered-document` mode as code-owned definitions.
4. Move manage view, Markdown mode, and management document-control contributions to the manage entrypoint input.
5. Project shared `bookmark` and `info` controls for the rendered-document mode.
6. Project manage `edit`, `markdown-source`, and `save-markdown-source` controls.
7. Make existing renderers consume projected records while retaining their handlers and live state inputs.
8. Remove superseded normalization/eligibility branches and broad toolbar callback bridges; add no aliases.
9. Update toolbar, panel-host, view-capability, runtime-module, and user guidance documents.

## Verification

Prefer pure JavaScript module checks for:

- definition normalization
- duplicate/reserved-id behavior
- public versus manage eligibility
- capability denial
- route-policy narrowing
- active view/mode control projection
- empty projected-control sets
- rejection of unknown policy ids

Use a narrow DOM/component check to prove projected controls render without an empty toolbar. Keep the static public import-boundary test. Run route/browser smokes only if boot, route config, or network/module boundaries change.

Do not add permanent tests for button copy, focus choreography, hover state, modal timing, or source-editor interaction feel.

## Acceptance

- One code-owned owner normalizes and resolves views, document modes, and toolbar controls.
- Shared definitions and manage entrypoint contributions preserve the public/manage import boundary.
- Browser config cannot invent handlers, modules, views, modes, or controls.
- Markdown source remains a display mode of the document main view.
- Public contexts cannot resolve manage-only modes or controls.
- Manage mode retains current document controls and workflows.
- Route policy can hide only known controls and cannot widen app/capability access.
- `bookmark`, `info`, `edit`, `markdown-source`, and `save-markdown-source` are migrated in the first slice.
- Handlers and live state remain in focused controllers.
- No empty toolbar renders when no projected controls remain.
- Management toolbar actions remain in their existing workflow owners.
- No review-specific behavior or generic plugin/module-loader surface is added.
- Public/manage baseline checks remain green.

## Implementation Outcome

Implemented on 2026-07-11.

- `docs-viewer-view-registry.js` is the sole normalization, lookup, and eligibility owner for panel views, document modes, and document controls.
- Shared definitions register the current public-safe views, the rendered-document mode, bookmark, and info. The manage entrypoint contributes index graph, semantic-token picker, Markdown source, edit, source-toggle, and source-save definitions.
- Route records use `docs_viewer_route_config_v4`. `view_policy` may hide known view, mode, or control ids; unknown ids fail registry construction. Route-owned `hosted_views` and `ui.main_view_toolbar` are rejected.
- Hosts resolve through the shared registry. The display-mode host no longer owns a second mode normalizer or access engine.
- Main and manage renderers construct only projected controls. The Moments route hides bookmark and info and therefore renders no document toolbar.
- Bookmark, info, management, and source-editor controllers retain handlers and pressed, open, busy, disabled, and dirty state.
- The superseded `docs-viewer-hosted-views.js` registry and hosted-view access helper were removed without aliases.

Verification evidence:

- focused route/lifecycle tests: 25 passed
- focused router/registry browser module smoke: passed
- `docs-viewer-smoke` profile: passed all four checks
- final check summary: `var/admin/test-runs/docs-viewer-phase4-view-registry-final/summary.md`
