---
doc_id: search-next-steps
title: Search Next Steps
last_updated: 2026-03-31
parent_id: search
sort_order: 90
---

# Search Next Steps

This document collects the main follow-up areas for search so they are not buried inside the implementation-facing docs.

The current implementation is already live across:

- `catalogue` on `/search/`
- `studio` inline on `/docs/`
- `library` inline on `/library/`

The items below are refinement areas, not part of the current build state.

## Build Ownership And Pipeline Boundaries

The largest structural follow-up is to keep moving search assembly toward a search-owned pipeline, especially for `catalogue`.

Detailed references:

- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Pipeline Target Architecture](/docs/?scope=studio&doc=search-pipeline-target-architecture)
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)

## Policy And Config Extraction

The dedicated search policy file already exists for runtime shell behaviour, but ranking, field participation, and build-time policy are still largely code-owned.

Detailed references:

- [Search Config Architecture](/docs/?scope=studio&doc=search-config-architecture)
- [Search Config Implementation Note](/docs/?scope=studio&doc=search-config-implementation-note)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)

## Ranking And Field Refinement

The current ranking and field model is intentionally simple. The main follow-up work is to decide which fields should stay active, which should become stronger, and whether the current score bands remain the right tradeoff.

Detailed references:

- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)

## Tag-Aware Search

Tag fields are already serialized for `catalogue`, but they are not active in v1 ranking or filtering. A later pass can decide when tag coverage is strong enough to justify making them first-class search inputs.

Detailed references:

- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)

## Result Shaping And Diversification

The current runtime returns a flat ranked list. If redundancy and hierarchy become a stronger problem, the next layer is result shaping rather than more scoring complexity inside the base ranking model.

Detailed references:

- [Search Result Shaping](/docs/?scope=studio&doc=search-result-shaping)
- [Search Result Shaping draft JSON](/docs/?scope=studio&doc=search-result-shaping-json)
- [Search Result Shaping draft slimmer JSON](/docs/?scope=studio&doc=search-result-shaping-json-slimmer)

## Prose And Payload Expansion

The current artifacts stay compact by avoiding body-prose indexing. If prose search is added later, it should be treated as an additional payload or shard decision rather than inflating the base indexes without review.

Detailed references:

- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Pipeline Target Architecture](/docs/?scope=studio&doc=search-pipeline-target-architecture)

## UI And Accessibility Refinement

The current UIs are intentionally simple. The main follow-up areas are keyboard behaviour, richer error/loading treatment, and deciding whether any future scopes should use the dedicated `/search/` route rather than inline docs-viewer search.

Detailed references:

- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)
