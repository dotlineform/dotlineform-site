---
draft: false
doc_id: d-20261116-160615-a73e2c
title: Book Parts And Sections
added_date: "2026-11-16 16:06:15"
last_updated: "2026-11-16"
summary: Give each Book one choice for linking its Part headings and keep Sections private for chapter preparation.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Book Parts And Sections

**Proposed delivery.** Readers enter Parts from the Book's table of contents (TOC) according to one Book setting. Authors use Sections in Manage to collect sources and prepare chapters privately. [Planned Features](../Planned_Features.md) · [Book Editions](Book_Editions.md)

## Requirements

- Give each Book one checkbox, **Link Part headings to their first document**. With it clear, Part headings are plain text and each included chapter has its own TOC entry. Keep this as the default for existing Books.
- With the checkbox selected, each Part heading links to the first document filed directly under it in the saved Tree order. The TOC uses the Part heading as the link text and omits the separate row for that document. The first document appears once in the reading sequence, before the other chapters. Its title and content belong to the author. It can be a title page, a longer introduction, or any other authored page. The author may use the Part title or a different title. The ordinary document title rules apply.
- Omit a Part with no directly filed document. A Part containing only Sections has no entry in the TOC.
- Keep Sections and every document filed in them in Manage. Section placement excludes a document from the reader editions regardless of its Draft setting. Sections contribute neither headings nor pages to the TOC or reading order. The same exclusion applies to the web manifest, direct public page availability, Search and Recent, and the resolved Book export selection.
- Keep chapter identity when moving between a Section and a reader-facing position. Moving a draft chapter to a Part keeps it draft until the author marks it ready. If a page already has a public copy when it moves into a Section, Working queues its withdrawal through the ordinary publication handoff.

## Deliverables

- A saved Book-wide TOC setting in Manage. When linking is enabled, identify the first directly filed document in each Part so the author can see the effect of reordering. Keep the existing document title editor and leave title choice independent of the setting.
- One placement rule in Working's shared edition selection. Use the saved Book order alongside existing readiness and edition rules to prepare the web TOC and reader sequence, publication selections, discovery refreshes, and the resolved export sequence. Publish applies the prepared queue.
- A short walkthrough covering both checkbox states, private Sections, and a chapter moving from staging into a Part and back. Whole-Book export and a reader-facing Subpart level are follow-ons.

## Authoring Process

1. In Manage, copy Library sources to a Section and create the chapter there. Save the chapter while the working copies and their media are still available so Source Save can adopt the media it uses. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)
2. Move completed chapters directly into a Part and mark them ready. If the Book links its Part headings, place the intended introduction first in each Part. Choose the introduction's title as you would for any other document.
3. After moving and checking the chapters, delete the remaining working copies when finished with them and remove the Section if it is no longer needed.

## Delivery Steps

### 0. Readiness

- [x] Confirm the boundary in the current product. Working already shares ready edition rows across the TOC, public membership, and discovery. Today a ready page in a Section can enter those outputs. Extend the shared selection with the placement rule. [Book editions](../Sub_Scope_Index_Architecture.md#book-editions)
- [ ] Settle the case where the first directly filed document is draft while later documents in the Part are ready. The link must follow the authored first document, so Working must never substitute a later chapter. Confirm how the Part and its later pages should appear until that first document is ready.
- [ ] Agree the implementation and verification scope before editing runtime code.

### 1. Implement Authoring And Reader Output

- [ ] Save the checkbox with Book authoring, retain the complete Book Tree in Manage, and show authors which document the heading will open.
- [ ] Apply Section exclusion in Working and prepare the TOC in both checkbox states. Reuse the saved order for navigation and distinguish a TOC formatting change from a change in public page eligibility.
- [ ] Use the ordinary withdrawal handoff for a previously public document moved into a Section. Check discovery through its existing refresh actions.

### 2. Review And Accept

- [ ] In one desktop Manage walkthrough, check a plain heading, a linked heading with a different document title, an empty Part, a Section containing a ready document, and a chapter moved out of and back into a Section. Verify the TOC, reading sequence, public membership or queued withdrawal, and the resolved export order. Allow about 20–30 minutes plus any explicit discovery builds, Publish or deployment the walkthrough needs. Use scoped lint and source review. If shared runtime changes, verify the site projection. Agree any new test work separately.
- [ ] Review use of the saved Tree and shared eligibility selection under the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review). After acceptance, update the durable Book editions and TOC guidance.

### Living Memory Test State

Living Memory's host is currently draft. All current Book content is for testing. Mark the host ready only for a test that requires web eligibility, then return it to draft and use the normal withdrawal workflow for any test pages that were published. Leave orphaned R2 media in place during testing and handle their cleanup separately at deployment time. Publish applies exact queued R2 removals. GitHub Pages deployment applies the committed site snapshot. [Media handling](../Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

## Follow-On

If a larger Book needs a public hierarchy below Parts, introduce Subparts as a reader-facing level. Sections remain available in Manage for preparing chapters.
