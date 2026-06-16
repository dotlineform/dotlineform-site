---
doc_id: site-request-work-detail-section-data-model
title: Work Detail Section Data Model Request
added_date: 2026-06-16
last_updated: 2026-06-16
ui_status: draft
parent_id: change-requests
viewable: true
---
# Work Detail Section Data Model Request

Status:

- proposed

## Summary

Replace the current work-detail section metadata model before moving detail editing into modals on the work editor page.

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
- `title` sorts details by normalized title with `detail_id` or `detail_uid` as a deterministic tie-breaker
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

Focused work-detail lookup records may still expose the joined section metadata if the standalone work detail editor needs it during the transition, but that should be treated as a temporary route compatibility surface. The target modal UI should load section metadata from the parent work lookup or a section-focused service response.

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

Decide during implementation whether public payloads should expose the field as `section_order` or continue projecting a compatibility `sort_order`. Prefer `section_order` for new schema clarity unless a public runtime compatibility concern requires a staged switch.

### Public Runtime

Review the public catalogue runtime after payload generation changes:

- `site/assets/js/catalogue/routes/work-page.js`
- `site/assets/js/catalogue/routes/work-detail-page.js`

The public runtime should render details in generated order and should not need to sort detail rows itself. If route code currently derives section ids or labels from nested detail fallback fields, remove those fallbacks after payload migration.

## Studio Editor Changes

### Current Work Editor

`/studio/catalogue-work/` currently includes the detail navigation/browser surface.

Before modal editing:

- update `catalogue-work-detail-browser.js` to read section-level `details_subfolder`, `section_order`, and `detail_sort`
- ensure nested detail rows no longer depend on repeated `section_id`, `section_title`, or `details_subfolder`
- keep `detail_uid` as the edit identity
- keep `detail_id` for display, filtering, and local sort affordances

Future modal UI:

- section modal edits `details_subfolder`, `section_title`, `section_order`, and `detail_sort`
- detail modal edits `detail_id`, `title`, `project_filename`, and selected `section_id`
- detail move workflows should change only the detail `section_id`
- section delete workflows must define what happens to contained details before implementation

### Current Work Detail Editor

`/studio/catalogue-work-detail/` is transitional.

During the model migration it should either:

- continue to work through joined focused lookup payloads while section fields are visibly read-only or removed, or
- be narrowed to detail-owned fields only and link users back to the parent work editor for section changes

The target direction is to retire this standalone page once work-detail modals exist on the work editor.

Do not add new section-editing behavior to the standalone work detail editor unless it is required as a temporary migration bridge.

## Workbook Import

Current detail ordering has historically been handled before import: Excel rows were manually sorted and assigned sequential detail ids.

The import path should preserve that behavior:

- detail ids remain the stable imported order inside a section when `detail_sort` is empty or `detail_id`
- import may create section records from `details_subfolder` plus `section_title`
- import may accept `section_order` and `detail_sort` when present
- import should reject or ignore legacy detail-level `sort_order` according to the migration policy

## Migration Plan

1. Add source model support for `work_detail_sections` while reading current detail-level section fields.
2. Write a one-time migration that extracts unique section records from current `work_details`.
3. Rename current section `sort_order` values to section `section_order`; existing values are all null in current canonical data.
4. Set migrated section `detail_sort` to null.
5. Remove `details_subfolder`, `section_title`, and `sort_order` from detail records.
6. Update validators and mutation planners to reject the old detail-level fields after migration.
7. Update lookup export and public work JSON generation.
8. Regenerate Studio lookup payloads and public catalogue artifacts as required.
9. Update Studio work editor detail browser to consume the new lookup shape.
10. Narrow or retire the standalone work detail editor after modal editing exists.

## Tests And Verification

Required focused tests:

- source validation accepts migrated section/detail records
- source validation rejects detail-level `sort_order`
- source validation rejects mismatched detail `section_id` / `work_id`
- lookup export projects section metadata once per section
- lookup export strips section metadata from nested detail summaries
- public work JSON section ordering uses `section_order` with `section_id` fallback
- public work JSON detail ordering uses `detail_sort` with `detail_id` fallback
- workbook import creates or resolves section records correctly
- current work editor detail browser works with the new lookup shape
- standalone work detail editor either works with joined payloads or no longer exposes section fields

Suggested commands:

```bash
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_source_media_section_schema.py
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_source_mutation.py
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_lookup_dependencies.py
$HOME/miniconda3/bin/python3 studio/tests/python/test_catalogue_generation_records.py
$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py
```

Add or update focused smoke coverage for:

- `studio/tests/smoke/catalogue_work_editor_state_modules.py`
- any modal smoke introduced by the later work-editor detail modal implementation

## Documentation Follow-Up

Update these stable docs after implementation:

- [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source)
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server-build-lookup)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)

## Open Questions

- Should the migrated source keep sections inside `work_details.json`, or should sections move to a separate `work_detail_sections.json` file?
- Should public work JSON expose `section_order`, or project a temporary `sort_order` compatibility alias?
- Should `detail_sort: title` sort by raw title, normalized casefolded title, or a future title-sort key?
- Should a section with no details be allowed in canonical source so users can create sections before adding details?
- What should happen when a section is deleted: block while details exist, move details, or delete contained details after explicit confirmation?
