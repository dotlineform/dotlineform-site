---
draft: false
doc_id: d-20260602-160839-6d3cbb
title: Docs Viewer Search
added_date: "2026-06-02 16:08:39"
last_updated: "2026-11-20"
summary: Index, Search, Recent and collection data, browsing state and return behaviour.
parent_id: d-20260424-000000-50b63f

---
# Reader discovery and return

Manage and Public share the reader. Manage reads saved Working data through local configuration and services. Public reads the deployed `site/` snapshot plus its configured media. Each browse surface loads the data it needs for its list, then opens the selected document by exact identity. [Find and read things](../guide/Find_And_Read_Things.md) · [Generated data contracts](Generated_Data_Contracts.md)

## Retained Index Views

| Surface | What it reads | What opening an item does |
| --- | --- | --- |
| **Index tree** | Working's complete `index-tree.json` or the eligible public tree, in authored sibling order. | Opens the exact ordinary document or ordinary collection host. The tree highlights an ordinary page by ID and a collection detail by its host. |
| **Index Search** | One saved Search scope on demand. Manage uses `/docs/search` with `search-scope`. Public reads the corresponding deployed file. | A document row opens its exact document route. A Gallery row opens Media View over the current document. |
| **Recent** | The saved `recent.json`. It contains up to 20 eligible additions across Context, Concepts, Moments and Catalogue Galleries. | Uses the same document and Gallery activation as Search. |
| **Collection host** | The owner's `manage-manifest.json` in Manage or `manifest.json` in Public. Context also reads Selected for first-page stars, and Catalogue uses the prepared Gallery report/search data for Gallery matches. | A Work or other document link opens its by-ID payload. Collection links can carry the invoking document order. Gallery results use Media View. |

The app retains the tree independently of the current Search or Recent list. In the visible tree, it opens the current row's ancestors and moves the row into view when needed. While results cover the tree it tracks the current target without expanding or scrolling it. Clearing Search or toggling Recent off reveals that target. Manage Index Actions and Position are disabled while results occupy the Index. Main-pane document controls follow their own capability rules. [Workspace provider](../../docs-viewer/runtime/js/shared/docs-viewer-workspace-provider.js) · [Recent payload](Generated_Data_Contracts.md#recent-contract) · [Runtime](Docs_Viewer_Runtime.md#document-action-policy)

## Choosing A Scope

The field names the active scope, and the adjacent icon names the destination of a switch. A scope switch reruns the current query. Ordinary pages and Catalogue use Portfolio as their Index search default. Catalogue has a separate Work/Gallery field. An explicit Portfolio choice persists across portfolio collections and through clearing the field. Selecting Library or Living Memory from the tree resets the preferred scope to that collection. An existing active query normally keeps its scope during document navigation. [Search controller](../../docs-viewer/runtime/js/shared/docs-viewer-search-controller.js)

### Scope And Eligibility

| Scope | File | Fields and coverage |
| --- | --- | --- |
| Portfolio | `index.json` | Titles of eligible ordinary pages and portfolio hosts, Context, Concepts, Moments and Catalogue Galleries. Reference collection hosts stay with their own scope. |
| Context, Concepts, Moments | `works.json`, `concepts.json`, `moments.json` | Title, heading, summary, body and code in the selected collection. |
| Library, Living Memory | `library.json`, `book.json` | Titles and summaries. Living Memory uses its web edition. |

Discovery projects ordinary eligibility by pruning Draft and publication-excluded branches. Collection rows require an eligible host and the selected collection's readiness or edition rules. Gallery titles come from prepared Gallery search data when the Catalogue host is eligible. Individual Works are found with Catalogue's dedicated search. Recent uses its own coverage and exact exclusions. [Eligibility owner](../../docs-viewer/services/docs_discovery_selection.py) · [Recent exclusions](Source_Organisation.md#recent-exclusions)

## Index Results And Navigation

Search loads one index per visited scope and reuses it for queries in the mounted reader. **More** reveals another batch of 50. Down from the search field applies a pending query and focuses the first result. Arrow keys move within results, Enter opens the focused item, and Escape or Up from the first result returns to the field. Recent replaces the tree and clears the active query. Typing a query switches back to Search. Known Manage deletions are suppressed in the visible saved results.

Search scope and query use `search-scope` and `q` in the URL. Changing them replaces the current browser entry. Following a result keeps the current view, scope, query, paging and result scroll. Back changes the main document and aligns result selection to that document. The restored URL carries the current Index query. A fresh open or reload can reapply the URL query, beginning with the first batch. Recent mode and its scroll belong to the mounted panel. [Search controls](../../docs-viewer/runtime/js/shared/docs-viewer-search-controller.js)

### Query And Ranking

A multi-term query intersects the normalized matches. Text prefixes start at two characters. Standalone integers use exact title postings, including comma-grouped forms. Ranking uses the active scope's fields, favouring exact title, title, heading, summary, then body and code. Ties sort by title and exact identity. [Browser matcher](../../docs-viewer/runtime/js/shared/docs-viewer-search.js) · [Tokenizer](Docs_Search_Tokenizer.md)

### Payload Contract

`docs_viewer_search_index_v4` has schema/version/time/count in its header, ordered `fields`, exact `docs` rows and field-specific `terms` postings into the zero-based table. Gallery rows have `kind: catalogue-gallery` and the exact Gallery `id`. Summary text contributes postings rather than result-row text. The content version covers schema, fields, rows and terms. Identical builds can keep the saved bytes and timestamp. The browser constructs result routes. [Search builder](../../docs-viewer/build/build_search.py) · [Scope filenames](../../docs-viewer/services/docs_search_scopes.py)

### Source Boundary

Text scopes extract their configured fields from selected Markdown. Supported visible references contribute display text. The producer removes registered media tokens, active Docs image tokens and hidden Catalogue references before ordinary text extraction. Code examples keep their code-field treatment. The renderer separates readable prose, headings and code. Link destinations, media paths and markup attributes do not become prose terms. Ordinary image alt text and visible HTML text can contribute. [Tokenizer](Docs_Search_Tokenizer.md) · [Reference grammar](Document_And_Catalogue_References.md#supported-source-forms)

## Build And Publication

**Refresh Search and Recent** updates the six Working Search scopes and Recent explicitly. Full Working Build supplies its loaded inputs to the same owners. The standalone Search command refreshes Search. Changed scope/Recent files queue independently. Ordinary saves preserve the saved discovery files. Publish transfers queued bytes through Preview and the repository, and Deploy Public releases the new snapshot. [Working generation](Builder.md#working-rebuild) · [Discovery refresh owner](../../docs-viewer/services/docs_discovery_refresh.py)

## Collection List Preparation

A collection report loads the exact configured manifest, prepares title and date orderings and filters the loaded rows. Opening a direct ordinary or collection document route uses its by-ID payload independently of the list. Manage applies committed document effects to its retained lists. Context pages 20 regular rows and groups matching starred rows above the first regular page. Authored artwork uses the document's assigned thumbnail. Catalogue thumbnails use the Work ID and the configured rendition policy. [Collection report](../../docs-viewer/runtime/js/shared/docs-collection-report.js) · [Collection manifests](Generated_Data_Contracts.md#collection-manifest-ownership) · [Thumbnail assignment](Media_And_Asset_Handling.md#assigned-document-thumbnails)

### Catalogue Collection Browsing

The Catalogue host uses the Catalogue document manifest for Work IDs, titles and dates. Its **work or gallery** field searches all Works by title or Work ID and loads `galleries/report-search.json` when it needs Gallery titles and membership matches. It groups Gallery-title matches, Galleries containing matching Works, then Work results. Search pages have 20 entries. A new search defaults to A–Z. A–Z and Last added sort within groups, and refining a query preserves the chosen sort. [Catalogue read models](Catalogue_Indexes_And_Payloads.md#generated-read-models) · [Browsing projector](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js)

Unfiltered List starts with up to 64 of the latest Works. **Shuffle** advances that mode's selection. The rolling Gallery has its own cycle, adding a column of eight and keeping up to eight columns. Switching back to List restores its displayed Works and scroll. The tab remembers the view and displayed Work IDs. A successful Manage Regenerate resets to the default List. The **Open selection in Media View** action uses the unfiltered List sequence. [Shuffle data and cycles](Catalogue_Shuffle_Randomness.md) · [Discovery grid](Catalogue_Media_View.md#discovery-grid)

The Catalogue query uses `catalogue-search` on its host URL, independently of Index `q`. An explicit Catalogue search link applies that query and opens its first page. Manage **Copy search link** supplies a shareable relative Markdown link for a nonempty query. A retained Back uses the report's saved page and controls. [Collection report state](../../docs-viewer/runtime/js/shared/docs-collection-report-state.js)

## Exact Document Navigation And Return

| Action | What is restored |
| --- | --- |
| Open an ordinary Search or Recent document result, then **browser Back** | The immediate calling document or report, its reading position and the opener when it is still visible. The Index retains its current view, query and result scroll. |
| Open a Work from the Catalogue list or its search, then **browser Back** | The retained Catalogue report and its browsing state. The reader can reuse the mounted list and data. |
| Open Work A, follow **Next** to Work B, then **browser Back** | Work A. The report is now outside the retained pair. The Work's **index** shortcut opens Catalogue and restores its last-visible controls from the tab snapshot. |
| Open a Gallery result in **Media View**, then **Back to document** | The underlying document or report, scroll and invocation focus. Media View uses the current browser entry. If you follow its `cat.` or Context document link, later browser Back returns to the underlying caller. |
| Open a shared URL, reload, or use browser history beyond the retained pair | The exact URL opens in a new reader session. Catalogue and other collection reports in the same tab can restore saved controls when opened. Earlier document mounts and Index result paging belong to the old session. |

### Collection Previous And Next

Same-tab collection links capture their invoking order. Previous and Next use that order across report pages, including starred Context documents followed by other matches. Catalogue uses its displayed List, captured rolling grid order or matching Work sequence from its own search. Gallery results activate Media View independently. Book uses the saved Manage Tree or the generated web TOC sequence. The TOC host can supply that sequence on direct entry to the TOC. A document opened directly or through Index Search or Recent starts with just its exact target. [Collection navigation](../../docs-viewer/runtime/js/shared/docs-viewer-collection-navigation.js) · [Book source and placement](Source_Organisation.md#book-source-and-provenance)

### Browser History

The reader retains its active mount and one immediate caller. A new document opening pushes a browser entry and releases any older caller. Returning consumes the active return context. Same-document anchors and browse/filter changes update the existing entry. An older browser destination reloads its exact URL. The Index's loaded view is independent of that pair. [Navigation owner](../../docs-viewer/runtime/js/shared/docs-viewer-navigation.js) · [Route workflow](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js)

Each configured collection also saves its latest visible query, sort, page, filters, supported contribution controls and scroll per host and viewer path in tab `sessionStorage`. This snapshot restores controls against the current inventory after a remount. It does not hold payloads or mounts. A heading hash takes precedence over saved scroll. If storage is blocked, restoration is limited to the current page session. Missing targets fail at their exact route; a removed or hidden opener can leave focus on the restored view. [Tab snapshots](../../docs-viewer/runtime/js/shared/docs-collection-report-state.js) · [Media return](Catalogue_Media_View.md#gallery-presentations)

[Design rationale](../design/Reader_Discovery_And_Return.md) · [Accepted navigation evidence](../deliveries/Document_View_And_Return_Navigation_Handoff.md#acceptance-and-separate-work) · [Scoped Search evidence](../deliveries/Public_Index_Search_Scopes.md#3-verify-the-cutover-locally)
