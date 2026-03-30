---
doc_id: search-studio-v1-index-shape
title: Search Studio V1 Index Shape
last_updated: 2026-03-30
parent_id: search
sort_order: 103
---

# Search Studio V1 Index Shape

## Purpose

This document defines the proposed v1 search-record shape for `scope=studio` and explains how that first Studio implementation fits into the wider search architecture.

It exists to make the Studio rollout concrete without requiring a full search-pipeline refactor first.

## Design constraint

Studio v1 should be:

- simple enough to implement soon
- compatible with the shared `/search/` shell
- explicitly transitional toward a search-owned pipeline

Studio v1 should not:

- make the docs builder the long-term owner of Studio search
- require the catalogue indexing pipeline to absorb docs-specific schema
- force a full cross-scope generic indexing framework before there is enough evidence for one

## Upstream source for v1

The canonical upstream source for Studio v1 search should be:

- the published Studio docs outputs

That means Studio search can read from the docs system’s canonical published data rather than re-parsing raw Markdown as a first step.

Recommended v1 source material:

- `assets/data/docs/scopes/studio/index.json`
- `assets/data/docs/scopes/studio/by-id/<doc_id>.json`

This keeps the source of truth clear while avoiding direct ownership by the docs builder.

## Proposed v1 record contract

Studio v1 should emit normalized records that fit the shared public search shell.

Required fields:

- `id`
- `kind`
- `title`
- `href`
- `display_meta`
- `search_terms`
- `search_text`

Recommended v1 values:

- `id`
  - the docs `doc_id`
- `kind`
  - `doc`
- `title`
  - the docs title
- `href`
  - the docs viewer URL for the Studio scope
- `display_meta`
  - compact metadata for result display, likely the doc date and possibly the parent section label
- `search_terms`
  - high-value exact/prefix lookup terms such as:
    - `doc_id`
    - title tokens
    - selected section or parent labels when useful
- `search_text`
  - a lightweight normalized text field built from:
    - title
    - doc id
    - parent title or section title
    - possibly small selected metadata fields

## Proposed v1 output shape

Recommended first output:

```json
{
  "scope": "studio",
  "schema": "search_index_studio_v1",
  "generated_at_utc": "2026-03-30T00:00:00Z",
  "entries": [
    {
      "id": "search-config-architecture",
      "kind": "doc",
      "title": "Search Config Architecture",
      "href": "/docs/?scope=studio&doc=search-config-architecture",
      "display_meta": "2026-03-30",
      "search_terms": [
        "search-config-architecture",
        "search",
        "config",
        "architecture"
      ],
      "search_text": "search config architecture 2026 03 30"
    }
  ]
}
```

This is intentionally simpler than the catalogue schema.

## What v1 intentionally omits

Studio v1 does not need:

- a true summary field
- body-prose full-text search
- rich snippet extraction
- scope-wide filter UI
- catalogue-style work metadata fields

Reason:

- the current docs system does not yet have a canonical summary concept
- summary generation would be a separate product decision, not a required precondition for v1 search
- the shared shell already supports useful ranked lookup with a minimal normalized record

## Ranking implications

Studio v1 ranking should be scope-specific.

That likely means:

- strong preference for exact `doc_id`
- strong preference for exact title
- title-token prefix behavior
- fallback to compact `search_text`

This does not need to match catalogue ranking exactly.

The shared runtime should tolerate different scope-specific ranking behavior keyed by `scope`.

## Recommended build ownership for v1

Studio v1 should be implemented as:

- a search-owned adapter over docs outputs

Recommended interpretation:

- the docs builder still publishes canonical docs JSON
- a search-owned build step reads those docs outputs
- that search-owned step emits `assets/data/search/studio/index.json`

This is the key boundary that keeps Studio search compatible with the target architecture.

## What not to do for v1

Avoid these shortcuts:

- adding permanent Studio-search ownership to `scripts/build_docs_data.rb`
- folding docs indexing rules into `scripts/generate_work_pages.py`
- making the shared runtime depend on catalogue-only fields
- inventing a full declarative cross-scope indexing framework before `library` exists

These would increase coupling without enough long-term clarity yet.

## How v1 fits the grand plan

Studio v1 is the first non-catalogue scope.

Its role in the wider plan is:

1. prove that the public `/search/` shell can support a second scope
2. prove that a second scope can use a different upstream source and a simpler normalized record
3. keep search assembly on the search side of the boundary
4. delay deeper shared build abstractions until both `studio` and `library` provide real comparison points

This is exactly the kind of staged implementation the target architecture is meant to allow.

## Suggested implementation order

1. keep the current scope-aware public shell and policy layer as-is
2. add a search-owned Studio index builder that reads canonical docs outputs
3. emit `assets/data/search/studio/index.json`
4. enable `studio` in `assets/data/search/policy.json`
5. add a Studio-owned CTA to `/search/?scope=studio`
6. add scope-specific ranking behavior for `studio`

Only after that should the repo decide whether `catalogue` and `studio` have enough genuine overlap to justify a deeper shared build abstraction.

## Main benefits

- ships Studio search without blocking on a large refactor
- preserves the intended ownership boundary
- keeps the shared runtime contract small and stable
- avoids overfitting catalogue assumptions onto docs search

## Main risks

- some duplication between scope adapters is likely at first
- if Studio v1 reaches too far into body text too early, payload size and ranking complexity may jump before the product model is clear

Those risks are acceptable for a v1 as long as the build boundary stays search-owned.

## Related documents

- [Search Pipeline Target Architecture](/docs/?doc=search-pipeline-target-architecture)
- [Search Public UI Contract](/docs/?doc=search-public-ui-contract)
- [Search Config Architecture](/docs/?doc=search-config-architecture)
- [Search Config Implementation Note](/docs/?doc=search-config-implementation-note)
