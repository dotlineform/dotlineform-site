---
doc_id: search
title: Search
added_date: 2026-03-31
last_updated: 2026-05-11
parent_id: ""
---
# Search

This section describes the current search implementation and the direction toward separate domain search products.

Current live search surfaces:

- Catalogue search on `/catalogue/search/`
- Studio docs search inline on `/docs/`
- Library docs search inline on `/library/`
- Analysis docs search inline on `/analysis/`

Architecture direction:

- Catalogue search and Docs search are separate data-domain products.
- Docs Viewer owns document-domain search for `/docs/`, `/library/`, and `/analysis/`.
- Catalogue search owns structured artwork/catalogue lookup.
- The retired top-level `/search/` route should not return as a generic merged-result search product.
- The retired `/studio/search/` dashboard should not return as a standalone Studio search domain. Catalogue search administration belongs under `/studio/catalogue/`; document search administration belongs in Docs Viewer manage mode.

## Current Implementation

- [Overview](/docs/?scope=studio&doc=search-overview) - a concise overview of the site search subsystem.
- [Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract) - defines the Catalogue-owned `/catalogue/search/` route and entry-point model.
- [Index Schema](/docs/?scope=studio&doc=search-index-schema) - describes the current catalogue search index shape.
- [Field Registry](/docs/?scope=studio&doc=search-field-registry) - separates “field exists in schema” from “field participates in search and how.”
- [Ranking Model](/docs/?scope=studio&doc=search-ranking-model) - explain current relevance behaviour separately from schema and field policy.
- [UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour) - separates browser behaviour from ranking and indexing
- [Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) - explains how source content becomes the generated index.
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape) - describes the current search artifact shape for the Studio and Library docs scopes.
- [Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules) - describes token preparation, deduplication, hyphen/space handling, and similar preprocessing rules.
- [Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist) - operational checks for catalogue and docs-domain search surfaces.
- [Incremental Search Orchestration Plan](/docs/?scope=studio&doc=search-incremental-orchestration-plan) - separates server/watch orchestration from search-owned record generation for future incremental updates.
- [Catalogue Targeted Search Plan](/docs/?scope=studio&doc=search-catalogue-targeted-plan) - additive-only catalogue targeted search boundary and remaining follow-on work.

## Maintenance

- [Change Log Guidance](/docs/?scope=studio&doc=search-change-log-guidance)
- [Change Log](/docs/?scope=studio&doc=search-change-log)
