---
doc_id: scripts-catalogue-write-server-operations
title: Catalogue Write Server Operations
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: scripts-catalogue-write-server
sort_order: 4300
---
# Catalogue Write Server Operations

## Module Ownership

- `scripts/catalogue/catalogue_write_server.py` owns HTTP transport, request parsing, endpoint-specific write allowlist checks before writes, source-write/build/refresh orchestration decisions, local service logging, Studio Activity append timing, and final response payload assembly.
- `scripts/catalogue/catalogue_source.py` owns canonical source field order, shared catalogue id-list and detail-uid normalization, source record normalization, and source validation.
- `scripts/catalogue/catalogue_routes.py` owns catalogue local-service endpoint path constants, the POST route inventory, and the CORS preflight route inventory shared by the write server and catalogue activity profiles.
- `scripts/catalogue/catalogue_activity.py` owns catalogue-specific Studio Activity profiles, activity context normalization, activity row construction, and activity response-count bookkeeping.
- `scripts/catalogue/catalogue_cleanup.py` owns generated public-artifact cleanup discovery, cleanup-scope allowlist checks, generated JSON cleanup payload mutation including moment index cleanup, and cleanup file deletion helpers used by delete and unpublish transactions.
- `scripts/catalogue/catalogue_delete_plans.py` owns delete preview construction, delete affected-record calculation, delete validation preflight, draft-series primary-work cleanup planning for work deletes, and delete apply plan construction.
- `scripts/catalogue/catalogue_invalidation.py` owns the remaining moment-build invalidation helper.
- `scripts/catalogue/catalogue_lookup_refresh.py` owns registry-derived Studio lookup refresh planning, full and focused lookup refresh execution, result payload shape, artifact labels, written counts, and written path reporting.
- `scripts/catalogue/catalogue_publication.py` owns publication preview planning, target-record normalization, publication blockers, affected-record calculation, build impact planning, series publish bootstrap planning, publication source payload construction, unpublish cleanup orchestration, and publication build backup orchestration.
- `scripts/catalogue/catalogue_prose_import.py` owns staged catalogue prose import target normalization, Markdown validation, preview payloads, and draft moment source import application helpers.
- `scripts/catalogue/catalogue_save_build.py` owns common save-time public-build response decisions for work, work-detail, series, and moment saves, including `build_requested`, `build_skipped`, no-public-artifact skip payloads, and the build runner call.
- `scripts/catalogue/catalogue_source_mutation.py` owns pure source mutation planning for save/create paths: source record normalization, changed-field calculation, source validation against already-loaded records, generated detail section-id planning, series member-work update planning, and source JSON payload construction without file writes.
- `scripts/catalogue/catalogue_transactions.py` owns source JSON write execution, source payload-map validation, timestamped backup names, backup path formatting for source-write responses, transaction backup copying, best-effort restore behavior, path de-duplication for transaction paths, atomic multi-file JSON writes with rollback, catalogue and moment cleanup transaction execution, and the no-backup atomic text write primitive used by prose imports.
- `scripts/catalogue/catalogue_lookup.py` owns construction and writing of derived Studio catalogue lookup payloads.
- `scripts/catalogue/catalogue_json_build.py` owns scoped public catalogue build planning and execution used by publication and build endpoints.
## Validation

The server validates the proposed update through the shared catalogue source loader and validator before writing. Validation checks the full catalogue source set, not only the submitted work record, so invalid series references are blocked before `works.json` is replaced.

## Security Constraints

- binds to `127.0.0.1` only
- CORS allows loopback origins only
- write target is allowlisted to canonical catalogue source JSON files under `assets/studio/data/catalogue/`
- current save endpoints write only canonical catalogue source JSON under `assets/studio/data/catalogue/`, including `works.json`, `work_details.json`, `series.json`, and `moments.json`
- standalone work-file and work-link write endpoints are retired; files and links are saved as work-owned metadata through `POST /catalogue/work/save`
- timestamped backup bundles are created under `var/studio/catalogue/backups/`
- event logs are written under `var/studio/catalogue/logs/`
- logs include IDs, changed fields, status, and error summaries only; they do not include full submitted records
- covered save, create, delete, publication, import, and report actions also update `var/studio/activity/activity_log.json` when valid Studio activity context is supplied

## Dev Studio

`bin/dev-studio` starts this service alongside Jekyll and the Tag Write Server.

Default local endpoint:

```text
http://127.0.0.1:8788
```

The port can be overridden for the dev launcher:

```bash
CATALOGUE_WRITE_PORT=8798 bin/dev-studio
```

## Source And Target Artifacts

Source JSON:

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`
- `assets/studio/data/catalogue/series.json`
- `assets/studio/data/catalogue/moments.json`
- `assets/studio/data/catalogue/meta.json`

Studio activity feed:

- `var/studio/activity/activity_log.json`

Backup target:

- `var/studio/catalogue/backups/`

Derived lookup target:

- `assets/studio/data/catalogue_lookup/`

Operational log target:

- `var/studio/catalogue/logs/catalogue_write_server.log`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Servers](/docs/?scope=studio&doc=servers)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
