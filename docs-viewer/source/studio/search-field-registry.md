---
doc_id: search-field-registry
title: Search Field Registry
added_date: 2026-04-01
last_updated: 2026-05-19
parent_id: search
---
# Search Field Registry

This document defines how fields in the search index participate in the current search system.
It is the field-level policy index rather than a raw schema definition.

## Purpose

Use this section to answer:

- which fields are actively searched in v1
- which fields are displayed but not searched
- which fields are serialized but inactive in the current search model
- which fields exist mainly as derived search support

It does not define precise scoring tiers, low-level normalization algorithms, UI event handling, or generator implementation details.

## Relationship To Other Documents

- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema) defines what fields exist and what they mean.
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry) defines how those fields behave in search.
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model) defines how field matches are prioritised.
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules) defines how field values are transformed for retrieval.
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour) defines how search results are presented.

## Principles

- Every field should have a known role, even if that role is currently stored but inactive.
- Fields should not influence relevance unless they improve known-item lookup or discovery clearly enough to justify the added noise.
- Field policy should be understandable without reading the builder and runtime side by side.
- The registry should separate serialized schema fields, v1 matching fields, display-only fields, and inactive stored fields.

## Child References

- [Registry Table](/docs/?scope=studio&doc=search-field-registry-table)
- [Field Definitions](/docs/?scope=studio&doc=search-field-registry-definitions)
- [Field Policy](/docs/?scope=studio&doc=search-field-registry-policy)
