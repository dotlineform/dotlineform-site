---
doc_id: search-config-implementation-note
title: Search Config Implementation Note
last_updated: 2026-03-29
parent_id: search
sort_order: 101
---

# Search Config Implementation Note

## Purpose

This document turns the config-architecture direction into a concrete implementation sequence.

It answers:

- what the first config extraction should be
- what code and files should change
- what should stay in code for now
- what later config phases should look like

This is an implementation note, not the long-term policy source itself.

Related docs:

- [Search Config Architecture](/docs/?doc=search-config-architecture)
- [Search Field Registry](/docs/?doc=search-field-registry)
- [Search Ranking Model](/docs/?doc=search-ranking-model)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)

## Current implementation boundary

Current search configuration is split like this:

- `assets/studio/data/studio_config.json`
  - route path
  - search data path
  - search UI text
- `assets/studio/js/studio-search.js`
  - debounce timing
  - results batch size
  - filter list and order
  - live-search behaviour
  - Enter-to-search behaviour
  - ranking logic
- `scripts/generate_work_pages.py`
  - build-time search entry generation and normalization

This means the obvious runtime search-policy knobs are still embedded in JavaScript.

## First implementation step

The first step should externalize runtime search UI policy only.

That means:

- move stable runtime knobs into a dedicated JSON file
- keep ranking bands in code
- keep field participation rules in code/docs
- keep build-time generator policy out of this first phase

This is the right first cut because it removes the clearest hardcoded search policy without forcing a premature config model for ranking or indexing.

## Phase 1 scope

### In scope

- live-search enabled/disabled
- Enter runs search enabled/disabled
- minimum query length
- debounce timing
- initial results batch size
- load-more batch increment size
- enabled kind filters
- filter display order

### Out of scope

- ranking score bands
- field activation and match-mode policy
- normalization algorithm parameters
- build-time inclusion policy
- shard definitions
- prose search policy

## Proposed file shape

Create:

- `assets/studio/data/search_policy.json`

Recommended initial payload:

```json
{
  "search_policy_version": "search_policy_v1",
  "updated_at_utc": "2026-03-29T00:00:00Z",
  "runtime": {
    "live_search": true,
    "enter_runs_search": true,
    "min_query_length": 1,
    "debounce_ms": 140,
    "results": {
      "initial_batch_size": 50,
      "batch_increment_size": 50
    }
  },
  "filters": {
    "kind_order": ["all", "work", "series", "moment"],
    "enabled": {
      "all": true,
      "work": true,
      "series": true,
      "moment": true
    }
  }
}
```

## How the runtime should find it

Keep `studio_config.json` narrow, but let it continue to own Studio data paths.

Add one path in:

- `assets/studio/data/studio_config.json`

Recommended addition:

```json
{
  "paths": {
    "data": {
      "studio": {
        "search_policy": "/assets/studio/data/search_policy.json"
      }
    }
  }
}
```

This keeps the generic Studio shell config small while still giving the search page a normal config-based lookup path.

## Proposed code ownership

Do not grow `assets/studio/js/studio-config.js` into the full owner of search policy.

Instead, add one search-specific loader module:

- `assets/studio/js/studio-search-policy.js`

Recommended responsibilities:

- define `DEFAULT_SEARCH_POLICY`
- fetch and merge `search_policy.json`
- sanitize runtime values
- expose small helpers for search runtime consumption

Recommended non-responsibilities:

- ranking logic
- normalization logic
- DOM rendering
- search result scoring

## Recommended runtime module shape

Suggested module outline:

```js
const DEFAULT_SEARCH_POLICY = {
  search_policy_version: "search_policy_v1",
  updated_at_utc: "",
  runtime: {
    live_search: true,
    enter_runs_search: true,
    min_query_length: 1,
    debounce_ms: 140,
    results: {
      initial_batch_size: 50,
      batch_increment_size: 50
    }
  },
  filters: {
    kind_order: ["all", "work", "series", "moment"],
    enabled: {
      all: true,
      work: true,
      series: true,
      moment: true
    }
  }
};

export async function loadSearchPolicy(studioConfig) { /* ... */ }
export function getSearchRuntimePolicy(policy) { /* ... */ }
export function getSearchFilterKinds(policy) { /* ... */ }
```

The helpers should return already-sanitized values so `studio-search.js` can stay simple.

## Recommended `studio-search.js` changes

Phase 1 should be a mechanical refactor of the current runtime.

### Replace hardcoded constants

Remove direct ownership of:

- `RESULTS_BATCH_SIZE`
- `SEARCH_DEBOUNCE_MS`

### Load policy after Studio config

Current flow:

1. load Studio config
2. load search index
3. initialize page state

Recommended flow:

1. load Studio config
2. load search policy
3. load search index
4. initialize page state

### Derive page state from policy

State should include:

- `policy`
- `visibleCount` from `runtime.results.initial_batch_size`
- active filter list from `filters.kind_order` and `filters.enabled`

### Gate input behavior from policy

Recommended behavior mapping:

- if `runtime.live_search` is `true`, input events run debounced search
- if `runtime.live_search` is `false`, input events do not trigger search
- if `runtime.enter_runs_search` is `true`, Enter runs immediate search
- if `runtime.enter_runs_search` is `false`, Enter does nothing special

### Enforce minimum query length

Recommended v1 behavior:

- if normalized query length is below `min_query_length`, show the standard prompt state and do not search

That keeps the runtime rule simple and visible.

### Use policy-driven batching

Recommended behavior:

- initial render count from `initial_batch_size`
- each `more` click increments by `batch_increment_size`

## Validation for phase 1

Codex-run checks:

- `node --check assets/studio/js/studio-search.js`
- `node --check assets/studio/js/studio-search-policy.js`
- `./scripts/build_docs_data.rb --write` if docs change
- `bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Manual checks:

- `/studio/search/` still loads correctly
- typing still gives live results with the configured debounce
- Enter still triggers immediate search when enabled
- `more` still reveals the next result batch
- filter buttons still render in the configured order

## Phase 2: Ranking band config

Once phase 1 is stable, the next candidate for extraction is ranking order.

Recommended addition to `search_policy.json`:

```json
{
  "ranking": {
    "tie_break_order": ["title", "id"],
    "bands": [
      { "score": 900, "field": "id", "mode": "exact" },
      { "score": 860, "field": "title", "mode": "exact" },
      { "score": 780, "field": "search_terms", "mode": "exact" }
    ]
  }
}
```

Important constraint:

- config should define precedence
- code should still execute the actual comparisons

Do not attempt to encode the full matching engine as declarative JSON in the first ranking phase.

## Phase 3: Field participation config

After ranking extraction, add a machine-readable field policy layer.

Recommended shape:

```json
{
  "fields": {
    "title": {
      "active": true,
      "roles": ["display", "ranking"],
      "match_modes": ["exact", "prefix", "token_prefix"]
    },
    "medium_type": {
      "active": true,
      "roles": ["display", "ranking", "future_filter"],
      "match_modes": ["contains"]
    },
    "tag_labels": {
      "active": false,
      "roles": ["future_ranking", "future_filter"],
      "match_modes": ["exact", "contains"]
    }
  }
}
```

This should align directly with [Search Field Registry](/docs/?doc=search-field-registry), but only once the runtime is ready to consume it safely.

## Phase 4: Shared runtime/build policy boundary

Only after ranking and field policy are stable should build-time search policy start reading the same config family.

At that point, split policy by responsibility if needed:

- runtime policy
- shared search policy
- build-only policy

Possible later split:

- `assets/studio/data/search_policy.json`
  - runtime-facing and shared policy
- `_data/search_build_policy.json`
  or another generator-owned location
  - build-only controls such as payload budgets or shard generation rules

Do not force Python and browser consumers into one file if that makes ownership less clear.

## Phase 5: Future expansion areas

Later phases may add:

- tag-aware ranking enablement
- filter definitions for `medium_type`, `series_type`, and tags
- shard definitions for prose or heavy enrichment fields
- benchmark/report config for ranking validation

These should come only when the relevant feature is real enough to justify a machine-readable surface.

## Main benefits of this sequence

- phase 1 removes the clearest hardcoded runtime policy with low risk
- later phases stay additive rather than forcing one large config refactor
- docs, config, and code can evolve in a controlled order
- search can keep its architecture boundary clear as prose and tags become more important

## Main risks of this sequence

- adding config too early can create duplication between docs, JSON, and code
- defaults and JSON can drift if sanitization and fallback rules are weak
- trying to express too much algorithmic behavior in JSON will make the system harder to understand, not easier

## Recommendation

Implement phase 1 now.

Do not implement phases 2 to 5 until phase 1 is in use and stable enough to show which policy surfaces actually need to be tuned as data.
