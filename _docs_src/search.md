---
doc_id: search
title: "Search"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: ""
sort_order: 180
---
# Search

This section describes the current search implementation.

Current live search scopes:

- `catalogue` on `/search/`
- `studio` inline on `/docs/`
- `library` inline on `/library/`

## Current Implementation

- [Overview](/docs/?scope=studio&doc=search-overview) - a concise overview of the site search subsystem.
- [Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract) - defines the public `/search/` route, `scope`/`q` URL contract, and scope-led entry-point model.
- [Index Schema](/docs/?scope=studio&doc=search-index-schema) - describes the current catalogue search index shape.
- [Field Registry](/docs/?scope=studio&doc=search-field-registry) - separates “field exists in schema” from “field participates in search and how.”
- [Ranking Model](/docs/?scope=studio&doc=search-ranking-model) - explain current relevance behaviour separately from schema and field policy.
- [UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour) - separates browser behaviour from ranking and indexing
- [Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) - explains how source content becomes the generated index.
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape) - describes the current search artifact shape for the Studio and Library docs scopes.
- [Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules) - describes token preparation, deduplication, hyphen/space handling, and similar preprocessing rules.
- [Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist) - operational checks for catalogue and docs-domain search surfaces.

## Maintenance

- [Change Log Guidance](/docs/?scope=studio&doc=search-change-log-guidance)
- [Change Log](/docs/?scope=studio&doc=search-change-log)
