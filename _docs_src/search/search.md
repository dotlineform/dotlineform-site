---
doc_id: search
title: Search
last_updated: 2026-03-30
parent_id: ""
sort_order: 30
---

# Search

This section describes the search planning and implementation.

[Search](/search/?scope=catalogue){:target="_blank"} is currently available on the public site for the `catalogue` scope.

## Documents

- [Overview](/docs/?scope=studio&doc=search-overview) - a concise overview of the site search subsystem.
- [Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract) - defines the public `/search/` route, `scope`/`q` URL contract, and scope-led entry-point model.
- [Index Schema](/docs/?scope=studio&doc=search-index-schema) - describes the current catalogue search index shape.
- [Field Registry](/docs/?scope=studio&doc=search-field-registry) - separates “field exists in schema” from “field participates in search and how.”
- [Ranking Model](/docs/?scope=studio&doc=search-ranking-model) - explain current relevance behaviour separately from schema and field policy.
- [UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour) - separates browser behaviour from ranking and indexing
- [Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) - explains how source content becomes the generated index.
- [Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules) - describes token preparation, deduplication, hyphen/space handling, and similar preprocessing rules.
- [Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist) - should be short and operational rather than explanatory
- [Config Architecture](/docs/?scope=studio&doc=search-config-architecture) - this file explains the architecture choice; the registry and ranking docs should define the actual rules.
- [Config Implementation Note](/docs/?scope=studio&doc=search-config-implementation-note) - sketches the concrete first config extraction and the later phases after that.
- [Pipeline Target Architecture](/docs/?scope=studio&doc=search-pipeline-target-architecture) - sketches the long-term ownership boundary where search owns its own pipeline and consumes canonical outputs from other systems.
- [Studio V1 Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape) - defines the proposed `scope=studio` record shape and explains how Studio v1 fits the wider plan.
- [Change Log Guidance](/docs/?scope=studio&doc=search-change-log-guidance)
- [Change Log](/docs/?scope=studio&doc=search-change-log)
