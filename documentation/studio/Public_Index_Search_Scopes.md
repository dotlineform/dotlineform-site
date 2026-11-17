---
draft: false
doc_id: d-20261116-203803-742848
title: Public Index Search Scopes
added_date: "2026-11-16 20:38:03"
last_updated: "2026-11-17"
summary: Shared Manage and Public search coverage, with a scope button in the main Index that shows the destination of the next click.
ui_status: done
parent_id: d-20260924-135214-baa9ec
---
# Public Index Search Scopes

Portfolio search helps readers find work and writing by title across Catalogue, Context, Concepts and Moments. Library and Living Memory are reference collections with their own search scopes. Manage and Public share the main Index search field, results list and scope rules. [Collection Search And Site Search](Collection_Search_And_Site_Search.md)

## Search Before This Delivery

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

## Target Search Coverage

| Search scope | Fields to match | Coverage |
| --- | --- | --- |
| **Portfolio** | Titles only | Eligible ordinary documents, the four portfolio collection landing pages, Context documents, Concepts, Moments and Catalogue Galleries. Catalogue Works and both reference collections, including their landing pages, are excluded. |
| **Catalogue** | Work titles, partial Work IDs and Gallery titles | Works and Galleries. A Gallery also appears when one of its direct member Works matches. |
| **Context** | Full text | Context documents. |
| **Concepts** | Full text | Concept documents. |
| **Moments** | Full text | Moment documents. |
| **Library** | Titles and summaries | Library entries. |
| **Living Memory** | Titles and summaries | Web-edition pages, with results linking directly to each page. |

Context, Concepts, Moments, Library and Living Memory use the main Index field and results. Catalogue alone keeps search controls within its collection view. The other collection reports serve as browsing lists.

Drafts are excluded when the indexes are built. Living Memory search uses eligible web-edition pages. Its public table of contents stays in the reading pane. The Manage Book Index panel keeps List and Tree for authoring, using its existing Book management data. Remove its search field. The panel requires no additional manifest or search index.

## Gallery Results

Portfolio search matches a Catalogue Gallery by the Gallery's own title only. Each Gallery result carries its exact `gallery_id` for navigation. Selecting the result opens the existing Catalogue Gallery Media View in the main pane using that ID as a `catalogue-gallery` target. The Index retains the search query and results while the Gallery is open. [Catalogue Media View](Catalogue_Media_View.md)

## Behaviour

Place the scope button beside the search field in Manage and Public. The field names the current scope. The button icon, tooltip and accessible name show the scope that clicking it will select. Changing scope reruns any active query and leaves the current page open. The scope button uses the standard icon button hover fill. Recent uses a persistent fill while its results are open.

| Current Index search | Scope button icon | Tooltip and accessible name |
| --- | --- | --- |
| **Search Concepts** | `globe.svg` | **Search portfolio** |
| **Search portfolio**, with Concepts open | Concepts collection icon | **Search Concepts** |

The same rule applies to other collections with their own main Index search. On an ordinary page such as **dotlineform** or **About**, and in Catalogue, the main Index offers portfolio search and shows a disabled globe. In Catalogue, the collection's own controls search Works and Galleries.

An explicit choice to search the portfolio survives moves among portfolio collections, clearing the query and closing search. Deliberately selecting **Library** or **Living Memory** in the Index switches to that collection's search. Readers can use the globe to switch back to portfolio search from either collection.

Opening a result keeps the active query, scope and results. For example, opening a Context result from a portfolio search changes the button to the Context icon while the field still reads **Search portfolio**. Clicking the Context icon switches to **Search Context**. Closing search returns the Index to the collection or document the reader has reached.

Use spacing alone to group the Index items. Keep Context, Concepts, Catalogue and Moments together, followed by a small gap before **Library** and **Living Memory**, and another before **about**. Start with about a third of a row's height of extra space at each break.

## Separate Search Indexes

Portfolio has its own title-only index. Context, Concepts, Moments, Library and Living Memory each have a search index with the fields listed above. The main Index loads the file for the active scope and uses the same Docs Viewer matcher for all six indexes. Manage reads the latest completed Working indexes. Public reads the published copies of those same files. Catalogue search uses its existing Work manifest and Gallery search file.

The current `include_in_site_search` setting controls which collections supply records to the shared Search index and also affects Recent. The proposed search indexes have their own coverage and field policies, independent of Recent. [Current Search index contract](Docs_Search_Index.md)

### Search Files By Scope

Current paths are public URLs under the site root. The target column describes each index by purpose while its file path is still open.

| Scope | Files used today | Files needed for the target |
| --- | --- | --- |
| **Portfolio** | `/assets/data/search/analysis/index.json` is the shared full-text index. | A portfolio title index with the coverage in the target table. Gallery rows carry titles and exact Gallery IDs for Media View. |
| **Catalogue** | `/assets/data/docs/catalogue/manifest.json` supplies Work titles and IDs. `/assets/data/catalogue/galleries/report-search.json` supplies Gallery titles and Work-to-Gallery memberships. | Reuse both files for the existing Catalogue search. The portfolio index uses Gallery titles for matching and exact Gallery IDs for Media View navigation. |
| **Context** | `/assets/data/docs/works/manifest.json` supplies titles for the report filter. | A Context full-text index. Context titles also go in the portfolio index. |
| **Concepts** | `/assets/data/docs/concepts/manifest.json` supplies titles for the report filter. | A Concepts full-text index. Concept titles also go in the portfolio index. |
| **Moments** | `/assets/data/docs/moments/manifest.json` supplies titles for the report filter. | A Moments full-text index. Moment titles also go in the portfolio index. |
| **Library** | `/assets/data/docs/library/manifest.json` supplies titles for the report filter. | A Library title-and-summary index, loaded by **Search Library** in the main Index in place of the report filter. |
| **Living Memory** | `/assets/data/docs/by-id/d-20261111-120000-5af14d.json` supplies the table of contents for browsing. The configured Book manifest is `/assets/data/docs/book/manifest.json`. | A Living Memory title-and-summary index of web-edition pages, loaded by **Search Living Memory** in the main Index. |

### Estimated Search Payload Sizes

The baseline is the prepared site snapshot on 16 November 2026. Sizes are in decimal kB. The gzip column uses the same local compression settings for each file. [Prepared Search index](../../site/assets/data/search/analysis/index.json)

| Search index | Entries | JSON size | Gzipped |
| --- | ---: | ---: | ---: |
| Current site search | 168 | 1,316 kB | 142.2 kB |
| **Portfolio titles** | **511** | **157 kB** | **11.4 kB** |
| Context full text | 5 | 52.6 kB | 4.7 kB |
| Concepts full text | 246 | 198.4 kB | 15.2 kB |
| Moments full text | 61 | 163.0 kB | 16.4 kB |
| Library titles and summaries | 152 | 164.8 kB | 18.2 kB |
| Living Memory titles and summaries | 3 | 1.4 kB | 0.4 kB |
| **All target indexes combined** | | **737 kB** | **66.3 kB** |

The 193 Gallery titles add about 4.1 kB gzipped to the portfolio index. Catalogue's existing search files are outside this total.

The target estimates use the current Docs Viewer index format with a typed Gallery target. The portfolio estimate draws titles from the prepared public tree, collection manifests and Gallery search file. Context, Library and Living Memory reuse postings from the prepared Search index. Concepts and Moments use current Working text for the documents listed in the prepared public manifests. The figures cover the current corpus, before the queued imports and planned writing described above.

## Building And Publishing Search Indexes

1. **Studio Refresh prepares Gallery data.** After adding, renaming or deleting a Gallery, run Studio Refresh before refreshing Docs Viewer search. Studio Refresh produces the Catalogue Gallery search file. The portfolio index uses the prepared Gallery titles and exact IDs from that file. [Catalogue Gallery search publication](deliveries/Catalogue_Index_Gallery_Results.md#studio-refresh-and-publication)
2. **Refresh Search and Recent builds all six Search indexes in Working.** The action builds Portfolio, Context, Concepts, Moments, Library and Living Memory. Portfolio uses saved document titles and prepared Gallery data. The collection indexes reuse the eligible document metadata and read the fields specified in the target table. Recent follows its own selection rules within the same action. The refresh writes and queues each changed index as a separate publication artifact. The full Working Build uses the same index builder with the document data it already loaded. [Current refresh owner](../../docs-viewer/services/docs_discovery_refresh.py) · [Full Working Build owner](../../docs-viewer/services/docs_working_rebuild.py)
3. **Publish transfers the queued files.** Publish copies the exact completed index files through Preview into the tracked `site/` tree. **Deploy Public** serves the indexes from the committed site snapshot. [Publication workflow](Builder.md#publish-preparation)

## Recent Coverage

Site Recent keeps its current coverage. It selects eligible ordinary documents, including eligible collection landing pages, plus individual entries from Context, Library and Living Memory's web edition. Individual Concepts, Moments and Catalogue entries are outside this coverage. Recent applies its exact exclusions, sorts by update date and shows up to 20 entries. [Recent contract](Generated_Data_Contracts.md#recent-contract)

Gallery titles are searchable in Portfolio. Galleries stay outside site Recent for this delivery.

A follow-on can decide whether to show recent Galleries in site Recent or in a Catalogue-specific recent view. The current Catalogue default Work list is ordered by last update, most recent first. [Catalogue default sort](../../docs-viewer/runtime/js/shared/docs-collection-report.js#L24)

## Delivery Steps

Status **Done.** The user accepted the local delivery on 17 November 2026. The six indexes and shared reader are prepared in the repository. Keep this record pending manual archive. [Docs Viewer Search](Docs_Viewer_Search.md) and [Search Index](Docs_Search_Index.md) own the current behaviour and artifact contract.

### 0. Confirm readiness

- [x] Trace Search generation, publication and reading in Working and Public. The singleton Search transfer can become six named selections in the existing shared-output queue. The reader can open exact Gallery targets through the existing Media View. The prepared Working Gallery file is available and supplies 193 titles. [Publication transfer](../../docs-viewer/services/docs_selected_publication.py) · [Media View adapter](../../docs-viewer/runtime/js/shared/docs-viewer-media-detail.js)
- [x] Confirm the following cutover decisions. Approved on 17 November 2026.

**Artifact names and handoff.** Keep `index.json` and the `workspace/search` queue entry for Portfolio. Add `works.json`, `concepts.json`, `moments.json`, `library.json` and `book.json` for the five collection scopes, using their configured collection IDs. Queue each as `workspace/search-<collection-id>`. Resolve each file within the current `working/generated/search/`, `preview/search/` and `site/assets/data/search/analysis/` owners. Manage reads one scope through `/docs/search` with `search-scope` selecting a configured artifact. Public reads the corresponding static file. Publish uses the same selected-transfer workflow and queue schema.

**Documents and Galleries.** Keep the stage-independent Search format and matcher. Portfolio Gallery rows use `kind: catalogue-gallery` and their exact Gallery ID as the row's `id`. Gallery activation passes that ID to the current Media View from the Index result. Document results keep the current link handling. Read the prepared Gallery title file once per build. Portfolio uses saved document titles. Refresh still needs ordinary update dates for Recent because the saved ordinary tree has no dates. Full Working Build supplies those dates from its loaded sources.

**Scope and history.** Store `search-scope` alongside `q` in search URLs, using `portfolio` or the configured collection ID. Reload and shared links restore the query and scope. Back continues to restore the document while keeping the active panel search, carrying the scope alongside the query. The Portfolio preference stays in the browser as search closes and reopens. [Current route restoration](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js#L75)

**Manage after an edit.** Use the completed Working indexes as the source of postings. Today Manage patches title and summary postings in memory after an edit, while body postings still come from the last build. Retire that partial rewrite so changes to indexed fields take effect together at Refresh Search and Recent. Preserve immediate suppression of known deleted targets in Manage. [Current Search change handler](../../docs-viewer/runtime/js/shared/docs-viewer-search-controller.js#L243)

### 1. Generate and queue the indexes

- [x] Build the six indexes through one Working builder used by Refresh Search and Recent, Full Working Build and the standalone Search command. Portfolio uses saved titles and prepared Gallery data. Collection scopes use their selected source fields. Full Working Build supplies loaded sources. Recent selects its own coverage.
- [x] Register each scope as its own publication artifact. One Working refresh produced 511 Portfolio rows, including 193 exact Gallery targets, plus 5 Context, 246 Concepts, 61 Moments, 152 Library and 3 Living Memory rows. The Book index excluded draft and export-only pages. Recent skipped its write and the six Search files were the only queued selections.

### 2. Wire the shared Index search

- [x] Connect Manage and Public to their respective copies of the six indexes. Load the active scope on demand through the existing matcher and result list. Show the globe or the current collection's icon and label according to the destination scope. Apply the agreed reset and persistence rules and open Gallery results through the existing Media View.
- [x] Group the Index with small gaps before Library and about. Remove the non-Catalogue collection search fields. Catalogue search and the Book's browsing and authoring controls keep their existing data owners.

### 3. Verify the cutover locally

- [x] Project the shared runtime and inspect the tracked changes. Changed-source lint, `bin/site-code-update --check`, `bin/site-validate` and `git diff --check` passed. Publish transferred six exact files through Preview to the repository and cleared those selections. A fresh Manage service and local public preview returned the expected fields and counts for all six URLs.
- [x] Complete manual review and accept the local delivery. The user confirmed that browsing Gallery and Work results returns to the active search, following a Context link keeps the results, and the scope button shows the destination collection icon after the projection fix. The user also accepted the Catalogue search focus change.

### 4. Review and close

- [x] Complete the [Redundancy And Defensive Behavior Review](Development_Checklist.md#redundancy-and-defensive-behavior-review). Reuse collection metadata for Portfolio and scoped rows, loaded sources in Full Working Build, and the current document mount for Gallery activation. Ordinary source reads supply dates for Recent only. Removed the browser's partial postings rewrite and the unused singleton publication path. Retained path and identity checks at selected read boundaries, a schema check on browser load, and selected byte verification in Publish. Publish does no new content or eligibility work.
- [x] Update the maintained [Search guide](Docs_Viewer_Search.md) and [Search contract](Docs_Search_Index.md).
- [x] Record acceptance and evidence limits. The final same-tab `cat.` link passed focused lint and site validation. That click, shared URL restoration and narrow-screen behaviour were not individually reported in the manual walkthrough. Commit, push and Deploy Public are separate release actions.
