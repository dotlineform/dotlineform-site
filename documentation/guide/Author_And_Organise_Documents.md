# Author and organise documents

Open Docs Viewer Manage at `/docs/` to create, edit and arrange documents. Manage writes to Working, where Markdown and front matter hold the editable content and generation prepares what the readers display. Studio owns changes to Catalogue Works, which arrive in Docs Viewer through Refresh Catalogue and Regenerate. [How the site fits together](How_The_Site_Fits_Together.md)

## Choose where the document belongs

- **Ordinary Index.** Use **Actions → New** to create a draft beside the open ordinary document, or at the root when there is no ordinary anchor. Use the Index row menu for **New Child**, **New Sibling** or **Position**. Position moves the document with its descendants. Working saves the hierarchy and sibling order separately from the Markdown, so a title or body edit leaves placement intact. [Source controls and document identity](../studio/Source_Organisation.md#source-controls)
- **An existing collection.** Open its host in the Index and use **Collection Actions → New doc…**, or use **Import doc…** for one supported native file and **Import docs…** for folder-based sources and packages. A named collection keeps its documents under its own configured owner and displays them through its host. New collection registration is a development change. [Collection identity](../studio/Source_Organisation.md#document-and-collection-identity) · [Docs Import](../studio/Docs_Import.md#import-one-native-file)

## Edit, save and check the result

Open the document and choose **Source editor** from its document actions. Edit the Markdown and its fields, then choose **Save**. Save persists the source and any selected media, builds the exact document and any affected direct link dependencies, and refreshes the displayed result. Body, title and summary edits advance `last_updated`. Use the Source calendar control to author a date for display through `[[date]]`. [Source Save](../studio/Docs_Viewer_Runtime.md#source-editing-and-save) · [Date provenance](../studio/Document_Identity.md#date-provenance) · [Document date](../studio/Builder.md#document-date)

For an external Markdown edit, save the file, supply the intended `last_updated` timestamp for a body, title or summary change, then choose **Rebuild** for the exact document or run its targeted CLI build. Reload the reader after a CLI build. Exact generation keeps routine edits local to the affected output, while Search and Recent have an explicit refresh. If Save reports that the source was written but generation failed, correct the reported problem and rebuild the saved document. [External edits and rebuilds](../studio/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) · [Publish and deploy](Publish_And_Deploy.md)

Choose **Mark ready** in the document actions when a draft is ready. Working recalculates its eligibility and queues the applicable changes. The separate **Publish** action applies them to the configured destinations. [Publication eligibility](Publish_And_Deploy.md#1-prepare-the-change)

## Add links and media

- Use **Insert doc link** in Source to choose an exact document. The link carries its stable identity, so it survives a title change and opens through the active reader. To show computed incoming and outgoing links, put `[[links|Further reading]]` on its own line. Working renders the list from its saved relationships. Use the **Broken Links** report's explicit **Refresh** to check destinations. [Related Links](../studio/Related_Links.md#authoring-decision) · [Broken Links report](../studio/Broken_Links_Script.md#saved-local-report)
- Use **Add image** or **Add file** in Source to select a file and insert its reference. Save stores the selected media. When reusing body media stored under another document's ID, save the destination while the original bytes still exist. Save copies the referenced files into the destination's own media folder and rewrites the references so the documents can be maintained independently. [Media intake](../studio/Docs_Images_And_Assets.md#add-a-new-image-or-download) · [Media adoption](../studio/Media_And_Asset_Handling.md#source-save-media-adoption)

## Curate a Book

Use **Library → Select → Actions → Copy to Book…** to make draft working copies that retain their Library provenance. In the Book pane, use **Tree** and **Position…** to arrange opening pages, Root chapters, Parts and back matter. Sections hold private staging pages, including pages marked ready. Opening and back-matter pages can be **Both**, **Web only** or **Export only**. [Book curation](../studio/Sub_Scope_Index_Architecture.md#book-curation-in-manage) · [Book editions](../studio/Sub_Scope_Index_Architecture.md#book-editions)

Put `[[toc]]` on its own line in the ordinary Book host. Add any introductory material there. Working uses the saved Tree and page settings for the web contents and reading order. Changing a ready page's placement or edition can queue its withdrawal or restoration. The host's eligibility governs publication of the Book. This lets the author stage material and adjust the reading sequence while Working keeps the reader output in step. [Book table of contents](../studio/Builder.md#book-table-of-contents) · [Publication eligibility](Publish_And_Deploy.md#1-prepare-the-change)

Return to the [guide contents](README.md).
