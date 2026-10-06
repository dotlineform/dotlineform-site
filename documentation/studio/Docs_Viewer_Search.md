---
draft: false
doc_id: d-20260602-160839-6d3cbb
title: Docs Viewer Search
added_date: "2026-06-02 16:08:39"
last_updated: "2026-10-06 22:13:31"
parent_id: d-20260331-000000-5dcf32

---
# Docs Viewer Search

Docs Viewer Search provides one static inverted-index format and one browser query path for the Docs workspace. Working builds eligible ordinary documents plus eligible Works subdocs into one index. Preview and the public reader consume unchanged copies through their existing lifecycle.

## Durable Contracts

- [Docs Viewer Search Index](Docs_Search_Index.md) owns payload structure, workspace field and coverage policy, source extraction, ranking inputs, complete rebuilds, and the extension boundary.
- [Docs Viewer Search Tokenizer](Docs_Search_Tokenizer.md) owns normalization, technical-term derivation, exclusions, stop words, query prefix semantics, and Python/JavaScript parity.

`docs-viewer/build/build_search.py`, `docs-viewer/config/workspace/docs-workspace.json`, `docs-viewer/runtime/js/shared/docs-viewer-search.js`, and the generated JSON remain exact code/config authority. The current `docs_viewer_search_index_v4` payload contains no stage or stored result URLs. The configured consumer owns index location and navigation; snapshot manifests own provenance.

## Workspace Policies

The workspace enables `title`, `heading`, `summary`, `body`, and `code`. Ordinary and collection documents contribute their canonical front-matter summary through the shared text tokenizer; missing or blank summaries emit no postings. Summary text is indexed without adding snippets or a new result display.

Parent title, identity and update time remain document-table metadata for display, navigation and deterministic ordering but emit no postings. Shared source extraction includes visible authored headings, prose, inline code, fenced code, image alt text, and visible raw-HTML text; it excludes front matter other than title and summary, report declarations, link destinations, media paths, attributes, scripts, styles, document IDs, date fragments, and 64-character hexadecimal digests.

Working tree metadata selects ordinary documents, pruning draft and unpublishable roots with their descendants. Included collections contribute flat non-draft entries from their management manifests only when their configured ordinary hosts survive. All metadata selection precedes selected Markdown and collection by-ID reads. Search requires current Working document projections and fails clearly on selected inconsistencies.

## Site-Search Corpus

Ordinary documents and Works share one index, query and relevance order. Catalogue, Concepts and Moments subdocs are excluded by explicit collection policy; their eligible ordinary landing pages remain searchable. A collection delivery explicitly sets `include_in_site_search`; registration does not imply inclusion. Recents shares the collection policy and metadata eligibility without reading the Search index. Report-local title search remains a list filter, not another full-text engine.

Collection results retain exact `{collection, doc_id}` identity plus `report_doc_id` metadata. The reader composes the active Manage or public `collection`/`doc` URL directly; the report host does not represent the displayed document. Collection/report title remains payload metadata and emits no postings; result rows display only decorative collection artwork and the document title.

## Build And Publication

The builder reconstructs the complete Working index. Ordinary source saves and watcher passes rebuild document projections only. Manage Rebuild builds document outputs before Search; `build_search.py --stage working --write` uses those existing outputs directly. No path patches postings or maintains a separate collection index. The content version excludes generation time, so an identical rebuild skips its write.

The Working index lives at its configured generated-search location. Prepare Preview captures the saved file and copies its exact bytes into Preview; Deploy Repo copies that file to the public repository destination. Neither rebuilds Search nor applies a second coverage filter. Ordinary source edits may leave Search stale, and prepared document membership need not equal Search membership. Field and coverage policy changes take effect on the next complete Working Search build; rebuilding does not prepare or deploy them.

## Browser Query Path

Generated browser config declares the Docs Viewer domain, v4 schema, index URL, and `whole_index` rebuild policy. The workspace provider checks the v4 schema once at acquisition without requiring stage identity inside that JSON. `docs-viewer-search-controller.js` caches that loaded input and owns query/loading/paging state; route commands own history writes. `docs-viewer-search.js` is the sole tokenizer, postings-intersection, ranking, and tie-breaking owner, with no repeated schema validation on query or More. Recent is acquired independently and normalized once by the generated-data adapter, then cached by the same list controller. Neither list reads destination documents or collection manifests to populate its rows.

A multi-term query requires one matching posting set per normalized term. Prefix matching begins at three characters. Generic ranking prefers exact identity, exact title, title, heading, summary, parent title, body/code, and update metadata; only enabled fields participate. The workspace therefore ranks exact title, title, heading, summary, then body/code. Ties sort by title and identity, and each exact ordinary or collection target appears at most once.

## Index Results And Navigation

Search renders and announces no numeric result counts or shown/total summaries. Loading, searching, empty-result and error messages remain, and More continues to reveal the next batch of results. Recent likewise shows no count.

Search and Recent controls occupy the first Index row in Public and Manage. Their results replace the visible tree while the document remains in the main pane. Manage keeps Index Actions and Position in a second row, disabled while results are active; displayed-document controls retain their normal capabilities. Expanded main views can hide the whole Index panel and retain its active view for return. Public narrow screens bound the list height so the document below remains reachable.

Opening a result, pinned Related link or in-app document-content link preserves the active list, query, paging and list scroll. Only exact ordinary or collection/document identity determines the highlighted row; a destination outside the displayed results leaves no row active. These links leave the tree's explicit selection, expansion and position intact. Related links retain their independent Info capture and lifecycle, including release on Source entry. Clearing Search or toggling Recent off reveals the retained tree and keeps the current exact document and heading. Recent clears an active query; typing a non-empty query switches from Recent to Search.

The Index panel owns its active tree/Search/Recent view, query, visible count, tree selection/expansion and list scroll independently of document navigation. Control adjustments replace the current URL without adding a document history entry. Back restores the immediate caller's exact document/report and reading position, consumes that return context and preserves the panel as currently configured; it cannot reopen Recent or reinstate an earlier Search query. Result highlighting follows the restored target using existing mounted rows. The restored document URL retains the panel's current `q`; initial/reloaded routes apply their URL query once. Native browser destinations outside the current/caller pair reload by exact URL. A view-only change does not remount the document. Matching query/index state reuses mounted rows and cached matches, and More slices that ranking in memory. Switching visibility reloads neither the Index nor either list. Committed metadata updates an existing retained Search record's title/summary/update-date postings and Recent label/order; Delete removes the target from their projections. This changes no saved Search file, body postings, coverage or membership policy. Explicit Search rebuild and authoritative Index refresh keep their separate owners.

## Extension Boundary

Site-search collection inclusion is configuration policy, independent of collection registration and publication eligibility. Included collections reuse the shared schema, tokenizer, reader and query engine. Collection-scoped full-text search remains a separately specified feature.

The practical ceiling remains one client-loaded static index. Short prefixes can return broad result sets after full-text adoption; snippets, highlighting, stemming, synonyms, spelling correction, phrase positions, and section results remain outside the current contract.
