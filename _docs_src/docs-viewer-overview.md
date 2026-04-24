---
doc_id: docs-viewer-overview
title: "Overview"
added_date: 2026-04-24
last_updated: 2026-04-24
parent_id: docs-viewer
sort_order: 10
---

# Docs Viewer Overview

## Purpose

The Docs Viewer is a shared documentation reader used by the site's docs-domain scopes.
It provides:

- a left-hand tree navigation built from generated docs indexes
- a right-hand document pane for rendered doc content
- inline docs search within the same viewer shell
- a shared recently-added list beside inline docs search

Current live scopes:

- Studio docs at `/docs/`
- Library docs at `/library/`

Catalogue pages do not use the Docs Viewer.

## Shared Module Model

The current implementation is split into three layers.

### 1. Scope-owned route shells

The route pages define scope-specific values such as:

- the docs index URL
- the search index URL
- the base route
- the default root doc
- whether the scope parameter is part of the canonical URL

Current route shells:

- `docs/index.md`
- `library/index.md`

### 2. Shared shell include

The route shells both render the same structural include:

- `_includes/docs_viewer_shell.html`

This include renders:

- the sidebar nav container
- the main content pane
- the optional inline search input
- status, path, and updated metadata areas

It also passes the current scope configuration into the DOM through `data-*` attributes.

### 3. Shared runtime

The viewer behavior is implemented in:

- `assets/js/docs-viewer.js`

This runtime is shared across the current docs scopes.
It reads the shell configuration, loads the generated JSON for the active scope, builds the tree navigation, loads document payloads, and switches between document and search modes.

## Current URL And State Contract

The current viewer URL model is query-based rather than path-segment based.

Current URL state:

- `doc` selects the active document
- `q` activates inline docs search for the current scope
- `#hash` targets a heading within the rendered document

Studio docs currently normalize onto a canonical scoped URL:

- `/docs/?scope=studio&doc=<doc_id>`

Library docs currently use:

- `/library/?doc=<doc_id>`

## Current Runtime Behavior

At runtime the viewer:

1. loads the scope index JSON
2. builds the tree from `parent_id`
3. sorts siblings by `sort_order`, then title, then `doc_id`
4. loads per-doc rendered HTML from the selected document payload
5. keeps the left navigation in place while the right pane switches between document view and inline search results

Current search behavior:

- docs search is inline within the viewer rather than a separate docs search page
- the viewer lazily loads the scope search index when `q` is present
- result links route back into the same viewer URL model
- search and recently-added list entries use title plus muted metadata rather than showing `doc_id`
- search metadata uses `last_updated` and, when available, parent title in the form `date • parent`

Current recently-added behavior:

- the button is rendered by the shared shell when inline docs search is enabled
- the runtime sorts current-scope docs by `added_date` descending, then title ascending
- the list is capped by `docs_viewer.recently_added_limit` in `assets/studio/data/studio_config.json`
- list metadata uses `added_date` and, when available, parent title in the form `date • parent`
- `_archive` is excluded from the list

Document view metadata continues to display `last_updated`, because that is more meaningful while reading a single doc. Docs search also continues to use `last_updated`; revisiting search metadata and ranking is a separate search task.

## Scope Boundary

The current design keeps some behavior scope-specific and some behavior shared.

Scope-owned:

- source doc trees
- generated docs indexes and per-doc payloads
- route/page shell copy
- route configuration values passed into the shell include

Shared:

- shell structure
- viewer runtime
- tree-navigation model
- document rendering model
- inline docs search interaction pattern

The rule for when this should and should not fork is recorded in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
