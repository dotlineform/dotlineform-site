---
doc_id: docs-viewer-runtime-boundary
title: Docs Viewer Runtime Boundary
added_date: 2026-03-31
last_updated: "2026-05-14"
parent_id: docs-viewer
sort_order: 90
---
# Docs Viewer Runtime Boundary

## Purpose

This document records the current boundary between:

- scope-specific docs page shells such as `/docs/` and `/library/`
- the shared docs viewer runtime in `assets/docs-viewer/js/docs-viewer.js`

It exists as a guardrail so the repo can continue adding scope-specific docs behavior without forking the core viewer too early.

## Current boundary

Current model:

- scope pages may diverge at the route-shell level
- the viewer runtime remains shared
- the structural shell include remains shared

Current route-shell examples:

- `docs/index.md`
- `library/index.md`
- `analysis/index.md`

Current shared implementation:

- `assets/docs-viewer/js/docs-viewer.js` as the shared entry controller
- `assets/docs-viewer/js/docs-viewer-management.js` as the management-mode controller loaded only by management-enabled viewer shells
- `assets/docs-viewer/js/docs-viewer-management-render.js` for management-only markup helpers imported by the management controller
- `assets/docs-viewer/js/docs-viewer-management-client.js` for docs-management server transport helpers used by the management controller
- `assets/docs-viewer/js/docs-viewer-drag-drop.js` for drag/drop helpers used by the management controller
- `assets/docs-viewer/js/docs-viewer-tree.js` for pure tree and visibility helpers imported by the entry controller
- `assets/docs-viewer/js/docs-viewer-search.js` for pure inline-search and recently-added helpers imported by the entry controller
- `assets/docs-viewer/js/docs-viewer-bookmarks.js` for bookmark state, rendering, IndexedDB storage orchestration, and events imported by the entry controller
- `assets/docs-viewer/js/docs-viewer-favourites.js` for bookmark record and IndexedDB storage helpers imported by the bookmark controller
- `assets/docs-viewer/js/docs-viewer-render.js` for read-oriented result and bookmark markup helpers imported by the entry and bookmark controllers
- `assets/docs-viewer/js/docs-viewer-router.js` for URL building, anchor route parsing, browser history writes, requested-doc resolution, canonical route correction, popstate orchestration, and payload-load orchestration imported by the entry controller
- `_includes/docs_viewer_shell.html`
- `assets/docs-viewer/css/docs-viewer-management.css` for management-only shell and modal styling

The shell loads the entry controller as an ES module.
Extracted helper modules must not import the entry controller or mutate its shared state directly.
The management controller receives a narrow context API from the entry controller so public read-only viewers do not download or execute management orchestration.

Current scope-owned data:

- `assets/data/docs/scopes/studio/`
- `assets/data/docs/scopes/library/`
- `assets/data/docs/scopes/analysis/`

Current route capability boundary:

- `/docs/` is the only route shell that enables `?mode=manage`
- `/docs/` can switch the loaded docs scope with `?scope=studio`, `?scope=library`, or `?scope=analysis`
- `/library/` and `/analysis/` are public read-only viewer routes and do not render management controls, configure write-capable management mode, or load management-only CSS
- public read-only viewer routes also avoid loading the management controller module
- local `bin/dev-studio` builds may configure `data-generated-base-url` for read-only generated-data reads because the local Jekyll overlay excludes generated docs/search JSON from the watch surface
- a `mode=manage` query on a public viewer route is normalized away by the shared runtime because those routes cannot perform local writes on the static public site
- canonical internal docs links stay read-only-safe and omit `mode=manage`; the management-capable `/docs/` shell preserves manage mode at runtime only when the current session is already in manage mode

## What should stay scope-specific

These are normal route-shell differences and should not force a runtime fork.

- scope-specific inline search controls or other shell actions
- different viewer data index URLs
- different base routes and default docs
- whether the route shell enables management mode
- whether the route shell exposes scope switching
- surrounding page context and navigation state
- scope-specific copy or small shell-level layout changes
- distinct source trees and generated JSON artifacts
- scope-specific viewer options in generated docs indexes, such as manage-only structural tree roots

These are expected uses of the current architecture.

## What should not trigger a fork

The following are not good reasons to split the runtime.

- adding or removing a button in one scope page
- changing page-level copy
- changing which scope-owned JSON tree the viewer loads
- adding small optional shell parameters to the shared include
- keeping Studio and library docs in separate source roots
- hiding a structural tree branch in one scope when that rule can be expressed as generated scope-owned data

If the difference can be expressed through data, route-shell composition, or a small include option, the runtime should stay shared.

## Potential fork triggers

A fork only becomes justified if the scopes stop being the same kind of viewer.

### Fundamentally different navigation model

Examples:

- one scope stays a tree-based docs viewer while another becomes faceted browsing
- one scope wants timeline or gallery navigation instead of a docs tree

### Fundamentally different rendering model

Examples:

- one scope needs a richer content renderer with annotations, embedded canvases, or interactive reading tools
- one scope needs a different page anatomy than the sidebar-plus-content viewer

### Fundamentally different URL and state model

Examples:

- one scope needs nested route segments rather than `?doc=...`
- one scope needs version switching, compare state, or multi-pane state in the URL

### Fundamentally different performance model

Examples:

- one scope remains small and loads one index JSON
- another scope needs chunked indexes, lazy subtree loading, or other large-corpus behavior

### Fundamentally different interaction contract

Examples:

- one scope stays read-only
- another scope needs editing affordances, advanced keyboard navigation, or persistent review state

## Preferred response before forking

If a new requirement appears, prefer these steps in order:

1. express it as scope-owned data
2. express it as route-shell divergence
3. add a narrow optional include parameter
4. add a narrow runtime option if the core viewer model is still the same
5. fork only if the viewer model itself has diverged

This order is intended to delay a fork until there is clear evidence that the scopes are no longer the same product.

## Practical design rule

Use one runtime while the scopes are still:

- tree-index driven
- document-viewer shaped
- compatible with the same URL/state contract
- compatible with the same loading strategy

Consider a fork only when a new scope would otherwise force the shared runtime to carry a second competing model of navigation, rendering, or interaction.
