---
draft: false
doc_id: d-20260605-125108-c68916
title: Generated Data Contracts
added_date: "2026-06-05 12:51:08"
last_updated: "2026-10-19"
summary: Public and manage Docs Viewer payload schemas, registered publication roots, read authority, publishing, and builder ownership contracts.
parent_id: d-20260331-000000-c313fd
---
# Docs Viewer Generated Data Contracts

This document records generated-data ownership for [Docs Viewer Runtime Boundary](Docs_Viewer_Runtime.md).
It separates public read-only route data from local/manage route data so payload-size and management-safety decisions have a durable home.

## Ownership Rules

- Public routes load only public-reader data needed for navigation, selected-document rendering, search, Recent, and reader-facing metadata.
- Manage routes may load manage generated data and local-service data, but manage needs should not force public payloads to carry management/tooling metadata.
- Public and manage payload names and shapes should be explicit route contracts, not incidental current renderer requirements.
- The workspace provider is the feature-facing collection-read owner. The generated-data runtime remains the read transport/retry owner; backend writes and management capability truth remain in management services.
- There should be no compatibility fallback to retired public payloads once a route contract has moved.
- Data Sharing document source-context reads are not generated-data runtime reads; they use Docs Viewer-owned helpers over the configured Working owner and source Markdown.
- `docs-viewer-workspace-provider.js` resolves current workspace URLs and delegates `readIndex`, `readDocument`, `readSearch`, `readRecent` and `readLinks` to the generated-data runtime.
- `readSource` and `writeSource` are absent from a provider unless a source adapter explicitly supplies them. Method or provider presence does not grant backend or write authority; the source endpoint remains capability-gated.

## Workspace Provider Contract

Public and Manage routes use one workspace-provider implementation. Each composition supplies one workspace from `docs_viewer_config_v4`, without a stages array. It adapts configured URLs to collection-facing methods so route, document, Search/Recents, report and Source Editor consumers do not reconstruct generated-data paths or choose a publishing stage. Local services resolve Working; public readers use repository/public data.

`readLinks` opens the exact document's separate relationship record through its configured URL base. `docs-viewer-generated-data-runtime.js` owns static-versus-local reads, generated-read capability checks, retry delays, reload paths and payload normalization.

Docs Review retains its separate package owner. No Preview browser provider or fallback to another workspace is available.

### Catalogue Reference And Presentation

Working by-ID payloads optionally carry `catalogue: {schema: "docs_catalogue_presentation_v1", references: [...]}`. Each ordered occurrence has `reference_id` (`c1`, `c2`, ...), exact `target: {kind, id}`, `presentation` (`entry`, `image` or `media`) and applicable authored `options`. Image options are `use_work_title_caption`, restricted `summary_html`, `placement` and `fill_width`; Media View links carry `label`; Entry has no authored options. Each occurrence binds to `data-docs-catalogue-ref` in `content_html`. Build emits no Work-derived title, alt text, dimensions, URLs, resources or Gallery relationships. Documents without Catalogue references omit the envelope.

Manage creates an operation-local live presentation provider on document or Media View activation. Public reads `catalogue.presentations`, keyed by `<kind>:<id>`, from prepared by-ID payloads. Each distinct Work has `schema_version: "docs_media_view_v2"`, exact `target`, `label`, `image` with intrinsic pixels and candidates, `new_tab_target` and ordered `galleries`. Entry occurrences add `entry: {metadata_lines, resources}`; resource rows carry `kind` (`download` or `link`), `label` and `url`. There is no unused top-level Work `metadata` array or v1 reader branch. Prepared Catalogue documents always include their own Work presentation. Gallery references retain authored labels without embedding all member Works.

The shared browser renderer fills live slots and binds complete public markup without replacing it. Public initial document and own Work Media View need no Work-record, media-policy or Series–Gallery lookup. Gallery browsing retains its exact membership/policy inputs; selecting a Work navigates through the prepared `collection: catalogue, doc_id: <work_id>` payload. Physical Work/relationship JSON distribution remains independently maintained.

`docs_catalogue_static.py` owns selected static preparation for Publish, collection Export and content-bearing Prepare package. It consumes supplied payload/reference values and operation-local Working Catalogue inputs, returns a prepared payload plus exact Work-media descriptors, and writes no files or queues. Publish callers serialize once and carry those bytes through Preview/distribution. Export carries the payload and maps only emitted/linked media into its existing snapshot planner. Prepare package supplies its selected renderer output/reference envelope before existing content transformations and adds no media packaging. Tree-only packages need no presentation preparation. Work media retains its configured Work owner and does not become document media or a by-ID media list.

## Current Payload Roots

| Owner | Docs root | Search root |
| --- | --- | --- |
| Manage/local | `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/documents/` | `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/search/index.json` |
| Prepared artifact | `$DOTLINEFORM_DOCS_BASE_DIR/preview/documents/` | `$DOTLINEFORM_DOCS_BASE_DIR/preview/search/index.json` |
| Site-preview / public | `site/assets/data/docs/` | `site/assets/data/search/analysis/index.json` |

Working builders and management follow-through write local output and finished public artifacts. They queue exact completed writes/removals; Publish applies only those selections to Preview and configured public destinations. Named collections retain their configured Preview/public reader roots. [Builder](Builder.md#publish-preparation) owns preparation and queue handoffs.

Media references and authoring before/after differences are operation-local inputs, with no `publication-media.json` or additional by-ID JSON field. Index generation reads the single canonical `working/source/unpublishable.json` once per operation and carries the list in memory; neither management nor public indexes store a copy. Exact and complete generation apply the current policy, comparing resulting membership with saved public indexes. The `docs_publish_pending_v1` current/deleted document selections optionally carry `removed_media` alongside collection/current media. Removals merge across later selections until transferred, or cancel when completed generation restores a reference with ready bytes. [Publication Media](data_model/Publication_Media.md) explains the handoff; [Media And Asset Handling](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals) owns ordering and manual cleanup.

Manage-only Catalogue target discovery is the `/docs/catalogue-media-targets` response over configured Working Catalogue indexes. It retains `docs_semantic_token_target_lookup_v2` without a persisted application lookup file or target-refresh builder. Authoring and Subject pickers normalize this response through their existing Catalogue provider. `docs-viewer/data/generated/` is not a payload fallback or a served static family. [Target Lookup](Target_Lookup.md) owns the discovery boundary.

## Collection Manifest Ownership

The [collection builder](../../docs-viewer/build/docs_builder/collection.py) produces complete `manage-manifest.json` and eligible reader `manifest.json` together from the same metadata. Each manifest contains exactly one root `docs` array; collection identity comes from the configured owner and route. Management includes requested Draft documents and scalar Subject metadata; no customisation envelope or Subject generation hash remains. Browser collection configuration supplies list/by-ID locations without customisation descriptors or loader registries. The local generated collection route serves the management manifest and exact common by-ID documents; it does not serve the public manifest.

Application writes pass exact changed/deleted document identities to the builder. Targeted Working builds parse the saved management manifest once without auditing its schema, rows, identities, dates or Subjects, merge selected rows and use saved membership/titles as rendering context. Unselected rows and document payloads remain intact. The manifest is written only when its projected contents change. Missing/unreadable JSON fails with a complete collection Build instruction; unavailable required fields fail where consumed. There is no public-manifest agreement check or full-source fallback. Catalogue Regenerate supplies already parsed sources and generated Work records to the same in-process builder and carries the completed manifest and Selected state between per-Work builds. Selected and Links follow-through parse saved data without complete-list/schema audits; exact configured file/owner handling, authored-reference parsing, required date projection and completed writes retain their owners.

Working keeps eligible public `manifest.json` beside each management manifest. Context emits authored `has_thumbnail: true`, otherwise Work-only scalar `subject`, otherwise neither. Folder/private fields and management manifests remain local. An excluded ordinary host produces an empty public collection inventory; its document withdrawals remain separate exact effects. Only a changed projected public list is written/queued. Publish copies that completed file to Preview/public destinations without source reads, eligibility filtering or projection. [Subject Associations](data/subject-associations.md#subject-and-association-shape) owns scalar/thumbnail semantics.

Identity and date contracts remain unchanged. Targeted reconstruction rejects retired Subject shapes in saved metadata; a complete collection Build owns reconciliation. Collection diagnostics report the selected `manifest_filename` and one `manifest_changed` count; the former separate management-manifest count is retired.

## Route Payload Contract

| Capability | Public route source | Manage route source | Notes |
| --- | --- | --- | --- |
| Navigation tree | `index-tree.json` | `index-tree.json` | Public and manage tree nodes share the same nested structure. |
| Selected document render | by-id payload | by-id payload | By-id payloads remain in scope for selected documents. |
| Info-panel metadata | selected by-id payload | selected by-id payload | Public reader metadata is limited to title, summary, and last updated. |
| Search | search payload | search payload | Search runtime reads separate search payloads. |
| Recent | unchanged copy of Working `recent.json` | Working generated `recent.json` | One stage-independent payload lists recently edited documents; readers own navigation. |
| Management metadata/actions | not public route data | management services and manage payloads as needed | Public tree/by-id payloads should not carry management-only metadata. |

## List Date Projections

All collection reader and management manifests, Search result metadata, Recents and Selected Documents use populated update dates in canonical `YYYY-MM-DD` form. The ordinary builder's in-memory flat rows use the same projection; no flat index file is written. List inventories omit `added_date`; source Markdown and by-ID document payloads retain their original `added_date` and `last_updated` precision for exact document metadata and source/output consistency checks. Collection reader manifests include `last_updated` even when they previously exposed only identity, title and subject. Ordinary navigation trees retain their authored order and carry no update dates.

Recency sorting uses the projected update date; entries updated on the same day use the owning report's deterministic title/identity ties. List dates derive from existing source timestamps or dates. Undated documents retain an empty update value, sort after dated report entries and are excluded from Recents; creation dates are never substituted. Catalogue, Works and Selected Documents continue to require populated update dates. Source-to-list date projection fails on an unprocessable selected value at its owning operation. Targeted collection builds consume saved management metadata in Working without auditing unselected dates; explicit full builds own baseline reconciliation. Standalone Search consumes selected saved metadata and required source content without source/manifest/by-ID agreement audits; required source-to-list date projection remains at its generation owner.

## `index-tree.json` Contract

Public and Manage `index-tree.json` use the same nested document structure. The root fields are `generated_at`, `schema` and `docs`, with the timestamp written first. The timestamp changes only when projected contents change. The retired `viewer_options`, `non_loadable_doc_ids` and `manage_only_tree_root_ids` have no configuration, payload or runtime role.

Working contains all ordinary documents, including drafts. Upstream public preparation derives the eligible public tree from saved metadata; Publish copies only its queued finished bytes. Navigation retains exact IDs and authored order, with the configured default or first Index root.

`docs` is an array of root nodes. Child relationships are expressed with each node's optional `children` array.
Generated tree nodes do not carry `parent_id`; `docs-viewer-tree-payload-adapter.js` derives runtime-only parent ids while normalizing the nested payload for existing renderer and management state.

Public `index-tree.json` nodes should stay as close as possible to:

- `doc_id`
- `title`
- `children`, only when non-empty
- `ui_status`
- `report_id`, only when the document hosts a registered report

Fields excluded from public `index-tree.json`:

- `summary`
- `last_updated`
- `viewer_url`
- `content_text_length`
- default or derivable values

Working tree nodes additionally carry boolean `draft`, which does not filter the browser Index and is omitted from the public tree. Working generates the eligible `public-index-tree.json` alongside its complete `index-tree.json`; Publish copies the former to Preview/public `index-tree.json`. Neither tree carries a transport URL, and the reader resolves exact document identity through configured owners. Local reads consume saved metadata without loading publication policy or canonical ancestry. `ui_status` remains separate presentation metadata. `report_id` comes from the validated report descriptor so the shared index renderer can identify report-host roles without loading every by-ID payload; it grants no loader access.

## By-Id Payload Contract

Selected document loading stays by-id.
The public info panel reads selected-document metadata from the selected by-id payload, not public tree rows and not `index.json`.

Public reader-facing by-id metadata for the info panel is:

- title
- summary
- last updated

By-ID `summary` retains the authored text, including emphasis markers and internal newlines. A nonempty Summary additionally carries `summary_html`: builder-produced restricted emphasis paragraphs, with explicit line breaks and escaped literal HTML. Document Summary blocks and the pinned Info panel consume the same completed fragment; list/discovery metadata does not carry this rendered field. Empty Summary omits both optional fields. [Builder](Builder.md#summary-block) owns syntax and generation.

Local and public readers consume the same generated by-ID document. Eligible ordinary/non-Catalogue payloads retain `draft: false`; Catalogue omits it. Diagrams use ordinary imported SVG references; fenced code remains code. Private collection authoring metadata remains in management manifests; source paths and authoring controls are not part of the public info panel. Both readers hydrate selected-document information from by-ID payloads rather than tree rows.

A report host carries `report` with required `id` and `collection` only for `docs_collection`. Other reports omit `collection`; no `preset` or null placeholder fields are generated. Local and public report readers select the renderer by `id` and collection storage by the configured collection identity. The full descriptor stays in by-ID payloads, while the Index projects only `report_id`. [Reports](Reports.md#build-and-payload-flow) owns source validation and registry/loader boundaries.

## Search Contract

Search runtime reads the separate search payload through `search_index_url`, such as:

- Public: `/assets/data/search/analysis/index.json`
- Manage: `/docs/search`, resolved to configured Working output

Search selects eligible targets from saved Working metadata, reads each required source through its confined exact path and parses front-matter fields plus report declarations needed for text extraction. It does not reopen collection by-ID documents, reread canonical ordinary ancestry, repeat Subject/readiness/thumbnail validation or compare source/title/date/parent metadata against generated output. The final table retains supplied display metadata; normalization belongs to term/token generation. The complete Working Build supplies its already loaded records through the same projection. Search build inputs do not depend on retired public docs `index.json`.

## Recent Contract

Recents uses one `docs_recent_v2` artifact with `schema`, `limit`, `generated_at` and `docs`. Explicit discovery refresh and Full Working Builds generate it and queue only changed content; unchanged content preserves saved bytes and timestamps. Publish only transfers queued bytes. The workspace's limit remains 20, update-based sorting remains authoritative, and no stage/public variants are generated.

Each row carries exact `doc_id`, title, one date-only update `timestamp` (`YYYY-MM-DD`) and optional parent context. Collection rows additionally carry `collection`, `report_doc_id` and `collection_title`. Rows contain no stage, result URL or `content_url`. The active route resolves navigation from exact document/collection/host identity. Recents and Search share result navigation but load independent artifacts.

Recents retains Search's configured base coverage: ordinary documents plus explicitly included collections, with draft/subtree/host eligibility applied by [the metadata selector](../../docs-viewer/services/docs_discovery_selection.py). It removes exact [Recent exclusions](Source_Organisation.md#recent-exclusions), sorts dated candidates and takes the configured limit. Hosts have no automatic Recent exclusion. Search membership remains separately owned.

The [Recent payload owner](../../docs-viewer/services/docs_recent_payload.py) projects one eligible discovery selection and supplied ordinary update dates. Explicit discovery refresh carries dates from the sources already parsed for Search; full builds reuse loaded ordinary records. Included collections supply completed Working `manage-manifest.json` metadata: identity, title, date-only `last_updated` and draft state for non-Catalogue collections. Selection shares pruning without row/schema/identity/title/date/readiness audits. Recent excludes exact targets, sorts dated candidates and limits its constructed rows without additional body reads, a Search-index read or a source-scan fallback. Missing/unreadable required metadata fails at its owning read/use. Full maintenance supplies built collection metadata; standalone ordinary builds and discovery refresh consume saved collection metadata.

Manage **Refresh Search and Recent** and full Working maintenance own explicit generation. Targeted/collection-only generation, Save, Move, Delete and eligibility changes preserve saved Recent. External Recent-exclusion edits take effect on the next explicit discovery refresh or full Build. Opening Recent only reads saved JSON.

Changed Recent completion queues the finished file, preserving existing pending selections when unchanged. Publish copies its bytes through Preview to the repository without reserialization, sorting, limiting, freshness checks or timestamps. An unqueued Recent file remains untouched. Publish neither writes Working Recent nor returns a `recent_updated` marker or triggers a browser Recent/capability refresh. Required file/path checks and selected byte verification remain; readers consume the saved payload directly. Search also queues only changed saved output and retains its standalone CLI.

## Public Flat `index.json` Retirement

Public flat `site/assets/data/docs/scopes/<scope>/index.json` is retired from the Docs Viewer route contract.
Public Docs Viewer routes do not publish or load it.
The route contract is covered by:

- `index-tree.json` covers navigation
- by-id payloads cover selected-document rendering and info-panel metadata
- search reads its separate search payload
- Recent reads its small generated payload

Document-package needs for richer document data are covered by `docs_document_packages.source_context`, `docs_document_packages.source_records`, and `docs_document_packages.rendered_content`.
Those helpers read configured docs source and source-rendered content for direct document-package workflows.
It must not fall back to public flat indexes, generated by-id payloads, search payloads, Recent payloads, manage/local generated indexes, or generated metadata JSON.
Other tooling needs for richer generated data still need their own owning contract.

Private collection `manage-manifest.json` files remain owned by configured Working generated storage and are not public route dependencies. Reader targets and Links carry exact document/collection identities without stage fields. The standalone backlinks and semantic usage outputs are retired; [Related Links](Related_Links.md) expands persisted relationships into document content. Storage/build completion receipts retain internal provenance. [Configuration And Extension Points](Configuration_And_Extension_Points.md) owns current identity and service contracts.
