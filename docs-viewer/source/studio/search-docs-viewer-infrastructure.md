---
doc_id: search-docs-viewer-infrastructure
title: Docs Viewer Infrastructure
added_date: 2026-06-02
last_updated: 2026-06-02
ui_status: review
parent_id: search
viewable: true
---
# Docs Viewer Search Infrastructure

## Domain

Docs Viewer search owns document-corpus lookup for Docs Viewer scopes.

Current live surfaces:

- `/docs/`
- `/library/`
- `/analysis/`

Current outputs:

- `docs-viewer/generated/search/studio/index.json`
- `docs-viewer/generated/search/tmp/index.json`
- `assets/data/search/library/index.json`
- `assets/data/search/analysis/index.json`

Docs Viewer search is separate from Catalogue search.
It does not index works, series, moments, or public catalogue route state.

## Config Surface

Current scope config:

- `docs-viewer/config/scopes/docs_scopes.json`

Current responsibilities:

- declare Docs Viewer scopes
- declare source Markdown roots
- declare generated docs output paths
- declare generated search output paths
- declare viewer base routes and scope routing behavior
- declare viewability and manage-only scope settings used by generated docs payloads

Docs Viewer browser config is generated from the same scope config by:

- `docs-viewer/build/build_docs.py`

The generated browser config includes per-scope docs index URLs and search index URLs.
It also emits a Docs Viewer search policy payload with the docs-domain `record_update` targeted policy.

Docs Viewer search does not use `studio/services/catalogue/search/build_config.json`.

## Build Pipeline

Current build entrypoint:

```bash
./docs-viewer/build/build_search.py --scope studio
```

Write command:

```bash
./docs-viewer/build/build_search.py --scope studio --write
```

The same entrypoint supports any configured Docs Viewer scope, including `studio`, `library`, `analysis`, and `tmp`.

Current source input:

- the scope's generated Docs Viewer index, normally `<scope output>/index.json`

For example:

- `docs-viewer/generated/docs/studio/index.json`
- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/analysis/index.json`

Current pipeline shape:

1. load the requested scope from `docs-viewer/config/scopes/docs_scopes.json`
2. resolve source docs index and search output paths from that scope config
3. read the generated docs index
4. filter out non-viewable and manage-only docs
5. derive one search entry per viewable doc
6. derive `search_terms` and `search_text`
7. compute a content hash in the artifact header
8. write only when changed, forced, or targeted changes require it

Docs search is downstream of the generated Docs Viewer docs payload.
It does not parse source Markdown directly during search-index generation.

## Index Schema

Current top-level shape:

- `header`
- `entries`

Current entry fields include:

- `id`
- `kind`
- `title`
- `href`
- `last_updated`
- `parent_id`
- `parent_title`
- `display_meta`
- `search_terms`
- `search_text`

Current included record kind:

- `doc`

Current exclusions:

- Catalogue records
- raw Markdown
- raw rendered HTML
- full body prose
- section-level records
- generated snippets or summaries

## Ranking Runtime

Current runtime modules:

- `docs-viewer/runtime/js/docs-viewer-search-controller.js`
- `docs-viewer/runtime/js/docs-viewer-search.js`
- `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`
- `docs-viewer/runtime/js/docs-viewer-render.js`

The Docs Viewer app receives the current scope's `search_index_url` from normalized browser config.
The search controller loads that index through the generated-data runtime, normalizes doc entries, evaluates matches, sorts results, and renders them into the active Docs Viewer route context.

Current ranking is docs-domain-specific.
It weights exact id/title matches first, then phrase and prefix matches, then title-token coverage, then parent-title matches, then broader `search_text` matches.

Docs Viewer also has a recent-docs path that sorts viewable docs by `added_date` or `last_updated`.

## Targeted Updates

Docs targeted mode uses:

```bash
./docs-viewer/build/build_search.py --scope studio --only-doc-ids <doc_id> --remove-missing
```

Current targeted behavior:

- create or update entries by `doc_id`
- remove affected ids that are missing or no longer viewable when `--remove-missing` is passed
- fall back to a full search payload when the existing search artifact is unavailable
- report changed, removed, unchanged, and fallback counts in CLI/server output

Docs management writes and the Docs Live Rebuild Watcher use the same Docs Viewer search builder for same-scope follow-through.
The explicit docs rebuild endpoint can still run a full same-scope docs-search rebuild.

Unsupported Catalogue flags fail closed:

- `--only-records`

## Domain Review Questions

Docs Viewer-specific review should ask:

- Are doc title, parent title, date, and id enough for real docs lookup?
- Should headings, summaries, or body excerpts enter search, and what payload cost would that add?
- Are non-viewable and manage-only docs filtered correctly?
- Does ranking reflect document lookup rather than catalogue lookup?
- Do results open in the correct Docs Viewer scope and route mode?
- Are targeted updates safe for source renames, parent changes, and visibility changes?
- Does portable Docs Viewer setup avoid depending on Catalogue search files?

Related docs:

- [Domain Review Patterns](/docs/?scope=studio&doc=search-domain-review-patterns)
- [Studio Scope](/docs/?scope=studio&doc=search-build-pipeline-studio)
- [Library Scope](/docs/?scope=studio&doc=search-build-pipeline-library)
- [Analysis Scope](/docs/?scope=studio&doc=search-build-pipeline-analysis)
- [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape)
