---
doc_id: search
title: "search"
added_date: 2026-05-26
last_updated: 2026-06-26
---

> _public_site/assets/data/search/catalogue/index.json is 1.5MB, which is probably not good for a runtime asset.

It is worth watching, but it is less bad than the raw file size suggests.

Current facts:
- raw JSON: about `1.5 MB`
- gzip-compressed locally: about `76 KB`
- live GitHub Pages response: `content-encoding: gzip`, `content-length: 83,735`
- entries: `2,135`
- loaded by the dedicated catalogue search page, not every route

So the network cost is roughly 80 KB, which is acceptable for a search page. The browser still has to parse 1.5 MB of JSON after decompression, but for 2,135 entries that is probably fine unless you see search-page delay on slower devices.

The main bloat is duplicated text:
- `search_terms`: ~296 KB raw
- `search_text`: ~237 KB raw

If we optimize later, I would look at:
1. Remove either `search_terms` or `search_text` if both are not needed.
2. Use shorter field names only if parse/download becomes measurable.
3. Split by kind only if the UI can search subsets.
4. Lazy-load only after the user focuses/types in search, if it is currently loaded immediately.

I would not rush to change it now. Because it is gzip-served and route-specific, this is more “worth a performance review” than “bad runtime asset.”

> is it lazy loaded at the moment, because that would be a quick optimisation?

No. The search index is loaded on catalogue search page init.

Current flow in `assets/js/catalogue-search.js`:

1. `DOMContentLoaded`
2. `initSearchPage()`
3. load search policy
4. set status to `loading search index...`
5. fetch `/assets/data/search/catalogue/index.json`
6. normalize all entries
7. render prompt/results

So it is route-scoped, but not interaction-lazy.

A quick optimisation would be to defer `loadScopedSearchEntries()` until either:

- the user types the first valid query, or
- the URL already has a search query parameter

That would make `/catalogue/search/` cheap when opened casually, while preserving direct query links. The UI would initially show “Enter a search query.” and only switch to “loading search index...” after input.

This is a sensible small follow-up. It touches only `assets/js/catalogue-search.js` plus a focused smoke/test around:
- empty search page does not fetch index on load
- typing fetches index once
- query-in-URL still fetches and renders immediately.