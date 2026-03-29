---
doc_id: search-overview
title: Search Overview
last_updated: 2026-03-29
parent_id: search
sort_order: 10
---

# Search Overview

## Purpose

This document gives a high-level overview of the current site search subsystem.

It explains what search currently covers, how the main parts fit together, and which companion documents define the detailed behaviour. It is intentionally broader than the schema, ranking, or UI documents.

## Search goals

The search subsystem exists to help users locate site content quickly and predictably without external plugins or hosted services.

Current goals:

- support direct lookup of known items such as work ids, titles, series ids, series titles, and moment titles
- support broader discovery through compact metadata such as series relationships and selected structured fields
- keep the runtime understandable and deterministic
- keep the payload small enough for responsive client-side use
- separate search policy from the source indexes used by other pages

## Current scope

The current implementation is a Studio-first search surface at `/studio/search/`.

It is based on:

- a dedicated build-time-generated search artifact: `assets/data/search_index.json`
- an in-house client-side search runtime in `assets/studio/js/studio-search.js`
- no third-party search libraries, plugins, or external search services

The browser loads the base search index once for the page session and searches it in memory.

## Content covered by search

Current indexed content types:

- works
- series
- moments

Current content intentionally excluded from v1 search:

- long-form prose or full-text body content
- docs content
- Studio/admin pages
- notes or other non-canonical site sections not represented in the search index

The current search model is built around one record per searchable item in those three content types.

## Search architecture summary

The current subsystem has five main parts.

### 1. Source content

Canonical site data for works, series, moments, and available tag metadata acts as the source input.

### 2. Search index generation

`scripts/generate_work_pages.py` builds a dedicated `search_index.json` artifact at build time. Search owns this artifact separately from `works_index.json`, `series_index.json`, and `moments_index.json`.

### 3. Search policy

Search policy currently exists in a combination of:

- generated field preparation in the build script
- deterministic ranking tiers in the client runtime
- Studio UI text and route config in `assets/studio/data/studio_config.json`

This policy is documented separately so it can later move out of implementation code more cleanly.

### 4. Search engine

The client runtime loads the search index, normalizes the loaded values into runtime-friendly fields, evaluates query matches, assigns score tiers, sorts matches, and returns an ordered result set.

### 5. Search UI

The Studio page captures the query, exposes a kind filter, renders result counts and result rows, and reveals additional result batches with a `more` control when needed.

## Design principles

The current implementation follows these principles.

### Lightweight

The base search experience should remain fast without external infrastructure and without loading prose-heavy payloads by default.

### Structured

Search has its own artifact and its own documentation set rather than piggybacking indefinitely on generic site indexes.

### Reviewable

Search behaviour should be understandable from focused documents covering schema, ranking, normalization, UI behaviour, and build flow.

### Incremental

The base artifact is designed to grow with additional structured fields such as `medium_type` or tags before later expansion into larger prose search shards.

### Static-site compatible

Search remains part of the existing static build pipeline and browser runtime. It does not depend on a dynamic backend.

## Out of scope for this document

This document does not define:

- the full `search_index.json` field schema
- normalization rules or token-preparation logic
- ranking tiers or scoring details
- UI event timing and pagination details
- validation procedure
- future config extraction architecture

Those belong in the dedicated companion documents.

## Related documents

- [Search Index Schema](/docs/?doc=search-index-schema)
- [Search Field Registry](/docs/?doc=search-field-registry)
- [Search Normalisation Rules](/docs/?doc=search-normalisation-rules)
- [Search Ranking Model](/docs/?doc=search-ranking-model)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?doc=search-build-pipeline)
- [Search Validation Checklist](/docs/?doc=search-validation-checklist)
- [Search Change Log Guidance](/docs/?doc=search-change-log-guidance)
- [Search Change Log](/docs/?doc=search-change-log)
- [Search Archive](/docs/?doc=search-archive)

[Search Config Architecture](/docs/?doc=search-config-architecture) is reserved for a later phase and should not be treated as current implementation documentation yet.

## Current status

Current implementation status:

- v1 is implemented as a Studio page at `/studio/search/`
- the search index is generated at build time into `assets/data/search_index.json`
- indexed content types are works, series, and moments
- ranking is field-aware and deterministic rather than flat
- the UI currently supports one text query plus a kind filter: `all`, `works`, `series`, `moments`
- results are rendered client-side in ranked order, with additional batches revealed via `more`

This is a production-like v1 implementation, but still a Studio-first surface rather than a main-site navigation feature.

## Open questions

High-level follow-up questions for the next phase:

- when tag coverage becomes strong enough, how should tags enter ranking and filtering
- when prose content expands substantially, how should prose search be added without inflating the base payload
- which additional structured fields should be promoted from schema presence to first-class ranking or filter signals
- when the Studio implementation is stable enough to move into the main site shell
