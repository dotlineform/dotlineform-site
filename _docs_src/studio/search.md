---
doc_id: search
title: Search
last_updated: 2026-03-29
parent_id: studio
sort_order: 30
---

# Search

This section holds the Studio-first search planning and implementation docs.

Current documents:

- **[Studio Search V1](search-v1.md)**
- **[Search V1 Implementation Plan](search-v1-implementation-plan.md)**

Current direction:

- search starts as a Studio page
- search owns its own generated artifact rather than reusing browse indexes directly
- full-text growth should be handled with optional secondary payloads rather than inflating the base payload

Planned future split:

- contract and data-shape docs
- field classification docs
- ranking and benchmark docs
- implementation and verification docs
