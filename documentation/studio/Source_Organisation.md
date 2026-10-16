---
draft: false
doc_id: d-20260423-000000-8fd731
title: Source Organisation
added_date: "2026-04-23 00:00:00"
last_updated: "2026-10-16"
summary: Working source and generated storage, one read-only Preview snapshot, and exact collection and media ownership.
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Source Organisation

`docs-viewer/config/workspace/docs-workspace.json` is the storage authority, using `docs_workspace_v8`. The loader resolves the existing root selected by `DOTLINEFORM_DOCS_BASE_DIR` without inferred or fallback storage. Document and Work media resolve beneath configured Working and Preview asset roots.

`DOTLINEFORM_DOCS_BASE_DIR` selects the Docs Viewer folder directly. It is independent of `DOTLINEFORM_PROJECTS_BASE_DIR`, which owns Catalogue, Processing, Data Sharing and other project workspaces. Both settings live in `.env.local`; neither is an alias or fallback for the other. To relocate Docs storage, stop services, move the complete Working and Preview trees to the explicitly selected root, change the setting, verify the resolved locations, and restart.

## Storage And Roles

```text
$DOTLINEFORM_DOCS_BASE_DIR/
  working/
    catalogue-updates-pending.json
    catalogue-publish-pending.json
    assets/works/{primary,thumbs,media/files}/
    assets/media/workspace/{img,thumbs,svg,files,html}/
    assets/media/collections/<collection>/{img,thumbs,svg,files,html}/
    source/
      index-order.json
      recent-exclusions.json
      selected.json
      unpublishable.json
      documents/<doc_id>.md
      collections/<collection>/
        documents/<doc_id>.md
    generated/
      documents/{index-tree.json,public-index-tree.json,publication-media.json,recent.json,by-id/,...}
      search/index.json
      collections/<collection>/documents/
      catalogue/
  preview/
    assets/works/{primary,thumbs,media/files}/
    assets/media/workspace/{img,thumbs,svg,files,html}/
    assets/media/collections/<collection>/{img,thumbs,svg,files,html}/
    documents/{index-tree.json,recent.json,by-id/,...}
    search/index.json
    collections/<collection>/documents/
    catalogue/
```

| Role | Ownership |
| --- | --- |
| Working Source | Canonical Markdown, ordinary hierarchy/order, selected membership, media provenance and registered producer input. |
| Working Generated | Replaceable document, Search and Catalogue JSON used by the local reader. |
| Private Catalogue queues | Persisted Working selections/readiness and completed publication progress, with owner-specific timestamps; ordinary document builds do not replace or reset them. |
| Working document assets | Current ordinary/collection media for local readers, intake, builds, inventory and package/export inputs. |
| Preview document assets | Prepared selected document media used for publication distribution, retained between operations. |
| Working Work assets | Refresh-owned prepared media used by local Docs readers. |
| Preview Work assets | Per-Work Publish output retained between operations. |
| Preview | Selected prepared public artifacts and media retained by Publish, independently inspectable on disk. |
| Public projection | Downstream repository/R2 output served by the website. |
| Rendered view | Presentation of document payloads and media; it is not source. |

Working registers document, collection and media owners once. Generation maintains one common by-ID document plus complete management and eligible public metadata under each existing generated owner, and records exact publication effects in `working/docs-publish-pending.json`. Ordinary `public-index-tree.json` sits beside `index-tree.json`; collection `manifest.json` sits beside `manage-manifest.json`. Private `publication-media.json` retains referenced-media/diagram records and the applied exclusion-policy input. The separate Working publication tree is retired. Preview receives selected finished bytes without a source/generated tree or browser route. Catalogue queues remain alongside the Docs queue under `working/`; [Builder](Builder.md#publish-preparation) and [Catalogue Deployment](Catalogue_Deployment.md) own handoffs.

Collection document-media paths in the tree above apply only to collections declaring `document_media: true`: Context (`works`), Concepts and Moments. Catalogue declares false, so it has documents and separate Work media but no `assets/media/collections/catalogue/` owner, source-media producer or document-media publication binding. Existing empty remnants of that former namespace are not read, maintained or recreated by these owners.

Both private Catalogue queue schemas are version 5 and place their header first. Updates retain the last successful Refresh time, shared pending state and per-Work readiness. Publication retains the last completed nonempty Catalogue Work queue time and exact pending selections, without Preview progress flags. The Docs queue uses `docs_publish_pending_v1`. These files are private workflow state, independent of generated-output replacement and public projection; missing or malformed queues stop their owning operation. Projects-owned `catalogue/media-staging/` remains outside the Docs root, with its current family layout mapped in [Media And Asset Handling](Media_And_Asset_Handling.md#workspace-configuration-and-storage).

Durable Studio development documentation is maintained in repository `documentation/studio/`, independently of these external document collections. The native App and Processing projects retain their own build and release boundaries.

### Source Controls

The four source-control JSON files live directly in `working/source/`; `documents/` contains ordinary Markdown bodies. They remain canonical editable state, with the same schemas and ownership, rather than replaceable generated indexes or private report caches.

| File | Owns |
| --- | --- |
| `index-order.json` | Ordinary hierarchy and literal sibling order. |
| `recent-exclusions.json` | Exact ordinary/collection targets excluded only from Recents. |
| `selected.json` | Star membership across owners, with Build-maintained reader metadata. |
| `unpublishable.json` | Ordinary roots excluded from publication with their descendants. |

`source_control_path` resolves fixed owned filenames from the configured source container and rejects symlink traversal. It does not load configuration or inspect document contents. `index_order_path` supplies one exact path to `read_index_order`; create/position/delete operations carry that resolved path into persistence. Import plans carry the hierarchy path for ordinary creation and include it in their changed-file/rollback inventory instead of inferring it from the Markdown parent. Unpublishable resolves its policy and the Markdown directory independently from one loaded Working configuration. Authoring, inspection, package preparation and builders all use these owners, with no old-location alias, fallback or automatic migration.

Source controls remain private. Generation uses hierarchy and policy to prepare public navigation and eligible Selected output; Publish transfers their queued files without reading the controls. Existing Preview/public reader paths remain, including `preview/documents/selected.json` and `site/assets/data/docs/selected.json`.

On 2026-10-14, the approved one-time filesystem rename moved all four existing files without changing their contents. Focused lint and compilation passed for all 21 affected Python owners, including review fixes, and existing Working/Preview builder help imports completed. Production readers found 34 hierarchy documents, six Recent exclusions, two selections and 14 Unpublishable IDs at the new paths. Source inspection selected the same 34 Markdown paths; Unpublishable resolved all 14 listed source titles through the independent documents directory. A targeted ordinary `build_docs.py --stage working --only-doc-ids d-20260426-164043-e14f49 --skip-media-builds` invocation, without `--write`, completed as a dry-run with zero proposed document/index writes, zero removals and zero warnings. This exercises the relocated hierarchy/selection/eligibility reads and ordinary builder wiring. The real configured dotlineform Markdown and hierarchy paths also passed the write-boundary function directly, without invoking a write. Create/Import/preparation owners imported through the application's `ensure_studio_python_paths` bootstrap; bare service-only import attempts lacked the existing shared logging/Catalogue import paths and required that normal bootstrap, not a production fix. No authoring mutation, Import, full Build, Publish capture/render/distribution or VS Code opening was executed. Those paths receive bounded source review and remain manual acceptance gates. Tests/fixtures targeting the former paths are unchanged and unrun, and require separately approved migration rather than compatibility support. [Source Control Relocation](deliveries/Source_Control_Relocation.md) tracks review and closeout.

The 2026-10-14 Redundancy And Defensive Behavior Review traced production hierarchy readers, New/Position/Delete persistence, Import plan/rollback inventory, local reports/openers, normal/atomic write follow-through and the then-current isolated Preview layout. It caught Create/Import boundaries that allowed only the Markdown directory: their plans/owners now supply the exact confined hierarchy file as the sole additional allowed path, without permitting writes throughout `source/`. The shared source-control resolver performs no content/configuration loading, and consumers carry checked paths into writes instead of inferring siblings or repeating confinement. Retained safeguards include configured-path/symlink confinement, JSON parsing and hierarchy/editor-policy rules at their owners; Import retains its operation-specific snapshot/rollback boundary. The one-time migration's source/destination checks prevent overwriting a destination and are not a runtime preflight/recovery workflow. Publication ownership subsequently moved upstream through Incremental Document Publish; the current selected workflow below supersedes that review's Preview/policy call path.

## Document And Collection Identity

A document retains its immutable `doc_id` across representations. Local API targets use `{doc_id}` for an ordinary document and `{collection, doc_id}` for a configured collection document. Collection targets are `{}` or `{collection}`. The service resolves Working; stage is not a target field. Collection, tree placement, Catalogue subject and media identity remain independent. Source filenames, titles, selected rows and ambiguous associations cannot substitute for exact identity.

Configured storage supplies collection membership. Source front matter uses `collection` with the exact configured collection ID; ordinary documents have no named membership. New, Import and metadata writers use the resolved owner, and reject retired `sub-scope` spellings. A metadata edit alone does not move a source file or change its owner.

Authored Markdown is flat beneath each owner's `documents/`. Ordinary hierarchy and sibling order come from `working/source/index-order.json`: a nested array of records containing `doc_id` and an optional `children` array. Omitted `children` means a leaf; persisted branches carry only nonempty child arrays. Nesting supplies the parent and literal array position supplies order. Ordinary Markdown no longer authors `parent_id`; runtime parent lookups are derived from this tree. Build joins the exact IDs with source metadata and writes `index-tree.json` in the same order. Named collection documents remain flat and retain their own sorting.

Hierarchy traversal reads omitted children as an empty sequence without enriching the loaded records. New and Import create leaves with only `doc_id`; inserting Inside a leaf creates its child array. The shared `index_order_text` serializer omits empty children recursively without changing its input, so Position and Delete use the same persisted format, including when a move removes a parent's final child. This is a source-format change; browser placement choices and generated reader payloads keep their existing owners. Formatting alone needs no document or Search rebuild. Restart the local service after updating the Python readers before continuing authoring.

On 2026-10-14, the configured Working hierarchy was rewritten through that serializer, removing 33 empty child arrays while retaining all 34 documents, including 13 nested documents, in their existing order and nesting. Focused lint and Python compilation passed for the four changed modules. The existing targeted `build_docs.py --stage working --only-doc-ids d-20260426-164043-e14f49 --skip-media-builds` dry run consumed the sparse tree with zero warnings and zero planned document/index changes. Tests, fixtures, harnesses and profiles were unchanged and unrun; live New, Import, Position, Delete and Publish were not exercised.

The distinct Redundancy And Defensive Behavior Review traced hierarchy lookups, subtree deletion, leaf insertion, moving the final child, exclusion of the final child and all shared serializer callers. Optional-child handling stays in traversal; canonical omission happens at serialization without a read-time normalization pass, file reread, extra filesystem scan, compatibility alias or repair workflow. Serialization makes an ordered in-memory projection and leaves the caller's tree intact. Existing JSON parsing, duplicate-ID detection, placement/cycle rules and configured path/authoring safeguards remain with their current owners. No actionable findings remained; interactive authoring and publication remain manual evidence limits.

Each collection has an exact ordinary report host. Positioning that host retains its immutable association; it does not choose a different collection or turn collection rows into tree children. A delivery registers the owner once in Working and explicitly places its host in the ordinary tree. Preparation later includes its eligible output in Preview.

Concepts and Moments are document collections rather than separate Concept/Moment entities. Works owns Subject specialisation through private `authoring_subject` metadata containing only `kind` and `key`. Assigned kinds are `folder`, `work`, and `series`; an unassigned Subject is `{kind: "none", key: ""}`. The source field is derived from the kind. Its private manifest keeps a collection-level `customisation` descriptor for local browser behavior; each document's Subject data is carried entirely by `authoring_subject`. Missing-target styling is computed from the current Catalogue title lookup. Reader manifests and individual document JSON omit `subject`. Ordinary documents retain their authored fields through common preparation, while collection customisations project their own authoring fields into reader data. Catalogue has its own canonical Work identity and regeneration owner.

The Position button beside Index Actions uses `arrow-up-down.svg`. Its synchronous modal moves the displayed ordinary document and its whole subtree Before, After or Inside a chosen ordinary destination. Inside appends the last child; Inside Root appends a root. All ordinary documents are available regardless of draft/unpublishable state, except the moved subtree. Save writes the JSON and refreshes the tree; Cancel writes nothing. Drag positioning is retired.

New inserts after the displayed ordinary document as its sibling. With no ordinary anchor it appends at root. New child and New sibling retain their explicit destinations. Import appends new documents inside the selected parent and preserves existing placement on overwrite; batch creation writes parents before their children while retaining sibling sequence. Delete removes the complete subtree from JSON and source. Renaming or editing content does not reposition documents. Hand edits to the JSON take effect on the next explicit Build.

## Collection Icons

Each registered collection requires an extensionless `icon` filename stem in `docs-viewer/config/workspace/docs-workspace.json`. The shared `docs_icon_assets.py` lookup validates the name and confines it to an existing, non-symlink SVG in `docs-viewer/static/icons/`; manual [Icon Tokens](Icon_Tokens.md) use the same filename boundary. There is no fallback artwork or separate collection-icon registry.

| Collection | Display title | `icon` |
| --- | --- | --- |
| `works` | Context | `dlf-context` |
| `concepts` | Concepts | `dlf-concept` |
| `moments` | Moments | `dlf-moment` |
| `catalogue` | Catalogue | `dlf-catalogue` |

The browser configuration projects `icon` and `report_host_doc_id` for every collection in both local and public readers. The Index panel matches the exact report host to its configured collection and renders that SVG using the existing list-icon mask, size and colour. It needs no document, collection-manifest or relationship read to select artwork. Report host IDs must be unique in the browser mapping; missing configuration fails visibly. Collection ownership and Subject artwork remain separate.

The builder's `write_browser_config` owner regenerates local/public reader settings from the checked workspace configuration. Icon/config changes require those settings to be regenerated and public artwork to be registered in `site-tools/config/site-code-update.json` and projected with `bin/site-code-update`. They do not require document or Search rebuilds. The proposed [Related Links](Related_Links.md) builder can later read the same collection `icon` and use the inline-icon renderer; ordinary related-link targets use the selected `dlf-doc` artwork. That directive is not implemented by this slice.

## Collection Deliveries

Collections can own specialised subject data, media producers, customisations, canonical records and public projections as well as documents. Creation, registration changes and whole-collection retirement are development deliveries under [Development Workflow](Development_Workflow.md), with a defined owner and outcome. Docs Viewer has no generic New Collection or Delete Collection action, capability, service endpoint or lifecycle creation receipt. `report_host_doc_id` remains mandatory configuration authority.

For each delivery, identify the collection ID and host, source/generated/media locations, producers and readers, document and subject associations, selected-document membership, Search inclusion, browser/report registration and public destinations. Creation defines and validates the required configuration and source, builds the owning outputs when needed, and updates the relevant browser projections. Retirement explicitly removes or preserves each owned resource and reference, including host tree placement, private publication metadata, pending selections, generated payloads, selected-document entries and deployed artifacts. There is no Preview completion receipt. Shared assets and other projects retain their own owners. Publish and Git/public deployment remain separately authorised operations.

Document-level New, Edit and Delete operate within an existing configured collection. Collection browsing, Regenerate and package workflows retain their own owners. Removing a document or report host does not deregister the collection or perform a whole-collection cleanup.

## Authoring And Publish

### Explicit External Edit And Media Rebuilds

The filesystem watcher is retired. Application writes await their required document/Links output. For a deliberate external Markdown edit, supply the intended full `last_updated` timestamp for a qualifying body, Title or Summary change, then open the exact document and choose **Edit doc → Rebuild**, reloading if needed. Rebuild does not rewrite source or capture filesystem edit time; [Document Identity](Document_Identity.md#date-provenance) owns timestamp evidence. A CLI author can run `python3 docs-viewer/build/build_docs.py --stage working --write --only-doc-ids <ids> --skip-media-builds`; add `--collection <id>` for a configured named collection. Use a complete document Build only when global changes or missing targeted prerequisites require reconciliation. Search remains separately requested.

External document edits require the exact generation command above. An intentional complete docs/Search reconciliation uses `python3 docs-viewer/build/rebuild_working.py --write`, carrying loaded sources through ready-media checks, document relationships, rendering, Selected and shared Search/Recent discovery. Exact Catalogue dependencies use the Docs queue; Catalogue Regenerate retains Work generation/publication ownership. This command performs no Mermaid or other registered diagram production. Publish remains separate; reload the reader after maintenance.

Normal Source Save processes only supplied pending media, and exact-document Rebuild reuses ready files. Neither scans media directories or invokes a diagram producer. Diagrams are rendered externally and imported as ordinary SVG. [Document Diagrams](Document_Diagrams.md) owns that workflow and [Media And Asset Handling](Media_And_Asset_Handling.md) owns storage.

### Recent Exclusions

`working/source/recent-exclusions.json` controls every Recent-specific exclusion. It is an editable JSON array of exact targets: ordinary pages use `{ "doc_id": "d-20260426-164043-e14f49" }`; collection documents also name their owner, for example `{ "collection": "works", "doc_id": "d-20260801-212422-df11f3" }`. Use exact configured collection IDs, omit `collection` for ordinary pages, and use `[]` for no exclusions. Duplicate targets collapse into one exact exclusion. Extra fields, invalid identities, missing files and invalid JSON fail visibly. The list may retain valid targets for documents that no longer exist.

Exclusions affect only the named document's Recent membership; descendants, Search, navigation and publication eligibility retain their existing rules. Collection hosts have no automatic exclusion. The initial list contains dotlineform and the Context, Concepts, Moments and Catalogue landing pages. Local Recent exposes **Open Recent exclusions in VS Code**, using an empty-body `/docs/open-recent-exclusions` action that opens only this configured file, including malformed JSON for repair. The file and control are local-only.

Save the file, then choose Manage **Refresh Search and Recent** to apply the exclusions; full Working maintenance also updates Recent. Only changed content joins the queue. Publish transfers queued bytes without Recent generation. Ordinary document operations preserve saved Recent. [Generated Data Contracts](Generated_Data_Contracts.md#recent-contract) owns its row fields.

### Selected Documents

`working/source/selected.json` owns star membership for ordinary documents and collection sub-documents. Its `docs_selected_v1` payload contains `docs` rows with exact `doc_id`, `title` and date-only `last_updated`; collection rows also carry their configured `collection` and `report_doc_id`. An assigned authored document thumbnail adds `has_thumbnail: true`. Otherwise a Context document with a Work subject adds the exact five-digit scalar `subject`; Folder subjects are omitted, and the two thumbnail fields are mutually exclusive in both Working and prepared rows. Catalogue thumbnails derive from their five-digit document IDs and carry neither field. Missing or malformed selection data fails visibly. Membership is the flag; there is no second editable front-matter value. The Working Actions menu's Star/Remove star item uses an outline when unset, a filled yellow star when set and an explicit menu checkbox state. It writes through `/docs/set-selected` without changing document Markdown or its modification date.

This JSON lives at the workspace source root with the other source controls: its membership is editable source state that cannot be reconstructed from Markdown. Build maintains the row metadata in that same file; it is not a discardable report cache or generated index. The local report reads it directly, so there is no separate Selected JSON under `working/generated/documents/` or the private generated reports directory. Preview contains only the prepared publication copy described below. The source-control relocation changes its canonical path without changing membership, metadata or Build/Publish ownership.

Star writes and ordinary or targeted collection builds refresh title/date/thumbnail metadata from source for the selected documents they handle. Delete removes all selected targets actually deleted, including ordinary descendants; collection-document delete recovery restores the selection alongside the source. A whole-collection retirement delivery handles that collection's selected-document entries explicitly. The list is independent of Search/Recents inclusion policy.

The shared `selected_documents` report on dotlineform (`d-20260426-164043-e14f49`) reads the current list when opened and displays linked titles ordered by `last_updated DESC`, then collection and immutable document ID for ties. Its pure data owner prepares the exact navigation URL, thumbnail choice and identity lookup once per loaded row without another saved-row audit. Initial preparation sorts once. A committed title/thumbnail change updates only its known row and cached thumbnail; only a changed date reorders the list. Deletion removes the row while preserving the remaining order, and irrelevant or unchanged non-thumbnail metadata produces no work. Authored thumbnail assignments retain the existing reload nonce on a committed update. Membership additions retain the existing normal-reload behavior; no new event or freshness mechanism is introduced.

The report reuses the collection report's decorative lazy-loaded 64×64px thumbnail, 6px corners, title spacing and row padding. Authored thumbnails resolve through the configured media root using `workspace/thumbs/` for ordinary documents and `collections/<collection>/thumbs/` for named collections; Context Work alternatives and Catalogue rows use the configured Work-thumbnail policy and route base. Only an actual Work-thumbnail choice requests that policy, once for the retained view, including a later committed change that first needs it. Authored-only, no-choice and empty lists make no policy request. A small pending set carries rows awaiting that single read; committed replacement/deletion removes obsolete entries before completion, without request versions or repeated whole-list URL preparation. Navigation and completed thumbnail URLs are reused on render and Back. The report reads no document bodies or per-Work JSON and does not probe image availability. When any row has a thumbnail choice, every row reserves the same slot; a failed image stays hidden within that slot. With no choices, titles remain compact. Local links use `/docs/` with exact document and optional collection identity; public links use the public reader route. Working reads all selections, including draft/unpublishable documents.

The retained view registers disposal before loading. Disposal releases prepared rows, identity lookup, pending thumbnail references and policy state, and ignores late load/policy success or failure. Detached retained views remain valid; DOM connection is not their lifetime authority. The document controller already owns subscription cleanup, so the report does not add a second unsubscribe owner. Local and public readers show no loading message for Selected Documents; empty and failure states remain explicit. Initial HTTP/JSON/policy failures remain visible through the report loader; failure of a later first-needed policy read uses the same report status presentation. There is no fallback thumbnail, automatic policy retry, persistent cache or background refresh. Authored URLs retain the configured media-root requirement and request-URL handling; Work thumbnails retain the existing media target/policy safety owner. The Work-subject predicate classifies thumbnail alternatives and excludes Folder subjects; it is not another authoring audit. Literal titles use `textContent`.

Star/Unstar and generation/eligibility/deletion follow-through prepare and queue an eligible public Selected file while retaining excluded Working selections. Publish transfers those bytes through `preview/documents/selected.json` to `site/assets/data/docs/selected.json` without rereading sources or membership. Runtime/report configuration remains design-time-owned and projected separately through `bin/site-code-update`.

The report's bounded cost is one saved JSON fetch and initial sort, one exact URL per row, and at most one media-policy fetch if a Work thumbnail needs it. A known committed effect uses an indexed identity lookup, changes one row and its affected thumbnail only, and sorts only on a changed date; deletion filters once. Rendering still builds the small list and derives shared thumbnail-slot presence from cached URLs. Required HTTP/JSON parsing, exact reader-route identity and thumbnail media safety remain with their existing boundary owners. Source membership, Build/Publish projection, eligibility and storage receive no new validation, scans or writes. [Selected Documents Optimisation](deliveries/Selected_Documents_Optimisation.md) tracks implementation evidence and manual acceptance.

On 2026-10-14, focused `bin/lint-js` passed for `selected-documents-report.js` and `docs-selected-documents.js`. One read-only invocation loaded actual Working rows through `read_selected` and the current public `selected.json`, then called `prepareSelectedDocuments` with the production `buildViewerUrl` owner and each configured reader base. Both prepared two indexed rows with two Work-thumbnail choices in `10,000`, `3 symbols` order, resolving exact `/docs/` and `/analysis/` links respectively. This exercised real-row identity preparation, initial date/identity sorting and route construction, with no synthetic inputs, assertions, test scripts or writes. It did not execute committed changes, DOM rendering, policy requests, image loads, empty/error cases or disposal. The earlier local GET returned HTTP 200 with the same two selections, and Working/Preview/public files were all present; the reported disappearance was a source-location misunderstanding.

Distinct code review covered the normal/empty/unchanged/title/date/deletion paths, authored/Work/no-choice alternatives, queued assignment replacement/deletion, first-needed policy failure, immediate/late disposal and reused request/thumbnail/controller helpers. Review confirmed that configured media values are consumed directly, route preparation has no second `URL` wrapper, title-only changes retain thumbnail URLs, pending completion consumes only current queued rows, failed initial mounts release their data and late success/failure cannot update a disposed report. Existing HTTP/JSON, exact target and media safety remain necessary boundary checks; source-domain validity stays upstream, with no new row audit, retry or fallback. No actionable findings remained. Public projection changed exactly the two mirrored runtime files; projection check and site validation passed. Tests, fixtures, harnesses and profiles remain unchanged and unrun. Manual acceptance remains for local/public report interaction, thumbnail policy/image loading, committed effects, retained Back/disposal and unavailable data; no browser automation or live authoring/Build/Publish was run. These are focused diagnostics and static review, not measured performance or end-to-end coverage.

### Operations

| Operation | Docs Viewer Manage | Site-preview / public site |
| --- | --- | --- |
| Browse documents, media and Search | Working generated output and assets | Repository/public output and configured public media |
| Create, edit, Delete, placement and Import | Authoring operations | Unavailable |
| Publish | One awaited selected Preview/distribution operation | Unavailable |
| Collection reports | Configured Working owner | Published read-only output |

Ordinary and other collection source documents require explicit boolean `draft`. Catalogue source rejects that field, its generated document metadata omit it and every Catalogue document has fixed intrinsic eligibility. Upstream generation excludes draft roots and descendants, roots in ordinary `working/source/unpublishable.json` and their descendants, and collections whose report host is excluded, including Catalogue. An intentionally empty ignore file contains `[]`; missing or invalid policy fails at its owning read. Saved private hierarchy/readiness metadata selects exact document/manifest writes and removals before Publish. Public navigation retains surviving branches in order without promoting excluded children; Working retains the complete tree. Catalogue host exclusion concerns document/manifest effects only and does not withdraw Catalogue JSON or Work media.

`POST /docs/publish` accepts an empty object. It consumes completed Docs/Catalogue selections, applies exact files/removals to Preview and configured destinations, and clears only successful units. Empty queues cause no publication work. No source capture, rendering, eligibility discovery, full snapshot, remote listing or corpus reconciliation runs. Failures retain completed effects and report phase/target; correction is manual.

Ordinary Working edits and deletions reach Preview and the repository through the next Publish. Source Save awaits validated persistence, exact document/Links generation and fresh display. Draft changes await their exact build; creation, deletion, imports and Regenerate retain their own generation owners. Ordinary writes preserve Search and Recent. Manage **Refresh Search and Recent** updates discovery explicitly without document/media generation; complete Rebuild is maintenance CLI work. Links and Broken Links remain Working-owned.

Local generated reads resolve the configured Working owner without a stage parameter. Ordinary document reads open the exact generated by-ID file without reading the document index or validating its stored URL. Exact immutable identity, configured ownership, path confinement and payload parsing remain required. Stage-bearing URLs/requests and `/docs/preview/*` browsing are retired without aliases. Management capabilities remain distinct from public read-only access.

Working and Preview remain internal storage/publication roles. The browser awaits the synchronous Publish result. Carry resolved queues/configuration and verified selected bytes through completion without freshness checks or repeated scans. Retain configured path authority, required input reads and completed write/transfer verification.

Distribution uses each selected unit's completed Preview files, without reading sources, rendering or filtering membership. Success means its repository and configured media effects completed and its queue removal persisted. Failure reports the owning phase and incomplete publication; completed Preview/destination effects remain inspectable. Repository and R2 writes are not one atomic transaction. Diagnosis, correction and whether another Publish is appropriate remain manual. Review the result through `bin/site-preview`. Git commit/push and the manual GitHub Pages workflow remain separate explicit actions. Public reader payloads carry no publishing-stage discriminator. [Builder](Builder.md) owns producer and distribution details.

## Media Ownership

Ready document media lives under `working/assets/media/` and `preview/assets/media/`, using `workspace/<type>/` and `collections/<id>/<type>/`. Local readers, intake, generation, inventory and export use Working. Exact configured owners keep same-named assets independent. Editable diagram sources belong to their external project/tool. The former workspace-level `assets/media/` root has no fallback owner.

Local media uses `/docs/assets/<configured-family>/<identity>`, resolved to Working. Authored tokens, `docs-media:` identities, public URLs and R2 namespaces remain unchanged. Generation records exact references in one `publication-media.json` list per document and supplies eligible queue selections. Publish copies only that selection into Preview and verifies selected transfers; Preview has no source/generated tree.

Logical identity, storage provider and served URL are separate. Location helpers confine paths/keys and own reads, writes and byte verification. A reference does not establish ownership of its bytes; Catalogue media and retained external originals have separate owners.

Publish processes each document's supplied ready-media references independently, including repeated shared files. It copies selected Working bytes into Preview, compares exact remote size/ETag, and verifies changed transfers. It leaves unselected media in place and performs no media deletion, inventory or orphan cleanup. Required missing bytes stop the selected unit; completed effects remain, with no snapshot receipt or automatic recovery.

Manual review covers the principal Manage readers/actions and successful Publish feedback. Works editor, package operations, saved-state conversion, failure recovery and independent R2 verification have not been exercised as part of this workflow change; no measured speedup is claimed. Historical scope and publication tests remain unchanged and are not current integration evidence.
