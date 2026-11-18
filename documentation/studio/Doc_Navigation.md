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

- [Reorder docs](Reorder_Docs.md) defines the agreed canonical nested `index-order.json`, removal of authored ordinary `parent_id`, and one Position modal for Before/After/Inside movement of whole subtrees. Draft and unpublishable records remain editable; Prepare Preview excludes their branches.
- [Reorder docs delivery](archive/Reorder_Docs_Delivery.md) is done, with focused checks passed and user testing confirmed through site-preview on 2026-09-26. [Source Organisation](Source_Organisation.md) owns the maintained behaviour.
- [Context Navigation](Document_Context_Navigation.md) remains proposed separately. It will consume the resulting ordered tree for previous/next navigation without introducing another ordering owner.

The feature covers ordinary documents and collection report hosts. Catalogue has its own sequences for the displayed List selection, Gallery columns and search results. [Catalogue collection browsing](Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) · [Separate Document Content And Metadata proposal](Document_Content_And_Metadata.md)
