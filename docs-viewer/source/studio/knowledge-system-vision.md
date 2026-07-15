---
doc_id: knowledge-system-vision
title: Knowledge System Vision
added_date: 2026-07-11
last_updated: 2026-07-12
parent_id: architecture
viewable: true
---
# Knowledge System Vision

## Purpose

Studio, Analytics, Docs Viewer, Data Sharing, and the public Analysis scope are parts of one evolving experiment in knowledge creation and management.

The ambition is not only to publish documents or manage a catalogue. It is to create a system in which structured data, human interpretation, AI-assisted development, media, and relationships can be assembled into accessible knowledge collections and repeatedly developed over time.

This document owns that cross-system product vision. Roadmap features and architecture documents should link here rather than restating the conceptual model inside technical delivery plans.

## End State

The `/analysis/` scope is the clearest expression of the intended end state.

An Analysis document may be:

- partly written by a person
- partly generated or revised by AI
- partly constructed from structured catalogue data
- connected to works, series, moments, tags, and other entities through semantic tokens
- illustrated with authored, catalogue-derived, or AI-generated media
- reorganized and developed through repeated external editing cycles

The rendered result should read as one coherent document even though its source combines several kinds of knowledge and authorship.

## Meaning Of Canonical

`Canonical` means the currently accepted source state used by the system. It does not mean original, exclusively human-authored, permanently final, or intrinsically more truthful.

A Library or Analysis document may begin as a ChatGPT output, be edited by a person, gain catalogue-derived semantic content, return to ChatGPT for further development, and later be accepted as a new canonical version.

Canonical status is therefore an operational authority boundary:

- it identifies the source currently used to build, render, search, and publish
- it provides a stable base for provenance and later comparison
- it changes only through an explicit accepted workflow
- it does not erase how the content was produced

## Hybrid Documents

The target document model combines:

### Authored narrative

Human- or AI-written Markdown provides interpretation, argument, description, and connective structure.

### Structured semantic content

Typed semantic tokens reference canonical catalogue or registry entities instead of copying their data into prose wherever a live relationship is more appropriate.

Tokens may project current titles, links, media, labels, metadata, reports, or other controlled representations. They should remain inspectable in source and validated against named registries or domain owners.

### Media And interactive content

Images, documents, diagrams, and sandboxed interactive assets are part of the knowledge object rather than incidental presentation. A complete exchange workflow must preserve or intentionally replace them alongside Markdown.

### Hierarchy And relationships

Document identity, parent-child organization, summaries, tags, semantic references, and links provide navigable structure across a collection.

## System Roles

### Studio

Studio manages editorial and catalogue source workflows. It provides controlled ways to create and maintain the structured source data from which public catalogue surfaces and semantic document projections are built.

### Analytics

Analytics develops relationships across the catalogue through tags, registries, dimensions, reports, and analysis workflows. It hosts Data Sharing because exchange, enrichment, and returned-data validation are analytical/domain workflows rather than presentation concerns.

### Docs Viewer

Docs Viewer makes knowledge collections accessible. It owns document navigation, hierarchy, rendering, search, source inspection/editing, and scope-aware presentation across local and public contexts.

It is both a reading surface and a way to gather otherwise scattered outputs into coherent collections that people and AI can inspect again.

### Data Sharing

Data Sharing makes selected knowledge portable. It owns packages, manifests, provenance, external task context, returned-package validation, and the trusted handoff to review and import consumers.

### Analysis Scope

The public `/analysis/` scope is the synthesis surface. It aims to combine authored interpretation, AI-assisted development, catalogue-derived semantic projections, media, and cross-document relationships in one readable body of work.

## Knowledge Development Loop

```text
catalogue and registry data
  + human writing
  + AI-generated or AI-revised material
  + media and interactive assets
  -> hybrid source documents
  -> Docs Viewer collections
  -> browsing, linking, hierarchy, summaries, and search
  -> complete Data Sharing package
  -> external AI analysis and editing
  -> returned-package validation
  -> persistent read-only Docs Review projection
  -> staged package enters Docs Viewer collection import
  -> selected records are created, overwritten, or skipped by the user
  -> accepted documents join or update a configured collection
```

This is a loop, not a one-time publication pipeline.

## Design Principles

- Treat human and AI authorship as provenance, not as competing source classes.
- Keep canonical source inspectable, portable, and separate from generated presentation artifacts.
- Preserve stable document and catalogue identities across revisions.
- Prefer typed semantic references to duplicated catalogue facts when live projection is intended.
- Keep generated content traceable to its source data and projection rules.
- Preserve source Markdown, media, links, and embedded assets in complete exports; keep accepted text-only returns explicit about any source-only constructs they omit.
- Treat returned AI work as untrusted until it has been validated and accepted.
- Keep preview/review authority separate from canonical mutation authority.
- Make summaries, hierarchy, and relationships first-class knowledge rather than navigation afterthoughts.
- Allow the system to improve incrementally without requiring every document to use every capability.

## Current Direction

The complete vision is not implemented yet. Current and planned work moves toward it through:

- clearer documentation scopes and user/architecture guidance
- Docs Viewer app-context, provider, route-feature, and view/mode/control refactors
- source-aware semantic token expansion
- full source-and-asset Data Sharing export packages
- isolated returned-package preview in Docs Review
- schema-aware Docs Viewer collection import from immutable staged JSONL
- summary-aware and later broader content-aware search

Each project should remain independently reviewable. The vision explains why the projects connect; it does not justify mixing their implementation responsibilities.

## Related Documents

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Data Sharing](/docs/?scope=studio&doc=data-sharing)
- [Data Sharing Full Document Export Package](/docs/?scope=studio&doc=data-sharing-full-document-package-delivery)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references)
