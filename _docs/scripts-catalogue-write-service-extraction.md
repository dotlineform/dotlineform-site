---
doc_id: scripts-catalogue-write-service-extraction
title: Catalogue Write Service Extraction
added_date: 2026-05-22
last_updated: 2026-05-23
parent_id: scripts-catalogue-write-server
sort_order: 4400
---
# Catalogue Write Service Extraction

This is the follow-up map for reducing `scripts/catalogue/catalogue_write_server.py` without replacing one large server file with one large service file.

The target is a normal callable catalogue service boundary that Local Studio can use directly:

```python
handle_catalogue_post(repo_root, api_path, body, dry_run=False)
```

The target is not a wholesale move of `Handler` methods into a new class.

## Current Coupling

`scripts/studio/studio_catalogue_api.py` still imports `scripts/catalogue/catalogue_write_server.py` as `legacy_write_server`.
For the remaining core catalogue editor mutation routes, it creates an in-process fake `Handler` instance, attaches an `InProcessCatalogueServer`, replaces `_read_json_body`, captures `_send_json`, and invokes the legacy handler method.

That coupling means the HTTP server entrypoint is also the reusable behavior owner.
It keeps Local Studio dependent on the shape of `BaseHTTPRequestHandler` methods for the routes that have not yet moved to `scripts/catalogue/catalogue_write_service.py`.

## Already Local-App Native

These routes already have Local Studio API functions in `scripts/studio/studio_catalogue_api.py` and do not require the fake handler path:

| Route | Current owner | Notes |
| --- | --- | --- |
| `GET /studio/api/catalogue/read` | `catalogue_read_payload()` | Duplicates the standalone server read behavior in a direct function. |
| `POST /studio/api/catalogue/import-preview` | `import_preview_payload()` | Workbook import preview already calls the import planner directly. |
| `POST /studio/api/catalogue/import-apply` | `import_apply_response()` | Workbook import apply already calls the import planner/apply helpers and transaction writer directly. |
| `POST /studio/api/catalogue/project-state-report` | `project_state_report_payload()` | Project State report no longer needs the standalone catalogue server. |
| `POST /studio/api/catalogue/thumbnail-quality-preview` | `thumbnail_quality_preview_payload()` | Thumbnail Quality preview no longer needs the standalone catalogue server. |

These should not be re-migrated by copying their old handler implementations.
If a later service module is introduced, these direct functions can move or delegate to it deliberately.

## First Service Slice

`scripts/catalogue/catalogue_write_service.py` now owns the first low-risk service group:

| Route | Service function path | Notes |
| --- | --- | --- |
| `POST /studio/api/catalogue/delete-preview` | `handle_catalogue_post()` | Calls `catalogue_delete_plans.build_delete_preview()` directly. |
| `POST /studio/api/catalogue/build-preview` | `handle_catalogue_post()` | Builds the scoped preview through existing build-scope, field-plan, and media-plan helpers. |
| `POST /studio/api/catalogue/build-apply` | `handle_catalogue_post()` | Runs the scoped build helper directly and returns the same success/error status shape. |
| `POST /studio/api/catalogue/moment/preview` | `handle_catalogue_post()` | Calls moment metadata/source preview helpers directly. |
| `POST /studio/api/catalogue/prose/import-preview` | `handle_catalogue_post()` | Calls `catalogue_prose_import.build_prose_import_preview()` directly. |
| `POST /studio/api/catalogue/prose/import-apply` | `handle_catalogue_post()` | Calls `catalogue_prose_import.apply_prose_import()` directly. |
| `POST /studio/api/catalogue/moment/import-preview` | `handle_catalogue_post()` | Calls `catalogue_prose_import.build_moment_import_preview()` directly. |
| `POST /studio/api/catalogue/moment/import-apply` | `handle_catalogue_post()` | Calls `catalogue_prose_import.apply_moment_import()` directly and writes Studio Activity rows without constructing a fake HTTP handler. |

`publication-preview` intentionally stayed with the legacy publication group for now.
Although the handler method is thin, its `save_published` request extraction depends on the same record-update helpers as publication apply and the save handlers.
Move it with publication apply instead of duplicating the source-save extraction rules.

## Create Mutation Slice

`scripts/catalogue/catalogue_write_service.py` now also owns:

| Route | Service function path | Notes |
| --- | --- | --- |
| `POST /studio/api/catalogue/work/create` | `work_create_payload()` | Calls `catalogue_source_mutation.plan_work_create()`, writes through `catalogue_transactions.execute_source_json_write()`, refreshes lookups after real writes, and writes Studio Activity rows best-effort. |
| `POST /studio/api/catalogue/work-detail/create` | `work_detail_create_payload()` | Calls `catalogue_source_mutation.plan_work_detail_create()`, preserves parent-work validation and generated `section_id`, writes through the transaction helper, refreshes lookups after real writes, and writes Studio Activity rows best-effort. |

These are the first mutation routes moved out of fake `Handler` reuse.
## Save Mutation Slice

`scripts/catalogue/catalogue_write_service.py` now also owns:

| Route | Service function path | Notes |
| --- | --- | --- |
| `POST /studio/api/catalogue/work/save` | `work_save_payload()` | Calls `catalogue_source_mutation.plan_work_save()`, preserves field-registry build planning, targeted lookup invalidation, removed-series rebuild scope, optional public build follow-through, and Studio Activity rows. |
| `POST /studio/api/catalogue/work-detail/save` | `work_detail_save_payload()` | Calls `catalogue_source_mutation.plan_work_detail_save()`, preserves field-registry build planning, targeted lookup invalidation, optional parent-work public build follow-through, and Studio Activity rows. |

These routes moved after create because they coordinate more post-save behavior than source writes alone.

## Handler Inventory

| Handler method | Size | Route family | Main dependencies | Extraction assessment |
| --- | ---: | --- | --- | --- |
| `_catalogue_read_payload` | 45 lines | read | `catalogue_source`, `catalogue_lookup`, activity feed loader | Already replaced for Local Studio by `catalogue_read_payload()`. Keep any final service version as a simple read function. |
| `_handle_work_save` | 193 lines | work save | `catalogue_source_mutation`, `catalogue_lookup_refresh`, `catalogue_save_build`, `catalogue_activity`, transactions | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_bulk_save` | 209 lines | bulk save | bulk request parsing, source validation, lookup/build planning, activity | Trapped orchestration. Needs its own bulk-save service function rather than a generic catch-all. |
| `_handle_publication_preview` | 5 lines | publication | `catalogue_publication.build_publication_preview` | Thin wrapper. Can move early into dispatch/status handling. |
| `_handle_publication_apply` | 151 lines | publication | `catalogue_publication`, cleanup transactions, lookup/build/activity helpers | Mixed orchestration. Extract after preview/delete because apply coordinates several existing modules. |
| `_handle_delete_preview` | 14 lines | delete | `catalogue_delete_plans.build_delete_preview` | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_delete_apply` | 98 lines | delete | `catalogue_delete_plans`, cleanup transactions, activity, search rebuild | Mixed orchestration. Extract as delete-apply service after preview is direct. |
| `_handle_work_create` | 98 lines | work create | `catalogue_source_mutation`, source write transaction, lookup/activity | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_work_detail_create` | 105 lines | detail create | `catalogue_source_mutation`, source write transaction, lookup/activity | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_work_detail_save` | 183 lines | detail save | `catalogue_source_mutation`, `catalogue_lookup_refresh`, `catalogue_save_build`, activity | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_work_file_*` | 2 lines each | retired work file metadata | none | Retired endpoints. Keep excluded from new service unless a current route still needs them. |
| `_handle_work_link_*` | 2 lines each | retired work link metadata | none | Retired endpoints. Keep excluded from new service unless a current route still needs them. |
| `_handle_series_save` | 213 lines | series save | series/work mutation planning, lookup/build/activity helpers | Trapped orchestration. Extract after work/detail save patterns are established. |
| `_handle_series_create` | 116 lines | series create | `catalogue_source_mutation`, source write transaction, lookup/activity | Trapped orchestration. Extract with series save. |
| `_handle_import_preview` | 11 lines | workbook import | `catalogue_workbook_import` | Already replaced for Local Studio by `import_preview_payload()`. |
| `_handle_import_apply` | 115 lines | workbook import | `catalogue_workbook_import`, source write transaction, lookup/activity | Already replaced for Local Studio by `import_apply_response()`. Avoid copying the old handler version. |
| `_handle_build_preview` | 47 lines | scoped build | field registry, build scopes, media plan | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_build_apply` | 16 lines | scoped build | `run_scoped_build_scope` through helper | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_moment_preview` | 21 lines | moment preview | moment source/metadata helpers, media plan | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_moment_save` | 149 lines | moment save | moment metadata mutation, invalidation, build/activity helpers | Trapped orchestration. Extract after work/detail/series save patterns. |
| `_handle_prose_import_preview` | 4 lines | prose import | `catalogue_prose_import` | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_prose_import_apply` | 50 lines | prose import | `catalogue_prose_import`, activity | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_moment_import_preview` | 3 lines | moment import | `catalogue_prose_import` | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_moment_import_apply` | 59 lines | moment import | `catalogue_prose_import`, activity | Moved for Local Studio to `catalogue_write_service.py`; standalone wrapper still has its old handler method. |
| `_handle_project_state_report` | 73 lines | project state | `project_state_report`, activity | Already replaced for Local Studio by `project_state_report_payload()`. |
| `_handle_thumbnail_quality_preview` | 17 lines | thumbnail quality | `build_thumbnail_quality_preview` | Already replaced for Local Studio by `thumbnail_quality_preview_payload()`. |

## Recommended Extraction Order

1. Keep `scripts/catalogue/catalogue_write_service.py` small: route mapping, status selection, response shaping, and calls into existing domain modules.
2. Treat the first service slice as complete for delete preview, build preview/apply, moment preview, prose import preview/apply, and moment import preview/apply.
3. Treat work and work-detail create/save as the established mutation extraction pattern.
   Keep source mutation planning in `catalogue_source_mutation.py`, transaction writes in `catalogue_transactions.py`, lookup refresh in `catalogue_lookup_refresh.py`, and activity row construction in `catalogue_activity.py`.
4. Move series create/save and moment save after the work/detail pattern is verified.
5. Move publication preview/apply and delete apply as separate slices because they coordinate source-save extraction, cleanup, build, lookup, and activity behavior.
6. Remove the fake handler path from `studio_catalogue_api.py`.
7. Decide whether the standalone `catalogue_write_server.py` wrapper still has an audience.
   If it does not, remove the `8788` wrapper rather than keeping a compatibility server around as a second exercise path.

## Non-Goals

- Do not move every handler method into one `CatalogueWriteService` class.
- Do not make the service module own source mutation, transaction, lookup, publication, delete, import, or build domain rules that already have focused modules.
- Do not restore retired work-file or work-link endpoints unless there is a current route that needs them.
- Do not keep `127.0.0.1:8788` as a normal Local Studio dependency once the local app can call the service functions directly.
