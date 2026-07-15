---
doc_id: site-request-llm-semantic-enrichment
title: LLM Semantic Enrichment
added_date: 2026-04-16
last_updated: 2026-07-15
ui_status: paused
parent_id: change-requests
viewable: true
---
# LLM Semantic Enrichment

This is a paused feature concept. It is not current architecture, an implementation contract, or a dependency for active work.

The earlier notes explored several useful applications of LLM assistance, then accumulated detailed envelopes, schemas, phases, and UI behaviour before any one deliverable had been chosen. They have been consolidated here so that speculative detail does not look implemented.

## Long-Term Aim

Use a model as an advisory semantic tool where rules and exact matching are weak:

- propose tags for works or series
- recommend or challenge portfolio dimensions
- draft Library summaries
- report possible Library structure improvements
- surface registry overlap, ambiguity, or strain

The model should propose, explain, compare, or draft. It must not become a canonical scorer or write accepted source data directly.

## Stable Boundary

If this work resumes, every delivery should follow the same high-level boundary:

1. The owning domain selects and exports explicit source context.
2. A task sends structured input and requests structured output.
3. The response is treated as untrusted proposal data and validated against a task-owned schema.
4. A person reviews, edits, accepts, or rejects the proposals.
5. Accepted changes pass through the domain's existing writer and validation rules.
6. Existing builders regenerate any derived output.

Canonical ownership does not move into a model helper:

- tag registry and assignments remain Analytics data
- catalogue and dimension data remain Catalogue/Analytics source data
- document content, summaries, and hierarchy remain document source
- search consumes accepted metadata, not raw model responses

## Architecture Direction

A reusable invocation layer may eventually own provider transport, structured-response parsing, timeouts, and common diagnostics. It should be extracted from the first concrete workflow, not designed in advance as a general semantic platform.

Each task still needs its own:

- source selection and privacy boundary
- input and output schema
- review surface
- validation and apply rules
- audit/trace decision
- generated-output impact

Shared transport does not imply shared UI, persistence, or governance.

## Candidate Deliveries

These are separate possible deliveries, not phases of one request:

- **Library summaries:** select documents, produce summary proposals, validate them, review a diff, and apply accepted front matter. This is additive and probably the smallest proving case.
- **Tagging assistance:** propose existing tags with reasons from catalogue and registry context, then apply accepted assignments through current tag writers.
- **Dimension recommendation:** advise on dimensions and model strain. This should wait until dimensions have a real implemented source model.
- **Library structure review:** produce a report of possible parent or grouping changes. Keep it report-only until document moves have a deliberately reviewed workflow.

When one becomes important, create a bounded delivery request with one user-visible outcome. Do not reactivate this whole feature as a single implementation task.

## Decisions Required Before Delivery

- Which single workflow is valuable enough to prove first?
- What source material may leave the local environment, and through which provider?
- Is the run single-record, batch, or both?
- What is stored: proposal, accepted result, provider trace, or nothing beyond logs?
- What validation blocks malformed, invented, or stale ids?
- How are large batch changes made reviewable and reversible through normal source control?
- What model/provider cost, availability, and change risk is acceptable?

## Known Risks

- Plausible language can hide incorrect or invented structure.
- A generic helper can become abstraction without a real workflow.
- Batch suggestions can create large, low-confidence diffs.
- Different domains may need incompatible context and review methods.
- Provider behaviour, data handling, and cost can change independently of this codebase.

## Resume Condition

Ignore this feature until a concrete semantic task becomes an active priority. At that point, inspect current domain writers and data contracts, choose one finishable delivery, and create its concept/architecture detail only to the depth needed for that delivery.
