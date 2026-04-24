---
doc_id: library
title: "Library"
added_date: 2026-04-18
last_updated: 2026-04-24
parent_id: ""
sort_order: 165
---

# Library

This is a planning stub for the Library domain so Studio can develop as a multi-domain tool rather than waiting for Catalogue to be fully complete first.

This document should be developed in parallel with **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**.

## Purpose

- define the Studio administration boundary for `/library/`
- identify the highest-value Library workflows that need Studio surfaces
- keep Library planning separate from Catalogue unless the work changes shared Studio shell, navigation, or infrastructure

## Current Boundary

- Library is a distinct domain from Catalogue
- this plan currently captures direction only, not committed implementation detail
- shared Studio shell and navigation decisions should come from the Studio implementation plan, not be duplicated here

## Candidate Phases

### Phase 1. Library Workflow Definition

- define the main maintenance tasks the Studio Library domain should support
- identify current manual or file-based workflows that need clearer operational support
- confirm the source-of-truth boundary and generated-runtime boundary
- define semantic enrichment workflows for summaries and structure review; see [Library Semantic Enrichment Spec](/docs/?scope=studio&doc=library-semantic-enrichment-spec)

### Phase 2. Library Entry Surfaces

- define the landing/dashboard entry point from `/studio/`
- identify the first search, status, or editor surfaces needed

### Phase 3. Library Actions And Validation

- identify which workflows need source writes, preview/apply patterns, validation, and activity reporting

## Dependencies

- shared Studio navigation from **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**
- any shared write-service or activity conventions used across Studio domains

## Open Questions

- what are the first Library workflows worth moving into Studio
- what data and content boundaries are canonical for Library administration
- which Library tasks need only visibility/status versus true edit flows
