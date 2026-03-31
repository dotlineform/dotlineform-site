---
doc_id: search-studio-v1-index-shape
title: Docs Scope Index Shape
last_updated: 2026-03-31
parent_id: search
sort_order: 75
---

# Docs Scope Index Shape

## Purpose

This document defines the current search-record shape for the docs-domain search artifacts.

It covers the current generated outputs for:

- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`

These are the current search artifacts used by the inline Docs Viewer search on `/docs/` and `/library/`.

For the wider docs-scope model that these artifacts sit on top of, use:

- [Data Models: Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Data Models: Library Scope](/docs/?scope=studio&doc=data-models-library)

## Upstream Sources

The docs-domain search builder reads the published docs indexes:

- `assets/data/docs/scopes/studio/index.json`
- `assets/data/docs/scopes/library/index.json`

It does not read raw Markdown source files directly.

## Top-Level Output Shape

Each docs-domain search artifact currently uses:

- `header`
- `entries`

Current top-level example:

```json
{
  "header": {
    "schema": "search_index_studio_v1",
    "scope": "studio",
    "version": "blake2b-...",
    "generated_at_utc": "2026-03-30T00:00:00Z",
    "count": 1
  },
    "entries": [
    {
      "id": "search-overview",
      "kind": "doc",
      "title": "Search Overview",
      "href": "/docs/?scope=studio&doc=search-overview",
      "display_meta": "2026-03-30",
      "search_terms": [
        "search-overview",
        "search",
        "overview"
      ],
      "search_text": "search overview 2026 03 30"
    }
  ]
}
```

The Library artifact uses the same shape, but `header.scope` is `library` and `header.schema` is `search_index_library_v1`.

## Current Record Contract

Current required record fields:

- `id`
- `kind`
- `title`
- `href`
- `search_terms`
- `search_text`

Current optional record fields:

- `last_updated`
- `parent_id`
- `parent_title`
- `display_meta`

Current field mapping back to the docs model:

- `id` <- docs `doc_id`
- `kind` <- always `doc`
- `title` <- docs title
- `href` <- scope-owned docs viewer URL
- `last_updated`, `parent_id`, `parent_title`, `display_meta` <- docs metadata used for context and search support
- `search_terms` and `search_text` <- search-specific derived fields built from that metadata

## Current Builder Rules

Current builder behavior:

- one search record per published doc
- no section-level records
- no summary or snippet field
- no body-prose indexing
- one scope-owned artifact per docs scope

Current builder entrypoint:

```bash
./scripts/build_search_data.rb --scope studio --write
./scripts/build_search_data.rb --scope library --write
```

## Relationship To Other Search Artifacts

These docs-domain search artifacts are separate from:

- `assets/data/search/catalogue/index.json`

The dedicated `/search/` page currently uses only `catalogue`.
The Studio and Library artifacts are currently consumed by the shared Docs Viewer runtime for inline search.

## Related documents

- [Data Models](/docs/?scope=studio&doc=data-models)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
