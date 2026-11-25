# Author and organise documents

Open Docs Viewer Manage at `/docs/` to create, edit and arrange documents. Manage writes to Working, where Markdown and front matter hold the editable content and generation prepares what the readers display. Studio owns changes to Catalogue Works, which arrive in Docs Viewer through Refresh Catalogue and Regenerate. [Start a local surface](How_The_Site_Fits_Together.md#start-a-local-surface)

## Choose where the document belongs

- **Ordinary Index.** Use **Actions → New** to create a draft beside the open ordinary document, or at the root when there is no ordinary anchor. Use the Index row menu for **New Child**, **New Sibling** or **Position**. Position moves the document with its descendants. Working saves the hierarchy and sibling order separately from the Markdown, so a title or body edit leaves placement intact. [Source controls and document identity](../reference/Source_Organisation.md#source-controls)
- **An authored collection.** Open its landing page in the Index and use **Collection Actions → New doc…**, **Import doc…** for one supported native file, or **Import docs…** for folder-based sources and packages. The landing page is an ordinary Index document, and the configured collection owns its members. Moving the landing page preserves their storage and IDs. Catalogue uses **Regenerate** for its Work documents. [Collection identity](../reference/Collections_And_Books.md#collection-identity) · [Docs Import](../reference/Docs_Import.md#import-one-native-file)

If the Index Actions button is disabled while Search or Recent is open, clear the query or turn Recent off to return to the tree. [Index results and navigation](../reference/Reader_Discovery_And_Return.md#index-results-and-navigation)

## Edit, save and check the result

Open the document and choose **Source editor** from its document actions. On a collection list this edits its host. Open a row first to edit that exact member. Title, Summary and body stay in one Markdown buffer. **Save** persists the source and selected media, builds the exact document and affected direct links, then shows the fresh result in place. Use the Source calendar control to author a date displayed through `[[date]]`. [Source Save walkthrough](../reference/Source_Editing.md#follow-a-save) · [Document date](../reference/Builder.md#document-date)

Source uses a defined front-matter grammar for metadata and ordinary Markdown with specific directives for content. Its immutable ID stays with the document through title and placement changes. The grammar reference traces those fields and links into the generated reader output. [Source grammar and rendering](../reference/Document_Identity.md#source-grammar)

For an external Markdown edit, supply the intended full `last_updated` timestamp and use the document's **Rebuild** action or targeted CLI build. If Source Save reports saved source and incomplete generation, correct the reported cause and rebuild the saved document. If the failure is only in the fresh display, reload the reader. Search and Recent have their own refresh. [External edits](../reference/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) · [Save failure phases](../reference/Source_Editing.md#if-save-stops)

Choose **Mark ready** in the document actions when a draft is ready. Working recalculates its eligibility and queues the applicable changes. The separate **Publish** action applies them to the configured destinations. [Publication eligibility](Publish_And_Deploy.md#1-prepare-the-change)

## Import and exchange collection documents

Use **Import doc…** to convert a file into a fresh draft. Pick **Import docs…** for a one-document folder with separate images or attachments. Repeating either ordinary import creates another draft. [Native import walkthrough](../reference/Docs_Import.md#import-one-native-file)

Choose **Select** and check rows before **Collection Actions → Export…** for a readable HTML snapshot or **Prepare package…** for structured exchange. In Concepts, a complete trusted return can update existing Titles, Summaries and bodies. If you only changed a Summary, keep the prepared IDs and omit the returned body field so the canonical Markdown survives. [HTML snapshot](../reference/Export.md) · [Checked package round trip](../reference/Document_Packages.md#follow-a-checked-document-round-trip)

To save a list for review or analysis, check documents and choose the list-plus **Save results** button beside **Clear** and **Done**. Name the list and save it. You can point an analysis at the JSON or reopen the list later through **Saved results** in the Index. [Collection selection](../reference/Collections_And_Books.md#standard-collection-actions) · [Saved results storage](../reference/Reader_Discovery_And_Return.md#saved-results-in-manage)

## Add links and media

- Use **Insert doc link** in Source to choose an exact document. The link carries its stable identity, so it survives a title change and opens through the active reader. To show computed incoming and outgoing links, put `[[links|Further reading]]` on its own line. Working renders the list from its saved relationships. Use the **Broken Links** report's explicit **Refresh** to check destinations. [Related Links](../reference/Related_Links.md#authoring-decision) · [Broken Links report](../reference/Broken_Links.md#saved-local-report)
- Use **Add image** or **Add file** in Source to select a file and insert its reference. Save stores the selected media. When reusing body media stored under another document's ID, save the destination while the original bytes still exist. Save copies the referenced files into the destination's own media folder and rewrites the references so the documents can be maintained independently. [Media intake](../reference/Media_And_Asset_Handling.md#add-a-new-image-or-download) · [Media adoption](../reference/Media_And_Asset_Handling.md#source-save-media-adoption)
- Use **Edit → Thumb** to choose or remove collection-list artwork. Removing the last saved body reference to an owned file queues that file's removal and leaves the independent thumbnail in place. [Thumbnails](../reference/Media_And_Asset_Handling.md#assigned-document-thumbnails) · [Exact removals](../reference/Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)
- Use **Add Media View link** to show a Work image that opens the Work or one of its Galleries. Choose **Inline link** for a text opener or **Hidden** to record the association. A selected Gallery appears in Related Links, and the pictured Work’s Catalogue document links back. [Catalogue media authoring](../reference/Catalogue_Media_View.md#authoring)

## Curate a Book

Use **Library → Select → Actions → Copy to Book…** to make draft working copies that retain their Library provenance. In the Book pane, use **Tree** and **Position…** to arrange opening pages, Root chapters, Parts and back matter. Sections hold private staging pages, including pages marked ready. Opening and back-matter pages can be **Both**, **Web only** or **Export only**. [Book curation](../reference/Collections_And_Books.md#book-curation-in-manage) · [Book editions](../reference/Collections_And_Books.md#book-editions)

Put `[[toc]]` on its own line in the ordinary Book host. Add any introductory material there. For example, move a ready Root chapter into a Section to stage it privately. Book Save updates the Working web contents and queues a withdrawal. Moving it back restores its web membership when the host is eligible. The chapter stays editable in Manage throughout. **Publish** applies the queued effects. [Book table of contents](../reference/Builder.md#book-table-of-contents) · [Book edition and placement rules](../reference/Collections_And_Books.md#book-editions) · [Publish and deploy](Publish_And_Deploy.md)

Return to the [guide contents](README.md).
