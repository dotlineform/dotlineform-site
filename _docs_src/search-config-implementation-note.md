---
doc_id: search-config-implementation-note
title: Search Config Implementation Note
last_updated: 2026-03-30
parent_id: ""
sort_order: 101
published: false
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

- [Search Config Architecture](/docs/?scope=studio&doc=search-config-architecture)
- [Search Pipeline Target Architecture](/docs/?scope=studio&doc=search-pipeline-target-architecture)
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

## Current implementation boundary

Current search configuration is split like this:

- `assets/studio/data/studio_config.json`
  - route paths
  - scope-owned search index paths
  - search policy path
- `assets/js/search/search-page.js`
  - policy consumption
  - ranking logic
- `assets/js/search/search-policy.js`
  - default runtime shell policy
  - policy loading and sanitization
  - scope-policy lookup
- `scripts/generate_work_pages.py`
  - build-time catalogue search entry generation and normalization

This means the search route contract is already scope-led and the public runtime shell now reads scope-aware UI behavior from a dedicated policy artifact.

## Phase 1 status

Phase 1 is now implemented.

It does this:

- moves stable runtime shell knobs into a dedicated JSON file
- moves scope-owned UI copy and enablement into that same file
- keeps ranking bands in code
- keeps field participation rules in code/docs
- keeps build-time generator policy out of this phase

This was the right first cut because it makes the `/search/` shell properly scope-native before `scope=studio` is implemented, without forcing a premature config model for ranking or indexing.

## Phase 1 scope

### In scope

- live-search enabled or disabled
- Enter-runs-search enabled or disabled
- minimum query length
- debounce timing
- initial results batch size
- load-more batch increment size
- scope enablement
- scope label
- scope-owned back-link label and route-key mapping
- scope-owned input aria label and placeholder
- missing-scope and unsupported-scope messages

### Out of scope

- ranking score bands
- field activation and match-mode policy
- normalization algorithm parameters
- build-time inclusion policy
- shard definitions
- prose search policy
- result-kind filters, because the public UI no longer exposes them

## Proposed file shape

Create:

- `assets/data/search/policy.json`

Implemented payload shape:

```json
{
  "search_policy_version": "search_policy_v1",
  "updated_at_utc": "2026-03-30T00:00:00Z",
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
  "scopes": {
    "catalogue": {
      "enabled": true,
      "scope_label": "catalogue",
      "back_label": "← works",
      "back_route_key": "series_page_base",
      "input_aria_label": "Search works, series, and moments",
      "input_placeholder": "search works, series, moments"
    },
    "studio": {
      "enabled": false,
      "scope_label": "studio",
      "back_label": "← studio",
      "back_route_key": "studio_home",
      "input_aria_label": "Search Studio docs",
      "input_placeholder": "search studio docs"
    },
    "library": {
      "enabled": false,
      "scope_label": "library",
      "back_label": "← library",
      "back_route_key": "library_page",
      "input_aria_label": "Search library",
      "input_placeholder": "search library"
    }
  },
  "messages": {
    "missing_scope_error": "Search is unavailable without a valid search scope.",
    "unsupported_scope_error": "Search is not yet available for this scope."
  }
}
```

## Runtime lookup

Keep `studio_config.json` narrow, but let it continue to own Studio data paths.

Implemented path in `assets/studio/data/studio_config.json`:

```json
{
  "paths": {
    "data": {
      "search": {
        "policy": "/assets/data/search/policy.json"
      }
    }
  }
}
```

This keeps the shared shell config small while still giving the search page a normal config-based lookup path.

## Code ownership

Do not grow `assets/studio/js/studio-config.js` into the full owner of search policy.

Instead, add one search-specific loader module:

- `assets/js/search/search-policy.js`

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

## Runtime module shape

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
  scopes: { /* ... */ },
  messages: { /* ... */ }
};

export async function loadSearchPolicy(policyUrl) { /* ... */ }
export function getSearchRuntimePolicy(policy) { /* ... */ }
export function getSearchScopePolicy(policy, scope) { /* ... */ }
```

The helpers should return already-sanitized values so `search-page.js` can stay simple.

## `search-page.js` after phase 1

Current flow:

1. load Studio config
2. load search policy
3. resolve scope from the URL
4. validate the scope against policy
5. load the scope-owned index only when the scope is known and enabled
6. initialize page state

Current state includes:

- `runtimePolicy`
- `scopePolicy`
- `visibleCount` from `runtime.results.initial_batch_size`

Current behavior mapping:

- if `runtime.live_search` is `true`, input events run debounced search
- if `runtime.live_search` is `false`, input events do not trigger search
- if `runtime.enter_runs_search` is `true`, Enter runs immediate search
- if `runtime.enter_runs_search` is `false`, Enter does nothing special

## Minimum query length

Current behavior:

- if normalized query length is below `min_query_length`, show the standard prompt state and do not search

That keeps the runtime rule simple and visible.

## Policy-driven batching

Current behavior:

- initial render count from `initial_batch_size`
- each `more` click increments by `batch_increment_size`

## Scope validation before data load

Current behavior:

- if no `scope` query is present, show the missing-scope state
- if the `scope` is unknown to policy, show the missing-scope state
- if the `scope` is known but `enabled: false`, show the unsupported-scope state
- only fetch a scope-owned index when the scope is both known and enabled

This prevents `scope=studio` from becoming a special case in code before the Studio search artifact exists.

## Validation for phase 1

Codex-run checks:

- `node --check assets/js/search/search-page.js`
- `node --check assets/js/search/search-policy.js`
- `./scripts/build_docs.rb --write` if docs change
- `bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Manual checks:

- `/search/?scope=catalogue` still loads correctly
- `/search/?scope=studio` shows a clear unsupported-scope state without trying to load a Studio index
- `/search/?scope=library` shows a clear unsupported-scope state without trying to load a library index
- `/search/` still shows a clear missing-scope state
- typing still gives live results with the configured debounce
- Enter still triggers immediate search when enabled
- `more` still reveals the next result batch
- the page still shows explicit catalogue scope context

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

This should align directly with [Search Field Registry](/docs/?scope=studio&doc=search-field-registry), but only once the runtime is ready to consume it safely.

## Phase 4: Shared runtime/build policy boundary

Only after ranking and field policy are stable should build-time search policy start reading the same config family.

At that point, split policy by responsibility if needed:

- runtime policy
- shared search policy
- build-only policy

Possible later split:

- `assets/data/search/policy.json`
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

Keep phase 1 stable while `scope=studio` is introduced.

Do not implement phases 2 to 5 until the first non-catalogue scope is live enough to show which policy surfaces actually need to be tuned as data.
