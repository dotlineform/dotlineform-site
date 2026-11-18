---
draft: false
doc_id: d-20260903-220300-694ee5
title: Doc Navigation
added_date: "2026-09-03 22:03:00"
last_updated: "2026-09-26 21:36:29"
parent_id: d-20260428-000000-f5ff18
---
# Doc Navigation

This feature combines explicit organisation of ordinary documents with navigation through their saved sequence, supporting a book-like reading experience with chapters and pages. Normal documents, previously called scope documents, include the whole ordinary hierarchy rather than roots alone.

- [Position ordinary documents](../reference/Source_Organisation.md#position-ordinary-documents) owns the current subtree workflow. [Reorder docs](../design/Reorder_Docs.md) explains why one nested order and one searchable Position dialog were chosen.
- [Reorder docs delivery](../deliveries/Reorder_Docs_Delivery.md) is done, with focused checks passed and user testing confirmed through site-preview on 2026-09-26. [Source Organisation](../reference/Source_Organisation.md) owns the maintained behaviour.
- [Context Navigation](Document_Context_Navigation.md) remains proposed separately. It will consume the resulting ordered tree for previous/next navigation without introducing another ordering owner.

The feature covers ordinary documents and collection report hosts. Catalogue has its own sequences for the displayed List selection, Gallery columns and search results. [Catalogue collection browsing](Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) · [Separate Document Content And Metadata proposal](Document_Content_And_Metadata.md)
