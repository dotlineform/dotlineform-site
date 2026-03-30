---
doc_id: scripts-build-search-data
title: Build Search Data
last_updated: 2026-03-30
parent_id: scripts-overview
sort_order: 45
---

# Build Search Data

Script:

```bash
./scripts/build_search_data.rb
```

Current purpose:

- search-owned build entrypoint for non-catalogue scopes
- current implemented scope: `studio`

Default command:

```bash
./scripts/build_search_data.rb
./scripts/build_search_data.rb --write
```

## Current defaults

- scope:
  - `studio`
- canonical source index:
  - `assets/data/docs/scopes/studio/index.json`
- generated output:
  - `assets/data/search/studio/index.json`

## Current flags

- `--scope NAME`
  - current supported value: `studio`
- `--source-index PATH`
  - override the canonical source index JSON path
- `--output PATH`
  - override the generated search index output path
- `--write`
  - persist generated files; omit for dry-run

## Current behavior

- reads the published Studio docs index
- emits one search record per published doc
- keeps record shape compatible with the shared `/search/` runtime
- does not index section-level records
- does not index doc body prose or summaries

This is the first search-owned builder step toward the longer-term search pipeline documented in [Search Pipeline Target Architecture](/docs/?doc=search-pipeline-target-architecture).

## Related references

- [Scripts Overview](/docs/?doc=scripts-overview)
- [Search Build Pipeline](/docs/?doc=search-build-pipeline)
- [Search Studio V1 Index Shape](/docs/?doc=search-studio-v1-index-shape)
