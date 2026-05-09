---
doc_id: local-studio-server-architecture
title: "Local Studio Server Architecture"
added_date: 2026-04-17
last_updated: "2026-05-09 21:45"
parent_id: servers
sort_order: 10
---

# Local Studio Server Architecture

## Current Position

Studio currently uses `bin/dev-studio` as the integrated local runner for everyday Studio development.
That runner starts Jekyll plus several separate localhost services:

- `scripts/analytics/tag_write_server.py`
- `scripts/catalogue/catalogue_write_server.py`
- `scripts/docs/docs_management_server.py`
- `scripts/studio/audit_service.py`

When docs live watching is enabled, the same runner also starts:

- `scripts/docs/docs_live_rebuild_watcher.py`

This means the current implementation is already an integrated local workflow, but not a combined server process.
Each local service still owns its own port, health surface, CORS handling, route set, logging, and write boundary.

That separation remains intentional for the current implementation phase.
The tag server is broad and stable.
The catalogue write service has grown into the active JSON-led catalogue source writer, but it still benefits from a narrow domain boundary.
The docs management server and audit service also have distinct safety profiles: docs management owns source-doc writes and generated docs reads, while the audit service runs only allowlisted local checks.

Keeping these services separate for now reduces regression risk:

- tag write behavior can remain unchanged
- catalogue source writes get their own explicit allowlist
- docs source writes and generated-data reads stay isolated from catalogue writes
- audit commands stay isolated from write endpoints
- backup, validation, and rebuild behavior can be tested within each domain before shared server infrastructure is introduced

The architecture described below is still the preferred development option for a future consolidation pass.
It should be treated as a deliberate refactor, not as a requirement for ordinary feature work.
Use the existing owning service for narrow tag, catalogue, docs, or audit changes.
Start the combined-server work when a new local capability would otherwise add another long-running server or duplicate loopback, CORS, health, logging, capability, backup, or write-allowlist logic.

## Target Direction

The long-term target should be one local Studio server process with separate domain modules.

The target is not a pile of independent long-running servers, and it is not one large mixed script. The intended shape is a single process with clear route modules and domain-specific write policies.

Possible future structure:

```text
scripts/studio/studio_local_server.py
scripts/studio/local_server_common.py
scripts/analytics/tag_routes.py
scripts/catalogue/catalogue_routes.py
scripts/studio/build_routes.py
scripts/studio/import_routes.py
```

Possible route namespaces:

```text
GET  /health
POST /tags/save
POST /tags/import-registry
POST /catalogue/work/save
POST /catalogue/work-detail/save
POST /catalogue/series/save
POST /catalogue/bulk-preview
POST /catalogue/bulk-apply
POST /catalogue/build-preview
POST /catalogue/build-apply
GET  /catalogue/activity
```

## Write Policy

A combined server must still keep write authority domain-specific.

Tag routes should only write:

- `assets/studio/data/tag_assignments.json`
- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_aliases.json`
- tag-server backup and log paths

Catalogue routes should only write:

- canonical catalogue source JSON under `assets/studio/data/catalogue/`
- catalogue backup and log paths

Build routes should only invoke allowlisted local commands and write their documented generated outputs.

Import routes should keep preview and apply separate. Apply endpoints should use narrow allowlists, validation, backup bundles, and operation summaries.

## Shared Infrastructure

The eventual combined server should share:

- loopback binding
- CORS validation
- JSON request parsing
- response helpers
- request size limits
- stale-version or hash checks
- backup helpers
- minimal JSONL logging
- health and capability reporting

Shared helpers should not erase domain boundaries. Each route module should still define its own allowed files, validation rules, and operation summaries.

## Migration Path

Recommended path:

1. Keep the Tag Write Server and Catalogue Write Server separate while the first catalogue editor work is implemented.
2. Extract shared localhost server helpers after both services have stable behavior.
3. Add `scripts/studio/studio_local_server.py` as the combined process.
4. Keep the existing tag and catalogue server scripts as compatibility launchers for a transition period.
5. Move `bin/dev-studio` to start the combined server.
6. Add future local-server requirements as route modules under the combined server rather than as new standalone processes.

This lets future local features reuse the same server surface while preserving explicit write boundaries.

## Benefits

- fewer ports to manage
- one health and capability endpoint for Studio pages
- one CORS and loopback implementation
- one logging and backup pattern
- simpler `bin/dev-studio` process management
- easier service discovery for future Studio pages

## Risks

- merging too early can regress working tag flows
- a combined server can become too broad if route modules do not keep strict write policies
- future build endpoints may need stronger guardrails than simple JSON save endpoints

Mitigation:

- keep route modules domain-specific
- keep write allowlists local to each domain
- keep preview/apply split for destructive or multi-record operations
- preserve compatibility launchers during migration
