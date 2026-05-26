---
doc_id: site-request-docs-viewer-javascript-app-shell
title: Docs Viewer JavaScript App Shell Request
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: draft
parent_id: change-requests
sort_order: 12100
viewable: true
---
# Docs Viewer JavaScript App Shell Request

Status:

- proposed

## Summary

Move Docs Viewer toward a JavaScript-owned app shell with a clear backend boundary for local editing workflows.

This request is related to [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer), but it focuses on explaining and implementing the runtime shape rather than moving files.

The target is:

- JavaScript owns the Docs Viewer shell, routing, panels, document rendering, search UI, management UI, modals, and link behavior.
- Generated docs/search JSON and config own the read data contract.
- The Docs Viewer backend owns source writes, rebuilds, import, archive, delete, move, scope setup, source opening, and other filesystem operations.

Management mode is not treated as a removable publishing add-on in this request. Docs Viewer has two first-class uses:

- local editing and maintenance, where management mode and backend APIs are available
- public presentation, where the same viewer reads generated JSON without exposing write capabilities

Portability means those two uses can be explained, installed, and hosted cleanly from the same product boundary.

## Reason

The portable Docs Viewer direction needs a simple story.

The current architecture has made progress: Docs Viewer runtime modules, CSS, config, generated payloads, and services now sit under the `docs-viewer/` boundary. But the product story is still hard to explain because route shells, generated data, management capabilities, and backend service behavior are not described as one clean app/backend contract.

The intended model should be easier to communicate:

- The viewer app is browser JavaScript.
- The read contract is generated JSON plus config.
- Local editing uses the same viewer app with management mode enabled and a backend service available.
- Public presentation uses the same viewer app with write capabilities unavailable.
- The backend is a local capability for editing source docs, not the definition of the viewer.

This separation should make portability easier because a consuming project can understand which pieces are required for viewing, which pieces are required for editing, and which paths are project-specific.

## Goals

- define Docs Viewer as a JavaScript app with a narrow backend contract
- keep management mode as a first-class local editing workflow
- keep public presentation as the read-only generated-data workflow
- make scope setup, generated docs/search payloads, UI text, and external paths config-driven
- reduce host/Jekyll route-shell assumptions inside the viewer runtime
- make the install explanation clearer for another local project
- keep write operations behind explicit backend endpoints
- preserve current `/docs/`, `/library/`, and `/analysis/` behavior during migration

## Non-Goals

- removing management mode from portable installs
- turning Docs Viewer into only a static publishing widget
- allowing browser JavaScript to write source Markdown directly
- replacing the Python Docs Viewer backend as part of this request
- changing the generated docs payload schema in the first slice
- rewriting all Docs Viewer runtime modules in one batch
- merging Studio and Docs Viewer concepts

## Product Model

Docs Viewer should be explainable as one app with two runtime contexts.

### Local Editing Context

Local editing uses:

- Docs Viewer browser app
- generated docs/search payloads
- source scope config
- management UI
- local backend APIs for writes and rebuilds

This context powers `/docs/?mode=manage`.

It should support source editing workflows such as:

- create docs
- edit metadata
- move docs
- archive/delete docs
- import staged docs
- create or update scopes
- rebuild generated payloads
- open source files locally

### Public Presentation Context

Public presentation uses:

- Docs Viewer browser app
- generated docs/search payloads
- public viewer config
- read-only routing, search, index, document rendering, reports, bookmarks, and links

This context powers routes such as `/library/` and `/analysis/`.

It should not expose management controls or write-capable backend endpoints.

The public presentation context is not a separate product. It is the same viewer app running without local editing capabilities.

## Target Architecture

```text
Docs Viewer JavaScript app
  - boot/runtime config
  - route and query-state handling
  - scope selection
  - index/sidebar/panel rendering
  - document payload loading and rendering
  - inline search and generated report loading
  - management UI and modals when management is enabled
  - backend client for management workflows

Generated data and config
  - docs indexes
  - per-doc payloads
  - search indexes
  - scope config
  - UI text
  - capability flags and route settings

Docs Viewer backend
  - source Markdown writes
  - source config writes
  - import/archive/delete/move/apply workflows
  - generated docs/search rebuilds
  - source opening
  - filesystem allowlists, backups, and validation
```

In this model, a route shell should mainly provide a mount point and route context. The Docs Viewer JavaScript app should render the viewer shell from config and generated data.

## Backend Boundary

The backend remains necessary for local editing.

The backend should own:

- source file mutation
- source config mutation
- import staging and apply workflows
- move/archive/delete workflows
- generated payload rebuilds
- backups and recovery points
- filesystem allowlists
- local source-file opening
- structured validation and error shaping

The browser should only call named Docs Viewer backend endpoints. It should not send arbitrary filesystem paths, shell commands, or direct write instructions.

The backend can remain Python. A future Node backend would still be a backend and would still need the same safety boundary. The important architecture decision is frontend/backend separation, not backend language.

## Config Boundary

Config should describe installation-specific and mode-specific behavior.

Candidate config responsibilities:

- available scopes
- default scope
- generated docs index paths
- generated search index paths
- management-enabled routes
- public read-only routes
- UI text
- backend base URL for local editing
- feature flags for import, scope lifecycle, source opening, reports, or bookmarks

The viewer app should consume this config directly. Route shells should not hardcode scope lists, management capability rules, or generated payload paths where those can be represented as config.

## Benefits

- clearer portable story: "browser app plus generated data, with backend APIs for local editing"
- management mode remains central to local editing rather than treated as an optional extra
- public routes stay read-only without becoming a separate viewer implementation
- host projects get a smaller integration surface
- route shells can become thinner and less Jekyll-specific
- management backend safety stays explicit
- generated JSON remains the stable read contract
- the same pattern can later inform Studio's JavaScript app-shell direction

## Risks

- moving shell ownership into JavaScript increases reliance on browser boot behavior
- management code could leak into public presentation if capability checks are weak
- generated config shape could become too broad if it tries to model every local detail
- route migration could temporarily duplicate Jekyll include logic and JS shell logic
- public and management contexts could drift if they are tested separately but not as one app

Mitigations:

- keep public and management contexts in one runtime contract
- lazy-load management-only modules only when management is enabled
- keep backend capability checks server-side as well as client-side
- migrate one shell responsibility at a time
- add smoke coverage for both `/docs/?mode=manage` and public read-only routes

## Proposed Approach

1. Document the app/backend contract.
   Define which behavior belongs to the browser app, generated data/config, and backend service.

2. Make the route shell thinner.
   Keep route pages responsible for mount/context only. Move viewer shell composition into JavaScript where practical.

3. Make management capabilities explicit config plus backend capabilities.
   The browser can hide controls from config, but backend endpoints must still enforce write capability.

4. Preserve generated docs/search JSON as the read contract.
   Do not change payload shape just to move shell ownership.

5. Prove the pattern on the management route and one public route.
   `/docs/?mode=manage` and one public route such as `/library/` should both boot from the same app-shell model.

6. Update the portable setup docs after the runtime shape is proven.
   The install explanation should describe local editing and public presentation as two contexts of the same Docs Viewer app.

## First Slice

The first implementation slice should avoid a broad rewrite.

Suggested first slice:

- define a small Docs Viewer app boot module if the current entry module cannot cleanly own shell rendering
- move one shell-owned element from `_includes/docs_viewer_shell.html` into JavaScript
- keep the existing generated JSON paths and backend endpoints
- keep `/docs/`, `/library/`, and `/analysis/` URLs unchanged
- verify management controls still appear only when management is enabled
- verify public routes do not load management-only modules

The first slice is successful when one visible shell responsibility is owned by JavaScript without weakening the backend write boundary or changing the public read-only route contract.

## Open Questions

- Which shell responsibility is the safest first move: header actions, scope picker, index panel, document mount, or management action area?
- Should the current `docs-viewer/runtime/js/docs-viewer.js` remain the app shell entrypoint, or should a new boot module coordinate shell rendering?
- How should route shells pass route context to the app: data attributes, JSON script tag, config URL, or generated route config?
- Should management capability be represented as route config, backend capability response, or both?
- What fixture project is enough to prove portability after the app/backend boundary is clearer?

## Verification

Focused checks for implementation slices should include:

```bash
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_service.py
$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py
$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py
node --check docs-viewer/runtime/js/docs-viewer.js
```

Browser smoke expectations:

- `/docs/?mode=manage` boots the Docs Viewer app and exposes management controls
- public read-only routes boot the same viewer app without management controls
- management-only modules are not loaded on public routes
- generated docs/search payloads remain the read contract
- write workflows still call backend endpoints and cannot be performed by static browser JS alone
