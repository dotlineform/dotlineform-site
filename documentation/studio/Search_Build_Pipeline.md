---
draft: false
doc_id: d-20260519-210908-69d0e9
title: Search Build Pipeline
added_date: "2026-05-19 21:09:08"
last_updated: "2026-11-18"
parent_id: d-20260331-000000-5dcf32

---
# Search Build Pipeline

[Builder](Builder.md#commands) owns the current Working Search command. [Working rebuild](Builder.md#working-rebuild) explains **Refresh Search and Recent** and the path from completed discovery files to the publication queue. [Docs Search Index](Docs_Search_Index.md) owns source coverage, index fields and reader matching.

Studio **Refresh Catalogue** prepares the Work and Gallery inputs used by the active Catalogue page. Its output is described in [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md#generated-read-models). The former standalone Catalogue Search index belongs to the frozen [Catalogue Archive](Catalogue_Archive.md#site-snapshot).
