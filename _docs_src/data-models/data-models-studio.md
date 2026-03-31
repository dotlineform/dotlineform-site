---
doc_id: data-models-studio
title: Studio Scope
last_updated: 2026-04-01
parent_id: data-models
sort_order: 30
---

# Studio Scope

This document covers the current checked-in data model for the Studio scope.

The Studio scope has two main model families:

- Studio route data used by `/studio/`
- Studio docs data used by `/docs/`

## Scope Boundary

Current checked-in Studio data artifacts:

- Studio route data:
  - `assets/studio/data/tag_registry.json`
  - `assets/studio/data/tag_aliases.json`
  - `assets/studio/data/tag_assignments.json`
  - `assets/studio/data/tag_groups.json`
  - `assets/studio/data/build_activity.json`
  - `assets/studio/data/work_storage_index.json`
- Studio docs source:
  - `_docs_src/**/*.md`
- generated Studio docs data:
  - `assets/data/docs/scopes/studio/index.json`
  - `assets/data/docs/scopes/studio/by-id/<doc_id>.json`
- Studio docs search:
  - `assets/data/search/studio/index.json`

Related config, documented separately:

- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`

## Studio Route Data

### `work_storage_index.json`

Purpose:

- provide Studio-only work storage lookups without putting curator-only storage data into the public `works_index.json`

Current content families:

- header metadata
- `works` map keyed by `work_id`
- per-work storage values only where storage is populated

Current consumers:

- `/studio/studio-works/`

Why it is separate:

- `storage` is useful to the curator but does not belong in the current public works summary index
- the Studio works page needs one lightweight bulk lookup, not one per-work JSON fetch per row

### `build_activity.json`

Purpose:

- lightweight Studio-facing feed of recent catalogue build runs

Current content families:

- feed header metadata
- recent run entries with:
  - time
  - status
  - short summary
  - workbook change groups
  - media change groups
  - action counts
  - result flags

Why it is separate:

- the curator-facing feed should stay smaller and more stable than raw script logs
- the Studio page only needs the latest small slice of recent activity

Current consumers:

- `/studio/build-activity/`

### `tag_registry.json`

Purpose:

- canonical vocabulary for Studio tags

Current content families:

- version and update metadata
- allowed groups policy
- canonical tag rows with:
  - identity
  - group
  - label
  - status
  - description
  - per-row update metadata

Why it is separate:

- vocabulary needs to be reviewable and mutable without editing assignments
- aliases and assignments should point at stable canonical tags rather than embedding their own parallel definitions

Current consumers:

- Tag Editor
- Tag Registry
- Tag Aliases
- Series Tags status and labeling logic
- catalogue search tag-label enrichment through the search builder

### `tag_aliases.json`

Purpose:

- stable shorthand mapping onto canonical tags

Current content families:

- version and update metadata
- alias map keyed by alias string
- alias rows that carry:
  - description
  - one or more canonical target tags

Why it is separate:

- alias management changes more often than vocabulary policy
- keeping aliases separate allows import/edit/promote/demote flows without rewriting the registry format
- the editor can preserve canonical tag identity while still recording alias-assisted selection history

Current consumers:

- Tag Editor input resolution
- Tag Aliases page
- local mutation flows in the tag write server

### `tag_assignments.json`

Purpose:

- canonical Studio-owned assignment state for series tags and per-work overrides

Current content families:

- version and update metadata
- `series` object keyed by `series_id`
- per-series rows with:
  - `tags`
  - `updated_at_utc`
  - `works`
- per-work override rows nested under the owning series

Why it is designed around series-first ownership:

- series is the main curation unit in Studio
- per-work overrides are intentionally modeled as deltas under the owning series rather than as a separate flat table
- catalogue search and Studio status logic can derive effective work tags by combining series tags with work overrides

Current consumers:

- Tag Editor
- Series Tags
- Studio RAG/status logic
- catalogue search generation

Important design choice:

- work overrides are stored under the owning series, not globally by `work_id`

Why:

- it preserves the series membership context that the UI already uses
- it makes it easier to detect invalid overrides when a work no longer belongs to a series
- it keeps override review close to the series row that owns it

### `tag_groups.json`

Purpose:

- descriptive reference for the tag-group taxonomy

Current content families:

- version and update metadata
- ordered group descriptions
- short and long descriptions per group

Why it is separate:

- group prose is explanatory content, not assignment state
- it is reused across Studio pages for labels, help text, and info links

Current consumers:

- Tag Groups page
- group keys and info buttons across Studio pages and modals

## Studio Route Data Dependencies

The Studio route data model has important dependencies that are only partly explicit in the JSON.

Key dependencies:

- `tag_aliases.json` targets must refer to canonical tags in `tag_registry.json`
- `tag_assignments.json` series keys must line up with `assets/data/series_index.json`
- `tag_assignments.json` work override keys must line up with `assets/data/works_index.json` and with the owning series membership in `series_index.json`
- group logic in the UI depends on `tag_registry.json`, `tag_groups.json`, and the group order configured in `studio_config.json`

Current enforcement:

- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages) syncs missing series rows into `tag_assignments.json`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline) prunes removed series rows and removed per-work overrides from `tag_assignments.json` when the owning workbook rows are removed
- [Audit Site Consistency](/docs/?scope=studio&doc=scripts-audit-site-consistency) checks cross-references between assignments, series membership, and works
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server) constrains writes to the Studio-owned JSON files and creates backups/logs

## Studio Docs Data

### `_docs_src/**/*.md`

Purpose:

- source corpus for the Studio docs scope served at `/docs/`

Current content families:

- front matter used as identity/tree metadata:
  - `doc_id`
  - `title`
  - `last_updated`
  - `parent_id`
  - `sort_order`
  - optional `published`
- Markdown or raw HTML body content

Why Markdown is part of the data model here:

- for docs, the source Markdown is the canonical authored content
- the builder turns that content into the generated docs-viewer payloads

### `assets/data/docs/scopes/studio/index.json`

Purpose:

- lightweight tree/index payload for the Studio docs corpus

Current content families:

- one row per published Studio doc
- identity, title, ordering, source path, viewer URL, and per-doc content URL

Current site mapping:

- left-hand tree and lookup layer for `/docs/`

Why it exists separately from the per-doc payload:

- the docs viewer needs tree metadata for many docs at once
- it should not load full rendered HTML for every doc on first page load

### `assets/data/docs/scopes/studio/by-id/<doc_id>.json`

Purpose:

- per-doc rendered payload for one Studio doc

Current content families:

- the same identity metadata as the index row
- rendered `content_html`

Current site mapping:

- right-hand document pane on `/docs/`

Why it is per-doc:

- docs bodies can be much larger than nav metadata
- loading them on demand keeps the shared viewer responsive

## Studio Docs Search Data

### `assets/data/search/studio/index.json`

Purpose:

- search-owned flattened index for published Studio docs

Current content families:

- one `doc` entry per published Studio doc
- doc identity, title, viewer URL, last-updated metadata, parent context, and normalized search text

Current site mapping:

- inline docs search on `/docs/`

Why it is derived from the docs index rather than the source Markdown directly:

- the canonical published Studio docs corpus is the generated docs index, not every source file under `_docs_src/`
- this keeps unpublished docs and invalid tree relationships out of the search corpus automatically

Current writer:

- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)

## Performance Notes

The Studio scope is designed for browser-side tooling and docs navigation.

Current performance choices:

- registry, aliases, groups, and assignments are loaded as ordinary JSON rather than paged API responses
- assignments are series-keyed, which makes per-series editing and status computation straightforward
- Studio docs use index plus by-id payloads so `/docs/` does not load the whole corpus at once
- Studio docs search uses a flattened generated artifact instead of scanning doc HTML in the browser

The tradeoff is that some relationships are enforced by scripts and UI code rather than by a formal schema system.

## Practical Update Rule

If a change affects:

- Studio tag vocabulary, aliases, or assignments
  update this doc and the relevant Studio page doc
- Studio docs source metadata or docs payload shape
  update this doc and the relevant Docs Viewer or Scripts doc
- Studio docs search shape
  update this doc and the relevant Search doc

For Studio config files and loader behavior, use [Config](/docs/?scope=studio&doc=config) as the owning section.
