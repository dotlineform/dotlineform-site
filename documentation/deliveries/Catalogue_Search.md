---
draft: false
doc_id: d-20260602-160839-4ebe27
title: Catalogue Search
added_date: 2026-06-02 16:08:39
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260331-000000-5dcf32

---
# Catalogue Search

Historical record of the standalone Work and Series search. Its static runtime and saved data belong to the frozen `site/archive/` snapshot. The former builder and dependency registry are retired. [Catalogue Archive](../studio/Catalogue_Archive.md#historical-reader-references) · [Current Search](../studio/Search.md)

## Execution Path

1. Before the freeze, `studio/services/catalogue/search/build_search.py` read canonical Catalogue source and selected published Works and Series for the public search index.
2. `studio/services/catalogue/search/build_config.json` declared the source families, emitted-field dependencies and permitted targeted operations.
3. The archived `/archive/search/` route loads the [saved policy](../../site/archive/assets/data/search/policy.json) and [static index](../../site/archive/assets/data/search/catalogue/index.json).
4. The frozen [search runtime](../../site/archive/assets/js/search/catalogue-search-runtime.js) normalizes, filters, scores, sorts and renders results in the browser.

Selecting published records at build time kept the search entries within the same publication boundary as the routes they linked to.

## Capability Summary

- searches works and series together
- supports exact and prefix identity/title matches
- uses structured series and medium context below known-item matches
- requires every query token to be represented before scoring a result
- filters by record kind in the client
- loads additional results in fixed batches
- offers opt-in performance instrumentation through query/storage flags

The exact score bands and entry fields are code. `search_text` is broad fallback; it is not a full-text body index.

## Former Build Dependencies

The registry assigned Catalogue ownership to source families and declared which families supplied each emitted field, including derived fields. The builder failed on undeclared emitted fields. The Catalogue policy was `additive_only`: creating Works or Series could merge those entries into a saved index, while edits and deletes required a complete build. The registry vocabulary included `record_update` and `full_rebuild`; implementing a new invalidation mode also required builder changes.

[Catalogue Search Policy](Catalogue_Search_Policy.md) describes the separate browser configuration for timing, labels, messages and the index URL.

## Weak Spots

- The build registry checked field provenance declarations. Record shape came from the builder.
- The policy JSON has JavaScript fallback defaults, so changes must keep both deliberate.
- Similar normalization and scoring code exists in Docs Viewer search but is not shared.
- The runtime normalized `tagLabels` although the builder emitted no Analytics tags.
