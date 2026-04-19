---
doc_id: new-pipeline-refine-analytics
title: Analytics Plan
last_updated: 2026-04-18
parent_id: new-pipeline
sort_order: 61
---

# Analytics Plan

This is a planning stub for the Analytics domain so tagging and future analytical tooling can be planned in parallel with Catalogue-led Studio work.

This document should be developed in parallel with **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**.

## Purpose

- define the future Studio Analytics domain
- clarify how current tagging tools relate to broader analytical workflows
- identify the first dashboards, reports, or maintenance tools that should live under Analytics

## Current Boundary

- existing tag-oriented Studio pages remain live and useful
- Analytics should not absorb Catalogue, Library, or Search concerns unless a workflow is genuinely cross-domain
- shared shell, nav, and common Studio patterns belong to the Studio implementation plan

## Candidate Phases

### Phase 1. Analytics Domain Definition

- define what belongs in `Analytics` versus current tag maintenance pages
- identify the first operator questions Analytics should answer

### Phase 2. Analytics Dashboard

- define the first dashboard or index page linked from `/studio/`
- identify the most useful summaries, counts, or maintenance queues

### Phase 3. Workflow Surfaces

- identify which analytics tasks need read-only dashboards versus editor/action flows
- identify any shared dependencies on search, tag, or catalogue data

## Dependencies

- shared Studio navigation from **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)**
- existing tag tooling and any shared activity/reporting conventions

## Open Questions

- what should the first Analytics dashboard show
- which current tag workflows should remain where they are versus moving under a wider Analytics domain
- which analytics tasks are primarily observational and which require action surfaces
