# Find and read things

The public site opens the Docs Viewer at `/`. Local Manage uses the same reader at `/docs/` with Working data. Use the Index panel to find a document or collection and the main pane to read it. To browse the checked-in site, open the same public reader through local preview. [Public site](https://www.dotlineform.com/) · [Start a local surface](How_The_Site_Fits_Together.md#start-a-local-surface)

## Start with Index, Search or Recent

- **Index.** Expand branches to browse the authored tree. Selecting a row opens that document or a collection’s landing page. The tree highlights the ordinary document you are reading, or the collection’s landing page when you are reading one of its members. [Index behaviour](../reference/Reader_Discovery_And_Return.md#retained-index-views)
- **Search.** Type into the Index search field. **Search portfolio** finds titles across the portfolio, including Catalogue Galleries. In Context, Concepts and Moments, collection Search reads full text. In Library and Living Memory it searches titles and summaries. The field names the current scope and the scope button names the destination you can switch to. Use **More** to reveal another batch. The URL carries the current Index query and scope for sharing or reloading. Use the Catalogue collection's own field to find individual Works. [Search scopes and result controls](../reference/Reader_Discovery_And_Return.md)
- **Recent.** Select **Recent** to see up to 20 of the newest eligible additions across Context, Concepts, Moments and Catalogue Galleries. Toggling Recent off or clearing a Search query reveals the tree at the document you are reading. Manage reads the saved Working discovery files and the public reader uses the published snapshot. [Recent contract](../reference/Generated_Data_Contracts.md#recent-contract)

Open a document from Search and use **Previous** or **Next** below it to review the other document matches in ranked order. The links reach matches beyond **More** and stay available when the Index is collapsed. Clearing Search keeps the document open at your reading position and removes its Search links. [Search navigation](../reference/Reader_Discovery_And_Return.md#search-previous-and-next)

Opening a document result keeps the Index results in place. Use **browser Back** to return to the previous page and its reading position. The Index panel keeps its current view, query and result scroll. A Gallery result opens Media View over the current document and uses the return controls described below. [Reader history](../reference/Reader_Discovery_And_Return.md#browser-history)

## Browse a collection

Open its landing page from the Index. The collection list reads its saved manifest and sorts or filters those rows. For example, Context puts matching starred documents first on page one. Opening a document there captures that list's order for **Previous** and **Next**. Browser Back can restore the immediate calling list. The document's **index** shortcut reopens the collection with its last visible browsing controls in this tab. [Collection data](../reference/Reader_Discovery_And_Return.md#collection-list-preparation) · [Return paths](../reference/Reader_Discovery_And_Return.md#exact-document-navigation-and-return)

## Browse the Catalogue

Open **Catalogue** from the Index. The **work or gallery** field matches titles and Work IDs. It searches the full Catalogue and has its own query in the Catalogue page URL. Results group matching Gallery titles, Galleries with matching Works, then individual Works. Use **A–Z** or **Last added** to sort within each group. [Catalogue collection browsing](../reference/Reader_Discovery_And_Return.md#catalogue-collection-browsing)

With the field empty, List starts with up to 64 of the most recently added Works. Use **Shuffle** to browse another selection. **Switch to Gallery view** opens a rolling grid where each shuffle adds a column. Returning to List restores its selection and scroll. [Catalogue collection browsing](../reference/Reader_Discovery_And_Return.md#catalogue-collection-browsing)

A Work title or thumbnail opens its Catalogue document. **Previous** and **Next** below the document follow the order captured from the List, rolling grid or search results. Browser Back directly after opening a Work returns to your Catalogue results or browsing position. If you follow **Next** first, browser Back returns to the first Work. Use the Work document’s **index** shortcut to reopen Catalogue and resume its last browsing state, including after a direct Work link. [Collection order and return](../reference/Reader_Discovery_And_Return.md#collection-previous-and-next) · [Reader history](../reference/Reader_Discovery_And_Return.md#browser-history)

## Open and leave Media View

Select a Gallery search result, follow a Media View link or linked Work image in a document, or use **Open selection in Media View** in the unfiltered Catalogue List. Media View opens in the main pane over the current page. A Gallery opens a paged thumbnail grid. Select a Work to see its larger image, catalogue number, Gallery links and available Context links. [Gallery presentations](../reference/Catalogue_Media_View.md#gallery-presentations) · [Catalogue discovery grid](../reference/Catalogue_Media_View.md#discovery-grid)

For the Work's full Related Links list, select its **cat.** number to open the Catalogue document. If you expected a Context link in the image view, check how the referring document names the Work. [Which links appear](../reference/Catalogue_Media_View.md#what-links-appear)

- **Return to the grid.** From a Work opened in a Gallery, use **Previous** and **Next** to browse that Gallery’s Works, then select the Gallery link to return to the page containing the current Work. For the grid made from Catalogue List, use the **Catalogue Discovery** link.
- **Return to the underlying page.** Use Media View’s **Back to document** control to close it and restore the underlying document or list. Focus returns to the opening control when it is still available. Media View stays within the current browser entry. If you follow a document link from it, such as the Work’s catalogue number, browser Back returns to the underlying page. [Reader history](../reference/Reader_Discovery_And_Return.md#browser-history)

For changes to what appears in discovery, see [Publish and deploy](Publish_And_Deploy.md). Return to the [guide contents](README.md).
