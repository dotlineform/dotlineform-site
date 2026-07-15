---
doc_id: analytics-llm-integration-concept
title: LLM Integration Concept
added_date: 2026-04-16
last_updated: 2026-07-15
ui_status: paused
parent_id: analytics-llm-integration
viewable: true
---
# LLM Integration Concept

## Aim

Use a model where rules and exact matching are weak, while keeping it advisory and reviewable.

Possible applications include:

- propose tags for works or series;
- recommend or challenge portfolio dimensions;
- draft Library summaries;
- report possible Library structure improvements;
- surface registry overlap, ambiguity, or strain.

The model may propose, explain, compare, or draft. It must not become a canonical scorer or write accepted source data directly.

## Product Boundary

- A person reviews, edits, accepts, or rejects proposals.
- Canonical source and identifiers remain owned by their current domains.
- Accepted changes use existing domain writers and validation.
- Search and builders consume accepted source, never raw model responses.
- Each workflow chooses its own source, privacy, review, and apply boundary.

## Questions

- Which single workflow is valuable enough to prove first?
- What source material may leave the local environment, and through which provider?
- Is the useful unit one record, a batch, or both?
- What should persist: proposal, accepted result, provider trace, or only normal logs?
- What blocks malformed, invented, or stale ids?
- How are large proposed changes made reviewable through normal source control?
- What cost, availability, and provider-change risk is acceptable?

## Risks

- Plausible language can hide invented or incorrect structure.
- Batch suggestions can create large low-confidence diffs.
- Domains may need incompatible context and review methods.
- A general helper can become an abstraction without a real workflow.
- Provider behavior, data handling, and cost can change independently of this repository.
