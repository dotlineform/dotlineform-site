---
doc_id: search-index-schema
title: Search Index Schema
last_updated: 2026-03-29
parent_id: search
sort_order: 20
---

# Search Index Schema

## Purpose

This document defines the structure of the generated search index used by the site search subsystem.

Its purpose is to describe the schema of the index records clearly and explicitly so that the data contract is reviewable without reading the index builder code or the browser search logic.

This document should define what fields exist in the search index, what each field means, how each field is used, and whether each field is intended for display, retrieval, filtering, or internal support.

This is a schema document. It should not contain scoring rules, UI behaviour, or implementation walkthroughs.

## Scope

This document applies to the generated search index file or files used by client-side search.

It should cover:

- the top-level structure of the index
- the schema for each indexed record
- the meaning and intended use of each field
- any required versus optional fields
- any known content-type-specific variations in record shape

If the search system later uses multiple index files or partitions, this document should either describe the shared schema or clearly identify where schemas diverge.

## Top-level index structure

This section should describe the overall shape of the generated index.

Examples of possible top-level shapes include:

- an array of records
- an object containing metadata plus a records array
- an object containing multiple grouped record arrays by content type

Codex should replace this placeholder text with the actual current top-level structure of the implemented search index.

This section should state:

- whether the top level is an array or object
- whether index-level metadata is present
- whether records from multiple content types share a single collection
- whether any version or generation metadata is included

## Record model

Each search record represents one searchable content item.

A record should contain enough information for the browser to:

- identify the item
- link to the item
- display a basic result
- match the item against user queries
- optionally filter or group the result

The search record should remain compact. It is not intended to duplicate the full content model of the source page.

## Core record fields

This section should list the fields that all indexed records are expected to contain.

The table below is a template and should be completed with the actual current schema.

| Field name | Type | Required | Purpose | Notes |
|---|---|---:|---|---|
| kind | string | yes | Identifies the content type of the indexed item | Examples: work, series, theme |
| id | string | yes | Canonical identifier for the item | Should remain stable across builds |
| title | string | yes | Primary display title and high-value search field | Usually the main label shown in results |
| href | string | yes | Relative or absolute link to the item | Used by the search UI to navigate |
| ... | ... | ... | ... | ... |

Codex should replace or complete this table based on the current implemented schema.

## Field definitions

This section should define each field individually.

Each definition should include:

- field name
- type
- whether it is required or optional
- semantic meaning
- whether it is display-oriented, search-oriented, filter-oriented, or mixed
- any known constraints or formatting rules

Suggested format:

### kind
Type: string  
Required: yes  
Purpose: identifies the indexed content type.  
Usage: used for result grouping, filtering, and type-aware rendering.  
Notes: values should come from a controlled set.

### id
Type: string  
Required: yes  
Purpose: provides the canonical stable identifier for the indexed item.  
Usage: used for direct lookup, internal result identity, and possible ID search.  
Notes: should not be derived from transient display text.

### title
Type: string  
Required: yes  
Purpose: primary human-readable title of the indexed item.  
Usage: display field and high-priority retrieval field.  
Notes: usually the most important ranking field.

Codex should continue this pattern for every field in the current schema.

## Display fields vs search fields

This section should distinguish between fields intended primarily for display and fields intended primarily for search.

Examples of display-oriented fields:
- title
- display_meta
- href
- thumbnail or preview fields, if present

Examples of search-oriented fields:
- search_terms
- search_text
- normalised field variants
- derived token arrays

Some fields may serve both purposes.

Codex should describe the actual split used by the current implementation.

## Structured fields vs derived fields

This section should distinguish between:

- structured source-like fields carried into the index
- derived search support fields produced during index generation

Examples of structured fields:
- year
- series_ids
- series_titles
- medium_type
- tag_ids
- tag_labels

Examples of derived fields:
- search_terms
- search_text
- normalised variants
- flattened arrays or token bundles

This distinction matters because structured fields are usually easier to review semantically, while derived fields are often implementation-oriented.

## Optional and content-specific fields

Not all record types may require exactly the same fields.

This section should describe:

- which fields are always present
- which fields may be empty arrays or null values
- which fields appear only for certain content types
- whether missing values are omitted, set to null, or set to empty collections

Codex should document the current implementation clearly and consistently.

## Field constraints and conventions

This section should document any important formatting or consistency rules that apply to index fields.

Examples:
- IDs must be strings even when numerically shaped
- years may be numeric or string values; the actual implementation should be stated explicitly
- arrays should contain canonical values, display values, or both
- empty relationships should use empty arrays rather than omitted keys, if that is the chosen convention
- links should be relative site paths unless otherwise stated

This section should focus on data contract rules, not ranking behaviour.

## Example record

This section should provide one or more real or representative example records from the current implementation.

At minimum it should include:
- one work record
- one non-work record if the schema differs meaningfully by content type

Examples should be short enough to inspect comfortably but complete enough to show the actual field shape.

## Schema design notes

This section should briefly explain why the current schema is shaped the way it is.

Examples of useful notes:
- why both canonical IDs and display labels are included
- why both structured fields and flattened search fields exist
- why some fields are duplicated in derived form
- why the index is intentionally compact rather than content-complete

These notes should be brief and architectural, not a build-pipeline narrative.

## Known limitations or open schema questions

This section should capture unresolved schema questions only.

Examples:
- whether certain derived fields are too redundant
- whether field provenance should be preserved more explicitly
- whether future filters require additional structured fields
- whether empty optional fields should remain explicit or be omitted

Only schema-level questions belong here.

## Out of scope for this document

This document should not define:

- how queries are normalised
- how records are scored
- how results are rendered
- keyboard or interaction behaviour
- build process steps in detail

Those belong in other search documents.