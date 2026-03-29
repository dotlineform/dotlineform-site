---
doc_id: search-normalisation-rules
title: Search Normalisation Rules
last_updated: 2026-03-29
parent_id: search
sort_order: 50
---

# Search Normalisation Rules

## Purpose

This document defines how source values and user queries are normalised for search.

Its purpose is to make the transformation layer of the search subsystem explicit and reviewable. It should describe how raw content becomes searchable terms, how user input is standardised before matching, and how equivalent forms are handled consistently.

This document is about normalisation policy. It is not a schema document, not a ranking document, and not a code walkthrough.

## Scope

This document applies to two related processes:

- **index-time normalisation**, where source content is transformed into search-ready values during index generation
- **query-time normalisation**, where user input is transformed into a comparable form before matching

It should cover:

- lowercasing or case folding
- whitespace handling
- punctuation handling
- hyphen and slug handling
- token splitting
- deduplication
- numeric handling
- alias expansion, if applicable
- any equivalence rules applied consistently across indexing and querying

## Relationship to other documents

This document should be read alongside:

- `search_index_schema.md`, which defines the indexed fields
- `search_field_registry.md`, which defines which fields participate in search
- `search_ranking_model.md`, which defines how normalised matches are prioritised
- `search_build_pipeline.md`, which defines where index-time normalisation occurs
- `search_validation_checklist.md`, which defines how normalisation behaviour should be tested

## Normalisation principles

The normalisation layer should follow these principles:

### Consistent
Equivalent values should be transformed consistently so that index values and user queries can be compared reliably.

### Predictable
Users should not need to know the exact punctuation, case, or formatting used in the source content.

### Conservative
Normalisation should improve retrieval without stripping away distinctions that are meaningful for the site’s content model.

### Reviewable
Important transformation rules should be documented in plain language rather than inferred from implementation details.

### Shared where possible
Index-time and query-time rules should align unless there is a clear reason for them to differ.

## Normalisation stages

The search subsystem may apply normalisation in stages.

### 1. Source value preparation
Raw source fields are read from the site content or metadata layer.

Examples:
- titles
- IDs
- series slugs
- series titles
- medium values
- tag labels

### 2. Index-time normalisation
Values are transformed into search-ready representations during index generation.

Examples:
- lowercasing
- slug expansion
- token splitting
- derived term generation
- deduplication

### 3. Query-time normalisation
User-entered queries are transformed into comparable values.

Examples:
- trimming
- lowercasing
- punctuation reduction
- token splitting
- normalised equivalent generation

### 4. Matching input preparation
The normalised index values and normalised query values are compared by the search engine.

This document defines the transformation rules used up to that point.

## Core normalisation rules

This section should define the base rules that apply broadly across the search system.

The list below is a template. Codex should replace or complete it with the actual current behaviour.

| Rule | Applies at index time | Applies at query time | Notes |
|---|---|---|---|
| Lowercase values | yes | yes | Improves case-insensitive matching |
| Trim leading and trailing whitespace | yes | yes | Basic cleanup |
| Collapse repeated internal whitespace | yes | yes | Makes matching stable |
| Strip or reduce punctuation | yes / no | yes / no | Actual behaviour should be stated explicitly |
| Expand hyphenated slugs to spaced form | yes | yes / no | Important for slug/title equivalence |
| Split phrases into tokens | yes | yes | Used for token matching |
| Deduplicate repeated terms | yes | no / yes | Actual behaviour should be stated explicitly |
| Preserve numeric tokens | yes | yes | Important for IDs, years, numbered titles |

## Query normalisation rules

This section should describe exactly how user input is normalised before matching.

Questions to answer include:

- Is the query lowercased?
- Is punctuation removed, reduced, or preserved?
- Are repeated spaces collapsed?
- Are hyphens treated the same as spaces?
- Is the query split into tokens?
- Are empty tokens removed?
- Are very short tokens discarded?
- Are aliases or equivalent forms expanded?

Suggested format:

### Lowercasing
Describe whether all user queries are case-folded before matching.

### Whitespace cleanup
Describe how leading, trailing, and repeated internal spaces are handled.

### Punctuation handling
Describe whether punctuation is removed, replaced with spaces, or preserved selectively.

### Hyphen and separator handling
Describe whether `grey-series`, `grey series`, and similar variants are treated as equivalent.

### Tokenisation
Describe whether the query is split into tokens and, if so, how.

### Numeric handling
Describe how year-like, ID-like, or mixed alphanumeric queries are handled.

Codex should document the actual current implementation rather than leaving this generic.

## Index-time normalisation rules

This section should describe how source values are transformed when building the search index.

Questions to answer include:

- Which fields are lowercased before storage?
- Which fields are stored in original display form and also in normalised form?
- Are slugs expanded into spaced forms?
- Are phrases split into tokens?
- Are duplicate terms removed?
- Are stop-words removed or preserved?
- Are both phrase and token variants emitted?

Suggested format:

### Structured fields
Describe how source-like fields such as title, year, series titles, medium type, and tag labels are normalised or preserved.

### Derived fields
Describe how derived fields such as `search_terms` and `search_text` are built from structured fields.

### Duplicate handling
Describe whether repeated values are preserved intentionally or removed during index generation.

### Empty-value handling
Describe how empty arrays, null values, and missing values are treated when generating searchable fields.

## Field-specific normalisation rules

Some fields may require different treatment from others.

This section should define any field-specific rules.

Examples:

### id
IDs may be preserved exactly, tokenised minimally, or handled differently from prose-like text.

Questions:
- Is `01261` indexed as a single token only?
- Are numeric IDs ever split?
- Are leading zeros preserved?

### title
Titles may be indexed as both full phrases and split tokens.

Questions:
- Is the full phrase retained?
- Are title tokens deduplicated?
- Are number suffixes such as `11` preserved?

### series_ids
Series slugs may need expansion from hyphenated to spaced form.

Questions:
- Is `grey-series` stored as both `grey-series` and `grey series`?
- Are slug fragments also tokenised separately?

### medium_type
Medium labels may be retained as both full phrases and separate tokens.

Questions:
- Is `digital print` stored as both phrase and tokens?
- Are generic words like `print` preserved even if common?

### tag_labels / tag_ids
Tags may require alias-aware handling.

Questions:
- Are canonical labels and aliases both indexed?
- Are namespace prefixes such as `theme:` preserved, stripped, or both?

Codex should complete this section based on the current field set.

## Equivalence rules

This section should define which different-looking values are intentionally treated as equivalent for search purposes.

Examples:
- uppercase and lowercase forms
- slug form and spaced form
- repeated whitespace and single whitespace
- punctuation-separated and space-separated variants
- canonical labels and approved aliases, if applicable

Examples of equivalence statements:
- `grey-series` should match `grey series`
- `B&W` may match `black and white`, if alias expansion is supported
- `01261` should remain distinct from `1261` if leading zeros are meaningful

This section is important because equivalence decisions strongly affect user expectations.

## Deduplication policy

This section should define whether repeated terms are removed during index generation and whether repeated query tokens matter.

Questions to answer:
- Are duplicate terms removed from `search_terms`?
- Is `search_text` built from deduplicated inputs or raw concatenation?
- Does duplicate presence in a derived field affect matching or ranking?
- Are duplicate structured values preserved if they come from different sources?

This section should document both the policy and the current implementation status.

## Numeric and code-like value policy

Search systems often need special treatment for numbers, years, and IDs.

This section should define:

- whether year values are indexed as strings, numbers, or both
- whether leading zeros are preserved in IDs
- whether numeric tokens are treated differently from prose tokens
- whether a query like `11` should match numbered titles
- whether very common year values are likely to produce broad matches

This document should describe normalisation policy, not ranking priority.

## Alias and synonym policy

If alias expansion or synonym mapping is supported, this section should define it.

Questions to answer:
- Are aliases applied at index time, query time, or both?
- Are aliases used only for tags or also for other fields?
- Are aliases canonicalised into a single form or stored as multiple search forms?
- Are synonym expansions controlled centrally or embedded ad hoc?

If alias or synonym expansion is not yet part of the implemented search system, this section should state that explicitly.

## Unsupported or intentionally excluded transformations

This section should list transformations that are not currently performed.

Examples:
- stemming
- fuzzy matching
- typo correction
- singular/plural expansion
- accent folding
- phonetic equivalence
- semantic synonym inference

Documenting what is deliberately absent is useful because it clarifies user expectations and prevents assumptions about search intelligence.

## Current implementation summary

This section should provide a short factual summary of the current implemented normalisation behaviour.

Examples:
- whether lowercasing is applied
- whether hyphen-to-space expansion is supported
- whether duplicate terms are currently preserved
- whether queries and indexed values are normalised symmetrically
- whether aliases are already incorporated

This section should be concise and descriptive.

## Known limitations or open normalisation questions

This section should capture unresolved normalisation issues only.

Examples:
- whether duplicate title terms are unintentionally overweighted
- whether generic tokens should be removed from derived fields
- whether slug expansion is sufficiently consistent
- whether year and ID handling need clearer separation
- whether field-specific normalisation should be made more explicit
- whether query-time and index-time rules are fully aligned

## Out of scope for this document

This document should not define:

- the full index schema
- the ranking model
- result UI behaviour
- build orchestration details beyond where normalisation occurs
- code-level implementation walkthroughs

Those belong in other search documents.

## Related documents

This document should be read alongside:

- `search_overview.md`
- `search_policy_externalisation.md`
- `search_index_schema.md`
- `search_field_registry.md`
- `search_ranking_model.md`
- `search_build_pipeline.md`
- `search_validation_checklist.md`