---
doc_id: search-overview
title: Search Overview
last_updated: 2026-03-30
parent_id: search
sort_order: 20
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

The current implementation has two public search surfaces:

- a dedicated catalogue search page at `/search/`
- an inline Studio docs search experience on `/docs/`
- an inline Library docs search experience on `/library/`

It is based on:

- a dedicated build-time-generated catalogue search artifact: `assets/data/search/catalogue/index.json`
- a dedicated search-owned Studio search artifact: `assets/data/search/studio/index.json`
- a dedicated search-owned Library search artifact: `assets/data/search/library/index.json`
- an in-house client-side search runtime in `assets/js/search/search-page.js`
- a shared docs viewer runtime in `assets/js/docs-viewer.js` which now owns inline Studio and Library docs search
- no third-party search libraries, plugins, or external search services
- an initial search-owned builder entrypoint for future non-catalogue scopes at `scripts/build_search_data.rb`

The browser loads scope-owned search data into memory per surface as needed.

## Content covered by search

Current indexed content types:

- works
- series
- moments
- Studio docs
- Library docs

Current content intentionally excluded from v1 search:

- long-form prose or full-text body content
- Studio/admin tools and non-doc pages
- notes or other non-canonical site sections not represented in the search index

The current search model is built around one record per searchable item in those three content types.

## Search architecture summary

The current subsystem has five main parts.

### 1. Source content

Canonical site data for works, series, moments, and available tag metadata acts as the source input.

### 2. Search index generation

`scripts/generate_work_pages.py` builds a dedicated catalogue search artifact at build time. Search owns this artifact separately from `works_index.json`, `series_index.json`, and `moments_index.json`.

### 3. Search policy

Search policy currently exists in a combination of:

- generated field preparation in the build script
- deterministic ranking tiers in the client runtime
- shared search UI text and route config in `assets/studio/data/studio_config.json`

This policy is documented separately so it can later move out of implementation code more cleanly.

### 4. Search engine

The client runtime loads the search index, normalizes the loaded values into runtime-friendly fields, evaluates query matches, assigns score tiers, sorts matches, and returns an ordered result set.

### 5. Search UI

Catalogue search uses the dedicated `/search/` page, while Studio docs search is handled inline in the docs viewer by replacing the right content pane with results when `q` is present in the docs URL.

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

- the full catalogue search index field schema
- normalization rules or token-preparation logic
- ranking tiers or scoring details
- UI event timing and pagination details
- validation procedure
- future config extraction architecture

Those belong in the dedicated companion documents.

## Related documents

- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)
- [Search Pipeline Target Architecture](/docs/?scope=studio&doc=search-pipeline-target-architecture)
- [Search Studio V1 Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Search Change Log Guidance](/docs/?scope=studio&doc=search-change-log-guidance)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)
- [Search Archive](/docs/?scope=studio&doc=search-archive)

[Search Config Architecture](/docs/?scope=studio&doc=search-config-architecture) is reserved for a later phase and should not be treated as current implementation documentation yet.

## Current status

Current implementation status:

- v1 is implemented as a public page at `/search/`
- the current dedicated public route is `/search/?scope=catalogue`
- the dedicated `/search/` runtime and policy are now trimmed to catalogue-only behavior
- the current catalogue search index is generated at build time into `assets/data/search/catalogue/index.json`
- a search-owned Studio builder emits `assets/data/search/studio/index.json` from published Studio docs outputs
- a search-owned Library builder emits `assets/data/search/library/index.json` from published Library docs outputs
- indexed content types are works, series, moments, Studio docs, and Library docs
- ranking is field-aware and deterministic rather than flat
- the UI currently searches all indexed catalogue kinds together and does not expose per-kind filter buttons
- Studio docs search is inline on `/docs/`
- Library docs search is inline on `/library/`
- results are rendered client-side in ranked order, with additional batches revealed via `more`

This is a production-like implementation with a dedicated catalogue search page and an inline Studio docs search surface, but it is still early in the wider multi-domain search architecture.

## Open questions

High-level follow-up questions for the next phase:

- when tag coverage becomes strong enough, how should tags enter ranking and filtering
- when prose content expands substantially, how should prose search be added without inflating the base payload
- which additional structured fields should be promoted from schema presence to first-class ranking or filter signals
- how the later `studio` and `library` scopes should plug into the same public route contract
- when the second search scope is live, what abstractions truly want to be shared across scope adapters and what should remain scope-specific
