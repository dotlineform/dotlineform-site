---
doc_id: new-pipeline-refine-search
title: Search Plan
added_date: 2026-04-18
last_updated: 2026-05-11
parent_id: archive
sort_order: 20000
---
# Search Plan

Archived: current Search documentation lives under [Search](/docs/?scope=studio&doc=search).

This is an archived planning stub for the former Studio Search domain.

This document should be developed in parallel with **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**.

The `/studio/search/` dashboard has been retired.
Catalogue search configuration or review surfaces now belong under the Catalogue dashboard; Docs Viewer search metrics and configuration belong in Docs Viewer manage mode.

## Purpose

- record the retired Studio Search domain boundary
- identify the first search-focused maintenance and reporting workflows that need dedicated Studio surfaces
- keep future search work attached to its owning data domain

## Current Boundary

- Search already has its own documentation set and implementation boundaries
- `/catalogue/search/` is the public Catalogue search surface
- Catalogue search configuration or review pages should be linked from `/studio/catalogue/`
- Docs Viewer search metrics or configuration should be handled by `/docs/` manage mode
- this stub is for Studio planning and operational surfaces, not for rewriting the whole search architecture
- shared shell, nav, and common Studio patterns belong to the Studio implementation plan

## Candidate Phases

### Phase 1. Search Workflow Definition

- define the main search administration and validation tasks that belong in Studio
- assign each task to Catalogue or Docs Viewer ownership

### Phase 2. Search Dashboard And Status

- define Catalogue-owned search status entries from `/studio/catalogue/`
- identify the most useful validation, pipeline, or status summaries

### Phase 3. Search Actions And Reporting

- identify which workflows need preview/apply actions, rebuild/reporting surfaces, or direct links into existing docs and tools

## Dependencies

- shared Studio navigation from **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**
- current Search docs and any shared activity/reporting conventions

## Open Questions

- what are the first search workflows that need Studio entry points
- which search checks should surface as dashboard status versus deeper drill-down tools
- where should Search operational reporting meet or stay separate from Catalogue and Studio Activity
