---
doc_id: local-studio-server-architecture
title: Local Studio Server Architecture
added_date: 2026-04-17
last_updated: 2026-05-30
parent_id: servers
---
# Local Studio Server Architecture

## Current Position

Studio currently uses the local Studio app server as the normal HTTP owner for Studio catalogue, audit, activity, admin, and operational local APIs.
`bin/local-studio` is the normal Studio runner and starts the local Studio app server:

- `studio/app/server/studio/studio_app_server.py`

Public Jekyll preview/build is explicit through `bin/public-site-preview` and `bin/public-site-build`.

Analytics tag APIs and Data Sharing APIs are owned by the standalone Local Analytics app.
Studio audit APIs, Project State report API, catalogue reads, workbook import, catalogue editor mutations, and migrated Studio route shells are owned by the local Studio app server.
Docs Viewer management, generated reads, and Docs source opening are owned by the standalone Docs Viewer service.
Local Studio links to Docs Viewer through plain external-link config; it does not publish Docs Viewer service endpoints.
The old standalone tag write server has been retired.
The old standalone Docs management server has been retired.
The old standalone catalogue write server has been retired.
The old standalone Audit Service HTTP wrapper has been retired; direct automation uses `studio/app/server/studio/audit_runner.py`.

When docs live watching is enabled, the same runner also starts:

- `docs-viewer/services/docs_live_rebuild_watcher.py`

The current implementation is therefore a split local workflow: public preview, Local Studio, Local Analytics, UI Catalogue, and Docs Viewer are peer services.
The important separation is service and module ownership.
The local app server owns loopback HTTP, route dispatch, runtime config, static asset serving, and Studio route shells.
Focused domain modules own write policy, validation, backups, activity rows, and result shaping.

Current boundaries:

- `studio/app/server/studio/studio_app_server.py` owns the local HTTP process and request dispatch.
- `studio/app/server/studio/studio_app_config.py` owns browser runtime config, service endpoint paths, and plain Docs Viewer link assembly from `external_links.docs_viewer`.
- `studio/app/server/studio/studio_app_views.py` owns migrated Studio route shell rendering.
- `studio/app/server/studio/studio_catalogue_api.py` owns `/studio/api/catalogue/...` adapter routing for catalogue reads, writes, reports, and import.
- `studio/services/catalogue/catalogue_write_service.py` dispatches catalogue mutation/build/import routes to focused catalogue workflow modules.
- `studio/app/server/studio/studio_audit_api.py` owns `/studio/api/audits/...` and keeps audit execution allowlisted.
- `analytics-app/app/server/analytics_app/analytics_app_server.py` owns the Local Analytics HTTP process and request dispatch.
- `analytics-app/app/server/analytics_app/analytics_api.py` owns `/analytics/api/...` for active tag read/write workflows.
- `analytics-app/app/server/analytics_app/analytics_data_sharing_api.py` owns `/analytics/api/data-sharing/...` for Data Sharing health, selectable records, package preparation, returned-package listing, review, and apply.

Some migration work remains, but it is no longer about merging endpoint ownership into one localhost service.
Remaining work is mostly route-family cleanup, projection contracts, public/local boundary hardening, and direct launcher cleanup.

## Current Direction

The target shape is now mostly implemented: peer public preview, Local Studio, Local Analytics, UI Catalogue, and Docs Viewer services with separate domain modules.

The target is not one large mixed script.
The intended shape is independent services with clear route modules and domain-specific write policies.

Current structure:

```text
studio/app/server/studio/studio_app_server.py
studio/app/server/studio/studio_app_config.py
studio/app/server/studio/studio_app_views.py
studio/app/server/studio/studio_catalogue_api.py
studio/app/server/studio/studio_audit_api.py
studio/services/catalogue/catalogue_write_service.py
analytics-app/app/server/analytics_app/analytics_app_server.py
analytics-app/app/server/analytics_app/analytics_api.py
analytics-app/app/server/analytics_app/analytics_data_sharing_api.py
docs-viewer/services/docs_viewer_service.py
docs-viewer/services/docs_management_service.py
```

Current route namespaces:

```text
GET  /health
GET  /studio/
GET  /studio/runtime-config.json
GET  /studio/<route>/?mode=manage
GET  /studio/api/catalogue/health
GET  /studio/api/catalogue/read
POST /studio/api/catalogue/<workflow>
GET  /studio/api/audits/<workflow>
POST /studio/api/audits/<workflow>
```

Analytics routes are served by the external Analytics app, not Local Studio:

```text
GET  /analytics/
GET  /analytics/<route>/
GET  /analytics/api/<workflow>
POST /analytics/api/<workflow>
GET  /analytics/api/data-sharing/<workflow>
POST /analytics/api/data-sharing/<workflow>
```

Docs Viewer routes are served by the external Docs Viewer app, not Local Studio:

```text
GET  <docs_viewer.base_url>/docs/
GET  <docs_viewer.base_url>/docs/<workflow>
POST <docs_viewer.base_url>/docs/<workflow>
```

## Write Policy

The local Studio app server must keep write authority domain-specific.

Analytics tag routes are owned by Local Analytics and write only:

- `analytics-app/data/canonical/tag-assignments.json`
- `analytics-app/data/canonical/tag-registry.json`
- `analytics-app/data/canonical/tag-aliases.json`
- `analytics-app/data/canonical/tag-groups.json`
- Analytics backup and compact log paths

Catalogue routes write only through explicit service allowlists:

- canonical catalogue source JSON under `studio/data/canonical/catalogue/`
- catalogue backup and log paths
- focused generated/public outputs when a scoped build, publication, delete, import, or Project State workflow explicitly owns them

Docs routes write only through the Docs Viewer service and its management mutation/import/rebuild services.
Data Sharing document writes are exposed through the Local Analytics Data Sharing API and remain docs-aware by delegating to document-domain helpers for validation, backups, source writes, and rebuild follow-through.

Audit routes run only allowlisted local checks.

Build routes invoke allowlisted local commands and write their documented generated outputs.

Import routes keep preview and apply separate.
Apply endpoints use narrow allowlists, validation, backup bundles, and operation summaries.

## Shared Infrastructure

The local Studio app server already shares:

- loopback binding
- CORS validation
- JSON request parsing
- response helpers
- request size limits
- runtime service endpoint discovery
- route shell rendering
- health reporting

Domain modules still own:

- stale-version, hash, or source-consistency checks where applicable
- backup helpers and backup destinations
- minimal JSONL logging
- capability details
- validation rules
- operation summaries

Shared helpers should not erase domain boundaries.
Each route module should still define its own allowed files, validation rules, and operation summaries.

## Migration Status

Implemented:

- route families have been migrating into the local Studio app server by domain module
- Docs management uses the standalone Docs Viewer service
- active analytics tag writes use Local Analytics APIs
- Studio audit APIs are mounted in the local app
- Analytics Data Sharing API endpoints are mounted in the Local Analytics app
- catalogue reads, workbook import, editor writes, build, publication, delete, prose import, moment import, and Project State workflows use local Studio catalogue APIs
- catalogue handler-owned behavior has been extracted into callable service functions
- the standalone tag write, Docs management, and catalogue write servers have been retired
- `bin/local-studio` starts only the local Studio app, optional Docs watcher, and Python startup maintenance tasks

Still in progress:

- finish retiring or replacing remaining Jekyll Studio route files as local route families are verified
- continue moving route state and cross-route data sharing from query-string compatibility toward explicit projection contracts
- keep separating public-site preview/build commands from Local Studio workflows
- keep retired Analytics/Data Sharing Studio paths unserved; do not add aliases, proxies, or dual-read/write fallbacks
- extract shared localhost helpers only where contracts are identical across domains

Future Studio features should be added as Studio route modules or focused Studio service modules.
Future Analytics, Docs Viewer, and UI Catalogue features should stay under their owning local app boundaries rather than being added back to Local Studio.

## Benefits

- fewer ports to manage in normal development
- one local app runtime-config endpoint for Studio pages
- one loopback HTTP process for active Studio APIs
- one place for route shell and service endpoint discovery
- simpler `bin/local-studio` process management
- easier service discovery for future Studio pages

## Risks

- the local app server can become too broad if route modules do not keep strict write policies
- shared helpers can accidentally widen write scope if domain allowlists are centralized too aggressively
- future build endpoints may need stronger guardrails than simple JSON save endpoints
- historical docs/tests can keep stale assumptions about retired sibling services unless updated with each migration slice

Mitigation:

- keep route modules domain-specific
- keep write allowlists local to each domain
- keep preview/apply split for destructive or multi-record operations
- preserve compatibility launchers only where an unmigrated workflow still requires them
- treat new local capabilities as additions to the local Studio app unless there is a clear process-isolation reason
