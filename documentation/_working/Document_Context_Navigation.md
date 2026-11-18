---
draft: false
doc_id: d-20260903-160226-5c6a3e
title: Context Navigation
added_date: "2026-09-03 16:02:26"
last_updated: "2026-11-18"
summary: Proposed previous and next traversal in the authored ordinary Index tree.
parent_id: d-20261118-235100-64ad2e
---
# Ordinary Index previous and next

This proposal would add document traversal in authored ordinary Index order, including nested pages. It uses the existing tree from Reorder and Position. Expanded/collapsed branches are presentation state. A collection host can appear as a document in the sequence. Its member documents keep their own navigation order. [Index order](../reference/Source_Organisation.md#position-ordinary-documents) · [Current collection and Book navigation](../reference/Reader_Discovery_And_Return.md#collection-previous-and-next)

## Decisions to make

- Choose parent/descendant traversal and whole-tree or subtree boundaries. Decide where first/last actions stop or wrap.
- Choose the toolbar placement, accessible link labels and any path, counter or return control.
- Decide how directly opened pages derive their exact tree membership, how history records returned pages and how controls release on out-of-sequence surfaces.
- Agree deterministic coverage of exact membership, neighbours and boundaries, and manual review of labels and interaction.

Use the Working or eligible Published tree supplied to each reader. Exact document IDs identify the current position and real links carry destinations. Search, Related Links and ordinary authored links remain independent ways to open a document. [Reader discovery](../reference/Reader_Discovery_And_Return.md)

## Status

Proposed ordinary-Index traversal. The collection, Catalogue and Book behaviours already shipped have their own owners. [Reader design](../design/Reader_Discovery_And_Return.md)
