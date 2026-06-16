---
doc_id: site-request-work-detail-section-data-model
title: Work Detail Section Data Model Request
added_date: 2026-06-16
last_updated: 2026-06-16
ui_status: complete
parent_id: change-requests
viewable: true
---
# Work Detail Section Data Model Request

Status: complete

## Summary

Replace the current work-detail section metadata model. This is a prerequisite to implementing work detail editing using modals on the work editor page.

The current canonical work-detail source and generated Studio lookup payloads mix section-level metadata with detail-record metadata. That makes the current work detail editor appear to edit one record, while it is often editing section attributes that are shared by multiple details.

This request separates:

- work detail section metadata
- individual work detail metadata
- generated lookup projection shape
- public work JSON section/detail ordering rules

This is a data-model and generation change first. The modal UI migration should happen after this model boundary is stable.

## Current Problem

Example generated lookup payload from `studio/data/generated/catalogue-lookup/works/00782.json`:

```json
{
  "detail_sections": [
    {
      "section_id": "00782-1",
      "section_title": "details",
      "sort_order": null,
      "count": 4,
      "details": [
        {
          "detail_uid": "00782-001",
          "detail_id": "001",
          "title": "birth of forms - detail 1",
          "section_id": "00782-1",
          "section_title": "details",
          "sort_order": null,
          "details_subfolder": "details",
          "project_filename": "birth of forms - detail 1.jpg"
        }
      ]
    }
  ]
}
```

Problems:

- `section_id`, `section_title`, `sort_order`, and `details_subfolder` are repeated for every nested detail even though `details[]` is already nested inside a section.
- `details_subfolder` is section-level source media organization, but it is not present on the section object in the Studio work lookup.
- The name `sort_order` is ambiguous. In current active code it means section ordering, but the detail list itself also needs a section-level sorting mode.
- The current work detail editor mixes section editing and detail editing in one form.

## Confirmed Current Behavior

Active implementation currently treats work-detail `sort_order` as section order:

- `studio/services/catalogue/catalogue_lookup.py` uses it to sort `detail_sections`.
- `studio/services/catalogue/catalogue_generation_records.py` uses it to sort public work JSON `sections[]`.
- `studio/app/frontend/js/catalogue-work-detail-fields.js` labels it as section sort order.
- source validation requires it to be a whole number when present.

Active detail ordering is always by `detail_id`.

Existing canonical detail data currently has no non-null `sort_order` values, so removing detail-level `sort_order` does not discard active ordering data.

## Target Canonical Model

Introduce a dedicated section source map and remove section metadata from detail records.

Target canonical source shape for `studio/data/canonical/catalogue/work_details.json`:

```json
{
  "header": {
    "schema": "catalogue_source_work_details_v2"
  },
  "work_detail_sections": {
    "00782-1": {
      "section_id": "00782-1",
      "work_id": "00782",
      "details_subfolder": "details",
      "section_title": "details",
      "section_order": null,
      "detail_sort": null
    }
  },
  "work_details": {
    "00782-001": {
      "detail_uid": "00782-001",
      "work_id": "00782",
      "detail_id": "001",
      "section_id": "00782-1",
      "title": "birth of forms - detail 1",
      "project_filename": "birth of forms - detail 1.jpg"
    }
  }
}
```

Section fields:

- `section_id`: stable generated section key, scoped to the parent work.
- `work_id`: parent work id.
- `details_subfolder`: source-image subfolder under the parent work `project_folder`.
- `section_title`: public section label.
- `section_order`: optional numeric section order.
- `detail_sort`: optional section-level detail sort mode.

Detail fields:

- `detail_uid`: stable detail identity and route/edit target.
- `work_id`: parent work id.
- `detail_id`: local detail suffix, retained for display and efficient sorting/filtering.
- `section_id`: foreign key to `work_detail_sections`.
- `title`: detail title.
- `project_filename`: source detail image filename.
- generated or media-maintained dimensions such as `width_px` and `height_px`.

Removed from detail records:

- `details_subfolder`
- `section_title`
- `sort_order`

## Ordering Semantics

### Section Order

`section_order` replaces the current section use of `sort_order`.

Rules:

- numeric values sort sections explicitly, ascending
- `null` means use the current fallback: sort by `section_id`
- `section_order` is section metadata, not detail metadata

### Detail Sort

`detail_sort` is a section-level sort mode.

Allowed values:

- `detail_id`
- `title`
- `null`

Rules:

- `null` means `detail_id`
- `detail_id` preserves current behavior
- `title` sorts details by raw title with `detail_id` or `detail_uid` as a deterministic tie-breaker
- the value belongs to the section because it controls the whole detail list inside that section

## Target Studio Work Lookup Projection

Generated `studio/data/generated/catalogue-lookup/works/<work_id>.json` should project section metadata once per section.

Target generated lookup shape for `studio/data/generated/catalogue-lookup/works/00782.json`:

```json
{
  "detail_sections": [
    {
      "section_id": "00782-1",
      "details_subfolder": "details",
      "section_title": "details",
      "section_order": null,
      "detail_sort": null,
      "count": 4,
      "details": [
        {
          "detail_uid": "00782-001",
          "detail_id": "001",
          "title": "birth of forms - detail 1",
          "project_filename": "birth of forms - detail 1.jpg"
        }
      ]
    }
  ]
}
```

Nested detail rows should not repeat:

- `section_id`
- `section_title`
- `section_order`
- `detail_sort`
- `details_subfolder`

`detail_uid` remains the identity field. `detail_id` remains as display and sorting metadata.

Focused work-detail lookup records do not need to preserve the current standalone editor contract as part of this data-model change. After the standalone editor is retired, focused detail lookup records should exist only if another current consumer needs them. The target modal UI should load section metadata from the parent work lookup or a work-scoped section/detail service response.

## Generation And Publishing Changes

### Catalogue Source Loader And Validation

Update `studio/services/catalogue/catalogue_source.py` to:

- parse and normalize `work_detail_sections`
- validate each section has `section_id`, `work_id`, and `section_title`
- validate each detail `section_id` references a section for the same `work_id`
- validate `section_order` as a whole number when present
- validate `detail_sort` as `detail_id`, `title`, or empty/null
- reject detail-level `sort_order`
- reject detail-level `section_title` and `details_subfolder` after migration

### Source Mutation And Write Services

Update create/save planning so section writes are explicit:

- creating a new section generates the next `section_id` for that work
- creating a detail requires a target `section_id`
- moving a detail between sections changes only the detail `section_id`
- editing `details_subfolder`, `section_title`, `section_order`, or `detail_sort` updates the section record
- editing `title` or `project_filename` updates the detail record

Affected services:

- `studio/services/catalogue/catalogue_source_mutation.py`
- `studio/services/catalogue/catalogue_work_detail_service.py`
- `studio/services/catalogue/catalogue_bulk_service.py`
- `studio/services/catalogue/catalogue_workbook_import.py`
- `studio/services/catalogue/validate_catalogue_source.py`

### Lookup Export

Update `studio/services/catalogue/catalogue_lookup.py` so:

- work lookup `detail_sections[]` joins section records with details
- nested detail summaries contain only detail identity and detail-owned fields
- section sorting uses `section_order`, falling back to `section_id`
- detail sorting uses section `detail_sort`, falling back to `detail_id`
- work-detail search and focused lookup records preserve the fields needed by the current editor during transition

Regenerate:

- `studio/data/generated/catalogue-lookup/work_search.json`
- `studio/data/generated/catalogue-lookup/work_detail_search.json`
- `studio/data/generated/catalogue-lookup/works/*.json`
- `studio/data/generated/catalogue-lookup/work_details/*.json`

### Public Work JSON

Update public work JSON generation:

- `studio/services/catalogue/generate_work_pages.py`
- `studio/services/catalogue/catalogue_generation_records.py`

Public `site/assets/works/index/<work_id>.json` should keep its existing nested section shape, but use the new section source map:

- each section carries `section_id`, `section_title`, `section_order`, optional `detail_sort`, and `details[]`
- nested public detail rows do not repeat section metadata
- section order uses `section_order` with `section_id` fallback
- detail order uses `detail_sort` with `detail_id` fallback

Example target public payload shape for `site/assets/works/index/00782.json`:

```json
{
  "sections": [
    {
      "section_id": "00782-1",
      "section_title": "details",
      "section_order": null,
      "detail_sort": null,
      "details": [
        {
          "detail_uid": "00782-001",
          "detail_id": "001",
          "title": "birth of forms - detail 1"
        }
      ]
    }
  ]
}
```

Public payloads should expose `section_order`. Do not project a temporary `sort_order` compatibility alias.

### Public Runtime

Review the public catalogue runtime after payload generation changes:

- `site/assets/js/catalogue/routes/work-page.js`
- `site/assets/js/catalogue/routes/work-detail-page.js`

Update the public work page runtime to consume `section_order` instead of `sort_order`. The public runtime should render details in generated order and should not need to sort detail rows itself. If route code currently derives section ids or labels from nested detail fallback fields, remove those fallbacks after payload migration.

## Studio Editor Changes

### Current Work Editor

`/studio/catalogue-work/` currently includes the detail navigation/browser surface.

- update `catalogue-work-detail-browser.js` to read section-level `details_subfolder`, `section_order`, and `detail_sort`
- ensure nested detail rows no longer depend on repeated `section_id`, `section_title`, or `details_subfolder`
- keep `detail_uid` as the edit identity
- keep `detail_id` for display, filtering, and local sort affordances

### Current Work Detail Editor

`/studio/catalogue-work-detail/` should be retired cleanly. Clean retirement should remove:

- the `/studio/catalogue-work-detail/` route registration and served-route entry
- Studio home/navigation links to the route
- route body renderer entries and route-specific shell bootstrapping
- route-specific frontend modules and UI text, unless a small helper is genuinely reused by the work editor without carrying old route behavior
- route-specific smoke tests and route registry assertions
- `POST /studio/api/catalogue/work-detail/create` and `POST /studio/api/catalogue/work-detail/save` from the local Studio service surface if they have no remaining callers
- no compatibility layers should remain or be created.

Future work-detail modals will get new work-scoped APIs that understand sections and detail operations together. The future server allowlist and write API will probably differ from the current standalone detail create/save endpoints, so adapting the old endpoints should not be part of this migration. Hence a complete retirement.

## Task List

### 1. Retire The Standalone Work Detail Editor

Remove the current route before adapting the data model so the implementation does not preserve obsolete workflows.

Touched areas:

- `studio/app/frontend/config/studio-config.json`: remove the `catalogue_work_detail_editor` route entry and route-specific UI text entry.
- `studio/app/server/studio/studio_app_config.py`: remove the served-route entry, route asset-version inputs, runtime view, and catalogue service endpoints for `create_work_detail` / `save_work_detail` if they have no remaining callers.
- `studio/app/server/studio/studio_app_server.py`: remove any special-case redirect or route handling for `/studio/catalogue-work-detail/`.
- `studio/app/frontend/js/studio-home-shell.js`: remove the home link to the standalone route.
- `studio/app/frontend/js/studio-route-body-renderers.js`: remove the body renderer for `catalogue_work_detail_editor`.
- `studio/app/frontend/js/studio-transport.js` and `studio/app/frontend/js/catalogue-editor-service-client.js`: remove route-only work-detail create/save client functions if they have no remaining callers.
- `studio/app/frontend/js/catalogue-work-detail-*.js` and `studio/app/frontend/config/ui-text/catalogue-work-detail-editor.json`: delete route-only frontend modules and copy after confirming no small helper is reused by the work editor.
- `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`, `studio/tests/smoke/catalogue_work_detail_modal.py`, `studio/tests/smoke/catalogue_editor_route_boot_modules.py`, `studio/tests/smoke/catalogue_sibling_editor_state_modules.py`, and `studio/tests/smoke/local_studio_navigation_adapter.py`: remove or update standalone-route expectations.
- `studio/tests/python/test_studio_app_server.py`: remove route registry, runtime view, endpoint, and callable route expectations for the retired route.

### 2. Remove Retired Detail-Route Service Endpoints

Do not adapt the old detail create/save endpoints for the new section model.

Touched areas:

- `studio/app/server/studio/studio_catalogue_api.py`: remove `work-detail/create` and `work-detail/save` from callable route dispatch if no remaining caller needs them.
- `studio/services/catalogue/catalogue_write_service.py`: remove `/work-detail/create` and `/work-detail/save` dispatch if no remaining caller needs them.
- `studio/services/catalogue/catalogue_routes.py`: remove retired detail create/save route constants if unused.
- `studio/services/catalogue/catalogue_work_detail_service.py`: delete or shrink to shared helpers only after the route/service callers are removed.
- `studio/services/catalogue/catalogue_invalidation.py`, `studio/services/catalogue/catalogue_activity.py`, and activity/context tests: remove route-only activity and invalidation entries.

Future modal APIs will be designed separately as work-scoped section/detail operations.

### 3. Migrate Canonical Source Shape

Add section records and remove section metadata from detail records.

Touched areas:

- `studio/data/canonical/catalogue/work_details.json`: migrate to the target `work_detail_sections` plus `work_details` shape.
- migration script or one-time command: extract unique sections from existing detail records, rename section `sort_order` to `section_order`, set `detail_sort` to null, and remove detail-level `details_subfolder`, `section_title`, and `sort_order`.
- `studio/services/catalogue/catalogue_source.py`: parse the new section map, build normalized records, and keep deterministic ordering.
- `studio/services/catalogue/validate_catalogue_source.py`: validate section records, cross-check detail `section_id` / `work_id`, reject retired detail-level section fields, validate `section_order`, and validate `detail_sort`.
- `studio/services/catalogue/catalogue_source_mutation.py`: update normalization and mutation helpers so section writes and detail writes are distinct.
- `studio/services/catalogue/catalogue_workbook_import.py` and `studio/services/catalogue/catalogue_bulk_service.py`: create or resolve sections from imported detail rows and stop writing retired detail-level fields.

### 4. Update Lookup Projection

Project the new source shape into Studio lookup payloads.

Touched areas:

- `studio/services/catalogue/catalogue_lookup.py`: join sections with details for work lookup, project section metadata once per section, remove repeated section fields from nested detail summaries, sort sections by `section_order` with `section_id` fallback, and sort details by `detail_sort` with `detail_id` fallback.
- `studio/services/catalogue/catalogue_lookup_refresh.py`: adjust targeted refresh artifacts if focused work-detail records or work-detail search no longer need the old shape.
- `studio/tests/python/test_catalogue_lookup_dependencies.py`: update field dependency expectations for section/detail fields.
- generated files under `studio/data/generated/catalogue-lookup/`: regenerate work lookup records, work search, and any remaining work-detail lookup/search payloads that still have callers.

### 5. Update Public Work JSON Generation

Make public payloads use the same section semantics without compatibility aliases.

Touched areas:

- `studio/services/catalogue/generate_work_pages.py`: update work JSON build flow to consume section records.
- `studio/services/catalogue/catalogue_generation_records.py`: group details by section, emit `section_order`, emit `detail_sort`, remove nested detail section metadata, and apply the new section/detail ordering rules.
- `site/assets/works/index/<work_id>.json`: regenerate public work payloads with `section_order` and without `sort_order`.
- generated public detail artifacts under `site/assets/work_details/` and catalogue indexes: refresh only where affected by source shape or detail deletion behavior.

### 6. Update Public Runtime

The public runtime must match the new public JSON shape in the same change set.

Touched areas:

- `site/assets/js/catalogue/routes/work-page.js`: consume `section_order` instead of `sort_order`, remove fallbacks that infer section metadata from nested detail records, and trust generated detail order.
- `site/assets/js/catalogue/routes/work-detail-page.js`: remove assumptions that focused detail payloads or adjacent navigation can read section metadata from nested detail rows.
- `studio/tests/smoke/public_route_simplification.py` and any public work/work-detail route smokes: update fixtures and assertions for `section_order`, `detail_sort`, and stripped nested detail metadata.

### 7. Update Current Studio Work Editor Surfaces

Before modal editing exists, the current work editor must at least browse the new lookup shape correctly.

Touched areas:

- `studio/app/frontend/js/catalogue-work-detail-browser.js`: read section-level `details_subfolder`, `section_order`, and `detail_sort`; stop reading repeated section fields from nested detail summaries.
- `studio/app/frontend/js/catalogue-work-editor.js` and related work-editor state/action modules: remove navigation to the retired standalone detail route and keep `detail_uid` as identity only where still useful.
- `studio/app/frontend/config/ui-text/catalogue-work-editor.json`: update any copy that references opening or creating details through the retired route.
- `studio/tests/smoke/catalogue_work_editor_state_modules.py` and work-editor route smokes: update fixtures and expectations for the new section/detail browser shape.
- the UI toolbar buttons that currently point to the retired details editor page should be kept as inert buttons, because they will be needed to open future modals.

### 8. Regenerate Artifacts

After source and projection changes:

- regenerate `studio/data/generated/catalogue-lookup/work_search.json`
- regenerate `studio/data/generated/catalogue-lookup/works/*.json`
- regenerate any still-used `studio/data/generated/catalogue-lookup/work_detail_search.json` and `studio/data/generated/catalogue-lookup/work_details/*.json`
- regenerate `site/assets/works/index/*.json`
- regenerate public catalogue indexes/search if their inputs or schemas change

### 9. Update Tests And Documentation

Touched areas:

- source schema and mutation tests: `studio/tests/python/test_catalogue_source_media_section_schema.py`, `studio/tests/python/test_catalogue_source_mutation.py`
- lookup and refresh tests: `studio/tests/python/test_catalogue_lookup_dependencies.py`, `studio/tests/python/test_catalogue_lookup_refresh.py`
- public generation tests: `studio/tests/python/test_catalogue_generation_records.py`
- Studio server and route tests: `studio/tests/python/test_studio_app_server.py`
- route/module smoke tests affected by route retirement or work-editor detail browsing
- documentation listed below under Documentation Follow-Up

## Tests And Verification

- Do not test negative assertions that assert functionality has been removed.
- Do not test server end points etc that don't yet exist for UI modals that do not yet exist.

Candidate focused tests:

- source validation accepts migrated section/detail records
- source validation rejects mismatched detail `section_id` / `work_id`
- lookup export projects section metadata once per section
- public work JSON section ordering uses `section_order` with `section_id` fallback
- public work JSON detail ordering uses `detail_sort` with `detail_id` fallback
- public work and work-detail routes render with the new public JSON shape
- current work editor detail browser works with the new lookup shape
- standalone work detail editor route, frontend modules, route tests, and obsolete detail create/save endpoints are retired cleanly

Suggested commands:

```bash
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_source_media_section_schema.py
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_source_mutation.py
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_lookup_dependencies.py
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_generation_records.py
$HOME/miniconda3/bin/python3 studio/tests/smoke/public_route_simplification.py --site-root <site-root>
$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py
```

Add or update focused smoke coverage for:

- `studio/tests/smoke/catalogue_work_editor_state_modules.py`

## Documentation Follow-Up

Update these stable docs after implementation:

- [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source)
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor) - mark as retired
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server-build-lookup)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)

## Implementation Closeout

Implemented on 2026-06-16.

Final decisions:

- canonical `work_details.json` uses `work_detail_sections` plus `work_details`
- detail records no longer store `details_subfolder`, `section_title`, or `sort_order`
- section ordering is `section_order`; section-level detail ordering is `detail_sort`
- Studio work lookup projects section metadata once per section and nested detail summaries contain detail-owned fields only
- public work JSON consumes the section map and strips section metadata from nested detail rows
- optional null `section_order` and `detail_sort` are compacted out of public payloads until meaningful values exist, matching existing public JSON conventions
- `/studio/catalogue-work-detail/` and its create/save endpoints are retired rather than adapted
- current work-editor detail toolbar actions remain present but inert for future work-scoped modals
