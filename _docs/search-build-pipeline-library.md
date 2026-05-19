---
doc_id: search-build-pipeline-library
title: Search Build Pipeline Library Scope
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: search-build-pipeline
sort_order: 8400
---
# Search Build Pipeline Library Scope

## Library Scope

### Current Writer

- `./scripts/build_search.rb --scope library`, dispatched to `scripts/docs/build_search.rb`

### Current Output

- `assets/data/search/library/index.json`

### Current Source Input

- `assets/data/docs/scopes/library/index.json`

The current Library search artifact is derived from the generated Library docs index rather than directly from `_docs_library/`.
Rows with `viewable: false` are skipped so draft Library docs can be generated for manage-mode review without appearing in public/default search.
Archive docs follow the same rule as every other doc: set `viewable: false` when they should remain generated and manageable without appearing in public/default search.

### Current Commands

Default write command:

```bash
./scripts/build_search.rb --scope library --write
```

Dry run:

```bash
./scripts/build_search.rb --scope library
```

Current supported overrides:

- `--source-index PATH`
- `--output PATH`
- `--only-doc-ids IDS`
- `--remove-missing`
- `--write`
- `--force`

### Current Build Behaviour

Current builder behaviour for Library:

- matches the same docs-domain record model used by Studio
- reads only the generated Library docs index
- can patch the existing Library search artifact for targeted `doc_id` updates
- emits one search record per public-viewable Library doc after applying `viewable` filtering
- stays compatible with the shared Docs Viewer inline search runtime

### Current Runtime Mapping

- consumed by inline docs search on `/library/`
- not consumed by the dedicated `/catalogue/search/` page
- manual docs rebuilds remain split:
  - `./scripts/build_docs.rb --scope library --write`
  - `./scripts/build_search.rb --scope library --write`
- targeted docs-search command:
  - `./scripts/build_search.rb --scope library --write --only-doc-ids library --remove-missing`
- live docs-management actions rebuild the current docs scope and then run targeted same-scope docs-search updates for explicit affected ids
- the explicit `POST /docs/rebuild` endpoint still runs a full same-scope docs-search rebuild
- the Docs Live Rebuild Watcher uses targeted same-scope docs-search updates for safe small source changes and falls back to full rebuilds for ambiguous or broad changes
- targeted docs-search updates rebuild only affected Library docs entries by `doc_id`, remove affected ids that are missing or non-viewable, and report diagnostic counts for Codex/server use
- if `DOCS_STARTUP_REBUILD_SCOPES` includes `library`, `bin/dev-studio` runs a startup `library` docs-search rebuild
- while `bin/dev-studio` is running, the Docs Live Rebuild Watcher keeps `_docs_library/*.md` changes aligned with `assets/data/search/library/index.json`
