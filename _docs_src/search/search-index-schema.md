---
doc_id: search-index-schema
title: Search Index Schema
last_updated: 2026-03-30
parent_id: search
sort_order: 20
---

# Search Index Schema

## Purpose

This document defines the current data contract for the generated search index used by site search.

It describes the actual serialized shape of `assets/data/search/catalogue/index.json`, the meaning of each field, and the difference between structured fields and derived search-support fields.

This is a schema document. It does not define ranking, UI behaviour, or detailed build flow.

## Scope

This document applies to the current base search artifact:

- `assets/data/search/catalogue/index.json`

It covers:

- the top-level payload shape
- the per-record schema
- required versus optional serialized fields
- cross-kind conventions shared by works, series, and moments

It does not attempt to define future prose shards or other later index partitions.

## Top-level index structure

The current top level is an object with two keys:

- `header`
- `entries`

`header` contains index-level metadata.

`entries` is a single flat array shared by all indexed content types. Works, series, and moments are not stored in separate top-level collections.

Current header shape:

```json
{
  "header": {
    "schema": "search_index_v1",
    "version": "blake2b-…",
    "generated_at_utc": "2026-03-29T13:31:21Z",
    "count": 2127
  },
  "entries": []
}
```

Header fields:

- `schema`
  schema identifier for the payload format
- `version`
  content-derived version hash for change detection
- `generated_at_utc`
  UTC generation timestamp
- `count`
  number of serialized entries in `entries`

## Record model

Each search record represents one searchable item:

- one work
- one series
- one moment

Every record carries enough data for the browser to:

- identify the item
- link to it
- render a compact result row
- evaluate matches against the current search model

The record model is intentionally compact. It does not duplicate full page content.

## Core record fields

The current serialized schema uses these fields.

| Field name | Type | Required in serialized output | Purpose | Notes |
|---|---|---:|---|---|
| `kind` | string | yes | identifies the content type | current values: `work`, `series`, `moment` |
| `id` | string | yes | canonical stable identifier | always serialized as a string |
| `title` | string | yes | primary display title and major search field | human-facing label |
| `href` | string | yes | site-relative destination path | current values are relative site paths |
| `year` | integer | no | year-based date value | used for works or series where available |
| `date` | string | no | canonical date string | currently used for moments |
| `display_meta` | string | no | compact display metadata | used in result rows and token generation |
| `series_ids` | array of strings | yes | associated series ids | empty array when none |
| `series_titles` | array of strings | yes | associated series titles | empty array when none |
| `medium_type` | string | no | structured work metadata | currently appears on works when populated |
| `storage` | string | no | structured work metadata | currently optional and often absent |
| `series_type` | string | no | structured series metadata | currently appears on series when populated |
| `tag_ids` | array of strings | yes | canonical assigned tag ids | empty array when none |
| `tag_labels` | array of strings | yes | display labels for assigned tags | empty array when none |
| `search_terms` | array of strings | yes | normalized token bundle used by runtime matching | derived at build time |
| `search_text` | string | yes | flattened broad-match string | derived at build time |

## Field definitions

### `kind`

Type: string  
Required: yes  
Purpose: identifies the indexed content type.  
Usage: filtering, type-aware rendering, and stable grouping semantics.  
Notes: current values are a controlled set: `work`, `series`, `moment`.

### `id`

Type: string  
Required: yes  
Purpose: canonical stable identifier for the indexed item.  
Usage: direct lookup, identity, sorting, and display.  
Notes: ids remain strings even when numerically shaped, such as `00533`.

### `title`

Type: string  
Required: yes  
Purpose: primary human-readable title.  
Usage: result display and major retrieval field.  
Notes: the generator falls back to the item id if a title is missing.

### `href`

Type: string  
Required: yes  
Purpose: target route for result navigation.  
Usage: result rendering.  
Notes: current values are relative site paths such as `/works/00533/`.

### `year`

Type: integer  
Required: no  
Purpose: canonical year value for year-based records.  
Usage: display support and token generation.  
Notes: serialized only when available; currently common on works and series.

### `date`

Type: string  
Required: no  
Purpose: canonical date value for date-based records.  
Usage: display support and token generation.  
Notes: currently used on moments.

### `display_meta`

Type: string  
Required: no  
Purpose: compact human-readable metadata summary for the result row.  
Usage: display and token generation.  
Notes: examples include year display strings and moment date display strings.

### `series_ids`

Type: array of strings  
Required: yes  
Purpose: canonical series relationships attached to the item.  
Usage: structured metadata and search support.  
Notes: works may contain related series ids; other kinds currently serialize `[]`.

### `series_titles`

Type: array of strings  
Required: yes  
Purpose: display-facing series relationships attached to the item.  
Usage: result display and search support.  
Notes: works may contain related series titles; other kinds currently serialize `[]`.

### `medium_type`

Type: string  
Required: no  
Purpose: structured work medium metadata.  
Usage: search support and result metadata display for works.  
Notes: omitted when empty.

### `storage`

Type: string  
Required: no  
Purpose: structured work storage metadata.  
Usage: reserved search support field.  
Notes: present in the logical schema, but may be absent from many or most current records.

### `series_type`

Type: string  
Required: no  
Purpose: structured series classification metadata.  
Usage: search support and result metadata display for series.  
Notes: omitted when empty.

### `tag_ids`

Type: array of strings  
Required: yes  
Purpose: canonical assigned tag ids.  
Usage: structured future-facing search metadata.  
Notes: currently populated from tag assignments; often empty because tag coverage is still sparse.

### `tag_labels`

Type: array of strings  
Required: yes  
Purpose: human-readable labels for assigned tags.  
Usage: future-facing search and review support.  
Notes: currently not used by the v1 ranking code, but present in the serialized schema.

### `search_terms`

Type: array of strings  
Required: yes  
Purpose: build-time-derived set of normalized discrete search tokens.  
Usage: exact-term and prefix-oriented runtime checks.  
Notes: may include canonical ids, titles, split title tokens, display metadata tokens, year/date text, related series terms, and structured metadata values when present.

### `search_text`

Type: string  
Required: yes  
Purpose: flattened broad-match text field derived from `search_terms`.  
Usage: fallback contains matching in the runtime.  
Notes: generated by joining `search_terms` with spaces.

## Display fields vs search fields

Fields used primarily for display:

- `title`
- `href`
- `display_meta`
- `series_titles`

Fields used primarily for search support:

- `search_terms`
- `search_text`

Fields used for both structured meaning and search support:

- `id`
- `year`
- `date`
- `series_ids`
- `medium_type`
- `storage`
- `series_type`
- `tag_ids`
- `tag_labels`

## Structured fields vs derived fields

Structured fields carried from source-like data:

- `kind`
- `id`
- `title`
- `href`
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

Derived fields generated specifically for search:

- `search_terms`
- `search_text`

This distinction matters because structured fields reflect semantic source data, while derived fields exist to make client-side matching simpler and faster.

## Optional and content-specific fields

Current serialization rules:

- fields with meaningful empty-list semantics are serialized as empty arrays:
  - `series_ids`
  - `series_titles`
  - `tag_ids`
  - `tag_labels`
- optional scalar fields are omitted when empty rather than serialized as `null`
- `year` and `date` are not both expected on every record
- `medium_type` and `storage` are work-oriented
- `series_type` is series-oriented

Current kind differences:

- works commonly have `year`, `display_meta`, `series_ids`, `series_titles`, and sometimes `medium_type`
- series commonly have `year`, `display_meta`, and sometimes `series_type`
- moments commonly have `date` and `display_meta`

## Field constraints and conventions

Important current conventions:

- ids are always strings
- links are site-relative paths
- array-valued relationship and tag fields serialize as arrays, not omitted scalars
- optional scalar fields are omitted when empty by the current generator
- `search_terms` values are already normalized at build time
- `search_text` is derived from `search_terms`, not authored independently

The runtime may create additional normalized in-memory variants, but those are not part of the serialized schema.

## Example records

Representative work record:

```json
{
  "kind": "work",
  "id": "00533",
  "title": "2 bodies monoprint",
  "href": "/works/00533/",
  "year": 2025,
  "display_meta": "2025",
  "series_ids": ["2-bodies"],
  "series_titles": ["2 bodies"],
  "medium_type": "drawing",
  "tag_ids": [],
  "tag_labels": [],
  "search_terms": [
    "00533",
    "2 bodies monoprint",
    "2",
    "bodies",
    "monoprint",
    "2025",
    "2-bodies",
    "2 bodies",
    "drawing"
  ],
  "search_text": "00533 2 bodies monoprint 2 bodies monoprint 2025 2-bodies 2 bodies drawing"
}
```

Representative series record:

```json
{
  "kind": "series",
  "id": "2-bodies",
  "title": "2 bodies",
  "href": "/series/2-bodies/",
  "year": 2025,
  "display_meta": "2025",
  "series_ids": [],
  "series_titles": [],
  "series_type": "primary",
  "tag_ids": [],
  "tag_labels": [],
  "search_terms": [
    "2-bodies",
    "2",
    "bodies",
    "2 bodies",
    "2025",
    "primary"
  ],
  "search_text": "2-bodies 2 bodies 2 bodies 2025 primary"
}
```

Representative moment record:

```json
{
  "kind": "moment",
  "id": "4-stories",
  "title": "4 stories",
  "href": "/moments/4-stories/",
  "date": "2020-01-01",
  "display_meta": "c. 2020?",
  "series_ids": [],
  "series_titles": [],
  "tag_ids": [],
  "tag_labels": [],
  "search_terms": [
    "4-stories",
    "4",
    "stories",
    "4 stories",
    "c. 2020?",
    "c",
    "2020",
    "2020-01-01",
    "01"
  ],
  "search_text": "4-stories 4 stories 4 stories c. 2020? c 2020 2020-01-01 01"
}
```

## Schema design notes

The current schema is shaped this way for pragmatic reasons:

- ids, titles, and hrefs are present so the browser can render useful results without secondary fetches
- compact structured metadata is included so search can grow beyond exact title lookup
- `search_terms` and `search_text` are precomputed so the browser does not need to reconstruct token bundles from heterogeneous fields on every search
- the index stays compact by excluding full content bodies and other large page data

## Known limitations or open schema questions

Current schema-level follow-up questions:

- whether `search_text` should continue to duplicate `search_terms` so directly, or evolve into a more selective broad-match field
- whether future filtering requires additional explicit structured fields beyond the current optional set
- whether tag-derived fields should eventually be expanded beyond `tag_ids` and `tag_labels`
- how future prose shards should share or diverge from the base record model

## Out of scope for this document

This document does not define:

- query normalization rules
- scoring and ranking
- result rendering behaviour
- keyboard or interaction behaviour
- detailed build steps
