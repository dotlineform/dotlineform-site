---
doc_id: scripts-tag-write-server
title: Retired Tag Write Server
added_date: 2026-03-31
last_updated: "2026-05-22"
parent_id: servers
---
# Retired Tag Write Server

`studio/services/analytics/tag_write_server.py` has been retired.

Tag write routes now run through the local Studio app server:

- API module: `studio/app/server/studio/studio_analytics_api.py`
- route constants: `studio/services/analytics/tag_routes.py`
- local API base: `/studio/api/analytics`
- operational log: `var/studio/logs/studio_analytics_api.log`

The old standalone `127.0.0.1:8787` process is no longer started by `bin/local-studio`, and browser modules no longer include hardcoded fallback URLs for it.
The deprecated tag-server `/build-docs` route was not migrated.
Docs rebuilds belong to the Docs management API.

Reusable analytics owners remain active:

- `studio/services/analytics/tag_activity.py`
- `studio/services/analytics/tag_source_model.py`
- `studio/services/analytics/tag_assignment_service.py`
- `studio/services/analytics/tag_registry_mutations.py`
- `studio/services/analytics/tag_alias_mutations.py`
- `studio/services/analytics/tag_promotion_mutations.py`
- `studio/services/analytics/tag_write_transactions.py`

## Active Endpoints

The local Studio app exposes these tag write endpoints under `/studio/api/analytics`:

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

- `assets/studio/data/tag_assignments.json`
- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_aliases.json`

Backups remain under `var/studio/backups/`.
Unified activity rows are written through `scripts/studio_activity.py`.

## Related References

- [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- [Local Studio App Implementation Plan](/docs/?scope=studio&doc=local-studio-app-implementation-plan)
- [Local Studio Runner](/docs/?scope=studio&doc=scripts-local-studio)
- [Servers](/docs/?scope=studio&doc=servers)
