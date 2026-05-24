---
doc_id: scripts-catalogue-write-server-operations
title: Catalogue Write Service Operations
added_date: 2026-05-19
last_updated: 2026-05-23
parent_id: scripts-catalogue-write-server
sort_order: 4300
---
# Catalogue Write Service Operations

## Module Ownership

- The retired `studio/services/catalogue/catalogue_write_server.py` wrapper no longer owns any Local Studio HTTP surface.
- `studio/app/server/studio/studio_catalogue_api.py` owns the active Local Studio `/studio/api/catalogue/...` HTTP surface and calls catalogue service functions directly.
- `studio/services/catalogue/catalogue_write_service.py` owns callable Local Studio catalogue route dispatch only.
  It maps `/studio/api/catalogue/...` service paths to focused workflow modules and preserves the shared `handle_catalogue_post(repo_root, api_path, body, dry_run=False)` boundary.
- `studio/services/catalogue/catalogue_service_context.py` owns shared Local Studio catalogue service context: source paths, lookup paths, write allowlists, backup paths, lookup refresh response helpers, compact service logging, and best-effort Studio Activity appends.
- `studio/services/catalogue/catalogue_bulk_service.py`, `studio/services/catalogue/catalogue_work_service.py`, `studio/services/catalogue/catalogue_work_detail_service.py`, and `studio/services/catalogue/catalogue_series_service.py` own the distinct bulk, create, and save workflows for works, work details, and series.
- `studio/services/catalogue/catalogue_build_service.py`, `studio/services/catalogue/catalogue_delete_service.py`, `studio/services/catalogue/catalogue_moment_service.py`, `studio/services/catalogue/catalogue_publication_service.py`, and `studio/services/catalogue/catalogue_prose_import_service.py` own scoped build, delete, moment, publication, and prose/moment import route behavior.
- [Catalogue Write Service Extraction](/docs/?scope=studio&doc=scripts-catalogue-write-service-extraction) records the service extraction and wrapper retirement.
- `studio/services/catalogue/catalogue_source.py` owns canonical source field order, shared catalogue id-list and detail-uid normalization, source record normalization, and source validation.
- `studio/services/catalogue/catalogue_routes.py` owns catalogue local-service endpoint path constants, the POST route inventory, and the CORS preflight route inventory shared by the write server and catalogue activity profiles.
- `studio/services/catalogue/catalogue_activity.py` owns catalogue-specific Studio Activity profiles, activity context normalization, activity row construction, and activity response-count bookkeeping.
- `studio/services/catalogue/catalogue_cleanup.py` owns generated public-artifact cleanup discovery, cleanup-scope allowlist checks, generated JSON cleanup payload mutation including moment index cleanup, and cleanup file deletion helpers used by delete and unpublish transactions.
- `studio/services/catalogue/catalogue_delete_plans.py` owns delete preview construction, delete affected-record calculation, delete validation preflight, draft-series primary-work cleanup planning for work deletes, and delete apply plan construction.
- `studio/services/catalogue/catalogue_invalidation.py` owns the remaining moment-build invalidation helper.
- `studio/services/catalogue/catalogue_lookup_refresh.py` owns registry-derived Studio lookup refresh planning, full and focused lookup refresh execution, result payload shape, artifact labels, written counts, and written path reporting.
- `studio/services/catalogue/catalogue_publication.py` owns publication preview planning, target-record normalization, publication blockers, affected-record calculation, build impact planning, series publish bootstrap planning, publication source payload construction, unpublish cleanup orchestration, and publication build backup orchestration.
- `studio/services/catalogue/catalogue_prose_import.py` owns staged catalogue prose import target normalization, Markdown validation, preview payloads, and draft moment source import application helpers.
- `studio/services/catalogue/catalogue_save_build.py` owns common save-time public-build response decisions for work, work-detail, series, and moment saves, including `build_requested`, `build_skipped`, no-public-artifact skip payloads, and the build runner call.
- `studio/services/catalogue/catalogue_source_mutation.py` owns pure source mutation planning for save/create paths: source record normalization, changed-field calculation, source validation against already-loaded records, generated detail section-id planning, series member-work update planning, and source JSON payload construction without file writes.
- `studio/services/catalogue/catalogue_transactions.py` owns source JSON write execution, source payload-map validation, timestamped backup names, backup path formatting for source-write responses, transaction backup copying, best-effort restore behavior, path de-duplication for transaction paths, atomic multi-file JSON writes with rollback, catalogue and moment cleanup transaction execution, and the no-backup atomic text write primitive used by prose imports.
- `studio/services/catalogue/catalogue_lookup.py` owns construction and writing of derived Studio catalogue lookup payloads.
- `studio/services/catalogue/catalogue_json_build.py` owns scoped public catalogue build planning and execution used by publication and build endpoints.
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

`bin/local-studio` starts the Local Studio app server, which owns catalogue APIs at `/studio/api/catalogue/...`.
It no longer starts or offers a fallback flag for a standalone catalogue write server.

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

- `var/studio/catalogue/logs/catalogue_service_context.log`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Servers](/docs/?scope=studio&doc=servers)
- [Local Studio Server Architecture](/docs/?scope=studio&doc=local-studio-server-architecture)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
