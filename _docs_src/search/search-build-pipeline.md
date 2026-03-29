---
doc_id: search-build-pipeline
title: Search Build Pipeline
last_updated: 2026-03-29
parent_id: search
sort_order: 70
---

# Search Build Pipeline

## Purpose

This document defines how the site search index is generated during the build process.

Its purpose is to make the build-time side of the search subsystem explicit and reviewable. It should describe which source content feeds the search index, how records are constructed, where normalisation and derivation occur, what output is produced, and how the build step fits into the wider site pipeline.

This document is about build-time generation. It is not a ranking document, not a UI behaviour document, and not a code walkthrough.

## Scope

This document applies to the process that transforms site content and metadata into the generated search index used by client-side search.

It should cover:

- source inputs to index generation
- inclusion and exclusion rules
- record construction
- normalisation and derived field generation
- output file structure and destination
- when the search index is built
- validation performed during generation
- how the search build integrates with the wider site or generator pipeline

This document should describe the build process in architectural terms rather than line-by-line implementation detail.

## Relationship to other documents

This document should be read alongside:

- `search_overview.md`, which describes the search subsystem at a high level
- `search_index_schema.md`, which defines the output structure of the generated index
- `search_field_registry.md`, which defines how indexed fields participate in search
- `search_normalisation_rules.md`, which defines how values are transformed during indexing
- `search_validation_checklist.md`, which defines how the generated index and search behaviour should be checked

## Build pipeline principles

The search build pipeline should follow these principles:

### Deterministic
Given the same source content and build rules, the generated search index should be stable.

### Minimal
The generated index should include only the fields needed for search, filtering, and result display.

### Reviewable
The transformation from source content to indexed records should be understandable without reading all implementation code.

### Structured
Source fields, derived search fields, and UI support fields should be distinguishable in the output.

### Compatible
The search build should fit cleanly into the existing site build and content-generation workflow.

## Pipeline overview

At a high level, the build pipeline should be described as a sequence of stages.

### 1. Source discovery
The build process reads eligible site content and metadata from the project’s source files or generated data files.

### 2. Inclusion filtering
The build process determines which records should be included in the search index and which should be excluded.

### 3. Record extraction
Relevant source values are extracted from each included content item.

### 4. Normalisation and derivation
Search-ready values are generated, including any normalised or flattened fields.

### 5. Index assembly
The resulting records are collected into the final search index structure.

### 6. Output write
The generated index file is written to its output location for browser use.

### 7. Validation
Basic structural or consistency checks are applied to the generated index.

Codex should replace or refine this generic overview with the actual current build path.

## Source inputs

This section should define exactly which source materials feed the search index.

Examples may include:
- generated JSON data files
- collection front matter
- structured metadata exports
- manually maintained content files
- tag registry or alias files, if used during indexing

Questions to answer:
- What is the canonical source for each content type?
- Does the search build read site source files directly or consume already-generated JSON?
- Are search records built from one unified source layer or multiple inputs?

Codex should document the actual current source inputs.

## Inclusion and exclusion rules

This section should define which content is eligible for indexing.

Questions to answer:
- Which content types are included?
- Are draft or unpublished items excluded?
- Are hidden utility pages excluded?
- Are records excluded if required fields are missing?
- Are some content types intentionally deferred from indexing?

Suggested subsections:

### Included content
List the currently indexed content types.

### Excluded content
List any intentionally excluded content types or record classes.

### Eligibility rules
Describe any required fields or conditions for inclusion.

This section is important because search quality is strongly affected by what enters the index at all.

## Record construction rules

This section should define how individual search records are built from source content.

Questions to answer:
- Which source fields are copied directly into the record?
- Which fields are renamed in the output schema?
- Which fields are omitted even if available in source content?
- Are fields added conditionally based on content type?
- How are arrays, empty values, and missing values handled?

Suggested subsections:

### Core identity fields
Examples:
- content kind
- canonical ID
- title
- link target

### Display support fields
Examples:
- display metadata
- year labels
- secondary result text
- thumbnail or preview fields, if included

### Search support fields
Examples:
- search terms
- flattened search text
- token bundles
- normalised field variants

Codex should describe the actual current construction rules rather than restating schema only.

## Normalisation and derivation stage

This section should define what transformations occur during index generation.

Examples:
- lowercasing
- token splitting
- slug expansion
- phrase retention
- derived term generation
- deduplication
- alias expansion, if applicable

This section should summarise how the pipeline uses the rules described in `search_normalisation_rules.md`.

Questions to answer:
- At what stage are derived fields built?
- Are phrase fields and token fields both emitted?
- Are duplicates preserved or removed?
- Are field-specific transformations applied?

## Output structure and location

This section should define what the build step writes and where.

Questions to answer:
- What is the output filename?
- Where in the site or asset tree is it written?
- Is there a single output file or multiple partitioned files?
- Does the output include metadata such as version, generated timestamp, or record count?
- Is the output intended to be committed, generated locally, or both?

Examples:
- `assets/data/search-index.json`
- multiple partitioned index files under a search data directory

Codex should replace these examples with the actual output location and structure.

## Build integration

This section should explain how search index generation fits into the wider site-generation workflow.

Questions to answer:
- Is the search index generated by a standalone script, by the main content pipeline, or by another generator stage?
- Does it run automatically during site generation or as a separate manual step?
- Does it depend on other generated files already existing?
- Does it need to be rerun whenever content changes?

This section should help clarify where search generation sits in the broader project pipeline.

## Error handling and fallback behaviour

This section should define what the build step does when source data is incomplete or inconsistent.

Questions to answer:
- What happens if a record is missing a title, ID, or link?
- What happens if optional arrays are empty?
- Does the build fail, warn, or silently skip malformed items?
- Are invalid records excluded from the index?

Codex should document the current behaviour and any areas that still need hardening.

## Validation during generation

This section should define any checks performed while building the search index.

Examples:
- required-field presence
- valid content kind values
- unique IDs
- non-empty link targets
- structural consistency of arrays
- duplicate-record detection

Questions to answer:
- Are validation checks currently implemented?
- Are they warnings or hard failures?
- Are record counts or content-type counts verified?
- Is the generated index inspected for obvious redundancy or malformed fields?

This section should describe build-time validation only, not behavioural search testing.

## Performance and size considerations

This section should describe any build-time decisions intended to keep the search index lightweight.

Examples:
- excluding full prose bodies
- using compact derived fields
- omitting fields not needed by search UI
- partitioning output in future if the index grows
- deduplicating repeated terms

Codex should document any current decisions already made in the implementation.

## Current implementation summary

This section should briefly summarise how the current search build pipeline works in practice.

Examples:
- which script or generator stage produces the index
- which source data it reads
- where the index is written
- whether the build is automatic or manual
- whether validation is minimal or explicit
- whether the output is a single flat index or a richer structured object

This section should be concise and factual.

## Known limitations or open pipeline questions

This section should capture unresolved build-pipeline questions only.

Examples:
- whether the build should consume canonical source data or generated site JSON
- whether duplicate derived terms are currently being emitted unnecessarily
- whether partitioned indexes may be needed later
- whether alias expansion should happen during build or at query time
- whether validation should be stricter
- whether search index generation should be integrated more tightly into the main site build

## Out of scope for this document

This document should not define:

- the full search ranking model
- browser UI behaviour
- keyboard interactions
- detailed schema semantics already covered elsewhere
- line-by-line implementation detail

Those belong in other search documents.

## Related documents

This document should be read alongside:

- `search_overview.md`
- `search_policy_externalisation.md`
- `search_index_schema.md`
- `search_field_registry.md`
- `search_normalisation_rules.md`
- `search_ranking_model.md`
- `search_validation_checklist.md`