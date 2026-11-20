---
draft: false
doc_id: d-20260813-214351-98d3f0
title: Docs Viewer Search Tokenizer
added_date: "2026-08-13 21:43:51"
last_updated: "2026-11-20"
summary: Durable normalization and term-recognition contract shared by Docs Viewer index generation and browser queries.
parent_id: d-20260602-160839-6d3cbb
---

# Docs Viewer Search Tokenizer

Index generation and browser queries share term recognition. The configured Search scope selects the fields, and the tokenizer derives terms from each supplied value. Portfolio currently searches Titles, Library/Book use Title and Summary, and other collection scopes use their configured fields. [Discovery fields and eligibility](Reader_Discovery_And_Return.md#scope-and-eligibility)

## Term Contract

Apply NFKC normalization and lowercase comparison. Recognize technical compounds before discarding punctuation, retain the complete compound and useful underscore/hyphen/dot/camel-case components, then deduplicate terms within a field. Mixed letters/numbers remain searchable. Standalone integers, including single digits and grouped thousands, are retained in Title fields.

| Input | Terms |
| --- | --- |
| `Full-text search` | `full-text`, `full`, `text`, `search` |
| `DOCS_VIEWER_BASE_URL` | `docs_viewer_base_url`, `docs`, `viewer`, `base`, `url` |
| `handleEditMetadataSave` | Whole lowercase compound and `handle`, `edit`, `metadata`, `save` |
| `build_search.py` | `build_search.py`, `build`, `search` |
| `SM-1.0` | `sm-1.0`, `sm` |
| `10,000` in Title | `10000` |

Prose terms omit complete immutable document IDs, 64-character hexadecimal digests, URLs, paths, markup spans, one-character words and file-extension-only components. Numeric-only body terms are omitted. The fixed stop words are `a an and are as at be by for from in is it of on or that the to with`. Corpus frequency can affect ranking without dropping common terms. [Python tokenizer](../../docs-viewer/build/build_search.py) · [Browser tokenizer](../../docs-viewer/runtime/js/shared/docs-viewer-search.js)

## Query Semantics

Every normalized query term must match the same document. Text terms of at least two characters also match prefixes. Numeric terms use exact Title postings, so `10,000` and `10000` find the same Titles. Exact `identity`/`last_updated` fields use their separate path when enabled by the index. A query without matching normalized terms or exact-field matches returns no results.

Source extraction uses parsed authored content and separate heading/body/code fields. Summary remains its metadata field. Extraction omits active Summary, Related Links and Docs-image forms, and all hidden Catalogue references. Term changes need matching Python/browser behavior and an explicit Search rebuild. A browser-only prefix rule travels through the public runtime projection. [Source extraction](Reader_Discovery_And_Return.md#source-boundary) · [Build and publication](Reader_Discovery_And_Return.md#build-and-publication)
