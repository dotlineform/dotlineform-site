---
draft: false
doc_id: d-20260423-000000-c9f3ea
title: Builder
added_date: "2026-04-23 00:00:00"
last_updated: "2026-10-17"
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

Dry-run is the default. Document Build and Search require explicit `--stage working` and reject `--scope`; neither builds Preview. `--only-doc-ids` selects ordinary or named-collection document payloads after orchestration has identified the affected documents. A full Working build can initialise or reconcile generated output. Links retains exact changed-document and affected-neighbour maintenance. Search remains an explicit complete-index rebuild, without a targeted-postings or Catalogue mode. Completed writes prepare public artifacts and queue their exact effects upstream; Publish copies those supplied files into Preview and configured destinations. The public Document Locations builder and its unused picker/index are retired; document navigation uses exact IDs and configured routes.

Named collections use the same builder for full and targeted operations. CLI operations pass exact affected IDs through `--collection <id> --only-doc-ids <ids>`. Application New, Source Save, Draft and exact Rebuild supply prepared source/report metadata to the existing in-process builder; Delete supplies known deleted IDs and an empty surviving-source selection. Imports and collection moves retain their own selected-input orchestration. The builder renders only selected surviving documents, merges their reader/manage rows into the saved manifests, and removes selected deleted entries. Saved identities provide membership and link destinations; saved authoring subjects supply unchanged entries when recomputing the subject association index. Unselected customisation rows and by-ID files are preserved. Targeted collection builds skip registered media producers. Links receives exact changed/deleted identities separately and owns lazy record creation. The publication handoff renders directly affected saved neighbours when their presentation changes. Complete Build and initial collection creation omit the selector and retain full source loading and rendering.

Targeted collection builds parse the saved collection manifest and consume its completed fields without membership/schema/row audits. Required read/parse/projection failures stop the operation; complete Build owns reconstruction, with no automatic full-source fallback. Targeted builds do not scan unselected by-ID files. Diagnostics distinguish `targeted_collection` from `collection` and report source files scanned, total saved documents, rendered documents and selected IDs separately. The retired semantic usage index is not a build prerequisite.

Ordinary builds derive document counts from the current canonical membership and required metadata. The [pipeline](../../docs-viewer/build/docs_builder/pipeline.py) returns its required tree, Recent, by-ID and write-plan results without constructing a separate flat `index_payload` or extracting plain text from every rendered payload for reporting. Documents Linking Here and the separate `backlinks.json` output are retired in favour of [Related Links](Related_Links.md); ordinary builds no longer read every rendered payload to scan anchors for a reverse-link index. Document-package export computes `content_text_length` through its separate source-context owner.

Ordinary application-write follow-through carries exact before/after identities, rendered payloads, navigation and changed relationship records into public preparation. Exact directly affected neighbours are rendered through the same owner, including Related Links and Work-title presentation dependencies, without recursive expansion or a corpus body scan. Parent changes do not rebuild unrelated children. Targeted operations preserve Recent and Search.

Application writes await their own exact generation. Prepared New, Source Save and Draft inputs are rendered without reopening their source files; exact Rebuild reads/parses saved source once and supplies its readiness-checked, report-classified record to the same builder. Its supplied Title remains literal with string representation required. CLI targeted builds load only selected surviving sources. Prepared application document generation and Delete do not regenerate/compare workspace browser configuration. Complete builds retain local configuration projection; the explicit design-time `python3 docs-viewer/build/build_browser_config.py` command projects both readers without a document build, as described by [Configuration And Extension Points](Configuration_And_Extension_Points.md#builder-and-local-service-integration). Ordinary membership and parentage remain owned by `index-order.json`, which canonical creation, Position and Delete update through their owning operation. The filesystem watcher and suppression machinery are retired. [Source Mutation Endpoints](Source_Mutation_Endpoints.md#post-docsrebuild-document) owns exact Rebuild's response and fresh-display completion.

Ordinary targeted builds read selected surviving Markdown and reuse unchanged navigation rows through [ordinary metadata](../../docs-viewer/build/docs_builder/ordinary_metadata.py). The current `index-order.json` defines complete membership, parentage and authored order, rejecting duplicate IDs. Selected sources replace their own saved metadata; unchanged titles, draft flags, status and report identifiers come from the saved tree. Current hierarchy excludes deleted or moved-out IDs and places surviving or moved-in documents; only selected absent IDs can remove by-ID payloads. A new current document without saved metadata must be selected or rebuilt through a full Build. Unselected Markdown validation and metadata freshness belong to each document's selected build or complete reconciliation.

The builder parses the saved Index tree once and consumes required navigation fields for unchanged current documents without repeating completed schema/identity/title/readiness audits or checking unrelated by-ID existence. Required file/parse/projection failures stop at their owner; a complete Build owns reconstruction. Service orchestration supplies selected IDs directly without a whole-source preflight. An empty targeted ID selector remains invalid instead of becoming a full Build; a nonempty deleted-ID selection can carry no surviving source records. Explicit full requests omit the selector, read every canonical source and regenerate complete navigation metadata.

Sort Children A–Z and same-parent Position share [navigation-only completion](../../docs-viewer/services/docs_navigation_order.py). Their service reads canonical `index-order.json` once and persists only a changed order. The shared owner reads the management/public navigation once each, reorders the selected sibling group while preserving existing public membership and complete subtrees, writes changed trees and queues only changed public navigation. It loads no builder/rendering configuration, document payloads, Markdown, eligibility policy, Selected, Search or Recent. Unchanged order preserves timestamps, queued selections and files; excluded public parents or children require no public work. Sorting trusts the browser's completed ordered child IDs without a membership audit; request parsing, authoring authority, exact node lookup and configured path/symlink confinement retain their boundary owners.

Reparenting Position additionally reads the moved by-ID payload, changes its `parent_id`, projects public eligibility and queues affected document/removal selections and changed navigation/manifests. Newly eligible content follows its exact source/rendering owner. Source bytes/dates, existing `content_html` and Links remain unchanged by the direct parent-field projection. Position does not read/requeue Selected because neither ordering nor reparenting changes its saved rows. Delete reads canonical tree and Selected once, removes the exact source subtree or flat collection target, then passes its remaining parent map, updated Selected/configuration and known deleted IDs into the existing builders. Ordinary navigation and collection manifests remove those identities; exact by-ID/Links removals and known-neighbour relationship updates follow without loading document bodies. Saved Recent and Search retain their explicit refresh owners.

Rendering, parent membership and tree projection reuse one document-identity lookup per operation. The targeted build carries its saved tree payload and text through timestamp and write comparison without reopening that input. Collection builders and document-package rendering pass their existing metadata lookups to the same rendering helpers. Links uses that lookup for known same-collection titles; its exact cross-collection or previously unknown neighbours retain their own source-metadata reads. Explicit `--links-doc-ids` can require additional selected sources independently of render targets, without broadening payload rendering. Optional targeted media processing receives the selected source text already loaded, including front matter, instead of reopening all Markdown; raw source text is retained only when that media operation needs it. Search and Recent retain their existing explicit refresh boundaries.

Ordinary diagnostics report `docs_total` as current canonical document count, `docs_emitted` as the number of rendered document payloads and `source_files_scanned` as the source loader's actual selected reads. The source count excludes separately owned Links neighbour metadata. These counts distinguish a targeted update from complete reconciliation without a separate flat metadata inventory. The retired backlinks payload, write-plan fields and diagnostic counter have no compatibility return values.

The legacy tests `test_build_docs_payloads.py`, `test_build_docs_recent.py` and `test_build_docs_subscopes.py` under `docs-viewer/tests/python/` consume the removed flat return value and also use retired scope/stage fixtures. They are unreviewed for the current workspace contract. Their separately specified modernisation should assert required generated outputs and reporting counts through current workspace fixtures; they do not justify retaining unused production computation or a compatibility return value.

`test_docs_write_rebuild.py` in the same test directory references the removed prerequisite-fallback helper and obsolete scope APIs. `test_docs_live_rebuild_watcher.py` is unreviewed residue of the retired production owner. Their old missing-output scenarios expect automatic full rebuilding, which the current targeted contract explicitly rejects. These selections have not been run or changed. Separately specified modernisation should cover current-workspace selector forwarding, empty-selection rejection, builder prerequisite failures, and exact source-write/build failure behavior; obsolete helper imports do not require a compatibility alias.

The rendering cases in `test_docs_document_link_targets.py` and `test_docs_workflow_stages.py` also pass the retired list-based helper argument and expect scope/subdoc or pre-publish routes. They remain unreviewed and unchanged. Future current-workspace generator coverage should protect selected source reads, saved tree merging, canonical creation/deletion/movement, unchanged payload preservation, missing metadata failure and the explicit count meanings; changing those tests requires its own agreed specification.

Backlinks-specific assertions in `test_build_docs_payloads.py` and the dedicated `test_docs_backlinks_report_contract.py` target the retired output/report. Their cleanup requires separately specified test work; the removed production modules, fields and routes must not be restored to satisfy them. [Reports](Reports.md#current-reports) records the retired report-test boundary.

## Workspace And Owners

`docs-viewer/config/workspace/docs-workspace.json` owns:

- Working collection registration and one design-time default document shared by both readers
- the public section URL, public document and Search destinations, and retained R2 media addresses
- media registration, hierarchy policy, Search fields and the Recent limit

`docs_workspace_config.py` derives Working and Preview paths from the existing `DOTLINEFORM_DOCS_BASE_DIR` and selected collection. Temporary Preview builds use an explicit isolated Docs root. `build_docs.py` delegates focused work to `docs-viewer/build/docs_builder/`. `build_search.py` owns the separate whole-index Search projection. Neither owner should carry a hand-maintained scope list or select an implicit authoring stage.

## Docs Build Flow

1. read canonical membership and load the complete or selected configured source corpus
2. validate source identity/metadata and merge required saved navigation metadata for targeted ordinary work
3. run configured media producers into their configured build outputs
4. determine generated removals and refresh Working Links for selected changed/deleted documents and their affected neighbours
5. resolve supported media and semantic tokens, interpret Unicode-whitespace-only lines as blank outside fenced code and explicit `<pre>` blocks, then render Markdown and permitted raw HTML with Related links using the refreshed records
6. build the tree, Recent, per-document and browser-config projections
7. compare content versions, write changed payloads and remove stale owned payloads before returning success

The source Markdown is canonical. Generated JSON is a projection and can be rebuilt. Render-time blank-line hygiene does not rewrite source files; managed Source Save and Docs Import apply the same narrow rule when they write canonical Markdown.

Explicit media maintenance checks the ready files referenced by the supplied documents. No registered build-source producers remain. `--skip-media-builds` skips those ready-media checks for a document-only build; Source Save and exact Rebuild prepare only their supplied native files and otherwise reuse ready media. Diagrams are imported as ordinary SVG images.

## Reader Subject Metadata

Every ordinary and sub-scope `by-id/<doc_id>.json` payload and every document row in a sub-scope `manifest.json` contains `subject`. A valid Catalogue declaration becomes an exact `{kind, key}` object, such as `{"kind": "work", "key": "00635"}`. Supported kinds are `work`, `series` and `detail`; keys remain strings, including leading zeroes and the complete Detail UID. Missing, malformed, conflicting or Folder declarations produce `null`. `docs-viewer/services/docs_document_subjects.py` owns this compact reader projection through the existing authoring normalizer; it does not consult Catalogue data or infer identity.

The same projection serves local and public reader payloads without exposing Folder paths, raw source values or authoring diagnostics. `manage-manifest.json` retains its separate `authoring_subject` metadata for management controls and diagnostics. Document Build updates the reader Subject in both manifest and by-ID output, including clearing it after a declaration is removed. Preview and deployed site snapshots receive the field through their normal publication workflow.

Manifest rows do not repeat `sub_scope`: their configured report supplies exact collection context to list and detail consumers. Subject metadata supports subsequent icon rendering but does not add icons itself.

## Document Relationship Maintenance

Ordinary and collection Doc Build call `docs-viewer/build/docs_builder/links_builder.py` before rendering document output and await its completion. The same refreshed records supply related-links sections in that build. Determine generated document removals once before relationship maintenance and carry those IDs into the final output plan. Links maintenance is a fixed Working-stage responsibility, including its configured collections; Preview builds use captured Links records without refreshing relationships. There is no separate Links configuration or file-presence enablement gate. Source-write operations pass exact changed/deleted document IDs separately from the ordinary renderer's target set. A full collection render or an ordinary-renderer fallback does not expand an ordinary save's Links target set.

Resolve local document ownership through configured Working storage and exact `doc_id`, with `collection` only for a named owner. Collection viewer links identify their owner through the configured report host. Relationship identity is `{collection, doc_id}`, with an empty collection for ordinary documents. Readers derive navigation from that identity and their configured viewer route/report hosts. Stage/scope-bearing targets are invalid. Authored Markdown/HTML document links and supported Catalogue Work image/media tokens supply references. Work tokens name `{collection: "catalogue", doc_id: "<work_id>"}` directly; Gallery Media View tokens contribute no document relationship. A Catalogue document's token referencing its own Work is omitted from the graph.

`links_model.py` owns unique directed document relationships and endpoint summaries. `links_schema.py` validates and serializes separate `generated/documents/links-by-id/<doc_id>.json` records beneath the configured Working root, shared by parent and child documents. Version 4 contains only `schema_version`, `self`, `incoming` and `outgoing`. `self` and each entry directly in the incoming/outgoing arrays use the same flat `{collection, doc_id, title}` object. Explicit identity lets the same records stand alone in the aggregate without their filenames. Repeated links to the same document collapse to one relationship in each direction, regardless of label or destination fragment; occurrence details and stored counts are omitted. Counts of distinct incoming/outgoing documents can be derived from the list lengths. Earlier schemas are rejected; saved records require explicit migration rather than runtime compatibility reads. These records supply targeted related-links builds and the local workspace diagnostic aggregate; the per-document Links view and read endpoint are retired.

`related_links.py` renders from the updater's refreshed records. Working generation carries those records and required direct-neighbour effects into public preparation; Publish consumes finished document bytes without reading relationships or linked sources. Eligibility selects document bodies upstream while authored target summaries remain intact.

The Markdown block parser consumes related-links directives without treating heading text as links. Expansion reuses the icon renderer, emits portable query targets and marks generated anchors; the shared anchor collector omits those anchors from authored-link diagnostics. The completed relationship refresh is the input to section rendering, so the section does not depend on document rendering order. Search and publication distribution do not derive these sections.

The existing Links record is the refresh's only relationship prior state:

1. Read the current record if present, preserving its incoming and previous outgoing entries. A missing record is normal for a document that has never participated in a relationship.
2. Parse the current document's Markdown and extract outgoing document targets without checking destination existence or link validity, deduplicating by exact document identity. Removing one repeated link preserves the relationship while another remains; removing the last removes it.
3. Read each linked neighbour's relationship record, creating one only when this relationship first needs it. Titles come from loaded documents or existing records; new endpoints may read source metadata for a title, with authored text or the target ID used when metadata is unavailable. No generated destination read permits or suppresses a relationship. Replace the current document's incoming contribution there and copy the neighbour's summary into the new outgoing list. Preserve every other contributor.
4. When the current title or collection identity changes, update its outgoing summary in each known incoming neighbour.
5. Remove its incoming contribution from previously linked neighbours absent from the new list.
6. Create the current record only if outgoing relationships need it, then write the current details and outgoing list while preserving incoming entries; write only changed records. Retain existing records when both lists become empty. The Related links directive alone never creates a record.

Relationship maintenance updates known counterpart records without recursively expanding neighbours. Public preparation renders the exact affected documents whose relationship records changed. Link validity belongs to the independent Broken Links audit; explicit document deletion removes the record and its owned contributions.

Full Working maintenance loads ordinary/non-Catalogue sources and completes their relationships before rendering Related links. Known cross-collection source metadata and saved neighbour records remain in memory; each collection renders against those final records. Changed relationship records select exact dependencies outside the bulk set, including Catalogue documents whose incoming links changed. The shared filename follows the current document owner after a collection transfer. Builders compare complete resulting by-ID JSON and write only differences; that comparison does not skip rendering. Catalogue Regenerate owns its source-body changes and Work publication selections; complete Catalogue design maintenance remains separate.

Working relationship maintenance and Insert document link discovery do not apply publication eligibility or validate target readiness. Public preparation applies saved draft/subtree/host rules separately. Ordinary targeted operations reuse saved exclusion policy; explicit full builds read external policy changes. Authoring Subject fields stay outside Links summaries.

Per-document Links maintenance owns lazy creation at both ends of a resolved relationship. A document with no outgoing links can still need a record for incoming contributions. A document without a record or resolved outgoing links remains without a record. Complete builds and source operations use this same rule; none performs a separate population pass or passes creation identities. Source Save awaits the existing exact-document build after persistence, then the editor awaits fresh display. New records contain exact identity, title and the required relationship contributions. Existing records remain the relationship prior state and are not reset or replaced.

A missing record does not trigger discovery of incoming contributions across other documents. Those contributions are maintained when referring documents build. A complete Build applies the same per-document rule across its built documents, reconstructing relationships from their authored outgoing links. Record creation itself never reads a collection index or scans neighbouring source bodies. Empty historical records may be removed as an explicitly requested one-off cleanup; routine builds do not prune them.

Deletion uses the previous record to remove the document's contributions from known neighbours before removing its own record, including the final document in a child collection. Publication exclusions do not remove records or relationships from Working Links. Collection placement keeps the immutable ID: the destination builds first and transfers the exact prior Links record after the old source is removed. The former collection's deletion cannot remove the destination-owned record. The placement owner rewrites authored source links; Links updates counterpart identities, including self-links. Builder diagnostics report distinct outgoing relationships added or removed.

A Working workspace lock serializes relationship creation, refresh writes and removals. Success means ordinary output and required Links writes/removals have completed. Malformed records and actual operation/write failures propagate synchronously; a failure can leave ordinary output and some relationship writes completed. Targeted operations have no full-refresh fallback. Correct malformed source or records explicitly; a complete Build reconciles current authored relationships without populating unrelated empty records.

Complete Working Build applies this same refresh to the documents it builds and carries completed relationship records into rendering before recording completion. Every Build leaves the separately owned Links report snapshot alone; its explicit Refresh reads current saved relationship records. `docs-viewer/tests/python/test_docs_links_builder.py` and the write/lifecycle tests still target retired scope contracts and require separately specified migration before their results can establish current coverage. Ordinary and named-collection updates still read and compare required navigation/collection metadata, rewriting those files when changed. The filesystem watcher and suppression layer are retired. Targeted source reads do not establish total Save or viewer-refresh timing.

## Publish Preparation

Working generation finishes one existing ordinary/collection `by-id/` document for both local reads and selected publication, including Catalogue. Eligible ordinary/non-Catalogue documents retain `draft: false`; Catalogue omits the field. Portable document and `docs-media:` references are resolved by the active reader. Folder-link publishability is authoring-owned; generation and Publish neither scrub these links nor add Folder-specific validation.

Documents retain ordinary fenced code as code. Diagrams are externally rendered SVG images handled by the normal image sanitizer, storage and reference owners.

Working builds `public-index-tree.json` beside its complete `index-tree.json` and eligible collection `manifest.json` beside each complete `manage-manifest.json`. The same build supplies loaded metadata to one eligibility/list owner, without another Markdown or rendering pass. Saved public lists provide prior membership; management metadata owns hierarchy, Draft and reader fields. Generation evaluates membership using the current exclusion policy, compares it with the saved public lists and writes/queues only changed projections. Ordinary exclusions prune whole subtrees; collection manifests follow their host. Public navigation contains identity rather than generated transport URLs.

Source Save compares the already loaded document and prepared candidate in memory, carrying current references and exact owned removals into generation. Replacement Import compares its loaded target and candidate and carries removals through its existing generation operation. Other generation derives current references from its supplied source/fields, including the independent thumbnail assignment; it has no historical-media baseline. Current references supply eligible publication selections, with no extra media list in by-ID JSON. Queue persistence precedes selected Working unlink. `publication-media.json` is retired. [Publication Media](data_model/Publication_Media.md) explains the current handoff; [Media And Asset Handling](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals) owns lifecycle and manual cleanup.

`working/source/unpublishable.json` is the single exclusion-policy file. Index generation reads it once per operation and carries the set through ordinary/collection projection and any required dependent generation. Exact operations use the current file just as complete builds do; policy edits take effect at the next index generation. There is no policy copy in `index-tree.json` and no saved policy-change tracking. A collection build first derives current ordinary host eligibility from saved management metadata; changed hosts update their collection manifests through the same owner. Required loaded management/public metadata and the prior index text are carried forward. Draft/exclusion retains owned media and does not limit reference extraction. Search/Recent retain their existing explicit refresh owners and coverage; Publish consumes completed selections.

The agreed `working/docs-publish-pending.json` uses `docs_publish_pending_v1`: schema/completion-time header, current/deleted document maps and current/deleted shared owner/output maps. Immutable global document IDs select exact payloads; optional collection selects its configured owner and current documents carry complete `media` type/relative-identity lists. Either document family can also carry exact `removed_media` lists. Later completed document writes/withdrawals replace opposite selections while preserving and merging media removals. Newly completed ownership with ready bytes cancels the exact restored removals; no intermediate progress is stored.

Draft/unpublishable ordinary roots exclude descendants, and excluded collection hosts exclude their document collections. Catalogue has fixed intrinsic eligibility and separate Work/media ownership. Document/manifest withdrawal never deletes canonical Works or Work media. Collection-host Draft/Delete changes remain design-time-owned. The author ensures starred documents are publishable; Publish copies saved `working/source/selected.json` unchanged, without membership checks or filtering. Recent and Search likewise use their existing completed files when queued.

Publish trusts the supplied artifacts/effects: no sources, eligibility/dependency calculations, rendering, producers, content audits or directory/remote listings. Document/shared/media deletions require only retained identities. Media removals remain actionable without a current eligible document or Working bytes. Whole-document media cleanup and orphan cleanup remain manual. Eligible documents may retain authored links to excluded targets; Broken Links remains independent.

Publication input paths resolve only existing generated documents, public metadata and explicitly selected saved controls. Publish never initialises, projects or reconciles them. Missing required inputs fail at their owning read; correction and the appropriate generation/publication action remain manual.

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

Manage **Refresh Search and Recent** sends one empty-object `/docs/refresh-discovery` request to [the discovery owner](../../docs-viewer/services/docs_discovery_refresh.py). It selects eligible ordinary IDs and included collection metadata once, reads selected source content for Search, and reuses its parsed ordinary dates for Recent. Recent uses saved collection metadata and its own exact exclusions/limit. There is no document rendering, media production, relationship/Selected update, Index/document reload, browser-config projection or full-build receipt. The browser awaits persistence and refreshes only Search/Recent caches, distinguishing saved-output success followed by display-refresh failure. The broad `/docs/rebuild` action/endpoint is retired without an alias; exact document Rebuild remains.

Full Working Rebuild is the explicit maintenance command `python3 docs-viewer/build/rebuild_working.py --write`. It requires `--write`, has no dry-run mode and is reserved for global renderer/configuration or external publication-policy changes, persistent media edits, missing targeted prerequisites or reconciliation. [The complete Working owner](../../docs-viewer/services/docs_working_rebuild.py) loads workspace/rendering configuration, canonical ordinary membership, Selected and ordinary/non-Catalogue Markdown once. Catalogue is excluded from bulk source loading, validation, stale-output discovery, rendering and Work publication selection; normal Catalogue generation and Work queue contributions belong to Regenerate. The operation carries raw Markdown into referenced-ready-media checks, completes selected relationships, then invokes the existing builders with completed inputs and stale-output IDs. Shared icon artwork and exact Catalogue Work lookups remain operation-local. Targeted document CLI and application follow-through retain their own owners.

Explicit media maintenance checks that the selected references have ready files; no diagram/source producer runs. Source Save remains the processing owner for newly supplied native files. Canonical document membership supplies media references; unindexed ordinary Markdown does not supply additional media work. Selected metadata is refreshed once across built owners, preserving saved Catalogue rows. Search and Recents share one completed discovery selection, retaining configured coverage, inherited draft/unpublishable exclusion, eligible collection hosts and Recent's separate exact-target exclusions. Catalogue is currently excluded from both. If included by configuration, Recent consumes its saved management manifest and Search reads only its selected saved Markdown, without rendering or queueing Catalogue documents. The action does not Refresh Catalogue, Regenerate its sources or Publish.

The maintenance operation carries completed relationship records into rendering, projects browser configuration once and records completion last. Working `generated/build-manifest.json` remains a `docs_working_build_v1` operation receipt with only `schema_version`, `stage` and `completed_at`. Failure stops at its reported phase, retains completed effects and leaves completion invalidated; CLI exit status reports failure. It neither aggregates the Links report nor requires a displayed/default document. Reload the reader after CLI maintenance. Preview retains selected publication files/media without a whole-snapshot inventory; ordinary writes and exact Rebuild omit Search/Recent and registered media production.

Complete document builds carry writer-selected changed IDs into publication selection. Newly eligible documents and actual withdrawals remain required even when payload bytes match. Unchanged documents add no selection unless already pending or their referenced media differ from local Preview. That maintenance-only comparison reads exact confined referenced files in bounded chunks, without remote access, directory scans or a hash ledger; missing Working bytes fail, while a missing Preview counterpart selects the unit. A media-only change queues its referring document with all supplied media references. Existing pending selections survive; normal targeted Save/Rebuild retain their exact queue handoff without media-byte comparisons. Selected, Recent and Search queue only changed saved content, retaining stable discovery timestamps. Public index/manifests already use their projected content comparison. An unchanged maintenance run adds nothing to the queue; Publish retains its queue-only transfer contract.

Document Build owns authored relationship maintenance in configured Working `generated/documents/links-by-id/<doc_id>.json`; destination validity and readiness belong to authoring. Full Working Build refreshes its built documents and affected saved neighbours, retaining unrelated Catalogue records. Changed relationship filenames select exact dependencies outside the bulk build. A Catalogue dependency render prepares and queues only its public document through the Docs queue, with no Work JSON/media or Catalogue Work-queue contribution. It preserves Selected membership/metadata and avoids regenerating an unchanged Catalogue manifest for a body-only effect. Source Save and exact-document rebuilds use the same dependency owner. Explicit Catalogue design maintenance remains the complete Catalogue rebuild owner.

The separate local Links report is the sole consumer of its private aggregate at workspace-configured `working/generated/reports/links/report.json`. Opening reads that saved result; only its explicit Refresh aggregates current per-document records and saves the report. No Build, including the complete docs-and-Search action, refreshes it. Report storage is independent of document output, and there is no runtime fallback to the retired sibling `links.json` or Build-only prepared-record handoff. [Reports](Reports.md#current-reports) owns its v4 schema, aggregation order, local API, safeguards, browser lifecycle and evidence limits.

The existing files `test_docs_scope_links.py`, `test_docs_write_rebuild.py`, `test_build_search_python.py` and `test_docs_workflow_stages.py` under `docs-viewer/tests/python/` still target old contracts, including Build-owned report aggregation; they have not been migrated or run as evidence. Test migration requires its separately approved specification.

## Source Contract

The common front matter is `doc_id`, `title`, `parent_id`, `added_date`, `last_updated`, and optional `summary`. Ordinary and other named-collection sources additionally require `draft` as an explicit boolean in Working and captured preparation input. Catalogue sources reject that field and have fixed document eligibility; Catalogue creation, Regenerate, management metadata, list manifests and by-ID payloads omit it. Source loading, Search, preparation and Source Save validate the owning collection's readiness rule before using or writing the document. New ordinary and other collection documents, imported documents and collection report hosts start with `draft: true`. Eligible common by-ID payloads retain `draft: false`, while public navigation/manifests omit Draft metadata. An excluded ordinary collection host still excludes its collection, including Catalogue. Ordinary workspace documents additionally support free-text `ui_status`, without a fixed value enumeration; this includes the text `draft`, which has no publication effect. Named collection documents do not use that field: source formatting and collection-placement rewrites remove it, collection management manifests and by-ID metadata omit it, and the metadata endpoint omits it for collection targets. The reader's optional status artwork is a separate presentation mapping. `publishable` is retired and rejected. The ignore list is separate Working source policy data and is not copied into prepared content. Source validation is owned by the builder/source model.

- new documents give `added_date` and `last_updated` one captured full timestamp; after creation, only body, `title`, or `summary` changes advance `last_updated`. Summary comparison normalizes line endings and outer whitespace while retaining internal breaks; equivalent quoted/literal-block representations do not create a content change.
- edited Recent includes only full `last_updated` timestamps; legacy date-only values become eligible after the next qualifying edit.
- Ordinary ignore roots, draft state and inherited descendant exclusions select document bodies for Preview; they do not filter Working relationships, picker targets or captured related-list destinations.
- `draft: true` records temporary authoring readiness. An omitted destination's title/link remains visible without adding its body or a publication warning/gate.
- hierarchy comes from `parent_id`, not folders.
- whether nested Markdown is allowed comes from the configured stage and collection.
- sibling order is title-based with a stable id tie-breaker.

Authoring extensions supported by the renderer include:

- <code>&#91;&#91;media:...&#93;&#93;</code> for configured docs media
- <code>&#91;&#91;html-media:docs/html/...&#93;&#93;</code> for ordinary HTML media, with <code>docs/sub-scopes/&lt;id&gt;/html/...</code> for an exact child owner
- explicit Catalogue `media` and `image` tokens for Media View links and Catalogue images; the retired three-part Catalogue text form has no compatibility alias
- standalone `[[summary]]` blocks for the current document's front-matter Summary

Ordinary Markdown document links are the relationship input. Local document href rewriting preserves explicit child selection, fragments and HTML escaping; URLs with a hostname, including protocol-relative external URLs, retain their authored destination.

Use [Docs Images And Assets](Docs_Images_And_Assets.md) for authoring guidance and `docs-viewer/build/docs_builder/` for the exact token rules.

### Summary Block

In Source, choose **Directives → Summary** to insert the token with block spacing, or place `[[summary]]` on its own Markdown line, separated from surrounding prose by blank lines, wherever the current document's Summary should appear:

```md
---
summary: |-
  First supporting line.
  Second supporting line.

  Another paragraph.
---
# Document title

[[summary]]

Main document text…
```

This example shows only the relevant metadata; normal document identity, dates and readiness fields are still required. Summary accepts the existing single-line scalar syntax, double-quoted `\n` escapes, and space-indented YAML literal blocks using `|` or `|-`. `|` clips the value to one final newline; `|-` removes it. The shared `docs-viewer/services/docs_front_matter.py` owner retains the existing scalar field types and adds literal blocks only for Summary; this is not general YAML support. Folded blocks, other chomping/indentation modifiers and nested YAML are outside this grammar.

In Source, type two spaces at the start of each Summary content line; Tab is not needed. Leave blank paragraph lines empty and keep `summary:` and the next metadata field unindented. Use the same space indentation for every content line.

Summary normalization converts CRLF/CR to LF and trims outer whitespace, retaining internal text, newlines and blank lines. General source serialization writes multiline Summary using `|-`; targeted Source normalization leaves an already normalized authored representation intact. Source rewrites operate on complete field spans, so indented `#`, colons, field-looking lines and `---` inside a literal block remain text instead of becoming metadata or delimiters. Metadata changes and timestamp updates do not rewrite Summary content inadvertently.

The shared ordinary/collection payload builder supplies this string to `summary_directive.py` through the Markdown renderer. Each standalone occurrence becomes escaped paragraphs inside `.docsViewer__summary`; a newline within a paragraph becomes `<br>`, and blank-line runs separate paragraphs. The panel retains the quote style's theme-aware background, spacing and padding without its border. Markdown, HTML and tokens inside Summary are displayed literally. A missing or blank Summary produces no block. Inline occurrences, escaped tokens, fenced/indented code, comments and raw HTML retain normal literal behavior. No token options or automatic placement are supported. The Info panel displays the same paragraph/line-break meaning from its captured metadata string using safe text nodes.

Source retains the token and front matter. Working generation expands Summary and prepares the same public content upstream; readers need no runtime lookup. Static Export consumes expanded by-ID content. [Package Prepare](Package_Prepare.md) retains its separate flattened Summary policy. Search remains explicitly rebuilt, and ordinary Summary edits follow awaited Source Save without rebuilding Search.

The multiline extension on 2026-10-07 has focused Python/JavaScript lint, Python syntax/import diagnostics, shared runtime projection/site validation, Working docs-only reconciliation and bounded source-review evidence. The user accepted the delivery on 2026-10-07 after spaces-based authoring guidance. No behavior tests, browser checks, real package preparation/Import or Export actions were run by Codex, and detailed manual outcomes were not recorded; acceptance does not add behavioral evidence. Public document data awaits separately authorized Publish.

## Preview And Deployment Boundary

Working owns source, local output and finished public artifacts. Preview retains selected applied publication files and media, with no source tree, browser stage, complete-snapshot receipt or publication ledger. Local readers resolve Working; site-preview serves the repository output.

`docs_publish.py` reads the Docs and Catalogue queues once. Empty queues return before artifact/media setup. Otherwise Catalogue Works complete first, Docs document/media units next, and shared outputs after required item work. Each unit applies its selected bytes/removals to Preview and distributes those bytes to configured destinations before successful queue removal. No full inventory, source capture, generation or reconciliation runs.

Each eligible document supplies all referenced ready media, including its assigned thumbnail and imported SVG images. Each document unit also applies its exact queued media removals in Preview and at configured destinations before completion, including when the document itself is withdrawn/deleted. Shared files are processed independently under each queued document. Exact-object size/ETag comparisons skip matching R2 uploads; changed transfers and selected remote deletions are verified. Unselected bytes remain in place; orphan cleanup and whole-document media cleanup remain manual. R2 removals occur during Publish, with the accepted interval before a later manual Pages deployment. [Media And Asset Handling](Media_And_Asset_Handling.md#link-resolution-and-delivery) owns storage and transfer configuration.

Public index/manifests and author-owned Selected are maintained upstream from known effects and saved metadata. Manage Refresh Search and Recent and full Working maintenance generate discovery with existing coverage, eligibility, Recent exclusions and limit. Save, exact Rebuild, Move, Delete and eligibility changes preserve saved discovery output. Explicit Search builds and Recent completion queue only changed saved files, preserving the `docs_viewer_search_index_v4` format. Publish performs no freshness or membership checks and leaves unqueued discovery files untouched.

Manage exposes one awaited Publish action with phase/target error reporting and completed-unit/effect evidence. Publish does not write Working Recent or refresh browser Recent/capabilities. Failure stops immediately; successful effects/removals remain, failed/unprocessed selections remain queued, and diagnosis/correction are manual. There are no progress flags, guaranteed retry, rollback or authoring lock. Git commit/push and public deployment remain explicit actions. [Catalogue Deployment](Catalogue_Deployment.md) owns Catalogue item/shared selections.

[Generated Data Contracts](Generated_Data_Contracts.md) owns reader payloads. Focused lint, syntax/import diagnostics and source review establish only static integration evidence; the queue-only workflow, failures and real remote transfers still require manual acceptance. Historical lifecycle tests remain unreviewed for this contract.

## Diagnostics And Safety

- the builder prints a compact human summary; `--diagnostics` adds machine-readable console diagnostics
- document token-resolution and Markdown-rendering validation errors identify the document ID, title, ordinary/collection owner and source Markdown filename alongside the underlying cause. This applies to full and targeted builds; the build stops at the first failure, and the rebuild service retains that detail in its error response
- unchanged content is skipped unless forced
- targeted writes require an existing full-scope output tree
- renderer output allows raw HTML and is not a sanitization boundary
- management/service writes validate source and paths before calling builders
- application writes await required local generation and publication handoff; CLI exit 3 reports completed local generation with incomplete public preparation/queue persistence. Correction uses explicit Rebuild. Search and Recent retain explicit build owners.

## Change Guide

- workspace/source/output change: `docs-workspace.json` and `docs_workspace_config.py`
- Markdown/front-matter parsing: builder source model
- rendered document behaviour: renderer/token modules and acceptance fixtures
- search fields: `build_search.py` and Docs Viewer search runtime
- public preparation and selected publication: `docs_publication_preparation.py`, `docs_publication_queue.py`, `docs_selected_publication.py`, `docs_catalogue_publication.py` and workspace configuration
- external-edit and media regeneration workflow: [Source Organisation](Source_Organisation.md#explicit-external-edit-and-media-rebuilds)
- new media processing: agree its authoritative producer, explicit configuration, storage and reference contract before introducing it; Docs Viewer currently accepts finished media without a build-source registry

Keep exhaustive output filenames, diagnostics fields, and CLI flags in code. This page should change when the build boundary changes.
