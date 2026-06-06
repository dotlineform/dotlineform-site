---
doc_id: config-analytics-config-json
title: Analytics Config JSON
added_date: 2026-06-02
last_updated: 2026-06-03
parent_id: analytics
---
# Analytics Config JSON

Config file:

- `analytics-app/app/frontend/config/analytics-config.json`

## Contract Role

`analytics-config.json` is the browser-facing bootstrap manifest for the Local Analytics app.
It owns Analytics route shell metadata under `app.routes`, public catalogue index data lookup, and Analytics UI-text bundle paths.
It also owns the Analytics tag grouping and RAG scoring policy under `analysis`.

It is separate from Local Studio config.
Studio routes should not read Analytics route keys, tag config, or Data Sharing route config from `studio/app/frontend/config/studio-config.json`.

## What Reads It

The Analytics app frontend config loader reads this file once per Analytics page session and caches the payload.
Analytics route modules use it for:

- route URL lookup from `app.routes` for tag registry, aliases, groups, series tags, series tag editor, and Data Sharing prepare/review
- site data lookup for series and works indexes
- route-scoped UI-text bundle paths under `paths.data.ui_text`
- tag group order and coverage groups under `analysis.groups`
- RAG scoring thresholds under `analysis.rag`

Analytics-hosted Data Sharing routes get workflow metadata from `/analytics/api/data-sharing/config`.
They should not read `data-sharing/config/adapters.json` or `data-sharing/config/library-export-configs.json` directly through Analytics bootstrap config or static file serving.

The Analytics app server also treats this file as part of the local app route/runtime contract when serving Analytics pages.
It validates `app.routes` against currently served route shells, checks script paths, rejects duplicate paths, and rejects Analytics route metadata left in `paths.routes`.

## Edit Class

This file is maintainer-editable code infrastructure.
It is not a user-facing preference file.

Allowed edits include:

- adding or retiring Analytics route keys with matching route/server/test changes
- changing data path ownership when a data source moves
- adding or retiring UI-text bundle paths with route module changes

Do not add Local Studio route keys, Docs Viewer internals, generated payload schemas, or scoring implementations here.
Scoring policy belongs here, but scoring implementation belongs in `analytics-app/app/frontend/js/analysis-tag-scoring.js`.

## Cleanup Review

Completed cleanup:

- stale public-content route keys `library_page`, `analysis_page`, `series_page_base`, and `works_page_base` were removed from `paths.routes`
- Analytics app-route metadata moved from `paths.routes` to `app.routes`
- Analytics public catalogue links now use fixed public shells with query-state, matching the current public route contract
- Data Sharing config paths were removed from Analytics bootstrap config; Analytics-hosted Data Sharing routes now use the read-only Data Sharing config API endpoint
- tag grouping and RAG scoring policy are now explicit in the source JSON rather than only present in JavaScript fallback defaults
- tests assert the removed public route keys stay absent
- tests assert Analytics route metadata stays out of `paths.routes`

Site data path cleanup review:

- `paths.data.site.series_index` is retained because `series-tags.js`, `tag-registry.js`, and the series tag editor load the public series index through `loadSiteSeriesIndexJson(...)`
- `paths.data.site.works_index` is retained because the series tag editor loads the public works index through `loadSiteWorksIndexJson(...)`
- keeping these two paths in Analytics config makes the browser read dependency explicit; moving them into hidden loader constants would not remove a runtime dependency
- focused tests assert the runtime site data paths stay present

Subsequent sessions should also keep Data Sharing source config files server-owned.
Analytics browser routes should continue to use `/analytics/api/data-sharing/config` and should not restore direct `/data-sharing/config/...` reads or Analytics bootstrap keys for those files.
