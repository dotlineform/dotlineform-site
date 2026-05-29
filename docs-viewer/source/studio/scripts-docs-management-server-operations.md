---
doc_id: scripts-docs-management-server-operations
title: Docs Management Service Operations
added_date: 2026-05-19
last_updated: 2026-05-23
parent_id: scripts-docs-management-server
---
# Docs Management Service Operations

## Security Constraints

- HTTP access is provided by the standalone Docs Viewer service at `DOCS_VIEWER_BASE_URL`
- loopback binding and CORS are enforced by `docs-viewer/services/docs_viewer_service.py`
- docs source write targets are allowlisted through `docs-viewer/config/scopes/docs_scopes.json`; in this repo the configured source roots are:
  - `docs-viewer/source/studio/*.md`
  - `docs-viewer/source/analysis/**/*.md`
  - `docs-viewer/source/library/*.md`
- non-source write targets are allowlisted to:
  - `var/docs/backups/`
  - `var/studio/data-sharing/<data-domain>/exports/`
  - `var/studio/data-sharing/<data-domain>/import-preview/`
  - `var/docs/logs/`
  - `var/docs/watch-suppressions/`
- scope lifecycle ownership is recorded in `docs-viewer/config/scopes/docs_scope_manifest.json`; existing scopes are system-owned and not eligible for lifecycle deletion
- scope create apply creates a backup bundle for the previous scope config and manifest files before writing
- scope delete apply creates a backup bundle for the previous scope config and manifest files before deleting or changing scope lifecycle state
- timestamped backup bundles are created under `var/docs/backups/` before each non-dry-run write batch
- backups are operation-scoped rather than full-scope:
  - `create` writes a manifest-only backup bundle
  - `delete` backs up only the deleted doc before removal

## Operational Notes

- normal `bin/local-studio` renders configured Docs Viewer links but does not host Docs Viewer management
- shared Docs management dispatch lives in `docs-viewer/services/docs_management_service.py`; workflow behavior is split into focused `docs_management_*_service.py` modules for context, reads, capabilities, source mutations, imports, Data Sharing, source opening, and broken-links audit
- the old standalone Docs Management HTTP server and `127.0.0.1:8789` fallback have been removed
- the shared Docs Viewer probes `GET /capabilities` for generated-data reads on normal local loads and for write capability when `?mode=manage` is present
- if the local service is unavailable, the viewer falls back to static generated JSON for normal public-style reads; manage mode stays read-only and shows a manage-mode unavailable message
- successful source writes leave short-lived suppression markers under `var/docs/watch-suppressions/` so the docs live watcher can skip duplicate same-scope rebuilds for the exact files already rebuilt by the Docs management service
- `var/` is excluded from Jekyll because Docs Viewer management backups, logs, staged imports, and watcher-suppression markers are local operational files rather than publishable site input
- `docs-viewer/bin/docs-viewer` serves Docs Viewer management and generated docs/search reads without starting Jekyll

## Verification

Export/import adapter behavior is covered by focused checks:

- `docs-viewer/tests/python/test_docs_export.py` verifies the Library export engine and service-facing output contracts.
- `docs-viewer/tests/python/test_docs_import.py` verifies staged Library import parsing, preview rendering, and path allowlists.
- `docs-viewer/tests/python/test_docs_import_service.py` verifies Library import staged-file listing, preview dry-run/write behavior, summary apply, hierarchy apply, backups, and confirmation gates.
- `studio/tests/python/test_data_sharing_adapters.py` verifies active adapter resolution and future stub rejection.
- `docs-viewer/tests/python/test_docs_activity.py` verifies Docs Management Studio Activity helper suppression, record groups, source refs, and warning status behavior.
- `studio/tests/smoke/data_sharing_review.py` verifies the Studio Data Sharing review route, preview/apply UI flow with mocked service responses, unavailable-service state, and disabled future-adapter state. It starts a temporary Local Studio app by default.

The `docs` profile runs the parser, service, and adapter checks.
The `studio-smoke` profile builds a temporary site for module checks and runs Studio Data Sharing route smokes against the Local Studio host.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
