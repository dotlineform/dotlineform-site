---
doc_id: search-overview
title: Search Overview
added_date: 2026-03-31
last_updated: "2026-05-11 12:50"
parent_id: search
sort_order: 10
---
# Search Overview

## Purpose

This document gives a high-level overview of the current search subsystems.

It explains the current implementation and the architecture direction for separating search by data domain.
It is intentionally broader than the schema, ranking, or UI documents.

## Search goals

Search exists to help users locate data-domain content quickly and predictably without external plugins or hosted services.

There is no meaningful generic global site search target for this project.
The searchable domains are:

- Catalogue, which is structured artwork data
- Docs, which is document-domain content served by Docs Viewer

`/analysis/` may be concerned with catalogue subject matter, but architecturally it is still a document corpus.
It belongs to Docs search.

Current goals:

- support direct lookup of known items such as work ids, titles, series ids, series titles, and moment titles
- support broader discovery through compact metadata such as series relationships and selected structured fields
- support document lookup inside each Docs Viewer corpus
- keep the runtime understandable and deterministic
- keep the payload small enough for responsive client-side use
- keep Catalogue search policy separate from Docs search policy

## Current scope

The current implementation has these live search surfaces:

- a dedicated Catalogue search page at `/search/?scope=catalogue`
- inline Studio docs search on `/docs/`
- inline Library docs search on `/library/`
- inline Analysis docs search on `/analysis/`

It is based on:

- a dedicated build-time-generated catalogue search artifact: `assets/data/search/catalogue/index.json`
- a current transitional Studio docs search artifact: `assets/data/search/studio/index.json`
- a current transitional Library docs search artifact: `assets/data/search/library/index.json`
- a current transitional Analysis docs search artifact: `assets/data/search/analysis/index.json`
- an in-house client-side search runtime in `assets/js/search/search-page.js`
- opt-in dedicated-route performance instrumentation in `assets/js/search/search-performance.js`
- a shared docs viewer runtime in `assets/js/docs-viewer.js` which owns inline docs search behavior
- no third-party search libraries, plugins, or external search services
- a current transitional builder entrypoint for all live search artifacts at `scripts/build_search.rb`
- a current transitional build-owned source-family config at `scripts/search/build_config.json`

The browser loads domain-owned search data into memory per surface as needed.
The dedicated `/search/` page should be treated as Catalogue search unless a later route becomes a chooser between domain-specific search surfaces.

For the role of those artifacts in the wider site model, use [Data Models](/docs/?scope=studio&doc=data-models). This section stays focused on the search subsystem itself.

## Content covered by search

Current indexed content types:

- works
- series
- moments
- Studio docs
- Library docs
- Analysis docs

Current content intentionally excluded from v1 search:

- long-form prose or full-text body content
- Studio/admin tools and non-doc pages
- notes or other non-canonical site sections not represented in the search index

Catalogue search and Docs search both currently emit one record per searchable item, but they should not be treated as one product policy.
They have different source models and different search objectives.

## Search architecture summary

The current implementation still has a shared build entrypoint, but the target architecture has two domain search products.

### 1. Source Content

Catalogue search reads canonical site data for works, series, moments, and available tag metadata.
Docs search reads generated Docs Viewer indexes for document scopes.

Those source and upstream artifact families are documented in:

- [Data Models: Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Data Models: Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Data Models: Library Scope](/docs/?scope=studio&doc=data-models-library)

### 2. Search Index Generation

`scripts/build_search.rb` currently builds all live search artifacts at build time.
For `catalogue`, it reads the canonical repo JSON artifacts written by `scripts/catalogue/generate_work_pages.py`.
For docs scopes, it reads the canonical generated Docs Viewer indexes, skips docs with `viewable: false`, and can patch affected docs-search entries by `doc_id`.

Target direction:
Docs search build configuration should move under Docs Viewer ownership so portable Docs Viewer installs do not need the Catalogue/public search product.

### 3. Search Policy

Search policy currently exists in a combination of:

- generated field preparation in the build script
- deterministic ranking tiers in the client runtime
- dedicated `/search/` runtime policy in `assets/data/search/policy.json`
- shared route/data-path lookup and shared UI text in `assets/studio/data/studio_config.json`

Target direction:
Catalogue search and Docs search should own separate policies.
Shared low-level text helpers are acceptable only when they stay domain-neutral.

The file-level config boundary is documented in the new **[Config](/docs/?scope=studio&doc=config)** section.

### 4. Search Engine

Each search runtime loads its domain search index, normalizes the loaded values into runtime-friendly fields, evaluates query matches, assigns score tiers, sorts matches, and returns an ordered result set.
The dedicated `/search/` route can also expose opt-in local performance instrumentation for payload load, normalization, query, and render timings without changing search semantics.

### 5. Search UI

Catalogue search uses its dedicated public route.
Docs search lives inline in Docs Viewer by replacing the right content pane with results when `q` is present in the docs URL.

Any top-level `/search/` route, if kept, should be a chooser or dispatcher between domain searches rather than a merged-result product.

## Design principles

The current implementation follows these principles.

### Lightweight

The base search experience should remain fast without external infrastructure and without loading prose-heavy payloads by default.

### Structured

Catalogue search and Docs search should each have artifacts and documentation that match their domain, rather than piggybacking on a generic global site-search abstraction.

### Reviewable

Search behaviour should be understandable from focused documents covering schema, ranking, normalization, UI behaviour, and build flow.

### Incremental

The base artifact stays compact and structured rather than trying to index prose-heavy payloads by default.

### Static-site compatible

Search remains part of the existing static build pipeline and browser runtime. It does not depend on a dynamic backend.

## Out of scope for this document

This document does not define:

- the full catalogue search index field schema
- normalization rules or token-preparation logic
- ranking tiers or scoring details
- UI event timing and pagination details
- validation procedure

Those belong in the dedicated companion documents.

## Related documents

- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)
- [Config](/docs/?scope=studio&doc=config)
- [Data Models](/docs/?scope=studio&doc=data-models)
- [Search Change Log Guidance](/docs/?scope=studio&doc=search-change-log-guidance)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)

## Current status

Current implementation status:

- public Catalogue search is implemented as a page at `/search/?scope=catalogue`
- the current dedicated public route is `/search/?scope=catalogue`
- the dedicated `/search/` runtime and policy are now trimmed to catalogue-only behavior
- the current catalogue search index is generated at build time into `assets/data/search/catalogue/index.json`
- a single transitional builder emits `assets/data/search/catalogue/index.json`, `assets/data/search/studio/index.json`, `assets/data/search/analysis/index.json`, and `assets/data/search/library/index.json`
- the search builder validates source-family config before writing or skipping output
- docs-domain targeted updates are available for `studio`, `analysis`, and `library` by `doc_id`
- `catalogue` remains full-rebuild-only under the current source-family policy
- indexed content types are works, series, moments, Studio docs, Analysis docs, and Library docs
- ranking is field-aware and deterministic rather than flat
- the UI currently searches all indexed catalogue kinds together and does not expose per-kind filter buttons
- Studio docs search is inline on `/docs/`
- Library docs search is inline on `/library/`
- Analysis docs search is inline on `/analysis/`
- results are rendered client-side in ranked order, with additional batches revealed via `more`
