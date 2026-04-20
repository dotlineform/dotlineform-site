---
doc_id: new-pipeline-refine-search
title: "Search Plan"
last_updated: 2026-04-18
parent_id: new-pipeline
sort_order: 62
---

# Search Plan

This is a planning stub for the Search domain so search configuration, validation, and operational tooling can be developed in parallel with the wider Studio roadmap.

This document should be developed in parallel with **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**.

## Purpose

- define the Studio Search domain
- identify the first search-focused maintenance and reporting workflows that need dedicated Studio surfaces
- keep search planning separate from Catalogue unless a workflow directly crosses the domain boundary

## Current Boundary

- Search already has its own documentation set and implementation boundaries
- this stub is for Studio planning and operational surfaces, not for rewriting the whole search architecture
- shared shell, nav, and common Studio patterns belong to the Studio implementation plan

## Candidate Phases

### Phase 1. Search Workflow Definition

- define the main search administration and validation tasks that belong in Studio
- identify what should be visible from the Search dashboard first

### Phase 2. Search Dashboard And Status

- define the first Search landing/dashboard entry from `/studio/`
- identify the most useful validation, pipeline, or status summaries

### Phase 3. Search Actions And Reporting

- identify which workflows need preview/apply actions, rebuild/reporting surfaces, or direct links into existing docs and tools

## Dependencies

- shared Studio navigation from **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**
- current Search docs and any shared activity/reporting conventions

## Open Questions

- what are the first Search workflows that need Studio entry points
- which search checks should surface as dashboard status versus deeper drill-down tools
- where should Search operational reporting meet or stay separate from Catalogue and Build Activity
