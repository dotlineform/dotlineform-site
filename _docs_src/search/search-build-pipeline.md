---
doc_id: search-build-pipeline
title: Search Build Pipeline
last_updated: 2026-03-31
parent_id: search
sort_order: 70
---

# Search Build Pipeline

## Purpose

This document defines how the current search artifacts are built.

It covers:

- the current design of the search build layer
- which script currently owns each live scope
- what each scope reads and writes
- how record construction, validation, and change detection work in practice

This is a build-time document. It does not define ranking or UI behaviour.

## Current Design And Implementation

The current search build is one subsystem with two implementation paths.

Why the build is split today:

- `catalogue` search is derived from workbook-driven catalogue data that already exists in memory inside `scripts/generate_work_pages.py`
- `studio` and `library` search are derived from canonical published docs indexes, so they are built by the separate search-owned script `scripts/build_search_data.rb`

Current live search outputs:

- `assets/data/search/catalogue/index.json`
- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`

Current build principles:

- deterministic output from stable inputs
- scope-owned search artifacts
- compact records rather than prose-heavy payloads
- search stays downstream of canonical source systems rather than becoming a new source of truth

Current ownership split:

- `scripts/generate_work_pages.py`
  owns `catalogue` search generation
- `scripts/build_search_data.rb`
  owns docs-domain search generation for `studio` and `library`

This means the current implementation is scope-owned at the artifact level, but not yet unified behind one single build entrypoint.

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

- `scripts/generate_work_pages.py`

### Current Output

- `assets/data/search/catalogue/index.json`

### Current Source Inputs

Primary canonical source:

- `data/works.xlsx`

Current in-memory generator payloads used by search assembly:

- `series_payload`
- `works_payload`
- `moments_payload`
- `canonical_work_record_by_id`

Current tag metadata inputs:

- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_assignments.json`

### Current Build Path

The current catalogue build path is:

1. parse CLI arguments in `scripts/generate_work_pages.py`
2. load workbook and supporting pipeline inputs
3. build works, series, and moments in-memory payloads
4. derive search records from those payloads plus tag metadata
5. sort and assemble the flat search entry list
6. compute header metadata and version hash
7. write `assets/data/search/catalogue/index.json` if changed or forced

Current integration facts:

- search generation is enabled whenever the generator runs
- `--only search-index-json` can be used for a search-focused generator pass
- aggregate JSON artifacts, including search, are treated as always-rebuilt stages within the script execution model

### Current Included Content

- works
- series
- moments

Each included content item becomes one search record.

### Current Exclusions

- full prose or body text
- docs content
- Studio/admin pages
- unrelated site sections outside the current catalogue generator stage

### Current Record Construction

The generator currently uses `build_search_entry(...)` to construct catalogue records.

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
- `storage`
- `series_type`
- `tag_ids`
- `tag_labels`

Current derived search fields:

- `search_terms`
- `search_text`

Current helper functions involved in normalization and derivation:

- `normalize_search_text(value)`
- `build_search_tokens(*values)`
- `assignment_tag_ids_from_rows(tags_value)`

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

- controlled record construction through shared helpers
- normalized and deduplicated token generation
- deterministic sort order before serialization
- content-version hashing for change detection

## Studio Scope

### Current Writer

- `scripts/build_search_data.rb --scope studio`

### Current Output

- `assets/data/search/studio/index.json`

### Current Source Input

- `assets/data/docs/scopes/studio/index.json`

The current Studio search artifact is derived from the published Studio docs index rather than directly from `_docs_src/`.

### Current Commands

Default write command:

```bash
./scripts/build_search_data.rb --scope studio --write
```

Dry run:

```bash
./scripts/build_search_data.rb --scope studio
```

Current supported overrides:

- `--source-index PATH`
- `--output PATH`
- `--write`

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

The generated Studio search artifact is consumed by:

- inline docs search on `/docs/`

## Library Scope

### Current Writer

- `scripts/build_search_data.rb --scope library`

### Current Output

- `assets/data/search/library/index.json`

### Current Source Input

- `assets/data/docs/scopes/library/index.json`

The current Library search artifact is derived from the published Library docs index rather than directly from `_docs_library_src/`.

### Current Commands

Default write command:

```bash
./scripts/build_search_data.rb --scope library --write
```

Dry run:

```bash
./scripts/build_search_data.rb --scope library
```

Current supported overrides:

- `--source-index PATH`
- `--output PATH`
- `--write`

### Current Build Behaviour

Current builder behaviour for Library:

- reads the published Library docs index
- emits one search record per published Library doc
- uses the same docs-domain record contract as Studio, with `scope=library`
- does not create section-level records
- does not index doc body prose
- does not generate summaries or snippets

### Current Runtime Mapping

The generated Library search artifact is consumed by:

- inline docs search on `/library/`

## Change Detection And Write Behaviour

Current write behaviour differs slightly by implementation path, but both paths are content-driven rather than timestamp-driven.

Current catalogue behaviour:

- `scripts/generate_work_pages.py` writes the file when content changed or `--force` is used

Current Studio and Library behaviour:

- `scripts/build_search_data.rb` writes only when `--write` is supplied
- dry runs report the selected scope and target path without persisting output

## Performance And Size Considerations

Current build decisions that keep the search layer lightweight:

- one compact record per searchable item
- no full prose bodies in the base artifacts
- derived search fields are precomputed at build time
- duplicate tokens are removed during generation
- optional empty scalar fields are omitted from serialized output where the current builders do so

The current tradeoff is that search assembly is split across two writers. That is acceptable in the current implementation because each path is still downstream of the canonical source for that scope.

## Related Documents

- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
