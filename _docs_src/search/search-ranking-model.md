---
doc_id: search-ranking-model
title: Search Ranking Model
last_updated: 2026-03-31
parent_id: search
sort_order: 40
---

# Search Ranking Model

## Purpose

This document defines how matching search records are prioritised and ordered in the current v1 search implementation.

Its purpose is to make the relevance model explicit and reviewable without turning this document into a code walk-through.

This is a ranking-policy document. It is not the schema, normalization, or UI document.

## Scope

This document applies to the ranking stage of the current client-side search runtime.

It covers:

- the candidate gate before scoring
- the current match-precedence bands
- tie-breaking
- how derived fields are treated
- the main current limitations of the v1 model

## Relationship to other documents

- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema) defines the available fields
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry) defines each field’s search role
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules) defines how values are normalized before matching
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour) defines how ranked results are presented
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist) defines how ranking behaviour should be checked

## Ranking principles

The current ranking model follows these principles.

### Predictable

The runtime uses explicit numeric score tiers and deterministic ordering.

### Known-item friendly

Exact id and exact title matches are given the highest precedence.

### Structured-first

Direct matches in high-value fields outrank broad fallback matches.

### Recall without dominance

`search_text` broad-match recall exists, but it is intentionally the weakest scoring band.

### Lightweight

The model stays simple enough to run in plain browser JavaScript over the in-memory index.

## Ranking stages

The current runtime can be described in four stages.

### 1. Query normalization

The input query is normalized into a lowercased space-normalized form and split into tokens.

This document does not define the normalization rules in detail; those belong in [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules).

### 2. Candidate gate

Before an entry can be scored at all, every query token must match somewhere in the record.

Current gate rule:

- for every query token
  - either some `search_terms` token must equal it or start with it
  - or `search_text` must contain it

If any token fails that test, the record is discarded before ranking.

This is important because v1 ranking is not evaluating all records and then giving weak scores to almost-matches. It first enforces an all-tokens-present rule, then applies score tiers.

### 3. Score-band assignment

Each surviving candidate is assigned the first matching score tier from a descending precedence list.

The tiers are mutually exclusive in practice because the runtime returns on the first satisfied condition.

### 4. Tie-breaking

When two records have the same numeric score, the runtime sorts by:

1. title, ascending, locale-aware, case-insensitive, numeric-aware
2. id, ascending, locale-aware, case-insensitive, numeric-aware

There is no content-type preference in the current tie-breaker.

## Ranking dimensions

The current model ranks by a combination of:

### Field importance

The model distinguishes between:

- exact identity fields
- exact or prefix title-style matches
- derived token support
- structured metadata matches
- fallback broad-match text

### Match type strength

Stronger match types outrank weaker ones:

- exact
- exact derived token
- prefix
- title-token match
- metadata contains
- broad fallback contains

### Candidate completeness

The all-tokens-present gate means a result must cover the whole query in some combination of fields before ranking strength matters.

### Generic versus specific terms

The current implementation does not explicitly model token rarity, genericness, or inverse frequency. It treats all normalized tokens equally within the same rule band.

## Ranking table

Current score bands in descending order:

| Score band | Match condition | Relative strength | Notes |
|---|---|---|---|
| `900` | exact `id` match | strongest | highest-confidence known-item lookup |
| `860` | exact `title` match | very strong | exact human-readable known-item lookup |
| `780` | exact `search_terms` match | strong | exact derived token match |
| `720` | `title` prefix match | strong | partial known-item lookup |
| `690` | `id` prefix match | strong | partial id lookup |
| `620` | all query tokens match `title` tokens exactly or by prefix | medium-strong | title-token-oriented retrieval |
| `480` | any `series_titles` value contains the query | medium | contextual series discovery |
| `460` | `medium_type` contains the query | medium | structured metadata discovery |
| `440` | `storage` contains the query | low-medium | narrower metadata lookup |
| `420` | `series_type` contains the query | low-medium | narrower metadata lookup |
| `320` | `search_text` contains the query | weakest | fallback broad recall only |

The model is numeric, but the exact numbers are only meaningful as stable precedence bands, not as a continuous relevance scale.

## Field-level ranking notes

### `id`

Ranking role:
One of the two strongest fields in the system.

Strong matches:

- exact id
- id prefix

Notes:
Exact id outranks exact title in the current implementation.

### `title`

Ranking role:
Primary human-readable retrieval field.

Strong matches:

- exact title
- title prefix
- title-token coverage

Notes:
Title matching is highly favored, but exact title is still below exact id in the current v1 order.

### `search_terms`

Ranking role:
Primary derived support field.

Strong matches:

- exact term match
- token gate support through equals-or-prefix checks

Notes:
`search_terms` is not just fallback. It is central to candidate retrieval and provides an explicit high-tier exact match band.

### `series_titles`

Ranking role:
Main structured contextual discovery field.

Strong matches:

- query substring within any related series title

Notes:
This is currently the highest-ranking metadata field.

### `medium_type`

Ranking role:
Useful structured discovery field for works.

Strong matches:

- query substring within `medium_type`

Notes:
Weaker than title and series-title matches, stronger than broad fallback.

### `storage`

Ranking role:
Narrow structured metadata field.

Strong matches:

- query substring within `storage`

Notes:
Active in ranking, but not currently surfaced in result display.

### `series_type`

Ranking role:
Narrow structured metadata field for series.

Strong matches:

- query substring within `series_type`

Notes:
Weaker than `series_titles` and `medium_type`.

### `search_text`

Ranking role:
Low-priority fallback field.

Strong matches:

- broad substring contains

Notes:
`search_text` should help recall, but it should not outrank structured-field matches.

## Tie-breaking policy

Current tie-breaking is simple and explicit.

If two entries have the same score:

1. compare `title`
2. if titles are equal, compare `id`

Current tie-breaking does not use:

- content type priority
- recency
- year
- metadata richness
- source order

This means ambiguous results within the same score band are effectively alphabetical by title, then id.

## Duplicate-term and repeated-match policy

Current v1 behaviour does not count repeated occurrences as stronger evidence.

Important current properties:

- `build_search_tokens()` deduplicates tokens at generation time
- the runtime checks presence and precedence, not occurrence counts
- repeated appearance of a term in `search_text` does not create additive scoring
- a single strong exact or prefix field match still outranks repeated broad fallback presence

This keeps v1 reasonably stable even when the derived fields include overlapping terms.

## Derived field ranking policy

Current derived fields used in ranking:

- `search_terms`
- `search_text`

Current policy:

- `search_terms` is a primary derived retrieval field
- `search_text` is fallback only
- both are weaker, in general, than exact identity or title-style matches
- derived fields intentionally trade field provenance for a simpler runtime

Current consequence:

- the runtime can be simple and fast
- but it cannot always explain exactly which source field caused a lower-tier derived match

That loss of provenance is an accepted constraint of the current runtime.

## Content-type priority

The current search index mixes works, series, and moments in a single ranked result set.

Current policy:

- content type does not have an intrinsic score bonus or penalty
- a work, series, or moment can outrank another kind purely on match strength
- the only content-type-specific control currently exposed is the explicit kind filter in the UI

This keeps the raw ranking model content-type-neutral.

## Current implementation summary

Current ranking behaviour in practice:

- ranking is field-aware and uses explicit numeric precedence bands
- candidate retrieval requires every query token to appear somewhere in the record
- exact id and exact title matches are strongly favored
- metadata fields contribute meaningfully, but below title-style matching
- `search_text` is a broad fallback field and the weakest active score band
- tie-breaking is explicit and alphabetical, not source-order-based
- duplicate term frequency does not currently amplify ranking

## Out of scope for this document

This document does not define:

- full index schema
- detailed normalization rules
- result rendering markup
- build-pipeline steps
- UI event timing
- validation procedure details
