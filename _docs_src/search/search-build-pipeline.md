---
doc_id: search-build-pipeline
title: Search Build Pipeline
last_updated: 2026-03-29
parent_id: search
sort_order: 70
---

# Search Build Pipeline

## Purpose

This document defines how the current search index is generated during the build process.

It explains which source inputs feed search, how records are constructed, where normalization and derivation occur, what output is written, and how search generation fits into the wider content-generation workflow.

This is a build-time document. It is not the ranking or UI document.

## Scope

This document applies to the current process that generates:

- `assets/data/search_index.json`

It covers:

- source inputs
- inclusion and exclusion rules
- record construction
- normalization and derived field generation
- output assembly and write behaviour
- current validation and change-detection behaviour
- pipeline integration

## Relationship to other documents

- [Search Overview](/docs/?doc=search-overview) describes the subsystem at a high level
- [Search Index Schema](/docs/?doc=search-index-schema) defines the output structure
- [Search Field Registry](/docs/?doc=search-field-registry) defines how fields participate in search
- [Search Normalisation Rules](/docs/?doc=search-normalisation-rules) defines normalization rules in detail
- [Search Validation Checklist](/docs/?doc=search-validation-checklist) defines operational verification steps

## Build pipeline principles

The current search build follows these principles.

### Deterministic

Given the same source inputs, the generated search payload should be stable.

### Search-owned but pipeline-aligned

Search owns its own generated artifact, but it does not replace the canonical content pipeline or become a new source of truth.

### Compact

The generated payload should contain the fields needed for search, filtering growth, and result display, while excluding large bodies of prose.

### Structured

Structured source-like fields and derived search fields should remain distinguishable in the output.

### Compatible

Search generation should fit into the same generator workflow that already builds works, series, and moments outputs.

## Pipeline overview

The current build path is:

1. parse CLI arguments in `scripts/generate_work_pages.py`
2. load the workbook and supporting pipeline inputs
3. build the normal works, series, and moments in-memory payloads
4. if search generation is enabled, derive search records from those in-memory payloads plus tag metadata
5. sort and assemble the flat search entry list
6. compute a version hash and header metadata
7. write `assets/data/search_index.json` if the content version changed or `--force` is used

Search generation is therefore not a completely separate script today. It is a dedicated artifact stage inside the broader content generator.

## Source inputs

The current search build draws from multiple source layers.

### Canonical workbook-driven content

Primary canonical content still originates from `data/works.xlsx`, read by `scripts/generate_work_pages.py`.

From that generator flow, search consumes the canonical or generator-derived values needed for:

- works
- series
- moments

### Generator-built in-memory payloads

The current search records are built from in-memory payloads already assembled by the main generator:

- `series_payload`
- `works_payload`
- `moments_payload`
- `canonical_work_record_by_id`

This means search is not reparsing page files or consuming the published site HTML.

### Tag metadata inputs

The search build also reads:

- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_assignments.json`

These are used to derive:

- `tag_ids`
- `tag_labels`

for works and series.

### Source-model principle

The current implementation does not make search a new canonical data model. It remains downstream of the existing workbook and pipeline-owned metadata.

## Inclusion and exclusion rules

### Included content

Current indexed content types:

- works
- series
- moments

Each included content item becomes one search record.

### Excluded content

Current intentionally excluded content:

- full prose or body text
- docs content
- Studio/admin pages
- other site sections not represented in the current search generator stage

### Eligibility rules

The current generator applies practical fallback rules rather than strict hard validation at record-construction time.

Examples:

- title falls back to item id if title is missing
- works and series may omit optional structured metadata fields when empty
- empty relationship and tag arrays are still serialized as arrays

The client runtime later discards any malformed entry missing required runtime fields such as `kind`, `id`, `title`, or `href`, but the generator itself currently tries to construct a usable record rather than fail early on sparse optional metadata.

## Record construction rules

The current generator uses one helper, `build_search_entry(...)`, to construct records for all three content kinds.

### Core identity fields

Every record is built with:

- `kind`
- `id`
- `title`
- `href`

Current href conventions:

- works: `/works/<id>/`
- series: `/series/<id>/`
- moments: `/moments/<id>/`

### Display support fields

Depending on content kind, the generator may also include:

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

Current kind-specific construction:

- series records are built from `series_payload` plus series-level tag assignments
- work records combine canonical work metadata, `works_payload` relationships, series-title lookup, inherited series tags, and work-specific tag overrides
- moment records are built from `moments_payload`

### Search support fields

Every record also gets:

- `search_terms`
- `search_text`

These are generated during record construction, not appended later by a separate pass.

## Normalisation and derivation stage

The current derivation step happens inside the generator before serialization.

Current helpers:

- `normalize_search_text(value)`
- `build_search_tokens(*values)`
- `assignment_tag_ids_from_rows(tags_value)`

Current transformation behaviour:

- values are normalized to lowercase text
- whitespace is collapsed
- normalized phrases are retained
- additional split tokens are generated by replacing non-alphanumeric separators with spaces
- duplicate tokens are removed while preserving first-seen order
- `search_text` is built by joining `search_terms` with spaces

Current build inputs to `search_terms` include combinations of:

- id
- title
- display metadata
- year text
- date text
- series ids
- series titles
- `medium_type`
- `storage`
- `series_type`

Tag ids and tag labels are currently serialized structurally, but they are not part of the current `search_terms` build set.

## Output structure and location

Current output:

- one file: `assets/data/search_index.json`

Current top-level structure:

- `header`
- `entries`

Current header includes:

- schema id
- content-derived version hash
- UTC generated timestamp
- entry count

Current output is a generated artifact that is intended to live in the repo’s generated data tree alongside other generated JSON assets.

## Build integration

The current search build is integrated into `scripts/generate_work_pages.py`.

Important current facts:

- search generation is enabled whenever the generator runs
- `--only search-index-json` can be used to run a search-focused generation pass
- aggregate JSON artifacts, including search, are treated as always-rebuilt stages within the script’s execution model
- search output depends on the same generator pass that builds in-memory works, series, and moments payloads

This means search generation is not a post-Jekyll step and not a browser-side preprocessing step. It is part of the content-generation pipeline.

## Error handling and fallback behaviour

Current behaviour is pragmatic rather than heavily validated.

Current examples:

- if a title is missing, the generator falls back to the item id
- if optional metadata is empty, the field may be omitted or serialized as an empty array depending on field type
- if tag registry labels are unavailable for a tag id, the id may still be retained structurally while the label list remains partial or empty

There is not yet a dedicated search-only validation layer that hard-fails on schema or field-policy issues.

## Validation during generation

Current implemented validation is limited but not absent.

Current checks or safeguards include:

- controlled generation through a shared helper `build_search_entry(...)`
- normalized and deduplicated token generation
- deterministic sort order before serialization
- content-version hashing to detect unchanged output

Current change-detection behaviour:

- if the newly generated payload version matches the existing output version and `--force` is not set, the script reports `Wrote: 0. Skipped: 1.`
- otherwise it writes the file when `--write` is supplied

What is not yet implemented as a dedicated search validation layer:

- explicit schema assertion pass
- duplicate-record detection beyond ordinary source identity
- payload size budgets
- classification-rule enforcement
- benchmark-style relevance validation during generation

Those remain future hardening work.

## Performance and size considerations

Current pipeline decisions that keep the base artifact lightweight:

- only one compact record per searchable item
- no full prose bodies in the base artifact
- derived search fields are compact text/token forms rather than richer provenance structures
- duplicate tokens are removed during generation
- optional empty scalar fields are omitted from serialized output

Current future-scaling direction:

- keep the base artifact focused on compact metadata
- add future structured fields carefully
- use later partitioning or shards for prose-heavy search rather than bloating `search_index.json`

## Current implementation summary

Current build behaviour in practice:

- `scripts/generate_work_pages.py` produces the search index
- search reads workbook-derived content plus tag registry and tag assignment data
- records are assembled for works, series, and moments
- normalization and token derivation happen at build time
- the output is one flat generated artifact at `assets/data/search_index.json`
- write-skipping uses a content-derived version hash rather than file timestamps alone
- validation is currently light and pragmatic rather than strict

## Known limitations or open pipeline questions

Current pipeline questions for later phases:

- whether search should eventually move to a dedicated generator module while still sharing canonical inputs
- whether search should add an explicit validation pass for schema, field classification, and payload budgets
- whether tags should enter derived search token generation once tag coverage improves
- whether prose search should be added through separate shards rather than expanding the base artifact
- whether more explicit provenance should be retained between source fields and derived search fields

## Out of scope for this document

This document does not define:

- ranking behaviour
- browser UI behaviour
- keyboard interaction
- detailed field semantics already defined in the schema document
- low-level line-by-line implementation commentary
