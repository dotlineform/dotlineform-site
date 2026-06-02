---
doc_id: search-field-registry-definitions
title: Search Field Definitions
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: search-catalogue-infrastructure
---
# Search Field Definitions

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
Useful for structured filtering if that capability is enabled later and currently contributes to derived recall.

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

Notes:
This field exists in the current artifact so tag-aware search can be enabled later without reshaping the base record.

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
