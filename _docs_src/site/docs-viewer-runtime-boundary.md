---
doc_id: docs-viewer-runtime-boundary
title: Docs Viewer Runtime Boundary
last_updated: 2026-03-30
parent_id: site
sort_order: 30
---

# Docs Viewer Runtime Boundary

## Purpose

This document records the current boundary between:

- scope-specific docs page shells such as `/docs/` and `/library/`
- the shared docs viewer runtime in `assets/js/docs-viewer.js`

It exists as a guardrail so the repo can continue adding scope-specific docs behavior without forking the core viewer too early.

## Current boundary

Current model:

- scope pages may diverge at the route-shell level
- the viewer runtime remains shared
- the structural shell include remains shared

Current route-shell examples:

- `docs/index.md`
- `library/index.md`

Current shared implementation:

- `assets/js/docs-viewer.js`
- `_includes/docs_viewer_shell.html`

Current scope-owned data:

- `assets/data/docs/scopes/studio/`
- `assets/data/docs/scopes/library/`

## What should stay scope-specific

These are normal route-shell differences and should not force a runtime fork.

- scope-specific inline search controls or other shell actions
- different viewer data index URLs
- different base routes and default docs
- surrounding page context and navigation state
- scope-specific copy or small shell-level layout changes
- distinct source trees and generated JSON artifacts

These are expected uses of the current architecture.

## What should not trigger a fork

The following are not good reasons to split the runtime.

- adding or removing a button in one scope page
- changing page-level copy
- changing which scope-owned JSON tree the viewer loads
- adding small optional shell parameters to the shared include
- keeping Studio and library docs in separate source roots

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
