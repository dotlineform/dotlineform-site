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

Current Data Sharing route ownership is split:

- Studio owns the page shells at `/studio/data-sharing/prepare/?mode=manage` and `/studio/data-sharing/review/?mode=manage`.
- Studio browser modules load adapter config directly from `studio/data/config/data-sharing/`.
- Studio runtime config publishes Docs Viewer service URLs under `app.runtime.services.docs`.
- Browser Data Sharing health, generated-docs index, prepare, returned-package listing, review, and apply calls use those Docs Viewer URLs.
- Docs Viewer hosts the `/data-sharing/...` HTTP endpoints and delegates to Studio's shared dispatch modules.
- Studio's shared dispatch modules resolve adapters from `studio/data/config/data-sharing/data-sharing-adapters.json`.
- The documents adapter lives in `data-sharing/data_sharing/adapters/documents/` and calls docs-domain helpers in `docs-viewer/services/docs_data_sharing/`.
- The tags adapter lives in `data-sharing/data_sharing/adapters/tags/` and calls Analytics tag helpers for validation, backups, writes, and activity.
- The tracked top-level `data-sharing/` subsystem owns shared workflow dispatch, adapter implementations, and config.

The current browser-to-write path is:

```text
Studio page
-> studio/app/frontend/js/studio-transport.js
-> DOCS_VIEWER_BASE_URL /data-sharing/...
-> docs-viewer/services/docs_viewer_service.py
-> docs-viewer/services/docs_management_*_service.py
-> data-sharing/data_sharing/workflows/*
-> adapter handler from docs_management_data_sharing_service.py
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
2. It loads the adapter registry from `paths.data.studio.data_sharing_adapters`, falling back to `/studio/data/config/data-sharing/data-sharing-adapters.json`.
3. It derives scopes and prepare capability metadata with `data-sharing-adapters.js`.
4. If capability profiles are not embedded, it loads Library export config from `paths.data.studio.library_export_configs`, falling back to `/studio/data/config/data-sharing/library-export-configs.json`.
5. `data-sharing-prepare-docs.js` loads selectable documents by reading either:
   - `DATA_SHARING_ENDPOINTS.generatedIndex` with `scope=<scope>` when Docs Viewer service health passes, or
   - the static generated docs index path from Studio config when service health fails.
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

- `studio-transport.js` defaults Data Sharing endpoints to `http://127.0.0.1:8776`.
- `configureStudioTransport` rewrites Data Sharing endpoints from `app.runtime.services.docs`.
- Prepare-page document selection is built from a generated docs index, not from an adapter-owned selectable-record response.
- User-facing unavailable-service copy still names Docs Viewer service startup.

## Runtime Config

`studio/app/server/studio/studio_app_config.py` exposes:

- Studio page views for `data_sharing_prepare` and `data_sharing_review`.
- `app.runtime.services.docs`, populated by `docs_viewer_service_endpoints(repo_root)`.
- Docs Viewer-derived Data Sharing endpoint keys:
  - `data_sharing_prepare`
  - `data_sharing_returned_packages`
  - `data_sharing_review`
  - `data_sharing_apply`
- `generated_index`, also under `app.runtime.services.docs`.

`studio/app/server/studio/studio_docs_viewer_integration.py` resolves `DOCS_VIEWER_BASE_URL` from `var/local/site.env` or environment, validates that it is an HTTP loopback URL, and publishes:

- `<base>/health`
- `<base>/docs/generated/index`
- `<base>/data-sharing/prepare`
- `<base>/data-sharing/returned-packages`
- `<base>/data-sharing/review`
- `<base>/data-sharing/apply`

Current tests assert this publication in `studio/tests/python/test_studio_app_server.py`.
Future runtime config tests need to invert that contract so Data Sharing endpoints no longer live under `app.runtime.services.docs`.

## Service Endpoints

Endpoint constants live in `studio/app/server/studio/data_sharing_routes.py`:

- `GET /data-sharing/returned-packages`
- `POST /data-sharing/prepare`
- `POST /data-sharing/review`
- `POST /data-sharing/apply`

Docs Viewer mounts those constants in `docs-viewer/services/docs_viewer_service.py`.
GET requests dispatch through `docs_management_read_service.docs_management_get_payload`.
POST requests dispatch through `docs_management_service.docs_management_post_response`.

Current dispatch:

- `GET /data-sharing/returned-packages` -> `data_sharing_service.list_returned_packages(...)`
- `POST /data-sharing/prepare` -> `data_sharing_service.prepare_package(...)` and `docs_activity.maybe_attach_docs_export_activity(...)`
- `POST /data-sharing/review` -> `data_sharing_service.review_returned_package(...)`
- `POST /data-sharing/apply` -> `data_sharing_service.apply_returned_changes(...)` and `docs_activity.maybe_attach_documents_import_apply_activity(...)`

Docs Viewer local-origin enforcement and CORS still guard the POST and OPTIONS paths.
Studio does not currently expose same-origin `/studio/api/data-sharing/...` endpoints.

## Dispatch And Registry

Shared dispatch modules currently live under `studio/app/server/studio/`:

- `data_sharing_adapters.py`
- `data_sharing_service.py`
- `data_sharing_routes.py`

`data_sharing_adapters.py` owns:

- registry path `studio/data/config/data-sharing/data-sharing-adapters.json`
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

Handler registration currently lives in `docs-viewer/services/docs_management_data_sharing_service.py`:

- module `documents` -> `data-sharing/data_sharing/adapters/documents/adapter.py`
- module `analytics.tags` -> `data-sharing/data_sharing/adapters/tags/adapter.py`

The shared workflow dispatch is Data Sharing-owned. The Docs Viewer and Studio services still assemble concrete handler maps for their current local API entry points.

## Config Reads

Current config files:

- `studio/data/config/data-sharing/data-sharing-adapters.json`
- `studio/data/config/data-sharing/data-sharing-adapters.schema.json`
- `studio/data/config/data-sharing/library-export-configs.json`

Browser config reads:

- `studio/app/frontend/config/studio-config.json` maps `paths.data.studio.data_sharing_adapters` to `/studio/data/config/data-sharing/data-sharing-adapters.json`.
- The same config maps `paths.data.studio.library_export_configs` to `/studio/data/config/data-sharing/library-export-configs.json`.
- Prepare and review pages fetch the adapter registry directly.
- Prepare fetches Library export config directly when capability profiles are not embedded.

Server config reads:

- `data_sharing_adapters.py` reads `data-sharing/config/adapters.json`.
- `docs_data_sharing.package` reads the configured Library sharing profiles from `data-sharing/config/library-export-configs.json`.
- The documents adapter passes `adapter.config_path("sharing_profiles_path")` into docs-domain package helpers.
- The tags adapter derives profiles from adapter capability metadata and path contracts.

Migration pressure points:

- Registry/config ownership needs to move before both browser and server readers can converge on `data-sharing/config/`.
- Browser modules should stop reading registry/config files as endpoint ownership signals.
- Library profile config path appears in source config, tests, and fixture builders.

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

Those are assembled by `docs_management_data_sharing_service.documents_data_sharing_dependencies()` using:

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

- default config path `studio/data/config/data-sharing/library-export-configs.json`
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
`docs-viewer/services/docs_activity.py` attaches document export/apply activity after Docs Viewer service dispatch returns a successful payload.

Migration pressure points:

- `docs_export.py`, `docs_import.py`, backup, activity, and rebuild helpers are callable modules, but they are still grouped around Docs Viewer service concerns.
- The target implementation should separate docs-domain helper modules from Docs Viewer HTTP/service wrapper modules before moving the documents adapter.

## Test Coverage

Focused Python coverage:

- `studio/tests/python/test_data_sharing_adapters.py` validates registry schema, canonical operations, active/stub status behavior, safe paths, repo registry loading, and document/tags resolution.
- `studio/tests/python/test_data_sharing_service.py` validates neutral `/data-sharing/...` path constants and shared handler dispatch.
- `studio/tests/python/test_studio_app_server.py` currently asserts Data Sharing endpoints are published under `runtime.services.docs`.
- `docs-viewer/tests/python/test_docs_export.py` covers Library export config validation, document selection, deterministic output, format overrides, and output paths under `var/studio/data-sharing/library/exports`.
- `docs-viewer/tests/python/test_docs_import_service.py` directly exercises documents adapter prepare/list/review/apply helpers, backup creation, source writes, and hierarchy/summary apply planning.
- `studio/tests/python/test_tags_data_sharing_adapter.py` covers tags package preparation, returned package listing, review, apply, backups, and activity grouping.

Smoke coverage:

- `studio/tests/smoke/local_studio_app_data_sharing_routes.py` serves Studio and mocks Docs Viewer `/health`, `/docs/generated/index`, and `/data-sharing/...` calls.
- `studio/tests/smoke/data_sharing_prepare.py` mocks `/health`, `/docs/generated/index`, and `/data-sharing/prepare`.
- `studio/tests/smoke/data_sharing_review.py` mocks `/health`, `/data-sharing/returned-packages`, `/data-sharing/review`, and `/data-sharing/apply`.
- `studio/tests/smoke/data_sharing_prepare_modules.py` imports prepare workflow/render/service browser modules and intercepts `**/data-sharing/prepare`.
- `studio/tests/smoke/data_sharing_review_workflow_modules.py` imports review workflow modules and validates apply action projection and selection behavior.

Coverage gaps for the target architecture:

- No test currently asserts same-origin `/studio/api/data-sharing/...` endpoints.
- No adapter-owned selectable-record API test exists.
- Existing runtime config tests assert the old Docs Viewer publication contract.
- Existing browser smokes mock Docs Viewer endpoints rather than Studio Data Sharing endpoints.
- Existing documents adapter tests still build fixture registry/config paths under `studio/data/config/data-sharing/`.

## Migration Checklist From Inventory

Use this call graph inventory to drive the next tasks:

- Create `data-sharing/` as a headless package before moving registry/config and adapters.
- Move registry/config readers from `studio/data/config/data-sharing/` to `data-sharing/config/` without old-path compatibility reads.
- Add Studio-owned `/studio/api/data-sharing/...` endpoints before changing browser transport.
- Add an adapter selectable-record operation before removing generated-docs-index selection from the prepare page.
- Move shared workflow dispatch out of `studio/app/server/studio/`.
- Keep docs-domain helper calls direct, but extract them away from Docs Viewer HTTP wrappers.
- Keep documents and tags adapters at the same `data-sharing/` adapter boundary.
- Update runtime config tests and browser smokes as endpoint ownership changes.
