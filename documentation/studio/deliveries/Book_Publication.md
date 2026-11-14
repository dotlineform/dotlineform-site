---
draft: false
doc_id: d-20261114-213618-b4856c
title: Book Publication
added_date: "2026-11-14 21:36:18"
last_updated: "2026-11-14"
summary: Proposed workflow for copying private Book chapters into a draft edition with a Manage tree and a generated table of contents.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Book Publication

**Proposed.** Continue the design before readiness and implementation. [Planned Features](../Planned_Features.md) · [Private Book curation](library_structure.md)

## Requirements

Book remains the permanent private working area for compiling chapters. Completed chapters can be copied into a separate named collection for release through the normal Docs draft and Publish workflow.

The proposed collection ID is `book-published`, compatible with existing document and managed media routes. Its entry point is a generated table of contents (TOC) document, initially titled **Book draft** and marked draft. The TOC serves as the collection host. Its draft status keeps the entire release collection private while chapters are being marked ready. The TOC takes the place of the standard collection report.

Copy transfers one filed Book chapter at a time. Each chapter can have one linked copy in `book-published`. The first Copy creates a fresh destination ID, starts the copy as a draft, and saves the association by document ID. Repeat Copy opens the existing destination. Book's temporary working copies stay in Book. Each edition chapter owns the managed media referenced in its body. Chapter copies omit assigned thumbnails. Book and its edition copy have independent text. Small corrections to published chapters use ordinary Source Save and Publish so chapter URLs stay stable.

Copy carries over the Markdown body and the `title`, `summary`, `date`, and `date_display` front-matter fields when present. The copied `summary` supplies any `[[summary]]` token in the chapter. The normal creation flow sets fresh `added_date` and `last_updated` values for the edition copy. [Date provenance](../Document_Identity.md#date-provenance)

Book owns chapter creation for the edition through Copy and removal through Delete. When a Book chapter has a linked copy, Delete names both documents in the confirmation, removes both Working documents and their owned media, and regenerates the TOC. For a published chapter, the operation also queues its withdrawal through the ordinary Publish workflow. Edition membership is managed through Book.

## Edition Tree And Reader

Book's authored `working/source/collections/book/index-order.json` owns Parts, Sections, chapter placement, and order. Working generates both Book's `working/generated/collections/book/documents/index-tree.json` and the edition tree from that authored structure. The edition projection includes chapters with linked copies at their Book positions and uses their destination IDs. Copy adds the chapter association and refreshes the edition projection. Part and Section edits, chapter moves, and deletions in Book carry through to the edition tree and TOC in the same operation. The Manage JSON takes each chapter's title and draft status from the destination metadata. The destination chapter's ordinary draft field is the authority for readiness.

Once linked to an edition copy, a Book chapter must stay filed in a Part or Section. It can move between headings or change position within a heading. **Unfiled** is available for documents without an edition copy.

Click the book host in the ordinary Index to open its generated TOC in the standard document pane. Chapter links use normal document navigation. The main Index keeps its usual layout and behaviour.

On a `book-published` chapter, the existing collection Index button opens the configured host, which is the generated TOC. For these chapters, label the button **Table of contents** in Manage and public.

In Manage, an **All chapters** button in the document toolbar opens the edition tree in a read-only modal. The button is available on the TOC host and its chapters. The modal shows Parts, Sections, and both draft and ready chapters, with draft status visible. Choosing a chapter closes the modal and opens that document in the standard reader. The modal is for browsing. Chapter readiness uses the existing draft control on the displayed document.

The generated TOC links only to ready chapters, in tree order, and omits Parts and Sections with no ready chapters beneath them. Open it in Manage to review the ready-only contents before release. Public readers use the same document to browse the edition. Working generation owns TOC updates after changes to membership, order, titles, or readiness and prepares the finished output for the ordinary publication queue.

Include eligible edition chapters in Search and Recent through the existing collection discovery policy. The chapter and TOC host must both be eligible. Discovery keeps its existing refresh and publication workflow. [Collection discovery policy](../Sub_Scope_Index_Architecture.md#flat-book-collections)

## Chapter Links And Media

Private Book chapters use standard media tokens, Media View, and outgoing links in Working. Their Related Links show outgoing destinations only. Link generation omits backlinks to private Book from the saved Related Links JSON, linked documents, and backlink reports, including backlinks that would otherwise come from Catalogue references in Book.

Edition chapters participate in the standard document workflow, including media tokens, Media View, and incoming and outgoing Related Links. When the same Catalogue Work is referenced in a Book chapter and its edition copy, the edition copy supplies the backlink. The edition release check still reports an authored link in an edition chapter that points into private Book. [Related Links](../Related_Links.md)

## Fix Links And Media

To bring a new passage across from Book, paste its Markdown into the linked edition chapter's Source editor, select the passage, and run **Fix links and media**. Review the prepared references in the editor, then use **Save** to persist them. This keeps the edition chapter's ID and any edits elsewhere in its body.

The initial Copy and **Fix links and media** use the saved Book-to-edition ID mapping. When a target has an edition copy, rewrite the link to that copy and keep its section fragment. Flag any target whose edition copy is still draft. When a target has no edition copy, keep the original Book link and flag it as **No edition copy yet**.

After copying a missing target, reopen the edition chapter that contains the link, rerun **Fix links and media**, and save. Copying the target leaves previously saved chapters alone.

Source Save uses its existing media adoption flow to copy referenced managed images, SVGs, and files into the edition chapter's storage and rewrite their paths. If the destination filename already holds different bytes, Save reports the conflict for the author to resolve. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)

## Document Date Token

Add a shared `[[date]]` body token for displaying a document-level date in Library, Book, and the edition. It displays the current document's `date_display` when present and falls back to `date`. With both fields empty, the token produces no visible output. Review existing Library documents for chapter-level dates written in the body that would benefit from moving to front matter and using the token. Dates that are part of the prose stay in the text.

## Proposed Deliverables

- A configured release collection with its own document and media storage, a draft TOC host in the ordinary Index, and the normal chapter draft controls.
- A Book copy action that creates one linked draft per chapter, with edition placement derived from Book and linked deletion owned by Book.
- A **Fix links and media** Source action for selected passages in edition chapters, using the same chapter link mapping as Copy and the existing Save media adoption.
- A shared `[[date]]` token and a review of existing Library dates that could use it.
- Outgoing-only Related Links for private Book, with standard media and link behaviour for edition chapters.
- An advisory edition release check, run on demand from the TOC toolbar in Manage, that flags links into private Book and links to draft edition chapters for the author to review. Related Links for edition chapters use the standard document rules. The ordinary Broken Links report checks whether destinations resolve in Working. Publish continues to apply the prepared queue. [Broken Links audit](../Broken_Links_Script.md) · [Related Links](../Related_Links.md#generated-data-and-freshness)
- An **All chapters** toolbar button in Manage that opens the read-only edition tree, plus a generated ready-only TOC reached through the existing collection Index button.
- A first-release workflow that prepares the eligible TOC, chapters, and media through the existing Working generation and publication queue.

## Editorial Workflow

1. Finish a chapter in private **Book** and copy it to **Book draft**. Find the new draft in the Manage tree modal and open it for review.
2. Adjust Parts, Sections, or chapter order in private **Book**. To delete a linked chapter, use Book's Delete action and review the confirmation for both documents.
3. Mark the chapters intended for release ready. Run the advisory link check from the TOC toolbar and review the findings. Give the TOC its final title and review the generated contents before clearing the host's draft status.
4. Use the ordinary Publish action to apply the queued outputs and review the prepared public reader. Repository deployment follows the existing release workflow.

## Decisions Before Readiness

- **Link findings.** Agree how to present targets that need review in Copy, Source, and the TOC toolbar check.

## Delivery Steps

- [ ] **Readiness.** Confirm the Book-driven tree and TOC projections, chapter association and media handoff, and release review. Check the draft-host eligibility path and the linked deletion handoff. The browser owns tree interaction and selection. Python owns configured copying, media adoption, persistence, deletion, and generation. Agree the smallest verification scope before implementation.
- [ ] **Implementation.** Register the release collection and TOC, add linked Copy and Delete, and project Book's structure into the Manage modal and public reader. Demonstrate the draft-to-ready release handoff with representative chapters and referenced media.
- [ ] **Date token and Library review.** Add `[[date]]` to the shared renderer. Verify display text, fallback to `date`, and empty output. Review existing Library documents and identify candidates for editorial updates.
- [ ] **Code review.** Trace exact source and destination IDs, repeat Copy, link rewriting on Copy and selected passages, release findings for missing and draft destinations, media adoption on Save, Book structure edits, linked deletion, and the transition from a draft host to eligible public output. Verify that private Book creates no stored or displayed backlinks and that edition chapters use normal Related Links. Apply the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).
- [ ] **Closeout.** Record what was verified in Working and public preview, note remaining editorial decisions, and update the durable owners for collection browsing and publication.

## Follow-On

The workflow for substantial revisions to published chapters remains open. Thumbnail copying is a later enhancement. Multiple editions and downloadable editions can be scoped once the first release workflow has been reviewed.
