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

The target pattern is a master/detail report inside a normal Docs Viewer document:

- the indexed parent document remains the active Docs Viewer document
- the parent renders a report or list over the sub-scope document set
- selecting a row loads the corresponding detail document inside or below the report
- the sidebar stays anchored to the indexed parent document
- detail documents remain first-class Docs Viewer source docs built through the normal docs pipeline
- detail documents live in a Docs Viewer sub-scope owned by the parent scope

## Problem

Some Docs Viewer use cases can produce hundreds of document-like records.

Making every detail document a normal Docs Viewer index row creates two problems:

- the index panel becomes too large to scan
- moving those docs out of the index but into global docs search only moves the payload problem from `index-tree.json` to the search index

The better discovery surface is the report, not the Docs Viewer sidebar or global docs search.
Docs Viewer should own the detail Markdown source, report list metadata, rendering pipeline, generated payload shape, sub-scope lifecycle, and embedded detail-document rendering surface.

The ownership model treats these documents as a Docs Viewer sub-scope.
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

- shows the sub-scope list or table
- lets the user select a row

Detail state:

- keeps only a minimal report toolbar visible, containing the back/close action
- completely hides the list and list header
- renders the selected detail document inside the report surface
- provides a back/close action that restores the list state

Search and filter controls are intentionally out of scope for this request.
They need a separate design for metadata, toolbar behavior, and URL state.

Example flow:

```text
Tags

List:
  Materiality
  Scale
  Rhythm
```

Selecting tag `Scale` changes the same indexed parent document into:

```text
[Back to all tags]

<embedded Scale tag document>
```

## URL State

- The active Docs Viewer document should remain the indexed parent/report doc.
- The parent report document binds the generic report to a sub-scope.
- The URL only carries optional report detail state.

Generic shape:

```text
/docs/?scope=<scope>&doc=<parent_doc_id>
/docs/?scope=<scope>&doc=<parent_doc_id>&subdoc=<detail_doc_id>
```

Example with the standard `subdoc` detail parameter:

```text
/docs/?scope=studio&doc=analytics-tags
/docs/?scope=studio&doc=analytics-tags&subdoc=scale
```

In the second URL:

- `doc=analytics-tags` is still the Docs Viewer selected document
- `subdoc=scale` is report-owned state
- refresh should reload the parent report and open the embedded tag detail
- browser Back/Forward should move between report list/detail states without making the tag document a sidebar-selected doc

`subdoc` is the standard detail-state parameter for the generic `docs_subscope` report.

## Parent Report Config

A normal indexed document opts into the generic sub-scope report with front matter:

```yaml
viewer_report: docs_subscope
viewer_report_subscope: tags
```

Required fields:

- `viewer_report`: selects the generic `docs_subscope` report module
- `viewer_report_subscope`: names the Docs Viewer sub-scope whose manifest the report loads

The sub-scope is configured by the parent document payload, not by a URL query parameter.
This prevents a generic report from becoming an arbitrary sub-scope loader.

## Generic Report Behavior

The `docs_subscope` report should follow this behavior:

- receive normalized report config from the selected parent document payload
- validate `viewer_report_subscope` against the selected scope's configured sub-scopes
- load the sub-scope `manifest.json`
- read the `subdoc` query parameter from the current URL
- derive the detail payload URL from the selected scope, configured sub-scope, and selected detail `doc_id`
- derive list labels from the explicit report list metadata sources below
- when `subdoc` is absent, render the list from manifest `doc_ids`
- when `subdoc` is present and matches a manifest `doc_ids` entry, load the derived by-id payload URL and render it in the embedded detail region
- when `subdoc` is present but missing from the manifest, render a contained report error and keep the parent document selected
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

- The report loads the selected detail payload and renders its `content_html` into `docsReportDetail__body`.
- The embedded detail body should reuse the normal Docs Viewer rendered-document styling. The report-specific detail wrapper should only provide containment, spacing, and the single-row report toolbar; it should not redefine document typography, table, image, or link styles.
- The embedded document should not be placed inside a panel, card, or secondary document frame. It should use the available document content area just like a normal indexed document would.
- The transition from report controls to embedded document should be minimal, such as a pale divider line. After that divider, the embedded document should look like a normal rendered document, including its title and content.
- Any content before the report controls belongs in the authored parent report document and should render normally.

## Detail Document Payloads

Detail documents should be first-class Docs Viewer documents at the source/build layer.
They need the normal `build_docs.py` pipeline because detail docs may themselves use Docs Viewer features such as:

- media tokens
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
<scope> + <parent_report_doc_id> + <subdoc>
```

The parent report document supplies the sub-scope through `viewer_report_subscope`.
For example, this URL:

```text
/docs/?scope=analysis&doc=analytics-tags&subdoc=scale
```

resolves `scale` through the `analytics-tags` report configuration.
That report configuration identifies the sub-scope, so the raw detail `doc_id` does not have to be scope-global.

Cross-report references, logs, and caches should not treat raw detail `doc_id` as globally unique.
They should preserve enough context to resolve through the parent report config, or use a composite identity such as `<scope>/<sub-scope>/<doc_id>`.

## Manifest JSON Contract

- Each sub-scope should publish a minimal manifest used by the generic report. The manifest is an existence and ordering contract; it is not an `index-tree.json`.

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
- selected detail id: value of `subdoc` from the current URL
- by-id payload URL: sub-scope generated-data config plus selected detail id
- list labels: the explicit report list metadata sources below

The comma-delimited format requires detail document ids to exclude commas.
That should be enforced by the sub-scope builder.

Sub-scope detail documents may still carry normal Docs Viewer metadata such as `parent_id` because the builder reuses the normal document pipeline.
The initial `docs_subscope` report should not treat that metadata as list hierarchy.
If a report needs to render parent-child grouping or nested detail navigation later, that should be a subsequent report modification that reads explicit report/list metadata or by-id metadata and keeps the manifest contract as the minimal ordered `doc_ids` list.

## Report List Metadata Sources

The minimal manifest only lists `doc_ids`.
The `docs_subscope` report should read labels from explicit runtime sources:

- generated parent by-id payload in `docs-viewer/generated/docs/<scope>/by-id/<parent_doc_id>.json`
- published parent by-id payload in `site/assets/data/docs/scopes/<scope>/by-id/<parent_doc_id>.json`
- parent/sub-scope config in `docs-viewer/config/scopes/docs_scopes.json`
- browser-facing sub-scope projection generated from `docs-viewer/config/scopes/docs_scopes.json`
- report implementation in `docs-viewer/runtime/js/reports/docs-subscope-report.js`
- report loader allowlist in `docs-viewer/runtime/js/reports/docs-viewer-reports.js`

Public reports must read only browser-safe generated or published projections.
Reports must not read source Markdown files directly.
Parent page front matter is available to reports only after the Docs Viewer builder has normalized it into the generated parent by-id payload.

## By-Id JSON Contract

Each sub-scope document should publish the same by-id JSON shape as a normal Docs Viewer document.
The embedded-detail pattern changes where the document is displayed, not what kind of document payload is generated.

The by-id payload should keep the normal rendered content and metadata fields, including:

- `doc_id`
- `title`
- `last_updated`
- `content_html`
- front matter-derived fields exposed by the normal by-id payload contract

Keeping the full by-id shape preserves the option to promote a sub-scope document into an indexed document later without changing its source Markdown model or generated payload contract.
The generic `docs_subscope` report renders `content_html`, but it should pass through or make available the remaining by-id metadata for headings, detail-state labels, diagnostics, and future promotion workflows.

## Build Approach

`build_docs.py` remains the orchestration entrypoint. The implementation should add a small sub-scope builder module under `docs-viewer/build/docs_builder/` that reuses the existing pipeline:

- source parsing and front matter normalization
- Markdown and raw HTML rendering
- media token resolution
- doc-link rewriting policy
- deterministic payload writing

The sub-scope changes the output contract, not the rendering model.
The builder writes working generated JSON under `docs-viewer/...` for every scope, including public scopes:

```text
docs-viewer/generated/docs/<scope>/<sub-scope>/by-id/<doc_id>.json
docs-viewer/generated/docs/<scope>/<sub-scope>/manifest.json
```

For public scopes, the existing parent-scope `Publish` action copies the working generated sub-scope payloads to the public snapshot under `site/...`:

```text
site/assets/data/docs/scopes/<scope>/<sub-scope>/by-id/<doc_id>.json
site/assets/data/docs/scopes/<scope>/<sub-scope>/manifest.json
```

The builder should not write public snapshots directly.
The source, working output, and publish output should derive from the parent scope and sub-scope config.

The manifest lists detail `doc_id` values so the report can validate and order detail payloads without loading a large tree or search index.
The report derives by-id payload URLs from sub-scope config.

The builder should not emit normal `index-tree.json`, recently-added, or global docs-search records for sub-scopes.

The Docs Live Rebuild Watcher should be updated with the same sub-scope boundary.
When a configured sub-scope source file changes, the watcher should trigger the sub-scope build path for that parent scope and sub-scope.
It should not run parent-scope docs/search rebuilds for sub-scope-only changes, and it should not treat configured sub-scope Markdown as invalid nested source.
If scope config changes add or remove sub-scopes while the watcher is running, the watcher needs a safe refresh path or a clear restart requirement so stale config cannot misclassify sub-scope files.
Publishing remains separate: watcher rebuilds working generated payloads only, while public sub-scope snapshots are copied by the existing parent-scope `Publish` action.

## Sub-Scope Config

This should be sub-scope-config driven, not hardcoded for tags.
Sub-scopes should be declared in the same Docs Viewer scope config file as normal scopes, nested under their parent scope record.
They should not be top-level scopes.

A Docs Viewer sub-scope should declare:

- sub-scope id
- source root `docs-viewer/source/<scope>/<sub-scope>/`
- working output root `docs-viewer/generated/docs/<scope>/<sub-scope>/`
- public output root for public scopes `site/assets/data/docs/scopes/<scope>/<sub-scope>/`

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
      "publish_output": "site/assets/data/docs/scopes/analysis/tags"
    }
  ]
}
```

The parent scope config should provide enough browser-facing projection for the generic report to derive:

```text
manifest: site/assets/data/docs/scopes/<scope>/<sub-scope>/manifest.json
by-id: site/assets/data/docs/scopes/<scope>/<sub-scope>/by-id/<doc_id>.json
```

Docs Viewer owns sub-scope source Markdown, rendering, generated detail payload shape, manifests, lifecycle actions, and report embedding mechanics

## Sub-Scope Lifecycle

Sub-scopes should be managed in Docs Viewer, alongside normal scope management, with dedicated lifecycle actions in the UI 'Actions' button:

- `New sub-scope`
- `Delete sub-scope`

These actions should be scoped to the selected parent scope.
They should not create a new public route, add the sub-scope to the main scope selector, or make sub-scope documents directly selectable from the main Docs Viewer sidebar.

- The `New sub-scope` modal should use the active Docs Viewer scope as the parent scope.
- The user should only need to provide the sub-scope id and confirm or edit the derived title.
- Sub-scopes do not have a default document concept, so the modal should not ask for `default_doc_id`.

Deleting a sub-scope can remove many source documents and generated payloads, so it should use the same preview and confirm pattern as deleting a normal scope.

## Constraints

The model depends on these constraints:

- A sub-scope should not behave like a full scope in the scope selector or route model.
- Main scope builders must explicitly ignore `docs-viewer/source/<scope>/<sub-scope>/` for `index-tree.json`, recently-added, and search.
- Sub-scope builders should still reuse the normal Docs Viewer Markdown, media-token, link-rewriting, and payload-writing pipeline.
- Published sub-scope payloads should include a minimal manifest, for example `site/assets/data/docs/scopes/<scope>/<sub-scope>/manifest.json`, so the report can validate and order detail ids without loading a tree or search index.
- Detail ids are unique within their owning `<scope>/<sub-scope>`; cross-report references, logs, and caches need parent report context or a composite identity.
- `subdoc` should remain reserved as the standard detail-state URL parameter for `docs_subscope`; other reports should continue to use report-owned params.
- `Delete sub-scope` needs preview and confirmation because it can remove source docs, working generated payloads, and published payloads.
- Public sub-scope publishing should be handled by the existing parent-scope `Publish` action and should not introduce an implicit deploy-time copy step.
- Public manifests should not repeat scope, sub-scope, title, payload URL, or label data because those values are derived from explicit report metadata sources.

## Build Entrypoint

Keep the executable entrypoint in Docs Viewer so rendering authority stays centralized.
Sub-scopes should be selected by config or CLI arguments, for example:

```bash
./docs-viewer/build/build_docs.py --scope studio --sub-scope tags --write
./docs-viewer/build/build_docs.py --scope studio --sub-scope series --write
```

The sub-scope source root lives under the Docs Viewer source tree for the parent scope.

The implementation delta should stay small:

- keep `build_docs.py` as a CLI/orchestration layer
- add config for sub-scope sources and outputs
- reuse existing renderer and token modules
- write by-id detail payloads and a minimal manifest as described above
- do not add sidebar/search behavior to the sub-scope

The main design risk is link resolution, not rendering.
Detail docs may contain normal same-scope doc links or links to other sub-scope docs.
Those links will need to resolve to:

- ordinary Docs Viewer routes, or
- embedded report-detail URLs such as `?doc=analytics-tags&subdoc=scale`

For sub-scope detail links, the intended behavior is embedded report-detail navigation.
A link to a detail document should resolve to the indexed report document with detail state, for example:

```text
/docs/?scope=studio&doc=analytics-tags&subdoc=slow-looking
```

## Runtime Boundary

Docs Viewer owns:

- active scope
- active parent/report document
- sidebar tree selection
- parent document payload rendering
- report mounting hook

The report owns:

- selected detail id
- embedded detail payload loading
- detail-region rendering
- report-owned URL parameters

Future search and filter controls, if added, should also remain report-owned and should not change the selected Docs Viewer document.

The report should fetch the derived sub-scope by-id payload URL as report data.
Fetching a detail payload must not update Docs Viewer selected-document state.

## Public And Manage Behavior

The pattern should work in both `/docs/` and public read-only scopes when the report and its payloads are published for that scope.

Public behavior:

- parent/report doc appears in the public index when viewable
- detail payloads are loadable only through the report or report-owned links
- global docs search does not have to include detail docs
- the existing parent-scope `Publish` action should include configured sub-scope manifests and by-id payloads in the same publish preview/apply flow

Manage behavior:

- parent/report doc behaves like any report-backed docs document
- existing manage tools such as edit metadata apply to the indexed parent/report document, not to the embedded sub-scope detail document
- this implementation does not make sub-scope detail documents visible as normal standalone manage-mode docs outside the report
- source/edit workflows for sub-scope detail docs need a separate design

## Implementation Checklist

### 1. Config Foundation

- [x] Extend the Docs Viewer scope config schema to allow `sub_scopes` nested under a parent scope.
- [x] Add validation for sub-scope ids, source paths, output paths, publish paths, and duplicate ids within a parent scope.
- [x] Add a browser-facing projection for configured sub-scopes so reports can derive manifest and by-id payload URLs.
- [x] Define how parent scope source discovery recognizes configured sub-scope directories before builder changes are made.

### 2. Sub-Scope Lifecycle Actions

- [x] Add management-service capability data for sub-scope create/delete availability per parent scope.
- [x] Add `New sub-scope` management UI that uses the active scope as the parent scope.
- [x] Make the `New sub-scope` modal ask only for sub-scope id and title confirmation/editing, with no default-doc input.
- [x] Add `New sub-scope` service actions that create the nested config entry and source/output folders.
- [x] Add `Delete sub-scope` preview and apply actions that cover source docs, working generated payloads, and published payloads.
- [x] Make lifecycle actions operate within the selected parent scope rather than creating top-level scopes.
- [x] Add focused lifecycle tests for new/delete sub-scope config and file effects.

### 3. Manual Seed Content

- [x] Manually create a configured sub-scope for the first target public scope, such as `analysis`.
- [x] Manually add a small set of source Markdown docs under `docs-viewer/source/<scope>/<sub-scope>/`.
- [x] Confirm source doc front matter uses normal Docs Viewer document fields so promotion to indexed docs remains possible.
- [x] Confirm detail `doc_id` values are stable and contain no commas.

### 4. Sub-Scope Builder

- [x] Update source discovery so parent scope builds ignore sub-scope source directories for `index-tree.json`, recently-added, and search.
- [x] Add a sub-scope build path to `build_docs.py`, selected by `--scope <scope> --sub-scope <sub-scope>`.
- [x] Reuse the normal Docs Viewer source parsing, front matter normalization, Markdown rendering, media token, and link rewriting pipeline for sub-scope docs.
- [x] Write normal by-id payloads for sub-scope docs under the configured sub-scope output root.
- [x] Write `manifest.json` with only the ordered comma-delimited `doc_ids` field.
- [x] Enforce that sub-scope detail `doc_id` values do not contain commas.
- [x] Update the Docs Live Rebuild Watcher so configured sub-scope source changes run the sub-scope build path and do not trigger parent index/search rebuilds.
- [x] Ensure watcher config refresh or restart behavior is explicit so newly configured sub-scope roots are not reported as unsupported nested Markdown.
- [x] Add focused builder tests for sub-scope by-id payloads, minimal manifest output, and parent-scope exclusion from tree/search/recently-added.
- [ ] Add focused watcher tests for sub-scope source changes, parent-scope exclusion, and config-refresh or restart behavior.

### 5. Publish Flow

- [x] Add parent-scope publish preview support for configured sub-scope manifests and by-id payloads.
- [x] Add parent-scope publish apply support for copying configured sub-scope manifests and by-id payloads to the public publish root.
- [x] Ensure public sub-scope publishing remains part of the existing parent-scope `Publish` action.
- [x] Add focused publish tests for parent-scope publish preview/apply including configured sub-scope outputs.

### 6. Parent Report Page

- [x] Manually create the indexed parent page that will host the sub-scope report.
- [x] Add parent page front matter with `viewer_report: docs_subscope`.
- [x] Add parent page front matter with `viewer_report_access: public` when the report is intended for `/analysis/` or another public scope.
- [x] Add parent page front matter with `viewer_report_subscope`.
- [x] Confirm the parent page remains the selected Docs Viewer document in list and detail URLs.

### 7. Public Report Promotion

- [x] Revise supported `viewer_report_access` values to `public` and `local`.
- [x] Define `public` as public-static-route eligible only when the report is explicitly promoted and allowlisted.
- [x] Define `local` as local `/docs/` only, covering the current manage/local report use cases.
- [x] Migrate existing report registry defaults and source front matter from `manage` to `local`.
- [x] Remove `manage` as a long-term access value, or document it as a temporary migration alias with removal criteria.
- [x] Update report access checks and unavailable messages to use the `public`/`local` model.
- [x] Confirm the current public route does not mount reports merely because `viewer_report_access: public` is present.
- [x] Add public route config for the promoted report registry or promoted report metadata needed by `docs_subscope`.
- [x] Wire public `mountDocumentExtras` support so public report-backed docs can mount allowed report modules.
- [x] Ensure the public runtime only loads allowlisted public reports and does not expose manage/local reports.
- [x] Add public-route smoke coverage proving a `viewer_report_access: public` parent doc mounts its promoted report.

### 8. Generic Report Shell

- [x] Add the `docs_subscope` report registry entry and allowlisted report module.
- [x] Make the `docs_subscope` report read `viewer_report_subscope` from the selected parent document payload.
- [x] Make the `docs_subscope` report load the configured sub-scope manifest.
- [x] Make the `docs_subscope` report render the list state from manifest `doc_ids`.
- [x] Make the `docs_subscope` report derive list labels from explicit report metadata sources.

Implemented step 8’s generic report shell. The `docs_subscope` report is registered, public-allowlisted, loads the configured sub-scope manifest, and renders the manifest `doc_ids` as a report-owned list. Public route shells now ship the shared report stylesheet so the promoted report renders with the same report list classes as local reports. The current shell does not load embedded detail payloads or mutate `subdoc` URL state; those remain in steps 9 and 10.

### 9. Embedded Detail View

- [ ] Add embedded detail markup that uses the normal document content area with only minimal report controls and a simple divider, not a panel or card.
- [ ] Make the `docs_subscope` report derive by-id payload URLs from scope config, sub-scope config, and selected detail id.
- [ ] Make the `docs_subscope` report hide the list and list header completely in detail state, leaving only a minimal back/close control.
- [ ] Make the `docs_subscope` report render selected detail payload `content_html` inside the embedded detail section.
- [ ] Preserve normal by-id metadata such as `title`, `last_updated`, and front matter-derived fields for detail-state labels and diagnostics.
- [ ] Ensure detail rendering does not change Docs Viewer selected-document state.
- [ ] Add contained report error states for unknown sub-scopes, missing manifests, unknown detail ids, and failed detail payload loads.

### 10. URL State And Links

- [ ] Add report URL-state handling for selecting a detail row, refreshing a detail URL, Back/Forward, and returning to the list.
- [ ] Add link resolution for sub-scope details so detail links resolve to the parent report document plus report detail state.
- [ ] Add focused report-runtime tests for list state, detail state, URL refresh, Back/Forward, and missing-detail errors.

## Tests

Focused coverage should prove:

- the parent/report document remains the selected Docs Viewer document in list and detail states
- selecting a row loads the correct detail payload into the report detail region
- Back/close restores the list state
- refresh with report-owned detail URL state reopens the same detail
- the sidebar remains anchored to the parent/report doc
- a parent document with `viewer_report: docs_subscope` passes `viewer_report_subscope` into the report config
- the generic report loads the configured sub-scope manifest rather than reading a sub-scope from the URL
- the manifest contains the required `doc_ids` field
- the generic report derives by-id payload URLs from sub-scope config and selected detail id
- detail docs are built by `build_docs.py` into normal by-id payloads
- sub-scope by-id payloads preserve normal by-id metadata such as `title`, `last_updated`, and front matter-derived fields
- detail docs can use media tokens, doc links, and report front matter through the normal pipeline
- detail docs are not accidentally added to global docs search
- detail docs are not accidentally added to the index tree
- public published payloads include the parent/report and any required detail payloads
- missing detail payloads render a contained report error instead of breaking the parent document
