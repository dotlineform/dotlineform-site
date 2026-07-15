---
doc_id: docs-viewer-external-asset-collections-concept
title: External Asset Collections Concept
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: proposed
summary: Product concept for a local-only inventory of user-owned project files that stay outside the Docs Viewer document tree.
parent_id: docs-viewer-external-asset-collections
viewable: true
---
# External Asset Collections Concept

## Problem

Docs Import gives a standalone image or downloadable file a wrapper Markdown document. That is useful when an attachment intentionally belongs in the document tree. It is a poor fit for a large or frequently changing project collection: the index becomes one document per file, even though most files are not documents.

Processing is the first proving case. Its Markdown should remain in `docs-viewer/source/processing/`, while source sketches, libraries, archives, spreadsheets, images, and recovered material may be numerous, large, or independently useful. The I Ching collection is a later scale test.

## Desired Capability

An eligible local scope may opt into one external asset collection:

- source Markdown stays in its existing canonical source root
- files remain in their nested project structure
- one local-only report inventories the collection without creating a document per asset
- safe files may later be opened or downloaded through a confined local-service route
- the collection is user-owned data and is never silently deleted or relocated by scope lifecycle actions

This is a Docs Viewer inventory and linking capability, not a digital asset manager.

## Product Boundaries

- A file does not become a Docs Viewer document merely because it is present.
- Existing standalone image and file imports continue to create ordinary wrapper documents.
- The first feature is inventory and linking, not asset editing, moving, renaming, deletion, or automatic organisation.
- Public read-only routes do not expose local collections.
- Repo-managed document attachments remain valid and unmoved.
- Hashes, thumbnails, content indexing, OCR, archive expansion, remote publication, and background jobs wait for evidence.
- Wrapper creation, main-tree promotion, and embedded-detail sub-scopes are separate future capabilities with their own delivery decisions.

The [Architecture](/docs/?scope=studio&doc=docs-viewer-external-asset-collections-architecture) document owns the proposed storage, lifecycle, service, report, security, and extension boundaries behind this concept.

## Delivery

The ordered, finishable outcomes live in the [Docs Viewer Roadmap](/docs/?scope=studio&doc=docs-viewer-roadmap). The [feature parent](/docs/?scope=studio&doc=docs-viewer-external-asset-collections) groups this concept, its architecture, and promoted deliveries. This concept does not own implementation status.

Only the first ready outcome has a delivery document. Later deliveries should be added after the preceding outcome has exposed the real boundary, not copied out of a speculative multi-phase plan in advance.

The first user-visible inventory delivery should establish one durable `External Asset Collections` feature document. It will own shipped configuration, workflow, execution path, extension method, security boundary, and known weak spots. This concept can then retain only genuinely unresolved future capability or be retired.

## Questions To Resolve When Relevant

- Which minimal hidden/system exclusions are needed beyond platform noise?
- Should folders be explicit report rows or derived only from file paths?
- What measured scan time would justify caching or asynchronous refresh?
- Should a later disable workflow preserve the report document or offer separate confirmed deletion?
- Does I Ching become its own Docs Viewer scope or attach to another scope?

None of these blocks the lifecycle-ownership deliverable. Each belongs to the later roadmap row whose outcome it can actually change.
