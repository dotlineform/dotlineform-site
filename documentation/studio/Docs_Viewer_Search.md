---
draft: false
doc_id: d-20260602-160839-6d3cbb
title: Docs Viewer Search
added_date: "2026-06-02 16:08:39"
last_updated: "2026-10-24"
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

Working tree metadata selects ordinary documents, pruning draft and unpublishable roots with their descendants. Included collections contribute flat non-draft entries from their management manifests only when their configured ordinary hosts survive. Saved and completed in-memory selection use the same pruning functions without metadata row/schema/identity/title/date/readiness audits. Standalone Search reads each selected source once through confined, symlink-safe paths, retains source-filename identity and parses shared front-matter fields plus required report declarations for text extraction. It reads no collection by-ID payloads or canonical ordinary ancestry and performs no source/manifest/by-ID agreement checks or repeated Subject/readiness/thumbnail validation. Missing required inputs and actual file/parser failures remain errors.

## Site-Search Corpus

Ordinary documents and Works share one index, query and relevance order. Catalogue, Concepts and Moments subdocs are excluded by explicit collection policy; their eligible ordinary landing pages remain searchable. A collection delivery explicitly sets `include_in_site_search`; registration does not imply inclusion. Recents shares the collection policy and metadata eligibility without reading the Search index. Report-local title search remains a list filter, not another full-text engine.

Collection results retain exact `{collection, doc_id}` identity plus `report_doc_id` metadata. The reader composes the active Manage or public `collection`/`doc` URL directly; the report host does not represent the displayed document. Collection/report title remains payload metadata and emits no postings; result rows display only decorative collection artwork and the document title.

## Build And Publication

The builder reconstructs the complete Working index. Ordinary source saves await exact document/Links projections only. Manage Rebuild supplies its loaded document records and completed discovery selection; `build_search.py --stage working --write` consumes saved metadata and required selected source content. Table projection preserves supplied display metadata without coercion, title completeness, target uniqueness or collection-context audits; term normalization and postings construction retain their own behavior. No path patches postings or maintains a separate collection index. The content version excludes generation time, so an identical rebuild skips its write.

The Working index lives at its configured generated-search location. Prepare Preview captures the saved file and copies its exact bytes into Preview; Deploy Repo copies that file to the public repository destination. Neither rebuilds Search, applies a second coverage filter or audits its copied schema/content; required-file/path handling and byte verification remain. Ordinary source edits may leave Search stale, and prepared document membership need not equal Search membership. Field and coverage policy changes take effect on the next complete Working Search build; rebuilding does not prepare or deploy them.

## Browser Query Path

Generated browser config declares the Docs Viewer domain, v4 schema, index URL, and `whole_index` rebuild policy. The workspace provider checks the v4 schema once at acquisition without requiring stage identity inside that JSON. `docs-viewer-search-controller.js` caches that loaded input and owns query/loading/paging state; route commands own history writes. `docs-viewer-search.js` is the sole tokenizer, postings-intersection, ranking, and tie-breaking owner, with no repeated schema validation on query or More. Recent is acquired independently and consumed directly by the generated-data adapter, then cached by the same list controller without schema/row audits, metadata coercion, default-limit repair or silent row dropping. Neither list reads destination documents or collection manifests to populate its rows.

A multi-term query requires one matching posting set per normalized term. Prefix matching begins at two characters. Generic ranking prefers exact identity, exact title, title, heading, summary, parent title, body/code, and update metadata; only enabled fields participate. The workspace therefore ranks exact title, title, heading, summary, then body/code. Ties sort by title and identity, and each exact ordinary or collection target appears at most once.

## Index Results And Navigation

Search renders and announces no numeric result counts or shown/total summaries. Loading, searching, empty-result and error messages remain, and More continues to reveal the next batch of results. Recent likewise shows no count.

Search and Recent controls occupy the first Index row in Public and Manage. Their results replace the visible tree while the document remains in the main pane. Manage keeps Index Actions and Position in a second row, disabled while results are active; displayed-document controls retain their normal capabilities. Expanded main views can hide the whole Index panel and retain its active view for return. Public narrow screens bound the list height so the document below remains reachable.

Down from the Index search field focuses the first displayed Search or Recent result. It applies any pending search debounce immediately using the existing query owner. While the first index read is still loading or the result list is empty, focus stays in search; Down enters the results once they are available. Up/Down moves through the displayed document links, Enter opens the focused document through its normal link, and Escape or Up from the first result returns to search without changing its query. Down at the last result stays there; More retains its explicit button. Focused links use the [shared neutral-grey result fill](CSS_Ownership.md#search-result-highlight) without an outline. Tab, modified keys, composition input and tree navigation retain their existing behavior.

The browser Search controller binds the supplied mounted search input and the retained results list for the page lifetime. Arrow movement uses rendered sibling rows without another results array, active-row state, query pass, document read or history write. Consuming a pending debounce reuses ordinary Search loading, matching and failure handling without a separate request or delayed focus transfer. Keyboard focus alone does not change the currently displayed document or its existing `aria-current` result marker.

The 2026-10-24 keyboard change passed focused lint for `docs-viewer-search-controller.js` and `docs-viewer-app-runtime.js`, whitespace checks, public projection consistency and `bin/site-validate`. The distinct code and Redundancy And Defensive Behavior Review traced the mounted input handoff, pending/cached/loading/empty/error results, Search/Recent view ownership, first/last rows, More, native link activation, modified/composition keys and page-lifetime binding. Existing loading and match caches remain authoritative; focus movement adds no data acquisition, result inventory, validation, fallback, compatibility alias or recovery work. No actionable findings remained. Tests and browser interaction were not run. Keyboard focus/fill, scrolling, Enter opening and document return remain manual checks after force-reloading Docs Viewer or Site Preview. No document/media generation, Search rebuild, Publish, deployment, commit or push ran.

Opening a result, pinned Related link or in-app document-content link preserves the active list, query, paging and list scroll. Only exact ordinary or collection/document identity determines the current-document marker; a destination outside the displayed results leaves no row marked current. These links leave the tree's explicit selection, expansion and position intact. Related links retain their independent Info capture and lifecycle, including release on Source entry. Clearing Search or toggling Recent off reveals the retained tree and keeps the current exact document and heading. Recent clears an active query; typing a non-empty query switches from Recent to Search.

The Index panel owns its active tree/Search/Recent view, query, visible count, tree selection/expansion and list scroll independently of document navigation. Control adjustments replace the current URL without adding a document history entry. Back restores the immediate caller's exact document/report and reading position, consumes that return context and preserves the panel as currently configured; it cannot reopen Recent or reinstate an earlier Search query. Result highlighting follows the restored target using existing mounted rows. The restored document URL retains the panel's current `q`; initial/reloaded routes apply their URL query once. Native browser destinations outside the current/caller pair reload by exact URL. A view-only change does not remount the document. Matching query/index state reuses mounted rows and cached matches, and More slices that ranking in memory. Switching visibility reloads neither the Index nor either list. Committed metadata updates an existing retained Search record's title/summary/update-date postings and Recent label/order; Delete removes the target from their projections. This changes no saved Search file, body postings, coverage or membership policy. Explicit Search rebuild and authoritative Index refresh keep their separate owners.

## Extension Boundary

Site-search collection inclusion is configuration policy, independent of collection registration and publication eligibility. Included collections reuse the shared schema, tokenizer, reader and query engine. Collection-scoped full-text search remains a separately specified feature.

The practical ceiling remains one client-loaded static index. Short prefixes can return broad result sets after full-text adoption; snippets, highlighting, stemming, synonyms, spelling correction, phrase positions, and section results remain outside the current contract.
