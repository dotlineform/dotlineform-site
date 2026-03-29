---
doc-id: search-field-registry
title: Search Field Registry
last-updated: 2026-03-29
parent-id: search
sort-order: 30
---

# Search Field Registry

## Purpose

This document defines how fields in the search index participate in the search system.

Its purpose is not to define the raw schema of the search index, but to describe the search role of each field. It should explain which fields are searchable, which are filterable, which are displayed in results, which are used only for support, and how each field is intended to contribute to retrieval and ranking.

This document is the review surface for field-level search policy.

## Scope

This document applies to fields present in the generated search index and describes their role in the search subsystem.

It should cover:

- which fields are searchable
- which fields are filterable
- which fields are shown in result displays
- which fields are intended to carry high, medium, or low search importance
- which fields support exact, phrase, prefix, or token matching
- which fields are structured source fields versus derived search support fields

This document should describe field policy, not low-level matching implementation.

## Relationship to other documents

This document should be read as the policy companion to the schema document.

- `search-index-schema.md` defines what fields exist and what they mean
- `search-field-registry.md` defines how those fields behave in search
- `search-ranking-model.md` defines how field matches are prioritised
- `search-normalisation-rules.md` defines how field values are transformed for retrieval
- `search-ui-behaviour.md` defines how search results are presented to the user

## Field registry principles

The field registry should follow these principles:

### Explicit
Each indexed field should have a defined search role rather than being included implicitly.

### Minimal
A field should not participate in search unless there is a clear reason for it to do so.

### Reviewable
Field behaviour should be inspectable in one place without reading search engine code.

### Stable
The field registry should describe search intent, not transient implementation shortcuts.

### Structured
Where possible, the registry should distinguish between:
- display fields
- retrieval fields
- filter fields
- support-only fields

## Registry table

This table should be completed for every field in the current search index schema.

| Field name | Searchable | Filterable | Displayed in results | Importance | Match modes | Field class | Notes |
|---|---|---|---|---|---|---|---|
| kind | no / yes | yes | optional | low | exact | structural | Used primarily for grouping or filtering |
| id | yes | optional | optional | high | exact, prefix | structured | Useful for direct known-item lookup |
| title | yes | no | yes | high | exact phrase, prefix, token | structured | Usually the strongest retrieval field |
| href | no | no | no | none | none | support | Navigation target only |
| ... | ... | ... | ... | ... | ... | ... | ... |

Codex should replace this template with the actual current registry for all implemented fields.

## Field classes

Each field in the registry should be assigned to one of a small number of field classes.

Suggested classes:

### Structured
Fields directly representing meaningful source content or metadata.

Examples:
- title
- year
- medium-type
- series-titles
- tag-labels

### Structural
Fields used to define the record or content type rather than to carry descriptive search content.

Examples:
- kind
- id, if treated partly as a structural identifier
- internal grouping fields

### Derived
Fields generated during index build to support retrieval.

Examples:
- search-terms
- search-text
- flattened token arrays
- normalised composite fields

### Support
Fields used by the UI or runtime but not intended to influence search relevance.

Examples:
- href
- thumbnail URL
- preview image, if present
- display-only metadata fields that are not searched

Codex should confirm whether these classes are sufficient for the current implementation or refine them if needed.

## Field definition template

Each field should also have a short prose definition in this document.

Use the following pattern.

### title
Searchable: yes  
Filterable: no  
Displayed in results: yes  
Importance: high  
Match modes: exact phrase, prefix, token  
Field class: structured  

Purpose:
Primary human-readable label for the item and the most important known-item retrieval field.

Notes:
Title matches should usually outrank matches from supporting metadata fields.

### id
Searchable: yes  
Filterable: optional  
Displayed in results: optional  
Importance: high  
Match modes: exact, prefix  
Field class: structural  

Purpose:
Stable canonical identifier used for direct lookup and internal identity.

Notes:
Numeric or code-like IDs may require different handling from descriptive text fields.

Codex should extend this section for every field in the current implementation.

## Searchability rules

This section should describe the policy used to decide whether a field is searchable at all.

Typical reasons for including a field:
- users are likely to query it directly
- it is useful for discovery
- it adds important context not already present elsewhere
- it improves known-item retrieval

Typical reasons for excluding a field:
- it is purely technical
- it is redundant with stronger fields
- it adds noise without improving retrieval quality
- it is intended only for rendering or internal navigation

Codex should state the actual current inclusion logic if it is known from the implementation.

## Filterability rules

This section should define which fields are suitable for structured filtering rather than free-text search.

Examples of fields that may be filterable:
- kind
- year
- series-ids
- tag-ids
- medium-type

Examples of fields that are usually not filterable:
- title
- search-text
- free-form descriptive text

If filters are not yet implemented, this section should still identify which fields are intended to support future filtering.

## Display rules

This section should define which fields are intended to appear in search results and in what role.

Examples:
- title as the primary result label
- display-meta as secondary text
- kind as a badge or grouping label
- preview image as optional visual support
- matching tags or snippets as optional supporting context

This document should describe field display roles, not detailed markup or UI layout.

## Importance classes

This section should explain the meaning of the field importance labels used in the registry table.

Suggested classes:

### High
Fields strongly associated with direct lookup and primary relevance.

Typical examples:
- title
- id
- canonical series title
- primary tag label, depending on the content model

### Medium
Fields useful for discovery and contextual relevance, but usually weaker than title-like fields.

Typical examples:
- medium-type
- secondary metadata
- associated series titles
- selected labels

### Low
Fields that may contribute to recall but should not dominate ranking.

Typical examples:
- year
- broad fallback text
- generic tokens
- flattened support fields

### None
Fields not intended to contribute to relevance.

Typical examples:
- href
- UI-only support fields

Codex should align these classes with the implemented ranking model.

## Match mode policy

This section should define which types of matching are appropriate for each class of field.

Possible match modes:
- exact
- exact phrase
- phrase
- prefix
- token
- substring
- none

Examples:
- `id` may support exact and prefix matching
- `title` may support exact phrase, prefix, and token matching
- `year` may support exact matching only
- `search-text` may support token or substring matching as fallback only

This document should describe policy, not algorithmic details.

## Derived field policy

Derived fields require special attention because they often collapse multiple sources into one field.

This section should state:

- which derived fields exist
- why they exist
- whether they are intended for recall, fallback, performance, or convenience
- whether they are expected to have lower priority than structured fields
- whether they preserve or lose field provenance

Examples:
- `search-terms` may provide flattened token access
- `search-text` may provide broad fallback matching
- derived fields may be useful for v1 simplicity but may also reduce ranking precision

Codex should document the actual current approach.

## Common field-policy questions

This section should capture recurring review questions such as:

- should a field remain searchable if it duplicates stronger fields?
- should a display field also be searchable?
- should canonical IDs and human-readable labels both be indexed?
- should derived fields be used only as fallback?
- should empty array fields still be explicitly present in the schema?

These are field-policy questions, not schema or implementation questions.

## Open questions

This section should capture unresolved field-registry questions only.

Examples:
- whether some fields are currently over-indexed
- whether generic tokens should remain in derived fields
- whether title-related terms are duplicated too heavily
- whether future filters require promoting additional structured fields
- whether field provenance should be preserved more explicitly in the index

## Out of scope for this document

This document should not contain:

- full raw schema definitions
- low-level tokenisation rules
- exact scoring formulas
- UI event handling details
- build-script implementation notes

Those belong in other search documents.