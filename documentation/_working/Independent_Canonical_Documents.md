---
draft: false
doc_id: d-20260728-113139-95a885
title: Independent Canonical Documents
added_date: "2026-07-28 11:31:39"
last_updated: "2026-11-18"
summary: explain how Docs Viewer source can be seeded from another canonical system and then remain independently canonical without synchronization
ui_status: proposed
parent_id: d-20260424-000000-50b63f

---

# Independent Canonical Documents

This proposal describes a future one-time seeding workflow. Studio can remain canonical for a structured record while Docs Viewer owns a separately editable document initially created from selected record fields. Current Catalogue documents follow the explicit Regenerate adoption workflow. Book copies have their own Library provenance and curation owner. [Catalogue adoption](../reference/Generated_Data_Contracts.md#catalogue-reference-and-presentation) · [Book copy](../reference/Collections_And_Books.md#book-curation-in-manage)

## Ownership

Canonical ownership is contextual. Studio JSON owns its record, and Docs Viewer source owns its document. Generated payloads, discovery and reports are projections of their respective inputs. An initial cross-application reference records an association. Its owner defines how to inspect or repair a stale target.

## One-Time Seed

A producing workflow could allocate a stable document identity, create source from selected fields, validate the initial association and build the resulting document. After that deliberate Copy, each side has its own edit and deletion lifecycle. Exact identities carry the association, and titles or content cannot infer a replacement.

The earlier SSP-7 lineage concept treated Replace as another explicit Copy over the exact recorded destination. The current workspace has no configured lineage workflow, and its inactive historical tables were retired. Any future seed or Replace delivery must choose its owner and complete outcome before implementation. [Retired lineage boundary](../reference/Configuration_And_Extension_Points.md#workspace-and-target-contracts)

## References And Validation

Docs Viewer owns source grammar, exact collection/document identity, supported reference syntax and confined operation paths. A cross-application reference can become stale while the document remains editable and otherwise publishable. Selection can validate a target at insertion, while explicit Broken Links diagnoses later unresolved references. [Reference owners](../reference/Document_And_Catalogue_References.md) · [Broken Links](../reference/Broken_Links.md)

The former tag-document relationship illustrated a one-way reference from a tag to a document. That tag system was retired. Its old URL and storage model are historical context for this proposal. [Tag retirement](../deliveries/Retire_Studio_Tags.md)

## Consequences For A Future Delivery

The collection should list and manage every document it owns, including drafts, duplicate titles and documents with no external association. Title, publication readiness and presentation metadata remain document-owned. Exact document editing/deletion, explicit stale-reference diagnosis and public projection need their own defined behavior.

Every ongoing mutation must have one authoritative owner. Generated output remains derived even when the original source was seeded. A proposed delivery should decide the exact Copy transformation, association/provenance fields, replacement intent, failure completion and recovery. Initial validation establishes the selected operation's validity. Later synchronization, cascading deletion and automatic repair would each need an explicit product decision.

The generic collection and Book references describe the current navigation and copy behavior. This document retains the independent-ownership proposal for an explicitly chosen future adopter. [Collections and Books](../reference/Collections_And_Books.md)
