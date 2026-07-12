---
doc_id: site-request-docs-viewer-embedded-detail-documents
title: Embedded Detail Documents
added_date: 2026-06-23
last_updated: 2026-06-24
parent_id: docs-viewer
viewable: true
---
# Embedded Detail Documents

Embedded detail documents let a normal indexed Docs Viewer document host a large set of Docs Viewer-owned detail documents without adding every detail document to the main index tree or global docs search.

The pattern is useful when the discovery surface should be a report or list inside a parent document rather than the Docs Viewer sidebar.
The parent document stays selected, the sidebar stays anchored to that parent, and detail documents are loaded into a report-owned region on demand.

Detail documents are still first-class Docs Viewer source docs.
They use the normal Markdown, front matter, media-token, doc-link, rendering, by-id payload, and publish pipeline.
The embedded-detail model changes discovery and presentation; it does not create a weaker detail-document format.

## Source Layout

A sub-scope is a detail-document grouping below a normal Docs Viewer scope.
It is not a full navigable scope and must not appear in the scope selector.

```text
source: docs-viewer/source/<scope>/<sub-scope>/
generated: docs-viewer/generated/docs/<scope>/<sub-scope>/
published: site/assets/data/docs/scopes/<scope>/<sub-scope>/
```

The parent scope owns the indexed report document.
The sub-scope owns the detail payloads and manifest that the parent report loads.

Main-scope builds explicitly ignore configured sub-scope source directories for:

- `index-tree.json`
- `recently-added.json`
- global docs search

Sub-scope builds write only by-id payloads and a minimal manifest.

## Parent Report

A normal indexed source document opts into the generic sub-scope report with front matter:

```yaml
viewer_report: docs_subscope
viewer_report_subscope: tags
viewer_report_access: public
```

Fields:

- `viewer_report`: selects the `docs_subscope` report module
- `viewer_report_subscope`: names the configured sub-scope that the report may load
- `viewer_report_access`: follows the normal report access model; use `public` only when the report is promoted and allowlisted for public routes

The sub-scope is configured by the parent document payload, not by a URL query parameter.
This prevents the generic report from becoming an arbitrary sub-scope loader.

Any authored content before the report controls belongs to the parent document and renders normally.

## URL State

The active Docs Viewer document remains the indexed parent/report document.
The standard report-owned detail parameter is `subdoc`.

```text
/docs/?scope=<scope>&doc=<parent_doc_id>
/docs/?scope=<scope>&doc=<parent_doc_id>&subdoc=<detail_doc_id>
```

For a public route:

```text
/analysis/?doc=tags
/analysis/?doc=tags&subdoc=ordered
```

In the detail URL:

- `doc=tags` is still the selected Docs Viewer document
- `subdoc=ordered` is report-owned state
- refresh reloads the parent report and opens the embedded detail document
- browser Back/Forward moves between report list/detail states without selecting the detail document in the sidebar

The shared route helpers preserve `subdoc` only when the route still points at the indexed parent document.
Normal document navigation clears report-owned detail state.

## Runtime Behavior

The `docs_subscope` report:

- reads `viewer_report_subscope` from the selected parent document payload
- validates the configured sub-scope against the current scope's browser-facing config
- loads the configured sub-scope `manifest.json`
- reads `subdoc` from the current URL
- derives detail payload URLs from the current scope, configured sub-scope, and selected detail id
- renders list state when `subdoc` is absent
- renders detail state when `subdoc` is present and listed in the manifest
- renders a contained report error when `subdoc` is unknown or a detail payload fails to load
- updates only report-owned URL state when rows or the report back control are used
- never updates Docs Viewer selected-document state to the sub-scope detail document

The report owns:

- selected detail id
- embedded detail payload loading
- detail-region rendering
- `subdoc` URL state

Docs Viewer owns:

- active scope
- active parent/report document
- sidebar tree selection
- parent document payload rendering
- report mounting hook

Future search and filter controls, if added, should remain report-owned and should not change the selected Docs Viewer document.

## List And Detail States

List state shows the sub-scope list from the manifest and lets the user select a row.

Detail state:

- hides the list and list header completely
- leaves only minimal report controls, currently the back control and detail label
- renders the selected detail document inside the report surface
- provides a back control that clears `subdoc` and restores list state

The embedded detail body reuses normal Docs Viewer rendered-document styling.
Report-specific detail CSS provides only containment, spacing, and the report toolbar/divider.
It must not redefine document typography, table, image, or link styling.

Representative structure:

```html
<section class="docsReportDetail" aria-labelledby="docs-report-detail-title-tags">
  <div class="docsReportDetail__header">
    <button type="button">Back to all tags</button>
    <p id="docs-report-detail-title-tags">ordered</p>
  </div>
  <article class="docsReportDetail__body docsViewer__content content"></article>
</section>
```

The detail body receives the selected by-id payload's `content_html`.
The detail wrapper should not be a card, panel, or secondary document frame.

## Manifest Contract

Each sub-scope publishes a minimal manifest.
The manifest is an existence and ordering contract, not an index tree.

```json
{
  "doc_ids": "materiality,scale,rhythm"
}
```

Field requirements:

- `doc_ids`: comma-delimited ordered list of stable detail document ids

Detail `doc_id` values must not contain commas.
The sub-scope builder enforces this.

The report derives all other runtime information:

- parent scope from the active Docs Viewer scope
- sub-scope from `viewer_report_subscope`
- selected detail id from `subdoc`
- by-id payload URL from browser-facing sub-scope config
- list labels from explicit report metadata sources

Sub-scope detail documents may still carry normal Docs Viewer metadata such as `parent_id`.
The generic `docs_subscope` report does not treat that metadata as list hierarchy.
Nested detail navigation or grouping should be a later report-specific extension that reads explicit list metadata.

## By-Id Payload Contract

Sub-scope detail documents publish the same by-id JSON shape as normal Docs Viewer documents.
The payload keeps normal rendered content and metadata, including:

- `doc_id`
- `title`
- `last_updated`
- `content_html`
- front matter-derived fields exposed by the normal by-id payload contract

The generic report renders `content_html`, and keeps by-id metadata available for labels, diagnostics, and future promotion workflows.

Keeping the full by-id shape preserves the option to promote a detail document into an indexed document later without changing its source Markdown model.

## Detail Identity

Sub-scope detail ids only need to be unique within their owning `<scope>/<sub-scope>`.
They do not need to be unique across the whole parent scope.

Runtime detail identity is resolved from:

```text
<scope> + <parent_report_doc_id> + <subdoc>
```

Cross-report references, logs, and caches should preserve enough context to resolve through the parent report config, or use a composite identity such as:

```text
<scope>/<sub-scope>/<doc_id>
```

Raw detail `doc_id` values should not be treated as globally unique.

## Link Resolution

Detail documents may contain normal same-sub-scope Markdown links.
When a sub-scope has exactly one matching indexed parent report document, the sub-scope builder rewrites same-sub-scope links to the embedded report-detail URL.

Example:

```text
source detail link: related.md
rendered href: /docs/?scope=studio&doc=analytics-tags&subdoc=related
```

If the builder cannot identify a unique parent `docs_subscope` report for the sub-scope, it falls back to the normal Docs Viewer doc URL and records a warning for ambiguous parent report matches.

## Sub-Scope Config

Sub-scopes are declared inside the parent scope config record.
They are not top-level scopes.

Example:

```json
{
  "scope_id": "analysis",
  "source": "docs-viewer/source/analysis",
  "output": "docs-viewer/generated/docs/analysis",
  "publish_output": "site/assets/data/docs/scopes/analysis",
  "sub_scopes": [
    {
      "sub_scope": "tags",
      "title": "Tags",
      "source": "docs-viewer/source/analysis/tags",
      "output": "docs-viewer/generated/docs/analysis/tags",
      "publish_output": "site/assets/data/docs/scopes/analysis/tags"
    }
  ]
}
```

Browser-facing config projects each sub-scope with enough safe data for the report:

```json
{
  "sub_scope": "tags",
  "title": "Tags",
  "manifest_url": "/assets/data/docs/scopes/analysis/tags/manifest.json",
  "by_id_url_base": "/assets/data/docs/scopes/analysis/tags/by-id"
}
```

Public reports must read only browser-safe generated or published projections.
They must not read source Markdown files directly.

## Build And Publish

`build_docs.py` remains the orchestration entrypoint.
Sub-scope builds use:

```bash
./docs-viewer/build/build_docs.py --scope studio --sub-scope tags --write
```

The sub-scope build path reuses the normal Docs Viewer pipeline:

- source parsing
- front matter normalization
- Markdown and raw HTML rendering
- media token resolution
- doc-link rewriting
- deterministic JSON writing

The builder writes working generated JSON:

```text
docs-viewer/generated/docs/<scope>/<sub-scope>/by-id/<doc_id>.json
docs-viewer/generated/docs/<scope>/<sub-scope>/manifest.json
```

For public scopes, the existing parent-scope `Publish` action copies configured sub-scope manifests and by-id payloads to:

```text
site/assets/data/docs/scopes/<scope>/<sub-scope>/by-id/<doc_id>.json
site/assets/data/docs/scopes/<scope>/<sub-scope>/manifest.json
```

The builder does not write public snapshots directly.
Publishing remains part of the existing parent-scope publish preview/apply flow.

The Docs Live Rebuild Watcher treats configured sub-scope source changes as sub-scope builds.
It does not run parent-scope docs or search rebuilds for sub-scope-only source changes.

## Lifecycle

Sub-scopes are managed alongside normal Docs Viewer scope management with dedicated lifecycle actions:

- `New sub-scope`
- `Delete sub-scope`

These actions operate within the selected parent scope.
They do not create public routes, add the sub-scope to the main scope selector, or make sub-scope documents directly selectable in the main sidebar.

`New sub-scope` asks for the sub-scope id and title only.
Sub-scopes do not have a default document concept.

`Delete sub-scope` uses preview and confirmation because it can remove source docs, working generated payloads, and published payloads.

## Constraints

- A sub-scope is not a full scope in the route model or scope selector.
- Main scope builders must exclude configured sub-scope source directories from index, recent, and search payloads.
- Sub-scope builders must keep using the normal Docs Viewer rendering and by-id payload pipeline.
- Published sub-scopes must include a minimal manifest so the report can validate and order detail ids without loading a tree or search index.
- `subdoc` is reserved for `docs_subscope` detail state.
- Public sub-scope publishing remains part of the parent-scope `Publish` action.
- Public manifests should not repeat scope, sub-scope, title, payload URL, or label data because those values are derived from explicit report metadata sources.

## Public And Manage Behavior

Public behavior:

- parent/report doc appears in the public index when viewable
- detail payloads are loadable through the report and report-owned links
- global docs search does not include sub-scope detail docs by default
- published payloads include the parent report, configured sub-scope manifests, and required detail by-id payloads

Manage behavior:

- parent/report doc behaves like any report-backed Docs Viewer document
- existing manage tools such as edit metadata apply to the indexed parent/report document
- sub-scope detail documents are not visible as normal standalone manage-mode docs outside the report
- source/edit workflows for sub-scope detail docs need a separate design

## Files

- `docs-viewer/build/docs_builder/sub_scope.py`
- `docs-viewer/config/scopes/docs_scopes.json`
- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js`
- `site/docs-viewer/runtime/js/shared/docs-subscope-report.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-router.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js`
- `site/docs-viewer/static/css/docs-viewer-reports.css`
