---
doc_id: search-change-log
title: Search Change Log
last_updated: 2026-03-30
parent_id: search
sort_order: 3
---

# Search Change Log

## [2026-03-30] Moved catalogue search to the public `/search/` page and removed the Studio route

**Status:** implemented

**Area:** UI

**Summary:**  
Moved the current catalogue search page from `/studio/search/` to the public `/search/` route, removed the Studio page entirely, and added a catalogue search entry point to the `/series/` toolbar.

**Reason:**  
The agreed search contract now uses one public top-level search route with explicit scope context. Search needed to move out of Studio before later scope expansion so the public UI, route vocabulary, and entry-point model all align.

**Effect:**  
`/search/?scope=catalogue` is now the current public route, `/studio/search/` no longer exists, the `/series/` toolbar now includes a search CTA for the catalogue scope, and the public search page shows explicit scope context while continuing to use the same in-memory catalogue search runtime.

**Affected files/docs:**  
- `search/index.md`
- `studio/search/index.md`
- `series/index.md`
- `assets/css/main.css`
- `assets/studio/js/studio-search.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Search](/docs/?doc=search)
- [Search Overview](/docs/?doc=search-overview)
- [Search Public UI Contract](/docs/?doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)
- [Search Validation Checklist](/docs/?doc=search-validation-checklist)

**Notes:**  
The runtime is still the same shared search module and still only supports the `catalogue` scope. This change is route and entry-point migration, not the later modular multi-domain refactor.

## [2026-03-30] Removed visible kind filters from the Studio search page and required scope context

**Status:** implemented

**Area:** UI

**Summary:**  
Updated the current Studio search page so it always searches across all indexed catalogue kinds, no longer exposes the `all` / `works` / `series` / `moments` filter buttons, and requires a valid `scope` URL parameter before the page becomes usable.

**Reason:**  
The search UI needs to align with the newer scope-led public-search direction before the route moves out of Studio. Exposing per-kind buttons no longer matches that direction, while a required URL scope makes the page behavior closer to the future public contract.

**Effect:**  
`/studio/search/?scope=catalogue` is now the valid Studio route, the visible filter row is gone, catalogue search remains internally mixed across works, series, and moments, and loading the page without a valid scope now shows a missing-context message instead of an ambiguous fallback search UI.

**Affected files/docs:**  
- `studio/search/index.md`
- `assets/studio/js/studio-search.js`
- `assets/studio/data/studio_config.json`
- [Search Overview](/docs/?doc=search-overview)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)
- [Search Validation Checklist](/docs/?doc=search-validation-checklist)

**Notes:**  
This change intentionally does not remove the underlying internal support for per-kind filtering from the search runtime; it only removes that granularity from the current UI.

## [2026-03-30] Defined the public search route and scope-led UI contract

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated public-search contract doc that defines `/search/` as the shared public route, uses `scope` plus `q` as the URL contract, and establishes scope-owned page CTAs as the preferred public entry model.

**Reason:**  
Search is about to grow beyond the current Studio-first catalogue scope. The public route and UI model needed to be clarified before a larger modular refactor adds domain-specific search artifacts and policy/config.

**Effect:**  
The search docs now explicitly prefer a scope-led public model such as `/search/?scope=catalogue&q=...`, reserve future scope names such as `studio` and `library`, and avoid an ambiguous top-level public nav item called `search` as the default interaction pattern.

**Affected files/docs:**  
- [Search Public UI Contract](/docs/?doc=search-public-ui-contract)
- [Search](/docs/?doc=search)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)

**Notes:**  
This is a documentation-level contract decision. The public `/search/` route and the modular domain search architecture are not implemented yet.

## [2026-03-29] Added a concrete staged implementation note for search config extraction

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a focused implementation note that turns the search config architecture direction into a concrete phase sequence, beginning with runtime UI policy extraction and deferring ranking and field policy to later stages.

**Reason:**  
The architecture doc defined the boundary, but the next implementation step still needed a concrete shape in code terms so the config change can be reviewed and executed without ambiguity.

**Effect:**  
Search config work now has a documented first cut, a proposed `search_policy.json` shape, and a clearer roadmap for later phases such as ranking bands, field participation, and shared runtime/build policy.

**Affected files/docs:**  
- [Search Config Architecture](/docs/?doc=search-config-architecture)
- [Search Config Implementation Note](/docs/?doc=search-config-implementation-note)
- [Search](/docs/?doc=search)

**Notes:**  
This remains a documentation-level implementation plan; the config layer itself is not yet implemented.

## [2026-03-29] Normalized published search-doc references to docs-viewer links

**Status:** implemented

**Area:** architecture

**Summary:**  
Converted published-doc references across the search document set to use `/docs/?doc=...` links instead of raw filenames or legacy doc paths.

**Reason:**  
Search docs are now intended to be read through the docs viewer as a linked system. Raw filenames were inconsistent with that review flow and made navigation less direct.

**Effect:**  
Readers can now move between published search docs through stable viewer links, while non-doc file paths and unpublished docs remain explicit as plain repo references.

**Affected files/docs:**  
- [Search Overview](/docs/?doc=search-overview)
- [Search Field Registry](/docs/?doc=search-field-registry)
- [Search Ranking Model](/docs/?doc=search-ranking-model)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?doc=search-build-pipeline)
- [Search Normalisation Rules](/docs/?doc=search-normalisation-rules)
- [Search Validation Checklist](/docs/?doc=search-validation-checklist)
- [Search Config Architecture](/docs/?doc=search-config-architecture)
- [Search Change Log Guidance](/docs/?doc=search-change-log-guidance)

**Notes:**  
This is a documentation-navigation change only; it does not alter search behaviour or schema.

## [2026-03-29] Reviewed and split the search document set into focused implementation docs

**Status:** implemented

**Area:** architecture

**Summary:**  
Replaced the earlier broad v1 planning-only search notes with a focused documentation set covering overview, schema, field policy, normalization, ranking, UI behaviour, build pipeline, validation, config architecture, and change-log maintenance.

**Reason:**  
The search system had moved beyond a single planning note. Review and future changes required smaller documents tied directly to the implemented v1 behaviour.

**Effect:**  
Search can now be reviewed one concern at a time, and future implementation changes have a clearer documentation surface to update alongside code.

**Affected files/docs:**  
- [Search Overview](/docs/?doc=search-overview)
- [Search Index Schema](/docs/?doc=search-index-schema)
- [Search Field Registry](/docs/?doc=search-field-registry)
- [Search Normalisation Rules](/docs/?doc=search-normalisation-rules)
- [Search Ranking Model](/docs/?doc=search-ranking-model)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?doc=search-build-pipeline)
- [Search Validation Checklist](/docs/?doc=search-validation-checklist)
- [Search Config Architecture](/docs/?doc=search-config-architecture)
- [Search Change Log Guidance](/docs/?doc=search-change-log-guidance)

**Notes:**  
This documentation split is now part of the review surface for future search work and should be maintained alongside implementation changes.

## [2026-03-29] Defined the search config externalisation boundary and recommended staged adoption

**Status:** proposed

**Area:** architecture

**Summary:**  
Defined a structural direction for search policy externalisation: keep `studio_config.json` narrow, introduce a dedicated `search_policy.json`, and externalize runtime UI behaviour before ranking bands and field activation policy.

**Reason:**  
Search already has its own artifact, UI surface, and review docs. Config boundaries should be set before the next growth phase adds more fields, filters, and prose-related complexity.

**Effect:**  
Provides a clear basis for the next structural implementation step without prematurely externalizing all search logic.

**Affected files/docs:**  
- [Search Config Architecture](/docs/?doc=search-config-architecture)
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`

**Notes:**  
This is a documented direction, not yet an implemented config layer.

## [2026-03-29] Added batched result expansion to the Studio search UI

**Status:** implemented

**Area:** UI

**Summary:**  
Changed the Studio search page to render results in batches of `50` and reveal additional results with a `more` control instead of showing only a fixed hard cap.

**Reason:**  
The original result cap hid lower-ranked matches with no way to inspect more of the ranked set. Incremental expansion keeps the DOM lighter while preserving access to additional results.

**Effect:**  
Large result sets remain performant and readable, and the user can inspect more results without changing query or filter state.

**Affected files/docs:**  
- `assets/studio/js/studio-search.js`
- `studio/search/index.md`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)

**Notes:**  
The initial implementation had a runtime bug from an obsolete constant; that was fixed immediately in the same development phase and the current behaviour is the corrected batched model.

## [2026-03-29] Implemented Studio-first search with a generated base search index

**Status:** implemented

**Area:** build pipeline

**Summary:**  
Implemented v1 Studio search backed by a generated `assets/data/search_index.json` artifact and an in-memory client-side search runtime for works, series, and moments.

**Reason:**  
Search needed a simple but scalable in-house implementation that avoided external services and fit the existing static-site pipeline.

**Effect:**  
The site now has a working Studio-first search surface with deterministic ranking, build-time-generated search data, kind filtering, and a path toward later field and prose expansion.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `assets/data/search_index.json`
- `assets/studio/js/studio-search.js`
- `studio/search/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-data.js`
- [Search Build Pipeline](/docs/?doc=search-build-pipeline)
- [Search Ranking Model](/docs/?doc=search-ranking-model)
- [Search Index Schema](/docs/?doc=search-index-schema)

**Notes:**  
This implementation keeps search as a dedicated artifact stage inside the existing generator rather than introducing a separate search builder.
