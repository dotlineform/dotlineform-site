---
doc_id: scripts-build-search-data
title: Build Search Data
last_updated: 2026-03-31
parent_id: scripts
sort_order: 45
---

# Build Search Data

Script:

```bash
./scripts/build_search_data.rb
```

Current purpose:

- search-owned build entrypoint for non-catalogue scopes
- current implemented scopes: `studio`, `library`

Default command:

```bash
./scripts/build_search_data.rb --write
```

Dry-run:

```bash
./scripts/build_search_data.rb
```

## Current Defaults

- scope:
  - `studio`
- canonical source index:
  - `assets/data/docs/scopes/studio/index.json`
- generated output:
  - `assets/data/search/studio/index.json`

Library scope:

- scope:
  - `library`
- canonical source index:
  - `assets/data/docs/scopes/library/index.json`
- generated output:
  - `assets/data/search/library/index.json`

## Source And Target Artifacts

Source artifacts:

- `assets/data/docs/scopes/studio/index.json`
- `assets/data/docs/scopes/library/index.json`

Generated target artifacts:

- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`

These outputs are the docs-domain search indexes consumed by the shared Docs Viewer runtime for inline search in the Studio and Library scopes.

## Current Flags

- `--scope NAME`
  - current supported values: `studio`, `library`
- `--source-index PATH`
  - override the canonical source index JSON path
- `--output PATH`
  - override the generated search index output path
- `--write`
  - persist generated files; omit for dry-run

## Current behavior

- reads the published docs index for the selected scope
- emits one search record per published doc
- keeps record shape compatible with the shared docs-viewer inline search runtime
- does not index section-level records
- does not index doc body prose or summaries

This is the first search-owned builder step toward the longer-term search pipeline documented in [Search Pipeline Target Architecture](/docs/?scope=studio&doc=search-pipeline-target-architecture).

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Studio V1 Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
