---
draft: false
doc_id: d-20261115-175001-ee5e7b
title: Book Editions
added_date: "2026-11-15 17:50:01"
last_updated: "2026-11-15"
summary: Author the web and export editions of a Book in one Tree, with edition choices for Root front and back matter and a shared table of contents.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Book Editions

**Proposed delivery.** Author a Book's web and export editions in the same Manage UI and produce each edition from the saved Book Tree. [Planned Features](../Planned_Features.md) · [Book Publication](Book_Publication.md)

## Requirements

- Create, edit, and position every page in the Book UI, including a cover, title page, dedication, site introduction, TOC, and chapters. The saved Book Tree supplies the order for both editions.
- Show the existing TOC among the opening pages at Root. Opening pages can sit on either side of the TOC in the same saved order for both editions, ahead of the first Part or Section. Keep **Back matter** at Root after the chapters. Keep the existing TOC source and document identity, and open the web Book at the TOC from the site-wide Index.
- The edition setting applies to Root front and back matter. Its choices are **Both**, **Web only**, and **Export only**, with **Both** as the default. Draft controls readiness separately. Ready chapters, including those already at Root, and the ready TOC page appear in both editions.
- Expand `[[toc]]` from the edition's ready Root opening pages placed after the TOC, followed by ready chapters. Omit empty Parts and Sections. Opening pages before the TOC and back matter remain accessible in reading order. Future Book exports use the authored TOC in the same Tree position, with links within the exported edition. [Book TOC authoring](../Builder.md#book-table-of-contents)
- Authored cross-references within the Book target shared pages. Generated navigation follows the edition's reading order and skips omitted pages. When the web TOC opens directly from the site-wide Index, **Next** leads to the first included page after it, and **Previous** leads to the last included page before it when one exists.

### Source And Generated Manifests

The Markdown front matter of a Root front- or back-matter page owns its edition setting. The Book's `index-order.json` owns page placement and reading order, including the order of opening pages around the TOC and the placement of back matter. Working generation combines these inputs to prepare the Book's manifests and reading order.

- `manage-manifest.json` includes all Book pages, including drafts, with the edition settings for front and back matter and the full Tree placement and order.
- The public `manifest.json` includes chapters and **Both** or **Web only** front and back matter that meet the existing readiness and publication rules. Working uses the saved Tree to prepare web navigation and the TOC.

### Setting A Page's Edition

In Manage, open a Root front- or back-matter page and choose **Edit document → Edition…**. The modal presents **Both**, **Web only**, and **Export only** as a single choice, with the saved setting preselected. Save writes the choice to the page's Markdown front matter through the normal authoring workflow. The Book pane updates from the saved result.

In both List and Tree, show **Web only** or **Export only** as a short text suffix beside the page title. A page set to **Both** displays its title alone.

When the author chooses a chapter position for a **Web only** or **Export only** page, the **Book Position** modal shows that saving the move will set its edition to **Both**. Save the new position and edition setting in the same authoring operation. Working generation applies the usual readiness and publication rules to the moved page.

## Deliverables

- **Manage.** One Book Tree with editable front and back matter, the shared TOC page, and the existing chapter structure. The author can set the edition of a front- or back-matter page and see that choice while organising the Book. The browser owns the authoring controls and retained Tree state. The server saves the chosen placement and front matter and prepares the resulting outputs.
- **Web edition.** Working generation applies edition inclusion alongside existing draft and exclusion rules before preparing public document selections, navigation, and the TOC. It queues the withdrawal of a previously published page that becomes export-only. Search and Recent use web eligibility on their existing refresh paths. Publish applies the completed queue through its current handoff. [Builder](../Builder.md)
- **Export selection.** Resolve the ready export pages from the saved Book Tree. Use the existing HTML snapshot export in `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-export/` to inspect the collection-owned pages in that selection. The existing snapshot follows the flat management manifest order, so check the complete Book sequence, including the shared TOC host, against the Tree separately. [Export](../Export.md)

## Process

1. In Manage, place opening pages around the TOC at Root and closing pages after the chapters. Use **Edit document → Edition…** to set their editions. For example, put an **Export only** preface before the TOC, a **Web only** preface immediately after it, and an **Export only** production note at the end.
2. Mark the pages ready through the existing draft controls. In this example the web Book opens at the TOC, lists the web preface first, and opens it with **Next**. Publish applies the prepared selections through the ordinary queue.
3. Check the resolved export sequence against the Tree. In this example it starts with the export preface, continues with the TOC and chapters, and ends with the production note. Use the existing HTML snapshot to inspect which collection pages are included.

## Delivery Steps

### 0. Readiness

- [ ] Confirm how the resolved export page selection is supplied to the existing HTML snapshot and how the complete Tree order will be reviewed.
- [ ] Confirm the Book Tree, authoring, Working eligibility, and export owners and the effect on existing Book sources and URLs. Agree the bounded implementation and verification scope before starting.

### 1. Author The Book Editions

- [ ] Add the existing TOC to the opening order at Root, with Root placements on both sides of it and back matter after the chapters. Save the edition choice through normal page authoring and carry it in Book management metadata.
- [ ] Add the Edition action and modal. Check that List and Tree show the saved suffix and that selecting **Both** restores the title alone.
- [ ] Walk through positioning a web-only intro, an export-only title page, and an export-only closing page. Verify the **Both** default for front and back matter and confirm that existing Root chapters retain their chapter placement.
- [ ] Move an edition-only page to a chapter position. Verify that **Book Position** shows the change to **Both** before saving and applies it with the move.

### 2. Prepare Web Output And Verify Export Selection

- [ ] Prepare the web edition through Working generation and resolve the export selection from the same Tree. Run the existing HTML snapshot export to inspect its collection-owned pages.
- [ ] Enter the Book from the site-wide Index. Verify that the TOC opens, an eligible opening page placed after it appears in the TOC and is reachable with **Next**, and an eligible opening page placed before it is reachable with **Previous**. Check the Markdown around the token.
- [ ] Verify web and export inclusion for ready front and back matter of each edition choice and a draft. Check that changing a published front- or back-matter page to **Export only** queues its withdrawal.

### 3. Code Review

- [ ] Review authoring, shared ordering, browser and server ownership, web rendering, export selection, and the publication handoff. Record the findings and resolutions from the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).

### 4. Closeout

- [ ] Accept the Manage workflow, web output, and export selection. Update the durable authoring, generation, and export guidance with shipped behaviour.

## Follow-On Book Export

Keep **Collection Export** as the existing selected-document HTML snapshot for offline reading and checking which pages are in the export edition. Its `portable.html` is a text-first view with image placeholders and chapter-level link destinations. [Collection Export](../Export.md)

Scope a separate **Export Book** workflow for PDF and EPUB as a follow-on delivery. The author selects the Book and a format. Both formats use the same ordered selection of ready export documents from the Book Tree, including the cover, opening pages on either side of the authored TOC, chapters, and back matter.

Use the Working document bodies and referenced media as export inputs. Reuse document loading, media preparation, and link resolution from the existing exporter where they fit. Keep document IDs and heading destinations available until the selected format can turn them into local links. The Book Tree orders authored documents. Each format controls how those documents are presented.

- **PDF.** Assemble one print-ready HTML document with its images, cover layout, and page breaks. Give chapters and linked headings unique anchors and resolve TOC and cross-chapter links before rendering. Playwright was used in an earlier experiment and is a candidate to evaluate. Verify that the links stay clickable in the generated PDF. [Playwright PDF API](https://playwright.dev/python/docs/api/class-page#page-pdf)
- **EPUB.** Package the same documents as XHTML with their media and package metadata. Use Book Tree order for the EPUB reading order and derive reader navigation from the same chapter entries that render the authored TOC. Resolve chapter and heading links to the packaged files and fragments. [EPUB 3.3](https://www.w3.org/TR/epub-33/)

When this delivery is picked up, choose the first format and evaluate a representative cover, illustrated chapter, and cross-chapter link. For a site download, attach the finished PDF with **Add file** on the web-only introduction and use the existing Save and Publish workflow. Confirm attachment support separately if EPUB is also offered on the site. [Add a new image or download](../Docs_Images_And_Assets.md#add-a-new-image-or-download)
