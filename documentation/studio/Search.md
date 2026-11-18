---
draft: false
doc_id: d-20260331-000000-5dcf32
title: Search
added_date: "2026-03-31 00:00:00"
last_updated: "2026-11-18"
parent_id: ""
---
# Search

The active reader has Index Search on the public site at `/` and in Manage at `/docs/`. The Catalogue landing page has its own Work and Gallery search. For selecting a scope, opening a result and returning to the list, start with [Find and read things](../guide/Find_And_Read_Things.md).

- [Docs Viewer Search](Docs_Viewer_Search.md) owns the Index controls, Search scopes and result behaviour.
- [Docs Search Index](Docs_Search_Index.md) and the [Tokenizer](Docs_Search_Tokenizer.md) own the prepared postings, coverage and browser matching. Keep the prepared index small enough for on-demand browser loading and deterministic ranking.
- [Working rebuild](Builder.md#working-rebuild) owns the current Refresh Search and Recent action and generation handoff.
- [Catalogue collection browsing](Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) owns the Catalogue page’s Work and Gallery results.
- [Catalogue Archive](Catalogue_Archive.md#historical-reader-references) maps the frozen site's Search route and saved index.
