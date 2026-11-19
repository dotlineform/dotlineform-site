---
draft: false
doc_id: d-20260607-222033-ce5515
title: Source Mutation Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-11-18"
parent_id: d-20260607-222033-647b52
---
# Source mutation endpoints

Working resolves an ordinary target as `{doc_id}` and a named document as `{collection, doc_id}`. The action resolver owns editorial availability. The service owns configured target resolution and operation validation. Use [Source editing](Source_Editing.md) for the complete Markdown buffer and its Save. [Local service map](Endpoint_Overview.md) · [Endpoint dispatcher](../../docs-viewer/services/docs_management_service.py)

## `GET /docs/metadata`

Read the exact source's management `record`, target identity and `location_parent_id`. Ordinary resolution uses the saved Index order for membership and parentage. This read is independent of the Source editor's complete-buffer load. [Committed-record owner](../../docs-viewer/services/docs_management_document_target.py)

## `POST /docs/create`

New supplies its title and exact ordinary placement or configured collection. The service plans a new immutable identity and draft, writes the source create-only, and hands its prepared record and any tree change to exact generation. If generation fails after creation, use the committed identity to find the new source. Direct Catalogue New belongs to Regenerate. [Create planner](../../docs-viewer/services/docs_management_mutations.py) · [Write and rebuild](../../docs-viewer/services/docs_management_mutation_service.py) · [Import endpoints](Docs_Import.md#implementation-boundary)

## `POST /docs/rebuild-document`

Send the exact document target. Rebuild reads the saved Markdown once, checks identity, readiness and report structure, and supplies the parsed record to exact generation. For a Book document it also reads the saved Book order so generation can project a placement already written by an import. It preserves source bytes and dates. The completed `target`, `record` and rebuild effects feed the management change owner. The reader awaits a fresh exact generated payload in the current route. Search and Recent retain their saved files. Use this after an external edit or to regenerate a saved source. [Rebuild owner](../../docs-viewer/services/docs_document_rebuild.py) · [Generation handoff](../../docs-viewer/services/docs_write_rebuild.py) · [Exact build](Builder.md#docs-build-flow)

## `POST /docs/set-draft`

Send the exact target plus boolean `draft`. The service rewrites that field using the loaded source spans and preserves other text and dates. It completes exact generation even when readiness is unchanged. The response distinguishes saved source from generation and returns the committed record for the existing list/menu projection. The operation is separate from the publication exclusion policy. Catalogue uses its own readiness rules. [Draft owner](../../docs-viewer/services/docs_management_draft.py) · [Eligibility](Builder.md#publish-preparation)

## `POST /docs/set-selected`

Send the exact target plus boolean `selected`. Star reads the exact metadata for its row. Unstar removes the saved identity without reading source. Both carry the completed Selected change and its shared publication selection. Publish applies the selected artifact's saved bytes. [Selected owner](../../docs-viewer/services/docs_selected_documents.py) · [Selected Documents](Source_Organisation.md#selected-documents)

## `POST /docs/move` and `POST /docs/order-children`

Position sends ordinary `doc_id`, `target_doc_id` and `placement` (`before`, `after` or `inside`). An empty destination with `inside` means Root. It moves the whole ordinary Index node. **Sort Children A–Z** supplies `parent_doc_id` and the completed `child_doc_ids` order. Both persist `index-order.json` and project affected navigation. A parent change also updates the moved by-ID parent field and can change eligibility. These operations preserve Markdown and Links. After a failed handoff, the response can still report saved position. Book Position uses its own order. [Position owner](../../docs-viewer/services/docs_management_position.py) · [Ordinary placement](Source_Organisation.md#position-ordinary-documents) · [Book Tree](Collections_And_Books.md#book-curation-in-manage)

## `POST /docs/delete`

One locally confirmed request supplies `{doc_ids, confirm: true}` for ordinary subtree roots, `{collection, doc_id, confirm: true}` for a named document, or `{collection, doc_ids, confirm: true}` for a Book batch. Catalogue Work deletion follows Regenerate. The service selects exact sources, Index or Book placement effects, Selected rows and owned media. It carries the actual deleted IDs through Working generation, queues the public effects and completes Working media removal. [Delete owner](../../docs-viewer/services/docs_management_delete.py) · [Media cleanup](Media_And_Asset_Handling.md#document-delete-media-cleanup)

Responses retain completed effects on failure, including the actual deleted IDs and reported phase. The browser projects those effects. After successful ordinary generation it refreshes Index once and awaits a surviving caller or fallback when the displayed document was deleted. [Browser action owner](../../docs-viewer/runtime/js/management/docs-viewer-management-actions.js) · [Browser history](Reader_Discovery_And_Return.md#browser-history)

Confirmation uses the already loaded ordinary subtree, including collapsed descendants, or exact collection/Book selection. Cancel sends no request. The service carries known deleted IDs, remaining parent metadata and changed Selected rows into generation; it does not render unrelated sources. Publication handoff queues exact public effects before selected Working media is unlinked. Source, navigation, Selected, generation and media completion can therefore differ at a failing phase. The ordinary subtree includes descendants regardless of draft/publication exclusion; named-document deletion retains its host and unselected siblings. The design-time default remains unchanged.

## `POST /docs/refresh-discovery`

Send `{}`. The discovery service derives one selection for Search and Recent, writes and queues changed output, and reports its phase and completed files. The browser refreshes active discovery caches. Document rendering and the full maintenance CLI have separate entry points. [Discovery service](../../docs-viewer/services/docs_discovery_refresh.py) · [Build and publication](Reader_Discovery_And_Return.md#build-and-publication)

## Local Folder Links

`POST /docs/open-local-target` accepts only one canonical `target`. A `docs:` prefix selects the configured Docs root; other targets are Projects-relative. [The local-link service](../../docs-viewer/services/docs_local_links.py) decodes that identity, resolves the configured root, checks the existing file/directory and resolved containment, then opens the directory or reveals the file on macOS. It receives no document ID, label or browser URL and performs no document build/publication. Capabilities distinguish root availability from platform activation. [Source/local link authoring](Source_Editing.md#local-links-and-external-editor)

## Completion And Recovery

The [management client](../../docs-viewer/runtime/js/management/docs-viewer-management-client.js) retains structured failure data on `error.payload`. Draft distinguishes `source_saved` from `generation_complete`; Position/Sort distinguish `position_saved` from generation; Delete reports actual removed IDs, source/tree/Selected/generation/media effects and its failing phase/target. These are operation results rather than a shared all-or-nothing transaction.

The browser projects committed records/deletions even when later work fails, and keeps service completion distinct from list/display failures. Use completed effects to identify the failed owner, correct the cause and complete its Build, display refresh or Publish as applicable. Draft changes only readiness, Position preserves Markdown, and both preserve dates. Search/Recent, browser configuration and Publish remain independently owned. Earlier delete evidence and test limits are [recorded separately](../deliveries/Runtime_Configuration_And_Recovery_Review.md#later-local-service-map-review).
