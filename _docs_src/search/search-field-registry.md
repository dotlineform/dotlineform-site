---
doc_id: search-field-registry
title: Search Field Registry
last_updated: 2026-03-29
parent_id: search
sort_order: 30
---

# Search Field Registry

## Purpose

This document defines how fields in the search index participate in the current search system.

It is not a raw schema definition. Its job is to answer questions such as:

- which fields are actively searched in v1
- which fields are displayed but not searched
- which fields are present for future filtering or ranking work
- which fields exist mainly as derived search support

This is the main review surface for field-level search policy.

## Scope

This document applies to fields in the current base search index and describes their role in search behaviour.

It covers:

- search participation
- result-display role
- filter suitability
- current importance class
- current match modes
- future-reserved fields that exist in the schema but are not yet active in search policy

It does not define precise scoring tiers or normalization algorithms.

## Relationship to other documents

- [Search Index Schema](/docs/?doc=search-index-schema) defines what fields exist and what they mean
- [Search Field Registry](/docs/?doc=search-field-registry) defines how those fields behave in search
- [Search Ranking Model](/docs/?doc=search-ranking-model) defines how field matches are prioritised
- [Search Normalisation Rules](/docs/?doc=search-normalisation-rules) defines how field values are transformed for retrieval
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour) defines how search results are presented

## Field registry principles

The current registry follows these principles.

### Explicit

Every field should have a known role, even if that role is currently “stored but not active.”

### Minimal

Fields should not influence relevance unless they improve known-item lookup or discovery clearly enough to justify the added noise.

### Reviewable

Field policy should be understandable without reading the generator and runtime side by side.

### Distinct

The registry should separate:

- fields present in the serialized schema
- fields currently used by v1 search matching
- fields currently used only for display
- fields reserved for future ranking or filtering

## Registry table

Current field-policy registry:

| Field name | Searchable in v1 | Filterable now | Filterable later | Displayed in results | Importance | Match modes in v1 | Field class | Notes |
|---|---|---:|---:|---:|---|---|---|---|
| `kind` | no | yes | yes | yes | none | none | structural | current UI filter field and kind badge |
| `id` | yes | no | optional | yes | high | exact, prefix | structural | strong known-item lookup field |
| `title` | yes | no | no | yes | high | exact, prefix, token | structured | strongest human-readable retrieval field |
| `href` | no | no | no | yes | none | none | support | navigation target only |
| `year` | indirect | no | yes | indirect | low | via `search_terms` / `search_text` | structured | included in derived fields, not scored as its own dedicated tier |
| `date` | indirect | no | yes | indirect | low | via `search_terms` / `search_text` | structured | same policy as `year` |
| `display_meta` | indirect | no | no | yes | low | via `search_terms` / `search_text` | structured | rendered and also folded into derived search fields |
| `series_ids` | indirect | no | yes | no | medium | via `search_terms` | structured | present in derived token bundle |
| `series_titles` | yes | no | yes | yes | medium | contains | structured | explicit mid-tier ranking field for works |
| `medium_type` | yes | no | yes | yes | medium | contains | structured | explicit mid-tier ranking field for works |
| `storage` | yes | no | yes | no | low-medium | contains | structured | searched in v1, not displayed in current UI |
| `series_type` | yes | no | yes | yes | low-medium | contains | structured | searched in v1 and displayed for series |
| `tag_ids` | no | no | yes | no | none in v1 | none | structured | stored for future structured filtering |
| `tag_labels` | no | no | yes | no | none in v1 | none | structured | stored for future ranking and possibly filter UI |
| `search_terms` | yes | no | no | no | high support | exact, prefix | derived | primary derived retrieval field |
| `search_text` | yes | no | no | no | low fallback | substring | derived | broad fallback field only |

## Field classes

The current implementation is well described by four field classes.

### Structured

Fields that represent meaningful source content or metadata.

Current examples:

- `title`
- `year`
- `date`
- `display_meta`
- `series_ids`
- `series_titles`
- `medium_type`
- `storage`
- `series_type`
- `tag_ids`
- `tag_labels`

### Structural

Fields that define record identity or type rather than descriptive content.

Current examples:

- `kind`
- `id`

### Derived

Fields generated specifically to support retrieval.

Current examples:

- `search_terms`
- `search_text`

### Support

Fields used by the UI or runtime but not intended to affect relevance.

Current example:

- `href`

These four classes are sufficient for the current v1 implementation.

## Field definitions

### `kind`
Searchable in v1: no  
Filterable now: yes  
Displayed in results: yes  
Importance: none  
Match modes: none  
Field class: structural  

Purpose:
Defines the content type of the record.

Notes:
`kind` is not queried through free-text search in v1. It is used by the explicit UI filter and displayed as the result kind label.

### `id`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: yes  
Importance: high  
Match modes: exact, prefix  
Field class: structural  

Purpose:
Provides stable direct lookup for known-item search.

Notes:
The runtime has dedicated high-score tiers for exact id matches and id-prefix matches.

### `title`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: yes  
Importance: high  
Match modes: exact, prefix, token  
Field class: structured  

Purpose:
Primary human-readable retrieval field and primary result label.

Notes:
The runtime has dedicated tiers for exact title, title prefix, and token-oriented title matching.

### `href`
Searchable in v1: no  
Filterable now: no  
Displayed in results: yes  
Importance: none  
Match modes: none  
Field class: support  

Purpose:
Provides the navigation target for a result row.

Notes:
`href` is not part of search relevance.

### `year`
Searchable in v1: indirect  
Filterable now: no  
Displayed in results: indirect  
Importance: low  
Match modes: via derived fields  
Field class: structured  

Purpose:
Carries year-oriented chronology for year-based records.

Notes:
`year` contributes to the derived token bundle and can therefore match queries, but the runtime does not currently give it a dedicated score tier.

### `date`
Searchable in v1: indirect  
Filterable now: no  
Displayed in results: indirect  
Importance: low  
Match modes: via derived fields  
Field class: structured  

Purpose:
Carries canonical date information for date-based records.

Notes:
Like `year`, it is searchable through derived fields rather than through a dedicated date-specific score tier.

### `display_meta`
Searchable in v1: indirect  
Filterable now: no  
Displayed in results: yes  
Importance: low  
Match modes: via derived fields  
Field class: structured  

Purpose:
Provides compact result metadata such as year display or moment date display.

Notes:
It is displayed directly and also folded into derived search tokens.

### `series_ids`
Searchable in v1: indirect  
Filterable now: no  
Displayed in results: no  
Importance: medium  
Match modes: via derived fields  
Field class: structured  

Purpose:
Carries canonical series relationships for records, mainly works.

Notes:
Useful for future structured filtering and currently contributes to derived recall.

### `series_titles`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: yes  
Importance: medium  
Match modes: contains  
Field class: structured  

Purpose:
Provides human-readable related series context.

Notes:
The runtime has an explicit metadata tier for series-title matching.

### `medium_type`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: yes  
Importance: medium  
Match modes: contains  
Field class: structured  

Purpose:
Provides structured medium information for works.

Notes:
The runtime has an explicit metadata tier for `medium_type` matching.

### `storage`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: no  
Importance: low-medium  
Match modes: contains  
Field class: structured  

Purpose:
Provides structured work storage metadata.

Notes:
The runtime can rank matches on `storage`, but the current UI does not display it in result rows.

### `series_type`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: yes  
Importance: low-medium  
Match modes: contains  
Field class: structured  

Purpose:
Provides structured series classification metadata.

Notes:
The runtime can rank matches on `series_type`, and the current UI may display it for series records.

### `tag_ids`
Searchable in v1: no  
Filterable now: no  
Displayed in results: no  
Importance: none in v1  
Match modes: none  
Field class: structured  

Purpose:
Carries canonical assigned tag ids.

Notes:
This is a future-facing field. It is not currently used by ranking or UI filters.

### `tag_labels`
Searchable in v1: no  
Filterable now: no  
Displayed in results: no  
Importance: none in v1  
Match modes: none  
Field class: structured  

Purpose:
Carries display labels for assigned tags.

Notes:
This field exists to support future tag-aware search behaviour once tag coverage is good enough.

### `search_terms`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: no  
Importance: high support  
Match modes: exact, prefix  
Field class: derived  

Purpose:
Provides the main derived token bundle used for exact and prefix-oriented matching support.

Notes:
This is the most important derived field in the current implementation.

### `search_text`
Searchable in v1: yes  
Filterable now: no  
Displayed in results: no  
Importance: low fallback  
Match modes: substring  
Field class: derived  

Purpose:
Provides broad fallback recall when more specific fields do not match strongly enough.

Notes:
This field should remain weaker than structured-field and `search_terms` matches.

## Searchability rules

Current inclusion logic in practice:

- fields are actively searchable in v1 when the runtime gives them direct matching behaviour or when they contribute materially through the derived fields
- fields remain non-searchable when they are purely navigational or when using them now would add more noise than value

Current policy split:

- direct active search fields:
  - `id`
  - `title`
  - `series_titles`
  - `medium_type`
  - `storage`
  - `series_type`
  - `search_terms`
  - `search_text`
- indirect searchable fields through derivation:
  - `year`
  - `date`
  - `display_meta`
  - `series_ids`
- present but not active in v1 search:
  - `kind`
  - `href`
  - `tag_ids`
  - `tag_labels`

## Filterability rules

Current implemented filter surface:

- `kind`

Current fields that are good candidates for future structured filters:

- `kind`
- `year`
- `date`
- `series_ids`
- `medium_type`
- `storage`
- `series_type`
- `tag_ids`

Current fields that should not become structured filters:

- `title`
- `href`
- `search_terms`
- `search_text`
- `display_meta`

V1 intentionally keeps filtering minimal and explicit.

## Display rules

Current v1 result display roles:

- `kind` as a small type label
- `title` as the primary result label and link text
- `href` as the link destination
- `id` as the secondary identifier line
- `display_meta` as secondary metadata when present
- `medium_type` added to work metadata rows when present
- `series_titles` added to work metadata rows when present
- `series_type` added to series metadata rows when present

Current fields stored but not displayed:

- `year`
- `date`
- `series_ids`
- `storage`
- `tag_ids`
- `tag_labels`
- `search_terms`
- `search_text`

## Importance classes

Current meaning of the registry importance labels:

### High

Fields strongly associated with known-item lookup and primary relevance.

Current examples:

- `id`
- `title`
- `search_terms` as a derived support field

### Medium

Fields useful for discovery and context, but weaker than title or id.

Current examples:

- `series_titles`
- `medium_type`
- `series_ids` as structured context

### Low-medium

Fields that help recall in narrower cases but should not dominate results.

Current examples:

- `storage`
- `series_type`

### Low

Fields that support recall but should remain weak and contextual.

Current examples:

- `year`
- `date`
- `display_meta`
- `search_text`

### None

Fields not intended to contribute to relevance in v1.

Current examples:

- `kind`
- `href`
- `tag_ids`
- `tag_labels`

## Match mode policy

Current field-policy fit by match mode:

- `id`
  - exact
  - prefix
- `title`
  - exact
  - prefix
  - token-oriented title matching
- `series_titles`
  - contains
- `medium_type`
  - contains
- `storage`
  - contains
- `series_type`
  - contains
- `search_terms`
  - exact
  - prefix
- `search_text`
  - substring fallback

Fields like `year`, `date`, and `display_meta` do not currently have dedicated independent match policies; they enter the runtime through `search_terms` and `search_text`.

## Derived field policy

Current derived fields:

- `search_terms`
- `search_text`

Why they exist:

- to make the browser runtime simpler
- to avoid reconstructing heterogeneous field bundles for every query
- to provide one explicit exact/prefix support field and one broad fallback field

Current policy:

- derived fields are useful for v1 simplicity and performance
- derived fields should not erase the distinction between stronger structured matches and weaker fallback matches
- `search_terms` is a primary support field
- `search_text` is a fallback field only
- derived fields currently lose some field provenance, which is acceptable for v1 but may need refinement later

## Common field-policy questions

Current answers in v1:

- should a field remain searchable if it duplicates stronger fields
  - only if it improves recall without overwhelming ranking
- should a display field also be searchable
  - sometimes; `display_meta` is an example of a displayed field that contributes indirectly through derivation
- should canonical ids and human-readable labels both be indexed
  - yes
- should derived fields be used only as fallback
  - `search_text` yes; `search_terms` no, because it is central to v1 matching
- should empty array fields still be present in the schema
  - yes, where empty-list semantics are meaningful

## Open questions

Field-registry questions for later phases:

- whether tag fields should become active ranking and filtering fields once coverage improves
- whether `storage` is useful enough to remain an active search field
- whether some metadata terms should keep participating directly or only through derived fallback
- whether future prose search should introduce new field classes or provenance-aware derived fields

## Out of scope for this document

This document does not define:

- full raw schema structure
- low-level normalization rules
- exact scoring numbers
- UI event handling
- generator implementation details
