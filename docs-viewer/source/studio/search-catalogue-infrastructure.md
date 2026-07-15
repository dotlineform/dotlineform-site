---
doc_id: search-catalogue-infrastructure
title: Catalogue Search
added_date: 2026-06-02
last_updated: 2026-07-15
parent_id: search
viewable: true
---
# Catalogue Search

Catalogue Search is the public known-item and metadata lookup for works and series at `/catalogue/search/`.

## Execution Path

1. Catalogue builders produce public series/works indexes and per-work payloads.
2. `studio/services/catalogue/search/build_search.py` projects those records into the public search index.
3. `studio/services/catalogue/search/build_config.json` validates source-family and emitted-field dependencies.
4. `/catalogue/search/` loads runtime policy and the static index.
5. `site/assets/js/search/catalogue-search-runtime.js` normalizes, filters, scores, sorts, and renders results in the browser.

Catalogue search deliberately consumes public catalogue projections rather than canonical source or Analytics tag data. This keeps the public search payload inside the same publication boundary as the routes it links to.

## Capability Summary

- searches works and series together
- supports exact and prefix identity/title matches
- uses structured series and medium context below known-item matches
- requires every query token to be represented before scoring a result
- filters by record kind in the client
- loads additional results in fixed batches
- offers opt-in performance instrumentation through query/storage flags

The exact score bands and entry fields are code. `search_text` is broad fallback; it is not a full-text body index.

## Registries And Config

- [Search Build Config](/docs/?scope=studio&doc=config-search-build-json) owns build dependencies and targeted-update policy.
- [Catalogue Search Policy](/docs/?scope=studio&doc=config-search-policy-json) owns the public route's timing, labels, messages, and index URL.
- `studio/services/catalogue/catalogue_public_paths.py` owns public catalogue/search paths used by Python services.

## Extension Method

For a new searchable Catalogue field:

1. confirm it belongs in a public projection
2. add its source-family mapping to build config
3. project it in the builder
4. decide whether it affects matching, display, or filtering in the runtime
5. update focused builder/runtime coverage

Do not publish canonical-only fields just to make search easier.

## Weak Spots

- Targeted updates are create-only. Updates and deletes fall back to a full search build.
- Build config validates provenance declarations, but it is not a full JSON schema for index records.
- The policy JSON has JavaScript fallback defaults, so changes must keep both deliberate.
- Similar normalization and scoring code exists in Docs Viewer search but is not shared.
- `tagLabels` is normalized by the runtime although the current builder does not emit Analytics tags; it should not be mistaken for an active integration.
