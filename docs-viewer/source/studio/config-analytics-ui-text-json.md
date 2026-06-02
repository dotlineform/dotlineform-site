---
doc_id: config-analytics-ui-text-json
title: Analytics UI Text Config
added_date: 2026-06-02
last_updated: 2026-06-02
parent_id: studio
viewable: true
---
# Analytics UI Text Config

Config files:

- `analytics-app/app/frontend/config/ui-text/data-sharing-prepare.json`
- `analytics-app/app/frontend/config/ui-text/data-sharing-review.json`
- `analytics-app/app/frontend/config/ui-text/series-tag-editor.json`
- `analytics-app/app/frontend/config/ui-text/series-tags.json`
- `analytics-app/app/frontend/config/ui-text/tag-aliases.json`
- `analytics-app/app/frontend/config/ui-text/tag-groups.json`
- `analytics-app/app/frontend/config/ui-text/tag-registry.json`

## Contract Role

These files hold route-scoped visible copy for Local Analytics and Analytics-hosted Data Sharing pages.
They are the Analytics equivalent of Local Studio UI-text bundles.

They do not own service endpoints, tag data schemas, Data Sharing adapter rules, or public route contracts.

## What Reads Them

Analytics frontend modules load the bundle URL configured in `analytics-app/app/frontend/config/analytics-config.json` under `paths.data.ui_text`.
The route then reads strings by scoped key with caller fallbacks.

Data Sharing prepare/review copy belongs here only for the Analytics-hosted route surface.
Adapter behavior, source-write policy, export profiles, and import review rules belong in `data-sharing/config/...` and the Data Sharing service modules.

## Edit Class

These files are maintainer-editable copy config.
Changing copy is low risk.
Changing keys requires updating the route module and its focused tests.

## Cleanup Review

For each bundle:

- verify the route remains active in `analytics-config.json`
- remove unused keys by searching route modules for the scoped key prefix
- keep Data Sharing operation copy separate from Data Sharing adapter capability config
- remove retired-route bundles only after route config and server exposure are retired

