---
doc_id: ideas
title: Ideas
last_updated: 2026-03-31
parent_id: ""
sort_order: 20
published: false
---

# Ideas

This file is the entry point for unplanned proposals and architecture-direction notes.

Use `_docs_src/_dev/backlog.md` for work that is expected to be done.

Current detailed idea docs:

- `_docs_src/_dev/search-config-architecture.md`
  defines which parts of search could become machine-readable policy and which should remain code
- `_docs_src/_dev/search-config-implementation-note.md`
  turns the search config idea into a staged implementation sequence
- `_docs_src/_dev/search-pipeline-target-architecture.md`
  describes the longer-term ownership boundary where search owns search assembly
- `_docs_src/_dev/search-result-shaping.md`
  describes a possible post-ranking shaping layer for redundancy and hierarchy handling
- `_docs_src/_dev/search-result-shaping-json.md`
  draft JSON policy sketch for a broader shaping layer
- `_docs_src/_dev/search-result-shaping-slimmer-json.md`
  draft JSON policy sketch for a narrower first shaping layer

Use these docs when:

- a proposal should stay documented without polluting the implementation-facing `/docs/` set
- a future architecture direction needs to be preserved for review
- a detailed draft is useful, but the repo should not present it as current site behaviour
