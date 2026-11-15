---
draft: false
doc_id: d-20261114-213618-b4856c
title: Book Publication
added_date: "2026-11-14 21:36:18"
last_updated: "2026-11-15"
summary: Proposed shared design for curated books, starting with Living Memory, with a Manage split view and a generated table of contents for each book.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Book Publication

**Proposed.** Continue the design before readiness and implementation. [Planned Features](../Planned_Features.md) · [Private Book curation](library_structure.md)

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

The existing host is on the unpublishable list, and new documents in `book` currently start as non-draft. Keep the host excluded while reviewing existing chapters and temporary copies and setting their intended draft flags. Give documents without a Part or Section placement an initial saved order at Root. Set the Living Memory host to draft before removing its unpublishable entry. Clear the host's draft flag when Living Memory is ready to release through the ordinary Docs workflow. [Current Book curation](library_structure.md)

## Chapter Links And Media

Chapters use the standard document links, media tokens, and Media View. During compilation, Source Save adopts referenced managed files from Library working copies into the chapter's own storage. Save the chapter while those files are available. Once saved, the chapter can be edited and published at its existing ID with its own media. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)

Book links and Related Links follow the ordinary collection rules, including visibility of draft destinations. Authors handle references to draft material in their release review and use the existing Broken Links report for its standard destination checks. [Related Links](../Related_Links.md#generated-data-and-freshness) · [Broken Links audit](../Broken_Links_Script.md)

## Document Date Token

Add a shared `[[date]]` body token for displaying a document-level date in Library and Book. It displays the current document's `date_display` when present and falls back to `date`. With both fields empty, the token produces no visible output. Review existing Library documents for chapter-level dates written in the body that would benefit from moving to front matter and using the token. Dates that are part of the prose stay in the text.

## Proposed Deliverables

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
| Book generated `manage-manifest.json` and current separate `index-tree.json` | Put the generated Book structure alongside document rows in the existing private `manage-manifest.json`, and retire the separate Book tree payload and its route. The visible Manage pane loads one manifest for the active book. List, Tree, search, reading order, width changes, and reopening a retained view use that loaded data. Copy to Book uses the retained manifest for its selected destination if available, or loads it when needed. Committed effects update the retained view. |
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

- [ ] **Readiness.** Trace the existing operations tied to the literal `book` ID and the current tree, manifest, and exact-document call paths. Confirm the manifest handoff for placement and TOC refresh, the initial Root order, and the Living Memory release handoff. Agree the smallest verification scope before implementation.

### Implementation

- [ ] **Configured Book instance.** Resolve the book and host through collection configuration and scope the existing actions to that book. Confirm that Living Memory resolves to the existing `book` owner, host ID, document IDs, and media paths.
- [ ] **Root placement and management projection.** Persist editable Root order with Parts and Sections. Project placements and document rows together in the Book management manifest. Confirm that new, moved, reordered, and deleted documents have the expected saved placement and that the manifest reflects the completed changes.
- [ ] **Library copy and draft defaults.** Select the destination book and Root or Section, then apply the ordinary copy and chapter actions. Confirm that new copies, chapters, and imports start as drafts, adding sources preserves the existing chapter's draft flag, and Library still records the copy marker.
- [ ] **Desktop Manage split view.** Mount List, Tree, and expand or collapse alongside the standard reader. Confirm that changing mode or width preserves the selected document and uses the retained manifest, and that the visible pane loads only the selected book's manifest on first use.
- [ ] **Generated TOC.** Generate the host's ready-only links from the completed placement and document rows. Confirm that Root links come first, nested order follows the tree, empty headings are omitted, and a Root-only book renders as a flat list.
- [ ] **TOC refresh and queue handoff.** Connect eligible title and readiness changes, placement changes, deletions, and host Rebuild to the exact host refresh. Confirm that a TOC-affecting batch completes one refresh, a body-only save takes the ordinary build path, and changed host bytes enter the existing publication queue.
- [ ] **Reader sequence.** Pass the saved order from List, Tree, and TOC links to the existing Previous and Next controls. Confirm navigation across Root and heading boundaries, the eligible public sequence, and the standard direct-entry and Back paths. Trace document and navigation requests against the read boundaries above.
- [ ] **Date token and Library review.** Add `[[date]]` to the shared renderer. Verify display text, fallback to `date`, and empty output. Review existing Library documents and identify candidates for editorial updates.

### Verification And Closeout

- [ ] **Code review.** Trace reads and checks in opening and switching the Manage pane, opening a chapter from the TOC or directly, ordinary chapter Save, placement changes, and TOC refresh. Account for every Book-specific read and verification, including those inside reused helpers, and verify the completed handoff to Publish. Apply the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).
- [ ] **Living Memory first release.** Apply the reviewed Root order and draft flags, then move the existing excluded host to ordinary draft control. Confirm the ready TOC, chapter and media handoff, and public preview through the normal Publish workflow once the host is eligible.
- [ ] **Closeout.** Record what was verified in Working and public preview, note remaining editorial decisions, and update the durable owners for collection browsing and publication.

## Follow-On

A Broken Links report tailored to books can be considered after the first release. The workflow for reviewing substantial revisions to published chapters across multiple saves remains open. Multiple editions of a book and downloadable editions can be scoped once the first release workflow has been reviewed.
