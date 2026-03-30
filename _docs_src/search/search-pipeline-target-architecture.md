---
doc_id: search-pipeline-target-architecture
title: Search Pipeline Target Architecture
last_updated: 2026-03-30
parent_id: search
sort_order: 102
---

# Search Pipeline Target Architecture

## Purpose

This document sketches the intended end-state ownership model for the whole search subsystem.

It exists to keep near-term search work pragmatic without letting search become conceptually owned by either the site generator or the docs builder.

This is an architecture-direction document. It is not a build-spec or implementation checklist.

## Core ownership rule

The long-term owner of search should be:

- the search subsystem itself

The long-term owners of canonical content should remain:

- the site generator for works, series, and moments canonical outputs
- the docs builder for Studio and library docs canonical outputs

Search should consume canonical outputs from those systems, but should not be embedded inside them as a permanent responsibility.

## Target end-state

The intended end-state is:

1. content systems publish canonical data
2. a search-owned pipeline reads that canonical data through scope adapters
3. the search pipeline emits scope-owned search artifacts
4. the public `/search/` shell consumes those scope-owned artifacts

That means:

- canonical content publication stays local to each source domain
- search indexing, normalization-for-search, and search artifact assembly belong to search
- the runtime stays scope-led rather than source-system-led

## Target layers

### 1. Canonical publishers

Examples:

- the site generator publishes canonical JSON for:
  - works
  - series
  - moments
- the docs builder publishes canonical docs JSON for:
  - Studio docs
  - library docs

These systems publish the source material that search should index.

They do not own the final search artifacts as a long-term design.

### 2. Search-owned build pipeline

Target entrypoint shape:

- one search-owned build script such as:
  - `scripts/build_search_data.rb`
  - or `scripts/build_search_data.py`

Target responsibilities:

- read scope-owned canonical outputs
- normalize them into a search record contract
- apply scope-owned inclusion rules
- emit scope-owned search artifacts
- keep search-specific logic out of unrelated publishers

### 3. Scope adapters

The search pipeline should own one adapter per content domain.

Expected scopes:

- `catalogue`
- `studio`
- `library`

Each adapter can:

- read a different canonical source
- map different upstream fields
- emit different scope-specific metadata
- use different ranking behavior at runtime

The adapters should share only the abstractions that are genuinely common.

### 4. Shared public shell

The public route stays:

- `/search/`

The shared shell should remain responsible for:

- reading `scope`
- loading the matching search artifact
- applying scope-aware shell policy
- rendering one common result interface

The shell should not assume all scopes have the same upstream schema or the same ranking rules.

## Scope-owned artifacts

Expected search outputs:

- `assets/data/search/catalogue/index.json`
- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`

Later additions may include:

- per-scope policy/config
- derived shard files
- validation reports

The route contract should not need to change when these are added.

## What should be shared

These should be shared across the whole search system:

- public route and URL contract
- scope vocabulary
- runtime shell policy model
- minimal normalized search-record contract
- shared utility code only where reuse is real

## What should not be forced into one abstraction too early

These should remain scope-specific until there is evidence they truly want one abstraction:

- upstream source schema
- field extraction rules
- summary-generation rules
- ranking behavior
- build inclusion rules
- validation details

Prematurely forcing all scopes into one generic indexing framework would add complexity before the real common boundaries are known.

## Relationship to current repo state

Current state is transitional:

- `catalogue` search output is still built from `scripts/generate_work_pages.py`
- docs canonical outputs are still built from `scripts/build_docs_data.rb`
- the public `/search/` shell is already scope-led
- the runtime now has a scope-aware policy layer

This is acceptable as long as new scope work continues to move toward search-owned indexing rather than deeper embedding inside upstream publishers.

## Transitional rule

During the transition:

- upstream systems may continue to publish canonical content outputs
- temporary search outputs may still be produced near those systems
- but new search logic should be designed so it can move into a search-owned pipeline without changing the public route contract

This is the main design constraint for `scope=studio`.

## Why this matters before `studio`

Studio search will likely differ from catalogue search in:

- source schema
- available metadata
- result presentation details
- ranking priorities

Without an explicit target architecture, there is a risk of:

- embedding Studio search in the docs builder
- embedding more search logic in the site generator
- creating multiple incompatible search artifacts

This document exists to prevent that.

## Recommended near-term rule

Before `scope=studio` is implemented:

- treat the docs builder as the publisher of canonical docs outputs
- treat Studio search indexing as a search concern
- if a temporary implementation reads docs outputs directly, that is acceptable
- do not treat the docs builder itself as the long-term owner of Studio search

## Main benefits

- preserves a clean ownership boundary as search grows
- allows scope-specific indexing without locking search into upstream systems
- keeps the public runtime stable while build internals evolve
- gives `studio` and `library` a clear place in the architecture before they are live

## Main risks

- if the target architecture is treated as a hard framework too early, implementation may become slower than necessary
- if the transition period lasts too long, temporary ownership boundaries may become de facto permanent

The right balance is to keep the end-state explicit while still shipping scope work incrementally.

## Related documents

- [Search Public UI Contract](/docs/?doc=search-public-ui-contract)
- [Search Config Architecture](/docs/?doc=search-config-architecture)
- [Search Config Implementation Note](/docs/?doc=search-config-implementation-note)
- [Search Studio V1 Index Shape](/docs/?doc=search-studio-v1-index-shape)
