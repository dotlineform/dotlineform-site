---
draft: false
doc_id: d-20261118-192400-8e42d6
title: Document Grammar And Review Delivery
added_date: "2026-11-18 19:24:00"
last_updated: "2026-11-18"
summary: Preserved identity migration, conversion and audit evidence, Review corrections and proposal dispositions.
parent_id: d-20261118-151521-a0f9c3
---
# Document grammar and Review delivery

The 2026-11-18 review consolidated fourteen Studio pages into five Reference owners and three Working proposals. Six overlapping entry points or inventories were retired after checking their references and parent identities. The original records remain in Git at `c76f6608ef` under `documentation/studio/`. [Current grammar](../reference/Document_Identity.md) · [Design rationale](../design/Document_Grammar_And_Exchange.md)

## Identity migration

The repository ID/date migration preserved explicit times, used Git addition time when a date-only value agreed with the Git date, and otherwise used midnight. Deliberately authored historical dates stayed in place. External Notes used midnight for date-only metadata because repository history did not establish its source creation time.

The later Recent seed followed renames and selected the latest Git author time at which body, Title or Summary changed. It updated the bounded union needed by edited projections, with actual write times for dirty qualifying edits. These were migration decisions. Current managed operations own dates at their write boundary. The existing Source Save timestamp discrepancy remains logged. [Current date behavior](../reference/Document_Identity.md#date-provenance)

## Conversion and diagrams

The Word adapter's fixed map reserves H1 for Title and reports Heading 6 clamping. The shared HTML converter preserves semantic content with deliberate degradation. Finished SVG import replaced application-owned diagram source/building, while repository Markdown retains external-viewer rendering. The approved diagram cleanup scope and evidence remain with Testing. [Mapping](../reference/HTML_Import_Mapping.md) · [Diagram cleanup](../_working/testing/Testing.md#diagram-pipeline-cleanup)

## Review corrections

Older Review pages described v1/v2 manifests with scope/stage provenance, canonical links containing a stage parameter and a guarantee that failed rebuilding preserved the previous preview. The current service requires v4 provenance, exact selected membership and collection identity. Explicit Build writes package-generated output in place, while initial materialization exposes a completed temporary package by rename. The reference now describes those separate failure boundaries. [Current Review](../reference/Docs_Review.md)

The original reference listed package, materialization, edited-source and smoke files as coverage. Current retained Python fixtures still use v1 manifests or scope/stage requests. Those files require separately scoped review before they establish current behavior. Review's authority boundary and the missing named-collection canonical shortcut are recorded in the tracker. [Code and test follow-ups](../_working/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups)

## Broken Links evidence

The 2026-10-14 cleanup had focused lint, compilation and source review. Its read-only audit found eleven missing Context attachments across six documents with no unavailable generated sources. Saved Refresh persistence, failure branches and browser row/sort/cursor behavior remained unverified. The current source trace shows Work-token diagnosis using adopted Catalogue document data, superseding the older reference's direct consumer-record description. [Current audit](../reference/Broken_Links.md)

## Pending proposals and verification limits

Metadata separation, independent seeding and directed link strength initially moved to Working with their original IDs and titles. Metadata separation and independent seeding were subsequently retired as recorded below. Directed link strength remains a separate proposal. The navigation umbrella was retired into the completed order references; the separate Context Navigation proposal was later [retired at the user's request](Document_View_And_Return_Navigation_Handoff.md#ordinary-index-traversal-proposal-retired).

This batch inspected parser, renderer, link, conversion, package and Review source and checked Markdown links, identities and whitespace. Live parsing/builds, package writes, canonical Import, browser interaction and runtime tests were outside this documentation review.

## Independent Seeding Proposal Retired

The user requested retirement of Independent Canonical Documents. It proposed creating an independently editable Docs document once from selected structured-record fields, with each side retaining its own edit/deletion lifecycle and no ongoing synchronization. It was retired without implementation or a follow-on. Current [Catalogue adoption](../reference/Generated_Data_Contracts.md#catalogue-reference-and-presentation) and [Book copying](../reference/Collections_And_Books.md#book-curation-in-manage) retain their own explicit contracts; this proposal adds no generic Copy/Replace or lineage workflow. References and document-ID/parent dependencies were checked before removing the Working page.

## Metadata Separation Proposal Retired

On 18 November 2026 the user agreed to retire Separate Document Content And Metadata. Keeping front matter and body together preserves a portable source file; ordinary organisation is already separate, and no measured benefit justified the wider storage migration and coordinated mutation/exchange work. The [design rationale](../design/Document_Grammar_And_Exchange.md#self-contained-source) retains that decision. Current [source ownership](../reference/Source_Organisation.md) and [Build/relationship maintenance](../reference/Builder.md) keep their existing contracts. The proposal was retired without implementation or a follow-on, after checking references and document-ID/parent dependencies.
