---
doc_id: site-request-studio-data-sharing-call-graph-inventory
title: Studio Data Sharing Call Graph Inventory
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: in-progress
parent_id: site-request-studio-data-sharing-architecture
sort_order: 110
viewable: true
---
# Studio Data Sharing Call Graph Inventory

This inventory started as the current Data Sharing implementation before the architecture move in [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture).
It is kept current for moved ownership boundaries; implementation tasks should move code toward the target boundary rather than preserve older paths through compatibility shims.

## Summary

Current Data Sharing route ownership is split, with browser traffic now on the Studio-owned local API:

- Studio owns the page shells at `/studio/data-sharing/prepare/?mode=manage` and `/studio/data-sharing/review/?mode=manage`.
- Studio browser modules load adapter config directly from `data-sharing/config/`.
- Studio runtime config publishes same-origin Data Sharing URLs under `app.runtime.services.data_sharing`.
- Browser Data Sharing health, selectable-record, prepare, returned-package listing, review, and apply calls use `/studio/api/data-sharing/...`.
- Docs Viewer still hosts transitional `/data-sharing/...` HTTP endpoints for SDSA-013 cleanup, but Studio browser modules no longer use them.
- Studio's dispatch compatibility module resolves adapters from `data-sharing/config/adapters.json`.
- The documents adapter lives in `data-sharing/data_sharing/adapters/documents/` and calls docs-domain helpers in `docs-viewer/services/docs_data_sharing/`.
- The tags adapter lives in `data-sharing/data_sharing/adapters/tags/` and calls Analytics tag helpers for validation, backups, writes, and activity.
- The tracked top-level `data-sharing/` subsystem owns shared workflow dispatch, adapter implementations, and config.

The current browser-to-write path is:

```text
Studio page
-> studio/app/frontend/js/studio-transport.js
-> /studio/api/data-sharing/...
-> studio/app/server/studio/studio_app_server.py
-> studio/app/server/studio/studio_data_sharing_api.py
-> data-sharing/data_sharing/workflows/*
-> adapter handler from studio_data_sharing_api.py
-> documents or tags adapter
-> domain helper writes, backups, rebuilds, and activity
```

## Browser Modules

Main entrypoints:

- `studio/app/frontend/js/data-sharing-prepare.js`
- `studio/app/frontend/js/data-sharing-review.js`

Shared browser helpers:

- `studio/app/frontend/js/data-sharing-adapters.js`
- `studio/app/frontend/js/data-sharing-prepare-docs.js`
- `studio/app/frontend/js/data-sharing-prepare-render.js`
- `studio/app/frontend/js/data-sharing-prepare-service.js`
- `studio/app/frontend/js/data-sharing-prepare-workflow.js`
- `studio/app/frontend/js/data-sharing-review-apply.js`
- `studio/app/frontend/js/data-sharing-review-render.js`
- `studio/app/frontend/js/data-sharing-review-workflow.js`
- `studio/app/frontend/js/studio-transport.js`

Prepare boot flow:

1. `data-sharing-prepare.js` loads Studio config and calls `configureStudioTransport`.
2. It loads the adapter registry from `paths.data.studio.data_sharing_adapters`, falling back to `/data-sharing/config/adapters.json`.
3. It derives scopes and prepare capability metadata with `data-sharing-adapters.js`.
4. If capability profiles are not embedded, it loads Library export config from `paths.data.studio.library_export_configs`, falling back to `/data-sharing/config/library-export-configs.json`.
5. `data-sharing-prepare-docs.js` loads selectable records from `DATA_SHARING_ENDPOINTS.selectableRecords` with `data_domain=<scope>` when the Studio Data Sharing API health probe passes.
6. `data-sharing-prepare-service.js` posts prepare requests to `DATA_SHARING_ENDPOINTS.prepare`.

Review boot flow:

1. `data-sharing-review.js` loads Studio config and calls `configureStudioTransport`.
2. It loads the adapter registry from the same Studio config path/fallback.
3. It derives scopes from the `list_returned` capability and apply actions from the `apply` capability.
4. It probes `DATA_SHARING_ENDPOINTS.health`.
5. It lists returned packages with `GET DATA_SHARING_ENDPOINTS.returnedPackages?data_domain=<scope>`.
6. It posts review requests to `DATA_SHARING_ENDPOINTS.review`.
7. `data-sharing-review-apply.js` posts apply preflight and confirmed apply requests to `DATA_SHARING_ENDPOINTS.apply`.

Migration pressure points:

- SDSA-013 removed old Data Sharing endpoint keys from `app.runtime.services.docs`.
- SDSA-013 removed the transitional Docs Viewer `/data-sharing/...` HTTP endpoints.
- SDSA-014 removed the old `--mock-docs-service` and `--block-docs-service` Data Sharing smoke aliases.

## Runtime Config

`studio/app/server/studio/studio_app_config.py` exposes:

- Studio page views for `data_sharing_prepare` and `data_sharing_review`.
- `app.runtime.services.data_sharing`, populated by `studio_data_sharing_api.service_endpoints()`.
- Studio Data Sharing endpoint keys:
  - `health`
  - `selectable_records`
  - `returned_packages`
  - `prepare`
  - `review`
  - `apply`
- `app.runtime.services.docs`, populated by `docs_viewer_service_endpoints(repo_root)`, for Docs Viewer base, health, and generated-index reads only.

`studio/app/server/studio/studio_docs_viewer_integration.py` resolves `DOCS_VIEWER_BASE_URL` from `var/local/site.env` or environment, validates that it is an HTTP loopback URL, and publishes:

- `<base>/health`
- `<base>/docs/generated/index`

Current tests assert that Data Sharing endpoints no longer live under `app.runtime.services.docs`.

## Service Endpoints

Studio API endpoint constants live in `studio/app/server/studio/studio_data_sharing_api.py`:

- `GET /studio/api/data-sharing/health`
- `GET /studio/api/data-sharing/selectable-records`
- `GET /studio/api/data-sharing/returned-packages`
- `POST /studio/api/data-sharing/prepare`
- `POST /studio/api/data-sharing/review`
- `POST /studio/api/data-sharing/apply`

`studio/app/server/studio/studio_app_server.py` routes same-origin API requests to `studio_data_sharing_api.data_sharing_get_payload` and `studio_data_sharing_api.data_sharing_post_response`.

Current Studio dispatch:

- `GET /studio/api/data-sharing/health` -> Studio API health payload
- `GET /studio/api/data-sharing/selectable-records` -> `data_sharing_service.selectable_records(...)`
- `GET /studio/api/data-sharing/returned-packages` -> `data_sharing_service.list_returned_packages(...)`
- `POST /studio/api/data-sharing/prepare` -> `data_sharing_service.prepare_package(...)` and `docs_activity.maybe_attach_docs_export_activity(...)`
- `POST /studio/api/data-sharing/review` -> `data_sharing_service.review_returned_package(...)`
- `POST /studio/api/data-sharing/apply` -> `data_sharing_service.apply_returned_changes(...)` and `docs_activity.maybe_attach_documents_import_apply_activity(...)`

Studio local-origin enforcement guards `/studio/api/data-sharing/...` POST and OPTIONS paths with the other Studio write APIs.

## Dispatch And Registry

Shared dispatch modules currently live under `studio/app/server/studio/`:

- `data_sharing_adapters.py`
- `data_sharing_service.py`
- `data_sharing_routes.py`

`data_sharing_adapters.py` owns:

- registry path `data-sharing/config/adapters.json`
- schema version `data_sharing_adapters_v2`
- canonical operations: `prepare`, `list_returned`, `review`, `apply`
- allowed capability statuses: `active`, `planned`, `stub`, `disabled`
- safe relative path validation
- adapter resolution by `data_domain` and `operation`

`data_sharing_service.py` owns:

- `DataSharingAdapterHandlers`
- handler lookup by adapter module id
- `prepare_package`
- `list_returned_packages`
- `review_returned_package`
- `apply_returned_changes`

Handler registration lives in `studio/app/server/studio/studio_data_sharing_api.py`:

- module `documents` -> `data-sharing/data_sharing/adapters/documents/adapter.py`
- module `analytics.tags` -> `data-sharing/data_sharing/adapters/tags/adapter.py`

The shared workflow dispatch is Data Sharing-owned. The Studio service assembles the concrete handler map for the local API entry point.

## Config Reads

Current config files:

- `data-sharing/config/adapters.json`
- `data-sharing/config/adapters.schema.json`
- `data-sharing/config/library-export-configs.json`

Browser config reads:

- `studio/app/frontend/config/studio-config.json` maps `paths.data.studio.data_sharing_adapters` to `/data-sharing/config/adapters.json`.
- The same config maps `paths.data.studio.library_export_configs` to `/data-sharing/config/library-export-configs.json`.
- Prepare and review pages fetch the adapter registry directly.
- Prepare fetches Library export config directly when capability profiles are not embedded.

Server config reads:

- `data_sharing_adapters.py` reads `data-sharing/config/adapters.json`.
- `docs_data_sharing.package` reads the configured Library sharing profiles from `data-sharing/config/library-export-configs.json`.
- The documents adapter passes `adapter.config_path("sharing_profiles_path")` into docs-domain package helpers.
- The tags adapter derives profiles from adapter capability metadata and path contracts.

Migration pressure points:

- Browser modules still read the adapter registry and Library export profile config directly for page metadata. That is acceptable for this slice, but these reads must not be used as endpoint ownership signals.
- Some fixture builders and historical docs may still mention old `studio/data/config/data-sharing/` paths; current code should resolve through `data-sharing/config/`.

## Documents Adapter

Current module:

- `data-sharing/data_sharing/adapters/documents/adapter.py`

Imports and dependencies:

- `docs_data_sharing.apply`
- `docs_data_sharing.package`
- `docs_data_sharing.review`
- `docs_data_sharing.write`
- `docs_source_model`
- `studio.data_sharing_adapters.AdapterResolution`
- `data_sharing.services.dispatch.DataSharingAdapterHandlers`

Dependency injection comes from `DocumentsDataSharingDependencies`:

- `log_event`
- `make_backup_bundle`
- `perform_source_write_and_rebuild`

Those are assembled by `studio_data_sharing_api.documents_data_sharing_dependencies()` using:

- `docs_management_context.log_event`
- `docs_management_context.make_backup_bundle`
- `docs_write_rebuild.perform_source_write_and_rebuild`

Operation mapping:

- `prepare_package` resolves the documents adapter, normalizes scope from adapter metadata, validates `config_id`, parses selected `doc_ids`, and calls `docs_export.build_export`.
- `list_returned_packages` calls `docs_import.list_staged_import_files`.
- `review_returned_package` calls `docs_import.parse_staged_import` and `docs_import.render_markdown_previews`, then shapes `review_rows`.
- `apply_returned_changes` dispatches `summary_apply` or `hierarchy_apply`.
- `apply_summary_updates` and `apply_hierarchy_updates` parse staged imports, load source docs, plan front matter changes, create backups, write source Markdown, and call docs/search rebuild follow-through when confirmed.

Documents workflow roots currently resolve from the adapter registry:

- outbound packages: `var/studio/data-sharing/library/exports`
- returned package staging: `var/studio/data-sharing/library/import-staging`
- review output: `var/studio/data-sharing/library/import-preview`
- source root: `docs-viewer/source/library`
- backup root: `var/docs/backups`

The document adapter is the main place where docs-domain helper boundaries need to be made explicit before moving the adapter under `data-sharing/`.

## Tags Adapter

Current module:

- `data-sharing/data_sharing/adapters/tags/adapter.py`

Imports and dependencies:

- `analytics.tag_alias_mutations`
- `analytics.tag_assignment_service`
- `analytics.tag_registry_mutations`
- `analytics.tag_source_model`
- `analytics.tag_write_transactions`
- `studio_activity.append_studio_activity`
- `studio_activity.normalize_activity_context_from_contract`
- `studio_activity.studio_activity_entry`
- `studio.data_sharing_adapters.AdapterResolution`
- `studio.data_sharing_adapters.safe_relative_path`
- `data_sharing.services.dispatch.DataSharingAdapterHandlers`

Dependency injection comes from `TagsDataSharingDependencies`:

- `log_event`

Operation mapping:

- `prepare_package` builds tag registry, alias, assignment, or bundle packages and writes them under the outbound root when not dry-run.
- `list_returned_packages` scans the staging root for JSON and JSONL files.
- `review_returned_package` validates returned registry, alias, or assignment packages without writing.
- `apply_returned_changes` dispatches `registry_apply`, `aliases_apply`, or `assignments_apply`.
- Apply helpers use `tag_write_transactions.atomic_write_many` with adapter `backup_root`.
- Prepare/apply activity is appended directly through Studio activity helpers.

Tags workflow roots currently resolve from the adapter registry:

- outbound packages: `var/studio/data-sharing/tags/exports`
- returned package staging: `var/studio/data-sharing/tags/import-staging`
- review output: `var/studio/data-sharing/tags/import-preview`
- source root: `assets/studio/data`
- backup root: `var/studio/data-sharing/tags/backups`

The tags adapter avoids Docs Viewer domain logic and receives adapter resolution through the same Data Sharing workflow dispatch contract as the documents adapter.

## Docs Export And Import Helpers

`docs-viewer/services/docs_export.py` currently owns document outbound package generation:

- default config path `data-sharing/config/library-export-configs.json`
- output root `var/studio/data-sharing`
- generated docs index and payload reads
- config validation
- document selection expansion
- JSON and JSONL payload rendering
- output path safety under the configured root

`docs-viewer/services/docs_import.py` currently owns returned Library package parsing and preview generation:

- workflow root `var/studio/data-sharing`
- staging root `<workflow-root>/<scope>/import-staging`
- preview root `<workflow-root>/<scope>/import-preview`
- JSON and JSONL parsing
- source metadata extraction
- import type detection
- Markdown review preview rendering
- relationship-tree preview rendering

`docs-viewer/services/docs_write_rebuild.py` owns source-write follow-through:

- `perform_source_write_and_rebuild`
- `rebuild_scope_outputs`
- targeted docs/search rebuild behavior where possible
- full-scope fallback behavior where needed

`docs-viewer/services/docs_management_context.py` owns docs backup bundles and event logging used by the documents adapter.
`docs-viewer/services/docs_activity.py` attaches document export/apply activity after Studio or transitional Docs Viewer service dispatch returns a successful payload.

Migration pressure points:

- Documents package, review, apply planning, source write, backup, and rebuild behavior is now reachable through docs-domain helper modules under `docs-viewer/services/docs_data_sharing/`.
- Some lower-level CLI modules still live under Docs Viewer because the Library source and generated payloads remain docs-domain data.

## Test Coverage

Focused Python coverage:

- `studio/tests/python/test_data_sharing_adapters.py` validates registry schema, canonical operations, active/stub status behavior, safe paths, repo registry loading, and document/tags resolution.
- `studio/tests/python/test_data_sharing_service.py` validates neutral `/data-sharing/...` path constants and shared handler dispatch.
- `studio/tests/python/test_studio_app_server.py` currently asserts Data Sharing endpoints are published under both `runtime.services.data_sharing` and the legacy `runtime.services.docs` location.
- `docs-viewer/tests/python/test_docs_export.py` covers Library export config validation, document selection, deterministic output, format overrides, and output paths under `var/studio/data-sharing/library/exports`.
- `docs-viewer/tests/python/test_docs_import_service.py` directly exercises documents adapter prepare/list/review/apply helpers, backup creation, source writes, and hierarchy/summary apply planning.
- `studio/tests/python/test_tags_data_sharing_adapter.py` covers tags package preparation, returned package listing, review, apply, backups, and activity grouping.

Smoke coverage:

- `studio/tests/smoke/local_studio_app_data_sharing_routes.py` serves Studio and mocks `/studio/api/data-sharing/...` calls for health, selectable records, prepare, returned-package listing, and review.
- `studio/tests/smoke/data_sharing_prepare.py` starts a temporary Local Studio app by default and mocks or blocks `/studio/api/data-sharing/health`, `/studio/api/data-sharing/selectable-records`, and `/studio/api/data-sharing/prepare`.
- `studio/tests/smoke/data_sharing_review.py` starts a temporary Local Studio app by default and mocks or blocks `/studio/api/data-sharing/health`, `/studio/api/data-sharing/returned-packages`, `/studio/api/data-sharing/review`, and `/studio/api/data-sharing/apply`.
- `studio/tests/smoke/data_sharing_prepare_modules.py` imports prepare workflow/render/service browser modules and intercepts `**/studio/api/data-sharing/prepare`.
- `studio/tests/smoke/data_sharing_review_workflow_modules.py` imports review workflow modules and validates apply action projection and selection behavior.

Coverage gaps for the target architecture:

- SDSA-013 added runtime config assertions that Data Sharing endpoints no longer publish under `app.runtime.services.docs`.
- SDSA-013 added a Docs Management route assertion that `/data-sharing/...` endpoints are not published by Docs Viewer.

## Migration Checklist From Inventory

Use this call graph inventory to drive the next tasks:

- Keep Data Sharing endpoint publication out of `app.runtime.services.docs`.
- Keep transitional Docs Viewer `/data-sharing/...` service helpers retired.
- Keep browser smokes on same-origin `/studio/api/data-sharing/...` paths.
- Keep documents and tags adapters at the same `data-sharing/` adapter boundary.
- Update docs-log evidence as endpoint cleanup lands.
