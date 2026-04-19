---
doc_id: studio-search-v1
title: Studio Search V1
last_updated: 2026-03-29
parent_id: _archive
sort_order: 10
published: false
---

# Studio Search V1

Status:

- locked v1 planning spec
- Studio-first implementation
- no external plugins or hosted search services

## Summary

Search should start as a dedicated Studio page and own one build-time-generated search artifact:

- route: `/studio/search/`
- payload: `assets/data/search_index.json`

V1 should search across:

- works
- series
- moments

The search runtime should stay intentionally simple:

- one lean base payload
- one in-house client-side ranking pass
- no runtime fetches of per-work JSON before first results

The important scalability constraint is not record count alone. It is the future growth of prose and other metadata fields.

Because of that, the base search contract must be designed so that:

- future fields can be added without breaking the page contract
- large prose search can be added later without bloating the default payload
- search-specific data can evolve independently from `works_index.json`, `series_index.json`, and `moments_index.json`

## Goals

- keep client-side search responsive on first interaction
- avoid external search infrastructure
- keep the runtime understandable and easy to tune
- support exact id/title matches well
- support gradual expansion into metadata fields such as `medium_type`
- create a clean path to later full-text or prose-aware search

## Non-Goals For V1

- no hosted or server-backed search
- no dependency on third-party search plugins
- no prose-heavy full-text index in the default payload
- no top-nav rollout on the main site yet
- no analytics, typo-learning, or personalization

## Primary Surface

V1 should ship first as a Studio page.

Reason:

- it allows the search contract and ranking rules to mature before they affect the public site shell
- it avoids early complexity in `_layouts/default.html`
- it gives a safe place to test additional filters and field expansion

Proposed initial page responsibilities:

- text input for query
- type filter: `all`, `works`, `series`, `moments`
- result count
- result list with lightweight metadata
- empty state and load/error state

The Studio page should load `search_index.json` on page load or on first interaction. Either is acceptable for v1 because the route is dedicated to search.

Recommended interaction model:

- load the base artifact once
- keep it in memory for the page session
- run search after a short debounce while typing
- allow `Enter` to trigger an immediate search if needed

Typing should feel responsive, but search should not perform a network fetch on each keypress.

## Main-Site Rollout Path

When the Studio search behavior is stable, the same runtime can move to the main site in two stages:

1. Add a search trigger or input to the top nav.
2. Reuse the same `search_index.json` contract and search module on a public site page or overlay.

The main-site rollout should not require a new data model. It should be a surface change, not a search-contract rewrite.

## Data Ownership

The repo already produces lightweight site indexes for works, series, and moments.

Those indexes remain useful for their current pages, but v1 search should own its own artifact:

- `assets/data/search_index.json`

Reason:

- search data has different optimization needs from browse/index data
- search will grow new fields faster than the other indexes
- search ranking benefits from pre-normalized fields that are not useful elsewhere
- future prose search should not force unrelated pages to download larger generic indexes

The search artifact should be generated at build time from canonical source data in the same pipeline that already builds site indexes.

Search generation should remain a self-contained pipeline concern:

- it reads canonical source data and existing generated metadata
- it writes a search-specific artifact
- it does not change canonical ownership of `works.xlsx`
- it does not make search the source of truth for non-search pages

## Search Artifact Contract

Top-level shape:

```json
{
  "header": {
    "schema": "search_index_v1",
    "version": "<content-version>",
    "generated_at_utc": "<timestamp>",
    "count": 0
  },
  "entries": []
}
```

`entries` should be a flat array, not an object keyed by id.

Reason:

- the runtime will iterate and score entries rather than perform id lookups only
- arrays are simpler for stable ordering and lightweight client-side scans
- the payload can later be split into shards without changing the per-entry shape

Each entry should use one common shape with optional fields:

```json
{
  "kind": "work",
  "id": "00008",
  "title": "nerve",
  "href": "/work/00008/",
  "year": 1995,
  "date": null,
  "display_meta": "July 1990 - January 1995",
  "series_ids": ["nerve", "collected-1989-1998"],
  "series_titles": ["nerve", "collected 1989-1998"],
  "medium_type": "writing",
  "search_text": "00008 nerve nerve collected 1989 1998 writing",
  "search_terms": ["00008", "nerve", "collected-1989-1998", "writing"]
}
```

Field rules:

- `kind`
  - one of `work`, `series`, `moment`
- `id`
  - canonical item id such as `work_id`, `series_id`, or `moment_id`
- `title`
  - primary display title
- `href`
  - canonical public route target
- `year`
  - used when a record is year-based
- `date`
  - used when a record is date-based
- `display_meta`
  - compact display string for the result row
- `series_ids`
  - optional related series ids
- `series_titles`
  - optional related series titles
- `medium_type`
  - optional in v1 data model even if not populated for every record yet
- `search_text`
  - one normalized string used for broad contains matching
- `search_terms`
  - normalized discrete tokens used for exact and prefix checks

`search_text` and `search_terms` should be produced at build time, not normalized in the browser.

## V1 Indexed Fields

V1 base search should index only compact, high-value fields:

- work id
- work title
- series id
- series title
- moment id
- moment title
- year or date values as text
- associated series titles for works

V1 should also reserve space for structured metadata fields that are likely to matter soon:

- `medium_type`
- `storage`
- `series_type`
- assigned tags

These do not all need to be visible in the UI on day one, but the search contract should treat them as first-class optional fields rather than ad hoc later additions.

Tag data is a specifically important future signal.

Current constraint:

- tag coverage is still sparse

Future direction:

- use `tag_registry.json` and `tag_assignments.json` as the source for normalized tag search fields
- treat tags as both a ranking signal and a filter surface when coverage is strong enough
- keep tag-derived search fields optional until the underlying tagging data is reliable enough to improve results consistently

## Ranking Rules

V1 ranking should stay deterministic and easy to reason about.

Recommended priority order:

1. exact `id` match
2. exact `title` match
3. exact `search_terms` match
4. title prefix match
5. id prefix match
6. title token match
7. associated metadata match such as series title or medium type
8. broad `search_text` contains match

Future ranking expansion:

- once tag coverage is strong enough, assigned-tag matches should rank above broad generic `search_text` contains matches
- exact or prefix tag matches should be treated as stronger than weak metadata-only contains matches
- tag-aware ranking should only be enabled when sparse tagging no longer creates uneven result quality

Tie-break rules:

- prefer title matches over metadata-only matches
- prefer shorter exact titles over longer partial titles when the same score tier applies
- then apply stable item ordering by `kind`, `title`, and `id`

This should be implemented with explicit numeric score tiers, not fuzzy black-box heuristics.

## Query Semantics

Normalization rules:

- lowercase
- trim outer whitespace
- collapse repeated internal whitespace
- strip punctuation for token comparison where practical
- preserve the original display values separately for rendering

V1 query behavior:

- empty query: show no results by default
- one token: run exact, prefix, then contains scoring
- multiple tokens: require that all tokens appear somewhere in the entry before broad contains ranking is considered a match

This keeps the result set focused without needing a more complex index structure in v1.

## Payload and Runtime Strategy

The base payload must remain lean enough that typing stays responsive after the initial fetch.

Rules:

- do not include `content_html`
- do not include full prose in `search_index.json`
- do not fetch per-work JSON files before first search results
- do not make each keypress trigger additional network requests

The runtime may:

- load the artifact once
- keep it in memory for the page session
- score in plain JavaScript
- render only a limited first page of results, for example the top 50

This is sufficient for the current catalogue size and keeps the system simple.

## Future Full-Text Scale Path

Future prose growth should be handled with a second stage, not by inflating the base payload.

Recommended expansion path:

1. Keep `search_index.json` as the fast base index for ids, titles, dates, and compact metadata.
2. Add one or more optional prose-oriented artifacts later, loaded only when needed.

Acceptable future shapes:

- `assets/data/search_index_prose.json`
- `assets/data/search_index.works-prose.json`
- multiple smaller shards by content type

Principle:

- a shard is a separate search payload for a specific slice of search data
- the browser loads only the shards needed for the current search mode
- base search remains fast because large prose payloads stay out of the default first load

When prose search arrives, the search flow should remain:

1. search base index immediately
2. show fast results
3. optionally load prose shards for deeper matching or result enrichment

This avoids making prose growth a first-load tax for every search interaction.

## Field Expansion Rules

Every new search field should be classified as one or more of:

- display field
- filter field
- ranking field
- lazy enrichment field

Examples:

- `medium_type`
  - filter field
  - ranking field
  - optional display field
- assigned tags
  - filter field
  - ranking field
  - optional display field
- `storage`
  - filter field
  - optional display field
- prose excerpt
  - lazy enrichment field
  - optional ranking field

This classification prevents the base search artifact from becoming an undifferentiated dump of site metadata.

The classification rules should be enforced in generator code and verification checks, not only described in docs.

Recommended enforcement:

- keep one explicit field registry in code
- mark each search field with its allowed roles
- reject `lazy_enrichment` fields in the base artifact
- keep tag-derived fields behind an explicit enable/disable decision until coverage is sufficient
- report payload size and included fields in verification output

## Generator Guidance

The search artifact should be generated in the existing content pipeline, alongside the current site indexes.

Generator expectations:

- deterministic ordering
- content-version checksum in `header.version`
- stable normalized token generation
- one common entry shape across works, series, and moments

The generator should own search normalization rules so the runtime stays small and predictable.

## Ranking Assessment

Ranking effectiveness should be assessed with a small curated benchmark, not only by ad hoc manual impressions.

Recommended approach:

- maintain a fixed set of representative queries
- define expected top results for each query
- track top-1 and top-5 hit rates
- include exact-id, exact-title, prefix, multiple-token, metadata, future tag, and ambiguous queries
- expose optional Studio debug output showing score tier and matched fields

This gives a concrete way to tune ranking rules without introducing external analytics or black-box heuristics.

## Benefits

- simple v1 implementation with clear ownership
- fast client-side behavior without external dependencies
- clean separation between browse indexes and search indexes
- straightforward path to add fields such as `medium_type`
- future prose search can scale without bloating the base payload

## Risks

- search quality depends on deliberate ranking choices rather than a library default
- future field growth can still bloat the base payload if classification rules are ignored
- generating one more artifact adds pipeline scope
- later prose search will require a second artifact and a slightly more complex runtime
