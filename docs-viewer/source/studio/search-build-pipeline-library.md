---
doc_id: search-build-pipeline-library
title: Library Scope
added_date: 2026-05-19
last_updated: 2026-06-05
parent_id: search-docs-viewer-infrastructure
viewable: true
---
# Search Build Pipeline Library Scope

## Library Scope

### Current Writer

- `./docs-viewer/build/build_search.py --scope library`, dispatched to `docs-viewer/build/build_search.py`

### Current Output

- `assets/data/search/library/index.json`

### Current Source Input

- `docs-viewer/source/library/*.md`

The current Library search artifact is derived from source front matter through the configured scope source root.
It no longer reads `assets/data/docs/scopes/library/index.json` or accepts `--source-index`.
Rows with `viewable: false` are skipped so draft Library docs can be generated for manage-mode review without appearing in public/default search.

### Current Commands

Default write command:

```bash
./docs-viewer/build/build_search.py --scope library --write
```

Dry run:

```bash
./docs-viewer/build/build_search.py --scope library
```

Current supported overrides:

- `--output PATH`
- `--only-doc-ids IDS`
- `--remove-missing`
- `--write`
- `--force`

### Current Build Behaviour

Current builder behaviour for Library:

- matches the same docs-domain record model used by Studio
- reads source front matter from the configured Library docs source root
- can patch the existing Library search artifact for targeted `doc_id` updates
- emits one search record per public-viewable Library doc after applying `viewable` filtering
- stays compatible with the shared Docs Viewer inline search runtime

### Current Runtime Mapping

- consumed by inline docs search on `/library/`
- not consumed by the dedicated `/catalogue/search/` page
- manual docs rebuilds remain split:
  - `./docs-viewer/build/build_docs.py --scope library --write`
  - `./docs-viewer/build/build_search.py --scope library --write`
- targeted docs-search command:
  - `./docs-viewer/build/build_search.py --scope library --write --only-doc-ids library --remove-missing`
- live docs-management actions rebuild the current docs scope and then run targeted same-scope docs-search updates for explicit affected ids
- the explicit `POST /docs/rebuild` endpoint still runs a full same-scope docs-search rebuild
- the Docs Live Rebuild Watcher uses targeted same-scope docs-search updates for safe small source changes and falls back to full rebuilds for ambiguous or broad changes
- targeted docs-search updates rebuild only affected Library docs entries by `doc_id`, remove affected ids that are missing or non-viewable, and report diagnostic counts for Codex/server use
- while `bin/local-studio` is running, the Docs Live Rebuild Watcher keeps `docs-viewer/source/library/*.md` changes aligned with `assets/data/search/library/index.json`
