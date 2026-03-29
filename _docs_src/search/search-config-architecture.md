---
doc_id: search-config-architecture
title: Search Config Architecture
last_updated: 2026-03-29
parent_id: search
sort_order: 100
---

# Search Config Architecture

## Purpose

This document defines which parts of the search system should become machine-readable configuration and which parts should remain implementation code.

It is an architecture and decision document. It exists to make future search-policy extraction deliberate rather than ad hoc.

This document does not define the detailed rules themselves. Those belong in:

- [Search Field Registry](/docs/?doc=search-field-registry)
- [Search Ranking Model](/docs/?doc=search-ranking-model)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)
- [Search Normalisation Rules](/docs/?doc=search-normalisation-rules)

## Current state

Current v1 search has three different policy surfaces:

- **documentation**
  - field policy, ranking policy, normalization policy, and UI behaviour are now documented explicitly
- **runtime config already in use**
  - `assets/studio/data/studio_config.json`
  - current search use is limited to paths/routes and UI text strings
- **implementation code**
  - `assets/studio/js/studio-search.js`
  - `scripts/generate_work_pages.py`

Current practical split:

- configurable now:
  - search route
  - search data path
  - search UI copy
- not yet configurable:
  - field participation rules
  - ranking bands
  - runtime behaviour values such as debounce and batch size
  - build-time field inclusion policy

This means search is documented well enough to review, but not yet externalized enough to adjust core policy without touching code.

## Why review this now

This is worth addressing early because search is already past the “one experimental file” stage.

Current facts:

- search has its own artifact
- search has its own Studio surface
- search now has a dedicated document set
- future expansion will add more fields, more ranking pressure, and likely prose shards

If config boundaries are not set early, the system is likely to drift into:

- duplicated rules across docs and code
- accidental policy hidden in JavaScript or Python constants
- harder future changes when field weighting and filters become more important

The goal is not to externalize everything immediately. The goal is to decide what should become config before the search surface grows further.

## Principle

Search should be divided into three layers:

- **Docs**
  - human review surface
  - explains what the rules are and why
- **Config**
  - machine-readable policy surface
  - only for stable knobs and structured policy decisions
- **Code**
  - mechanism
  - normalization functions, candidate evaluation, rendering, fetch logic, and other algorithmic behaviour

Policy should move into config only when both of these are true:

1. the rule is likely to be discussed or tuned repeatedly
2. representing it as data is clearer than burying it in implementation code

## Recommended architecture

### 1. Keep `studio_config.json` narrow

`assets/studio/data/studio_config.json` should remain the Studio shell config.

It is already a good fit for:

- routes
- data paths
- UI copy
- page-level Studio defaults

It should not become the container for the full search policy model.

Reason:

- it already serves multiple Studio features
- a large search policy tree would make it harder to review and maintain
- search will likely need policy shared across generator and runtime, not just Studio page text

### 2. Introduce a dedicated search policy config

Recommended new file:

- `assets/studio/data/search_policy.json`

Reason for this location:

- it is already in a public JSON area used by the Studio runtime
- it can be read by browser code directly
- it can also be read by Python at build time
- it keeps search policy separate from generic Studio shell config

This file should become the machine-readable search-policy surface.

### 3. Keep docs as the normative review surface

The config file should not replace the docs.

Recommended relationship:

- docs explain the intended behaviour
- config expresses the subset of that behaviour that code consumes directly
- code implements the mechanisms that apply the config

This avoids the trap of trying to make JSON itself the only human-readable explanation.

## What should be configurable

The first externalized search-policy surface should cover only stable, reviewable rules.

### A. Runtime UI behaviour

Good candidates for config:

- debounce interval
- initial results batch size
- batch increment size
- available kind filters and their display order
- whether Enter forces immediate search
- whether live search on input is enabled
- minimum query length, if introduced

These are stable product decisions and are straightforward to express as data.

### B. Field participation policy

Good candidates for config:

- whether a field is active in ranking
- whether a field is display-only
- whether a field is filterable now or reserved for later
- field importance class
- allowed match modes by field

This should be the machine-readable counterpart to [Search Field Registry](/docs/?doc=search-field-registry), but only once the implementation is ready to consume it.

### C. Ranking band policy

Good candidates for config:

- ordered precedence bands
- which field and match mode each band represents
- tie-break order

Example of the kind of rule that belongs here:

- exact `id` match outranks exact `title` match
- `series_titles` contains outranks `search_text` fallback

The matching engine should still perform the comparisons; config should define the order of precedence.

### D. Future filter definitions

Not required for current v1, but worth reserving conceptually:

- filter ids
- supported fields
- display labels
- value source mode such as static or derived

## What should stay in code

The following should remain implementation code for now.

### Matching engine

Examples:

- all-query-tokens-present gate
- exact/prefix/contains comparison logic
- candidate iteration and sorting execution

### Normalization functions

Examples:

- `normalize_search_text(...)`
- browser-side `normalize(...)`
- token splitting and deduplication implementation

These rules may be documented and partly parameterized later, but the underlying algorithm should remain code.

### Index loading and caching

Examples:

- fetch behaviour
- in-memory storage
- fallback to default Studio config values

### DOM rendering

Examples:

- result row markup
- focus handling
- button event wiring

### Performance optimizations

Examples:

- precomputed normalized values
- future shard loading strategy
- future inverted index structures

## Build-time vs runtime config

Search policy has two different consumers and they should not be conflated.

### Build-time policy

Used by:

- `scripts/generate_work_pages.py`

Good build-time config candidates:

- field inclusion in `search_terms`
- whether specific structured fields are emitted
- future shard layout
- payload budget targets

### Runtime policy

Used by:

- `assets/studio/js/studio-search.js`

Good runtime config candidates:

- ranking precedence bands
- filter options
- debounce and batching behaviour
- result-display toggles

### Shared policy

Some policy will eventually need to be shared across both build time and runtime.

Best examples:

- field registry
- field activation status
- match-mode allowance by field

That is the strongest argument for introducing a dedicated search policy file sooner rather than later.

## Proposed initial config shape

Illustrative target shape only:

```json
{
  "search_policy_version": "search_policy_v1",
  "ui": {
    "debounce_ms": 140,
    "results_batch_size": 50,
    "enable_live_search": true,
    "enable_enter_submit": true,
    "kind_filters": ["all", "work", "series", "moment"]
  },
  "fields": {
    "id": {
      "active": true,
      "importance": "high",
      "match_modes": ["exact", "prefix"]
    },
    "title": {
      "active": true,
      "importance": "high",
      "match_modes": ["exact", "prefix", "token"]
    },
    "tag_labels": {
      "active": false,
      "reserved_for": ["future_ranking", "future_filtering"]
    }
  },
  "ranking": {
    "bands": [
      { "score": 900, "field": "id", "match": "exact" },
      { "score": 860, "field": "title", "match": "exact" }
    ],
    "tie_break": ["title", "id"]
  }
}
```

This is intentionally modest. It is not trying to externalize every implementation detail.

## Recommended implementation order

Recommended order of adoption:

### Step 1. Externalize runtime UI behaviour

Move these first:

- debounce
- results batch size
- filter list/order

Reason:

- low risk
- easy to verify
- no schema or generator coupling

### Step 2. Externalize ranking band definitions

Move next:

- score bands
- tie-break order

Reason:

- ranking is already explicitly documented
- this creates a strong review surface without forcing a redesign of the matching engine

### Step 3. Externalize field activation registry

Move after ranking config is stable:

- which fields are active in ranking
- which are display-only
- which are future filter candidates

Reason:

- this is where shared build-time/runtime policy starts to matter
- it should be implemented once the team is comfortable that the field registry is stable enough to become machine-readable

### Step 4. Consider build-time policy extraction

Later, if needed:

- field inclusion in derived token generation
- future shard policy
- payload budget thresholds

This is a later step because it touches generator behaviour and has more structural impact.

## Why not externalize everything now

Immediate full externalization would likely be the wrong move.

Risks:

- duplicated logic between config and implementation
- overly abstract JSON that is harder to review than code
- unstable policy surface before the first few tuning rounds are complete

The right move is a staged extraction of the most stable and high-value policy knobs first.

## Change rules

Apply these update rules:

- if a new stable UI behaviour knob is introduced, consider whether it belongs in search policy config
- if ranking precedence changes, update both the ranking doc and the machine-readable ranking config once that layer exists
- if a field becomes active or inactive in search, update the field registry doc and the field policy config once that layer exists
- if normalization logic changes but remains algorithmic, update docs and code, not necessarily config
- if build-time field inclusion changes materially, update the build-pipeline doc and build-time config once that layer exists

## Current implementation summary

Current status:

- there is no dedicated search policy config file yet
- `studio_config.json` currently carries only routes, data paths, and UI text for search
- ranking, field participation, and runtime behaviour still live in code
- the docs set now provides the human review surface needed to support the next extraction step

This means the architecture work is timely: search is documented enough to externalize stable policy, but not yet so large that the extraction becomes messy.

## Recommended decision

Recommended next structural move:

- create a dedicated `search_policy.json`
- keep `studio_config.json` limited to Studio shell concerns
- externalize runtime UI behaviour first
- then externalize ranking bands
- treat field activation as the next shared build/runtime policy layer

That is the cleanest path toward a configurable search system without over-engineering v1.
