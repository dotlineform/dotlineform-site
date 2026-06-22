---
doc_id: analytics-tag-source-data
title: Tag Source Data
added_date: 2026-04-19
last_updated: "2026-05-06 20:51"
parent_id: analytics
viewable: true
---
# Analytics Tag Source Data

Analytics tag source data lives under `analytics-app/data/canonical/` and is read/written through the Local Analytics API and Analytics-owned tag helper package.

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
  - description
  - per-row update metadata

Why it is separate:

- vocabulary needs to be reviewable and mutable without editing assignments
- aliases and assignments should point at stable canonical tags rather than embedding their own parallel definitions

Current consumers:

- Tag Editor
- Tag Registry
- Tag Aliases
- Series Tags labeling and coverage logic
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
- Analytics logic can derive effective work tags by combining series tags with work overrides

Current consumers:

- Tag Editor
- Series Tags
- Analytics RAG logic
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
- `tag-assignments.json` series keys must line up with `site/assets/data/series_index.json`
- `tag-assignments.json` work override keys must line up with `site/assets/data/works_index.json` and with the owning series membership in `series_index.json`
- group logic in the UI depends on `tag-registry.json`, `tag-groups.json`, and the group order configured in Analytics route config

Current enforcement:

- the scoped JSON build flow refreshes generated catalogue payloads that tag assignments align against
- catalogue build and cleanup flows update Analytics tag assignments through the Analytics tag source path contract where catalogue membership changes require sync
- [Audit Site Consistency](/docs/?scope=studio&doc=scripts-audit-site-consistency) checks cross-references between assignments, series membership, and works
