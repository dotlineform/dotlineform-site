---
draft: false
doc_id: d-20260726-191340-d00c52
title: Usage Index
added_date: "2026-07-26 19:13:40"
last_updated: "2026-10-01 13:20:00"
parent_id: d-20260725-153656-516b61
---
# Usage Index

The generated semantic usage index is retired. Build no longer stores occurrence rows, raw token text or source positions, and targeted builds require no semantic index prerequisite. The Semantic Tokens report and its read endpoint are also retired.

Supported Work tokens contribute unique Catalogue document relationships through [Document Build](Builder.md), stored in the existing `links-by-id` graph. [Related Links](Related_Links.md) presents these relationships. Gallery Media View tokens create no document relationship.

Live token parsing retains raw text and source positions for Source editing and audits. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns that contract; [Docs Broken Links](Broken_Links.md) independently checks authored links and media. The private Catalogue target lookup has separate consumers and is unaffected by usage-index retirement.
