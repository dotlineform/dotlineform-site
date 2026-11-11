---
draft: true
doc_id: d-20260526-000000-04ce37
title: library structure
added_date: "2026-05-26 00:00:00"
last_updated: "2026-11-11"
---
# library structure

This proposed delivery follows the completed conversion to a flat Library collection. [Planned Features](../Planned_Features.md) · [Book Collections](book-collection.md)

## Requirements

Library is the permanent public collection of source fragments. Continue importing and cleaning up documents there. In Manage, copy fragments into a new, initially empty `book` collection. The same batch can create a blank chapter, add sources to an existing chapter or leave the copies ready for manual chapter import. Edit and save the chapter before deleting the temporary copies. Library records whether each original has ever been copied. Each chapter keeps its own record of the Library fragments, including their titles at the time of copying.

Book has one section tree and an ordered document list inside its collection host. Add the Book host as an ordinary entry for Manage and put its ID in `working/source/unpublishable.json` before the first generation. The excluded host keeps the whole Book collection private. Keep the tree and editorial metadata in Working. The main Index retains its current layout and behaviour. Enable Book document media and leave Book out of site Search and Recent. A publishable Book or a downloadable edition is a separate decision. [Collection configuration and publication](../Source_Organisation.md#collection-deliveries)

## Tree, Files And Copy Mechanics

The Book tree shows section headings and, when needed, Parts that group sections. Documents stay in one flat folder. The tree stores stable heading IDs and ordered Book document IDs. **All documents** includes unfiled copies and new chapters. Selecting a section lists its documents in saved order. The reader gets titles and links from the existing Book inventory. Deleting a Book document removes its placement. Moving a placement changes the tree order. There is one tree and no map picker.

The proposed files fit under `$DOTLINEFORM_DOCS_BASE_DIR` as follows. [Docs workspace layout](../Source_Organisation.md#storage-and-roles)

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

The copy operation accepts exact selected Library IDs and targets Book. For each source it reads the canonical Markdown, allocates a fresh Book `doc_id`, copies the referenced managed media and any assigned thumbnail to that ID, and rewrites the copied body’s managed media references. It creates an independent Book document and finishes its Working generation before reporting it copied. Ordinary document links can be removed or replaced during editing. Copies start unfiled. The browser supplies the selection and displays the completed results. Python owns configured file access, identity allocation, selected media copies, source writes and generation.

Each working copy stores its original Library ID and title together in `copied_from_library`, so the source details are available when the user imports a chapter later. After a copy succeeds, set **Copied to Book** for its original Library ID. The proposed private flag file keeps this history with Library without editing fragment Markdown or dates. The flag stays set when the Book copy is deleted.

The copy batch has three modes. Each uses the same copy operation.

- **New chapter.** Supply a chapter title. Create a blank Book document with a fresh chapter ID and its `library_sources` already filled in from the completed copies.
- **Existing chapter.** Choose the Book chapter to receive the sources. Append the completed copies’ source records in batch order, keeping the existing chapter body, source order and saved title for any Library ID already listed.
- **Copy only.** Create the working copies with their source details. This is the route for using **Import doc** to create a chapter from an edited file later.

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
2. **Open the chapter and working copies.** In Book, find them in **All documents**. Open the chapter’s **Edit document** action to work in Source. Keep the working copies until the chapter has been saved and checked.
3. **Copy the source bodies.** Open each working copy’s Markdown source and paste the body or the relevant passages into the chapter, including the media references you want to retain. Leave each copy’s front matter in place and keep the chapter’s own ID and front matter. Edit the combined text, headings and links into a coherent chapter.
4. **Save the chapter while the copies still exist. The existing Source Save workflow already adopts referenced media into the chapter’s own storage.** On Save, it copies the referenced document-owned images, SVGs, files and HTML companions from the working copies into the chapter’s media folders and rewrites the saved paths. It needs the original bytes at that point. If different files have the same destination filename, resolve the reported conflict before deleting either copy. An assigned thumbnail is separate from body media, so choose one for the chapter if needed. [Source Save media adoption](../Media_And_Asset_Handling.md#source-save-media-adoption)
5. **Review the source list.** If the chapter used only part of the batch, select it in the Book report and open **Library sources…** from the toolbar to remove unused entries. Place the chapter in its section and set its reading order when ready.
6. **Review and remove the copies.** Open the saved chapter, check its text and retained media, then delete the temporary Book copies. Delete removes the copies’ own media. The saved chapter uses its own adopted files and retains its Library source IDs and titles. [Document Delete media cleanup](../Media_And_Asset_Handling.md#document-delete-media-cleanup)

## Compile A Chapter With ChatGPT

1. Use **Copy only** when the returned file will become a new chapter through **Import doc**. In Book, choose **Select**, check the working copies and use **Collection Actions → Prepare package**. Choose **Document content** with Markdown content and JSON or JSONL output. Check the package result for omissions or truncation before handing it over. [Prepare package](../Package_Prepare.md) · [Package content formats and limits](../Package_Prepare_Profiles.md)
2. Give ChatGPT the package and editorial brief. Ask for one new chapter as a Markdown file. If useful, ask for a separate list of the input documents it used so you can check the sources yourself. The package is an editorial handoff. Its rendered Markdown may transform media references, so keep the Book copies available as the source for any original media you want in the chapter.
3. From Book’s **Collection Actions**, use **Import doc** to create a new Book document from the returned Markdown. Select it and use **Library sources…** to add the original IDs and titles from the working copies. Ordinary Markdown import ignores custom incoming front matter. If you already prepared a chapter with **New chapter** or **Existing chapter**, paste the returned Markdown body into that chapter’s Source editor to keep its ID and source list. [Ordinary Markdown import](../Docs_Import_Architecture.md#normalized-document-intent)
4. Review the chapter in Source. Restore any wanted media references from the working copies, edit and save while the media still exists, then place the chapter in the section tree. Check the saved chapter before deleting the temporary copies, as in the Manage workflow.

## UI Design After The Mechanics

Design the controls after the single-tree and copy workflows are working. The desktop starting point is a section index taking about a quarter of the Book host, with the selected list beside it. **All documents** gives access to unfiled material. The Book report needs controls to create and name sections, place documents and set their order. Use the existing **Position** interaction as the reference for ordering documents within a section. When a document is opened from a section, Previous and Next follow that section’s order and Back returns to the list. [Existing Position interaction](../Reorder_Docs_Delivery.md)

The Library report needs **Copy to Book** for checked documents and an icon that shows the saved **Copied to Book** flag. The copy modal offers **New chapter**, **Existing chapter** and **Copy only**. Show a title field for a new chapter or a chapter picker for an existing one. In the Book report, try **Library sources…** as a toolbar button that opens a modal for one selected chapter. Display saved source records from the chapter and offer additional records from the working copies. The user can add records after import or remove unused entries after editing. Keep **Prepare package** and **Import doc** in the existing Book Collection Actions.

On tablet and phone, start with a compact section picker above a full-width list when the columns become cramped. Let the toolbar wrap and make row actions reachable by touch. Review only the Book workflow at narrow widths.

## Delivery Steps

- [ ] **Readiness.** Confirm registration and exclusion for Book, the exact tree and copy owners, reuse of managed media adoption and the existing package and import entry points. Agree focused verification before implementation.
- [ ] **Tree and copy mechanics.** Register the empty private Book collection. Establish the single authored and generated tree, initially editable directly for verification. Implement exact selected Library-to-Book copying with fresh IDs, media ownership, source ID and title snapshots, and durable Library flags. Support creating a chapter with the batch, appending distinct source records to an existing chapter, and copying only. Confirm existing New, Source Save, Delete, Prepare package and ordinary Import doc work against Book before designing new UI.
- [ ] **UI design and implementation.** Review the desktop workflow after the mechanics are working, then design and add the Book section controls, Library copy action and flag icon, and the chapter sources modal. Include the small-screen layout for the Book report.
- [ ] **Review and closeout.** Apply the [Development Checklist](../Development_Checklist.md#redundancy-and-defensive-behavior-review). Verify a chapter created with a batch, an additional batch with an already recorded source, and a copy-only batch exported and followed by manual chapter import. Check that adopted media and saved source IDs and titles survive deletion of the working copies, Library retains its copy flags, and Book stays out of public output. Record desktop acceptance and the brief narrow-width check before closeout.

## Follow-On: Review A Revised Book

Package a set of existing Book chapters for ChatGPT to suggest links between chapters, write transitions and propose a revised section tree. Carry the existing Book document IDs through the round trip and return the proposed section order alongside the chapter edits. Use Docs Review, the local package preview, to read the revised chapters together, follow their links and try the proposed order before choosing what to apply to Working. Revisit the review and return flows against the current collection, media and publication boundaries when this work is scoped. [Docs Review](../Docs_Review.md)

For that round trip, decide which Book front matter the package should carry and which fields the return path may accept. Start by considering `library_sources` so the saved IDs and titles can travel with a chapter. Keep document identity and collection ownership tied to the exported selection, and review section order as a proposal before applying it to the Book tree. This follow-on has its own scope. [Import field handling](../Docs_Import_Architecture.md#normalized-document-intent)
