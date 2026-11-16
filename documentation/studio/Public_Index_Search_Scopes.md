---
draft: false
doc_id: d-20261116-203803-742848
title: Public Index Search Scopes
added_date: "2026-11-16 20:38:03"
last_updated: "2026-11-16"
summary: Current and proposed public search coverage for the main Index and each collection, with an Index scope selector for Library and Living Memory.
parent_id: d-20260924-135214-baa9ec
---
# Public Index Search Scopes

Public search serves two purposes. Site search helps readers find a document or collection by title. Collection search can match the fields most useful to readers of that collection. The proposed Index scope selector uses the existing Index search field and results list for Whole site, Library and Living Memory. Living Memory keeps its table of contents in the reading pane. [Collection Search And Site Search](Collection_Search_And_Site_Search.md)

## Current Search Behaviour

| Collection | Search within the collection | What appears in main Index search |
| --- | --- | --- |
| **Catalogue** | Work and Gallery titles match from the start of a word. Work IDs support partial matches. A Gallery also appears when one of its direct member Works matches. | Catalogue landing page only |
| **Concepts** | Title filter. The query can match anywhere in a Concept title. | Concepts landing page only |
| **Moments** | Title filter. The query can match anywhere in a Moment title. | Moments landing page only |
| **Context** | Title filter. The query can match anywhere in a document title. | Landing page and individual Context documents, full text |
| **Library** | Title filter. The query can match anywhere in an entry title. | Landing page and individual Library entries, full text |
| **Living Memory** | Table of contents for browsing. No dedicated search field today. | Landing page and indexed web-edition pages, full text |

Main Index search matches titles, headings, summaries, body text and code, and returns one result per document. Collection title filters match the typed text as a continuous string. The Index matches individual terms, so different words in a query can match in the title and body of the same document. [Collection matching](../../docs-viewer/runtime/js/shared/docs-collection-browsing.js#L170) · [Index search contract](Docs_Search_Index.md#query-and-ranking)

In the prepared site snapshot on 16 November 2026, Library accounted for 152 of 168 indexed documents, compared with five Context documents and three Living Memory pages. [Prepared Search index](../../site/assets/data/search/analysis/index.json)

## Collection Growth Estimates

- **Catalogue** is expected to grow modestly, with potentially 5–10% more Works and Galleries queued.
- **Moments** is expected to stay close to its current size, with no source documents queued.
- **Context** has about 50 documents queued.
- **Concepts** is expected to have about half as many documents as it does now, with substantially more content in each.
- **Library** has about 300 documents queued for import.
- **Living Memory** is still to be written, with a target of about 50 substantial pages.

## Target Search Behaviour

| Search scope | Fields to match | Coverage |
| --- | --- | --- |
| **Whole site** | Titles only | Eligible ordinary documents and collection landing pages, plus Context documents, Concepts, Moments and Catalogue Galleries. Exclude Catalogue Works and all Library and Living Memory pages, including their landing pages. |
| **Catalogue** | Work titles, partial Work IDs and Gallery titles | Works and Galleries. A Gallery also appears when one of its direct member Works matches. |
| **Context** | Full text | Context documents. |
| **Concepts** | Full text | Concept documents. |
| **Moments** | Full text | Moment documents. |
| **Library** | Titles and summaries | Library entries. |
| **Living Memory** | Titles and summaries | Web-edition pages, with results linking directly to each page. |

Context, Concepts and Moments run full-text queries from the search field in each collection report and display results in that report's list. The matcher returns document IDs from the collection's own index, and the report renders the matching rows from its loaded manifest. Clearing the query restores the full collection list. The field label names the collection, for example **Search Context**.

Readers reach Library and Living Memory through the Index tree. Both collections use the main Index search field and results panel. **Search Library** replaces the title filter in the Library report.

## Gallery Results

Whole site matches a Catalogue Gallery by the Gallery's own title only. Each Gallery result carries its exact `gallery_id` for navigation. Selecting the result opens the existing Catalogue Gallery Media View in the main pane using that ID as a `catalogue-gallery` target. The Index retains the search query and results while the Gallery is open. [Catalogue Media View](Catalogue_Media_View.md)

## Selecting A Scope

A new search defaults to the current document's context. On the Library landing page or an entry, the label reads **Search Library**. On the Living Memory table of contents or a book page, it reads **Search Living Memory**. Opening an Index item outside either collection sets the next search to **Whole site**. Following a result keeps the active query and scope so readers can browse several results from the same search.

The scope label is a dropdown directly below the Index search field and stays visible while the reader types.

```text
[ hippocampus                 × ]
  Search Living Memory ▾
```

In Living Memory, the menu offers **Living Memory** and **Whole site**, with a checkmark beside the active scope. Selecting **Whole site** changes the label to **Search whole site** and reruns the same query in the Index panel while keeping the current page open. Library follows the same pattern.

## Separate Search Indexes

Whole site has its own title-only index. Context, Concepts, Moments, Library and Living Memory each have a separate search index with the fields listed above. Catalogue search uses its existing Work manifest and Gallery search file. In the public Index panel, the selected scope determines which file the search field loads. The same Docs Viewer matcher uses the fields and postings in that file to determine what can match. For example, a term that appears only in a summary can match in Library or Living Memory because their indexes include summaries.

The current `include_in_site_search` setting controls which collections supply records to the shared Search index and also affects Recent. The proposed search indexes have their own coverage and field policies, independent of Recent. [Current Search index contract](Docs_Search_Index.md)

### Search Files By Scope

Current paths are public URLs under the site root. The target column describes each index by purpose while its file path is still open.

| Scope | Files used today | Files needed for the target |
| --- | --- | --- |
| **Whole site** | `/assets/data/search/analysis/index.json` is the shared full-text index. | A site-wide title index with the coverage in the target table. Gallery rows carry titles and exact Gallery IDs for Media View. |
| **Catalogue** | `/assets/data/docs/catalogue/manifest.json` supplies Work titles and IDs. `/assets/data/catalogue/galleries/report-search.json` supplies Gallery titles and Work-to-Gallery memberships. | Reuse both files for the existing Catalogue search. The site index uses Gallery titles for matching and exact Gallery IDs for Media View navigation. |
| **Context** | `/assets/data/docs/works/manifest.json` supplies titles for the report filter. | A Context full-text index. Context titles also go in the site index. |
| **Concepts** | `/assets/data/docs/concepts/manifest.json` supplies titles for the report filter. | A Concepts full-text index. Concept titles also go in the site index. |
| **Moments** | `/assets/data/docs/moments/manifest.json` supplies titles for the report filter. | A Moments full-text index. Moment titles also go in the site index. |
| **Library** | `/assets/data/docs/library/manifest.json` supplies titles for the report filter. | A Library title-and-summary index, loaded by **Search Library** in the main Index in place of the report filter. |
| **Living Memory** | `/assets/data/docs/by-id/d-20261111-120000-5af14d.json` supplies the table of contents for browsing. The configured Book manifest is `/assets/data/docs/book/manifest.json`. | A Living Memory title-and-summary index of web-edition pages, loaded by **Search Living Memory** in the main Index. |

### Estimated Search Payload Sizes

The baseline is the prepared site snapshot on 16 November 2026. Sizes are in decimal kB. The gzip column uses the same local compression settings for each file. [Prepared Search index](../../site/assets/data/search/analysis/index.json)

| Search index | Entries | JSON size | Gzipped |
| --- | ---: | ---: | ---: |
| Current site search | 168 | 1,316 kB | 142.2 kB |
| **Target site search** | **511** | **157 kB** | **11.4 kB** |
| Context full text | 5 | 52.6 kB | 4.7 kB |
| Concepts full text | 246 | 198.4 kB | 15.2 kB |
| Moments full text | 61 | 163.0 kB | 16.4 kB |
| Library titles and summaries | 152 | 164.8 kB | 18.2 kB |
| Living Memory titles and summaries | 3 | 1.4 kB | 0.4 kB |
| **All target indexes combined** | | **737 kB** | **66.3 kB** |

The 193 Gallery titles add about 4.1 kB gzipped to the target site index. The total covers the listed indexes. Context, Concepts and Moments also load their report manifests to render result rows, and Catalogue uses its existing search files.

The target estimates use the current Docs Viewer index format with a typed Gallery target. The site estimate draws titles from the prepared public tree, collection manifests and Gallery search file. Context, Library and Living Memory reuse postings from the prepared Search index. Concepts and Moments use current Working text for the documents listed in the prepared public manifests. The figures cover the current corpus, before the queued imports and planned writing described above.

## Building And Publishing Search Indexes

1. **Studio Refresh prepares Gallery data.** After adding, renaming or deleting a Gallery, run Studio Refresh before refreshing Docs Viewer search. Studio Refresh produces the Catalogue Gallery search file. The site index uses the prepared Gallery titles and exact IDs from that file. [Catalogue Gallery search publication](deliveries/Catalogue_Index_Gallery_Results.md#studio-refresh-and-publication)
2. **Refresh Search and Recent builds all six Search indexes in Working.** The action builds Whole site, Context, Concepts, Moments, Library and Living Memory. Whole site uses saved document titles and prepared Gallery data. The collection indexes reuse the eligible document metadata and read the fields specified in the target table. Recent follows its own selection rules within the same action. The refresh writes and queues each changed index as a separate publication artifact. The full Working Build uses the same index builder with the document data it already loaded. [Current refresh owner](../../docs-viewer/services/docs_discovery_refresh.py) · [Full Working Build owner](../../docs-viewer/services/docs_working_rebuild.py)
3. **Publish transfers the queued files.** Publish copies the exact completed index files through Preview into the tracked `site/` tree. **Deploy Public** serves the indexes from the committed site snapshot. [Publication workflow](Builder.md#publish-preparation)

## Recent Coverage

Site Recent keeps its current coverage. It selects eligible ordinary documents, including eligible collection landing pages, plus individual entries from Context, Library and Living Memory's web edition. Individual Concepts, Moments and Catalogue entries are outside this coverage. Recent applies its exact exclusions, sorts by update date and shows up to 20 entries. [Recent contract](Generated_Data_Contracts.md#recent-contract)

Adding Gallery titles to Whole site makes Galleries searchable there. Galleries stay outside site Recent for this delivery.

A follow-on can decide whether to show recent Galleries in site Recent or in a Catalogue-specific recent view. The current Catalogue default Work list is ordered by last update, most recent first. [Catalogue default sort](../../docs-viewer/runtime/js/shared/docs-collection-report.js#L24)

## Open Issues

1. **What should Manage search?** The recommendation is to use the six public-eligible indexes for reader search and keep Manage's manifest filters available for finding drafts. Full-text search of drafts is a separate decision. [Current local search configuration](../../docs-viewer/config/defaults/docs-viewer-config.json#L15)
2. **When should a selected scope reset?** The recommendation is to keep the reader's explicit scope when they clear the query. Deliberate navigation in the Index tree can set the default from the destination. Store the active scope alongside `q` so a reload, browser Back or a shared link can restore the same search. [Current URL handling](../../docs-viewer/runtime/js/shared/docs-viewer-router.js#L19)
3. **How should collection reports order full-text matches?** The recommendation is to use the matcher's relevance order in Context, Concepts and Moments while a query is active. Keep matching starred entries pinned in Context and restore the normal report order when the query clears. [Current report ordering](../../docs-viewer/runtime/js/shared/docs-collection-report.js#L859)

Choose the exact index paths and the Gallery result record format during implementation planning.
