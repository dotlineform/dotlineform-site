---
draft: false
doc_id: d-20261126-221122-5cdb8e
title: Authored Page Breaks For Texts
added_date: "2026-11-26 22:11:22"
last_updated: "2026-11-26"
summary: Add page turns at authored breaks within a single Docs Viewer document, using nerve as the first edition.
ui_status: proposed
parent_id: d-20261118-235100-64ad2e
---
# Authored Page Breaks For Texts

Keep *nerve* as one Markdown document in **Texts**, with one title, one document ID and one reading link from Catalogue Work `00008`. Give readers shorter stretches of the continuous text by placing breaks at natural pauses. The page turns supply the reading sequence. [How to publish a Text edition](Publish_A_Text_Edition.md)

## Authoring And Reading

- In Source, place a standalone `[[pagebreak]]` between paragraphs or fragments. The literal spelling is proposed and follows the existing directive convention. The author chooses the breaks, so they fall at the same passages on desktop and phone. [Source directives](../reference/Source_Editing.md#directives)
- The reader opens the first page from the edition’s ordinary link. Each page ends with **Previous page**, **Next page** and a position such as **Page 4 of 12**. A page can scroll when its contents exceed the available height. Page turns start at the top of the new page and use controls distinct from navigation between documents. [Document navigation](../reference/Reader_Discovery_And_Return.md#collection-previous-and-next)
- Tap or click the page count to open a **Go to page** field with the valid page range. Enter a page number and submit to jump to the top of that page.
- The URL records the current page as a one-based `page` query parameter, such as `&page=4`, and is the sole place that persists the reading position. Page turns and jumps replace the current browser history entry. Reloading or opening a bookmarked URL restores that page. An edition link without a page number opens page 1. [Browser history](../reference/Reader_Discovery_And_Return.md#browser-history)

## Search

**Portfolio Search** includes the Texts landing page and eligible editions by title. Selecting the *nerve* web edition in the search results opens the document on its first page. Consider a dedicated full-text **Search Texts** scope later if readers need to find which edition contains a phrase. Use the pilot to see how readers find a passage within an already open edition. [Current search scopes](../reference/Reader_Discovery_And_Return.md#scope-and-eligibility)

## Delivery Steps

1. Extend document generation to recognise the standalone directive at a valid block boundary and mark each break in the generated content. Keep the entire text in the document for Related Links, static HTML export and possible future full-text search. Preserve literal examples inside code blocks.
2. Add page controls and the page-count jump to the shared reader for documents containing authored breaks. Use the reader’s existing URL and history handling for page changes and return navigation. An existing heading link should reveal the page containing its target. [Reader return state](../reference/Reader_Discovery_And_Return.md#browser-history) · [HTML export](../reference/Export.md#artifact-contract)
3. Author representative breaks in the draft *nerve* edition. Review their placement and the reading flow in Manage and public preview before the edition is released.

## Completion Gates

- [ ] Save and reopen the draft with one document ID. All text and media appear in sequence. Verify that the Catalogue reading link and the Portfolio title result open that edition on its first page when ready.
- [ ] Check first, middle and last pages on desktop and phone. Verify page count, keyboard operation, the start of the new page on a turn, and return to the same page after following a link.
- [ ] Open **Go to page** from the page count with touch and keyboard. Verify that a valid number jumps to the requested page and updates the URL. Reload and reopen a bookmark to a middle page. Confirm that browser Back leaves the edition after page turns and that position restoration works from the URL alone.
- [ ] Verify that a heading link reaches its page, a Catalogue reference after a break generates its backlink, and static HTML export includes the complete text. Note how browser Find behaves across pages during the pilot.
- [ ] Confirm the authored pauses with the editor before preparing the public edition.
