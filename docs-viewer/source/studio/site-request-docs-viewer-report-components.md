---
doc_id: site-request-docs-viewer-report-components
title: Docs Viewer Report Components Request
added_date: 2026-05-12
last_updated: "2026-05-13 11:14"
ui_status: done
parent_id: archive
sort_order: 32000
viewable: true
---
# Docs Viewer Report Components Request

Status:

- implemented

## Summary

Add a small report-component extension point to the Docs Viewer so selected documents can render a scope-aware report in the document pane.

The first use case is to replace the separate `/studio/library-documents/` route with a reusable docs-index table report.
That report should show generated docs records with filter buttons, sortable columns, and links back into the Docs Viewer management shell.

The core goal is to remove one-off routed report pages where the user is already working inside the Docs Viewer, without turning `docs-viewer.js` into a general Studio application controller.

## Requirement

The Docs Viewer should support document-level report opt-in from source metadata.

Example front matter:

```yaml
viewer_report: docs_index_table
viewer_report_scope: library
viewer_report_access: manage
```

Behavior:

- when a document payload includes `viewer_report`, the viewer mounts the matching report module into the document pane
- `viewer_report_scope` selects the data scope the report reads
- if `viewer_report_scope` is omitted, the report defaults to the current viewer scope
- `viewer_report_access` declares whether the report is available in public read-only mode, manage mode, or local-only contexts
- the document still belongs to normal Docs Viewer navigation, search, bookmarks, and management-mode routing
- report rows link to the relevant Docs Viewer document URL rather than to a separate Studio route

## Availability Contract

Reports must declare where they are allowed to run.
Some reports are useful as public reading aids, while others are only useful in a management context.

Initial access values:

- `public`: available in read-only and manage contexts
- `manage`: available only when the Docs Viewer management shell is active
- `local`: available only when the local generated-data or management-server capability required by the report is available

If `viewer_report_access` is omitted, default to the report module's own access policy.
The `docs_index_table` report should support both public and manage use cases through presets or parameters.

Examples:

```yaml
viewer_report: docs_index_table
viewer_report_scope: library
viewer_report_access: public
viewer_report_preset: az_index
```

```yaml
viewer_report: docs_index_table
viewer_report_scope: library
viewer_report_access: manage
viewer_report_preset: library_documents_admin
```

When a report is not available in the current context, the document pane should render a small unavailable state rather than failing silently.
For example, a manage-only report opened on a public read-only route should explain that the report is available in manage mode.

## First Use Case

Replace `/studio/library-documents/` with a Docs Viewer report-backed document.

The current route:

- reads the generated Library docs index
- displays `doc_id`, `added_date`, parent indicator, `viewable`, and `title`
- supports independent `viewable` and `parent` filters
- supports sorting by `doc_id`, `added_date`, and `title`
- links `doc_id` and `title` to `/docs/?scope=library&mode=manage&doc=<doc_id>`

The new implementation should preserve that behavior inside a reusable `docs_index_table` report.

Candidate report config:

```js
{
  id: "docs_index_table",
  sourceScope: "library",
  columns: ["doc_id", "added_date", "parent", "viewable", "title"],
  filters: ["viewable", "parent"],
  sortable: ["doc_id", "added_date", "title"]
}
```

The same report module should later be reusable from other docs by changing only the document metadata or report parameters.
For example, a Studio-scope report and a Library-scope report should not require separate report JavaScript files.

## Design Principles

Keep `docs-viewer.js` thin.
It should detect report metadata, pass a small viewer context to the report system, and delegate all report-specific behavior.
It should not own report filtering, sorting, row rendering, or per-report data shaping.

Use a report registry rather than hardcoded conditionals.
The viewer should resolve `viewer_report: docs_index_table` through a registry or loader, then call the report module's mount function.

Make reports scope-aware.
The document decides where the report appears in the tree.
The report parameters decide which generated docs scope supplies the data.

Treat report documents as normal documents.
Report-backed docs should keep ordinary `parent_id`, `sort_order`, title, visibility, bookmark, and management metadata behavior.
The report controls what appears in the document pane; the docs index controls where the report appears.

Keep report state routeable.
Filter and sort state should be reflected in URL parameters so refresh, back, and shared URLs remain understandable.

Use Docs Viewer-owned CSS and UI primitives.
Do not reuse Studio-only classes such as `tagStudioList` inside portable Docs Viewer report components unless those primitives have first been moved into the Docs Viewer boundary.

Prefer one generic report before adding specific reports.
The first implementation should be a configurable docs-index table report, not a Library-only component.

## Limitations

This feature is for lightweight report and inspection surfaces.
It is not a general dashboard framework.

Good candidates:

- docs index tables
- hidden or non-viewable docs lists
- parent or orphan inspection lists
- recently updated or recently added variants
- public A-Z indexes
- read-only generated-data summaries

Poor candidates:

- multi-step workflows
- source or config editing screens
- import, export, apply, or rebuild flows
- screens that depend on broad Studio route-ready state
- screens that need project-specific write allowlists or backup behavior

## Non-Goals

- Do not add config-write behavior to Docs Viewer report components.
- Do not move Studio write workflows into the Docs Viewer.
- Do not make the Docs Viewer responsible for Catalogue, Analytics, or other non-document application logic.
- Do not add report-specific logic directly to `docs-viewer.js`.
- Do not dynamically load arbitrary report code from untrusted config.
- Do not preserve `/studio/library-documents/` indefinitely once the report replacement is accepted and linked.
- Do not require a new report module per scope when one scope-aware module is enough.

## Proposed File Ownership

Candidate files:

- `assets/docs-viewer/js/docs-viewer-reports.js`
- `assets/docs-viewer/js/reports/docs-index-table-report.js`
- `assets/docs-viewer/css/docs-viewer-reports.css`

Responsibilities:

- `docs-viewer.js`: report metadata detection, context creation, mount/unmount handoff
- `docs-viewer-reports.js`: registry, report lookup, route-state helpers shared by report modules
- `docs-index-table-report.js`: generated docs index loading, table filters, sort state, row rendering
- `docs-viewer-reports.css`: report table/list layout and responsive behavior

## Implementation Tasks

### 1. Carry Report Metadata Through Generated Payloads

Add supported front-matter fields to the docs generation contract:

- `viewer_report`
- `viewer_report_scope`
- `viewer_report_access`
- `viewer_report_preset`
- later optional report parameters if needed, such as columns or default filters

Acceptance:

- generated by-id payloads expose report metadata for opted-in docs
- docs without report metadata render exactly as they do today
- unsupported report metadata fails closed with an unavailable state, not a broken document pane

### 2. Add A Thin Report Mount Point

Update the Docs Viewer runtime so document rendering can delegate to a report module after payload load.

Acceptance:

- `docs-viewer.js` does not gain report-specific filtering or table code
- report mount and unmount are explicit
- report availability is checked before mounting
- ordinary document content, search mode, recently-added mode, bookmarks, and management mode still work

### 3. Build The Scope-Aware Docs Index Table Report

Create one reusable report that reads a generated docs index for a selected scope.

Acceptance:

- defaults to current viewer scope when no report scope is configured
- supports both public and manage access when configured for the right preset
- supports the Library Documents columns and filters
- can also support a simple public A-Z index without adding another report module
- supports sortable `doc_id`, `added_date`, and `title`
- links rows back into the Docs Viewer URL model
- does not depend on Studio config, Studio route state, or Studio CSS

### 4. Move Library Documents To A Report-Backed Doc

Create or update the source doc that represents the Library Documents report and mark it with `viewer_report: docs_index_table`.

Acceptance:

- the report is reachable from the Docs Viewer tree
- the report-backed doc can be moved or reparented with normal Docs Viewer management operations
- the report reproduces the useful behavior of `/studio/library-documents/`
- the old Studio route can be removed or redirected after links have moved

### 5. Document The Contract

Update the owning Docs Viewer docs after implementation.

Acceptance:

- report metadata fields are documented
- report file ownership is documented
- the distinction between read-only reports and write/config workflows is explicit

## Risks

- Reports could become a back door for adding Studio-only application screens to the portable viewer.
- URL parameter growth could make Docs Viewer routes harder to reason about if report state is not namespaced.
- A generic table report could become too configurable too early; keep the first version limited to docs-index use cases.
- Removing the standalone Studio route too early could hide a useful admin surface before report navigation and mobile behavior are proven.
- Public reports could accidentally expose management-only metadata if access policy and presets are not explicit.

## Acceptance Criteria

This request is ready to close when:

- the Docs Viewer supports a document-level report mount without bloating `docs-viewer.js`
- the first `docs_index_table` report works for Library Documents
- the report can be reused for another scope by changing document metadata or report parameters, not by copying JavaScript
- report access is enforced for public, manage, and local-only contexts
- filter and sort state survive refresh through route parameters
- no config write, source write, import, export, rebuild, or apply workflow has moved into the report component
- `/studio/library-documents/` is no longer needed as the primary Library Documents surface
