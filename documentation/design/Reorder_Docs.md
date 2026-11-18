---
draft: false
doc_id: d-20260903-195713-4c8f2a
title: Reorder docs
added_date: "2026-09-03 19:57:13"
last_updated: "2026-10-14 21:49:12"
summary: Design rationale for storing ordinary Index hierarchy and order together and editing them through one Position dialog.
ui_status: done
parent_id: d-20260903-220300-694ee5
---
# Reorder docs

The ordinary Index needs an editorial sequence that survives document renames and body edits. Its nested `index-order.json` puts parentage and order in one editable structure. Nesting supplies the parent and array order supplies sibling placement. Duplicating parentage in front matter or introducing numeric positions would make a subtree move depend on coordinated updates across documents.

**Position** uses one searchable destination picker with Before, After and Inside. The same operation handles reordering and reparenting, and the whole subtree travels with its internal order. The dialog was chosen over drag-only placement so an author can find an exact destination in a large tree. Keeping placement separate from readiness lets authors arrange drafts and excluded branches before publication.

An ordinary collection host can move in the Index while its flat member list keeps its own owner. This separation lets the ordinary tree describe placement without also becoming the order for every named collection. The proposed ordinary previous/next traversal can use the same authored tree. [Context Navigation](../studio/Document_Context_Navigation.md)

Current operator and storage details live in [Source Organisation](../reference/Source_Organisation.md#position-ordinary-documents). The [completed delivery](../deliveries/Reorder_Docs_Delivery.md) records the cutover and acceptance.
