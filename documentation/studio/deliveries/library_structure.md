---
draft: true
doc_id: d-20260526-000000-04ce37
title: library structure
added_date: "2026-05-26 00:00:00"
last_updated: "2026-11-11"
---
# library structure

This delivery adds private Book curation after the conversion to a flat Library collection. [Planned Features](../Planned_Features.md) · [Book Collections](book-collection.md)

Complete in Working on 2026-11-11. The user reviewed the desktop flow in Manage and approved closeout after the final UI refinements. Revisit the editorial workflow after more content has been copied into Book. [Collection behavior](../Sub_Scope_Index_Architecture.md#book-curation-in-manage) · [Source and provenance](../Source_Organisation.md#book-source-and-provenance)

## Requirements

Library is the permanent public collection of source fragments. Continue importing and cleaning up documents there. In Manage, copy fragments into a new, initially empty `book` collection. The same batch can create a blank chapter, add sources to an existing chapter or leave the copies ready for manual chapter import. Edit and save the chapter before deleting the temporary copies. Library records whether each original has ever been copied. Each chapter keeps its own record of the Library fragments, including their titles at the time of copying.

Book has one section tree and an ordered document list inside its collection host. Add the Book host as an ordinary entry for Manage and put its ID in `working/source/unpublishable.json` before the first generation. The excluded host keeps the whole Book collection private. Keep the tree and editorial metadata in Working. The main Index retains its current layout and behaviour. Enable Book document media and leave Book out of site Search and Recent. A publishable Book or a downloadable edition is a separate decision. [Collection configuration and publication](../Source_Organisation.md#collection-deliveries)

## Tree, Files And Copy Mechanics

The Book tree contains Sections and optional Parts that group Sections. Both kinds of heading have a stable ID and an ordered list of Book document IDs. A Part can hold its own documents, such as a preface, before its child Sections in the book’s reading order. Documents stay in one flat folder. **Unfiled** shows documents without a placement. Selecting a heading lists the documents directly assigned to it in saved order. The reader gets titles and links from the existing Book inventory. Deleting a Book document removes its placement. Moving a placement changes the tree order.

The Book workflow uses these files under `$DOTLINEFORM_DOCS_BASE_DIR`. [Docs workspace layout](../Source_Organisation.md#storage-and-roles)

| Role | Path |
| --- | --- |
| Existing Library fragments | `working/source/collections/library/documents/<doc_id>.md` |
| Private Library **Copied to Book** flags | `working/source/collections/library/copied-to-book.json` |
| Book working copies and chapters | `working/source/collections/book/documents/<doc_id>.md` |
| Book's authored tree | `working/source/collections/book/index-order.json` |
| Book's generated Manage tree | `working/generated/collections/book/documents/index-tree.json` |
| Book's generated document inventory and payloads | `working/generated/collections/book/documents/{manage-manifest.json,by-id/}` |
| Book's owned body media | `working/assets/media/collections/book/<type>/<doc_id>/` |
| Book's assigned thumbnails | `working/assets/media/collections/book/thumbs/<doc_id>-thumb.webp` |

The copy operation accepts exact selected Library IDs and targets Book. For each source it reads the canonical Markdown, allocates a fresh Book `doc_id`, copies the referenced managed body media to that ID, and rewrites the copied body’s managed media references. It creates an independent Book document and finishes its Working generation before reporting it copied. Ordinary document links can be removed or replaced during editing. Copies start unfiled. Use Book’s existing thumbnail action for finished chapters when suitable images are available. The browser supplies the selection and displays the completed results. Python owns configured file access, identity allocation, selected media copies, source writes and generation.

Each working copy stores its original Library ID and title together in `copied_from_library`, so the source details are available when the user imports a chapter later. After a copy succeeds, set **Copied to Book** for its original Library ID. The private flag file keeps this history with Library without editing fragment Markdown or dates. The flag stays set when the Book copy is deleted. **Clear Copied to Book** removes the selected flags from `copied-to-book.json` independently of the Book copies and chapter source records.

The copy batch has three modes. Each uses the same copy operation.

- **New chapter.** Supply a chapter title. Create a Book document with a fresh chapter ID, a title heading and its `library_sources` already filled in from the completed copies.
- **Existing chapter.** Choose the Book chapter to receive the sources. Append the completed copies’ source records in batch order, keeping the existing chapter body, source order and saved title for any Library ID already listed.
- **Copy only.** Create the working copies with their source details. This is the route for using **Import doc** to create a chapter from an edited file later.

Book documents created through **Collection Actions → New doc…** or **Copy to Book** start with `draft: false` and their title as the first Markdown heading. The Book host exclusion governs publication for these documents.

**New doc…** appends the document to the selected Part or Section before opening Source. From **Unfiled**, it creates an unfiled document.

The chapter stores its optional `library_sources` array in Markdown front matter. Each entry holds the original Library ID and the title captured when the fragment was copied.

```yaml
library_sources:
  - doc_id: d-20261101-104500-a1b2c3
    title: "Biological and physical memories"
  - doc_id: d-20261103-141200-d4e5f6
    title: "Attractor-network Memory"
```

The list records the fragments gathered for the chapter. After editing, remove any that did not contribute if you want the list to reflect the final text. Manage displays the saved titles and IDs directly, so renamed, combined or deleted Library documents remain understandable without a lookup. The flag and both provenance fields are for Manage.

## Compile A Chapter In Manage

1. **Copy the fragments and choose a chapter.** In Library, choose **Select**, check the cleaned fragments and run **Copy to Book**. Choose **New chapter** and enter its title, or choose **Existing chapter** to add another batch. The operation copies the fragments and records their original IDs and titles on the chapter.
2. **Open the chapter and working copies.** In Book, find the copies and any new chapter in **Unfiled**. If the chapter already has a placement, open its Part or Section. Open the chapter’s **Edit document** action to work in Source. Keep the working copies until the chapter has been saved and checked.
3. **Copy the source bodies.** Open each working copy’s Markdown source and paste the body or the relevant passages into the chapter, including the media references you want to retain. Leave each copy’s front matter in place and keep the chapter’s own ID and front matter. Edit the combined text, headings and links into a coherent chapter.
4. **Save the chapter while the copies still exist. The existing Source Save workflow already adopts referenced media into the chapter’s own storage.** On Save, it copies the referenced document-owned images, SVGs, files and HTML companions from the working copies into the chapter’s media folders and rewrites the saved paths. It needs the original bytes at that point. If different files have the same destination filename, resolve the reported conflict before deleting either copy. An assigned thumbnail is separate from body media, so choose one for the chapter if needed. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)
5. **Review the source list.** If the chapter used only part of the batch, select it in the Book report and open **Library sources…** from the toolbar to remove unused entries. Place the chapter in its section and set its reading order when ready.
6. **Review and remove the copies.** Open the saved chapter and check its text and retained media. Back in the Book report, use **Select** to check the temporary copies, then choose **Actions → Delete selected…** and confirm the batch. Delete removes the checked Book documents, their section placements and their own media. The saved chapter uses its own adopted files and retains its Library source IDs and titles. [Document Delete media cleanup](../Media_And_Asset_Handling.md#document-delete-media-cleanup)

## Compile A Chapter With ChatGPT

1. Use **Copy only** when the returned file will become a new chapter through **Import doc**. In Book, choose **Select**, check the working copies and use **Collection Actions → Prepare package**. Choose **Document content** with Markdown content and JSON or JSONL output. Check the package result for omissions or truncation before handing it over. [Prepare package](../Package_Prepare.md) · [Package content formats and limits](../Package_Prepare_Profiles.md)
2. Give ChatGPT the package and editorial brief. Ask for one new chapter as a Markdown file. If useful, ask for a separate list of the input documents it used so you can check the sources yourself. The package is an editorial handoff. Its rendered Markdown may transform media references, so keep the Book copies available as the source for any original media you want in the chapter.
3. From Book’s **Collection Actions**, use **Import doc** to create a new Book document from the returned Markdown. Select it and use **Library sources…** to add the original IDs and titles from the working copies. Ordinary Markdown import ignores custom incoming front matter. If you already prepared a chapter with **New chapter** or **Existing chapter**, paste the returned Markdown body into that chapter’s Source editor to keep its ID and source list. [Ordinary Markdown import](../Docs_Import_Architecture.md#normalized-document-intent)
4. Review the chapter in Source. Restore any wanted media references from the working copies, edit and save while the media still exists, then place the chapter in the section tree. Check the saved chapter before deleting the temporary copies, as in the Manage workflow.

## UI Design After The Mechanics

The desktop Book tree uses the main Index’s type size, pills and disclosure arrows. Click a Part or Section title to see its own documents. Use the arrow beside a Part to expand or collapse its Sections. The tree toolbar offers **Unfiled**, **New section**, **New part**, and a pencil for the selected heading. On wide screens the tree uses some of the space to its left, keeping the document list in place.

The **Position…** icon in the Book selection toolbar opens the same searchable modal as the main Index. Choose **Before** or **After** an existing document to place the selection beside it, or **Inside (at end)** a Part or Section to append the selection. Choose **Unfiled** with **Inside** to remove the placement. A batch moves in the order shown in the list. When a document is opened from a heading, Previous and Next follow that heading’s document order and Back returns to the list. [Main Index Position](../Reorder_Docs_Delivery.md)

In Manage, the Library selection toolbar uses `dlf-doc.svg` for **Copy to Book** and the same icon with a diagonal strike for **Clear Copied to Book**. The clear control appears when the selection includes flagged documents. The saved **Copied to Book** row indicator uses the plain icon in the left gutter. The copy modal offers **New chapter**, **Existing chapter** and **Copy only**. Show a title field for a new chapter or a chapter picker for an existing one. In the Book report, **Library sources…** opens a modal for one selected chapter. It displays saved source records and offers additional records from the working copies. The user can add records after import or remove unused entries after editing. **Prepare package** and **Import doc** are in the existing Book Collection Actions.

On tablet and phone, use a compact heading picker above a full-width list when the columns become cramped. Let the toolbar wrap and make row actions reachable by touch. Review only the Book workflow at narrow widths.

## Readiness — 2026-11-11

**Ready for the tree and copy mechanics.** The configured Working workspace contains Library source and generated inventory. Book is a new collection with its own ordinary report host, flat document and media owners, and one Working-only tree. The existing collection creation model supports this as a design-time registration. Before generating the host or accepting the first copy, set its exclusion and initialise Book’s empty Working manifests and tree. Targeted generation merges into the saved management manifest and the public eligibility owner reads the saved public membership. Initial setup supplies these inputs once. [Collection deliveries](../Source_Organisation.md#collection-deliveries) · [Prior collection setup](book-collection.md)

- **Publication and discovery.** The host exclusion keeps the host and Book document rows out of public navigation and eligibility, including their media uploads. Set `include_in_site_search: false` for Book. Today browser configuration lists every registered collection, so the public settings can still name `book` even with an excluded host and no public Book content. Check the actual public selection for the host, chapter payloads and media, and keep the tree and provenance in Working. Hiding the registration itself would be a separate visibility requirement. [Browser configuration projection](../../../docs-viewer/build/docs_builder/browser_config.py) · [Public eligibility projection](../../../docs-viewer/services/docs_publication_metadata.py)
- **Tree and report.** Book owns its section order. Use the saved collection inventory to resolve titles and links and keep placement distinct from flat document membership. The existing named-collection Delete takes one document at a time. Its Book-specific follow-through removes the deleted ID from the tree alongside the existing document and media cleanup. The later browser work owns section choice, ordering, checked rows and the chapter destination. Show the tree in Book and **Copy to Book** in Library. [Collection report ownership](../Sub_Scope_Index_Architecture.md#shared-report-ownership) · [Document Delete](../Media_And_Asset_Handling.md#document-delete-media-cleanup)
- **Copy and chapter persistence.** One operation takes the exact Library selection and Book chapter intent. Python resolves the two configured owners, allocates new IDs, prepares selected body media using the existing adoption rules, and persists the completed copies, chapter changes and flags. Carry the parsed source and completed copy records into targeted generation. The media helper currently takes a resolved document target. Reuse its selected-file work with the prepared Book identity without creating a throwaway saved document. Retain the chapter body and its saved records on append. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)
- **Structured front matter.** The shared parser handles scalar fields and the Summary block today. A direct read-only diagnostic confirmed that the proposed two-entry `library_sources` block is rejected by the strict reader as duplicate keys. Add bounded parse and write support for the Book provenance fields in their existing shared owner so Source Save, Build and package preparation can read the same chapter. Validate the ID/title structure at authoring. A missing Library document remains valid provenance. This work is separate from accepting custom fields from an external file. [Current front matter owner](../../../docs-viewer/services/docs_front_matter.py)
- **Package and import.** Existing Prepare package takes the exact configured collection and checked IDs. Ordinary **Import doc** creates a new document in its invoking collection. Book can use both with the **Document content** profile and the ordinary Markdown importer. Returned-package import and Docs Review remain follow-on work. [Prepare package](../Package_Prepare.md#selection-rules) · [Ordinary import](../Docs_Import_Architecture.md#normalized-document-intent)

The credible risks are exposing Book content through a shared projection, losing existing chapter fields during a provenance write, and retaining media links into a working copy that will be deleted. Raise scope if the mechanics require general cross-collection copy, general YAML support, a change to ordinary Import or a new Publish policy. The user approved using real Working for the mechanics check. Readiness itself used source and configuration inspection and the direct parser diagnostic. It made no changes to the live workspace or public artifacts.

| Risk | Proposed evidence and cost |
| --- | --- |
| Shared parsing and collection registration | Review the changed owners and generated config, run scoped Python lint and whitespace checks. Where canonical public browser configuration changes, run the existing site projection, consistency check and site validation and inspect the tracked delta. Allow seconds to a few minutes. Projection writes tracked runtime copies locally. |
| Copy, provenance, media and public eligibility | In real Working, choose a small batch of Library documents with body media. Exercise all three copy modes, including an already recorded Library ID, and inspect the chapter source, manifest, tree, flags and selected public effects. Save a chapter using media from a copy, delete that copy and check that the chapter still renders its owned media. Use the existing package and ordinary Markdown import with one copy-only batch. Allow roughly 15–30 minutes of manual work. This writes Book source, generated files and media, the selected Library copy flags, and a local package. |
| Report UI after the mechanics | User review of section navigation, copy destination selection, the flag and source editing on desktop, plus a brief narrow-width check. No automated browser run is selected. |

Use the existing commands and workflows for these checks. New executable tests or fixtures would need their own specification. [Development Checklist](../Development_Checklist.md#verification-gate)

## Delivery Steps

- [x] **Readiness.** Confirmed the implementation boundary and recorded the proposed verification budget above.
- [x] **Tree and copy mechanics.** Registered Book, built its excluded host in Working and established the single authored and generated tree. Exercised all three copy modes, New, Source Save, Delete, Prepare package and ordinary Import doc before wiring the report controls.
- [x] **UI design and implementation.** Added the Book tree, Part and Section editing, shared Position modal, Library copy modal and flag icon, and chapter sources modal. The user refined the desktop layout and interactions in Manage. The narrow layout uses a heading picker.
- [x] **Code review.** Traced the change under the [Development Checklist](../Development_Checklist.md#redundancy-and-defensive-behavior-review). See the review record below.
- [x] **Closeout.** Recorded mechanics and desktop acceptance, with narrow widths and live batch Delete left for normal use. Transferred the current behavior to the durable collection, source and media owners.

### Implementation And Review Record

Book host `d-20261111-120000-5af14d` sits after Library in the Working Index and is in `unpublishable.json`. In real Working, the three copy modes allocated fresh IDs, appended a second batch without duplicating the first source, and recorded the source titles. A chapter Save adopted a copied SVG. Delete removed the working copy's tree placement and owned SVG while the chapter kept its SVG and source records. A non-draft chapter stayed out of Book’s public manifest and the upload queue. New, ordinary Markdown import and saving source records after import worked. Document content package preparation succeeded with a temporary Projects output root because the sandbox could not write the configured Data Sharing directory.

The redundancy review traced the selected-copy, no-new-source append, placement and Delete paths. The copy uses one resolved workspace and one targeted Book generation per batch. It supplies the prepared Book identity to the existing media helper without creating a temporary source. The parser owns the two structured fields, and formatting carries validated records forward. The browser reuses the current Book inventory for placement and source selection, loads chapter destinations only when needed from Library, and applies committed records to retained lists. Retained checks bind requests to their configured files and exact IDs, validate the submitted tree and provenance structure, and verify selected media writes. Copy reports the phase and completed effects if persistence fails. Public projection has the existing collection descriptor and shared report extension point, while the Book controls and tree data load through Manage.

Changed-file Python and JavaScript lint, whitespace, the Book build dry run, site projection consistency and site validation passed during implementation. The eight verification Book documents were removed through Delete and the tree was reset at the end of that exercise. The two Library copy flags were retained as history. Delete queued removal entries for those verification documents, with no Book upload selected.

The Book report sends the checked IDs to the existing Delete service after one confirmation. The service resolves each selected Book source within the configured folder before the first removal, carries those paths into one tree update and one targeted generation, and returns the removals to the report. A dry run with two existing Book documents returned exactly the two requested IDs. Live batch Delete can be confirmed through normal use.

The shared Position modal receives its valid destinations from each Index. Book uses the loaded tree and inventory to compute the move in the browser and sends one tree save when placements change. The server validates that submitted IDs belong to Book and that each document has at most one placement across Parts and Sections. Delete removes placements from both kinds of heading. The Working cutover added an empty document list to the existing Part and verified that the authored and generated trees agree. Focused lint and a Book build dry run passed.

Desktop feedback covered the tree and report layout, Part and Section selection, document creation from the collection menu, and the Unfiled view. The user approved closeout after these refinements. A separate narrow-width pass and an editorial package round trip with real chapter material remain for normal use. Closeout updated the repository documentation and reused the implementation checks.

## Follow-On: Review A Revised Book

Package a set of existing Book chapters for ChatGPT to suggest links between chapters, write transitions and propose a revised section tree. Carry the existing Book document IDs through the round trip and return the proposed section order alongside the chapter edits. Use Docs Review, the local package preview, to read the revised chapters together, follow their links and try the proposed order before choosing what to apply to Working. Revisit the review and return flows against the current collection, media and publication boundaries when this work is scoped. [Docs Review](../Docs_Review.md)

For that round trip, decide which Book front matter the package should carry and which fields the return path may accept. Start by considering `library_sources` so the saved IDs and titles can travel with a chapter. Keep document identity and collection ownership tied to the exported selection, and review section order as a proposal before applying it to the Book tree. This follow-on has its own scope. [Import field handling](../Docs_Import_Architecture.md#normalized-document-intent)
