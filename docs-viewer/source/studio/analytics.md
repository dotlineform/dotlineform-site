---
doc_id: analytics
title: Analytics
added_date: "2026-05-06 18:19"
last_updated: 2026-05-30
parent_id: ""
---
# Analytics

Analytics is now a standalone local app boundary.
Run it with:

```bash
bin/local-analytics
```

Default local route:

- `http://127.0.0.1:8766/analytics/`

Analytics owns tag groups, tag registry, tag aliases, series tags, series tag editing, Data Sharing routes/APIs, semantic-reference maintenance, document analysis, and future visualisation workflows.
Retired Studio paths under `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, and `/studio/api/data-sharing/...` should not be recreated.

Current source boundary:

- `analytics-app/app/server/analytics_app/` owns the Local Analytics HTTP server, route views, runtime config projection, static serving, tag APIs, and Data Sharing API dispatch.
- `analytics-app/app/server/analytics_app/tag_services/` owns reusable tag-domain source path contracts, validation, planning, dry-run/write transactions, backups, route constants, and compact activity projection.
- `analytics-app/app/frontend/` owns Analytics browser modules, route modules, UI text, and runtime config.
- `analytics-app/app/assets/` owns Analytics-only CSS and route assets.
- `analytics-app/tests/` owns Analytics route/API smoke tests and focused Python endpoint tests.
- `studio/data/canonical/analytics/` remains the canonical tag source data path, but it is not a Studio route or API ownership claim.
- `data-sharing/` owns the headless Data Sharing registry, config, workflow dispatch, package I/O, and domain adapters used by Analytics.

[analysis](/analysis/) is the public-facing Docs Viewer for this data domain.
