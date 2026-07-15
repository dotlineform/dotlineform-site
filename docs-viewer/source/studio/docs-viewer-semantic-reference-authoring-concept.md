---
doc_id: docs-viewer-semantic-reference-authoring-concept
title: Semantic Reference Authoring Concept
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: proposed
summary: Product concept for optional semantic-reference authoring improvements beyond the current picker.
parent_id: docs-viewer-semantic-reference-authoring
viewable: true
---
# Semantic Reference Authoring Concept

## Current Baseline

The manage-mode Markdown editor can insert a semantic reference from selected text or the caret. It uses registry-declared kinds and generated browser-safe targets, inserts into the local source buffer, and leaves the actual source write to `Rebuild doc`.

Missing or stale targets remain report concerns rather than build or write failures.

## Possible Improvements

- seed picker search from the word or id around a collapsed cursor
- let an author enter a known target id directly
- support exact lookup for kinds whose target sets are large or title-ambiguous
- add one new registry-backed token kind when its route and target data are settled
- allow deliberate label editing without losing the canonical target
- audit malformed or suspicious token-like text more clearly

These are separate opportunities, not one v2 deliverable.

## Product Boundaries

- Source editing remains owned by the Markdown editor.
- Insertion remains local until the normal rebuild workflow.
- The registry owns supported kinds and route behavior.
- Browser assistance should use generated safe data where practical.
- Public routes do not load picker UI or editor CSS.
- The builder remains parse/render authority.
- Reports own stale-target and suspicious-token audits.

High-cardinality tags depend on a settled embedded-detail route. Returned text exchange remains owned by [Shareable Content Blocks](/docs/?scope=studio&doc=analytics-shareable-content-blocks).

Semantic directives such as inserting fields or related lists are larger than editor assistance. They change registry, resolver, builder, provenance, and rendering behavior and should become a separate feature concept if promoted.

## Delivery

Small finishable candidates live on the [Docs Viewer Roadmap](/docs/?scope=studio&doc=docs-viewer-roadmap). None is currently scheduled or has a delivery.

Each future delivery should complete one authoring improvement without using “v2” as permission to absorb the rest of this list.

## Questions To Resolve When Relevant

- Can cursor seeding avoid surprising replacement of nearby Markdown or punctuation?
- Can direct id entry reuse current generated target records before exact-record machinery is justified?
- What target count or ambiguity demonstrates a real need for lazy exact lookup?
- Are custom labels common enough to justify editor UI rather than report guidance?

Resolve each question only when its outcome is being considered for promotion.
