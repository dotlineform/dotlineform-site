---
doc_id: scripts-tag-write-server
title: Retired Tag Write Server
added_date: 2026-03-31
last_updated: 2026-05-30
parent_id: servers
---
# Retired Tag Write Server

`studio/services/analytics/tag_write_server.py` has been retired.

Tag write routes now run through the standalone Local Analytics app server:

- API module: `analytics-app/app/server/analytics_app/analytics_api.py`
- route constants: `analytics-app/app/server/analytics_app/tag_services/tag_routes.py`
- local API base: `/analytics/api`
- operational log: `var/studio/logs/analytics_app.log`

The old standalone `127.0.0.1:8787` process is no longer started by local runners, and browser modules no longer include hardcoded fallback URLs for it.
Local Studio also no longer exposes tag write endpoints under `/studio/api/analytics`.
The deprecated tag-server `/build-docs` route was not migrated.
Docs rebuilds belong to the Docs management API.

Reusable analytics owners remain active:

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

Tag writes remain allowlisted to:

- `analytics-app/data/canonical/tag-assignments.json`
- `analytics-app/data/canonical/tag-registry.json`
- `analytics-app/data/canonical/tag-aliases.json`

Backups remain under `var/studio/backups/`.
Unified activity rows are written through `scripts/studio_activity.py`.

## Related References

- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Local Studio App Implementation Plan](/docs/?scope=studio&doc=local-studio-app-implementation-plan)
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
- [Servers](/docs/?scope=studio&doc=servers)
