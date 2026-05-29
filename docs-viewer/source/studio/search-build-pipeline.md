---
doc_id: search-build-pipeline
title: Search Build Pipeline
added_date: 2026-04-23
last_updated: 2026-05-19
parent_id: search
---
# Search Build Pipeline

## Purpose

This document defines how the current search artifacts are built.

It covers:

- the current domain-adapter design of the search build layer
- the stable build entrypoint that dispatches to domain-owned builders
- what each scope reads and writes
- how record construction, validation, and change detection work in practice

This is a build-time document. It does not define ranking or UI behaviour.
## Current Child References

- [Architecture](/docs/?scope=studio&doc=search-build-pipeline-architecture) covers the shared adapter registry, build config, and cross-scope conventions.
- [Catalogue Scope](/docs/?scope=studio&doc=search-build-pipeline-catalogue) covers the Catalogue writer, inputs, commands, targeted mode, record construction, and validation.
- [Studio Scope](/docs/?scope=studio&doc=search-build-pipeline-studio) covers Studio docs-search input, commands, runtime mapping, and targeted updates.
- [Library Scope](/docs/?scope=studio&doc=search-build-pipeline-library) covers Library docs-search input, viewability filtering, commands, runtime mapping, and targeted updates.
- [Analysis Scope](/docs/?scope=studio&doc=search-build-pipeline-analysis) covers Analysis docs-search input, viewability filtering, commands, runtime mapping, and targeted updates.

## Related Documents

- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Analysis Scope](/docs/?scope=studio&doc=data-models-analysis)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
