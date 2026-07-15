---
doc_id: docs-viewer-roadmap
title: Docs Viewer Roadmap
added_date: 2026-07-14
last_updated: 2026-07-15
ui_status: in-progress
parent_id: roadmap
---
# Docs Viewer Roadmap

## Purpose

This page says what matters next. It sits above individual features so dependencies and priority do not disappear inside long conceptual discussions.

- A concept may describe a large capability and unresolved choices.
- A roadmap row is one complete delivery with an explicit place in the sequence.
- A delivery document is added only when its row is coherent enough to build.
- A completed row leaves no half-finished feature behind. Shipped behavior moves to its durable owner.

The roadmap stays short. Design detail belongs in the concept or architecture; implementation detail belongs in the active delivery or the code.

## Current Sequence

| ID | status | delivery | depends on | delivery or owner |
| --- | --- | --- | --- | --- |
| DV-01 | done | install the Docs Viewer documentation and delivery model | — | [Docs Viewer](/docs/?scope=studio&doc=docs-viewer) and [Roadmap](/docs/?scope=studio&doc=roadmap) |
| EAC-01 | ready, not active | make scope lifecycle explicitly preserve user-owned external asset roots on delete and refuse unsafe rename | DV-01 done | [Lifecycle Delivery](/docs/?scope=studio&doc=docs-viewer-external-asset-lifecycle-delivery) |
| EAC-02 | queued | extract a confined metadata-only filesystem inventory primitive and migrate Project State without behavior change | EAC-01 | add delivery when promoted |
| EAC-03 | queued | give Processing a useful read-only metadata inventory report, without file-opening actions | EAC-02 | add delivery when promoted |
| EAC-04 | queued | add confined local open/download links to the proven Processing inventory | EAC-03 | add delivery when promoted |
| EAC-05 | queued | let eligible local scopes enable the collection through previewed New Scope and retrofit workflows | EAC-04 | add delivery when promoted |
| EAC-06 | queued | measure the I Ching collection, decide whether performance machinery is justified, and close the initial feature | EAC-05 | add delivery when promoted |

The External Asset Collections sequence comes from its [feature parent](/docs/?scope=studio&doc=docs-viewer-external-asset-collections), which separates concept, architecture, and promoted delivery documents. Only EAC-01 has a delivery document because later rows should be reconsidered against what the earlier delivery actually proves.

## Unsequenced Concepts

These feature parents have no active delivery and no implied priority:

- [Index Multiple Selection](/docs/?scope=studio&doc=docs-viewer-index-multiple-selection) — action targeting is shipped; pointer selection and group movement remain proposed.
- [Semantic Reference Authoring](/docs/?scope=studio&doc=docs-viewer-semantic-reference-authoring) — optional improvements beyond the current editor.

When one becomes important, split its first useful outcome into this roadmap and add only that delivery. Do not interpret document length or age as priority.

## Unsequenced Deliverables

These outcomes are separated but not scheduled. They have no delivery documents.

| ID | feature | complete outcome | dependency |
| --- | --- | --- | --- |
| IMS-00 | Index Multiple Selection | establish one action-target and cardinality owner without changing visible behavior | done; owned by [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) |
| IMS-01 | Index Multiple Selection | deliver visible pointer selection as complete local manage-mode behavior | IMS-00 |
| IMS-02 | Index Multiple Selection | move a selected group through one validated mutation and coordinated rebuild | IMS-01 |
| SRA-01 | Semantic Reference Authoring | seed picker search safely from the word or id around a collapsed cursor | current editor |
| SRA-02 | Semantic Reference Authoring | support direct known-id entry using current generated target data | current editor |

Add another row only when its outcome is clear enough to compare with current priorities. Additional bulk actions, token kinds, exact-target machinery, labels, and directives remain concepts until then.

## Maintaining The Roadmap

- Keep one row per independently finishable result.
- Put ordering here, not in the opening paragraph of a feature or delivery.
- Do not add speculative implementation steps merely to make a concept look planned.
- Split a row before implementation if its outcome cannot be completed coherently.
- Mark a row done only when the delivery is complete and its durable documentation owner is current.
- Remove obsolete sequencing detail once it no longer helps choose the next deliverable.
