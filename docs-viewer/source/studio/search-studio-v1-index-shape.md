---
doc_id: search-studio-v1-index-shape
title: Docs Scope Index Shape
added_date: 2026-03-31
last_updated: 2026-06-05
parent_id: search-docs-viewer-infrastructure
viewable: true
---
# Docs Scope Index Shape

## Purpose

This document defines the current search-record shape for the docs-domain search artifacts.

It covers the current generated outputs for:

- `docs-viewer/generated/search/studio/index.json` for local Studio scope
- `site/assets/data/search/<scope>/index.json` for public library and analysis scopes

## Upstream Sources

The docs-domain search builder reads the configured Docs Viewer source roots:

- `docs-viewer/source/studio/*.md`
- `docs-viewer/source/<scope>/*.md`

It reads source front matter rather than public route payloads.
Rows with `viewable: false` are excluded from the docs-domain search artifacts.
Retired public docs `index.json` artifacts are not search-builder inputs.

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

The public artifacts use the same shape, but `header.scope` is `<scope>` and `header.schema` is `search_index_<scope>_v1`.

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

Source front matter can include `added_date`, but docs-domain search intentionally does not consume it yet. Search review remains separate from the Docs Viewer recently-added list.

## Current Builder Rules

Current builder behavior:

- one search record per viewable generated doc
- no section-level records
- no summary or snippet field
- no body-prose indexing
- one scope-owned artifact per docs scope

Current builder entrypoint:

```bash
./docs-viewer/build/build_search.py --scope studio --write
./docs-viewer/build/build_search.py --scope library --write
./docs-viewer/build/build_search.py --scope analysis --write
```

## Relationship To Other Search Artifacts

These docs-domain search artifacts are separate from:

- `site/assets/data/search/catalogue/index.json`

The dedicated `/catalogue/search/` page currently uses only `catalogue`.
The local and public artifacts are currently consumed by the shared Docs Viewer runtime for inline search.

## Related documents

- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture)
