---
doc_id: tag-groups
title: Tag Groups
added_date: 2026-03-31
last_updated: 2026-07-15
parent_id: analytics
---
# Tag Groups

## Capability

`/analytics/tag-groups/` is the read-only taxonomy reference. It shows the configured short and long description for each tag group in Analytics order.

It does not edit group identity or policy. Group descriptions come from `analytics-app/data/canonical/tag-groups.json`; group order and coverage participation come from `analytics-config.json`; allowed registry groups are enforced by registry policy/model validation.

## Execution Path

```text
tag-groups.html
  -> tag-groups.js
  -> analytics-data.js
  -> GET /analytics/api/tag-groups
  -> tag-groups.json
  + analysis.groups ordering from runtime config
```

The route has no commands and never sets busy. Its Analytics ready-state root moves to list or empty after load.

## Code Map

- template: `analytics-app/app/frontend/routes/tag-groups.html`
- controller: `analytics-app/app/frontend/js/tag-groups.js`
- shared selectors/styles: `analytics-ui.js`, `analytics.css`
- API read map: `analytics_api.py::READ_ENDPOINTS`
- canonical prose: `analytics-app/data/canonical/tag-groups.json`
- order/coverage policy: `analytics-config.json::analysis.groups`

## Change Method

- prose change: edit `tag-groups.json`;
- display order or coverage membership: edit Analytics config and scoring tests;
- new group identity: treat it as a registry-model change, then update descriptions, policy, UI/scoring assumptions, imports, and tests together.

Do not use this page as a second exhaustive list of group values. Current JSON and config show the exact set.
