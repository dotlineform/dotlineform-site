---
doc_id: data-models-studio
title: Studio Scope
added_date: 2026-04-19
last_updated: "2026-05-06 20:51"
parent_id: studio
---
# Studio Scope

This document covers the current checked-in data model for the Studio scope.

The Studio scope has two main model families:

- Studio route data used by `/studio/`
- Studio docs data used by `/docs/`

## Scope Boundary

Current checked-in Studio data artifacts:

- Studio route data:
  - `assets/studio/data/work_storage_index.json`
  - local service-backed activity data:
    - `var/studio/activity/activity_log.json`
    - `var/studio/activity/activity_log.jsonl`
- Analytics tag source data, owned outside Studio:
  - `analytics-app/data/canonical/tag-registry.json`
  - `analytics-app/data/canonical/tag-aliases.json`
  - `analytics-app/data/canonical/tag-assignments.json`
  - `analytics-app/data/canonical/tag-groups.json`
- Studio docs source:
  - `docs-viewer/source/studio/*.md`
- generated Studio docs data:
  - `docs-viewer/generated/docs/studio/index.json`
  - `docs-viewer/generated/docs/studio/by-id/<doc_id>.json`
- Studio docs search:
  - `docs-viewer/generated/search/studio/index.json`

Studio is a committed manage-mode Docs Viewer scope.
Its generated docs and search runtime payloads are tracked repo data, but they are not public static assets.
Do not move Studio generated docs/search back under `assets/data/docs/scopes/studio/` or `assets/data/search/studio/`; those roots are reserved for public read-only scopes.

Related config, documented separately:

- `studio/app/frontend/config/studio-config.json`
- `studio/app/frontend/js/studio-config.js`

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

## Analytics Tag Source Data

Analytics tag source data is no longer Studio route data.
It lives under `analytics-app/data/canonical/` and is read/written through the Local Analytics API and Analytics-owned tag helper package.

### `tag-registry.json`

Purpose:

- canonical vocabulary for Analytics tags

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
- Data Sharing tags adapter

### `tag-aliases.json`

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
- local mutation flows in the Local Analytics API

### `tag-assignments.json`

Purpose:

- canonical Analytics-owned assignment state for series tags and per-work overrides

Current content families:

- version and update metadata
- `series` object keyed by `series_id`
- per-series rows with:
  - `tags`
  - `updated_at_utc`
  - `works`
- per-work override rows nested under the owning series

Why it is designed around series-first ownership:

- series is the main curation unit for Analytics tag assignment
- per-work overrides are intentionally modeled as deltas under the owning series rather than as a separate flat table
- Analytics status logic can derive effective work tags by combining series tags with work overrides

Current consumers:

- Tag Editor
- Series Tags
- Analytics RAG/status logic
- Data Sharing tags adapter

Important design choice:

- work overrides are stored under the owning series, not globally by `work_id`

Why:

- it preserves the series membership context that the UI already uses
- it makes it easier to detect invalid overrides when a work no longer belongs to a series
- it keeps override review close to the series row that owns it

### `tag-groups.json`

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
- group keys and info buttons across Analytics pages and modals

## Analytics Tag Source Dependencies

The Analytics tag source model has important dependencies that are only partly explicit in the JSON.

Key dependencies:

- `tag-aliases.json` targets must refer to canonical tags in `tag-registry.json`
- `tag-assignments.json` series keys must line up with `assets/data/series_index.json`
- `tag-assignments.json` work override keys must line up with `assets/data/works_index.json` and with the owning series membership in `series_index.json`
- group logic in the UI depends on `tag-registry.json`, `tag-groups.json`, and the group order configured in Analytics route config

Current enforcement:

- the scoped JSON build flow refreshes generated catalogue payloads that tag assignments align against
- catalogue build and cleanup flows update Analytics tag assignments through the Analytics tag source path contract where catalogue membership changes require sync
- [Audit Site Consistency](/docs/?scope=studio&doc=scripts-audit-site-consistency) checks cross-references between assignments, series membership, and works
- [Retired Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server) records the migration of tag writes into the Local Analytics API, which constrains writes to Analytics-owned JSON files and logs activity

## Studio Docs Data

### `docs-viewer/source/studio/*.md`

Purpose:

- source corpus for the Studio docs scope served at `/docs/`

Current content families:

- front matter used as identity/tree metadata:
  - `doc_id`
  - `title`
  - `added_date`
  - `last_updated`
  - optional `summary`
  - optional `ui_status`
  - `parent_id`
  - optional `viewable`
- Markdown or raw HTML body content

Why Markdown is part of the data model here:

- for docs, the source Markdown is the canonical authored content
- the builder turns that content into the generated docs-viewer payloads

### `docs-viewer/generated/docs/studio/index.json`

Purpose:

- lightweight tree/index payload for the Studio docs corpus

Current content families:

- one row per generated Studio doc
- identity, title, added/update dates, optional `summary`, optional `ui_status`, ordering, `viewable`, source path, viewer URL, and per-doc content URL
- `viewer_options` for scope-level display behavior such as keeping document-view updated dates visible

Current site mapping:

- left-hand tree and lookup layer for `/docs/`

Why it exists separately from the per-doc payload:

- the docs viewer needs tree metadata for many docs at once
- it should not load full rendered HTML for every doc on first page load

### `docs-viewer/generated/docs/studio/by-id/<doc_id>.json`

Purpose:

- per-doc rendered payload for one Studio doc

Current content families:

- the same identity metadata as the index row
- optional `summary` and `ui_status` metadata when the source front matter defines them
- rendered `content_html`

Current site mapping:

- right-hand document pane on `/docs/`

Why it is per-doc:

- docs bodies can be much larger than nav metadata
- loading them on demand keeps the shared viewer responsive

## Studio Docs Search Data

### `docs-viewer/generated/search/studio/index.json`

Purpose:

- search-owned flattened index for published Studio docs

Current content families:

- one `doc` entry per viewable Studio doc
- doc identity, title, viewer URL, last-updated metadata, parent context, and normalized search text

Search currently uses `last_updated`, not `added_date`. The docs-viewer recently-added list reads `added_date` from the generated docs index, but search review is intentionally separate.

Current site mapping:

- inline docs search on `/docs/`

Why it is derived from the docs index rather than the source Markdown directly:

- the canonical generated Studio docs corpus is the generated docs index, not every source file under `docs-viewer/source/studio/`
- docs with `viewable: false` can have generated payloads for manage mode, but are filtered out of public/default docs search

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
