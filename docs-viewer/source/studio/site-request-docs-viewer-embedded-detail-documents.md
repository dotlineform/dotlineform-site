---
doc_id: site-request-docs-viewer-embedded-detail-documents
title: Docs Viewer Embedded Detail Documents Request
added_date: 2026-06-23
last_updated: 2026-06-24
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Embedded Detail Documents Request

## Request

Support large Docs Viewer-owned detail document sets by loading detail documents inside an indexed parent or report document, rather than adding every detail document to the Docs Viewer index tree or global docs search.

This request is a prerequisite for adding high-cardinality semantic reference kinds such as `tag`.
The semantic-reference authoring work is tracked in [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor).

The target pattern is a master/detail report inside a normal Docs Viewer document:

- the indexed parent document remains the active Docs Viewer document
- the parent renders a report or list over a large domain dataset
- selecting a row loads the corresponding detail document inside or below the report
- the sidebar stays anchored to the indexed parent document
- detail documents remain first-class Docs Viewer source docs built through the normal docs pipeline
- detail documents live in a Docs Viewer sub-scope owned by the parent scope

## Problem

Some domains can produce hundreds of document-like records.
For example, every tag in `analytics-app/data/canonical/tag-registry.json` may eventually need a corresponding document.
Another expected use is one detail document per catalogue series from `studio/data/canonical/catalogue/series.json`.

Making every tag document a normal Docs Viewer index row creates two problems:

- the index panel becomes too large to scan
- moving those docs out of the index but into global docs search only moves the payload problem from `index-tree.json` to the search index

The better discovery surface is the report, not the Docs Viewer sidebar or global docs search.
For tag documents, the tag registry or Analytics app should own the source data, filters, grouping, aliases, status, and usage context exposed to the report through semantic targets or tokens.
Docs Viewer should own the detail Markdown source, rendering pipeline, generated payload shape, sub-scope lifecycle, and embedded detail-document rendering surface.

The revised ownership model treats these documents as a Docs Viewer sub-scope.
A sub-scope is a detail-document grouping under a normal scope, not a full navigable scope.
For example:

```text
source: docs-viewer/source/<scope>/<sub-scope>/
generated: docs-viewer/generated/docs/<scope>/<sub-scope>/
published: site/assets/data/docs/scopes/<scope>/<sub-scope>/
```

The parent scope still owns the indexed report document.
The sub-scope owns the detail payloads that report can load on demand.

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
The parent report document binds the generic report to a sub-scope.
The URL only carries optional report detail state.

Generic shape:

```text
/docs/?scope=<scope>&doc=<parent_doc_id>
/docs/?scope=<scope>&doc=<parent_doc_id>&<detail_param>=<detail_doc_id>
```

Example with the configured detail parameter `report_tag`:

```text
/docs/?scope=studio&doc=analytics-tags
/docs/?scope=studio&doc=analytics-tags&report_tag=scale
```

In the second URL:

- `doc=analytics-tags` is still the Docs Viewer selected document
- `report_tag=scale` is report-owned state
- refresh should reload the parent report and open the embedded tag detail
- browser Back/Forward should move between report list/detail states without making the tag document a sidebar-selected doc

Report state parameters should remain namespaced or clearly owned by the report.
For a generic implementation, prefer report-prefixed state such as `report_tag=scale`.

## Parent Report Config

A normal indexed document opts into the generic sub-scope report with front matter:

```yaml
viewer_report: docs_subscope
viewer_report_subscope: tags
viewer_report_detail_param: report_tag
```

Required fields:

- `viewer_report`: selects the generic `docs_subscope` report module
- `viewer_report_subscope`: names the Docs Viewer sub-scope whose manifest the report loads
- `viewer_report_detail_param`: names the report-owned URL query parameter containing the selected detail `doc_id`

The sub-scope is configured by the parent document payload, not by a URL query parameter.
This prevents a generic report from becoming an arbitrary sub-scope loader.

## Generic Report Behavior

The `docs_subscope` report should follow this behavior:

- receive normalized report config from the selected parent document payload
- validate `viewer_report_subscope` against the selected scope's configured sub-scopes
- load the sub-scope `manifest.json`
- read the configured detail query parameter from the current URL
- derive the detail payload URL from the selected scope, configured sub-scope, and selected detail `doc_id`
- derive list labels and filter metadata from the parent report config, sub-scope config, or semantic target data
- when the detail query parameter is absent, render the list from manifest `doc_ids`
- when the detail query parameter is present and matches a manifest `doc_ids` entry, load the derived by-id payload URL and render it in the embedded detail region
- when the detail query parameter is present but missing from the manifest, render a contained report error and keep the parent document selected
- update only report-owned URL state when list rows, back, or close actions are used
- never update Docs Viewer selected-document state to the sub-scope detail document

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

Detail documents should be first-class Docs Viewer documents at the source/build layer.
They need the normal `build_docs.py` pipeline because detail docs may themselves use Docs Viewer features such as:

- media tokens
- semantic reference tokens
- doc-to-doc links
- rendered Markdown and raw HTML
- report front matter such as `viewer_report`
- normal generated by-id payloads

The embedded-detail pattern changes discovery and presentation.
It should not create a second, weaker document format.

For tag docs, the detail doc id should be derived from the tag key so payload URLs are predictable.

Required shape:

- tag/detail docs live as Docs Viewer source Markdown docs in a configured sub-scope
- `build_docs.py` renders them into normal by-id payloads
- generated by-id payloads remain loadable by the parent report
- discovery policy keeps large detail sets out of the sidebar and global docs search

The chosen implementation should preserve:

- full Docs Viewer rendering features
- stable detail ids
- rendered HTML from authored/generated Markdown
- normal by-id metadata such as `title`, `last_updated`, and front matter-derived fields
- direct loading by the parent report
- no automatic inclusion in global Docs Viewer search
- no automatic inclusion in the Docs Viewer index tree

## Detail Identity

Sub-scope detail `doc_id` values only need to be unique within their owning `<scope>/<sub-scope>`.
They do not need to be unique across the whole parent scope.

Runtime detail identity is resolved from:

```text
<scope> + <parent_report_doc_id> + <detail_param_value>
```

The parent report document supplies the sub-scope through `viewer_report_subscope`.
For example, this URL:

```text
/docs/?scope=analysis&doc=analytics-tags&report_tag=scale
```

resolves `scale` through the `analytics-tags` report configuration.
That report configuration identifies the sub-scope, so the raw detail `doc_id` does not have to be scope-global.

Cross-report references, logs, caches, and semantic-reference outputs should not treat raw detail `doc_id` as globally unique.
They should preserve enough context to resolve through the parent report config, or use a composite identity such as `<scope>/<sub-scope>/<doc_id>`.

## Manifest JSON Contract

Each sub-scope should publish a minimal manifest used by the generic report.
The manifest is an existence and ordering contract; it is not an `index-tree.json`.
For public scopes such as `/analysis/`, the manifest should avoid repeating data that can be derived from the parent report payload, sub-scope config, or semantic target data.

Required manifest fields:

```json
{
  "doc_ids": "materiality,scale,rhythm"
}
```

Field requirements:

- `doc_ids`: comma-delimited ordered list of stable detail document ids

The report derives all other information:

- parent scope: current Docs Viewer scope
- sub-scope: `viewer_report_subscope` from the parent document payload
- selected detail id: value of `viewer_report_detail_param` from the current URL
- by-id payload URL: sub-scope generated-data config plus selected detail id
- list labels, grouping, filters, and search data: parent report config, sub-scope config, or semantic target data

The comma-delimited format requires detail document ids to exclude commas.
That should be enforced by the sub-scope builder.

## By-Id JSON Contract

Each sub-scope document should publish the same by-id JSON shape as a normal Docs Viewer document.
The embedded-detail pattern changes where the document is displayed, not what kind of document payload is generated.

The by-id payload should keep the normal rendered content and metadata fields, including:

- `doc_id`
- `title`
- `last_updated`
- `content_html`
- front matter-derived fields exposed by the normal by-id payload contract

Keeping the full by-id shape preserves the option to promote a sub-scope document into an indexed document later without changing its source Markdown model or generated payload semantics.
The generic `docs_subscope` report renders `content_html`, but it should pass through or make available the remaining by-id metadata for headings, detail-state labels, diagnostics, and future promotion workflows.

## Build Approach

Prefer extending the modular Docs Viewer builder rather than creating a second renderer.
`build_docs.py` should remain the orchestration entrypoint.

The implementation can add a small sub-scope builder module under `docs-viewer/build/docs_builder/` that reuses the existing pipeline:

- source parsing and front matter normalization
- Markdown and raw HTML rendering
- media token resolution
- semantic reference token resolution
- doc-link rewriting policy
- deterministic payload writing

The sub-scope changes the output contract, not the rendering model.
For local/manage tag docs, an output shape such as this is acceptable:

```text
docs-viewer/generated/docs/studio/tags/by-id/<tag-id>.json
docs-viewer/generated/docs/studio/tags/manifest.json
```

For public scopes, the configured output may need to live under `site/...`, for example:

```text
site/assets/data/docs/scopes/library/tags/by-id/<tag-id>.json
site/assets/data/docs/scopes/library/tags/manifest.json
```

Do not hardcode `studio` or `tags` as the only sub-scope shape.
The source, working output, and public output should derive from the parent scope and sub-scope config.

The manifest lists detail `doc_id` values so the report can validate and order detail payloads without loading a large tree or search index.
The report derives by-id payload URLs from sub-scope config.

The builder should not emit normal `index-tree.json`, recently-added, or global docs-search records for sub-scopes unless a separate discovery policy explicitly asks for them.

## Sub-Scope Config

This should be sub-scope-config driven, not hardcoded for tags.
Sub-scopes should be declared in the same Docs Viewer scope config file as normal scopes, nested under their parent scope record.
They should not be top-level scopes.

A Docs Viewer sub-scope should declare at least:

- sub-scope id
- source root, usually `docs-viewer/source/<scope>/<sub-scope>/`
- working output root, usually `docs-viewer/generated/docs/<scope>/<sub-scope>/`
- optional public output root for public scopes, usually `site/assets/data/docs/scopes/<scope>/<sub-scope>/`
- optional semantic target kind

Example nested config shape:

```json
{
  "scope_id": "analysis",
  "source": "docs-viewer/source/analysis",
  "output": "docs-viewer/generated/docs/analysis",
  "publish_output": "site/assets/data/docs/scopes/analysis",
  "sub_scopes": [
    {
      "sub_scope": "tags",
      "source": "docs-viewer/source/analysis/tags",
      "output": "docs-viewer/generated/docs/analysis/tags",
      "publish_output": "site/assets/data/docs/scopes/analysis/tags",
      "semantic_kind": "tag"
    }
  ]
}
```

The parent scope config should provide enough browser-facing projection for the generic report to derive:

```text
manifest: site/assets/data/docs/scopes/<scope>/<sub-scope>/manifest.json
by-id: site/assets/data/docs/scopes/<scope>/<sub-scope>/by-id/<doc_id>.json
```

Docs Viewer should own the source Markdown and generated payload contract for sub-scope documents.
Domain apps should own source data that sub-scope documents and reports consume through semantic tokens or semantic target data.

Ownership examples:

- Analytics owns tag registry data and tag semantic target data
- Studio/catalogue owns series source data and series semantic target data
- Docs Viewer owns sub-scope source Markdown, rendering, generated detail payload shape, manifests, lifecycle actions, and report embedding mechanics

## Sub-Scope Lifecycle

Sub-scopes should be managed in Docs Viewer, alongside normal scope management, with dedicated lifecycle actions:

- `New sub-scope`
- `Delete sub-scope`

These actions should be scoped to the selected parent scope.
They should not create a new public route, add the sub-scope to the main scope selector, or make sub-scope documents directly selectable from the main Docs Viewer sidebar.

Deleting a sub-scope can remove many source documents and generated payloads, so it should use the same preview and confirm pattern as deleting a normal scope.

## Constraints To Examine

The revised model depends on these constraints:

- A sub-scope should not behave like a full scope in the scope selector or route model.
- Main scope builders must explicitly ignore `docs-viewer/source/<scope>/<sub-scope>/` for `index-tree.json`, recently-added, and search.
- Sub-scope builders should still reuse the normal Docs Viewer Markdown, media-token, semantic-reference-token, link-rewriting, and payload-writing pipeline.
- Published sub-scope payloads should include a minimal manifest, for example `site/assets/data/docs/scopes/<scope>/<sub-scope>/manifest.json`, so the report can validate and order detail ids without loading a tree or search index.
- Detail ids are unique within their owning `<scope>/<sub-scope>`; cross-report references, logs, caches, and semantic-reference outputs need parent report context or a composite identity.
- Report URL params should be report-owned and preferably prefixed, such as `report_tag=scale`, to avoid collisions with Docs Viewer route state.
- `Delete sub-scope` needs preview and confirmation because it can remove source docs, working generated payloads, and published payloads.
- Domain data should enter sub-scope documents and reports through semantic tokens or semantic target payloads, not by moving Docs Viewer rendering into Analytics or Studio app code.
- Public sub-scope publishing should be handled by the existing parent-scope `Publish` action and should not introduce an implicit deploy-time copy step.
- Public manifests should not repeat scope, sub-scope, title, payload URL, grouping, filter, or search data when those values can be derived from config or semantic target data.

## Build Entrypoint

Keep the executable entrypoint in Docs Viewer so rendering authority stays centralized.
Sub-scopes should be selected by config or CLI arguments, for example:

```bash
./docs-viewer/build/build_docs.py --scope studio --sub-scope tags --write
./docs-viewer/build/build_docs.py --scope studio --sub-scope series --write
```

The sub-scope source root should normally live under the Docs Viewer source tree for the parent scope.
The report and documents may consume app-owned data through semantic tokens or semantic target payloads.

The implementation delta should stay small:

- keep `build_docs.py` as a CLI/orchestration layer
- add config for sub-scope sources and outputs
- reuse existing renderer and token modules
- write by-id detail payloads and a minimal manifest
- avoid adding sidebar/search behavior to the sub-scope by default

The main design risk is link semantics, not rendering.
Detail docs may contain same-scope doc links, semantic references, or links to other detail docs.
The implementation should decide whether those links resolve to:

- ordinary Docs Viewer routes
- embedded report-detail URLs such as `?doc=analytics-tags&report_tag=scale`
- report-owned URLs supplied by the report

For tag semantic references, the intended behavior is embedded report-detail navigation.
A semantic token such as:

```text
[[ref:tag:slow-looking]]
```

should resolve to the indexed tag report document with tag detail state, for example:

```text
/docs/?scope=studio&doc=analytics-tags&report_tag=slow-looking
```

It should not resolve to a standalone non-indexed tag document route.

That decision should be made before detail docs depend heavily on cross-detail navigation.
It is especially important before enabling tag semantic tokens in [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor).

## Discovery Model

Report-owned discovery is required.

For tag documents:

- Analytics tag rows should link to the corresponding detail state
- the tag registry report should list tag docs with tag-specific filters and metadata
- the Docs Viewer index should include high-level entry points such as `Tags`, `Tag Groups`, or `Analytics Vocabulary`
- global docs search should not automatically include every tag detail document
- a separate tag-doc search mode or lazy-loaded tag search index can be added later if needed

For series documents:

- catalogue series UI or reports should link to the corresponding series detail state
- a catalogue series report should list series docs with catalogue-specific filters and metadata
- global docs search should not automatically include every series detail document

This avoids treating hundreds of detail docs as first-class Docs Viewer route documents while still giving each domain record a real Docs Viewer-rendered document payload.

## Runtime Boundary

Docs Viewer owns:

- active scope
- active parent/report document
- sidebar tree selection
- parent document payload rendering
- report mounting hook

The report owns:

- domain data loading
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
- detail payloads are loadable only through the report or report-owned links
- global docs search does not have to include detail docs
- the existing parent-scope `Publish` action should include configured sub-scope manifests and by-id payloads in the same publish preview/apply flow

Manage behavior:

- parent/report doc behaves like any report-backed docs document
- detail payload loading should work through the local generated-read service when available
- source/edit workflows for sub-scope detail docs should use the Docs Viewer sub-scope source model

## Implementation Checklist

### 1. Config Foundation

- [ ] Extend the Docs Viewer scope config schema to allow `sub_scopes` nested under a parent scope.
- [ ] Add validation for sub-scope ids, source paths, output paths, publish paths, and duplicate ids within a parent scope.
- [ ] Add a browser-facing projection for configured sub-scopes so reports can derive manifest and by-id payload URLs.
- [ ] Define how parent scope source discovery recognizes configured sub-scope directories before builder changes are made.

### 2. Sub-Scope Lifecycle Actions

- [ ] Add management-service capability data for sub-scope create/delete availability per parent scope.
- [ ] Add `New sub-scope` management UI and service actions that create the nested config entry and source/output folders.
- [ ] Add `Delete sub-scope` preview and apply actions that cover source docs, working generated payloads, and published payloads.
- [ ] Make lifecycle actions operate within the selected parent scope rather than creating top-level scopes.
- [ ] Add focused lifecycle tests for new/delete sub-scope config and file effects.

### 3. Manual Seed Content

- [ ] Manually create a configured sub-scope for the first target public scope, such as `analysis`.
- [ ] Manually add a small set of source Markdown docs under `docs-viewer/source/<scope>/<sub-scope>/`.
- [ ] Confirm source doc front matter uses normal Docs Viewer document fields so promotion to indexed docs remains possible.
- [ ] Confirm detail `doc_id` values are stable and contain no commas.

### 4. Sub-Scope Builder

- [ ] Update source discovery so parent scope builds ignore sub-scope source directories for `index-tree.json`, recently-added, and search.
- [ ] Add a sub-scope build path to `build_docs.py`, selected by `--scope <scope> --sub-scope <sub-scope>`.
- [ ] Reuse the normal Docs Viewer source parsing, front matter normalization, Markdown rendering, media token, semantic reference token, and link rewriting pipeline for sub-scope docs.
- [ ] Write normal by-id payloads for sub-scope docs under the configured sub-scope output root.
- [ ] Write `manifest.json` with only the ordered comma-delimited `doc_ids` field.
- [ ] Enforce that sub-scope detail `doc_id` values do not contain commas.
- [ ] Add focused builder tests for sub-scope by-id payloads, minimal manifest output, and parent-scope exclusion from tree/search/recently-added.

### 5. Publish Flow

- [ ] Add parent-scope publish preview support for configured sub-scope manifests and by-id payloads.
- [ ] Add parent-scope publish apply support for copying configured sub-scope manifests and by-id payloads to the public publish root.
- [ ] Ensure public sub-scope publishing remains part of the existing parent-scope `Publish` action.
- [ ] Add focused publish tests for parent-scope publish preview/apply including configured sub-scope outputs.

### 6. Parent Report Page

- [ ] Manually create the indexed parent page that will host the sub-scope report.
- [ ] Add parent page front matter with `viewer_report: docs_subscope`.
- [ ] Add parent page front matter with `viewer_report_access: public` when the report is intended for `/analysis/` or another public scope.
- [ ] Add parent page front matter with `viewer_report_subscope`.
- [ ] Add parent page front matter with `viewer_report_detail_param`.
- [ ] Confirm the parent page remains the selected Docs Viewer document in list and detail URLs.

### 7. Public Report Promotion

- [ ] Revise supported `viewer_report_access` values to `public` and `local`.
- [ ] Define `public` as public-static-route eligible only when the report is explicitly promoted and allowlisted.
- [ ] Define `local` as local `/docs/` only, covering the current manage/local report use cases.
- [ ] Migrate existing report registry defaults and source front matter from `manage` to `local`.
- [ ] Remove `manage` as a long-term access value, or document it as a temporary migration alias with removal criteria.
- [ ] Update report access checks and unavailable messages to use the `public`/`local` model.
- [ ] Confirm the current public route does not mount reports merely because `viewer_report_access: public` is present.
- [ ] Add public route config for the promoted report registry or promoted report metadata needed by `docs_subscope`.
- [ ] Wire public `mountDocumentExtras` support so public report-backed docs can mount allowed report modules.
- [ ] Ensure the public runtime only loads allowlisted public reports and does not expose manage/local reports.
- [ ] Add public-route smoke coverage proving a `viewer_report_access: public` parent doc mounts its promoted report.

### 8. Generic Report Shell

- [ ] Add the `docs_subscope` report registry entry and allowlisted report module.
- [ ] Make the `docs_subscope` report read `viewer_report_subscope` and `viewer_report_detail_param` from the selected parent document payload.
- [ ] Make the `docs_subscope` report load the configured sub-scope manifest.
- [ ] Make the `docs_subscope` report render the list state from manifest `doc_ids`.
- [ ] Make the `docs_subscope` report derive list labels and filters from parent report config, sub-scope config, or semantic target data.

### 9. Embedded Detail View

- [ ] Add the embedded detail section markup and styling.
- [ ] Make the `docs_subscope` report derive by-id payload URLs from scope config, sub-scope config, and selected detail id.
- [ ] Make the `docs_subscope` report render selected detail payload `content_html` inside the embedded detail section.
- [ ] Preserve or expose normal by-id metadata such as `title`, `last_updated`, and front matter-derived fields for detail-state labels and diagnostics.
- [ ] Ensure detail rendering does not change Docs Viewer selected-document state.
- [ ] Add contained report error states for unknown sub-scopes, missing manifests, unknown detail ids, and failed detail payload loads.

### 10. URL State And Links

- [ ] Add report URL-state handling for selecting a detail row, refreshing a detail URL, Back/Forward, and returning to the list.
- [ ] Add semantic-reference link resolution for sub-scope details so tokens such as tags can resolve to the parent report document plus report detail state.
- [ ] Add focused report-runtime tests for list state, detail state, URL refresh, Back/Forward, and missing-detail errors.

## Tests

Focused coverage should prove:

- the parent/report document remains the selected Docs Viewer document in list and detail states
- selecting a row loads the correct detail payload into the report detail region
- Back/close restores the list state
- refresh with report-owned detail URL state reopens the same detail
- the sidebar remains anchored to the parent/report doc
- a parent document with `viewer_report: docs_subscope` passes `viewer_report_subscope` and `viewer_report_detail_param` into the report config
- the generic report loads the configured sub-scope manifest rather than reading a sub-scope from the URL
- the manifest contains the required `doc_ids` field
- the generic report derives by-id payload URLs from sub-scope config and selected detail id
- detail docs are built by `build_docs.py` into normal by-id payloads
- sub-scope by-id payloads preserve normal by-id metadata such as `title`, `last_updated`, and front matter-derived fields
- detail docs can use media tokens, semantic reference tokens, and report front matter through the normal pipeline
- detail docs are not accidentally added to global docs search
- detail docs are not accidentally added to the index tree
- public published payloads include the parent/report and any required detail payloads
- missing detail payloads render a contained report error instead of breaking the parent document
