---
draft: false
doc_id: d-20260728-113139-763354
title: Sub-Scope Index Architecture
added_date: "2026-07-28 11:31:39"
last_updated: "2026-11-18"
summary: Collection host ownership, exact actions, Book placement, editions and publication.
parent_id: d-20260424-000000-50b63f
---
# Collections and Books

A configured collection owns its document and media storage. The ordinary Index host provides an entry to that collection, and each member opens through the common reader. Manage supplies the authoring controls. [Reader browsing and return](Reader_Discovery_And_Return.md#collection-list-preparation) · [Report composition](Reports.md)

## Collection Identity

[Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) binds each exact `collection` to its `report_host_doc_id`, display title, icon and storage settings. The host is an ordinary document with its own source and place in `index-order.json`. A typical host declares `docs_collection` and the configured collection in its body. Living Memory uses the ordinary host as its TOC. The Manage curation pane resolves either that configured host or a book member to the same curated Book. [Book pane](../../docs-viewer/runtime/js/management/docs-viewer-book-pane.js) · [Report source](Reports.md#source-contract)

Ordinary document targets use `{doc_id}`. Collection targets use the exact `{collection, doc_id}`, also expressed in the reader URL. Selection carries the configured collection and explicit checked document IDs. The displayed document supplies document actions. The collection host supplies its own actions and is the destination of a member's **index** shortcut. [Source organisation](Source_Organisation.md#document-and-collection-identity) · [Runtime action policy](Docs_Viewer_Runtime.md#document-action-policy)

## Reachability Is Not Ownership

Moving the host in the ordinary Index changes its placement. The collection still owns its existing sources, member IDs, media and manifest. Draft or inherited exclusion on the configured host withholds the collection's public documents and manifest entries. Working keeps the collection usable. An ordinary Delete removes its selected ordinary source subtree. Any collection withdrawals follow the host eligibility change, while removing member sources requires a collection-owned operation. The report implementation remains registered independently of which document uses it. [Eligibility and queue](Builder.md#publish-preparation) · [Host reparenting evidence](../deliveries/Sub_Scope_Report_Reparenting.md)

## Standard collection actions

The shared `docs_collection` report owns the list, while the configured provider opens the exact document by ID. Manage supplies one explicit contribution for selection, applicable collection actions and updates from completed writes. **Select** changes the checked set. **Collection Actions** offers workflows appropriate to that owner, including New, Import, Prepare package and Export where enabled. Export and Prepare package use exact checked IDs. Import chooses the displayed collection for an ordinary incoming file, while a trusted returned package retains its manifest-owned destination. Confirmed document Delete uses the displayed exact document. Book additionally supports a confirmed batch in its pane. [Manage contribution](../../docs-viewer/runtime/js/management/docs-viewer-management-collection-default-contribution.js) · [Docs Import](Docs_Import.md) · [Prepare package](Document_Packages.md) · [Media cleanup](Media_And_Asset_Handling.md#document-delete-media-cleanup)

## Flat Book Collections

**Library** is a configured `book-collection` with a flat list and its own Index search scope. It holds independent source documents and can supply working copies to a curated Book. Public paginates the Library list. Manage offers a pagination toggle and starts with pagination off. **Living Memory** is the configured `curated-book`. Its curated order is separate from the flat storage. [Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) · [Reader discovery](Reader_Discovery_And_Return.md#collection-list-preparation)

### Book Curation In Manage

The desktop Book pane follows the configured host or page. **List** searches the full Working inventory. **Tree** shows **Opening pages** (including the ordinary TOC), Root chapters, Parts, Sections and **Back matter**. Use **Position…** to place the selected page. The Tree owns heading controls and the placement for new drafts. To bring a private Section to the top of the Tree, select its heading and choose **Edit section → Placement → Before Opening pages**. Sections placed there follow their saved sibling order in the Tree and Manage’s previous/next navigation. Choose **Top level** to return a Section to the main group of headings, or select a Part to nest it. A Book page’s **Table of contents** control opens the ordinary host. Write the host’s prose as ordinary Markdown and place `[[toc]]` where its generated web list belongs. [TOC authoring](Builder.md#book-table-of-contents)

The collection's `working/source/collections/<collection>/index-order.json` supplies `front`, `root`, `tree` and `back`. The ordinary TOC host appears exactly once in `front`. A Part can contain chapters directly and contain Sections. A Section holds private working pages. A top-level Section with `before_opening: true` appears above **Opening pages** in Manage. **Book settings → Link Part headings to their first ready document** saves `link_part_headings` in the order file. Working uses the first ready web chapter directly under an eligible Part. The heading represents that chapter and the remaining chapter links follow below it. [Placement and Save](../../docs-viewer/services/docs_book_tree.py) · [TOC projection](../../docs-viewer/services/docs_book_toc.py)

**Library → Select → Actions → Copy to Book…** copies the chosen sources as new drafts at Root or in a selected Section, adopts their owned body media and keeps Library ID/title provenance. The picker can also create a draft chapter at that placement or add the selected provenance records to an existing chapter. Clearing Library's copied indicators is a separate action. New, Import, Copy and Delete supply their saved placement changes to generation. [Book copy service](../../docs-viewer/services/docs_book_copy.py) · [Source and provenance](Source_Organisation.md#book-source-and-provenance)

### Book Editions

**Edit document → Edition…** sets **Both**, **Web only** or **Export only** on a front- or back-matter page. An omitted `book_edition` means Both. Moving a single-edition page out of front or back matter resets it to Both, including a move into a Section. Draft is the separate readiness flag.

| Saved placement | Web edition | Resolved export order |
| --- | --- | --- |
| Ready opening or back matter | Both or Web only | Both or Export only |
| Ready Root chapters and chapters directly under a Part | Included | Included |
| Sections, including those inside Parts | Private in Manage | Private in Manage |
| Draft pages | Private in Manage | Private in Manage |

For example, move a ready Root chapter into a Section. Book Save persists the placement, Working recomputes the web manifest and TOC, and the change queues that page's withdrawal. The page retains its ID, source and Draft status. Moving it back to Root or directly under a Part restores its web membership when the host is eligible. **Publish** applies those queued changes. **Refresh Search and Recent** applies edition eligibility to discovery when explicitly run. The generated web reading sequence includes eligible pages before the TOC and after the chapters. [Edition and reading-order owner](../../docs-viewer/services/docs_book_toc.py) · [Working publication](Builder.md#publish-preparation)

**Collection Export** makes an HTML snapshot of the checked collection documents and can produce a flat A–Z index. The ordinary TOC host is outside that checked selection. The Book's resolved export order is a separate input for the proposed whole-Book PDF/EPUB delivery. [Collection Export](Export.md#input-and-eligibility) · [Export Book proposal](../_working/Export_Book.md)

## Catalogue Work Records

Catalogue's configured host is the entry to the Work documents. Studio owns its canonical Work and Gallery data. Refresh selects Working records and Regenerate owns Work-document adoption and deletion. The collection reader consumes the exact Catalogue manifest and adopted by-ID payloads. [Catalogue lifecycle](Catalogue_Save_And_Refresh.md) · [Catalogue browsing](Reader_Discovery_And_Return.md#catalogue-collection-browsing)

[Design decisions](../design/Collections_Books_And_Reports.md) · [Host and Book delivery evidence](../deliveries/Collections_Books_And_Reports_Review.md)
