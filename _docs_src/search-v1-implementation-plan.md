---
doc_id: studio-search-v1-implementation-plan
title: Search V1 Implementation Plan
last_updated: 2026-03-29
parent_id: _archive
sort_order: 20
published: false
---

# Search V1 Implementation Plan

Status:

- implementation planning doc
- aligned to the `Studio Search V1` contract

## Scope

This plan covers:

- build-time generation of `assets/data/search_index.json`
- a Studio page at `/studio/search/`
- in-memory client-side search over the base artifact
- ranking benchmark fixtures and verification

This plan does not cover:

- prose shard implementation
- main-site top-nav rollout
- external search services or plugins
- tag-aware ranking in production before tag coverage is strong enough

## Phase 1: Search Artifact Generator

Goal:

- generate a dedicated `search_index.json` artifact without changing canonical source ownership

Targets:

- `scripts/generate_work_pages.py`
  or a small adjacent search-specific generator module if that keeps responsibilities cleaner
- `assets/data/search_index.json`

Output:

- `search_index_v1` payload
- one flat `entries` array across works, series, and moments
- stable `header.version`
- build-time normalized `search_text` and `search_terms`

Implementation notes:

- treat search generation as a self-contained pipeline module
- read existing canonical source data and generated metadata inputs
- do not make the search artifact the new source of truth for any other page

Benefits:

- clean ownership boundary
- minimal impact on existing browse/index pages

Key risks:

- generator scope becomes muddy if search-specific normalization is mixed carelessly into unrelated browse logic

Verification:

- dry-run summary shows artifact path and record count
- written artifact is deterministic across repeated runs with unchanged input
- payload size is reported

## Phase 2: Field Registry and Classification Enforcement

Goal:

- prevent the base payload from growing without discipline

Targets:

- search generator field-mapping code
- search verification checks

Output:

- one field registry in code
- each field tagged as one or more of:
  - `display`
  - `filter`
  - `ranking`
  - `lazy_enrichment`
- a build check that rejects `lazy_enrichment` fields in the base payload

Recommended checks:

- fail if an entry contains unknown search fields
- fail if a base artifact contains fields not allowed by the field registry
- warn or fail if the payload exceeds an agreed size budget

Benefits:

- field expansion becomes intentional
- future prose work does not accidentally leak into the base index

Key risks:

- over-strict validation can slow iteration if the field registry is awkward to update

Verification:

- generator checks for allowed and disallowed fields
- payload summary includes field list and byte size

## Phase 3: Ranking Engine and Benchmark Fixture

Goal:

- make ranking behavior explicit and tunable

Targets:

- Studio search runtime module
- ranking benchmark fixture file, likely JSON under `assets/studio/data/` or a docs-adjacent test fixture location

Output:

- numeric score tiers matching the v1 ranking order
- benchmark query set with expected top results
- optional debug output for why a result matched

Fixture categories:

- exact id
- exact title
- prefix
- multiple-token
- metadata match
- ambiguous title

Recommended debug data:

- matched fields
- score tier
- tie-break path

Benefits:

- ranking changes can be evaluated rather than guessed
- failures become visible and discussable

Key risks:

- the fixture set may be too small or too biased if only obvious queries are included

Verification:

- report top-1 and top-5 hit rates against the benchmark fixture
- spot-check ambiguous queries manually in the Studio page

## Phase 4: Studio Search Page

Goal:

- expose the search artifact through a dedicated Studio UI

Targets:

- `studio/search/index.md`
- `assets/studio/js/studio-search.js`
- `assets/studio/data/studio_config.json`
- shared Studio UI/CSS only where needed

Output:

- search input
- type filter: `all`, `works`, `series`, `moments`
- result count
- result list
- empty, loading, and error states

Interaction model:

- load the base artifact once per page session
- keep it in memory
- run search in memory after a short debounce
- `Enter` may trigger immediate search, but keypresses must not trigger network fetches

Benefits:

- realistic environment for testing search quality
- no public-site shell coupling yet

Key risks:

- UI can become overbuilt before ranking is proven

Verification:

- page loads cleanly on desktop and mobile
- no repeated network fetches during typing
- result rendering stays responsive with the full base artifact loaded

## Phase 5: Manual Review and Tuning

Goal:

- validate product usefulness before any main-site rollout

Tasks:

1. Run the benchmark fixture and review failures.
2. Test common queries manually in the Studio page.
3. Adjust score tiers or tie-break rules only when failures are clear.
4. Re-run the benchmark after each change.

Manual query set should include:

- known work ids
- exact and partial titles
- series-title lookups
- likely metadata lookups such as medium type
- empty and no-match cases

Benefits:

- search quality improves through visible evidence

Key risks:

- tuning can drift if changes are made without benchmark coverage

## Phase 6: Future Expansion Hooks

Goal:

- leave deliberate extension points without implementing them yet

Hooks to preserve:

- support for optional prose shards
- support for additional filters such as `medium_type`
- support for assigned-tag search fields sourced from `tag_registry.json` and `tag_assignments.json`
- support for a public-site search surface using the same runtime and artifact

Explicitly deferred:

- `search_index_prose.json`
- result snippets from prose
- tag-aware ranking rollout before tag coverage is strong enough
- main-site top-nav search

## Phase 7: Tag-Aware Search Expansion

Goal:

- add tags as a meaningful ranking and filter signal once the data quality is sufficient

Targets:

- search generator field registry
- tag-derived search fields in `assets/data/search_index.json`
- Studio search filters and ranking benchmark fixtures

Inputs:

- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_assignments.json`

Output:

- normalized tag ids and tag labels available to search
- optional tag filters in the Studio page
- ranking tiers that place strong tag matches above weak generic contains matches

Gate before rollout:

- tag coverage is broad enough across the catalogue to improve results consistently
- benchmark fixtures include representative tag queries
- manual review confirms that sparse tags are not distorting relevance

Benefits:

- search can surface conceptually related works beyond title-only matching
- the existing tagging model becomes useful in public discovery as well as Studio management

Key risks:

- sparse or inconsistent tags can produce misleading ranking
- tag labels and aliases may need additional normalization rules before they are search-ready

## Recommended First Implementation Batch

Start with:

1. search generator output
2. field registry and payload-budget checks
3. benchmark fixture
4. Studio search page with in-memory debounced search

This is the smallest slice that proves:

- the artifact contract
- the ranking model
- the UI usefulness

before prose and main-site concerns are added.
