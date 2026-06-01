---
doc_id: search-build-pipeline-analysis
title: Search Build Pipeline Analysis Scope
added_date: 2026-05-19
last_updated: 2026-06-01
parent_id: search-build-pipeline
---
# Search Build Pipeline Analysis Scope

## Analysis Scope

### Current Writer

- `./docs-viewer/build/build_search.py --scope analysis`, dispatched to `docs-viewer/build/build_search.py`

### Current Output

- `assets/data/search/analysis/index.json`

### Current Source Input

- `assets/data/docs/scopes/analysis/index.json`

The current Analysis search artifact is derived from the generated Analysis docs index rather than directly from `docs-viewer/source/analysis/`.
Rows with `viewable: false` are skipped so draft Analysis docs can be generated for manage-mode review without appearing in public/default search.

### Current Commands

Default write command:

```bash
./docs-viewer/build/build_search.py --scope analysis --write
```

Dry run:

```bash
./docs-viewer/build/build_search.py --scope analysis
```

Current supported overrides:

- `--source-index PATH`
- `--output PATH`
- `--only-doc-ids IDS`
- `--remove-missing`
- `--write`
- `--force`

### Current Build Behaviour

Current builder behaviour for Analysis:

- matches the same docs-domain record model used by Studio and Library
- reads only the generated Analysis docs index
- can patch the existing Analysis search artifact for targeted `doc_id` updates
- emits one search record per public-viewable Analysis doc
- stays compatible with the shared Docs Viewer inline search runtime
- does not index doc body prose

### Current Runtime Mapping

- consumed by inline docs search on `/analysis/`
- not consumed by the dedicated `/catalogue/search/` page
- manual docs rebuilds remain split:
  - `./docs-viewer/build/build_docs.py --scope analysis --write`
  - `./docs-viewer/build/build_search.py --scope analysis --write`
- targeted docs-search command:
  - `./docs-viewer/build/build_search.py --scope analysis --write --only-doc-ids analysis --remove-missing`
- live docs-management actions rebuild the current docs scope and then run targeted same-scope docs-search updates for explicit affected ids
- the explicit `POST /docs/rebuild` endpoint still runs a full same-scope docs-search rebuild
- the Docs Live Rebuild Watcher uses targeted same-scope docs-search updates for safe small source changes and falls back to full rebuilds for ambiguous or broad changes
- targeted docs-search updates rebuild only affected Analysis docs entries by `doc_id`, remove affected ids that are missing or non-viewable, and report diagnostic counts for Codex/server use
- while `bin/local-studio` is running, the Docs Live Rebuild Watcher keeps `docs-viewer/source/analysis/**/*.md` changes aligned with `assets/data/search/analysis/index.json`
