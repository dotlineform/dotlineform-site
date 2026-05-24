---
doc_id: search-build-pipeline-studio
title: Search Build Pipeline Studio Scope
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: search-build-pipeline
sort_order: 8300
---
# Search Build Pipeline Studio Scope

## Studio Scope

### Current Writer

- `./scripts/build_search.rb --scope studio`, dispatched to `studio/docs-viewer/build/build_search.rb`

### Current Output

- `assets/data/search/studio/index.json`

### Current Source Input

- `assets/data/docs/scopes/studio/index.json`

The current Studio search artifact is derived from the published Studio docs index rather than directly from `_docs/`.

### Current Commands

Default write command:

```bash
./scripts/build_search.rb --scope studio --write
```

Dry run:

```bash
./scripts/build_search.rb --scope studio
```

Current supported overrides:

- `--source-index PATH`
- `--output PATH`
- `--only-doc-ids IDS`
- `--remove-missing`
- `--write`
- `--force`

### Current Build Behaviour

Current builder behaviour for Studio:

- reads the generated Studio docs index
- can patch the existing Studio search artifact for targeted `doc_id` updates
- emits one search record per viewable Studio doc
- keeps record shape compatible with the shared Docs Viewer inline search runtime
- does not create section-level records
- does not index doc body prose
- does not generate summaries or snippets

Current record inputs come from docs metadata such as:

- `doc_id`
- `title`
- `last_updated`
- `parent_id`
- `viewer_url`

Current derived search support fields:

- `search_terms`
- `search_text`

### Current Runtime Mapping

- consumed by inline docs search on `/docs/`
- not consumed by the dedicated `/catalogue/search/` page
- manual docs rebuilds remain split:
  - `./scripts/build_docs.rb --scope studio --write`
  - `./scripts/build_search.rb --scope studio --write`
- targeted docs-search command:
  - `./scripts/build_search.rb --scope studio --write --only-doc-ids search-build-pipeline --remove-missing`
- live docs-management actions rebuild the current docs scope and then run targeted same-scope docs-search updates for explicit affected ids
- the explicit `POST /docs/rebuild` endpoint still runs a full same-scope docs-search rebuild
- the Docs Live Rebuild Watcher uses targeted same-scope docs-search updates for safe small source changes and falls back to full rebuilds for ambiguous or broad changes
- targeted docs-search updates rebuild only affected Studio docs entries by `doc_id`, remove affected ids that are missing or non-viewable, and report diagnostic counts for Codex/server use
- `bin/local-studio` only runs startup `studio` docs-search rebuilds when `DOCS_STARTUP_REBUILD_SCOPES` includes `studio`, and then uses the Docs Live Rebuild Watcher to keep `_docs/*.md` changes aligned with `assets/data/search/studio/index.json`
