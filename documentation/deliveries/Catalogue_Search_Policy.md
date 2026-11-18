---
draft: false
doc_id: d-20260331-154730-885d0f
title: Catalogue Search Policy
added_date: 2026-03-31 15:47:30
last_updated: "2026-08-09 22:00:00"
parent_id: d-20260602-160839-4ebe27

---
# Catalogue Search Policy

Historical reference for the [saved policy](../../site/archive/assets/data/search/policy.json) on the frozen `/archive/search/` route. [Catalogue Archive](../studio/Catalogue_Archive.md#historical-reader-references)

## It Owns

- live/Enter search behaviour and minimum query length
- debounce and result batch sizes
- enabled search scopes
- static index URL and back-route presentation
- input labels, status messages, result labels, and instrumentation copy

[The archived route module](../../site/archive/assets/js/catalogue-search.js) loads the file at startup. [The archived policy module](../../site/archive/assets/js/search/search-policy.js) validates values and supplies defaults.

## Boundary

The policy controls the archived route's browser behaviour. [Catalogue Search](Catalogue_Search.md#former-build-dependencies) records how the former builder made the index, and the [archived runtime](../../site/archive/assets/js/search/catalogue-search-runtime.js) owns ranking. Active Docs Viewer Search has its own [index contract](../studio/Docs_Search_Index.md).

## Weak Spot

The policy module duplicates the default policy so the route can run if the JSON fails to load. While the route was maintained, policy edits needed to account for both copies.
