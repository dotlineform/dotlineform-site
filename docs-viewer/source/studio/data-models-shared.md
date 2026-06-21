---
doc_id: data-models-shared
title: Shared Patterns
added_date: 2026-04-19
last_updated: 2026-06-13
parent_id: architecture
---
# Shared Patterns

This document records the model conventions that recur across scopes.

## Common Artifact Types

The current site uses a small number of repeated artifact patterns.

### 1. Fixed Route Shells

Examples:

- `site/works/index.html`
- `site/series/index.html`
- `site/work-details/index.html`
- `site/moments/index.html`
- `site/library/index.html`
- `site/analysis/index.html`
- `docs-viewer/source/studio/*.md`
- `docs-viewer/source/library/*.md`
- `docs-viewer/source/analysis/**/*.md`

Purpose:

- give the public static artifact and Docs Viewer scopes stable route/document surfaces
- keep the route layer publishable and linkable
- keep canonical runtime content in generated JSON when that content is too large or too dynamic for front matter alone

Public route shells are persistent static HTML under `site/`.
Docs Viewer source Markdown remains persistent authored content because it is the canonical document source for each docs scope.

### 2. Generated index JSON

Examples:

- `site/assets/data/series_index.json`
- `site/assets/data/works_index.json`
- `site/assets/data/moments_index.json`
- `docs-viewer/generated/docs/<scope>/index.json`

Purpose:

- provide one lightweight entry point for lists, trees, and cross-item lookup
- avoid one fetch per card or nav node
- keep large per-item prose or detail payloads out of list-level responses

Docs-scope indexes also carry `viewer_options` for scope-level runtime behavior that should remain data-driven. Current options include:

- `non_loadable_doc_ids`
  reserved compatibility field for structural docs that can appear in the tree but route to a loadable descendant or the scope default doc; current scopes should normally leave this empty
- `manage_only_tree_root_ids`
  reserved field for tree roots excluded from public/default viewer and docs-search discovery but visible in manage mode; current scopes should normally use per-doc `viewable: false` instead
- `show_updated_date`
  controls whether document view metadata displays the generated row's `last_updated` date

Docs-scope index rows can also carry optional metadata from source front matter:

- `added_date` and `last_updated`
  date metadata used by the Docs Viewer and docs-domain search; legacy date-only values and new minute-precision values both flow through as strings
- `summary`
  plain-text, single-paragraph summary used by the Docs Viewer metadata surface
- `ui_status`
  raw UI status key used by the Docs Viewer to resolve scope-configured status emoji

Search indexes do not consume these optional fields until a scope-specific search task explicitly promotes them.

Docs-scope generated index location depends on the scope's publishing contract.
Public read-only docs routes no longer publish or load flat `site/assets/data/docs/scopes/<scope>/index.json`.
Public docs routes use `index-tree.json` for navigation, `recently-added.json` for recently-added mode, by-id payloads for selected documents, and separate search payloads.
Local tracked scopes may still use `docs-viewer/generated/docs/<scope>/index.json` as a rich local `/docs/` generated artifact.

All of these are generated runtime data.
The `site/assets/` location is the public static asset location; `docs-viewer/generated/` is a tracked non-public Docs Viewer data location served by the local Docs Viewer service for local scopes.
Document Data Sharing does not use either public or manage generated docs indexes as metadata input; it reads Docs Viewer source metadata from scope config and source Markdown.

### 3. Generated per-record JSON

Examples:

- `site/assets/series/index/<series_id>.json`
- `site/assets/works/index/<work_id>.json`
- `site/assets/moments/index/<moment_id>.json`
- `site/assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`
- `docs-viewer/generated/docs/<scope>/by-id/<doc_id>.json`

Purpose:

- hold the heavier page-local payload for one record
- allow generated route pages to fetch only the content they need
- keep prose and richer structured data out of the shared indexes

### 4. Generated search JSON

Examples:

- `site/assets/data/search/catalogue/index.json`
- `docs-viewer/generated/search/studio/index.json`
- `site/assets/data/search/analysis/index.json`
- `site/assets/data/search/library/index.json`

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
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture)
  documents the unified search builder that now owns `catalogue`, `studio`, `analysis`, and `library` search outputs from canonical repo JSON and published docs indexes
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

- a generated route shell for routing
- an index entry for lists and lookup
- a per-record payload for page-local detail
- optionally a search entry for discovery

That split is intentional and is a core part of the current performance model.
