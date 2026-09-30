---
draft: false
doc_id: d-20260423-000000-8fd731
title: Source Organisation
added_date: "2026-04-23 00:00:00"
last_updated: "2026-09-30 12:20:34"
summary: Working source and generated storage, one read-only Preview snapshot, and exact collection and media ownership.
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Source Organisation

`docs-viewer/config/workspace/docs-workspace.json` is the storage authority, using `docs_workspace_v4`. `docs_workspace_config.py` resolves the single existing root selected by `DOTLINEFORM_DOCS_BASE_DIR`. An unavailable configured root is an unavailable workspace; no repository or alternate root is inferred. The earlier scope registry and nested scope storage are retired.

`DOTLINEFORM_DOCS_BASE_DIR` selects the Docs Viewer folder directly. It is independent of `DOTLINEFORM_PROJECTS_BASE_DIR`, which owns Catalogue, Processing, Data Sharing and other project workspaces. Both settings live in `.env.local`; neither is an alias or fallback for the other. To relocate Docs storage, stop services and the watcher, move the complete Working and Preview trees to the explicitly selected root, change the setting, verify the resolved locations, and restart.

## Storage And Roles

```text
$DOTLINEFORM_DOCS_BASE_DIR/
  working/
    source/
      documents/<doc_id>.md
      documents/index-order.json
      documents/unpublishable.json
      media/build-source/mermaid/
      collections/<collection>/
        documents/<doc_id>.md
        media/build-source/mermaid/
    generated/
      documents/{index-tree.json,recent.json,by-id/,...}
      search/index.json
      collections/<collection>/documents/
      catalogue/
  preview/
    preview-manifest.json
    documents/{index-tree.json,recent.json,by-id/,...}
    search/index.json
    collections/<collection>/documents/
    catalogue/
  assets/
    media/workspace/{img,svg,files,html}/
    media/collections/<collection>/{img,svg,files,html}/
    works/{primary,thumbs,media/files}/
```

| Role | Ownership |
| --- | --- |
| Working Source | Canonical Markdown, ordinary hierarchy/order, media provenance and registered producer input. |
| Working Generated | Replaceable document, Search and Catalogue JSON used by the local reader. |
| Shared assets | Current document and Work media, without per-stage copies. |
| Preview | One complete read-only prepared snapshot retained by Publish, independently inspectable on disk. |
| Public projection | Downstream repository/R2 output served by the website. |
| Rendered view | Presentation of document payloads and media; it is not source. |

Working registers ordinary documents, collection hosts, collection customisations and media once. Preview derives the same collection/media owners for preparation. Current named collections are Works, Concepts, Moments and Catalogue. Preview has no persistent source/generated tree or Docs Viewer browsing route. The preparation phase of Publish uses temporary input/output and removes it when the operation finishes.

Durable Studio development documentation is maintained in repository `documentation/studio/`, independently of these external document collections. The native App and Processing projects retain their own build and release boundaries.

## Document And Collection Identity

A document retains its immutable `doc_id` across representations. Local API targets use `{doc_id}` for an ordinary document and `{collection, doc_id}` for a configured collection document. Collection targets are `{}` or `{collection}`. The service resolves Working; stage is not a target field. Collection, tree placement, Catalogue subject and media identity remain independent. Source filenames, titles, selected rows and ambiguous associations cannot substitute for exact identity.

Configured storage supplies collection membership. Source front matter uses `collection` with the exact configured collection ID; ordinary documents have no named membership. New, Import and metadata writers use the resolved owner, and reject retired `sub-scope` spellings. A metadata edit alone does not move a source file or change its owner.

Authored Markdown is flat beneath each owner's `documents/`. Ordinary hierarchy and sibling order come from `working/source/documents/index-order.json`: a nested array of records containing `doc_id` and `children`. Nesting supplies the parent and literal array position supplies order. Ordinary Markdown no longer authors `parent_id`; runtime parent lookups are derived from this tree. Build joins the exact IDs with source metadata and writes `index-tree.json` in the same order. Named collection documents remain flat and retain their own sorting.

Each collection has an exact ordinary report host. Positioning that host retains its immutable association; it does not choose a different collection or turn collection rows into tree children. A delivery registers the owner once in Working and explicitly places its host in the ordinary tree. Preparation later includes its eligible output in Preview.

Concepts and Moments are document collections rather than separate Concept/Moment entities. Works owns Subject specialisation through private `authoring_subject` metadata. Reader manifests and individual document JSON omit `subject`. Ordinary documents retain their authored fields through common preparation, while collection customisations project their own authoring fields into reader data. Catalogue has its own canonical Work identity and regeneration owner.

The Position button beside Index Actions uses `arrow-up-down.svg`. Its synchronous modal moves the displayed ordinary document and its whole subtree Before, After or Inside a chosen ordinary destination. Inside appends the last child; Inside Root appends a root. All ordinary documents are available regardless of draft/unpublishable state, except the moved subtree. Save writes the JSON and refreshes the tree; Cancel writes nothing. Drag positioning is retired.

New inserts after the displayed ordinary document as its sibling. With no ordinary anchor it appends at root. New child and New sibling retain their explicit destinations. Import appends new documents inside the selected parent and preserves existing placement on overwrite; batch creation writes parents before their children while retaining sibling sequence. Delete removes the complete subtree from JSON and source. Renaming or editing content does not reposition documents. Hand edits to the JSON take effect on the next Build; the Markdown watcher does not watch that file.

## Collection Deliveries

Collections can own specialised subject data, media producers, customisations, canonical records and public projections as well as documents. Creation, registration changes and whole-collection retirement are development deliveries under [Development Workflow](Development_Workflow.md), with a defined owner and outcome. Docs Viewer has no generic New Collection or Delete Collection action, capability, service endpoint or lifecycle creation receipt. `report_host_doc_id` remains mandatory configuration authority.

For each delivery, identify the collection ID and host, source/generated/shared-media locations, producers and readers, document and subject associations, selected-document membership, Search inclusion, browser/report registration and public destinations. Creation defines and validates the required configuration and source, builds the owning outputs when needed, and updates the relevant browser projections. Retirement explicitly removes or preserves each owned resource and reference, including host tree placement, generated payloads, selected-document entries and deployed artifacts; invalidate a Preview completion receipt if its snapshot is changed outside Publish. Shared assets and other projects retain their own owners. Publish and Git/public deployment remain separately authorised operations.

Document-level New, Edit and Delete operate within an existing configured collection. Collection browsing, Regenerate and package workflows retain their own owners. Removing a document or report host does not deregister the collection or perform a whole-collection cleanup.

## Authoring And Publish

### Selected Documents

`working/source/documents/selected.json` owns star membership for ordinary documents and collection sub-documents. Its `docs_selected_v1` payload contains `docs` rows with exact `doc_id`, `title` and `last_updated`; collection rows also carry their configured `collection` and `report_doc_id`. Missing or malformed selection data fails visibly. Membership is the flag; there is no second editable front-matter value. The Working star control uses an outline when unset and a filled yellow star when set, and writes through `/docs/set-selected` without changing document Markdown or its modification date.

Ordinary and targeted collection builds update title/date metadata only for selected documents they build. Delete removes all selected targets actually deleted, including ordinary descendants; collection-document delete recovery restores the selection alongside the source. A whole-collection retirement delivery handles that collection's selected-document entries explicitly. The list is independent of Search/Recents inclusion policy.

The shared `selected_documents` report on dotlineform (`d-20260426-164043-e14f49`) reads the current list when opened and displays linked titles ordered by `last_updated DESC`, then collection and immutable document ID for ties. Local links use `/docs/`; collection links open the exact configured host with the sub-document ID. Public links use the public viewer route. Working reads all selections, including draft/unpublishable documents.

Publish preparation intersects selections with its exact eligible document set, refreshes retained title/date/host metadata from captured source, and builds `preview/documents/selected.json`. It excludes draft/unpublishable branches and sub-documents whose collection host is excluded while preserving Working selections. Distribution copies those prepared bytes unchanged to `site/assets/data/docs/selected.json`; it does not re-evaluate Working flags or eligibility. Every Publish prepares a fresh snapshot. The public report registry and reader configuration are tracked runtime configuration; selection content reaches the site only through Publish.

### Operations

| Operation | Docs Viewer Manage | Site-preview / public site |
| --- | --- | --- |
| Browse documents, media and Search | Working generated output and shared assets | Repository/public output and configured public media |
| Create, edit, Delete, placement and Import | Authoring operations | Unavailable |
| Publish | One awaited preparation and distribution operation | Unavailable |
| Collection reports | Configured Working owner | Published read-only output |

Ordinary and other collection source documents require explicit boolean `draft`. Catalogue source rejects that field, its generated document metadata omit it and every Catalogue document has fixed eligibility. Prepare Preview excludes draft roots and descendants, roots in ordinary `working/source/documents/unpublishable.json` and their descendants, and collections whose report host is excluded, including Catalogue. An intentionally empty ignore file contains `[]`; missing or invalid policy fails visibly. The eligible set is captured before building, with a pruned copy of `index-order.json` in the temporary inputs. Surviving branches retain their relative order; excluded children are not promoted. Working retains the complete tree.

`POST /docs/publish` accepts an empty object. `docs_publish.py` awaits `docs_prepare_preview.py`, then distributes the returned completed snapshot through `docs_deploy_repo.py`. Preparation captures current eligible source, saved Search/Recents and selected Catalogue JSON, builds documents in temporary storage, validates the finished output and replaces Preview. `docs_preview_snapshot.py` writes `preview-manifest.json` after byte verification. A build failure leaves the previous Preview intact; failure during replacement leaves no valid completion receipt. A fresh Publish is the recovery operation. There is no intermediate confirmation, change-list modal or separate acceptance action.

Ordinary Working edits and deletions reach Preview and the repository through the next Publish. Source Save writes validated source; the watcher rebuilds document projections independently. Source saves, draft changes and ordinary watcher updates do not rebuild Search. Rebuild docs and Search remains an explicit operation. Links and Broken Links remain Working-owned.

Local generated reads resolve the configured Working owner without a stage parameter. Ordinary document reads open the exact generated by-ID file without reading the document index or validating its stored URL. Exact immutable identity, configured ownership, path confinement and payload parsing remain required. Stage-bearing URLs/requests and `/docs/preview/*` browsing are retired without aliases. Management capabilities remain distinct from public read-only access.

Working and Preview are storage/build/publication roles only. The synchronous Publish workflow prevents edits until completion: capture inputs and compare destinations once, then carry those results through the operation. Do not add intermediate freshness checks or repeat source/snapshot scans. Input validation and verification of completed writes/transfers remain required; ordinary reading is not a snapshot audit.

Distribution consumes the exact completed snapshot from preparation, without rereading source/generated output or filtering membership again. Success means repository and configured media distribution completed. Failure reports the owning phase and incomplete publication; completed Preview remains inspectable after distribution failure. Repository and R2 writes are not one atomic transaction. Review the result through `bin/site-preview`. Git commit/push and the manual GitHub Pages workflow remain separate explicit actions. Public reader payloads carry no publishing-stage discriminator. [Builder](Builder.md) owns producer and distribution details.

## Media Ownership

Ready media has one shared current asset location and configured public destinations. Editable inputs retain their source owner; registered producers build their configured outputs. Collection media and Mermaid inputs remain with the exact collection owner. Same-named assets in different collections are independent.

Local media uses `/docs/assets/<configured-family>/<identity>`. Prepared content records exact shared asset identities; publication projects the configured public URLs. Authored logical identities remain unchanged. Preview contains no media copies or historical renditions.

Logical identity, storage provider and served URL are separate. Location helpers confine paths/keys and own reads, writes and byte verification. A reference does not establish ownership of its bytes; Catalogue media and retained external originals have separate owners.

Distribution reconciles the prepared asset selection from current shared local bytes into configured repository/R2 destinations. Missing local assets fail without remote fallback. Comparison precedes writes; transferred bytes are verified. Publish does not automatically delete shared or remote assets, advance media versions or retain backup trees. Existing public route and R2 namespaces retain their configured identities.

Manual review covers the principal Manage readers/actions and successful Publish feedback. Works editor, package operations, saved-state conversion, failure recovery and independent R2 verification have not been exercised as part of this workflow change; no measured speedup is claimed. Historical scope and publication tests remain unchanged and are not current integration evidence.
