---
draft: false
doc_id: d-20260423-000000-c9f3ea
title: Builder
added_date: "2026-04-23 00:00:00"
last_updated: "2026-10-01 13:29:44"
parent_id: d-20260424-000000-50b63f
---
# Builder

The Docs Viewer builders turn canonical Markdown and front matter into generated reader and search payloads. They do not deploy the site.

## Commands

The commands below use the single Docs workspace. Working source/generated storage and the read-only Preview snapshot live directly beneath the configured existing Docs root. Ordinary builder commands require `--stage working`.

```bash
python3 docs-viewer/build/build_docs.py --stage working
python3 docs-viewer/build/build_docs.py --stage working --write
python3 docs-viewer/build/build_docs.py --stage working --collection works --write
python3 docs-viewer/build/build_docs.py --stage working --collection catalogue --only-doc-ids <doc-id> --skip-media-builds --write
python3 docs-viewer/build/build_docs.py --stage working --only-doc-ids <doc-id> --skip-media-builds --write
python3 docs-viewer/build/build_search.py --stage working --write
```

Dry-run is the default. Document Build and Search require an explicit stage and reject `--scope`. Search accepts Working only. Preview preparation invokes Document Build with `--stage preview` and an explicit temporary `--docs-base-dir`, then copies its captured Working Search file; it does not create source/generated directories in the live Preview snapshot. `--only-doc-ids` selects ordinary or named-collection document payloads after orchestration has identified the affected documents. A full stage build can initialise or reconcile generated output. Links retains exact changed-document and affected-neighbour maintenance. Search remains an explicit complete-index rebuild, without a targeted-postings or Catalogue mode. The public Document Locations builder and its unused picker/index are retired; document navigation uses exact IDs and configured routes.

Named collections use the same builder for full and targeted operations. New, Save, metadata, Delete, imports, collection moves and watcher changes pass exact before/after source document IDs through `--collection <id> --only-doc-ids <ids>`. The builder reads and renders only selected surviving source files, merges their reader/manage rows into the saved manifests, and removes selected deleted entries. Saved identities provide membership and link destinations; saved authoring subjects supply unchanged entries when recomputing the subject association index. Unselected customisation rows and by-ID files are preserved. Targeted collection builds skip registered media producers. Links receives exact changed/deleted identities separately and owns lazy record creation; its direct-neighbour reads and updates do not broaden document rendering. Complete Build, Prepare Preview and initial collection creation omit the selector and retain full source loading and rendering.

Targeted collection builds require readable reader/manage manifests with agreeing document membership. Missing or invalid saved metadata fails; a complete Build owns reconstruction, with no automatic full-source fallback. Targeted builds do not scan unselected by-ID files. Diagnostics distinguish `targeted_collection` from `collection` and report source files scanned, total saved documents, rendered documents and selected IDs separately. Ordinary targeted builds retain their existing complete source read for index projection. The retired semantic usage index is not a build prerequisite.

## Workspace And Owners

`docs-viewer/config/workspace/docs-workspace.json` owns:

- Working collection registration and separate Working/Preview defaults
- the public section URL, public document and Search destinations, and retained R2 media addresses
- media registration, hierarchy policy, Search fields and the Recent limit

`docs_workspace_config.py` derives Working and Preview paths from the existing `DOTLINEFORM_DOCS_BASE_DIR` and selected collection. Temporary Preview builds use an explicit isolated Docs root. `build_docs.py` delegates focused work to `docs-viewer/build/docs_builder/`. `build_search.py` owns the separate whole-index Search projection. Neither owner should carry a hand-maintained scope list or select an implicit authoring stage.

## Docs Build Flow

1. load and validate the configured source corpus
2. parse identity/tree metadata from front matter
3. run configured media producers into their configured build outputs
4. determine generated removals and refresh Working Links for selected changed/deleted documents and their affected neighbours
5. resolve supported media and semantic tokens, interpret Unicode-whitespace-only lines as blank outside fenced code and explicit `<pre>` blocks, then render Markdown and permitted raw HTML with Related links using the refreshed records
6. build the tree, Recent, per-document and browser-config projections
7. compare content versions, write changed payloads and remove stale owned payloads before returning success

The source Markdown is canonical. Generated JSON is a projection and can be rebuilt. Render-time blank-line hygiene does not rewrite source files; managed Source Save and Docs Import apply the same narrow rule when they write canonical Markdown.

Configured media producers run before document rendering. A full build requests every configured build-media identity; an ordinary `--only-doc-ids` build derives build outputs from the selected documents' logical media tokens and requests only those identities. Named-collection targeted builds skip media producers. Mermaid is the first registered producer: canonical `.mmd` remains source authority and its same-basename sanitized SVG is the published reader asset.

## Reader Subject Metadata

Every ordinary and sub-scope `by-id/<doc_id>.json` payload and every document row in a sub-scope `manifest.json` contains `subject`. A valid Catalogue declaration becomes an exact `{kind, key}` object, such as `{"kind": "work", "key": "00635"}`. Supported kinds are `work`, `series` and `detail`; keys remain strings, including leading zeroes and the complete Detail UID. Missing, malformed, conflicting or Folder declarations produce `null`. `docs-viewer/services/docs_document_subjects.py` owns this compact reader projection through the existing authoring normalizer; it does not consult Catalogue data or infer identity.

The same projection serves local and public reader payloads without exposing Folder paths, raw source values or authoring diagnostics. `manage-manifest.json` retains its separate `authoring_subject` metadata for management controls and diagnostics. Document Build updates the reader Subject in both manifest and by-ID output, including clearing it after a declaration is removed. Preview and deployed site snapshots receive the field through their normal publication workflow.

Manifest rows do not repeat `sub_scope`: their configured report supplies exact collection context to list and detail consumers. Subject metadata supports subsequent icon rendering but does not add icons itself.

## Document Relationship Maintenance

Ordinary and collection Doc Build call `docs-viewer/build/docs_builder/links_builder.py` before rendering document output and await its completion. The same refreshed records supply related-links sections in that build. Determine generated document removals once before relationship maintenance and carry those IDs into the final output plan. `docs-viewer/config/links-builder.json` selects Working, including its configured collections. Source-write operations and the watcher pass exact changed/deleted document IDs separately from the ordinary renderer's target set. A full collection render or an ordinary-renderer fallback does not expand an ordinary save's Links target set.

Resolve local document ownership through configured Working storage and exact `doc_id`, with `collection` only for a named owner. Collection viewer links identify their owner through the configured report host. Relationship identity is `{collection, doc_id}`, with an empty collection for ordinary documents. Readers derive navigation from that identity and their configured viewer route/report hosts. Stage/scope-bearing targets are invalid. Authored Markdown/HTML document links and supported Catalogue Work image/media tokens supply references. Work tokens name `{collection: "catalogue", doc_id: "<work_id>"}` directly; Gallery Media View tokens contribute no document relationship. A Catalogue document's token referencing its own Work is omitted from the graph.

`links_model.py` owns unique directed document relationships and endpoint summaries. `links_schema.py` validates and serializes separate `generated/documents/links-by-id/<doc_id>.json` records beneath the configured Working root, shared by parent and child documents. Version 4 contains only `schema_version`, `self`, `incoming` and `outgoing`. `self` and each entry directly in the incoming/outgoing arrays use the same flat `{collection, doc_id, title}` object. Explicit identity lets the same records stand alone in the aggregate without their filenames. Repeated links to the same document collapse to one relationship in each direction, regardless of label or destination fragment; occurrence details and stored counts are omitted. Counts of distinct incoming/outgoing documents can be derived from the list lengths. Earlier schemas are rejected; saved records require explicit migration rather than runtime compatibility reads. These records supply targeted related-links builds and the local workspace diagnostic aggregate; the per-document Links view and read endpoint are retired.

`related_links.py` reuses the existing updater's refreshed version-4 records for the [Related Links](Related_Links.md) directive. Full and targeted Working builds include current outgoing links and saved incoming links in the same document build. Dry runs pass those records in memory; write builds persist the same records before rendering. Expansion does not refresh relationships again, scan neighbours or derive a separate graph. The existing per-collection full Build flow remains unchanged. Publish captures persisted records, binds them into its input revision and filters their entries to the already selected eligible document IDs; the temporary Preview build receives that captured directory through `--related-links-dir`.

The Markdown block parser consumes related-links directives without treating heading text as links. Expansion reuses the icon renderer, emits portable query targets and marks generated anchors; the shared anchor collector omits those anchors from backlinks and authored-link diagnostics. The completed relationship refresh is the input to section rendering, so the section does not depend on document rendering order. Search and publication distribution do not derive these sections.

The existing Links record is the refresh's only relationship prior state:

1. Read the current record if present, preserving its incoming and previous outgoing entries. A missing record is normal for a document that has never participated in a relationship.
2. Parse the current document's Markdown and extract outgoing document targets without checking destination existence or link validity, deduplicating by exact document identity. Removing one repeated link preserves the relationship while another remains; removing the last removes it.
3. Read each linked neighbour's relationship record, creating one only when this relationship first needs it. Titles come from loaded documents or existing records; new endpoints may read source metadata for a title, with authored text or the target ID used when metadata is unavailable. No generated destination read permits or suppresses a relationship. Replace the current document's incoming contribution there and copy the neighbour's summary into the new outgoing list. Preserve every other contributor.
4. When the current title or collection identity changes, update its outgoing summary in each known incoming neighbour.
5. Remove its incoming contribution from previously linked neighbours absent from the new list.
6. Create the current record only if outgoing relationships need it, then write the current details and outgoing list while preserving incoming entries; write only changed records. Retain existing records when both lists become empty. The Related links directive alone never creates a record.

A neighbour update does not rebuild that neighbour's Markdown or ordinary payload and does not recurse into its neighbours. No collection Index/manifest, reference baseline or whole-graph pass supplies Links refresh state. Relationship construction does not validate destination existence or link validity; Broken Links is the independent authoring audit. Explicit document deletion still removes the deleted record and its associated incoming/outgoing relationships, and collection moves retain their existing graph cleanup.

Manage's full Rebuild docs and Search includes Catalogue after Context, ordinary documents, Concepts and Moments. Each contributor refreshes its relationships before Catalogue renders its Related links sections. Rendering reuses the refreshed records in memory, without an extra Links-file change check or second read. A full build renders every Catalogue source, compares each complete resulting by-ID JSON with the saved file, and writes only differences. A changed incoming relationship therefore updates a Catalogue page even when its Markdown is unchanged. This output comparison does not skip rendering. Full Catalogue Regenerate owns source-body changes; ordinary document Build renders the saved source bodies.

Links reads the configured Working ordinary `source/documents/unpublishable.json` once per operation through `docs_publication_ignore.py`. An ordinary document is excluded when its exact ID or any ordinary ancestor's ID is listed. The file stays a flat list of explicit roots; `parent_id` inheritance is resolved in memory, reusing loaded parents or reading only exact ancestors needed by a targeted operation. Named collection IDs do not participate, and report-host exclusion does not change their Working Links eligibility. Drafts remain linkable. The Insert document link picker applies the same ordinary subtree exclusion. Editing the file does not reconcile existing relationships automatically; subsequent selected refreshes apply the policy, and a complete Working Build reconciles every document. `folder_path`, `work_id`, `series_id` and `detail_uid` are independent authoring subjects and never determine eligibility or appear in Links summaries. Folder documents follow the same rule as all other subjects. Subject-only and draft-only edits leave Working Links unchanged.

Per-document Links maintenance owns lazy creation at both ends of a resolved relationship. A document with no outgoing links can still need a record for incoming contributions. A document without a record or resolved outgoing links remains without a record. Complete builds, source operations and the watcher use this same rule; none performs a separate population pass or passes creation identities. Source Save remains a source-only write, with the watcher independently invoking Document Build. New records contain exact identity, title and the required relationship contributions. Existing records remain the relationship prior state and are not reset or replaced.

A missing record does not trigger discovery of incoming contributions across other documents. Those contributions are maintained when referring documents build. A complete Build applies the same per-document rule across its built documents, reconstructing relationships from their authored outgoing links. Record creation itself never reads a collection index or scans neighbouring source bodies. Empty historical records may be removed as an explicitly requested one-off cleanup; routine builds do not prune them.

Deletion and exclusion use the previous record to remove the document's contributions from known neighbours before removing its own record, including the final document in a child collection. An excluded document with no record is silently omitted. Eligible records also discard incoming entries from excluded ordinary documents, and outgoing resolution omits excluded targets. A complete Build therefore removes excluded records and their relationships, including stale incoming entries whose excluded source record is already absent. Collection placement keeps the immutable ID: the destination builds first and transfers the exact prior Links record after the old source is removed. The former collection's deletion cannot remove the destination-owned record. The placement owner rewrites authored source links; Links updates counterpart identities, including self-links. Builder diagnostics report distinct outgoing relationships added or removed.

A Working workspace lock serializes relationship creation, refresh writes and removals. Success means ordinary output and required Links writes/removals have completed. Malformed records and actual operation/write failures propagate synchronously; a failure can leave ordinary output and some relationship writes completed. Targeted operations have no full-refresh fallback. Correct malformed source or records explicitly; a complete Build reconciles current authored relationships and the ignore policy without populating unrelated empty records.

Complete Working Build applies this same refresh to the documents it builds and then aggregates the prepared records before recording completion. Ordinary saves leave the aggregate alone. `docs-viewer/tests/python/test_docs_links_builder.py` and the write/watcher/lifecycle tests still target retired scope contracts and require separately specified migration before their results can establish current coverage. The separate `docs_backlinks_v2` output remains owned by `backlinks.py`. Named-collection updates still read and compare shared JSON indexes, rewriting those files when changed; watcher polling still inventories filenames and timestamps. The watcher seeds its parsed source snapshot at startup, then replaces only changed named-collection entries, including after suppressed management writes. Ordinary source inventories and backlinks retain their existing cost. Targeted source reads do not imply collection-independent total Save time.

## Publish Preparation

Working owns authoring. The preparation phase of **Publish** captures the complete eligible Working set and saved Search, Recents and inventory-selected Catalogue JSON. `docs_prepare_preview.py` invokes the document, collection and registered media builders synchronously through `build_preview.py` in a temporary workspace; Search and Recents are copied without rebuilding. `docs_preview_snapshot.py` validates the completed build and assembles reader payloads with exact shared asset references. There is no user-facing preparation plan or confirmation.

Draft documents and their descendants are excluded. Ordinary roots listed in `working/source/documents/unpublishable.json` and their descendants are also excluded; an excluded collection report host excludes its collection. An intentionally empty policy contains `[]`; missing or invalid policy fails visibly. Prepared sources retain explicit boolean readiness. Collection owners project their own fields; ordinary source bytes remain unchanged. Empty eligible collections are valid.

The service carries its captured inputs through the synchronous operation without intermediate freshness checks or repeated source/snapshot scans. It writes `preview-manifest.json` only after verifying every final file. The receipt records source, generated and Preview revisions. Failure before replacement leaves the previous Preview intact; a replacement failure leaves no valid completion receipt and requires a fresh Publish. Temporary source/generated inputs are removed when the operation finishes. Preview is read-only, has no persistent source tree and remains inspectable independently of the repository destination. The same completed snapshot is passed directly to distribution.

Links remains Working-only. If ready A links to draft B, preparation omits B and retains A's authored link. This does not include B or add a publication warning or gate. The Working Broken Links report remains independent.

### Historical Pre-publish Selection Evidence

The selection below documents evidence from before scope retirement. Its scope-based fixtures have not been migrated or accepted against the current workspace contract; do not treat the historical result or command as current verification. Any migration requires its own agreed test specification.

The bounded historical selection in `docs-viewer/tests/python/test_docs_pre_publish.py` is `test_readiness_and_intent_exclude_descendants` (draft subtree exclusion), `test_ignore_set_is_additional_and_does_not_exclude_child_collection_ids` (ordinary ignore membership, draft coexistence, sub-scope identity isolation, ignore-file removal and no policy-file projection), and `test_excluded_host_omits_collection_and_next_rebuild_removes_deleted_content` (draft and ignored report hosts remove prepared child output). These cases use the file's `repo` fixture: temporary documents, one Works host/child, a draft parent and ready descendant, and a local SVG. They exercise production source parsing and preparation; apply cases run the real Docs/Search builders in process through a substituted rebuild-command launcher. All writes stay in pytest temporary storage, with Docs and Projects environment settings isolated by the shared fixture; no real workspace publication, network, browser, or live service is used. The selection protects the existing rules around the changed descendant traversal; it does not directly exercise a ready ignored parent with multiple descendant levels. New coverage needs a separately agreed test specification. Expected cost is seconds to tens of seconds with local filesystem/build work; setup and failure diagnosis dominate. Run once for a relevant selection change and repeat only for a related failure or fix.

```bash
set -a
source .env.local
set +a
$HOME/miniconda3/bin/python3 -m pytest -q docs-viewer/tests/python/test_docs_pre_publish.py -k 'readiness_and_intent_exclude_descendants or ignore_set_is_additional_and_does_not_exclude_child_collection_ids or excluded_host_omits_collection_and_next_rebuild_removes_deleted_content'
```

### Working Rebuild

The **Rebuild docs and Search** action calls `/docs/rebuild` without a stage field. `docs-viewer/services/docs_write_rebuild.py::rebuild_working_outputs` resolves Working and calls the internal `rebuild_stage_outputs` owner, which awaits the main document collection, every configured child collection and requested Search, then aggregates relationships before recording the completed Build manifest and returning success. Ordinary source writes and watcher rebuilds omit Search. The builder retains internal stage provenance; local reader and authoring requests do not select it. Publish separately invokes a complete captured document build in temporary storage.

`docs-viewer/services/docs_workspace_links.py` combines every prepared `links-by-id/<doc_id>.json` beneath the configured Working generated documents root into the sibling `links.json`. Its version 4 envelope contains `schema_version` and `documents`; each record carries flat document summaries with `collection`, `doc_id` and `title` directly in its incoming/outgoing arrays. Included records remain unchanged in deterministic file order. Only records with both incoming and outgoing lists empty are omitted; incoming-only records remain. Document Build owns relationship maintenance and the existing Working eligibility policy; destination validity belongs to authoring.

Aggregation reads all inputs before writing and replaces the saved snapshot only when its serialized content changes. An empty prepared directory produces a valid empty aggregate. Missing or unreadable input, invalid JSON, stale schema/target identity or malformed list fields fail the rebuild visibly before completion is recorded; aggregation does not silently skip an input or save a partial result. Removed upstream records disappear on the next completed workspace rebuild.

Save, watcher builds and individual-document rebuilds update the prepared records but leave `links.json` at the last completed workspace rebuild. Opening or refreshing the local Links report only reads that saved snapshot. [Reports](Reports.md) owns its presentation and navigation. The existing files `test_docs_scope_links.py`, `test_docs_write_rebuild.py`, `test_build_search_python.py` and `test_docs_workflow_stages.py` under `docs-viewer/tests/python/` still target the old contracts; they have not been migrated or run as Retire Scopes evidence. Test migration requires its separately approved specification.

## Source Contract

The common front matter is `doc_id`, `title`, `parent_id`, `added_date`, `last_updated`, and optional `summary`. Ordinary and other named-collection sources additionally require `draft` as an explicit boolean in Working and captured preparation input. Catalogue sources reject that field and have fixed document eligibility; Catalogue creation, Regenerate, management metadata, list manifests and by-ID payloads omit it. Source loading, Search, preparation and Source Save validate the owning collection's readiness rule before using or writing the document. New ordinary and other collection documents, imported documents and collection report hosts start with `draft: true`. Prepared sources retain applicable captured readiness fields, while public reader payloads omit authoring readiness. An excluded ordinary collection host still excludes its collection, including Catalogue. Ordinary workspace documents additionally support free-text `ui_status`, without a fixed value enumeration; this includes the text `draft`, which has no publication effect. Named collection documents do not use that field: source formatting and collection-placement rewrites remove it, collection management manifests and by-ID metadata omit it, and the metadata endpoint omits it for collection targets. The reader's optional status artwork is a separate presentation mapping. `publishable` is retired and rejected. The ignore list is separate Working source policy data and is not copied into prepared content. Source validation is owned by the builder/source model.

- new documents give `added_date` and `last_updated` one captured full timestamp; after creation, only body, `title`, or `summary` changes advance `last_updated`.
- edited Recent includes only full `last_updated` timestamps; legacy date-only values become eligible after the next qualifying edit.
- Exact ordinary ignore-list IDs control Working relationship and picker eligibility; inherited descendant exclusions also apply to Preview selection.
- `draft: true` records readiness and does not exclude an otherwise eligible Working relationship source or target.
- hierarchy comes from `parent_id`, not folders.
- whether nested Markdown is allowed comes from the configured stage and collection.
- sibling order is title-based with a stable id tie-breaker.

Authoring extensions supported by the renderer include:

- <code>&#91;&#91;media:...&#93;&#93;</code> for configured docs media
- <code>&#91;&#91;html-media:docs/html/...&#93;&#93;</code> for ordinary HTML media, with <code>docs/sub-scopes/&lt;id&gt;/html/...</code> for an exact child owner
- explicit Catalogue `media` and `image` tokens for Media View links and Catalogue images; the retired three-part Catalogue text form has no compatibility alias

Ordinary Markdown document links are the relationship input. Local document href rewriting preserves explicit child selection, fragments and HTML escaping; URLs with a hostname, including protocol-relative external URLs, retain their authored destination.

Use [Docs Images And Assets](Docs_Images_And_Assets.md) for authoring guidance and `docs-viewer/build/docs_builder/` for the exact token rules.

## Preview And Deployment Boundary

Working Build produces replaceable `working/generated/` output. Publish preparation owns eligibility and the complete `preview/` snapshot, recorded as `docs_preview_manifest_v2` with internal `stage: preview` provenance. There is no `/docs/preview/*` browser surface. Ordinary local reads resolve Working directly; site-preview serves the repository output.

Search is a stage-independent `docs_viewer_search_index_v4` artifact built only in Working. Its header omits stage, its document rows omit result URLs, and its content version excludes stage. Readers use exact document/collection/report-host identity with their configured routes. Publish preparation captures the existing index, binds its bytes into the plan revision and copies it before recording build completion. Snapshot and repository projection preserve those exact bytes without JSON reserialization, label rewriting or rehashing. Missing/invalid Search fails without a rebuild fallback. Edits are unavailable during the synchronous operation; no intervening freshness check is needed. Search membership is separate from prepared document completeness.

`docs_publish.py` owns the empty-body `/docs/publish` request. After preparation completes, `docs_deploy_repo.py` receives its `CompletedPreview` with verified bytes and receipt, compares configured destinations once and applies the resulting operation-local plan. Distribution does not read source/generated output, prepare content or apply another document filter. It reconciles document/Search output, inventory-selected Catalogue JSON, referenced shared media and any configured publication-lineage projections. Completed repository output and transfers are verified; incomplete distribution is reported as failure while retaining completed Preview. Public reader payloads have public URLs without a `published` stage discriminator. Git commit/push and the manually triggered GitHub Pages workflow remain separate actions.

Manage offers one Publish action, remains busy until preparation and distribution finish and shows complete or phase-specific failure feedback. The stage selector, separate preparation/distribution endpoints, change-review modal and intermediate confirmation are retired. Review the repository result through `bin/site-preview`. Historical lifecycle tests remain unchanged and unreviewed for the current contract; manual success and static source review do not establish exercised failure recovery or measured performance.

Working alone generates Recents with the same coverage and eligibility as Search. It reuses ordinary metadata already loaded by the full document build and reads only included, eligible-host collection management manifests, including their effective added/updated dates. It does not reopen collection Markdown or by-ID bodies. Manage Rebuild refreshes included collection metadata before the ordinary build generates Recents once, leaving excluded collections in their existing position afterwards. Direct full Working document builds require saved current collection metadata. Targeted builds and authoring follow-through preserve Recents; watcher/service fallback builds pass `--skip-recent`.

Prepare Preview captures saved Search and Recents, binds both byte sequences into its plan and copies them before recording completion. Neither is regenerated during the temporary Preview build. Snapshot assembly and Deploy Repo preserve the exact bytes, and readers resolve navigation from IDs in their own context. Recents' separate publication variant and stored content URLs are retired. The next full Working build removes the old `.publish/recent.json`. [Generated Data Contracts](Generated_Data_Contracts.md#recent-contract) owns the maintained Recents fields and lifecycle.

## Diagnostics And Safety

- the builder prints a compact human summary; `--diagnostics` adds machine-readable console diagnostics
- unchanged content is skipped unless forced
- targeted writes require an existing full-scope output tree
- renderer output allows raw HTML and is not a sanitization boundary
- management/service writes validate source and paths before calling builders
- the live watcher rebuilds document projections after source changes; Search and Recents retain their independent full-build ownership

## Change Guide

- workspace/source/output change: `docs-workspace.json` and `docs_workspace_config.py`
- Markdown/front-matter parsing: builder source model
- rendered document behaviour: renderer/token modules and acceptance fixtures
- search fields: `build_search.py` and Docs Viewer search runtime
- Preview preparation: `docs_prepare_preview.py`, `docs_preview_snapshot.py` and workspace configuration
- watcher invalidation: Docs live rebuild watcher
- build-source producer: producer registry, scope `source.build_media`, published `build_inputs`, full/targeted build tests, and reader-runtime boundary

Keep exhaustive output filenames, diagnostics fields, and CLI flags in code. This page should change when the build boundary changes.
