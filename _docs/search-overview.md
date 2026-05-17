---
doc_id: search-overview
title: Search Overview
added_date: 2026-03-31
last_updated: "2026-05-11 21:30"
parent_id: search
sort_order: 1000
---
# Search Overview

## Purpose

This document defines the current search direction.
It separates search by data domain rather than treating search as one global site product.

The detailed schema, ranking, normalization, UI, and build-flow notes remain in the focused search child docs.

## Core Decision

There is no meaningful generic global site search target for this project.
The useful searchable domains are:

- **Catalogue search** for structured artwork/catalogue records
- **Docs search** for document corpora served by Docs Viewer

These domains have different source models, ranking goals, UI objectives, and maintenance boundaries.
They should not share one product policy.

`/analysis/` may discuss catalogue subject matter, but architecturally it is still a document corpus.
It belongs to Docs search.

## Search Ownership

### Catalogue Search

Catalogue search owns structured catalogue lookup.

It should optimize for:

- work, series, moment, and tag lookup
- catalogue identifiers
- artwork titles and relationships
- catalogue metadata and status fields
- navigation from results into catalogue pages

Current route:

- `/catalogue/search/`

Current generated artifact:

- `assets/data/search/catalogue/index.json`

### Docs Search

Docs search belongs to Docs Viewer.

It should optimize for:

- title, summary, headings, and document text
- document hierarchy and parent titles
- `hidden` / `viewable` filtering
- recently-added ordering
- opening results inside the active Docs Viewer route

Current routes:

- `/docs/`
- `/library/`
- `/analysis/`

Current generated artifacts:

- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`
- `assets/data/search/analysis/index.json`

Current ownership:

- Docs Viewer owns docs search build configuration
- Docs Viewer owns docs search runtime policy
- Docs Viewer owns docs search output shape
- portable Docs Viewer installs do not need the Catalogue/public search product

## Top-Level Search Route

The top-level `/search/` route has been retired as a global search surface.
It should not return as an aggregate, merged-result, or docs-scope search route.

Catalogue search now uses the Catalogue-owned `/catalogue/search/` route.
Docs search should stay inside Docs Viewer routes.

## Current Implementation

The implementation now uses one stable command wrapper that dispatches to domain-owned builders.

Current files:

- Catalogue browser runtime: `assets/js/catalogue-search.js`
- Catalogue runtime policy: `assets/data/search/policy.json`
- Docs browser runtime: `assets/docs-viewer/js/docs-viewer.js`
- Docs search helpers: `assets/docs-viewer/js/docs-viewer-search.js`
- Search build entrypoint and dispatcher: `scripts/build_search.rb`
- Search adapter registry: `scripts/search/adapter_registry.json`
- Catalogue search build implementation: `scripts/search/build_search.rb`
- Catalogue search build config: `scripts/search/build_config.json`
- Docs Viewer search build implementation: `scripts/docs/build_search.rb`
- Docs Viewer search scope config: `scripts/docs/docs_scopes.json`

Current live surfaces:

- Catalogue search on `/catalogue/search/`
- Studio docs search inline on `/docs/`
- Library docs search inline on `/library/`
- Analysis docs search inline on `/analysis/`

Current build behavior:

- `catalogue` search reads canonical generated catalogue JSON
- configured docs scopes such as `studio`, `library`, and `analysis` search read generated Docs Viewer indexes
- docs search skips rows where `viewable: false`
- docs search supports targeted updates by `doc_id`
- catalogue search remains full-rebuild-only for existing-record changes

## Extraction Direction

The next cleanup should package the route adapter pattern and continue removing dotlineform-specific assumptions from Docs Viewer management and import flows.
3. Move docs-search policy into Docs Viewer config/runtime.
4. Keep Catalogue search build/runtime policy separate.
5. Share only low-level helpers that are genuinely domain-neutral.

The broader ordered plan is tracked in [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer).

## Design Principles

### Domain First

Search follows the source data domain.
Catalogue records and document corpora should not be forced into one global ranking model.

### Static Compatible

Search remains compatible with static-site builds.
Generated artifacts are read by browser runtimes without a hosted search service.

### Portable Docs

Docs search is part of Docs Viewer portability.
A downstream Jekyll repo should be able to install Docs Viewer with inline docs search without copying Catalogue search.

### Reviewable Policy

Ranking and field participation should be understandable from focused docs.
As docs search moves under Docs Viewer, its policy should be documented there or in a Docs Viewer child doc.

## Related Documents

- [Search](/docs/?scope=studio&doc=search)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)
