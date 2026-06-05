---
doc_id: search-build-pipeline-studio
title: Studio Scope
added_date: 2026-05-19
last_updated: 2026-06-05
parent_id: search
viewable: true
---
# Search Build Pipeline Studio Scope

## Studio Scope

### Current Writer

- `./docs-viewer/build/build_search.py --scope studio`, dispatched to `docs-viewer/build/build_search.py`

### Current Output

- `docs-viewer/generated/search/studio/index.json`

The path comes from the `studio` scope's `search_output` field in `docs-viewer/config/scopes/docs_scopes.json`.
The search builder no longer derives the output path from the scope id alone.

### Current Source Input

- `docs-viewer/source/studio/*.md`

The current Studio search artifact is derived from source front matter through the configured scope source root.
It no longer reads `docs-viewer/generated/docs/studio/index.json` or accepts `--source-index`.

### Current Commands

Default write command:

```bash
./docs-viewer/build/build_search.py --scope studio --write
```

Dry run:

```bash
./docs-viewer/build/build_search.py --scope studio
```

Current supported overrides:

- `--output PATH`
- `--only-doc-ids IDS`
- `--remove-missing`
- `--write`
- `--force`

### Current Build Behaviour

Current builder behaviour for Studio:

- reads source front matter from the configured Studio docs source root
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
  - `./docs-viewer/build/build_docs.py --scope studio --write`
  - `./docs-viewer/build/build_search.py --scope studio --write`
- targeted docs-search command:
  - `./docs-viewer/build/build_search.py --scope studio --write --only-doc-ids search-build-pipeline --remove-missing`
- live docs-management actions rebuild the current docs scope and then run targeted same-scope docs-search updates for explicit affected ids
- the explicit `POST /docs/rebuild` endpoint still runs a full same-scope docs-search rebuild
- the Docs Live Rebuild Watcher uses targeted same-scope docs-search updates for safe small source changes and falls back to full rebuilds for ambiguous or broad changes
- targeted docs-search updates rebuild only affected Studio docs entries by `doc_id`, remove affected ids that are missing or non-viewable, and report diagnostic counts for Codex/server use
- while `bin/local-studio` is running, the Docs Live Rebuild Watcher keeps `docs-viewer/source/studio/*.md` changes aligned with `docs-viewer/generated/search/studio/index.json`
