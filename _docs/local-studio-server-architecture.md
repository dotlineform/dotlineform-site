---
doc_id: local-studio-server-architecture
title: Local Studio Server Architecture
added_date: 2026-04-17
last_updated: "2026-05-09 21:45"
parent_id: servers
sort_order: 1000
---
# Local Studio Server Architecture

## Current Position

Studio currently uses `bin/dev-studio` as the integrated local runner for everyday Studio development.
That runner starts Jekyll and the local Studio app server by default:

- `scripts/studio/studio_app_server.py`

It can still start the remaining separate catalogue localhost service when `CATALOGUE_WRITE_SERVER_ENABLED=1`:

- `scripts/catalogue/catalogue_write_server.py`

Docs management, Analytics tag APIs, Studio audit APIs, Project State report API, Thumbnail Quality preview API, catalogue reads, workbook import, and migrated catalogue editor mutations are now owned by the local Studio app server.
The old standalone tag write server has been retired.
The old standalone Docs management server has been retired.
The standalone Audit Service remains available only when explicitly enabled for fallback/debug use.

When docs live watching is enabled, the same runner also starts:

- `scripts/docs/docs_live_rebuild_watcher.py`

This means the current implementation is already an integrated local workflow, but not a combined server process.
The remaining separate catalogue service still owns its own port, health surface, CORS handling, route set, logging, and write boundary for compatibility/debug use.
The active local app still imports the old catalogue handler in-process for core editor mutations, so the next refactor is to extract those handler-owned behaviors into callable catalogue service functions.

That remaining separation is intentional for the current implementation phase.
The catalogue write service has grown into the active JSON-led catalogue source writer, but it still benefits from a narrow domain boundary.
The Project State report is the first narrow Catalogue API moved into the local Studio app because it writes only the fixed `_docs/project-state.md` report and does not expose general catalogue mutation.
Thumbnail Quality preview refresh is also local-app hosted because it writes only fixed preview assets under `assets/studio/img/thumbnail-quality/` and `assets/studio/data/thumbnail_quality_preview.json`.
The audit runner still has a distinct safety profile because it runs only allowlisted local checks, but its active HTTP ownership now sits inside the local Studio app.

Keeping these services separate for now reduces regression risk:

- migrated tag write behavior stays inside the local Studio app server and its analytics module
- migrated Project State report behavior stays inside a narrow local Studio app catalogue adapter
- migrated Thumbnail Quality refresh behavior stays inside the same narrow local Studio app catalogue adapter
- catalogue source writes get their own explicit allowlist
- docs source writes and generated-data reads stay isolated from catalogue writes through the local Studio app's Docs module
- audit commands stay allowlisted inside a dedicated local app API adapter
- backup, validation, and rebuild behavior can be tested within each domain before shared server infrastructure is introduced

The architecture described below is still the preferred development option for a future consolidation pass.
It should be treated as a deliberate refactor, not as a requirement for ordinary feature work.
Use the existing owning module/service for narrow tag, catalogue, docs, or audit changes.
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
- Studio analytics backup and log paths

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

1. Keep migrating route families into the local Studio app server by domain module.
2. Extract callable service functions for remaining catalogue handler-owned behavior, then decide whether the standalone catalogue and audit wrappers still have a real audience.
3. Extract shared localhost server helpers only where contracts are identical.
4. Move `bin/dev-studio` to start only the local Studio app plus genuinely required background processes.
5. Add future local-server requirements as route modules under the local Studio app rather than as new standalone processes.

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
- preserve compatibility launchers only where an unmigrated workflow still requires them
