---
doc_id: site-request-docs-viewer-embedded-detail-documents
title: Docs Viewer Embedded Detail Documents Request
added_date: 2026-06-23
last_updated: 2026-06-23
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Embedded Detail Documents Request

## Request

Support large domain-owned document sets by loading detail documents inside an indexed parent or report document, rather than adding every detail document to the Docs Viewer index tree or global docs search.

The target pattern is a master/detail report inside a normal Docs Viewer document:

- the indexed parent document remains the active Docs Viewer document
- the parent renders a report or list over a large domain dataset
- selecting a row loads the corresponding detail document inside or below the report
- the sidebar stays anchored to the indexed parent document
- detail documents remain generated, reusable, and directly addressable by domain-owned UI

## Problem

Some domains can produce hundreds of document-like records.
For example, every tag in `analytics-app/data/canonical/tag-registry.json` may eventually need a corresponding document.

Making every tag document a normal Docs Viewer index row creates two problems:

- the index panel becomes too large to scan
- moving those docs out of the index but into global docs search only moves the payload problem from `index-tree.json` to the search index

The better discovery surface is domain-owned.
For tag documents, the tag registry or Analytics app should own the list, filters, grouping, search, aliases, status, and usage context.
Docs Viewer should provide the indexed parent/report shell and the detail-document rendering surface.

## Target Interaction

The report has two main states.

List state:

- shows the domain list or table
- provides search/filter controls
- lets the user select a row

Detail state:

- keeps a compact search/back header visible
- hides or collapses the full list
- renders the selected detail document inside the report surface
- provides a back/close action that restores the list state

Example flow:

```text
Tags

[Search tags...] [Group filter]

List:
  Materiality
  Scale
  Rhythm
```

Selecting `Scale` changes the same indexed parent document into:

```text
Tags

[Search tags...] [Back to all tags]
Selected: Scale

<embedded Scale tag document>
```

## URL State

The active Docs Viewer document should remain the indexed parent/report doc.

Example:

```text
/docs/?scope=studio&doc=analytics-tags
/docs/?scope=studio&doc=analytics-tags&tag=scale
```

In the second URL:

- `doc=analytics-tags` is still the Docs Viewer selected document
- `tag=scale` is report-owned state
- refresh should reload the parent report and open the embedded tag detail
- browser Back/Forward should move between report list/detail states without making the tag document a sidebar-selected doc

Report state parameters should remain namespaced or clearly owned by the report when needed.
For a generic implementation, prefer report-prefixed state such as `report_tag=scale` if collisions are likely.

## Embedded Detail Region

The detail document should render inside a contained report-owned region.
This can be ordinary HTML structure with explicit classes and labels:

```html
<section class="docsReportDetail" aria-labelledby="tag-detail-title">
  <div class="docsReportDetail__header">
    <h2 id="tag-detail-title">Tag details</h2>
    <button type="button">Back to all tags</button>
  </div>
  <article class="docsReportDetail__body"></article>
</section>
```

The report loads the selected detail payload and renders its `content_html` into `docsReportDetail__body`.
The embedded content should be styled through the detail-region class so headings, tables, images, and links do not fight the parent document layout.

## Detail Document Payloads

Detail documents should have stable generated payloads.
For tag docs, the detail doc id should be derived from the tag key so links are predictable.

This request does not require each detail document to be a normal sidebar tree document.
Implementation may choose one of these shapes:

- generate detail docs as normal Docs Viewer by-id payloads but keep them out of tree/search discovery
- generate report-owned detail payloads under a report/domain path
- reuse existing source Markdown rendering helpers to create detail HTML without treating each detail as a full Docs Viewer route target

The chosen shape should preserve:

- stable detail ids
- rendered HTML from authored/generated Markdown
- direct loading by the parent report
- no automatic inclusion in global Docs Viewer search
- no automatic inclusion in the Docs Viewer index tree

## Discovery Model

Domain-owned discovery is required.

For tag documents:

- Analytics tag rows should link to the corresponding detail state
- the tag registry report should list tag docs with tag-specific filters and metadata
- the Docs Viewer index should include high-level entry points such as `Tags`, `Tag Groups`, or `Analytics Vocabulary`
- global docs search should not automatically include every tag detail document
- a separate tag-doc search mode or lazy-loaded tag search index can be added later if needed

This avoids treating hundreds of detail docs as first-class Docs Viewer documents while still giving every tag a real document payload.

## Runtime Boundary

Docs Viewer owns:

- active scope
- active parent/report document
- sidebar tree selection
- parent document payload rendering
- report mounting hook

The report owns:

- domain list loading
- filters and search inside the report
- selected detail id
- embedded detail payload loading
- detail-region rendering
- report-owned URL parameters

The report may use a generated-data helper to read a detail payload by id.
That helper should not update Docs Viewer selected-document state.

## Public And Manage Behavior

The pattern should work in both `/docs/` and public read-only scopes when the report and its payloads are published for that scope.

Public behavior:

- parent/report doc appears in the public index when viewable
- detail payloads are loadable only through the report or domain-owned links
- global docs search does not have to include detail docs

Manage behavior:

- parent/report doc behaves like any report-backed docs document
- detail payload loading should work through the local generated-read service when available
- source/edit workflows for generated detail docs need a separate design if detail docs are not normal source Markdown docs

## Tests

Focused coverage should prove:

- the parent/report document remains the selected Docs Viewer document in list and detail states
- selecting a row loads the correct detail payload into the report detail region
- Back/close restores the list state
- refresh with report-owned detail URL state reopens the same detail
- the sidebar remains anchored to the parent/report doc
- detail docs are not accidentally added to global docs search
- detail docs are not accidentally added as top-level index tree rows
- public published payloads include the parent/report and any required detail payloads
- missing detail payloads render a contained report error instead of breaking the parent document
