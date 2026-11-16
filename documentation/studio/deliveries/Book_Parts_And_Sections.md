---
draft: false
doc_id: d-20261116-160615-a73e2c
title: Book Parts And Sections
added_date: "2026-11-16 16:06:15"
last_updated: "2026-11-16"
summary: Give each Book one choice for linking its Part headings and keep Sections private for chapter preparation.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Book Parts And Sections

**Complete and accepted on 2026-11-16.** Readers enter Parts from the Book's table of contents (TOC) according to one Book setting. Authors use Sections in Manage to collect sources and prepare chapters privately. [Book curation and editions](../Sub_Scope_Index_Architecture.md#book-curation-in-manage) · [TOC generation](../Builder.md#book-table-of-contents)

## Requirements

- Give each Book one checkbox, **Link Part headings to their first ready document**. Save it as the top-level boolean `link_part_headings` in that Book’s `index-order.json`, alongside `front`, `root`, `tree`, and `back`. The default is `false`. With it clear, Part headings are plain text and each included chapter has its own TOC entry.
- With the checkbox selected, each Part heading links to the first ready document filed directly under it in the saved Tree order. The TOC uses the Part heading as the link text and omits the separate row for that document. The linked document appears once in the reading sequence, before the other ready chapters. Its title and content belong to the author. It can be a title page, a longer introduction, or any other authored page. The author may use the Part title or a different title. The ordinary document title rules apply.
- Omit a Part with no ready documents filed directly under it, in either checkbox state. This includes Parts containing only drafts or Sections.
- Keep Sections and every document filed in them in Manage, whether the Section is at the top level or inside a Part. Section placement excludes a document from the reader editions regardless of its Draft setting. Sections contribute neither headings nor pages to the TOC or reading order. The same exclusion applies to the web manifest, direct public page availability, Search and Recent, and the resolved Book export selection.
- Keep chapter identity when moving between a Section and a reader-facing position. Moving a draft chapter to a Part keeps it draft until the author marks it ready. If a page already has a public copy when it moves into a Section, Working queues its withdrawal through the ordinary publication handoff.

### Book Settings

Place a gear button labeled **Book settings** immediately before **Select** in the Book index toolbar. Keep it available in Tree and List, including when no chapter is selected.

Open a **Book settings** modal with **Link Part headings to their first ready document** set to its saved value. **Save** writes the choice to the Book’s `index-order.json` and refreshes the TOC if its output changes. **Cancel** closes the modal and preserves the saved setting. Use the modal for future Book-wide options as they are added.

## Deliverables

- A saved Book-wide TOC setting in Manage. When linking is enabled, identify the first ready document filed directly under each Part so the author can see the effect of reordering or changing readiness. Keep the existing document title editor and leave title choice independent of the setting.
- One placement rule in Working's shared edition selection. Use the saved Book order alongside existing readiness and edition rules to prepare the web TOC and reader sequence, publication selections, discovery refreshes, and the resolved export sequence. Publish applies the prepared queue.
- A short walkthrough covering both checkbox states, private Sections, and a chapter moving from staging into a Part and back. Whole-Book export and a reader-facing Subpart level are follow-ons.

## Authoring Process

1. In Manage, copy Library sources to a Section and create the chapter there. Save the chapter while the working copies and their media are still available so Source Save can adopt the media it uses. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)
2. Move completed chapters directly into a Part and mark them ready. If the Book links its Part headings, make the intended introduction the first ready document under each Part. Choose the introduction's title as you would for any other document.
3. After moving and checking the chapters, delete the remaining working copies when finished with them and remove the Section if it is no longer needed.

## Delivery Steps

### 0. Readiness

- [x] Confirm the boundary in the current product. At readiness, Working shared edition selection across the TOC, public membership, discovery and the resolved Book export sequence. That selection ignored Section placement. Living Memory's saved order matched its Working management manifest, and four of its five Section pages were ready. Its draft host and empty site manifest meant verification needed a ready host in a temporary workspace. [Book editions](../Sub_Scope_Index_Architecture.md#book-editions)
- [x] Settle the case where an earlier document is draft. The link opens the first ready document filed directly under the Part. When no ready document exists, the Part is omitted.
- [x] Agree the implementation and verification scope before editing runtime code.

**Ownership and sequence.** Manage owns the checkbox, modal and link target hint using the retained Book order and readiness rows. The Book save owner persists the boolean and returns the saved effect. An absent setting means off. Working applies Section exclusion to both editions and generates the TOC. A checkbox change affects TOC presentation. A ready page crossing the Section boundary can change web membership and queue a withdrawal or restoration even when its Markdown is unchanged. Discovery uses **Refresh Search and Recent**. Publish applies the queued effects.

**Verification and stop conditions.** Use scoped lint, review the affected Working artifacts and queue, and allow 20–30 minutes for one desktop walkthrough, plus the explicit discovery refresh. Review the resolved Book export sequence independently of the checked-document Collection Export. Run the required site projection checks only if shared runtime changes. Queue evidence is sufficient to check the withdrawal handoff at this stage; applying the queue and deploying the site are separate actions. Return for a scope decision if the work requires changing page identities or routes, expanding other eligibility rules, or changing how Publish consumes completed effects. New test work requires separate approval.

### 1. Implement Authoring And Reader Output

- [x] Add **Book settings** to the index toolbar and save `link_part_headings` in each Book’s `index-order.json`. Retain the complete Book Tree in Manage and show authors which document the heading will open.
- [x] Apply Section exclusion in Working and prepare the TOC in both checkbox states. Reuse the saved order for navigation and distinguish a TOC formatting change from a change in public page eligibility.
- [x] Use the ordinary withdrawal and restoration handoff when a ready page crosses the Section boundary. Check discovery through its existing refresh action.

**Implementation evidence.** Scoped Python and JavaScript lint and whitespace checks passed. Direct use of Book Save, Draft and Refresh Search and Recent on a temporary copy of Living Memory verified the plain and linked TOC, a first ready page after a draft, the omitted Part with only staging pages, and Section exclusion from the web manifest, reading order, refreshed discovery and export selection. Moving a ready page into a Section queued withdrawal. Moving it back queued restoration of the same ID. A draft moved out of a Section kept its Draft status. The exact live Working host rebuild refreshed the TOC while Living Memory stayed draft. JavaScript lint passed again after moving Book settings before Select.

**Manual walkthrough.** Open **Book settings** from Tree and List with no chapter selected. Verify that Save persists the checkbox on reopening and Cancel preserves the saved value. Check a plain heading, then use the Part title as a link to a first ready page whose own title differs and which follows a draft. Check that the target has no separate TOC row and appears once in Previous and Next order. Verify that the TOC omits a Part with no directly filed ready pages and that the reader editions exclude both top-level and nested Sections. Move a ready chapter into a Section and back. Verify its ID and Draft value, the TOC and reading sequence, Working web membership and queued effects, refreshed Search and Recent, and resolved export order. Confirm that moving a draft out leaves it draft.

### 2. Code Review

- [x] Review the changed paths and reused owners under the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review). Unchanged settings return before writes. Placement-only edits carry the completed manifest and web selection. A withdrawal uses the existing queue merge without reading chapter Markdown. Restoration prepares exact eligible targets and shares loaded rendering inputs with the host build. The placement handoff saves its completed queue once. Keep Book request shape and path confinement at the existing authoring boundary.

### 3. Acceptance And Closeout

- [x] Record the user's closeout approval after placing **Book settings** before **Select**. The walkthrough remains available for reference. The withdrawal evidence covers preparation and the queue. Publish and live deployment are separate.
- [x] Transfer lasting behavior to [Book curation and editions](../Sub_Scope_Index_Architecture.md#book-curation-in-manage), [Book source ownership](../Source_Organisation.md#book-source-and-provenance), and [TOC generation](../Builder.md#book-table-of-contents). Retain this delivery pending manual archive.

### Living Memory Test State

Living Memory's host is currently draft. All current Book content is for testing. Mark the host ready only for a test that requires web eligibility, then return it to draft and use the normal withdrawal workflow for any test pages that were published. Leave orphaned R2 media in place during testing and handle their cleanup separately at deployment time. Publish applies exact queued R2 removals. GitHub Pages deployment applies the committed site snapshot. [Media handling](../Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

## Follow-On

If a larger Book needs a public hierarchy below Parts, introduce Subparts as a reader-facing level. Sections remain available in Manage for preparing chapters.
