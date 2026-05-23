---
doc_id: local-studio-server-architecture
title: Local Studio Server Architecture
added_date: 2026-04-17
last_updated: "2026-05-23"
parent_id: servers
sort_order: 1000
---
# Local Studio Server Architecture

## Current Position

Studio currently uses the local Studio app server as the normal HTTP owner for Studio routes and local APIs.
`bin/dev-studio` remains a bridge runner for everyday development and starts Jekyll plus the local Studio app server by default:

- `scripts/studio/studio_app_server.py`

`bin/local-studio` starts the same local Studio app path with Jekyll disabled.
Public Jekyll preview/build is explicit through `bin/public-site-preview` and `bin/public-site-build`.

Docs management, Data Sharing, Analytics tag APIs, Studio audit APIs, Project State report API, Thumbnail Quality preview API, catalogue reads, workbook import, catalogue editor mutations, and migrated Studio route shells are now owned by the local Studio app server.
The old standalone tag write server has been retired.
The old standalone Docs management server has been retired.
The old standalone catalogue write server has been retired.
The old standalone Audit Service HTTP wrapper has been retired; direct automation uses `scripts/studio/audit_runner.py`.

When docs live watching is enabled, the same runner also starts:

- `scripts/docs/docs_live_rebuild_watcher.py`

The current implementation is therefore an integrated local workflow with one normal local Studio HTTP process.
The important separation is module ownership, not process ownership.
The local app server owns loopback HTTP, route dispatch, runtime config, static asset serving, and Studio route shells.
Focused domain modules own write policy, validation, backups, activity rows, and result shaping.

Current boundaries:

- `scripts/studio/studio_app_server.py` owns the local HTTP process and request dispatch.
- `scripts/studio/studio_app_config.py` owns browser runtime config and service endpoint paths.
- `scripts/studio/studio_app_views.py` owns migrated Studio route shell rendering.
- `scripts/studio/studio_catalogue_api.py` owns `/studio/api/catalogue/...` adapter routing for catalogue reads, writes, reports, import, and thumbnail-quality refresh.
- `scripts/catalogue/catalogue_write_service.py` dispatches catalogue mutation/build/import routes to focused catalogue workflow modules.
- `scripts/studio/studio_docs_api.py` owns `/studio/api/docs/...` and delegates to focused Docs management service modules.
- `scripts/studio/studio_analytics_api.py` owns `/studio/api/analytics/...` for active tag read/write workflows.
- `scripts/studio/studio_audit_api.py` owns `/studio/api/audits/...` and keeps audit execution allowlisted.

Some migration work remains, but it is no longer about moving endpoint ownership off sibling localhost services.
Remaining work is mostly route-family cleanup, projection contracts, public/local boundary hardening, and direct launcher cleanup.

## Current Direction

The target shape is now mostly implemented: one local Studio server process with separate domain modules.

The target is not a pile of independent long-running servers, and it is not one large mixed script.
The intended shape is a single process with clear route modules and domain-specific write policies.

Current structure:

```text
scripts/studio/studio_app_server.py
scripts/studio/studio_app_config.py
scripts/studio/studio_app_views.py
scripts/studio/studio_catalogue_api.py
scripts/studio/studio_docs_api.py
scripts/studio/studio_analytics_api.py
scripts/studio/studio_audit_api.py
scripts/catalogue/catalogue_write_service.py
scripts/docs/docs_management_service.py
```

Current route namespaces:

```text
GET  /health
GET  /studio/
GET  /studio/runtime-config.json
GET  /studio/<route>/?mode=manage
GET  /docs/
GET  /studio/api/catalogue/health
GET  /studio/api/catalogue/read
POST /studio/api/catalogue/<workflow>
GET  /studio/api/docs/<workflow>
POST /studio/api/docs/<workflow>
GET  /studio/api/analytics/<workflow>
POST /studio/api/analytics/<workflow>
GET  /studio/api/audits/<workflow>
POST /studio/api/audits/<workflow>
```

## Write Policy

The local Studio app server must keep write authority domain-specific.

Analytics tag routes write only:

- `assets/studio/data/tag_assignments.json`
- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_aliases.json`
- Studio analytics backup and log paths

Catalogue routes write only through explicit service allowlists:

- canonical catalogue source JSON under `assets/studio/data/catalogue/`
- catalogue backup and log paths
- focused generated/public outputs when a scoped build, publication, delete, import, Project State, or Thumbnail Quality workflow explicitly owns them

Docs routes write only through Docs management mutation/import/rebuild services and their allowlisted paths.

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
- Docs management and Data Sharing use local Studio Docs APIs
- active analytics tag writes use local Studio analytics APIs
- Studio audit APIs are mounted in the local app
- catalogue reads, workbook import, editor writes, build, publication, delete, prose import, moment import, Project State, and Thumbnail Quality workflows use local Studio catalogue APIs
- catalogue handler-owned behavior has been extracted into callable service functions
- the standalone tag write, Docs management, and catalogue write servers have been retired
- `bin/dev-studio` starts only the local Studio app, optional Jekyll, optional Docs watcher, and optional startup rebuilds

Still in progress:

- finish retiring or replacing remaining Jekyll Studio route files as local route families are verified
- continue moving route state and cross-route data sharing from query-string compatibility toward explicit projection contracts
- keep separating public-site preview/build commands from Local Studio workflows
- extract shared localhost helpers only where contracts are identical across domains

Future local features should be added as route modules or focused service modules under the local Studio app, not as new standalone localhost processes.

## Benefits

- fewer ports to manage in normal development
- one local app runtime-config endpoint for Studio pages
- one loopback HTTP process for active Studio APIs
- one place for route shell and service endpoint discovery
- simpler `bin/dev-studio` process management
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
