---
doc_id: search-change-log
title: Search Change Log
last_updated: 2026-03-29
parent_id: search
sort_order: 3
---

# Search Change Log

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
