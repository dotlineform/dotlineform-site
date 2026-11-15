---
draft: false
doc_id: d-20261114-213618-b4856c
title: Book Publication
added_date: "2026-11-14 21:36:18"
last_updated: "2026-11-15"
summary: First local release of curated Books, with a desktop Manage split view and a generated table of contents for Living Memory. Pages deployment and live verification remain open.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Book Publication

**Local release complete.** The user accepted the first release on 2026-11-15 after Publish and code review. Living Memory is in Preview and the prepared site. Pages deployment, live verification, and the withdrawal trial remain open. [Planned Features](../Planned_Features.md) · [Private Book curation](library_structure.md)

## Library And Book Collections

Library is the main document collection. Each book is a configured curated collection with its own ID and host. It can contain documents copied from Library and documents created directly in the book. Compile, edit, and publish a chapter in that book using the same chapter ID and owned media. Once published, the chapter keeps its URL through ordinary Source Save and Publish.

All Book instances share the same Manage UI, public reader, and authoring behaviour. A change to the shared UI applies to every instance. A future collection that needs a substantially different UI is a separate collection design with its own ID and implementation.

**Living Memory** is the first instance and uses the existing `book` collection and host ID. Set the host title to **Living Memory** and use the same display title in collection configuration. Living Memory sits directly in the main Index. If grouping becomes useful, an ordinary **Books** parent can hold the book hosts. That parent needs to be eligible for any books beneath it to appear publicly. [Index hierarchy](../Reorder_Docs_Delivery.md)

Each book's authored `index-order.json` owns its document placement and order at Root and within Parts and Sections. A small book can put all its documents at Root. Larger books can use Sections at the top level and Parts that contain Sections. The ordinary draft field owns document readiness.

**Root** is the top level of the Book tree. It is the default place for drafting and compilation and a publication position for opening documents such as a preface or foreword. Keep opening documents at Root and move other chapters into Parts or Sections as appropriate. Edit documents in any of these positions. Draft status controls publication independently of placement. Keep temporary Library copies as drafts while they are in Book.

## Copy From Library

**Copy to Book** shows the configured destination books by title. If there is one book, it is preselected. Initially that book is **Living Memory**. Within the selected book, the placement defaults to **Root** and the author can choose one of that book's Sections. The optional new chapter is created in the selected destination, and the existing-chapter picker shows chapters there.

**Copy to Book** automatically sets `draft: true` on each new Library working copy, regardless of the original's draft status. New Book chapters, including those created through the optional chapter action in **Copy to Book**, and newly imported Book documents also start as drafts. Adding Library source records to an existing chapter preserves its saved draft status.

Library documents generally contribute to one book. The existing **Copied to Book** marker records that a Library source has been copied to a book, and **Clear Copied to Book** clears that history for the selected sources.

## Manage Split View

The split view is for desktop Manage, served by the local Docs server. Opening a Book host or chapter there shows the standard Docs Viewer reader on the right and keeps the left pane available. The Book host opens with the generated TOC on the right.

- **List** shows a searchable list of Book documents, including Root documents and drafts. Selecting a row opens that document on the right.
- **Tree** shows the ordered documents at **Root**, followed by Parts and Sections with their chapters in saved order. Selecting a document opens the same reader. Use the existing Book actions to edit headings and position documents, including changing their order at Root. Use the existing document actions for Source, draft status, and Delete.
- **Expand** follows the Studio Catalogue editor's desktop interaction. The left pane widens and pushes the reader to the right within the available desktop width. Switching modes or widths preserves the displayed document and any edits in progress. [Studio Catalogue layout control](../../../studio/app/frontend/js/catalogue-work-layout.js)

The browser owns pane layout, selection, and view state. List, Tree, and Copy to Book use the selected book's management manifest for inventory and placement. Python resolves the configured collection for each operation and owns persistence, media adoption, generation, and preparation of publication effects.

## Table Of Contents And Public Reader

The generated table of contents (TOC) replaces the report content at each book's host in the ordinary Index. Non-draft Root documents appear as top-level links in saved order before the first Part or Section. The TOC then lists the remaining non-draft chapters in tree order and omits Parts and Sections with no ready chapters beneath them. In a book made entirely of Root documents, the TOC is a flat list. Manage shows the ready-only TOC even while the host is draft.

Book documents use the standard collection routes, links, and Back behaviour. Label the collection Index button **Table of contents** in Manage and public so readers can return to that book's host. The List and Tree pane is available in desktop Manage only.

Use the existing **Previous** and **Next** controls. Links from the Book List, Tree, and TOC supply the shared reader with the book's saved reading order across Root, Parts, and Sections. List and Tree navigation can include drafts. The TOC sequence includes its ready documents. Direct URLs and ordinary chapter links follow the standard reader entry behaviour. [Collection navigation](../Docs_Viewer_Runtime.md)

Working generation refreshes the TOC when heading names, placement, order, chapter titles, draft status, or deletions change its contents. It prepares the TOC and eligible chapter and media changes for the ordinary publication queue. Delete removes the selected Book document, its placement and its owned media, and queues withdrawal when applicable. Chapter eligibility follows the ordinary document and host draft rules. Eligible Book documents participate in site-wide Search and Recent through their existing refresh and publication workflow. [Collection discovery policy](../Sub_Scope_Index_Architecture.md#flat-book-collections)

## Living Memory Cutover

The existing host and its collection configuration are titled **Living Memory**. The user removed the explicit exclusion, marked the host ready, and confirmed Publish on 2026-11-15. Its collection is configured for eligible Search and Recent discovery. The prepared site contains the host and six ready documents. [Current Book curation](library_structure.md)

## Chapter Links And Media

Chapters use the standard document links, media tokens, and Media View. During compilation, Source Save adopts referenced managed files from Library working copies into the chapter's own storage. Save the chapter while those files are available. Once saved, the chapter can be edited and published at its existing ID with its own media. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)

Book links and Related Links follow the ordinary collection rules, including visibility of draft destinations. Authors handle references to draft material in their release review and use the existing Broken Links report for its standard destination checks. [Related Links](../Related_Links.md#generated-data-and-freshness) · [Broken Links audit](../Broken_Links_Script.md)

## Document Date Token

Add a shared `[[date]]` body token for displaying a document-level date in Library and Book. It displays the current document's `date_display` when present and falls back to `date`. With both fields empty, the token produces no visible output. Review existing Library documents for chapter-level dates written in the body that would benefit from moving to front matter and using the token. Dates that are part of the prose stay in the text.

## Deliverables

- A shared desktop Manage split view with List and Tree modes, the existing Book curation actions scoped to the active book, and the Studio-style expand control.
- A generated ready-only TOC at each book's host, a return link from public chapters, and standard Previous and Next controls in book order, starting with Living Memory.
- A Copy to Book destination picker with a per-book **Root** default and Section choice, plus draft defaults for new Book documents and a review of existing draft flags for Living Memory.
- A shared `[[date]]` token and a review of existing Library dates that could use it.

### Index JSON And Read Boundaries

Book uses the normal named-collection routes, document payloads, authoring operations, eligibility, links, and publication queue. Book-specific behaviour lives in the desktop curation pane and placement actions, Library copy, and the TOC host and its Working refresh. The reader opens a Book document through the existing by-ID path with the usual parsing, identity, and confinement checks. Its only Book-specific navigation input is the reading sequence supplied by the invoking link when available. [Collection architecture](../Sub_Scope_Index_Architecture.md) · [Targeted builds](../Builder.md)

| JSON | Owner and when it is read |
| --- | --- |
| Workspace `working/source/index-order.json` and generated `index-tree.json` | The authored file orders the main Index and places each book's host. The Index reads its usual generated tree. Public uses the eligible projection, prepared in Working as `public-index-tree.json` and published as `index-tree.json`. Book chapter order lives within the book. |
| Book `working/source/collections/<id>/index-order.json` | The authored order of Root documents, Parts, and Sections. A complete Book build reads it once. A placement operation reads it if it needs prior placement or uses the updated tree it already has. The ordinary document build carries the completed placement from its saved management manifest merge. |
| Book generated `manage-manifest.json` | The private manifest carries `book_order` alongside document rows. The visible Manage pane loads one manifest for the active book. List, Tree, search, reading order, width changes, and reopening a retained view use that loaded data. Copy to Book uses the retained manifest for its selected destination if available, or loads it when needed. Committed effects update the retained view. |
| Public collection `manifest.json` | The ordinary eligible collection inventory for existing consumers. It follows the normal generation and publication flow. |
| `by-id/<doc_id>.json` | The reader fetches the exact selected document through its standard route. The TOC is the host's ordinary generated by-ID payload. Its ordered chapter links carry their sequence into the common reader in memory, with zero index, manifest, or tree requests to establish Previous and Next. A chapter has zero Book-specific fetches or verifications, including when entered through a direct link. |

### TOC Refresh

Refresh the exact host in Working after a completed change to the TOC's visible order, headings, or ready document IDs and titles. Use the completed placement and document rows already available to the operation, including old and new values where needed to detect a change. Refresh once for a completed batch. A body-only or media-only change uses the ordinary document build alone. Host **Edit doc → Rebuild** can regenerate the TOC from the saved management inputs on demand.

Placement validity belongs to the placement operation. TOC generation consumes that completed structure and the existing draft and title metadata. It renders chapter links as generated navigation, with authored relationships handled by the existing Links owner. The refresh reads the exact host inputs needed to render it and carries its completed output into the normal publication handoff. It has zero chapter source or by-ID reads for enumeration or verification. Publish consumes the completed queue as usual. [Development checklist](../Development_Checklist.md#redundancy-and-defensive-behavior-review)

## Editorial Workflow

1. Create a chapter in the book or copy Library sources into the chosen book. Compile at **Root** or in the chosen Section. Use the List or Tree to open drafts and working copies in the reader. Save the chapter with its adopted media before deleting temporary copies.
2. Set the document's reading order at Root or move it into its Part or Section. Continue editing the same document there and clear its draft flag when ready.
3. Review the generated TOC and the intended draft flags. Use the ordinary Broken Links report as needed. Clear the book host's draft flag when ready for first release.
4. Use the ordinary Publish action to apply the queued outputs and review the prepared public reader. Repository deployment follows the existing release workflow.

## Delivery Steps

- [x] **Readiness review.** Traced configuration, placement, targeted generation, reader navigation, and publication preparation. Reviewed the Living Memory cutover against the current Working metadata. The delivery is ready for implementation approval using the boundaries below.

### Readiness Findings

- **Collection ownership.** Register curated books explicitly in collection configuration. The existing `book-collection` type identifies Library's flat browsing behaviour. Carry the resolved book and host through the existing Book tools, provenance, placement, copy, deletion, and generation. Check the existing thumbnail action and media-path checks, which also refer to the literal `book` ID. Keep `book` and its host ID for Living Memory. [Collection configuration](../../../docs-viewer/config/workspace/docs-workspace.json) · [Thumbnail ownership](../../../docs-viewer/services/docs_document_images.py)
- **One private projection.** The targeted collection manifest merge currently reconstructs an object containing only document rows. Carry the Book structure through that merge and apply placement effects to the same projection. Today Copy generates before it saves placement, and New follows document creation with a separate tree write. Complete the placement in the owning operation and pass the resulting structure into generation. Keep validation at the tree write boundary and give the pane, Copy to Book, and TOC refresh the completed manifest. [Manifest merge](../../../docs-viewer/build/docs_builder/collection_metadata.py) · [Book copy](../../../docs-viewer/services/docs_book_copy.py) · [Book tools](../../../docs-viewer/runtime/js/management/docs-viewer-book-tools.js)
- **One TOC generation path.** Full Working Build renders ordinary hosts before the collections. Prepare each Book's TOC inputs from documents already loaded for that build and its saved placement before rendering the host. For ordinary Book changes, decide whether to refresh from the previous and completed manifest data, then supply the completed inputs to the exact host generation in the same operation. Direct host Rebuild can load the one saved Book manifest. Register the resulting TOC link order with the shared navigation controls using the rendered host content, which keeps chapter entry on the existing by-ID route. [Working Build order](../../../docs-viewer/services/docs_working_rebuild.py) · [Shared navigation](../../../docs-viewer/runtime/js/shared/docs-viewer-collection-navigation.js)
- **Retained TOC.** The reader can restore its retained document without fetching it, and the existing document change notification updates metadata only. Carry the exact changed host as a completed generation effect. Apply the completed host payload if supplied, or invalidate that one retained body and fetch it through the standard route when it is displayed. [Reader entry](../../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js) · [Retained document updates](../../../docs-viewer/runtime/js/shared/docs-viewer-document-controller.js)
- **Living Memory cutover.** Working still has the host titled **Book**, with `draft: false` and its ID on the unpublishable list. The saved Book manifest has eight documents, all non-draft and all placed in the tree, so the initial Root order is empty. Review the intended draft flags for all eight and set the host draft before lifting its exclusion. Align the configured title and enable the existing site discovery option when preparing the delivery. Clearing the host draft uses the ordinary eligibility transition, which prepares the newly eligible chapter and media selections in Working. Those selected restoration reads belong to the existing release path. Publish consumes the completed selections. [Host eligibility](../../../docs-viewer/services/docs_publication_metadata.py) · [Preparation and restoration](../../../docs-viewer/services/docs_generation.py)

Agreed verification uses focused source review and changed-file lint, plus the required site projection and validation if shared runtime changes. Use one desktop walkthrough covering a Library copy, a Root placement, a ready and a draft document, and a title or order change. Inspect the resulting manifest, host payload, and queue effects. Confirm one Book manifest read on first pane use, reuse during List and Tree switches, and the normal chapter request after TOC navigation. Allow seconds to a few minutes for static checks and roughly 15–30 minutes for the desktop walkthrough and artifact review.

### Live Deployment And Withdrawal Test

Use disposable Living Memory test chapters, including a few chapter-owned images. Put the existing excluded host under ordinary draft control, then mark the selected chapters ready and make the host eligible for the trial. Record the test chapter IDs and exact R2 image paths from the publication selections. Publish consumes both configured queues, so check the queued scope before each Publish. [Publication destinations](../Source_Organisation.md#operations)

1. **Publish and deploy.** Use ordinary Publish to prepare the tracked `site/` output and transfer the selected images to R2. Check the TOC, chapter visibility, Previous and Next, and images through `bin/site-preview`. Commit and push the reviewed delivery and its matching `site/` snapshot to `main`, run **Deploy Public**, and verify the same paths on the live site. [Public site workflow](../../../.github/workflows/public-site.yml)
2. **Prepare withdrawal.** Set the Living Memory host back to draft. Use Book's **Delete** action on the exact disposable test chapters. Delete queues the removal of their owned images and thumbnails. If Search or Recent was refreshed for the trial, refresh both after setting the host to draft so the withdrawal includes their updated outputs. [Document Delete media cleanup](../Media_And_Asset_Handling.md#document-delete-media-cleanup)
3. **Publish and deploy the withdrawal.** Run Publish again and check the completed removals for the recorded R2 images. Commit and push the updated `site/` snapshot and run **Deploy Public** again. Verify on the live site that Living Memory has left the Index, the test TOC and chapter URLs are unavailable, and the recorded image URLs are gone. R2 removals take effect during Publish. The live pages are withdrawn by the second deployment. [Selected publication and transfers](../Builder.md#publish-preparation)

### Implementation

- [x] **Configured Book instance.** The `curated-book` type scopes the existing actions to the configured owner. The Working owner resolves to `book`, host `d-20261111-120000-5af14d`, the eight saved document IDs, and the existing Book media namespace. Display title and discovery settings are part of the Living Memory cutover.
- [x] **Root placement and management projection.** Editable Root order, Parts, and Sections are saved and projected alongside document rows in the Book management manifest.
- [x] **Library copy and draft defaults.** Copy uses the selected Book and Root or Section placement and records the Library copy marker. New copies, chapters, and imports start as drafts. Adding Library source records preserves the existing chapter's draft flag.
- [x] **Desktop Manage split view.** List, Tree, and Expand run alongside the standard reader and use the selected Book's retained private manifest.
- [x] **Generated TOC.** The host links ready Root documents and then ready chapters in saved order, omitting empty headings.
- [x] **TOC refresh and queue handoff.** Visible title, readiness, order, and deletion changes refresh the exact host. Body-only saves skip the host refresh. Changed eligible host output uses the ordinary publication queue.
- [x] **Reader sequence.** Book List, Tree, and TOC links supply their reading order to Previous and Next. Direct chapter URLs use the ordinary reader.
- [x] **Date token and Library review.** The shared renderer uses `date_display`, then `date`, and omits an empty standalone date paragraph. Direct document rendering verified both values, empty output, escaped display text, and literal code. Of 152 Library sources, 44 have one valid trailing date that could move to front matter. Examples include *Abstract Art as Evolutionary Mechanism* and *Existentialism’s 21st‑Century Continuations - Psychology & Therapy*. *Dissolving self* has a mid-document date, and *Ecosystem Beyond Plants and Animals — Microbes, Fungi, Abiotic Forces* has an incomplete date. Both need individual review. [Date token](../Builder.md#document-date)

The existing `book` order and manifest were migrated with all eight placements preserved and an empty Root. The former generated Book tree and its read route were retired. Complete and exact-document Book build dry runs reported zero planned writes and zero warnings. The user confirmed copying a Library document to Root and creating a new chapter on 2026-11-15. The saved manifest shows both at Root with `draft: true`. Move, reorder, Delete, Import, and existing-chapter provenance still have interactive verification open.

Desktop Manage keeps one Book pane beside the reader. List uses the shared search and row controls. Tree uses the saved Root, Part, and Section order. Expand widens the curation pane and preserves its visible row. Pane links supply Book reading order to the reader. Narrow windows now use the standard reader and generated TOC. Direct chapter entry, switching mode or width with Source edits in progress, and browser request counts remain for the walkthrough.

The configured Book host's authored report directive was retired. Its first Working TOC linked the eight ready documents in saved order and omitted the two Root drafts and empty Section. Working hosts use the same TOC renderer for full Build, exact host Rebuild, and refresh from completed placement or chapter changes. Direct-entry navigation and interactive TOC refresh remain for the walkthrough.

The prepared public Index contains Living Memory. Its TOC matches the Working ready reading order and the six public manifest members. The first link is the ready Root document *Brain Structure — Illustrated Overview*. All six selected by-ID files are present, and the Root document's referenced SVG exists in Preview. Both publication queues were empty after Publish. Browser playback, live R2 response, and Pages deployment remain unverified.

### Verification And Closeout

- [x] **Code review.** Reviewed pane and reader requests, configured ownership, chapter and placement edits, TOC refresh, and prepared publication output using the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).

The placement review traced one private manifest fetch per loaded Book for Manage and copy selection. Browser changes update retained order and rows from completed effects. Python validates submitted order against one saved inventory read. New, single-document Import, Copy, and Delete each read authored placement for their mutation and pass the completed order into generation. Ordinary chapter edits carry order through the manifest merge. The selected Book and chapter reads retain configured authority and confinement. Desktop request counts and interactive mutation outcomes remain for the walkthrough.

The split-view review traced List, Tree, and Expand to the existing pane DOM and retained manifest. The report is mounted once per opened Book during the page session, and the reader owns document and Source state throughout. Opening a row uses the ordinary reader route. Batch Delete now asks the existing Source navigation guard before deleting the displayed chapter and uses the common reader departure after a completed removal.

The TOC review traced chapter generation to the old and completed private manifest projections. A body-only save compares readiness and titles in memory and performs no host read. A changed TOC reads and writes the exact host payload, preserving its metadata and existing publication selections. Full Working Build passes the Book manifest assembled from its loaded sources and authored order to the ordinary host builder. The retained reader replaces the changed TOC subtree from the operation response, and TOC links provide the reading sequence in memory.

Review fixes apply a pane link's sequence to the current chapter in place, limit placement-only publication to the completed public Index and eligible queue entry, and limit Library provenance edits to source and private manifest fields. The existing chapter in a copy batch contributes provenance alongside the newly generated drafts. Book actions retain configured owner and exact target checks, authored placement validates against one private inventory, and Publish consumes completed selections through its existing destination checks. Changed-file lint, public projection and site validation passed. Interactive scenarios remain separate evidence.

- [x] **Local closeout.** The user accepted the first local release and confirmed Publish. The code review and prepared site inspection are recorded above. Remaining local scenario observations can be collected during normal use.
- [ ] **Living Memory live deployment.** Deploy the prepared Pages snapshot when ready, then verify the live TOC, chapter navigation, and representative images.
- [ ] **Living Memory withdrawal.** Set the host to draft, delete the disposable test chapters, and complete the withdrawal Publish and Pages deployment. Verify the live book withdrawal and R2 cleanup.
- [ ] **Final closeout.** Record live deployment and withdrawal evidence and any remaining editorial decisions.

## Follow-On

A Broken Links report tailored to books can be considered after the first release. The workflow for reviewing substantial revisions to published chapters across multiple saves remains open. Multiple editions of a book and downloadable editions can be scoped once the first release workflow has been reviewed.
