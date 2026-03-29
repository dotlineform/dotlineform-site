---
doc-id: search-overview
title: Search Overview
last-updated: 2026-03-29
parent-id: search
sort-order: 10
---

# Search Overview

## Purpose

This document provides a concise overview of the site search subsystem.

It is intended to explain, at a high level, what the search function is for, what kinds of content it covers, how it is structured, and which supporting documents define its detailed behaviour.

This is not the place for field-by-field schema definitions, scoring rules, or implementation walkthroughs. Those belong in the dedicated search documents referenced below.

## Search goals

The search subsystem exists to help users locate site content quickly and predictably without relying on external dependencies or plugins.

The current search design aims to support:

- direct lookup of known items, such as a work title, work ID, or series name
- broader discovery through related terms such as medium, tag labels, or associated metadata
- consistent behaviour across content types included in the search index
- a maintainable architecture in which search policy can be reviewed separately from implementation code

The search system should remain lightweight, understandable, and compatible with the site’s existing static-site architecture.

## Current scope

At a high level, the search subsystem operates by generating a search index during the site build process and loading that index in the browser for client-side querying.

The current implementation is based on:

- a generated search index file
- client-side JavaScript search logic
- no third-party search libraries, plugins, or hosted search services

The search index contains compact records derived from site content and metadata. The browser loads this index and uses it to return matching results in response to user queries.

## Content covered by search

This section should list which site content types are currently included in search.

Initial examples may include:

- works
- series
- themes
- notes
- other page types, if applicable

Codex should replace this placeholder list with the actual current scope of the implementation.

If some content types exist on the site but are intentionally excluded from search, that should also be stated here.

## Search architecture summary

The search subsystem is divided into a small number of distinct parts.

### 1. Source content
Structured site content and metadata act as the input to the search index build step.

### 2. Search index generation
A build-time process transforms source content into a compact search index suitable for browser use.

### 3. Search policy
Configurable policy determines which fields are searchable, how strongly different fields are weighted, and how the search UI behaves.

### 4. Search engine
Client-side JavaScript loads the search index, processes the user query, applies matching and ranking logic, and returns ordered results.

### 5. Search UI
The browser interface captures input, invokes the search engine, and renders the resulting matches.

This document only describes these parts at a high level. Detailed definitions belong in the dedicated supporting documents.

## Design principles

The search subsystem should follow these principles:

### Lightweight
Search should work without external plugins or dependencies.

### Structured
The system should distinguish clearly between search data, search policy, and implementation code.

### Reviewable
Important search behaviour should be understandable from focused documentation and config files, not only from JavaScript.

### Incremental
The architecture should support refinement over time without requiring a full redesign when ranking, indexing, or UI behaviour changes.

### Static-site compatible
The system should fit the existing Jekyll or build-pipeline workflow rather than depending on a dynamic backend.

## Out of scope for this document

This document should not contain:

- full field definitions for search index records
- detailed normalisation rules
- scoring formulas or ranking weights
- UI event handling details
- code-level implementation notes
- validation test cases

Those details belong in the dedicated documents listed below.

## Related documents

The search subsystem is documented in the following companion files:

- `search-config-architecture.md`
- `search-index-schema.md`
- `search-field-registry.md`
- `search-normalisation-rules.md`
- `search-ranking-model.md`
- `search-ui-behaviour.md`
- `search-build-pipeline.md`
- `search-validation-checklist.md`

## Current status

This document should describe the current implemented version of the search subsystem at a high level.

Codex should update this section with a short factual summary of the current state, for example:

- which version is currently implemented
- which content types are currently indexed
- whether the index is generated at build time
- whether ranking is field-aware or flat
- whether scoped search or filters are present yet

This section should remain brief and descriptive.

## Open questions

This section can be used to note high-level unresolved decisions that affect the overall search subsystem.

Examples:
- whether additional content types should be indexed
- whether search should remain global only or later support scoped modes
- whether field weighting should become more granular
- whether the current index format is sufficient for future filtering needs

Only major architectural or scope questions should be listed here. Lower-level issues belong in the more specific search documents.