---
doc_id: import-export
title: Import/Export
added_date: "2026-05-06 18:39"
last_updated: "2026-05-06 20:49"
parent_id: ""
sort_order: 50
published: true
viewable: true
---
# Import/Export

Data can be exported as JSON files for external editing (typically by an LLM).

A generic page handles the shared UI which is called from Studio pages that relate to a supported data domain, for example, [Library](/studio/library/)

Data extraction and import is handled by _adapters_ which are config-driven client and server-side functions that ensure data is correctly structured and saved.