---
doc_id: search-build-pipeline
title: "Search Build Pipeline"
last_updated: 2026-04-23
parent_id: search
sort_order: 70
---

# Search Build Pipeline

## Purpose

This document defines how the current search artifacts are built.

It covers:

- the current design of the search build layer
- the single build entrypoint that now owns all live scopes
- what each scope reads and writes
- how record construction, validation, and change detection work in practice

This is a build-time document. It does not define ranking or UI behaviour.

## Current Design And Implementation

The current search build is one subsystem with one build entrypoint:

- `scripts/build_search.rb`

Current live search outputs:

- `assets/data/search/catalogue/index.json`
- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`

Current build principles:

- deterministic output from stable repo inputs
- scope-owned search artifacts
- compact records rather than prose-heavy payloads
- search stays downstream of canonical source systems rather than becoming a new source of truth

Current source boundary:

- `catalogue` search reads canonical repo JSON artifacts, not `works.xlsx` and not non-repo source files
- `studio` and `library` search read canonical published docs indexes

This means search now has one owner even though the upstream source artifacts are different per scope.

## Cross-Scope Conventions

All current search artifacts use the same high-level top-level structure:

- `header`
- `entries`

Current shared build conventions:

- outputs are written under `assets/data/search/<scope>/`
- records are generated at build time, not assembled in the browser
- content-version hashing is used for write skipping
- generated payloads stay compact and avoid body-prose indexing

Current non-goals across all scopes:

- no raw HTML or Markdown parsing at runtime
- no search-specific backend service
- no prose shard loading
- no strict schema-fail validation layer separate from the builders themselves

## Catalogue Scope

### Current Writer

- `./scripts/build_search.rb --scope catalogue`

### Current Output

- `assets/data/search/catalogue/index.json`

### Current Source Inputs

Canonical catalogue source artifacts:

- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/data/moments_index.json`

Current Studio-owned tag metadata inputs:

- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_assignments.json`

Important boundary:

- the search builder treats these checked-in JSON artifacts as canonical from the site’s point of view
- drift between those JSON artifacts and workbook or non-repo source systems is outside search’s responsibility

### Current Build Path

The current catalogue build path is:

1. load the canonical catalogue indexes
2. load Studio tag registry and assignment data
3. derive `series` entries
4. derive `work` entries, including effective tag metadata by combining series tags with work overrides
5. derive `moment` entries
6. sort the flat entry list by kind, title, and id
7. compute header metadata and version hash
8. write `assets/data/search/catalogue/index.json` if changed or forced

Current integration facts:

- `scripts/generate_work_pages.py` no longer writes catalogue search directly
- the draft pipeline now rebuilds catalogue search after `generate_work_pages.py` refreshes the canonical catalogue JSON inputs
- catalogue search can be rebuilt independently as long as those source JSON artifacts already exist

### Current Commands

Default write command:

```bash
./scripts/build_search.rb --scope catalogue --write
```

Dry run:

```bash
./scripts/build_search.rb --scope catalogue
```

Current supported overrides:

- `--series-index PATH`
- `--works-index PATH`
- `--moments-index PATH`
- `--tag-assignments PATH`
- `--tag-registry PATH`
- `--output PATH`
- `--write`
- `--force`

### Current Included Content

- works
- series
- moments

Each included item becomes one search record.

### Current Exclusions

- full prose or body text
- docs content
- Studio/admin pages
- unrelated site sections outside the current catalogue model

### Current Record Construction

Current core identity fields:

- `kind`
- `id`
- `title`
- `href`

Current display and structured support fields may include:

- `year`
- `date`
- `display_meta`
- `series_ids`
- `series_titles`
- `medium_type`
- `series_type`
- `tag_ids`
- `tag_labels`

Current derived search fields:

- `search_terms`
- `search_text`

Current work-only enrichment from per-work JSON may also add values such as:

- `medium_caption`

Current transformation behaviour:

- lowercase normalization
- whitespace collapse
- phrase retention
- additional split-token generation
- duplicate-token removal while preserving first-seen order
- `search_text` assembled from `search_terms`

### Current Validation And Fallbacks

Current behaviour is pragmatic rather than strict.

Current examples:

- missing titles fall back to item id
- optional scalar fields may be omitted when empty
- array-valued relationship and tag fields are still serialized as arrays
- partial tag-label lookup does not block record generation

Current safeguards include:

- normalized and deduplicated token generation
- deterministic sort order before serialization
- content-version hashing for change detection

## Studio Scope

### Current Writer

- `./scripts/build_search.rb --scope studio`

### Current Output

- `assets/data/search/studio/index.json`

### Current Source Input

- `assets/data/docs/scopes/studio/index.json`

The current Studio search artifact is derived from the published Studio docs index rather than directly from `_docs_src/`.

### Current Commands

Default write command:

```bash
./scripts/build_search.rb --scope studio --write
```

Dry run:

```bash
./scripts/build_search.rb --scope studio
```

Current supported overrides:

- `--source-index PATH`
- `--output PATH`
- `--write`
- `--force`

### Current Build Behaviour

Current builder behaviour for Studio:

- reads the published Studio docs index
- emits one search record per published Studio doc
- keeps record shape compatible with the shared Docs Viewer inline search runtime
- does not create section-level records
- does not index doc body prose
- does not generate summaries or snippets

Current record inputs come from docs metadata such as:

- `doc_id`
- `title`
- `last_updated`
- `parent_id`
- `viewer_url`

Current derived search support fields:

- `search_terms`
- `search_text`

### Current Runtime Mapping

- consumed by inline docs search on `/docs/`
- not consumed by the dedicated `/search/` page
- manual docs rebuilds remain split:
  - `./scripts/build_docs.rb --scope studio --write`
  - `./scripts/build_search.rb --scope studio --write`
- live docs-management actions rebuild the current docs scope and then rebuild same-scope docs search automatically
- `bin/dev-studio` now runs a startup `studio` docs-search rebuild and then uses the Docs Live Rebuild Watcher to keep `_docs_src/*.md` changes aligned with `assets/data/search/studio/index.json`

## Library Scope

### Current Writer

- `./scripts/build_search.rb --scope library`

### Current Output

- `assets/data/search/library/index.json`

### Current Source Input

- `assets/data/docs/scopes/library/index.json`

The current Library search artifact is derived from the published Library docs index rather than directly from `_docs_library_src/`.

### Current Commands

Default write command:

```bash
./scripts/build_search.rb --scope library --write
```

Dry run:

```bash
./scripts/build_search.rb --scope library
```

Current supported overrides:

- `--source-index PATH`
- `--output PATH`
- `--write`
- `--force`

### Current Build Behaviour

Current builder behaviour for Library:

- matches the same docs-domain record model used by Studio
- reads only the published Library docs index
- emits one search record per published Library doc
- stays compatible with the shared Docs Viewer inline search runtime

### Current Runtime Mapping

- consumed by inline docs search on `/library/`
- not consumed by the dedicated `/search/` page
- manual docs rebuilds remain split:
  - `./scripts/build_docs.rb --scope library --write`
  - `./scripts/build_search.rb --scope library --write`
- live docs-management actions rebuild the current docs scope and then rebuild same-scope docs search automatically
- while `bin/dev-studio` is running, the Docs Live Rebuild Watcher also keeps `_docs_library_src/*.md` changes aligned with `assets/data/search/library/index.json`

## Related Documents

- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Data Models: Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Data Models: Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Data Models: Library Scope](/docs/?scope=studio&doc=data-models-library)
