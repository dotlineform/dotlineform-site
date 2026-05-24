---
doc_id: search-field-registry-table
title: Search Field Registry Table
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: search-field-registry
sort_order: 2100
---
# Search Field Registry Table

## Registry table

Current field-policy registry:

| Field name | Searchable in v1 | Filterable now | Stored for filtering | Displayed in results | Importance | Match modes in v1 | Field class | Notes |
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
| `series_type` | yes | no | yes | yes | low-medium | contains | structured | searched in v1 and displayed for series |
| `tag_ids` | no | no | yes | no | none in v1 | none | structured | stored in the current artifact but inactive in current filtering |
| `tag_labels` | no | no | yes | no | none in v1 | none | structured | stored in the current artifact but inactive in current ranking and filtering |
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
