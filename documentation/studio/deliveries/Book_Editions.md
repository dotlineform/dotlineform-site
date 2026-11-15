---
draft: false
doc_id: d-20261115-175001-ee5e7b
title: Book Editions
added_date: "2026-11-15 17:50:01"
last_updated: "2026-11-15"
summary: Author the web and export editions of a Book in one Tree, with edition choices for Root front and back matter and a shared table of contents.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Book Editions

**Complete and accepted on 2026-11-15.** Manage authors both editions in one Book Tree. Working prepares the web edition and resolves the export sequence. Whole-Book export remains a follow-on. [Planned Features](../Planned_Features.md) · [Book editions](../Sub_Scope_Index_Architecture.md#book-editions)

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
- **Export selection.** Resolve the ready export pages from the saved Book Tree and review the complete sequence there, including the shared TOC host. Collection Export remains available for snapshots of checked collection pages. A whole-Book export is a separate delivery. [Export](../Export.md)

## Process

1. In Manage, place opening pages around the TOC at Root and closing pages after the chapters. Use **Edit document → Edition…** to set their editions. For example, put an **Export only** preface before the TOC, a **Web only** preface immediately after it, and an **Export only** production note at the end.
2. Mark the pages ready through the existing draft controls. In this example the web Book opens at the TOC, lists the web preface first, and opens it with **Next**. Publish applies the prepared selections through the ordinary queue.
3. Check the resolved export sequence against the Tree. In this example it starts with the export preface, continues with the TOC and chapters, and ends with the production note.

## Delivery Steps

### 0. Readiness

- [x] Trace the Book Tree, authoring, Working eligibility, public navigation, and HTML snapshot against the current product.
- [x] Specify the snapshot handoff and how to verify the complete export sequence.
- [x] Approve the implementation and verification scope below before starting Step 1.

**Book Tree and sources.** At cutover, Living Memory had two Root chapters. The saved order gained the existing TOC at the start of Root and room for front and back matter. The TOC kept its ordinary Index address and chapters kept their placements and collection addresses. Markdown front matter owns the edition choice. The browser owns the placement and edition choices and updates its retained Book pane from the saved result. The authoring service saves the selected order and any affected Markdown in one awaited operation, then generates the affected outputs. [Book source ownership](../Source_Organisation.md#book-source-and-provenance)

**Working and reader.** Derive the ready reading orders from the saved Tree. Working applies the existing host, draft, and exclusion rules to the web edition and uses the same per-page eligibility for the public manifest, the TOC, and the existing Search and Recent refresh paths. The TOC link list is only part of the reading sequence. Moving a page before the TOC or into back matter can change Previous or Next while leaving the link list identical. Carry the complete web sequence through the existing reader navigation, including when the host opens directly from the site-wide Index. Working queues a withdrawal when a previously published page becomes export-only. The author keeps cross-references pointed at shared Book pages and reviews starred pages for web eligibility. [Builder](../Builder.md#book-table-of-contents)

**Export review.** Resolve the ordered ready export IDs from the Book Tree and verify that sequence against Manage, including the ordinary TOC host when it is ready. Export readiness uses draft status and edition choice independently of web publication policy. Collection Export takes checked collection IDs and builds its own flat A–Z index. The Book's TOC host belongs to the ordinary Index. [Collection Export](../Export.md#input-and-eligibility)

**Verification and gate.** Use focused source review and changed-file checks, including the required site projection checks for shared runtime changes. Allow roughly 20–30 minutes for one desktop walkthrough and artifact review, plus build time. Use one Book example to check edition choices, a draft, the move to a chapter position, direct TOC navigation, resolved export membership, and the withdrawal queue. Check Search and Recent on their normal refresh paths. Return for a scope decision if the work requires changing document identities or routes or changing how Publish consumes the queue. The accepted local Book Publication release supplies the starting point for this work.

### 1. Author The Book Editions

- [x] Add the existing TOC to the opening order at Root, with Root placements on both sides of it and back matter after the chapters. Save the edition choice through normal page authoring and carry it in Book management metadata. Living Memory's Working Tree was updated in place with its existing TOC and chapter placements.
- [x] Implement the Edition action, modal, and List and Tree suffixes.
- [x] Accept desktop authoring after the user's testing, covering the edition choices, suffixes, placement, and reset to **Both** when moving a single-edition page to a chapter position. The user reported creating and previewing the two single-edition prefaces. Individual results for the broader authoring walkthrough were not recorded.

### 2. Prepare Web Output And Verify Export Selection

- [x] Prepare the web edition through Working generation and resolve the export selection from the same Tree. Living Memory's Working TOC and the resolved export order both contain the TOC followed by six ready chapters. The existing HTML snapshot wrote the six selected collection pages and one media file to a temporary Projects workspace. The exact TOC rebuild queued its Working output.
- [x] Accept the web navigation and edition selection after the user's testing. The separate withdrawal trial remains with Book Publication. [Book Publication](Book_Publication.md#live-deployment-and-withdrawal-test)

Living Memory's two prefaces behaved as expected in the user's live preview. The prepared web sequence starts with the TOC and the **Web only** preface. The resolved export sequence starts with the **Export only** preface and the TOC. In the Book's selection mode, **All → Export…** included both prefaces and produced the snapshot's flat A–Z index. The user accepted Collection Export for selected documents and left whole-Book export to a separate delivery.

### 3. Code Review

- [x] Review authoring, shared ordering, browser and server ownership, web rendering, export selection, and the publication handoff. Record the findings and resolutions from the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).

- [x] Refresh retained TOC navigation after a Book change. TOC-origin links and arrows carry the host identity. On that host, the toolbar uses the latest generated TOC order. Links from Manage List and Tree still supply their own reading order. [Reader projection](../../../docs-viewer/runtime/js/shared/docs-viewer-document-controller.js#L27)
- [x] Report completed source writes when a Book Save fails during persistence. Save reports the failing phase and returns only the edition records it wrote. The browser applies the new order after its write completes. [Book Save](../../../docs-viewer/services/docs_book_tree.py#L187)
- [x] Skip the Links refresh during edition-only saves and edition resets. Selected generation uses saved relationship inputs for rendering and carries the existing eligibility and media effects into publication preparation. [Selected generation](../../../docs-viewer/services/docs_book_tree.py#L210)

**Redundancy and defensive behavior.** Manage reuses one loaded Book manifest for the Tree and Edition action. The write boundary checks the configured owner, exact source identity, confined paths, and that every page has one valid placement with the ordinary host in the opening order. Unchanged saves and moves skip writes. Order changes render the exact host when the visible TOC or reading sequence changes. Working owns edition eligibility and hands completed units to the existing Publish queue. The link-only TOC path supports prepared host bytes from before the runtime and data cutover. Living Memory's prepared host now carries the full sequence.

**Evidence.** The prepared Book manifest, Search index and Recent list include the **Web only** preface and omit the **Export only** preface. After the review fixes, changed-file lint, site projection, site validation and whitespace checks passed. The persistence failure path was checked by source review. The user reported finishing testing and approved closeout. The user did not report separate results for an induced write failure or a published-page withdrawal.

### 4. Closeout

- [x] Record the user's acceptance and update the durable guidance for [Book curation and editions](../Sub_Scope_Index_Architecture.md#book-editions), [source ownership](../Source_Organisation.md#book-source-and-provenance), [TOC generation](../Builder.md#book-table-of-contents), and [reader navigation](../Docs_Viewer_Runtime.md#collection-previous-and-next).

Keep this delivery in Reviews while it holds the Export Book proposal. Move that scope into its own delivery when picked up, then retire this document through the ordinary manual archive.

## Follow-On Book Export

**Collection Export** creates a selected-document HTML snapshot for offline reading. Its `portable.html` is a text-first view with image placeholders and chapter-level link destinations. [Collection Export](../Export.md)

Scope a separate **Export Book** workflow for PDF and EPUB as a follow-on delivery. The author selects the Book and a format. Both formats use the same ordered selection of ready export documents from the Book Tree, including the cover, opening pages on either side of the authored TOC, chapters, and back matter.

Use the Working document bodies and referenced media as export inputs. Reuse document loading, media preparation, and link resolution from the existing exporter where they fit. Keep document IDs and heading destinations available until the selected format can turn them into local links. The Book Tree orders authored documents. Each format controls how those documents are presented.

- **PDF.** Assemble one print-ready HTML document with its images, cover layout, and page breaks. Give chapters and linked headings unique anchors and resolve TOC and cross-chapter links before rendering. Playwright was used in an earlier experiment and is a candidate to evaluate. Verify that the links stay clickable in the generated PDF. [Playwright PDF API](https://playwright.dev/python/docs/api/class-page#page-pdf)
- **EPUB.** Package the same documents as XHTML with their media and package metadata. Use Book Tree order for the EPUB reading order and derive reader navigation from the same chapter entries that render the authored TOC. Resolve chapter and heading links to the packaged files and fragments. [EPUB 3.3](https://www.w3.org/TR/epub-33/)

When this delivery is picked up, choose the first format and evaluate a representative cover, illustrated chapter, and cross-chapter link. For a site download, attach the finished PDF with **Add file** on the web-only introduction and use the existing Save and Publish workflow. Confirm attachment support separately if EPUB is also offered on the site. [Add a new image or download](../Docs_Images_And_Assets.md#add-a-new-image-or-download)
