---
draft: false
doc_id: d-20260602-160839-6d3cbb
title: Docs Viewer Search
added_date: "2026-06-02 16:08:39"
last_updated: "2026-11-17"
parent_id: d-20260331-000000-5dcf32

---
# Docs Viewer Search

Manage and Public share one Index search field and results list. Portfolio search finds titles across the eligible portfolio, including Catalogue Gallery titles. Collection search uses full text in Context, Concepts and Moments, and titles and summaries in Library and Living Memory. Catalogue's own controls search Works and Galleries.

## Durable Contracts

- [Docs Viewer Search Index](Docs_Search_Index.md) owns scope coverage, payload structure, source extraction, ranking and build and publication.
- [Docs Viewer Search Tokenizer](Docs_Search_Tokenizer.md) owns normalization, technical-term derivation, exclusions, stop words, query prefix semantics, and Python/JavaScript parity.

## Choosing A Scope

The field names the active scope. The adjacent icon and tooltip name the scope that a click will select. In Concepts, the globe switches **Search Concepts** to **Search portfolio**. While Portfolio is active, the Concepts icon switches back to **Search Concepts**. Clicking reruns the current query in the newly selected scope. Ordinary pages and Catalogue use Portfolio directly and show a disabled globe.

An explicit Portfolio selection survives navigation among portfolio collections and closing or clearing Search. Selecting Library or Living Memory directly in the Index switches to that collection's scope. Catalogue focuses its dedicated Work and Gallery search when you enter its collection page.

## Build And Publication

**Refresh Search and Recent** updates all six Working scopes. Full Working Build and the standalone Search command use the same builder. Ordinary authoring changes reach Search when these indexes are refreshed. Manage hides known deletions immediately. Publish transfers the queued index files to Preview and the repository. Deploy Public serves the committed snapshot.

## Browser Query Path

The shared Search controller loads the active scope on demand and reuses it for subsequent queries. The workspace provider checks its schema at acquisition. Search and Recent use their own saved data to display results. Ordinary and collection rows open exact document routes. Gallery rows open the exact Gallery in Media View.

A multi-term query requires a match for each term. Text prefix matching begins at two characters. Standalone integers match titles exactly, with `10,000` and `10000` using the same posting. Ranking uses the fields in the active scope. Ties sort by title and identity.

## Index Results And Navigation

Search renders and announces no numeric result counts or shown/total summaries. Loading, searching, empty-result and error messages remain, and More continues to reveal the next batch of results. Recent likewise shows no count.

**Recent** shows the 20 newest additions across Context, Concepts, Moments and Catalogue Galleries. It uses the recorded addition date, with title and identity breaking same-day ties. Manage uses the latest completed Working list and Public uses the published snapshot. [Recent contract](Generated_Data_Contracts.md#recent-contract)

Search and Recent controls occupy the first Index row in Public and Manage. Their results replace the visible tree while the document remains in the main pane. Manage keeps Index Actions and Position in a second row, disabled while results are active; displayed-document controls retain their normal capabilities. Expanded main views can hide the whole Index panel and retain its active view for return. Public narrow screens bound the list height so the document below remains reachable.

Down from the Index search field focuses the first displayed result and applies any pending query immediately. While results load or the list is empty, focus stays in the field. Up and Down move between displayed results. Enter opens the focused document or Gallery. Escape or Up from the first result returns focus to search. More reveals the next batch.

Opening a result or following an in-app document link preserves the current query, scope and results. Clearing Search or toggling Recent off reveals the tree at the displayed document or collection. Recent clears an active query, and typing a query switches from Recent to Search.

The URL carries `q` and `search-scope` for reload and shared search links. Changing the query or scope updates the current history entry. Back restores the caller's document and reading position while the panel keeps its current search.
