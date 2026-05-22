---
doc_id: scripts-docs-management-server-operations
title: Docs Management Server Operations
added_date: 2026-05-19
last_updated: 2026-05-22
parent_id: scripts-docs-management-server
sort_order: 15500
---
# Docs Management Server Operations

## Security Constraints

- binds to loopback only
- CORS allows loopback origins only
- docs source write targets are allowlisted through `scripts/docs/docs_scopes.json`; in this repo the configured source roots are:
  - `_docs/*.md`
  - `_docs_analysis/**/*.md`
  - `_docs_library/*.md`
- non-source write targets are allowlisted to:
  - `var/docs/backups/`
  - `var/studio/data-sharing/<data-domain>/exports/`
  - `var/studio/data-sharing/<data-domain>/import-preview/`
  - `var/docs/logs/`
  - `var/docs/watch-suppressions/`
- scope lifecycle ownership is recorded in `scripts/docs/docs_scope_manifest.json`; existing scopes are system-owned and not eligible for lifecycle deletion
- scope create apply creates a backup bundle for the previous scope config and manifest files before writing
- scope delete apply creates a backup bundle for the previous scope config and manifest files before deleting or changing scope lifecycle state
- timestamped backup bundles are created under `var/docs/backups/` before each non-dry-run write batch
- backups are operation-scoped rather than full-scope:
  - `create` writes a manifest-only backup bundle
  - `archive` backs up only the touched doc before rewrite
  - `delete` backs up only the deleted doc before removal

## Operational Notes

- normal `bin/dev-studio` runs host Docs Viewer management through the Local Studio App, not this standalone server
- set `DOCS_MANAGEMENT_SERVER_ENABLED=1` only for fallback/debug runs that intentionally need the standalone `http://127.0.0.1:8789` process
- standalone local management experiments can start with `./scripts/docs/docs_management_server.py --port 8789`
- the shared Docs Viewer probes `GET /capabilities` for generated-data reads on normal local loads and for write capability when `?mode=manage` is present
- if the local service is unavailable, the viewer falls back to static generated JSON for normal public-style reads; manage mode stays read-only and shows a manage-mode unavailable message
- successful source writes now leave short-lived suppression markers under `var/docs/watch-suppressions/` so the docs live watcher can skip duplicate same-scope rebuilds for the exact files already rebuilt by the server
- `var/` is excluded from Jekyll because docs-management backups, logs, staged imports, and watcher-suppression markers are local operational files rather than publishable site input
- `bin/dev-studio` also uses a local-only Jekyll overlay so generated docs/search JSON can be read from this server without making Jekyll watch those generated files

## Verification

Export/import adapter behavior is covered by focused checks:

- `tests/python/test_docs_export.py` verifies the Library export engine and service-facing output contracts.
- `tests/python/test_docs_import.py` verifies staged Library import parsing, preview rendering, and path allowlists.
- `tests/python/test_docs_import_service.py` verifies Library import staged-file listing, preview dry-run/write behavior, summary apply, hierarchy apply, backups, and confirmation gates.
- `tests/python/test_data_sharing_adapters.py` verifies active adapter resolution and future stub rejection.
- `tests/python/test_docs_activity.py` verifies Docs Management Studio Activity helper suppression, record groups, source refs, and warning status behavior.
- `tests/smoke/data_sharing_review.py` verifies the Studio import route, preview/apply UI flow with mocked service responses, unavailable-service state, and disabled future-adapter state.

The `docs` profile runs the parser, service, and adapter checks.
The `studio-smoke` profile builds a temporary site and runs the Studio import route smokes.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
