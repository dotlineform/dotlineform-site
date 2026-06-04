---
doc_id: analytics-tag-services
title: Tag Services
added_date: 2026-06-02
last_updated: 2026-06-02
parent_id: analytics
---
# Tag Services

Tag write routes run through the standalone Local Analytics app server:

- API module: `analytics-app/app/server/analytics_app/analytics_api.py`
- route constants: `analytics-app/app/server/analytics_app/tag_services/tag_routes.py`
- local API base: `/analytics/api`
- operational log: `var/studio/logs/analytics_app.log`

Reusable analytics owners:

- `analytics-app/app/server/analytics_app/tag_services/tag_activity.py`
- `analytics-app/app/server/analytics_app/tag_services/tag_source_paths.py`
- `analytics-app/app/server/analytics_app/tag_services/tag_source_model.py`
- `analytics-app/app/server/analytics_app/tag_services/tag_assignment_service.py`
- `analytics-app/app/server/analytics_app/tag_services/tag_registry_mutations.py`
- `analytics-app/app/server/analytics_app/tag_services/tag_alias_mutations.py`
- `analytics-app/app/server/analytics_app/tag_services/tag_promotion_mutations.py`
- `analytics-app/app/server/analytics_app/tag_services/tag_write_transactions.py`

## Active Endpoints

The Local Analytics app exposes these tag write endpoints under `/analytics/api`:

- `POST /save-tags`
- `POST /import-tag-registry`
- `POST /import-tag-aliases`
- `POST /delete-tag-alias`
- `POST /mutate-tag-alias-preview`
- `POST /mutate-tag-alias`
- `POST /promote-tag-alias-preview`
- `POST /promote-tag-alias`
- `POST /import-tag-assignments-preview`
- `POST /import-tag-assignments`
- `POST /demote-tag-preview`
- `POST /demote-tag`
- `POST /mutate-tag-preview`
- `POST /mutate-tag`

## Write Policy

Tag writes are allowlisted to:

- `analytics-app/data/canonical/tag-assignments.json`
- `analytics-app/data/canonical/tag-registry.json`
- `analytics-app/data/canonical/tag-aliases.json`

Writes use atomic replacement and in-process rollback without writing backup files.
Unified activity rows are written through `studio/shared/python/studio_activity.py`.