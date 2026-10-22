---
draft: false
doc_id: d-20260513-105343-6de36b
title: Reports
added_date: "2026-05-13 10:53:43"
last_updated: "2026-10-22"
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
id: selected_documents
:::
```

The opener is exactly `:::report` and the closer is exactly `:::` at column one. The block is isolated from surrounding Markdown by a blank line. Interior lines use unquoted `key: value` syntax; indentation, inline attributes, blank interior lines, duplicate keys, and unknown keys or values fail source validation.

The attributes are:

- `id`: required registered report token
- `collection`: required configured collection for `docs_collection` and forbidden for other reports

`preset` is retired and fails as an unknown report attribute. There is no preset registration or selection path.

A document contains zero or one report block. Report-like examples inside fenced or indented code, inline code, HTML comments, and raw `<pre>` or `<code>` regions remain literal examples. A structural declaration outside those contexts must be complete and valid. The five retired `viewer_report*` front-matter fields are rejected; there is no compatibility or precedence path.

[Report Block Tokens](Report_Block_Tokens.md) is the concise current registry-token reference.

## Build And Payload Flow

The shared Python parser validates the complete source, resolves the registry and configured collection context, and returns one immutable descriptor plus the exact body source range. The document `doc_id` remains the report-host identity.

The builder replaces that exact source range with one inert host:

```html
<section class="docsViewerReport" data-docs-viewer-report-host aria-label="Document report"></section>
```

Only by-ID payloads receive the complete `report` descriptor. It contains required `id` and includes `collection` only when the report uses it; absent optional fields are omitted rather than written as null:

```json
{
  "id": "selected_documents"
}
```

For a collection host:

```json
{
  "id": "docs_collection",
  "collection": "works"
}
```

Manage, prepared and public by-ID payloads retain the report descriptor and generated host. Publication does not strip reports or infer eligibility from report type. The Index carries only `report_id` for report-host navigation; Recent, Search and manifests do not carry the complete descriptor.

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
- normalizes report identity and optional collection metadata
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

The source registry describes report ids, titles, descriptions and loader ids. Read the registry directly for the current report inventory.
The public projection includes only report metadata that has been explicitly promoted for public static routes.
The local manage route reads the source registry directly.
Public `/analysis/` and any other public route configs reference only the public projection.

Executable module loading remains allowlisted in:

- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js`

The JSON registry does not define arbitrary import paths.
Adding a JSON entry without a matching allowlisted loader does not make a new report executable.
This keeps the registry useful as user-facing metadata without turning it into an open-ended code-loading surface.

## Validation And Retirement

The parser validates registered report IDs against one immutable set and validates `docs_collection` against configured collection identities. Other reports reject `collection`. The former per-report preset definitions, registry arrays, payload field, browser normalization and expanded-presentation identity field are retired without aliases. The existing rejection of legacy `viewer_report*` front matter remains.

On 2026-10-11, changed-owner lint and Python syntax, the ordinary Working docs-only build, saved descriptor diagnostics, public runtime projection/check and site validation passed. The build processed 34 documents and rewrote 19 report payloads without Index, Links or Recents writes; Search and media were not rebuilt. Bounded source review covered parser validation, collection loading and report/presentation identity. Tests and fixtures remain unchanged and unexecuted, including historical preset expectations; their review requires separate test approval. Manual report mounting and presentation remain unverified. Restart Docs Viewer services and reload the browser to adopt the parser and runtime. Prepared/public document payloads acquire the sparse descriptor on the next explicitly requested Publish.

## Current Reports

`selected_documents`, hosted by dotlineform (`d-20260426-164043-e14f49`), is shared by local and public readers. Working reads the canonical `working/source/selected.json` membership list directly through `/docs/selected`; Build maintains metadata there. Preview/Public use its prepared eligible copy. Its source JSON lives at the workspace source root with the other controls, with no separate Working generated report file. The browser prepares each row's exact navigation/thumbnail choice once, indexes committed updates, reorders only changed dates and requests media policy only when an actual Work thumbnail needs it. Retained disposal owns asynchronous completion, while the document controller owns subscription release. Storage, membership, Build and Publish remain unchanged. [Source Organisation](Source_Organisation.md#selected-documents) owns the complete schema, preparation/commit behavior, retained lifetime, safeguards and cost; [Selected Documents Optimisation](deliveries/Selected_Documents_Optimisation.md) tracks delivery evidence and acceptance.

`workspace_links` is a local diagnostic report hosted by [Links](/docs/?doc=d-20260910-214604-f9e841), whose ordinary ID is in the publication ignore file. Workspace configuration's private `links_report` selects `working/generated/reports/links/report.json`. `GET /docs/workspace-links` loads one workspace configuration and reads only that confined saved JSON object. An empty-object `POST` to the same route selects Working from the same loaded workspace and calls `docs_workspace_links.write_workspace_links` with its resolved input owner and report target, then returns the completed in-memory payload without another configuration or saved-file read. **Links Refresh is the sole writer**; opening displays the last saved result. [Builder](Builder.md) maintains the underlying `working/generated/documents/links-by-id` records for document relationships and Related Links, but no Build reads, aggregates or writes the report snapshot. Refresh requires Working authoring capability and rejects dry-run requests; no document rendering, Search rebuild, source writes or freshness checks occur. Stage/scope parameters are rejected. Report paths remain server-only, and the report is absent from public metadata and executable loaders.

Links has exactly two columns, **from** and **to**, with one row per directed document pair from each record's outgoing entries. Incoming mirrors add no rows; reciprocal links produce two rows, while repeated authored links produce one pair through Build's relationship ownership. Both headers toggle ascending/descending title sorting. Initial order is from, then to; the other title and exact endpoint identities break ties. Version 4 uses flat `{collection, doc_id, title}` summaries directly in each incoming/outgoing array, with no occurrence details or stored counts. The browser trusts completed Build records without schema, identity, field or uniqueness audits. `workspace-links-data.js` shares each participating endpoint across its rows, preparing its literal title, exact identity sort key and URL once per dataset. URLs come from the mounted context's exact document/collection route owner; cells reuse them through sorting and Back. Distinct documents with identical titles remain distinct, and titles render through `textContent` without normalization.

The compact **🔄** Refresh button sits immediately left of the links count on the same row. Initial load reads the saved snapshot. Refresh awaits the aggregation POST and displays its returned data, keeping the button disabled until completion. One busy operation and the retained view's actual disposal own completion; a hidden/detached retained report can finish loading and returns with Refresh enabled. Disposal releases prepared state and ignores late success/failure/completion, without request versions or current-document/DOM freshness checks. The document controller owns subscription cleanup. Committed title changes update one shared endpoint, and deletion removes its rows and unused endpoints; only relevant effects reorder/render. Refresh acts immediately on current relationship records without a full workspace rebuild. An aggregate with no outgoing links displays an empty state; a failed load/Refresh clears the rows and displays the Refresh instruction. Catalogue pages' embedded Related links sections still update through their own document builds.

`workspace-links-report.js` owns the table, sort selection and single busy load, using the local report service and pure prepared-data owner. `docsViewerLinksDocumentSummary` is retired without an alias; the separately used shared/public `docsViewerLinksDocumentHref` retains its navigation behavior. Configuration owns report-target confinement beneath `working/generated/reports/`, requiring `report.json` and rejecting symlink traversal. GET retains JSON-object parsing; Refresh retains request/authoring authority, input directory/file symlink rejection, required directory availability, all-required-input parsing before a write and unchanged-byte write avoidance. These prevent out-of-owner filesystem access, malformed transfers and a successful partial aggregate. Build owns domain validity; saved reads, aggregation and browser preparation do not audit its completed handoffs. Refresh reads saved records in deterministic filename order, preserving included records unchanged and omitting only records with both lists empty; incoming-only records remain. An empty input directory produces a valid empty report, while unavailable/invalid inputs fail before persistence. Refresh costs one file listing, required saved-record reads, one serialization/comparison and at most one atomic replacement. GET costs one saved object read; browser preparation is linear in outgoing pairs with one URL/key per distinct participating endpoint, followed by title sorting. Committed titles use an indexed endpoint lookup; deletion filters rows once and prunes endpoint reference counts. Browser caches live only for the retained dataset. There is no old-location fallback, Build handoff, compatibility layer, automatic migration or repair.

On 2026-10-14, focused JavaScript lint passed for the report, prepared-data owner and shared presentation. A read-only invocation of `read_generated_workspace_links` piped the then-saved object into `prepareWorkspaceLinks`, the production `buildViewerUrl` route owner and all four `sortWorkspaceLinksRows` selections: 27 directed rows, 44 participating endpoints and 26 incoming-only records; each sort completed with 27 rows. The user's subsequent Refresh displayed 26 links, and direct inspection confirmed that the aggregate and current per-document records agreed. After the approved ownership change, the existing snapshot was moved once from `working/generated/documents/links.json` to the configured report path; the production getter read 43 saved records and 26 directed pairs there. This migration used a filesystem rename and did not regenerate the report or alter per-document records. Python lint and compilation passed for the six changed owners: workspace configuration, aggregate writer, generated reader, management route, complete Working owner and relationship builder docstring. Review traced configuration/privacy, the sole writer, complete/empty/unchanged/read-failure paths, required relationship diagnostics and rendering handoffs, and the prior browser lifetime/sort behavior. Required relationship work remains in Build; its diagnostics now live in `diagnostics.relationships`, with no report counts/changed flag or aggregation step. Public projection/check/site validation evidence from the earlier shared-helper removal remains applicable; the ownership follow-up changes no shared/public runtime. These are bounded implementation diagnostics, not an end-to-end or measured performance claim.

The historical scope-bearing test files have not been accepted as evidence for this contract; changes require their own test specification. Tests, fixtures, harnesses and profiles remain unchanged and unrun. Live HTTP/Refresh, full Build, committed title/deletion interaction, delayed load/Refresh and Back/disposal, error/empty states and public navigation remain manual acceptance boundaries. Restart Docs Viewer services and force-reload for those checks. [Links Optimisation](deliveries/Links_Optimisation.md) tracks delivery state.

`unpublishable` is a local, read-only report hosted by [Unpublishable](/docs/?doc=d-20260909-160530-224efe). `GET /docs/unpublishable-report` rereads configured ordinary Working `source/unpublishable.json` on each load or Refresh through `docs_publication_ignore.py`, using one loaded Working configuration. The `docs_unpublishable_report_v4` response contains exact document IDs and current source titles without stage. Each title comes from only the listed ID's confined source header after identity validation; no complete body read or unrelated Subject/readiness/report audit is needed, and missing sources retain a null title. The browser trusts those completed rows and owns one title/ID display sort; retained-view disposal bounds asynchronous reads and editor actions without request versions or DOM/current-document gates. There is no persisted report snapshot, collection-wide Markdown scan or draft expansion. Open in VS Code posts an empty object to `/docs/open-publication-ignore`, which opens that configured file without preferred-Markdown-editor discovery. Invalid JSON can still be opened for correction; missing, unreadable and invalid list reads fail visibly, while `[]` is empty. Named-collection documents are outside this policy. Stage/scope parameters are rejected; the report remains absent from public metadata and executable loaders. [Publication Ignore List](Publication_Ignore_List.md#unpublishable-report) owns preparation, safeguards, cost and evidence limits; [Unpublishable Optimisation](deliveries/Unpublishable_Optimisation.md) tracks review and manual acceptance.

The Analysis Documents report (`docs_index_table`) was retired on 2026-09-26. Its implementation, local registry entry, loader, presets, dedicated index-reader adapter and tree-indent style were removed, along with its Working host document.

The Reports List (`reports_list`) and its Working host document (`d-20260915-181648-d1e356`) were retired on 2026-10-15. This repository document remains the maintained Reports documentation; the report registry remains the authority for registered IDs.

Retirement review removed the dedicated module, loader, metadata, local registry handoff, CSS and obsolete protected-document/publication-exclusion entries. The existing Delete service completed source, Index, Selected and targeted generated/relationship removal with no warnings; it scanned no source files and rebuilt no other document payloads. Source-owned report-ID validation, executable-loader allowlisting and confined deletion retain their existing boundaries. Focused JavaScript lint and registry JSON parsing passed. Tests and fixtures retain historical `reports_list` examples and remain unchanged and unrun; Search, Publish and browser verification were outside this change.

`docs_collection` renders a browser-ordered list for a configured Docs Viewer collection. Its composition resolves `report.collection` once from the active workspace's collection map and carries that exact owner into the report and Manage contribution. Manage reads `manage-manifest.json`; the public reader uses `manifest.json`. Completed rows supply literal labels and metadata without another domain audit. The existing browsing data owner prepares exact URLs, thumbnail choices, search/sort keys and an identity lookup, caches title/recent ordering, filters without resorting and updates only the known committed row. Page and selection operations reuse complete filtered IDs. Work-thumbnail policy loads only for an actual choice, once per retained view. Controller-owned lifetime/subscription cleanup replaces DOM-removal/current-connection gates; tab controls and reading-position snapshots remain. [Collection List Preparation](Sub_Scope_Index_Architecture.md#collection-list-preparation) owns sorting, thumbnail, selection, safeguards and evidence limits; [Collection Report Optimisation](deliveries/Collection_Report_Optimisation.md) tracks public projection and manual acceptance.
Selecting a row opens the selected collection document through its exact by-ID reader. Collection documents carry no `publishable` field. Working inventories retain boolean `draft`, and drafts remain visible and loadable. The shared reader exposes a validated `{collection, doc_id}` action target after payload identity checks succeed. Collection manifests contain exactly one root `docs` array. Their former customisation envelope and Subject generation hash are retired; report identity comes from the configured collection.

The shared report accepts an optional caller-owned contribution with detached leading-cell/title-prefix row hosts, list/detail toolbar hosts and collection-owned mount, state, refresh and unmount events. It inserts only populated hosts and offers the detail toolbar only after by-ID identity is valid. The Manage contribution renders shared visual status and an additional 📝 indicator only for `draft: true`. It owns collection-keyed checkbox selection, the compact 🔧 Actions and Select all/Clear/Done controls and the lazy Prepare Package bridge. That bridge supplies exact checked IDs plus `{collection}`, never a selected parent or displayed child fallback. Public callers import no management module.

The local Collection Actions menu remains available in every configured collection, including empty lists. Export and Prepare package require checked IDs; Import doc and Import docs receive the exact collection and require no selection. Missing workflow support takes precedence over selection prompts. Existing action policy hides unsupported Catalogue package/import actions; Catalogue retains Export. Set Publishable and its callbacks, request handling and service support are removed. [Docs Import](Docs_Import.md) owns both intake workflows and package destination matching.

Manage supplies standard collection controls without Subject authoring or collection-specific Subject loaders. The shared document-level Thumb action applies to Library, Context, Concepts and Moments; [Media And Asset Handling](Media_And_Asset_Handling.md#assigned-document-thumbnails) owns its independent copy/delete lifecycle. Projects uses its own explicitly refreshed snapshot. The retired Processing Docs collection remains separate from the repository Processing project and Projects-owned Processing media.

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

The Source Config Report (`source_config`) was retired on 2026-09-26. Its JavaScript renderer, Python report builder, `GET /docs/source-config` endpoint, capability flag, registry entry, loader, client method, dedicated styles and Working host document were removed. Settings and its dedicated API were subsequently retired; configuration editing is a design-time action described by [Configuration And Extension Points](Configuration_And_Extension_Points.md#workspace-and-target-contracts).

`docs_broken_links` opens the saved Working audit through `GET /docs/broken-links`. Refresh explicitly scans ordinary and configured collection sources and saves a new private JSON snapshot through an empty-object `POST` to the same route. Last scanned time sits beside Refresh, vertically centred, without a broken-link count; unscanned sources remain explanatory rows. Missing data gives an empty report without a first-refresh prompt. Refresh retains loaded results and uses a progress cursor without running messages. [Broken Links Script](Broken_Links_Script.md) owns audit coverage, persistence, failure behavior and the local-only boundary.

`docs_backlinks` (Documents Linking Here), its executable loader, generated `backlinks.json`, browser setting and `/docs/backlinks` endpoint are retired. [Related Links](Related_Links.md) presents persisted incoming and outgoing document relationships through the author-inserted directive. The retired report ID has no registry entry or compatibility alias; old authored report blocks require conversion to the directive and otherwise fail normal unknown-report validation.

The dedicated `docs-viewer/tests/python/test_docs_backlinks_report_contract.py`, backlinks cases in `test_build_docs_payloads.py` and the route list in `docs-viewer/tests/js/docs_viewer_stage_target_contract.mjs` still target retired report/output or scope contracts. They remain unchanged and were not run during retirement. Separately approved cleanup should remove obsolete backlinks coverage while preserving unrelated current coverage; these test consumers do not require a production alias.

`semantic_tokens` and its generated usage index are retired. Work image and Work Media View text tokens now contribute ordinary document relationships to Catalogue subdocuments, presented by [Related Links](Related_Links.md). Gallery Media View tokens create no document relationship. `docs_broken_links` remains the independent authoring audit.

`project_state`, displayed as Projects, is the local project-folder reconciliation report. Its private snapshot is `working/generated/reports/projects/metadata.json`, relative to the configured Docs workspace and owned by `projects_report_metadata` in workspace configuration. Opening calls parameter-free `GET /docs/project-state`, which reads only that saved JSON object and returns `{ok: true, metadata: ...}`. An absent file returns `metadata: null` and asks the user to use Run/Refresh; it never triggers an automatic scan or write. Unreadable or invalid JSON fails with explicit Refresh guidance.

Run/Refresh calls `POST /docs/project-state` with `{}`; parameters and dry-run requests are unsupported. Python resolves one workspace, scans immediate physical `projects/` children and reads refreshed `private/work-sources.json`, `private/series.json`, `series-galleries-index.json` and the Context management manifest once each. It discovers Context identities/titles from that manifest, reads each by-ID JSON once and deduplicates its `catalogue.references[].target` Work/Gallery identities. The saved snapshot contains `generated_at`, folder keys/encoded local targets, document IDs/titles/typed `targets`, Work IDs/first-level folders/Series membership, Series IDs/titles and explicit `series_galleries` pairs. It writes only Projects metadata and returns the same in-memory object. Refresh does not read Links JSON or source tokens, refresh Catalogue, render documents, extend shared manifests/indexes or repair inputs.

The browser's `project-state-data.js` joins Work targets to their Series and Gallery targets to explicitly related Series, then places each document in every physical folder represented by those Series' member Works. Gallery membership does not infer Series relevance. Documents are unique within each folder/Series row and status counts each associated document once across placements. Plain Markdown Catalogue links, incoming links and generated Related Links do not contribute. Every scanned folder remains visible, including unmatched folders and empty document cells. Hidden-folder/symlink exclusions and first-level `projects/<project_folder>` interpretation across media sources remain unchanged. Projects covers Context documents only; it adds no all-Series audit.

Document stacks use case-insensitive title ordering with exact-title and document-ID ties. Prepared Folder/Series groups carry search, comparison and TSV text; the mounted report reuses one collator, sorts on dataset/group/sort changes and filters/copies the displayed projection. Status shows saved Refresh time in UTC and complete-dataset counts independently of search. Document Save/Delete, Catalogue Refresh and filesystem changes appear only after explicit Projects Refresh. Failed loads/refreshes retain an already displayed snapshot; disposal releases prepared state and ignores late responses. There is no committed-document subscription or Subject cue.

Report construction and browser consumption trust completed upstream data. An omitted document Catalogue envelope supplies no associations. Saved reads require only readable JSON-object representation; Refresh retains the existing Catalogue input representation checks, required document/manifest parsing and complete input assembly before persistence. Configured-root availability, confined input/output paths without symlinks, local-target encoding and Finder authority remain at their owning boundaries. Rendering uses text nodes and exact Context viewer URLs. No schema/membership audit, source fallback, output read-back, hash, freshness check, backup, repair or compatibility alias is added. Snapshot, service and report modules remain local-only and outside Publish.

The 2026-10-20 cutover replaced Subject placement and refreshed 208 folders, 159 Context documents, 4,618 Works and 139 Series; eight documents had Work/Gallery targets. Changed-owner lint/compilation, management imports, public projection/check and site validation passed. Legacy Subject/scope/report tests remain unchanged and unrun; their migration needs separate approval. Browser association/grouping/navigation and Thumb interactions remain unverified in the recorded manual evidence; further confirmation continues through normal use after restarting local services and force-reloading Manage.

The Projects report's Series column links each exact response-owned Series title to that Series in local Studio in both Folder and Series grouping modes. It uses the same `studio-work-editor-links.js` owner as Series and Galleries, resolving the configured loopback Studio base once per mount and encoding the supplied Series ID into `/studio/catalogue-work/?series=<series_id>`. Native links open in a new tab with `noopener noreferrer`. Link construction requires no extra request or report refresh; text-node labels and the shared Studio-base safety check retain their existing owners. Folder links, document links, search, sorting and copied TSV retain their existing behavior.

The 2026-10-22 link change passed focused JavaScript lint and whitespace checks. Source/redundancy review confirmed both grouping projections reuse the same cells and shared URL safety owner, with no new reads, duplicate validation or route handler. Browser/new-tab confirmation remains manual; no tests were changed or run.

`docs_media` is the local media-to-document inspection report hosted by [Docs Media](/docs/?doc=d-20260812-212735-6d9cf3). Opening reads saved metadata; Run/Refresh explicitly regenerates it across ordinary and configured collection owners, excluding derived thumbnails. The browser owns joins, exact document links and sortable Collection, Type, File name and Documents columns, with a collection filter and immediate search. File names retain the confined Finder action. The report remains absent from public metadata and executable loaders. [Media And Asset Handling](Media_And_Asset_Handling.md#docs-media-inventory-report) owns the saved-data, freshness and storage boundary.

`work_downloads`, hosted by [Work Downloads](/docs/?doc=d-20261004-202223-1e2205), complements Docs Media with Catalogue attachment coverage. Opening and Run/Refresh resolve workspace configuration once, read the saved Catalogue `private/work-resources.json` and scan direct regular files in the configured Docs workspace `assets.work_files` family live. The service supplies only Works with download references and a filename inventory; the browser matches exact stored filenames, including legacy names, without inferring ownership from Work ID prefixes. Save stages new attachments; Catalogue Refresh advances both their references and Working files before the report adopts them. `.DS_Store` and `.gitkeep` placeholders are ignored, directories are not traversed, and unavailable storage, unreadable JSON, unsafe file identities or symlinks fail visibly. No report snapshot is saved.

The report has only Work and File columns. Each refreshed download reference has one row: Work displays only the Work title linking to the exact Catalogue collection Work document, while File displays the matching saved filename or is blank if absent. Shared files repeat for each referencing Work. A saved file with no reference has a blank Work cell. Browser composition prepares these rows once per load using a filename set; the service does not join or presort them. `/docs/work-downloads` accepts an empty request and returns `report.works` with Work IDs, titles and download filenames, plus `report.files` with current direct filenames. File activation sends only `{filename}` to the local `/docs/open-work-download` action; the service checks that action's exact basename, confined path and current regular-file existence before delegating reveal to the shared Finder helper. No filesystem paths enter browser payloads. Registry, loader and service composition remain local-only, without canonical/media writes, conversion, cleanup, remote checks or publication.

`work_links`, hosted by [Work Links](/docs/?doc=d-20261005-153252-541ac3), reads refreshed authored links from Catalogue `private/work-resources.json` and returns one row per authored link through an empty-object `POST /docs/work-links`. Work displays the saved title and opens its exact Catalogue document; Links displays the authored label and opens its URL in a new tab with `noopener noreferrer`. It does not contact destinations, scan media, infer missing/orphaned links or save a report snapshot. Browser navigation accepts HTTP, HTTPS, mail and telephone targets, including relative web links, and rejects script/data schemes, credentials, controls and backslashes. The report and its host remain local-only, with the host explicitly listed in ordinary `unpublishable.json`.

Both Work resource reports share [the two-column presentation](../../docs-viewer/runtime/js/reports/work-resources-report.js), while their adapters own Downloads matching, Links URL safety and resource actions. Their saved resource reader accepts an explicitly resolved Working Catalogue location, performs one confined read and JSON-object parse, and trusts Refresh-owned schemas, identities, titles and resource arrays without repeating row audits or checking the other report's resource facts. The browser consumes those completed handoffs directly. Missing or unreadable saved input requires explicit maintenance; neither reader repairs data or falls back to canonical records. Each load prepares one exact Catalogue document URL per distinct Work through `viewerUrlForDocument`; sorting and retained Back reuse those URLs without configuration scans or URL reconstruction. Disposal releases prepared rows and ignores late Refresh/Finder completion through the existing view lifetime.

Both reports default to Work A–Z. Clicking Work or File/Links selects ascending order; clicking the active heading toggles direction. Indicators and column-header `aria-sort` expose the current choice. Blanks in the selected column stay last in either direction; Work title, resource label or referenced filename, resource identity and Work ID provide deterministic ties. Sorting already runs only on load or a changed sort selection; no additional ordering cache is needed. Refresh and retained Back navigation preserve the selected sort. Headers and links use normal theme text, black in light mode, with hover-only link underlining. Refresh and Finder completion disable sorting/navigation until the current operation finishes. There are no search, filters, paging or extra status columns.

Workspace configuration owns root and ancestor-symlink confinement once per run. The direct Downloads scan uses `scandir` entry types, rejecting symlinks and checking exact basenames without following directories, resolving each file again or reading contents/sizes. Finder retains an independent confinement/existence check because it is a later action accepting a browser-supplied filename. Links checks each URL's navigation policy once during row preparation, retains `noopener noreferrer` and renders labels as text; it does not audit authoring completeness or contact destinations. These are boundary safeguards, separate from completed Refresh data validity.

The 2026-10-14 optimisation passed focused Python/JavaScript lint, Python compilation and a read-only invocation of the production saved readers, browser composition and default sorting with current inputs: five Works with downloads, six saved files and six download rows, with no missing or unassigned files, plus three link rows. This exercised real saved parsing, direct inventory and current URL acceptance; it did not exercise synthetic missing/shared/unassigned/unsafe inputs, HTTP/browser transport, DOM rendering, sort interactions, disposal, new-tab, Back or Finder actions. Those interactions remain user manual review after restarting Docs Viewer services and force-reloading. Tests remain unchanged and unrun under [Testing](Testing.md).

Work Document Coverage (`works`) was retired on 2026-10-20, including its registry/loader, endpoint, private manifest/producer/maintenance selection and host `d-20260810-150346-bc7cdc`. The `works` Context collection remains active. Projects replaces the useful folder-based association view; the former all-Series coverage audit is not recreated. [Historical Works Report](Works_Report_Concept_And_Architecture.md) records the retired design.


`catalogue_works` is the local, read-only saved-Works inspection report in Working. It reads Refresh-generated private report metadata through Docs Viewer's parameter-free `GET /docs/catalogue-works-report`, independently of the running Studio server, requires a non-empty Work or Series search before showing rows, preserves exact Series membership, and renders one six-column semantic table with 20 matching rows per page. Its browser data owner trusts completed Refresh fields and prepares search/sort values once per load. Typing waits for a short pause; query changes filter, sorting reuses matches, and paging/Copy reuse the ordered result. Headers stay mounted and exact Work URLs are prepared only for displayed Works. Work, Year, Title, Series and curator-only Storage remain visible and sortable in the embedded document; Medium is expanded-only. The report is the first and only Expanded Report View adopter: its successful mount returns the exact table presentation, Manage rehosts the one live root, and temporary widths remain local presentation state. Report-owned Copy table exports every sorted match across pages, using five embedded or six expanded columns as TSV, with cell values prepared once per exported row. The retained view preserves pending searches and releases timers, prepared data, URL mappings and listeners on disposal. The local service reads only the configured saved file, retaining management/origin/path authority without canonical reads or generation. The report remains local-only; public report metadata, loaders, data, expansion code and CSS do not expose it. [Catalogue Works](Catalogue_Works.md) owns its durable data, link, editing, safeguard and evidence contract.

`catalogue_medium`, hosted by [Catalogue Medium](/docs/?doc=d-20261020-200307-25af4e) immediately after Catalogue Works, counts saved Medium usage in two columns: Medium and Works. [The browser module](../../docs-viewer/runtime/js/reports/catalogue-medium-report.js) groups the exact `medium` values in the existing Catalogue Works metadata from `readCatalogueWorks()` / `GET /docs/catalogue-works-report`. Each Work contributes one count. Case, punctuation and whitespace differences remain separate; explicit null has its own No medium row, sorted by that displayed label. An authored literal No medium remains a separate group from null. No new generated file, endpoint or server calculation is involved, and a running Studio server is not required.

Catalogue Medium initially sorts by Medium ascending, using the English numeric case-insensitive collator with exact text and null identity as deterministic ties. Both headings toggle ascending/descending; numeric Works sorting uses Medium ascending for equal counts. Grouping happens once per loaded dataset; sorting only reorders those prepared groups. Reload saved metadata rereads the same input, preserves the selected order and retains previous rows with a visible error on failure. A read completing while the view is retained can finish; actual disposal releases prepared groups and ignores late completion. Restoring during a read records the order for its eventual render. The local registry/loader/styles and host action identity remain private; the host is explicitly excluded through `unpublishable.json`, and public code/registry inventories are unchanged. No schema/field audit, normalization, canonical read, preflight, cache, generation, repair or fallback is added. Existing Docs Viewer endpoint authority, configured path confinement, JSON/HTTP parsing, text rendering and busy/disposal checks keep their boundary owners. [Catalogue Medium delivery](deliveries/Catalogue_Medium.md) records implementation evidence and manual acceptance limits.

`series_galleries`, hosted by [Series and Galleries](/docs/?doc=d-20261006-160017-e6589d) after Catalogue Medium, reads private `working/generated/catalogue/reports/series-galleries/metadata.json` through the parameter-free `GET /docs/series-galleries-report`. Refresh Catalogue generates it from the same validated loaded definitions and explicit relationship projection as `series-galleries-index.json`; runtime reads do not join canonical records or generate data. One row represents each Series–Gallery pair; every Series without Galleries and every Gallery without a Series has a row with a null opposite cell displayed as `—`. Several Series can reference the same Gallery, producing a row per association. Relationships are never inferred from Work membership.

Series and Gallery headings toggle ascending/descending order, expose indicators and `aria-sort`, and default to Series ascending. Ascending groups explicit null cells first; descending puts them last. Supplied titles pass unchanged through numeric-aware case-insensitive sorting with opposite-column titles and exact IDs as stable ties. Only an explicit null association displays `—`; present labels have no fallback. The shared Search control filters loaded rows immediately using a trimmed, case-insensitive substring match in either the Series title or Gallery title; clearing restores all rows, and an empty match has distinct feedback. Filtering reuses the current row order, with sorting only on load/order changes. Series titles open the configured local Studio Work editor at `?series=<series_id>` in a new tab with `noopener noreferrer`; Studio selects that Series and its member list with no Work selected, including empty Series. The shared report link builder resolves the local Studio address once per dataset, retaining loopback HTTP/root-only authority and encoded exact identities. Missing Work Images uses the same builder for its existing same-tab Work ID links. Gallery title controls call the existing exact Gallery Media View owner; Back retains the mounted report, query, sorting, scroll and invocation control. Reload saved report only rereads its JSON, preserving query/sorting and retaining the prior rows with a visible error if reloading fails. Controls, including Search and Series links, remain busy until reads or Media View opening complete, and released mounts reject late results. Report registry, loader, endpoint and generated data remain local-only; its ordinary host is explicitly listed in `unpublishable.json`, and the report JSON is absent from the public Catalogue artifact inventory. Search, sorting, Studio navigation, Gallery interaction and Back remain manual review under [Testing](Testing.md).

Both private saved readers perform one confined file read and JSON-object parse without existence preflights or saved schema/identity/label/membership/uniqueness/ordering audits. Browser response audits and unused validator helpers are retired. Authoring/Refresh own domain validity and serialization order; ordinary consumption trusts the completed handoff. Retained safeguards are configured Working artifact authority, path/symlink confinement, parsing/read errors with explicit maintenance guidance, HTTP/JSON failure handling, shared Subject interpretation, text-node rendering, exact document/Gallery navigation and mounted-view busy/disposal boundaries. These are bounded storage, representation and action checks; no canonical read, generation, repair, freshness pass, persistent cache or fallback is added. Public relationship-index and other Catalogue reader validators retain their separate owners. Headers, payload fields and source generation remain unchanged, so no data conversion, document/Search rebuild or Publish is required.

The 2026-10-21 Series/Galleries Search and Studio entry changes passed focused JavaScript lint and whitespace checks. The distinct code and redundancy review traced filtering/clearing, null cells, order changes, saved reload, retained query restoration, native new-tab handling and Studio startup through the existing search-field, routing and Series-browser owners. It removed repeated Studio-address parsing from Work rows and a duplicate Series existence check from the browser's known-Series selection. Incoming URL identity checks remain at initial route selection; local-address authority, encoded links, text rendering, new-tab isolation, exact Gallery targeting and busy/disposal safeguards retain their owners. No additional server work, handoff audit, compatibility layer or recovery behavior was added. Tests and browser interaction were not run; force-reload Docs Viewer and Studio for manual acceptance of populated/empty Series, invalid IDs, existing Work/new-Work entry, filtering and Gallery/Back. Changed report modules are outside the public projection inventory.

The 2026-10-14 [Works And Series Galleries Optimisation](deliveries/Works_And_Series_Galleries_Optimisation.md) records focused lint/compilation, distinct code review and read-only current-data evidence: 140 Series, 4,620 memberships and 235 Context records produced 20 covered Series and 23 documents; Series and Galleries supplied 301 rows. This does not prove HTTP/browser interaction, committed-change/disposal execution, Gallery Media View/Back or failure variants. Tests remain unchanged and unrun under their separate approval boundary. Restart Docs Viewer services and force-reload the viewer for manual acceptance; neither changed report module is in the public code projection inventory.

`uncataloged_files` lists live image files in represented Work source folders that are absent from refreshed primary-source registrations in Catalogue `private/work-sources.json`. Candidates use the same case-insensitive `IMAGE_EXTENSIONS` policy as Studio's Choose image picker; non-image attachments such as PDF and DOCX are excluded. Matching remains based on physical primary-source file identity, independently of managed download names or Work ID prefixes. Only represented directories are scanned; traversal does not expand to all source-root descendants. This is an extension filter, not image-content validation or an attachment-provenance audit. `missing_source_files` reads the same saved Work titles/declarations and lists registrations whose complete expected source path currently does not resolve to a regular file. It retains physical path equivalence and the Studio editor action. Both resolve roots through current configured media sources, retain declared registrations regardless of file existence and inspect the filesystem on each run.

Both filesystem report workflows now read the saved Catalogue input and pipeline configuration explicitly during the operation, prepare one checked media-source map/default and resolve only required source roots. Empty complete-registration selections return empty rows without Projects storage setup. `docs_work_source_inspection.py` owns a run-local reader anchored to the resolved Projects base. It carries confined directory prefixes, missing ancestors and terminal `lstat()` results forward; it performs no filesystem work in its constructor and adds no process/persistent cache. The reports no longer repeat declaration validation, source-map parsing for each Work, source-root walks, final `resolve()` walks or follow-up `stat()`/`is_dir()` checks. The general Work-media resolver and its media-processing, source-opening and other report callers retain their existing behavior.

Missing Source Files inspects each distinct declared leaf directly, reusing its regular-file result across Works but returning a separate row per missing Work. It never lists a directory. Uncataloged Files inspects registered leaves once, collects physical `(st_dev, st_ino)` identities separately for each source, and uses `os.scandir()` once per represented source/directory selection. It filters hidden names and unsupported extensions before inspecting candidates, reuses already-read registered metadata, and obtains remaining candidate metadata from the directory entry without another parent walk. Filesystem case/Unicode equivalence and hard links retain physical matching rather than filename equality. Final rows retain one existing ordering pass: Folder/File for Uncataloged Files and Work ID for Missing Source Files. No source contents or unused media totals are read.

Retained safeguards have distinct owners and costs. The Catalogue reader checks saved representation once; the prepared source map resolves exact configured identities without a default for unknown explicit IDs. The Projects owner resolves the existing base once; the report reader confines relative components, checks each required directory prefix and selected root for symlinks/type once, and checks root readability once. Missing roots, non-directory parents, declared symlinks and inspection/listing errors fail visibly; missing declared leaves or ancestors and non-regular leaves retain their report meanings. Uncataloged Files preserves its existing candidate-symlink outcomes: links to regular files fail, while dangling links and links to non-files contribute no candidate. Only this exceptional classification follows a link for one metadata read; no linked file becomes a row. Encoded local targets and later Finder/source-opening actions retain their existing exact-target/confinement checks, independently of completed report facts. No freshness rechecks, repairs, canonical fallback, alias or recovery mechanism is added.

Both browsers consume the service's completed row fields directly, retaining HTTP/JSON/error handling in the shared report service, text-node rendering and safe destination owners. Repeated response schema/key/identity/path audits and presentation coercion are removed. Missing Source Files displays configured source prefixes as supplied, including valid `projects/…` expected paths. Uncatalogued Images omits only a leading `projects/` from its displayed Folder cell; `processing/` and the remaining path are retained. This browser-owned presentation uses the existing row without changing its full folder path, ordering or encoded Finder target. The service response versions and row fields, report columns, Finder and Studio actions remain unchanged. Both report modules are local-only and outside the public code projection inventory.

The existing `docs-viewer/tests/python/test_docs_uncataloged_files.py::test_report_lists_direct_ordinary_uncataloged_files_only` still asserts the former all-file behavior, including PDF, WAV, extensionless and DOCX rows. It is unreviewed for the image-only contract. Fixtures in `test_docs_project_state.py`, `test_docs_uncataloged_files.py` and `test_docs_missing_source_files.py` also still construct the retired canonical-path input rather than a saved Catalogue input location; the two source-file report suites and their Python/JavaScript contract checks additionally retain retired producer/path objects or browser normalizers. These tests remain unchanged and unrun; migration needs separate approval. The user accepted the original report-input migration on 2026-10-10, with further testing during normal report use; that migration performed no live filesystem report runs. The 2026-10-14 [Source File Report Optimisation](deliveries/Source_File_Report_Optimisation.md) records focused lint/compilation, distinct code review and one read-only production run of each report, returning 0 missing-source rows and 223 uncataloged-image rows. These positive current-data results do not establish missing/non-file/symlink/error variants, physical alias cases, HTTP/browser transport, Finder/Studio interaction or Save/Refresh adoption timing. Restart Docs Viewer services and force-reload the viewer for manual acceptance; no Docs/Search rebuild or Publish is required.

Uncatalogued Folders (`folders_without_works`, formerly Folders Without Works) was retired on 2026-10-22 at the user's request. Its local registry/loader, browser service method, scan endpoint/producer, report styles and host `d-20261005-234748-d69c84` are removed. The ordinary document-deletion workflow removed its Working source, Index entry and generated payload; its publication exclusion and private-action identity are also removed. There is no replacement report or compatibility route. Shared `private/work-sources.json` remains required by Projects, Uncataloged Images and Missing Source Files, with its Refresh producer, saved reader and shared physical-source inspector retained. [The delivery](deliveries/Folders_Without_Works_Report_Delivery.md#retirement) records retirement evidence and adoption steps.

The five remaining report services read [Catalogue-owned private inputs](Catalogue_Indexes_And_Payloads.md#shared-private-report-inputs) from the configured Working Catalogue root, independently of another report's output and without a running Studio server. Studio Save alone does not advance those saved facts; Catalogue Refresh does. Report runs retain live physical inspection in their existing scopes and separately generated Context metadata where applicable. Missing/invalid inputs fail visibly without canonical fallbacks or runtime generation; explicit [private report-input maintenance](Catalogue_Save_And_Refresh.md#private-report-input-maintenance) repairs unselected inputs. These contracts require no Publish operation or ordinary Docs/Search rebuild.

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
- `docs-viewer/runtime/js/management/docs-viewer-management-collection-default-contribution.js`
- `docs-viewer/runtime/js/management/docs-viewer-management-collection-composition.js`
- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js`
- `docs-viewer/runtime/js/reports/catalogue-works-report.js`
- `docs-viewer/runtime/js/management/docs-viewer-managed-table-tools.js`
- `site/docs-viewer/runtime/js/public/docs-viewer-public-document-reports.js`
- `site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js`
- `docs-viewer/runtime/js/reports/`
- `site/docs-viewer/static/css/docs-viewer-reports.css`
- `docs-viewer/static/css/docs-viewer-local-reports.css`
- `docs-viewer/static/css/docs-viewer-manage.css`
