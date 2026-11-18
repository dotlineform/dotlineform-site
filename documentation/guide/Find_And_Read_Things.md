# Find and read things

The public site opens the Docs Viewer at `/`. Local Manage uses the same reader at `/docs/` with Working data. Use the Index panel to find a document or collection and the main pane to read it. [How the site fits together](How_The_Site_Fits_Together.md)

## Start with Index, Search or Recent

- **Index.** Expand branches to browse the authored tree. Selecting a row opens that document or a collection’s landing page. The tree highlights the ordinary document you are reading, or the collection’s landing page when you are reading one of its members. [Index behaviour](../studio/Docs_Viewer_Runtime.md#retained-index-views)
- **Search.** Type into the Index search field. **Search portfolio** finds titles across the portfolio, including Catalogue Galleries. In Context, Concepts and Moments, collection Search reads full text. In Library and Living Memory it searches titles and summaries. Use the scope button to switch between the available collection and Portfolio, and **More** to reveal another batch. The current URL carries the Index query and scope for sharing or reloading. [Search scopes and result controls](../studio/Docs_Viewer_Search.md)
- **Recent.** Select **Recent** to see up to 20 of the newest eligible additions across Context, Concepts, Moments and Catalogue Galleries. Toggling Recent off or clearing a Search query reveals the tree at the document you are reading. Manage reads the saved Working discovery files and the public reader uses the published snapshot. [Recent contract](../studio/Generated_Data_Contracts.md#recent-contract)

Opening a document result keeps the Index results in place. Use **browser Back** to return to the previous page and its reading position. The Index panel keeps its current view, query and result scroll, so you can continue with the next result. A Gallery result opens Media View over the current document and uses the return controls described below. [Reader history](../studio/Docs_Viewer_Runtime.md#browser-history)

## Browse the Catalogue

Open **Catalogue** from the Index. The **work or gallery** field matches titles and Work IDs. It searches the full Catalogue and has its own query in the Catalogue page URL. Results group matching Gallery titles, Galleries with matching Works, then individual Works. Use **A–Z** or **Last added** to sort within each group. [Catalogue collection browsing](../studio/Sub_Scope_Index_Architecture.md#catalogue-collection-browsing)

With the field empty, List starts with up to 64 of the most recently added Works. Use **Shuffle** to browse another selection. **Switch to Gallery view** opens a rolling grid where each shuffle adds a column. Returning to List restores its selection and scroll. [Catalogue collection browsing](../studio/Sub_Scope_Index_Architecture.md#catalogue-collection-browsing)

A Work title or thumbnail in the list or rolling grid opens its Catalogue document. **Previous** and **Next** below the document follow the order captured when you opened it. If you open a Work from the list and then follow **Next**, browser Back returns to the first Work. Use the Work document’s **index** shortcut to reopen Catalogue and resume its last browsing state, including after a direct Work link. The reader retains the immediate caller and remembers collection controls separately, so older browser entries can reopen by URL. [Collection order and return](../studio/Docs_Viewer_Runtime.md#collection-previous-and-next) · [Reader history](../studio/Docs_Viewer_Runtime.md#browser-history)

## Open and leave Media View

Select a Gallery search result, follow a Media View link or linked Work image in a document, or use **Open selection in Media View** in the unfiltered Catalogue List. Media View opens in the main pane over the current page. A Gallery opens a paged thumbnail grid. Select a Work to see its larger image, catalogue number, Gallery links and available Context links. [Gallery presentations](../studio/Catalogue_Media_View.md#gallery-presentations) · [Catalogue discovery grid](../studio/Catalogue_Media_View.md#discovery-grid)

- **Return to the grid.** From a Work opened in a Gallery, use **Previous** and **Next** to browse that Gallery’s Works, then select the Gallery link to return to the page containing the current Work. For the grid made from Catalogue List, use the **Catalogue Discovery** link.
- **Return to the underlying page.** Choose **Back to document** to close Media View and return to the document or list at its previous position, with focus on the opening control. Media View stays within the current browser entry. If you follow a document link from it, such as the Work’s catalogue number, browser Back returns to the underlying page. [Reader history](../studio/Docs_Viewer_Runtime.md#browser-history)

For changes to what appears in discovery, see [Publish and deploy](Publish_And_Deploy.md). Return to the [guide contents](README.md).
