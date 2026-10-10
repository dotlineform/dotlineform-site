---
draft: false
doc_id: d-20260513-105343-6de36b
title: Reports
added_date: "2026-05-13 10:53:43"
last_updated: "2026-10-10 20:01:05"
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Reports

Docs Viewer reports are lightweight, document-level inspection surfaces rendered inside the normal Docs Viewer document pane.

They exist so a document can show generated data that is easier to scan as a list, table, or summary than as prose.
The report-backed document still behaves like any other Docs Viewer document: it has a `doc_id`, title, `parent_id`, generated title ordering, visibility, search metadata, and `/docs/` management-route links.

Reports are deliberately not a dashboard or workflow framework.
They are for read-only or inspection-oriented views over Docs Viewer data, not for source edits, imports, exports, rebuilds, or apply flows.

[Report Capability and Composition](Report_Capability_And_Composition.md) owns the durable shared, public, local-only, contribution, data, and stylesheet boundaries. This document retains report metadata, registry behavior, current implementations, and the report inventory.

## Source Contract

A source document opts into one report with one exact block in its Markdown body:

```text
:::report
id: reports_list
:::
```

The opener is exactly `:::report` and the closer is exactly `:::` at column one. The block is isolated from surrounding Markdown by a blank line. Interior lines use unquoted `key: value` syntax; indentation, inline attributes, blank interior lines, duplicate keys, and unknown keys or values fail source validation.

The attributes are:

- `id`: required registered report token
- `preset`: optional registered preset; no current report registers presets
- `collection`: required configured collection for `docs_collection` and forbidden for other reports

A document contains zero or one report block. Report-like examples inside fenced or indented code, inline code, HTML comments, and raw `<pre>` or `<code>` regions remain literal examples. A structural declaration outside those contexts must be complete and valid. The five retired `viewer_report*` front-matter fields are rejected; there is no compatibility or precedence path.

[Report Block Tokens](Report_Block_Tokens.md) is the concise current registry-token reference.

## Build And Payload Flow

The shared Python parser validates the complete source, resolves the registry and configured collection context, and returns one immutable descriptor plus the exact body source range. The document `doc_id` remains the report-host identity.

The builder replaces that exact source range with one inert host:

```html
<section class="docsViewerReport" data-docs-viewer-report-host aria-label="Document report"></section>
```

Only by-ID payloads receive the fixed-shape `report` object:

```json
{
  "id": "reports_list",
  "preset": null,
  "collection": null
}
```

Manage, prepared and public by-ID payloads retain the report descriptor and generated host. Publication does not strip reports or infer eligibility from report type. Index, Recent, Search and manifests do not carry report metadata.

## Report Availability

Report blocks and descriptors have no `access` field. Each environment's registry and executable loader allowlist own availability. Public execution requires a code/config promotion slice:

- the report id must be included in a public-safe report metadata projection
- the executable report loader must be included in the public runtime allowlist
- the public route must expose the browser-safe config and generated data roots the report needs
- the report implementation must avoid local services, management actions, source paths, credentials, and manage-only data

If a public route receives a report without a registered public implementation, it renders a contained unavailable state. Publishing the containing document does not grant service access or promote report code. Excluding an internal document is an explicit ignore-list decision; there is no report-based publication exclusion.

## Runtime Design

[Report Capability and Composition](Report_Capability_And_Composition.md) is authoritative for the permitted dependency direction and for deciding whether a capability is genuinely shared, public, or local-only.

The manage Docs Viewer entrypoint opts into local report mounting through `docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js`.
The shared document controller renders the document payload and calls an optional document-extras hook; it does not import report runtime, report services, or report modules.
Public entrypoints opt into report mounting through `site/docs-viewer/runtime/js/public/docs-viewer-public-document-reports.js`.
Public route config exposes only the public-safe report registry projection at `site/assets/data/docs/public-reports.json`.
Public route shells load `site/docs-viewer/static/css/docs-viewer-reports.css`. Manage additionally loads `docs-viewer/static/css/docs-viewer-local-reports.css` and `docs-viewer/static/css/docs-viewer-manage.css`; public routes load neither local stylesheet.

The entry runtime wires the document controller but does not own report filtering, sorting, row rendering, or report-specific data shaping.

The report controller:

- reads the normalized descriptor from `payload.report`
- requires exactly one generated host inside the current document content and never creates or appends a second root
- loads the report metadata registry supplied by the route config
- normalizes report and preset metadata
- checks the requested report id against the executable module allowlist
- imports the allowed report module and calls its mount function

Navigation replaces the complete document content, which removes the current report host. Stale asynchronous registry, loader, or module work checks that its captured host is still inside the current content before mutating it.

Report modules own their own rendering behavior and route-state parameters. Report state should use report-prefixed URL parameters, such as `report_sort`, so ordinary Docs Viewer route state remains understandable.

A successful local report mount may return an optional validated `expandedPresentation` handle. The handle declares `flow` or `semantic-table` and supplies its exact `toolbar` element inside the report root, where the adapter places the expanded-view control alongside the existing buttons. A semantic table also declares one ordered stable column model, explicit `both` or `expanded` visibility, and a refresh subscription. The control is disabled when that exact table is hidden or has no body rows; the adapter subscribes to presentation refreshes and removes its subscription when releasing the report. Manage can then move the exact live report root into Content Detail without cloning, remounting, or refetching it. Eligibility is never inferred from registry metadata or rendered DOM. The expanded-view control hides within Content Detail and returns with the embedded report. Temporary widths are a Manage-only extension over an exact semantic-table model and are discarded on Reset, Back, or navigation.

## Source And Export Workflows

Direct Source editing retains a report block and validates the complete candidate before writing. Metadata and Draft edits preserve and revalidate the existing block.

In Markdown source mode, **Directives → Related links** inserts `[[links|related links]]` at the captured editor position. This is a build-rendered document section owned by [Related Links](Related_Links.md).

Generic Import rejects incoming report blocks and replacement of an existing report host. Document Transfer copies or moves report-host source unchanged and does not interpret report semantics; each report resolves or reports an error in its destination context. Returned-content Review cannot replace a report host. Rendered document-content packages omit the empty inert host, while static HTML export retains it as inert markup and exports no report registry, executable loader, service, or report JavaScript.

## Registry And Metadata

Report metadata lives in:

- `docs-viewer/config/reports/reports.json`

The browser-visible public projection is:

- `site/assets/data/docs/public-reports.json`

The source registry describes report ids, titles, descriptions, loader ids, and presets.
The public projection includes only report metadata that has been explicitly promoted for public static routes.
The local manage route reads the source registry directly.
Public `/analysis/` and any other public route configs reference only the public projection.

Executable module loading remains allowlisted in:

- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js`

The JSON registry does not define arbitrary import paths.
Adding a JSON entry without a matching allowlisted loader does not make a new report executable.
This keeps the registry useful as user-facing metadata without turning it into an open-ended code-loading surface.

## Presets

Preset validation uses the selected report's registered preset IDs. No current report registers presets; a supplied preset is rejected.

## Current Reports

`workspace_links` is a local diagnostic report hosted by [Links](/docs/?doc=d-20260910-214604-f9e841), whose ordinary ID is in the publication ignore file. `GET /docs/workspace-links` reads only saved `working/generated/documents/links.json` from the configured workspace. An empty-object `POST` to the same route calls `docs_workspace_links.write_workspace_links` to rebuild the aggregate from current `links-by-id` records and returns the saved result. It requires Working authoring capability and rejects dry-run requests; no document rendering, Search rebuild, source writes or freshness checks occur. Stage/scope parameters are rejected. The report is absent from public metadata and executable loaders. [Builder](Builder.md) owns relationship maintenance and the complete **Rebuild docs and Search** operation, which also refreshes this aggregate.

Links has exactly two columns, **from** and **to**, with one row per directed document pair from each record's outgoing entries. Incoming mirrors add no rows; reciprocal links produce two rows, while repeated authored links produce one pair. Both headers toggle ascending/descending title sorting. Initial order is from, then to; the other title and exact endpoint identities break ties. Version 4 uses flat `{collection, doc_id, title}` summaries directly in each incoming/outgoing array, with no occurrence details or stored counts. Each cell displays the prepared title and derives navigation from exact identity and the configured viewer route/collection report host through the shared Links navigation helper. Distinct documents with identical titles remain distinct.

The compact **🔄** Refresh button sits immediately left of the links count on the same row. Initial load reads the saved snapshot. Refresh awaits the aggregation POST and displays its returned data, keeping the button disabled until completion. It acts immediately on the current relationship records; document edits and deletions already processed by their owning build appear without a full workspace rebuild. A valid aggregate with no outgoing links displays an empty state; missing, invalid or unreadable data displays an error with the Refresh instruction. Catalogue pages' embedded Related links sections still update through their own document builds.

`workspace-links-report.js` owns the table and sorting, using the local report service and shared Links presentation. Exact targets contain collection/document identity without stage; navigation keeps the local route and exact report-host/subdocument IDs. The historical scope-bearing test files have not been accepted as evidence for this contract; changes require their own test specification.

`unpublishable` is a local, read-only report hosted by [Unpublishable](/docs/?doc=d-20260909-160530-224efe). `GET /docs/unpublishable-report` rereads configured ordinary Working `source/documents/unpublishable.json` on each load or Refresh through `docs_publication_ignore.py`. The `docs_unpublishable_report_v4` response contains exact document IDs and current source titles without stage. Each title comes from the listed ID's canonical source after identity validation; missing sources retain a null title. There is no collection-wide Markdown scan or draft expansion. Open in VS Code posts an empty object to `/docs/open-publication-ignore`, which opens that configured file. Invalid JSON can still be opened for correction; missing, unreadable and invalid list reads fail visibly, while `[]` is empty. Named-collection documents are outside this policy. Stage/scope parameters are rejected; the report remains absent from public metadata and executable loaders.

The Analysis Documents report (`docs_index_table`) was retired on 2026-09-26. Its implementation, local registry entry, loader, presets, dedicated index-reader adapter and tree-indent style were removed, along with its Working host document.

`reports_list` renders the report metadata registry itself.
This document uses it so the list of configured reports stays visible from the Docs Viewer.

`docs_collection` renders a manifest-ordered list for a configured Docs Viewer collection. It reads `report.collection`, validates that exact owner against the composition's single workspace configuration, loads its configured manifest and renders ordered document identity/title records. Manage reads `manage-manifest.json`; the public reader uses `manifest.json`.
Selecting a row sets `subdoc`, loads the selected collection by-ID payload and renders its `content_html` while the report host remains selected. Collection documents carry no `publishable` field. Working inventories retain boolean `draft`, and drafts remain visible and loadable. The report exposes a validated `{collection, doc_id}` action target only after manifest membership, payload loading and `doc_id` checks succeed. Optional root customisation has exactly `id` and `data`; it is independent of the collection action target.

The shared report accepts an optional caller-owned contribution with detached leading-cell/title-prefix row hosts, list/detail toolbar hosts and collection-owned mount, state, refresh and unmount events. It inserts only populated hosts and offers the detail toolbar only after by-ID identity is valid. The Manage contribution renders shared visual status and an additional 📝 indicator only for `draft: true`. It owns collection-keyed checkbox selection, the compact 🔧 Actions and Select all/Clear/Done controls and the lazy Prepare Package bridge. That bridge supplies exact checked IDs plus `{collection}`, never a selected parent or displayed child fallback. Public callers import no management module.

The local sub-scope Actions menu remains available in every configured collection, including empty lists. Copy and Prepare package remain visible when unavailable, with disabled controls and explanatory tooltips. Set Publishable and its sub-scope callbacks, request handling and service support are removed. Missing workflow support takes precedence over selection prompts; exposing the menu does not enable an unsupported operation.

A registered Manage contribution also receives the validated customisation root data from the loaded manifest. The Working Works contribution owns Subject display and actions. The empty Processing Docs collection was retired on 2026-09-27: its registration, report host, dedicated customisation and collection storage were removed. The separate repository `processing/` project and Projects-owned Processing media remain independent owners.

The shared report does not perform writes or package service calls. The
management host projects
**Parent Source**, **Subdoc Source**, and Edit metadata from that validated
state, passes one explicit `{ scope, doc_id }` or
`{ scope, sub_scope, doc_id }` target to the existing workflows, and remounts
the report after a targeted rebuild. Invalid or unavailable detail state
disables child actions; it never falls back to the displayed text, URL
`subdoc`, or selected parent.

Sub-scope Prepare Package reads the exact flat collection and is always
export-only. Package artifacts do not become public controls or actionable
Returned Packages.

Manage browser config uses local sub-scope manifest/by-ID URLs. Public browser
config uses the public projection and receives no management inventory, state
icons, source controls, or metadata actions.
The durable source, payload, URL, manifest, and lifecycle contract is documented in [Embedded Detail Documents](Embedded_Detail_Documents.md).

The Source Config Report (`source_config`) was retired on 2026-09-26. Its JavaScript renderer, Python report builder, `GET /docs/source-config` endpoint, capability flag, registry entry, loader, client method, dedicated styles and Working host document were removed. Configuration editing remains owned by `/docs/source-config-settings`.

`docs_broken_links` opens the saved Working audit through `GET /docs/broken-links`. Refresh explicitly scans ordinary and configured collection sources and saves a new private JSON snapshot through an empty-object `POST` to the same route. Last scanned time sits beside Refresh, vertically centred, without a broken-link count; unscanned sources remain explanatory rows. Missing data gives an empty report without a first-refresh prompt. Refresh retains loaded results and uses a progress cursor without running messages. [Broken Links Script](Broken_Links_Script.md) owns audit coverage, persistence, failure behavior and the local-only boundary.

`docs_backlinks` (Documents Linking Here), its executable loader, generated `backlinks.json`, browser setting and `/docs/backlinks` endpoint are retired. [Related Links](Related_Links.md) presents persisted incoming and outgoing document relationships through the author-inserted directive. The retired report ID has no registry entry or compatibility alias; old authored report blocks require conversion to the directive and otherwise fail normal unknown-report validation.

The dedicated `docs-viewer/tests/python/test_docs_backlinks_report_contract.py`, backlinks cases in `test_build_docs_payloads.py` and the route list in `docs-viewer/tests/js/docs_viewer_stage_target_contract.mjs` still target retired report/output or scope contracts. They remain unchanged and were not run during retirement. Separately approved cleanup should remove obsolete backlinks coverage while preserving unrelated current coverage; these test consumers do not require a production alias.

`semantic_tokens` and its generated usage index are retired. Work image and Work Media View text tokens now contribute ordinary document relationships to Catalogue subdocuments, presented by [Related Links](Related_Links.md). Gallery Media View tokens create no document relationship. `docs_broken_links` remains the independent authoring audit.

`project_state`, displayed as Projects, is the local project-folder reconciliation report. It first scans every immediate physical project folder and retains unmatched folder rows, then joins Refresh-owned `private/work-sources.json` and `private/series.json` with document Subjects from the configured Working `works` management manifest. Every Series definition remains available, including empty Series. Only Folder- and Work-subject documents participate in placement. Work subjects follow the exact Work's refreshed project folder and Series membership; Folder subjects may apply to every Series represented by Works in that folder. None contributes only to the complete input document count. Placement retains its existing first-level `projects/<project_folder>` interpretation across media sources. Direct Series subjects and the document `series_id` field are retired; Studio Series and their membership remain supported. Run/Refresh assembles the report without changing source or repairing its inputs. Existing response keys, including the `canonical_work_count` and `canonical_series_count` diagnostics, now count the saved Catalogue inputs.

The Projects report's Series column displays each exact response-owned Series title as plain text in both Folder and Series grouping modes. It does not open a Series Media View. Folder links, document links, search, sorting and copied TSV retain their existing behavior.

`docs_media` is the local media-to-document inspection report hosted by [Docs Media](/docs/?doc=d-20260812-212735-6d9cf3). Opening reads saved metadata; Run/Refresh explicitly regenerates it across ordinary and configured collection owners, excluding derived thumbnails. The browser owns joins, exact document links and sortable Collection, Type, File name and Documents columns, with a collection filter and immediate search. File names retain the confined Finder action. The report remains absent from public metadata and executable loaders. [Media And Asset Handling](Media_And_Asset_Handling.md#docs-media-inventory-report) owns the saved-data, freshness and storage boundary.

`work_downloads`, hosted by [Work Downloads](/docs/?doc=d-20261004-202223-1e2205), complements Docs Media with Catalogue attachment coverage. Opening and Run/Refresh read the saved Catalogue `private/work-resources.json` and scan direct regular files in the configured Docs workspace `assets.work_files` family live. Save stages new attachments; Catalogue Refresh advances both their references and Working files before the report adopts them. The local service matches exact stored filenames, including legacy names; Work ID prefixes do not infer ownership. `.DS_Store` and `.gitkeep` placeholders are ignored, directories are not traversed, and unavailable storage, invalid data or symlinks fail visibly. No report snapshot is saved.

The report has only Work and File columns. Each refreshed download reference has one row: Work displays only the Work title linking to the exact Catalogue collection Work document, while File displays the matching saved filename or is blank if absent. Shared files repeat for each referencing Work. A saved file with no reference has a blank Work cell. File activation sends only `{filename}` to the local `/docs/open-work-download` action; the service confines it to that configured direct-file family and delegates reveal to the shared Finder helper. No filesystem paths enter browser payloads. `/docs/work-downloads` accepts an empty request and returns current rows without canonical/media writes, conversion, cleanup, remote checks or publication. Registry, loader and service composition remain local-only.

`work_links`, hosted by [Work Links](/docs/?doc=d-20261005-153252-541ac3), reads refreshed authored links from Catalogue `private/work-resources.json` and returns one row per authored link through an empty-object `POST /docs/work-links`. Work displays the saved title and opens its exact Catalogue document; Links displays the authored label and opens its URL in a new tab with `noopener noreferrer`. It does not contact destinations, scan media, infer missing/orphaned links or save a report snapshot. Browser navigation accepts HTTP, HTTPS, mail and telephone targets, including relative web links, and rejects script/data schemes, credentials, controls and backslashes. The report and its host remain local-only, with the host explicitly listed in ordinary `unpublishable.json`.

Both Work resource reports share [the two-column presentation](../../docs-viewer/runtime/js/reports/work-resources-report.js), while their adapters own response validation and resource actions. The Catalogue-owned saved-input reader validates only its resource schema and consumed facts once per producer call. Both reports default to Work A–Z. Clicking Work or File/Links selects ascending order; clicking the active heading toggles direction. Indicators and column-header `aria-sort` expose the current choice. Blanks in the selected column stay last in either direction; Work title, resource label or referenced filename, resource identity and Work ID provide deterministic ties. Refresh and retained Back navigation preserve the selected sort. Headers and links use normal theme text, black in light mode, with hover-only link underlining. Refresh and Finder completion disable sorting/navigation until the current operation finishes. There are no search, filters, paging or extra status columns. [Testing](Testing.md) owns separate verification approval; sorting, new-tab, Back and Finder interactions remain manual review.

`works` is the local, read-only Work Document Coverage report. It retains one row for every Series in Refresh Catalogue's private `working/generated/catalogue/reports/work-document-coverage/manifest.json`, including empty Series. The Docs cell contains distinct exact generated Context documents whose Work subjects occur in that Series' saved member Work IDs; direct Series subjects are unsupported, and Folder/None contribute no coverage. The Series column is plain text and Docs cells retain exact document links. Opening reads the saved Catalogue manifest through parameter-free `GET /docs/work-document-coverage` and the private Working Context management manifest, then composes coverage in the browser. It reads no live canonical Catalogue lookup and needs no running Studio server. There is no separate report Refresh control; reload adopts saved inputs, while existing committed Context changes retain their document-side updates. Blank rows remain visible. Final coverage is not persisted, and the report/input remain local-only. [Works Report](Works_Report_Concept_And_Architecture.md) owns the minimal manifest, Refresh selection and current evidence.

Work Document Coverage displays each Series title as plain text. Document coverage and document-link destinations retain their existing behavior.

`catalogue_works` is the local, read-only saved-Works inspection report in Working. It reads Studio-generated private report metadata, requires a non-empty Work or Series search before showing rows, preserves exact Series membership, and renders one seven-column semantic table with 20 matching rows per page. Search fields are prepared once per load, typing waits for a short pause, and a compact chevron pager appears below the table. Work, Year, Title, Series, and curator-only Storage remain visible and sortable in the embedded document; Medium type and Medium caption are expanded-only. The report is the first and only Expanded Report View adopter: its successful mount returns the exact table presentation, Manage rehosts the one live root, and temporary widths remain local presentation state. Report-owned Copy table exports every sorted match across pages, using the five embedded columns or all seven expanded columns as TSV. The report is registered and executable only in the local report graph; public report metadata, loaders, data, expansion code, and expansion CSS do not expose it. [Catalogue Works](Catalogue_Works.md) owns its durable data, link, editing, and extension contract.

`series_galleries`, hosted by [Series and Galleries](/docs/?doc=d-20261006-160017-e6589d) immediately after Catalogue Works, reads private `working/generated/catalogue/reports/series-galleries/metadata.json` through the parameter-free `GET /docs/series-galleries-report`. Refresh Catalogue generates it from the same validated loaded definitions and explicit relationship projection as `series-galleries-index.json`; runtime reads do not join canonical records or generate data. One row represents each Series–Gallery pair; every Series without Galleries and every Gallery without a Series has a row with a null opposite cell displayed as `—`. Several Series can reference the same Gallery, producing a row per association. Relationships are never inferred from Work membership.

Series and Gallery headings toggle ascending/descending order, expose indicators and `aria-sort`, and default to Series ascending. Ascending groups missing cells first; descending puts them last. Titles use numeric-aware case-insensitive sorting with opposite-column titles and exact IDs as stable ties. Gallery title controls call the existing exact Gallery Media View owner; Back retains the mounted report, sorting, scroll and invocation control. Reload saved report only rereads its JSON, preserving sorting and retaining the prior rows with a visible error if reloading fails. Controls remain busy until reads or Media View opening complete, and released mounts reject late results. Report registry, loader, endpoint and generated data remain local-only; its ordinary host is explicitly listed in `unpublishable.json`, and the report JSON is absent from the public Catalogue artifact inventory. Sorting, Gallery interaction and Back remain manual review under [Testing](Testing.md).

`uncataloged_files` lists live image files in represented Work source folders that are absent from refreshed primary-source registrations in Catalogue `private/work-sources.json`. Candidates use the same case-insensitive `IMAGE_EXTENSIONS` policy as Studio's Choose image picker; non-image attachments such as PDF and DOCX are excluded. Matching remains based on physical primary-source file identity, independently of managed download names or Work ID prefixes. Only represented directories are scanned; traversal does not expand to all source-root descendants. This is an extension filter, not image-content validation or an attachment-provenance audit. `missing_source_files` reads the same saved Work titles/declarations and lists registrations whose complete expected source path currently does not resolve to a regular file. It retains physical path equivalence and the Studio editor action. Both resolve roots through current configured media sources, retain declared registrations regardless of file existence and inspect the filesystem on each run.

The existing `docs-viewer/tests/python/test_docs_uncataloged_files.py::test_report_lists_direct_ordinary_uncataloged_files_only` still asserts the former all-file behavior, including PDF, WAV, extensionless and DOCX rows. It is unreviewed for the image-only contract. Fixtures in `test_docs_project_state.py`, `test_docs_uncataloged_files.py` and `test_docs_missing_source_files.py` also still construct the retired canonical-path input rather than a saved Catalogue input location. Updating those fixtures and assertions requires separately approved test work. The report-input migration received changed-owner Python lint/syntax/import diagnostics, production validation of its initial saved inputs and bounded source/diff review. The user accepted delivery closeout on 2026-10-10, with further testing during normal report use. No tests or live filesystem report runs were performed; Save/Refresh timing, real missing-file/image/folder cases, Downloads/Finder, report presentation and failure variants remain unverified rather than open delivery gates.

`folders_without_works`, hosted by [Folders Without Works](/docs/?doc=d-20261005-234748-d69c84), complements Uncataloged Images and immediate-only Projects with a fresh recursive scan of every configured Work media source root, currently `projects/` and `processing/`. It includes every physical descendant folder with no directly registered refreshed Work primary source, independently of folder contents or image extensions. Empty, non-image and ordinary hidden folders remain visible; symbolic links and source-root containers are omitted. Each distinct folder is scanned once. Unavailable roots or unreadable folders fail the whole run visibly rather than producing a partial inventory. No report snapshot, file-content read or filesystem mutation is involved.

Direct membership uses exact source declarations from Catalogue `private/work-sources.json` and physical folder identity, including filesystem-equivalent case/Unicode spellings. A registered primary source counts even when its filename is missing, provided its folder exists; records without a project folder or primary filename have no source-folder membership. Works below counts refreshed registered Works in scanned descendant folders, accumulated once through the directory tree. Folder and Works below are the only columns; full paths relative to the configured Projects base are sorted A–Z and folder links use the existing confined `/docs/open-local-target` Finder action. Zero identifies a branch without registered Works; a positive count identifies a container with catalogued descendants. Opening and Run/Refresh use an empty-object `POST /docs/folders-without-works`; retained Back navigation keeps its existing mounted results until refreshed. Registry, loader, service and report styles remain local-only, and the ordinary host is explicitly excluded through `unpublishable.json`. Presentation and real Finder opening are manual review; [Testing](Testing.md) owns separately approved regression work.

All six report services read [Catalogue-owned private inputs](Catalogue_Indexes_And_Payloads.md#shared-private-report-inputs) from the configured Working Catalogue root, independently of another report's output and without a running Studio server. Studio Save alone does not advance those saved facts; Catalogue Refresh does. Report runs retain live physical inspection in their existing scopes and separately generated Context metadata where applicable. Missing/invalid inputs fail visibly without canonical fallbacks or runtime generation; explicit [private report-input maintenance](Catalogue_Save_And_Refresh.md#private-report-input-maintenance) repairs unselected inputs. These contracts require no Publish operation or ordinary Docs/Search rebuild.

## Good Candidates

Good report candidates are compact, read-oriented views over generated docs data:

- docs index tables
- explicit publication ignore-list inspection
- parent, child, or orphan inspection lists
- recently updated or recently added variants
- public A-Z indexes
- generated-data summaries

Poor report candidates are workflows with writes, long-running operations, broad Studio route state, or project-specific write allowlists.

## Files

- `site/assets/data/docs/public-reports.json`
- `docs-viewer/config/reports/reports.json`
- `docs-viewer/services/docs_report_source.py`
- `docs-viewer/services/docs_source_model.py`
- `docs-viewer/build/docs_builder/source.py`
- `docs-viewer/build/docs_builder/payloads.py`
- `docs-viewer/services/docs_rendered_links.py`
- `docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-subscope-default-contribution.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-subscope-composition.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-subscope-customisation-registry.js`
- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js`
- `docs-viewer/runtime/js/reports/catalogue-works-report.js`
- `docs-viewer/runtime/js/reports/folders-without-works-report.js`
- `docs-viewer/services/docs_folders_without_works.py`
- `docs-viewer/runtime/js/management/docs-viewer-managed-table-tools.js`
- `site/docs-viewer/runtime/js/public/docs-viewer-public-document-reports.js`
- `site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js`
- `docs-viewer/runtime/js/reports/`
- `site/docs-viewer/static/css/docs-viewer-reports.css`
- `docs-viewer/static/css/docs-viewer-local-reports.css`
- `docs-viewer/static/css/docs-viewer-manage.css`

:::report
id: reports_list
:::
