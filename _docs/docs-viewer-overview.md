---
doc_id: docs-viewer-overview
title: Overview
added_date: 2026-04-24
last_updated: 2026-05-20
parent_id: docs-viewer
sort_order: 1000
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
- Analysis docs at `/analysis/`

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
- the desktop sidebar collapse control
- the main content pane
- the optional inline search input
- status, path, and updated metadata areas

It also passes the current scope configuration into the DOM through `data-*` attributes.

### 3. Shared runtime

The viewer behavior is coordinated by:

- `assets/docs-viewer/js/docs-viewer.js`

The entry module imports focused helper modules as responsibilities are extracted.
Current helper modules:

- `assets/docs-viewer/js/docs-viewer-tree.js` owns pure document sorting, children-map construction, visibility checks, and doc-id set normalization
- `assets/docs-viewer/js/docs-viewer-search.js` owns pure search-entry normalization, scoring, matching, result ordering, and recently-added document ordering
- `assets/docs-viewer/js/docs-viewer-favourites.js` owns bookmark record normalization, ordering, key generation, and IndexedDB persistence helpers
- `assets/docs-viewer/js/docs-viewer-document-controller.js` owns document pane visibility, payload rendering, loading/missing/error states, and report mount handoff
- `assets/docs-viewer/js/docs-viewer-reports.js` owns report lookup and access checks
- `assets/docs-viewer/js/reports/docs-index-table-report.js` owns the reusable docs-index table report

This runtime is shared across the current docs scopes.
It reads the shell configuration, loads the generated JSON for the active scope, coordinates tree navigation, loads document payloads, and delegates document/search pane rendering to focused controllers.

When a route shell has `data-generated-base-url` and that local server advertises generated-data read capability, the runtime reads the active scope index, document payloads, and docs-search index through that server.
The local `bin/dev-studio` overlay uses this path because generated docs/search JSON is excluded from the Jekyll watch surface.
Public/static builds leave `data-generated-base-url` blank and use the generated JSON asset URLs directly.

## Current URL And State Contract

The current viewer URL model is query-based rather than path-segment based.

Current URL state:

- `doc` selects the active document
- `scope` selects the active docs scope on `/docs/`
- `q` activates inline docs search for the current scope
- `mode=manage` enables local manage mode only on `/docs/` when the docs-management server is available
- `report_sort`, `report_dir`, and `report_filter` hold state for report-backed document panes
- `#hash` targets a heading within the rendered document

The local management shell normalizes onto canonical scoped URLs:

- `/docs/?scope=studio&doc=<doc_id>`
- `/docs/?scope=library&doc=<doc_id>`
- `/docs/?scope=analysis&doc=<doc_id>`

When the current `/docs/` session is already in `mode=manage`, the browser runtime preserves that mode for internal canonical `/docs/?scope=<scope>&doc=<doc_id>` clicks.
Source Markdown links should stay canonical and should not include `mode=manage`.

Public read-only docs routes use:

- `/library/?doc=<doc_id>`
- `/analysis/?doc=<doc_id>`

## Current Runtime Behavior

At runtime the viewer:

1. loads the scope index JSON
2. builds the tree from `parent_id`
3. sorts siblings by `sort_order`, then title, then `doc_id`
4. loads per-doc rendered HTML from the selected document payload
5. keeps the left navigation in place while the right pane switches between document view and inline search results

Current document metadata behavior:

- the document H1 is treated as the visible title
- the metadata path shows ancestor docs only, so it does not duplicate the current document title
- root-level docs hide the metadata path and let remaining metadata move up
- the updated date uses `last_updated` only when the active scope's generated `viewer_options.show_updated_date` is not `false`
- Studio Docs shows the updated date; Library hides it in document view

Current sidebar behavior:

- larger screens show a small control in the index panel header that collapses the docs tree to a narrow rail
- the collapsed rail keeps the control visible so the index can always be restored
- the collapsed desktop layout widens the Docs Viewer reading measure without making prose fully fluid
- the collapsed state is stored per viewer scope in browser storage
- smaller screens keep the existing stacked layout and do not show the collapse control, because the document pane already has the full viewport width

Current search behavior:

- docs search is inline within the viewer rather than a separate docs search page
- docs search includes only viewable docs
- docs search excludes docs where `viewable: false`
- the viewer lazily loads the scope search index when `q` is present
- result links route back into the same viewer URL model
- search and recently-added list entries use title plus muted metadata rather than showing `doc_id`
- search metadata uses `last_updated` and, when available, parent title in the form `date • parent`

Current recently-added behavior:

- the button is rendered by the shared shell when inline docs search is enabled
- the runtime sorts current-scope viewable docs by `added_date` descending, then title ascending
- the list is capped by `docs_viewer.recently_added_limit` in `assets/studio/data/studio_config.json`
- list metadata uses `added_date` and, when available, parent title in the form `date • parent`

Current report behavior:

- docs source front matter can opt into a report with `viewer_report`
- `viewer_report_scope` selects the generated docs scope the report reads; if omitted, the current viewer scope is used
- `viewer_report_access` gates reports to public, manage, or local-only contexts
- report-backed docs remain normal docs in the index, so `parent_id`, `sort_order`, visibility, bookmarks, and management moves still work normally
- the first report is `docs_index_table`, a scope-aware generated-docs table with filter buttons, sortable columns, and Docs Viewer row links
- the Library Documents review now uses `viewer_report: docs_index_table` with `viewer_report_scope: library`

Current visibility behavior:

- generated docs indexes can carry `viewable: false` rows that remain generated and manageable
- public/default viewer navigation, inline search, and recently-added lists include only docs where `viewable !== false`
- `archive` is a normal doc id and parent folder; if it should be hidden, set `viewable: false` in front matter

Current manage-mode draft behavior:

- public/default tree rendering includes only docs whose generated index row is not `viewable: false`
- manage mode always includes non-viewable docs in the tree
- the manage toolbar has a `show viewable` checkbox, checked by default, that keeps viewable docs visible for context
- unchecking `show viewable` gives a focused non-viewable/draft review tree
- manage-mode direct links to a viewable doc auto-enable `show viewable` so links can land on the target
- non-viewable docs are prefixed with `✏️` in the index and use the configured draft color from `studio_config.json`
- a selected non-viewable doc can be made viewable through the manage toolbar; the action prompts before also making required non-viewable ancestors or optional descendants viewable

Document view updated-date metadata is scope-configurable because it is more useful in Studio Docs than Library. Docs search continues to use `last_updated`; revisiting search metadata and ranking is a separate search task.

## Scope Boundary

The current design keeps some behavior scope-specific and some behavior shared.

Scope-owned:

- source doc trees
- generated docs indexes and per-doc payloads
- scope-level viewer options in generated docs indexes
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
