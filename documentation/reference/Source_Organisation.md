---
draft: false
doc_id: d-20260423-000000-8fd731
title: Source Organisation
added_date: "2026-04-23 00:00:00"
last_updated: "2026-11-18"
summary: Working source and generated storage, one read-only Preview snapshot, and exact collection and media ownership.
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Source Organisation

`docs-viewer/config/workspace/docs-workspace.json` is the storage authority, using `docs_workspace_v10`. The loader resolves the existing root selected by `DOTLINEFORM_DOCS_BASE_DIR` without inferred or fallback storage. Document and Work media resolve beneath configured Working and Preview asset roots.

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
      documents/{index-tree.json,public-index-tree.json,recent.json,by-id/,...}
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

Working registers document, collection and media owners once. Generation maintains one common by-ID document plus complete management and eligible public metadata under each existing generated owner, and records exact publication effects in `working/docs-publish-pending.json`. Ordinary `public-index-tree.json` sits beside `index-tree.json`; collection `manifest.json` sits beside `manage-manifest.json`. Index generation reads the single `working/source/unpublishable.json` policy once per operation, without storing a policy copy in generated indexes. Media references and authoring comparisons stay in memory; `publication-media.json` and the separate Working publication tree are retired. Preview receives selected finished bytes without a source/generated tree or browser route. Catalogue queues remain alongside the Docs queue under `working/`; [Builder](Builder.md#publish-preparation) and [Catalogue publication](Catalogue_Save_And_Refresh.md#per-work-publish) own handoffs.

Collection document-media paths in the tree above apply only to collections declaring `document_media: true`: Library, Context (`works`), Concepts and Moments. Catalogue declares false, so it has documents and separate Work media but no `assets/media/collections/catalogue/` owner, source-media producer or document-media publication binding. Existing empty remnants of that former namespace are not read, maintained or recreated by these owners.

Both private Catalogue queue schemas are version 5 and place their header first. Updates retain the last successful Refresh time, shared pending state and per-Work readiness. Publication retains the last completed nonempty Catalogue Work queue time and exact pending selections, without Preview progress flags. The Docs queue uses `docs_publish_pending_v1`. These files are private workflow state, independent of generated-output replacement and public projection; missing or malformed queues stop their owning operation. Projects-owned `catalogue/media-staging/` remains outside the Docs root, with its current family layout mapped in [Media And Asset Handling](Media_And_Asset_Handling.md#workspace-configuration-and-storage).

Repository maintenance docs live under `documentation/`, independently of external Docs collections. Use the [workflow guide](../guide/README.md) to find a current reference. Native App and Processing keep their own build and release boundaries.

### Source Controls

The four source-control JSON files live directly in `working/source/`; `documents/` contains ordinary Markdown bodies. They remain canonical editable state, with the same schemas and ownership, rather than replaceable generated indexes or private report caches.

| File | Owns |
| --- | --- |
| `index-order.json` | Ordinary hierarchy and literal sibling order. |
| `recent-exclusions.json` | Exact ordinary/collection targets excluded only from Recents. |
| `selected.json` | Star membership across owners, with Build-maintained reader metadata. |
| `unpublishable.json` | Ordinary roots excluded from publication with their descendants. |

`source_control_path` resolves fixed owned filenames from the configured source container and rejects symlink traversal. It does not load configuration or inspect document contents. `index_order_path` supplies one exact path to `read_index_order`; create/position/delete operations carry that resolved path into persistence. Import plans carry the hierarchy path for ordinary creation and include it in their changed-file/rollback inventory instead of inferring it from the Markdown parent. Unpublishable resolves its policy and the Markdown directory independently from one loaded Working configuration. Authoring, inspection, package preparation and builders all use these owners, with no old-location alias, fallback or automatic migration.

The source controls stay in Working. Generation uses the hierarchy and exclusion policy to prepare public navigation. A queued Selected artifact uses the canonical `selected.json` bytes. [Selected Documents](#selected-documents)

## Document And Collection Identity

A document retains its immutable `doc_id` across representations. Local API targets use `{doc_id}` for an ordinary document and `{collection, doc_id}` for a configured collection document. Collection targets are `{}` or `{collection}`. The service resolves Working; stage is not a target field. Collection, tree placement, Catalogue token references and media identity remain independent. Source filenames, titles, selected rows and ambiguous associations cannot substitute for exact identity.

Configured storage supplies collection membership. Source front matter uses `collection` with the exact configured collection ID; ordinary documents have no named membership. New, Import and metadata writers use the resolved owner, and reject retired `sub-scope` spellings. A metadata edit alone does not move a source file or change its owner.

Authored Markdown is flat beneath each owner's `documents/`. Ordinary hierarchy and sibling order come from `working/source/index-order.json`: a nested array of records containing `doc_id` and an optional `children` array. Omitted `children` means a leaf; persisted branches carry only nonempty child arrays. Nesting supplies the parent and literal array position supplies order. Ordinary Markdown no longer authors `parent_id`; runtime parent lookups are derived from this tree. Build joins the exact IDs with source metadata and writes `index-tree.json` in the same order. Named collection documents remain flat and retain their own sorting.

The [Index order owner](../../docs-viewer/services/docs_index_order.py) accepts omitted children during traversal and writes only nonempty child arrays. The serializer preserves sibling order and leaves the in-memory tree intact.

Each collection has an exact ordinary report host. Positioning that host retains its immutable association; it does not choose a different collection or turn collection rows into tree children. A delivery registers the owner once in Working and explicitly places its host in the ordinary tree. Preparation later includes its eligible output in Preview.

Library, Book, Context, Concepts and Moments are authored document collections. They share ordinary source ownership and one independent Thumb action. Thumbnail presence comes from the stored document asset rather than front matter. Subject declarations/projections and their collection customisations are retired. Context associations in Projects derive from generated Work/Gallery token references. Catalogue retains its canonical Work identity, artwork and Regenerate owner.

### Position Ordinary Documents

Position sits beside Index Actions. Choose an ordinary destination in the searchable tree and select **Before**, **After** or **Inside**. A move carries the whole subtree in its existing order. Inside appends the last child. Inside **Root** appends at the top level. The picker includes drafts and excluded documents. It omits the moved node and its descendants.

Save persists the order and updates navigation. A same-parent move projects navigation only. A changed parent also updates the moved document's by-ID parent metadata and affected publication eligibility. Cancel closes without writing. Position does not edit Markdown or refresh Search or Recent. [Position service](../../docs-viewer/services/docs_management_position.py) · [Generation](Builder.md#commands)

New inserts a sibling after the displayed ordinary document, or appends at root without an ordinary anchor. New child and New sibling use their explicit destinations. Import inserts new ordinary documents under the selected parent and preserves the placement of overwritten documents. Delete removes the complete subtree from order and source. Content and title edits preserve placement. Hand edits to the order take effect on the next explicit Build.

## Collection Icons

Each registered collection requires an extensionless `icon` filename stem in `docs-viewer/config/workspace/docs-workspace.json`. The shared `docs_icon_assets.py` lookup validates the name and confines it to an existing, non-symlink SVG in `docs-viewer/static/icons/`; manual [Icon Tokens](Icon_Tokens.md) use the same filename boundary. There is no fallback artwork or separate collection-icon registry.

| Collection | Display title | `icon` |
| --- | --- | --- |
| `works` | Context | `dlf-context` |
| `concepts` | Concepts | `dlf-concept` |
| `moments` | Moments | `dlf-moment` |
| `catalogue` | Catalogue | `dlf-catalogue` |

The browser configuration projects `icon` and `report_host_doc_id` for every collection in both local and public readers. The Index panel matches the exact report host to its configured collection and renders that SVG using the existing list-icon mask, size and colour. It needs no document, collection-manifest or relationship read to select artwork. Report host IDs must be unique in the browser mapping; missing configuration fails visibly. Collection SVG icons and independent document thumbnail copies have separate owners.

The builder's `write_browser_config` owner regenerates local/public reader settings from the checked workspace configuration. Icon/config changes require those settings to be regenerated and public artwork to be registered in `site-tools/config/site-code-update.json` and projected with `bin/site-code-update`. They do not require document or Search rebuilds. The proposed [Related Links](Related_Links.md) builder can later read the same collection `icon` and use the inline-icon renderer; ordinary related-link targets use the selected `dlf-doc` artwork. That directive is not implemented by this slice.

## Collection Deliveries

Collections can own specialised metadata, media producers, customisations, canonical records and public projections as well as documents. Creation, registration changes and whole-collection retirement are development deliveries under [Development Workflow](../development/Development_Workflow.md), with a defined owner and outcome. Docs Viewer has no generic New Collection or Delete Collection action, capability, service endpoint or lifecycle creation receipt. `report_host_doc_id` remains mandatory configuration authority.

For each delivery, identify the collection ID and host, source/generated/media locations, producers and readers, document relationships, selected-document membership, Search inclusion, browser/report registration and public destinations. Creation defines and validates the required configuration and source, builds the owning outputs when needed, and updates the relevant browser projections. Retirement explicitly removes or preserves each owned resource and reference, including host tree placement, private publication metadata, pending selections, generated payloads, selected-document entries and deployed artifacts. There is no Preview completion receipt. Shared assets and other projects retain their own owners. Publish and Git/public deployment remain separately authorised operations.

Document-level New, Edit and Delete operate within an existing configured collection. Collection browsing, Regenerate and package workflows retain their own owners. Removing a document or report host does not deregister the collection or perform a whole-collection cleanup.

### Book Source And Provenance

Library and each configured Book own flat Markdown in `working/source/collections/<collection>/documents/`. A Book's authored `index-order.json` owns placement through `front` for opening pages and the configured ordinary TOC host, `root` for Root chapters, `tree` for Parts and Sections, and `back` for back matter. It also stores the top-level boolean `link_part_headings`, which defaults to false when absent. A page's optional `book_edition` front matter carries `both`, `web`, or `export`, with `both` as the default. Working applies the choice to front and back matter and carries the saved fields and `book_order` into the private `manage-manifest.json`. New, Import, Copy and Delete carry their completed placement into generation. Other exact-document builds carry the saved order forward. [Book editions](Collections_And_Books.md#book-editions) · [Book placement service](../../docs-viewer/services/docs_book_tree.py)

Each working copy has a `copied_from_library` record with the Library document's ID and title at copy time. A chapter's optional `library_sources` list holds those same pairs in the chosen source order. The saved title remains useful after the original is renamed or deleted. Source Save and Build carry the structured fields, and Book's Manage manifest supplies them to the report. Ordinary Markdown import uses its standard fields. Library's `working/source/collections/library/copied-to-book.json` stores the copy indicators independently of the Book documents and chapter provenance. [Book copy and provenance service](../../docs-viewer/services/docs_book_copy.py) · [Front matter parser](../../docs-viewer/services/docs_front_matter.py)

Book Save persists the affected order or edition fields, then uses the completed values to update the exact host and queue any affected web membership. Failure reports the phase and saved effects. A manual host Rebuild uses the saved Book manifest. [Book curation and editions](Collections_And_Books.md#book-curation-in-manage)

## Authoring And Publish

### Explicit External Edit And Media Rebuilds

Application Source Save awaits exact document/Links generation. For an external Markdown edit, supply the intended full `last_updated` timestamp for a body, Title or Summary change, then use **Edit doc → Rebuild** or the exact CLI command. Rebuild preserves saved source and reads its authored timestamps. Use Full Working Build for intentional corpus-wide maintenance, including referenced media updates. [Date provenance](Document_Identity.md#date-provenance) · [Build commands](Builder.md#commands) · [Exact and Full Working Build](Builder.md#docs-build-flow)

Source Save processes selected pending media. Exact document Rebuild uses ready files. Render editable diagrams externally and import the finished SVG. [Document diagrams](Document_Identity.md#diagrams) · [Media ownership](Media_And_Asset_Handling.md)

### Recent Exclusions

`working/source/recent-exclusions.json` controls every Recent-specific exclusion. It is an editable JSON array of exact targets: ordinary pages use `{ "doc_id": "d-20260426-164043-e14f49" }`; collection documents also name their owner, for example `{ "collection": "works", "doc_id": "d-20260801-212422-df11f3" }`. Use exact configured collection IDs, omit `collection` for ordinary pages, and use `[]` for no exclusions. Duplicate targets collapse into one exact exclusion. Extra fields, invalid identities, missing files and invalid JSON fail visibly. The list may retain valid targets for documents that no longer exist.

Exclusions apply to named document targets in Recent. The current feed takes its document entries from Context, Concepts and Moments. Manage Recent exposes **Open Recent exclusions in VS Code** through `/docs/open-recent-exclusions` and opens the configured file, including malformed JSON for repair.

Save the file, then choose Manage **Refresh Search and Recent** to apply the exclusions; full Working maintenance also updates Recent. Only changed content joins the queue. Publish transfers queued bytes without Recent generation. Ordinary document operations preserve saved Recent. [Generated Data Contracts](Generated_Data_Contracts.md#recent-contract) owns its row fields.

### Selected Documents

In Manage, use **Star** or **Remove star** on the displayed document. `POST /docs/set-selected` changes the exact ordinary or collection member in `working/source/selected.json`. The document’s Markdown and timestamps stay intact. Unstar resolves the owner without reading the document. Working stores the author's selections in this file, including draft or excluded targets. [Star service](../../docs-viewer/services/docs_selected_documents.py) · [Request contract](Source_Mutation_Endpoints.md#post-docsset-selected)

The saved `docs_selected_v1` list carries each `doc_id`, `title` and date-only `last_updated`. Collection rows add `collection` and `report_doc_id`. Build refreshes matching selected rows from built documents. Thumbnail assignment updates the selected row's saved thumbnail presence. Delete removes actual deleted targets, including ordinary descendants. Catalogue artwork derives from the five-digit Work ID.

The [Selected Documents report](/docs/?doc=d-20261111-114105-553436) reads the saved Working list when opened. It shows the most recently updated rows first, with collection and document ID breaking ties. Its [data owner](../../docs-viewer/runtime/js/shared/docs-selected-documents.js) prepares exact document links and thumbnail choices, and its [report](../../docs-viewer/runtime/js/reports/selected-documents-report.js) updates known rows from committed effects. It reuses that state across retained navigation. Catalogue thumbnails need at most one policy read for the view.

Star changes queue the shared Selected artifact. Publish copies the canonical file unchanged to `preview/documents/selected.json` and `site/assets/data/docs/selected.json`. The current report host is excluded from public navigation. Its exclusion does not filter the Selected artifact, so star only targets whose row metadata may be published. [Shared publication](../../docs-viewer/services/docs_selected_publication.py) · [Report hosts](Reports.md#current-reports)

### Operations

| Operation | Docs Viewer Manage | Site-preview / public site |
| --- | --- | --- |
| Browse documents, media and Search | Working generated output and assets | Repository/public output and configured public media |
| Create, edit, Delete, placement and Import | Authoring operations | Unavailable |
| Publish | One awaited selected Preview/distribution operation | Unavailable |
| Collection reports | Configured Working owner | Published read-only output |

Working generation carries authored Draft, Index placement, collection hosts and `working/source/unpublishable.json` into eligibility. An intentionally empty policy file contains `[]`; a missing or invalid file fails at its owner. Publish applies the finished queue. Search and Recent have their own refresh action, and ordinary edits preserve the saved discovery files. [Eligibility and queue](Builder.md#publish-preparation) · [Transfer and deployment](Builder.md#preview-and-deployment-boundary)

Local reads resolve the configured Working owner and open the exact generated by-ID file. Manage capability remains with local services. Preview is an applied publication artifact. [Reader payloads and roots](Generated_Data_Contracts.md#current-payload-roots)

## Media Ownership

Ready document media lives under `working/assets/media/` and `preview/assets/media/`, using `workspace/<type>/` and `collections/<id>/<type>/`. Local readers, intake, generation, inventory and export use Working. Exact configured owners keep same-named assets independent. Editable diagram sources belong to their external project/tool. The former workspace-level `assets/media/` root has no fallback owner.

Local media uses `/docs/assets/<configured-family>/<identity>`, resolved to Working. Authored tokens, `docs-media:` identities, public URLs and R2 namespaces remain unchanged. Generation derives exact current references from supplied source/fields in memory and supplies eligible queue selections. Authoring operations carry before/after owned-reference differences from their loaded sources. Publish copies only the completed queue selection into Preview and verifies selected transfers; Preview has no source/generated tree.

Logical identity, storage provider and served URL are separate. Location helpers confine paths/keys and own reads, writes and byte verification. A reference does not establish ownership of its bytes; Catalogue media and retained external originals have separate owners.

Publish processes each document's supplied ready-media references independently, including repeated shared files. It copies selected Working bytes into Preview, compares exact remote size/ETag, and verifies changed transfers. It applies supplied exact media removals and leaves unselected media in place. Inventory and orphan cleanup are separate operations. Required missing bytes stop the selected unit; completed effects remain, with no snapshot receipt or automatic recovery.
