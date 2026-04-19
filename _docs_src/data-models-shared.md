---
doc_id: data-models-shared
title: Shared Patterns
last_updated: 2026-04-19
parent_id: data-models
sort_order: 10
---

# Shared Patterns

This document records the model conventions that recur across scopes.

## Common Artifact Types

The current site uses a small number of repeated artifact patterns.

### 1. Minimal route stubs

Examples:

- `_works/*.md`
- `_series/*.md`
- `_work_details/*.md`
- `_moments/*.md`
- `_docs_src/*.md`
- `_docs_library_src/*.md`

Purpose:

- give Jekyll a stable route and identity record
- keep the route layer publishable and linkable
- keep canonical runtime content in generated JSON when that content is too large or too dynamic for front matter alone

### 2. Generated index JSON

Examples:

- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/data/moments_index.json`
- `assets/data/docs/scopes/<scope>/index.json`

Purpose:

- provide one lightweight entry point for lists, trees, and cross-item lookup
- avoid one fetch per card or nav node
- keep large per-item prose or detail payloads out of list-level responses

### 3. Generated per-record JSON

Examples:

- `assets/series/index/<series_id>.json`
- `assets/works/index/<work_id>.json`
- `assets/moments/index/<moment_id>.json`
- `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`

Purpose:

- hold the heavier page-local payload for one record
- allow route pages to fetch only the content they need
- keep prose and richer structured data out of the shared indexes

### 4. Generated search JSON

Examples:

- `assets/data/search/catalogue/index.json`
- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`

Purpose:

- flatten scope-owned content into one search-oriented artifact
- separate search concerns from the source indexes used by other pages
- precompute the text surface the client runtime needs

## Common Design Choices

### Header blocks

Most generated JSON artifacts use a `header` object with:

- `schema`
- `version`
- `generated_at_utc`
- a scope- or entity-specific identifier where useful
- `count` where counting the payload matters

Why:

- consumers can tell which payload family they are reading
- writers can skip unchanged outputs by comparing versions
- humans and tools can inspect freshness without reading the full payload

### Object maps for canonical lookup

The main catalogue and docs indexes prefer object maps or direct arrays of canonical records rather than nested page fragments.

Why:

- direct lookup by ID is cheap
- cross-reference validation is simpler
- one canonical map is easier to diff and audit than many partially duplicated fragments

### Arrays where order is part of the contract

Search payloads and some record-local child collections use arrays.

Why:

- order matters for ranked results, sections, and detail lists
- arrays preserve the writer’s intended sequence without requiring a second ordering field everywhere

### `content_html` as a generated field

Per-record catalogue payloads and per-doc docs payloads store rendered HTML separately from the lightweight indexes.

Why:

- prose is the main payload size risk
- list pages and nav trees rarely need it
- rendering Markdown once at build time keeps the browser/runtime simpler

## Enforcement And Drift Control

Current builders and validators enforce more of the model than the raw JSON alone makes obvious.

Current enforcement layers:

- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
  drives the live rebuild path that writes the main catalogue indexes and record payloads
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
  documents the unified search builder that now owns `catalogue`, `studio`, and `library` search outputs from canonical repo JSON and published docs indexes
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  validates duplicate `doc_id` values and unknown `parent_id` references before writing docs-scope payloads
- [Audit Site Consistency](/docs/?scope=studio&doc=scripts-audit-site-consistency)
  checks cross-references and key JSON schema expectations across catalogue and Studio artifacts

## Performance Implications

The current model favors:

- small shared indexes for list pages
- lazy loading of heavier per-record payloads
- generated HTML rather than runtime Markdown parsing
- scope-owned search artifacts rather than scanning unrelated data at runtime

This is why the site does not expose one single giant JSON dump for everything.

The tradeoff is that one conceptual entity can span more than one artifact:

- a route stub for routing
- an index entry for lists and lookup
- a per-record payload for page-local detail
- optionally a search entry for discovery

That split is intentional and is a core part of the current performance model.
