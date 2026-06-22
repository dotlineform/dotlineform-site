---
doc_id: site-request-catalogue-per-work-detail-source
title: Catalogue Per-Work Detail Source Request
added_date: 2026-06-22
last_updated: 2026-06-22
ui_status: implemented
parent_id: change-requests
viewable: true
---
# Catalogue Per-Work Detail Source Request

Status: implemented

## Implementation Note

Implemented on 2026-06-22.

- Migrated `studio/data/canonical/catalogue/work_details.json` into per-work files under `studio/data/canonical/catalogue/work_details/`.
- Moved the retired flat source to `studio/data/canonical/catalogue/retired/work_details.flat.v2.json`.
- Moved retired generated Studio lookup artifacts under `studio/data/generated/catalogue-lookup/retired/`.
- Kept retained generated lookup runtime files to `work_search.json`, `series_search.json`, and `series/{series_id}.json`.
- Replaced work and work-detail focused generated lookup reads with service projections for `catalogue_work_record` and `catalogue_work_detail_record`.
- Updated source loading, validation, write transactions, workbook import apply, delete plans, bulk/detail-section writes, frontend config, and tests for the per-work detail source model.

Verification:

- Migrated-directory flatten output matches the retired flat source.
- `records_from_json_source()` validates the migrated source with zero errors.
- Focused catalogue tests: `61 passed`.
- `admin-app/commands/run_checks.py --profile catalogue`: passed.

## Summary

Move canonical work-detail source data from one global flat `work_details.json` file to one nested canonical work-detail file per `work_id`.

The target model treats detail sections and details as a work-owned aggregate:

- `works.json` remains the canonical source for primary work metadata.
- each detailed work gets one canonical detail-source file keyed by `work_id`.
- generated Studio search/list lookup and public JSON keep their current output contracts.
- targeted work and work-detail editor reads become service projections over canonical source rather than generated per-record lookup files.

This keeps canonical authoring data aligned with the current work editor, where detail sections and detail images are browsed, created, edited, deleted, and rebuilt through the parent work.

## Source Ownership

### Current Source

Current canonical detail source is one global file:

```text
studio/data/canonical/catalogue/work_details.json
```

It contains two flat maps:

```json
{
  "header": {
    "schema": "catalogue_source_work_details_v2",
    "section_count": 163,
    "count": 2681
  },
  "work_detail_sections": {
    "00782-1": {
      "section_id": "00782-1",
      "work_id": "00782",
      "details_subfolder": "details",
      "section_title": "details"
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

### Target Source Paths

Target canonical detail source is a directory of per-work records:

```text
studio/data/canonical/catalogue/work_details/
  00001.json
  00158.json
  00782.json
```

Only works with detail sections need a file. A work with no detail sections has no detail-source file.

Empty sections are not allowed in the target source model. A detail section should exist only when it owns at least one detail record, matching the current UI rule that section creation starts from one or more selected image files.

The old global `studio/data/canonical/catalogue/work_details.json` should be retired during the migration. There should be no dual-running reader, fallback reader, compatibility alias, or long-lived support for both source shapes.

After the per-work files are generated, move the old global source file out of its runtime path immediately:

```text
studio/data/canonical/catalogue/retired/work_details.flat.v2.json
```

The retired file is available only for inspection, migration verification, flatten-compare tests, and rollback analysis. Runtime source loaders must not read from `retired/`.

## Target JSON Structures

### `works.json`

Primary work metadata stays in `studio/data/canonical/catalogue/works.json`.

The structure does not change:

```json
{
  "header": {
    "schema": "catalogue_source_works_v1",
    "count": 1
  },
  "works": {
    "00782": {
      "work_id": "00782",
      "status": "published",
      "published_date": "2026-04-01",
      "series_ids": [
        "009"
      ],
      "project_folder": "birth of forms",
      "project_filename": "birth of forms.jpg",
      "title": "birth of forms",
      "width_cm": 29.7,
      "height_cm": 21,
      "year": 2025,
      "year_display": "2025",
      "medium_type": "drawing",
      "medium_caption": "pencil on paper"
    }
  }
}
```

Detail data should not be embedded in `works.json`. Keeping detail data in companion per-work files avoids making primary work metadata diffs noisy and keeps detail-media workflows independently maintainable.

### Per-Work Detail Source File

Each detail-source file owns the sections and details for one work:

```json
{
  "header": {
    "schema": "catalogue_source_work_detail_record_v1",
    "work_id": "00782",
    "section_count": 1,
    "count": 1
  },
  "work_id": "00782",
  "detail_sections": [
    {
      "section_id": "00782-1",
      "details_subfolder": "details",
      "section_title": "details",
      "section_order": null,
      "detail_sort": null,
      "details": [
        {
          "detail_uid": "00782-001",
          "detail_id": "001",
          "title": "birth of forms - detail 1",
          "project_filename": "birth of forms - detail 1.jpg",
          "width_px": 4032,
          "height_px": 2268
        }
      ]
    }
  ]
}
```

Notes:

- `work_id` appears once at the file level.
- `section_id` remains stable because existing generated URLs, build behavior, delete plans, and activity context use it.
- `detail_uid` remains stable because public routes, service detail payloads, media derivatives, and cleanup paths use it.
- `detail_id` remains a child-local sequence value used for display and ordering.
- detail records should not repeat `work_id` or `section_id`; those values are structurally implied by file and section ownership.
- section-level fields such as `details_subfolder`, `section_title`, `section_order`, and `detail_sort` belong only on section records.

### Optional Source Index

If directory scanning becomes inconvenient for tooling, add a small manifest rather than restoring the global detail maps:

```text
studio/data/canonical/catalogue/work_details/index.json
```

```json
{
  "header": {
    "schema": "catalogue_source_work_detail_index_v1",
    "work_count": 142,
    "section_count": 163,
    "count": 2681
  },
  "works": [
    {
      "work_id": "00001",
      "path": "00001.json",
      "section_count": 1,
      "count": 17
    }
  ]
}
```

Do not add this manifest during the initial migration. It can be added later if directory scanning becomes a real maintenance or performance problem. If added, it should be treated as derived bookkeeping unless there is a specific source-authoring need for it. The canonical record remains the per-work JSON file.

## Lookup And Read Model Changes

Per-work canonical detail files should reduce the need for generated Studio lookup files, not create a new global lookup requirement.

For targeted work-editor and work-detail-editor operations, the service should read only the relevant source records:

```text
studio/data/canonical/catalogue/works.json
studio/data/canonical/catalogue/series.json
studio/data/canonical/catalogue/work_details/{work_id}.json
```

A request for `detail_uid` can derive `work_id` from the UID prefix, load `work_details/{work_id}.json`, and find the child detail inside that one aggregate. That path does not require a global detail index.

The frontend should still avoid direct canonical-file reads. It should request a service projection such as "work editor payload for `work_id`" or "detail editor payload for `detail_uid`". The server/helper boundary should own schema validation, parent/child resolution, and any derived fields the UI needs.

### Studio Lookup File Contract

The migration should be explicit about which generated lookup files remain runtime contracts and which old generated lookup files are retired.

Keep these generated lookup files unchanged:

| Runtime path | Schema | Decision |
| --- | --- | --- |
| `studio/data/generated/catalogue-lookup/work_search.json` | `studio_catalogue_lookup_work_search_v1` | Keep unchanged. Work search does not need detail records. |
| `studio/data/generated/catalogue-lookup/series_search.json` | `studio_catalogue_lookup_series_search_v1` | Keep unchanged. |
| `studio/data/generated/catalogue-lookup/series/{series_id}.json` | `studio_catalogue_lookup_series_record_v1` | Keep unchanged. |

Retained lookup JSON shapes:

```json
{
  "header": {
    "schema": "studio_catalogue_lookup_work_search_v1",
    "count": 1940
  },
  "items": [
    {
      "work_id": "00782",
      "title": "birth of forms",
      "year_display": "2025",
      "status": "published",
      "series_ids": [
        "009"
      ]
    }
  ]
}
```

```json
{
  "header": {
    "schema": "studio_catalogue_lookup_series_search_v1",
    "count": 143
  },
  "items": [
    {
      "series_id": "009",
      "title": "a poem divided into 4 parts",
      "status": "published",
      "primary_work_id": "00001"
    }
  ]
}
```

```json
{
  "header": {
    "schema": "studio_catalogue_lookup_series_record_v1"
  },
  "series": {
    "series_id": "009",
    "title": "a poem divided into 4 parts",
    "series_type": "primary",
    "status": "published",
    "primary_work_id": "00001"
  },
  "member_works": [
    {
      "work_id": "00001",
      "title": "a poem divided into 4 parts (\"our dreams are real\")",
      "year_display": "2025",
      "status": "published",
      "series_ids": [
        "009"
      ]
    }
  ]
}
```

Retire these generated lookup files because targeted reads should come from service projections over canonical source:

| Old runtime path | Old schema | Retired path |
| --- | --- | --- |
| `studio/data/generated/catalogue-lookup/works/{work_id}.json` | `studio_catalogue_lookup_work_record_v1` | `studio/data/generated/catalogue-lookup/retired/works/{work_id}.json` |
| `studio/data/generated/catalogue-lookup/work_details/{detail_uid}.json` | `studio_catalogue_lookup_work_detail_record_v1` | `studio/data/generated/catalogue-lookup/retired/work_details/{detail_uid}.json` |
| `studio/data/generated/catalogue-lookup/work_detail_search.json` | `studio_catalogue_lookup_work_detail_search_v1` | `studio/data/generated/catalogue-lookup/retired/work_detail_search.json` |

The retired generated lookup files are available only for migration comparison. Runtime code must not read from `studio/data/generated/catalogue-lookup/retired/`.

After migration, these old runtime paths should not exist:

```text
studio/data/generated/catalogue-lookup/works/
studio/data/generated/catalogue-lookup/work_details/
studio/data/generated/catalogue-lookup/work_detail_search.json
```

No new generated lookup files are required for work detail editing. Targeted work and detail reads should be service-only payloads built from canonical source at request time.

### Service Read Payloads

Replace generated per-record lookup reads with service-only read payloads. These are API contracts, not generated files.

Work editor read:

```text
GET /studio/api/catalogue/read?key=catalogue_work_record&record_id={work_id}
```

Target JSON:

```json
{
  "header": {
    "schema": "studio_catalogue_work_record_v1"
  },
  "work": {
    "work_id": "00782",
    "status": "published",
    "series_ids": [
      "009"
    ],
    "project_folder": "birth of forms",
    "project_filename": "birth of forms.jpg",
    "title": "birth of forms"
  },
  "detail_sections": [
    {
      "section_id": "00782-1",
      "details_subfolder": "details",
      "section_title": "details",
      "section_order": null,
      "detail_sort": null,
      "count": 1,
      "details": [
        {
          "detail_uid": "00782-001",
          "detail_id": "001",
          "title": "birth of forms - detail 1",
          "project_filename": "birth of forms - detail 1.jpg"
        }
      ]
    }
  ],
  "downloads": [],
  "links": [],
  "series_summary": [
    {
      "series_id": "009",
      "title": "a poem divided into 4 parts"
    }
  ]
}
```

Work detail editor read:

```text
GET /studio/api/catalogue/read?key=catalogue_work_detail_record&record_id={detail_uid}
```

Target JSON:

```json
{
  "header": {
    "schema": "studio_catalogue_work_detail_record_v1"
  },
  "work_detail": {
    "detail_uid": "00782-001",
    "work_id": "00782",
    "detail_id": "001",
    "section_id": "00782-1",
    "project_filename": "birth of forms - detail 1.jpg",
    "title": "birth of forms - detail 1",
    "width_px": 4032,
    "height_px": 2268,
    "section_title": "details",
    "details_subfolder": "details",
    "section_order": null,
    "detail_sort": null
  },
  "work_summary": {
    "work_id": "00782",
    "title": "birth of forms"
  }
}
```

The service can resolve `catalogue_work_detail_record` by parsing `work_id` from `detail_uid`, loading only `work_details/{work_id}.json`, and finding the matching child detail.

Update `studio/app/frontend/config/studio-config.json` accordingly:

- keep `catalogue_lookup_work_search`
- keep `catalogue_lookup_series_search`
- keep `catalogue_lookup_series_base`
- remove static paths for `catalogue_lookup_work_base`, `catalogue_lookup_work_detail_base`, and `catalogue_lookup_work_detail_search`
- add server-only read keys for `catalogue_work_record` and `catalogue_work_detail_record`

### Global Detail Loads

Loading all per-work detail-source files should be reserved for workflows that are inherently global:

1. full source validation
2. full public search generation
3. full public catalogue rebuilds
4. workbook import/export validation across many works
5. orphan, stale generated file, and cleanup audits
6. migration comparisons against retired generated lookup files

Targeted build, edit, delete, and preview operations should load the affected work-detail file rather than scanning the whole directory.

### Public Generation

Public site JSON remains generated and separate from canonical source:

```text
site/assets/works/index/{work_id}.json
site/assets/work_details/index/{detail_uid}.json
site/assets/data/search/catalogue/index.json
```

The public site output contract is not changing. Public pages, public JSON paths, public JSON schemas, and public frontend behavior are outside the scope of this migration.

Catalogue generators should target the same public JSON they currently target. Only the canonical source reader changes from global flat detail maps to per-work nested detail-source files. Full public search generation may still flatten all per-work detail files because search is a global read model.

## Helper API Boundary

Before changing source files, catalogue code should depend on helper functions that hide canonical storage shape.

Minimum helper responsibilities:

- load all canonical source into a normalized in-memory model for global validation and rebuilds
- load one work-detail aggregate by `work_id`
- look up one detail by `detail_uid`
- list ordered detail sections for one work
- list ordered details for one section
- create, update, reorder, and delete detail sections
- create, update, move, and delete details
- serialize one work-detail aggregate deterministically
- flatten details for search, publication, import, export, validation, and cleanup workflows when those workflows are global

The helper API may still expose normalized maps internally where that keeps existing generation code simple. The important constraint is that callers should not know whether source storage is one file, many files, flat maps, or nested aggregates.

## Migration Execution Policy

This should be an uninterrupted migration across sessions, not a compatibility period.

Execution rules:

- create the new per-work detail-source files and migrate the existing data first
- move the old global source file to `studio/data/canonical/catalogue/retired/work_details.flat.v2.json` immediately after generating the per-work files
- after source files exist, the remaining work is code migration from old source shape to new source shape
- do not add dual-read behavior or fallback compatibility for both source shapes
- do not leave `studio/data/canonical/catalogue/work_details.json` in place while code migration proceeds
- keep UI behavior unchanged unless a specific UI change is called out as preferable during migration and accepted as an explicit decision point
- runtime source validation should fail if the old global file exists at `studio/data/canonical/catalogue/work_details.json`
- production code must not reference `studio/data/canonical/catalogue/retired/`

The current UI rule is retained: section creation requires one or more selected image files, so empty sections are not part of the migration target.

## Migration Tasks

1. Migrate source data:
   - generate `studio/data/canonical/catalogue/work_details/{work_id}.json` files from current flat maps
   - include per-work files for works that currently have detail sections
   - fail validation if any empty section is discovered
   - move the old global file to `studio/data/canonical/catalogue/retired/work_details.flat.v2.json`
   - compare helper-flattened output with the retired flat source file
   - verify `studio/data/canonical/catalogue/work_details.json` no longer exists before runtime code migration begins

2. Inventory direct source-shape accesses:
   - `records.work_details`
   - `records.work_detail_sections`
   - `work_details.json`
   - `detail_uid`
   - `section_id`
   - `details_subfolder`
   - `section_title`
   - `section_order`
   - `detail_sort`

3. Introduce helper-backed read projection against the new source shape:
   - add aggregate helpers that return per-work nested detail structures
   - update work editor and detail editor services to call targeted helpers
   - update lookup generation to call global flattening helpers only for retained search/list output
   - keep output byte-equivalent where practical

4. Retire generated per-record detail lookup artifacts:
   - move `studio/data/generated/catalogue-lookup/works/` to `studio/data/generated/catalogue-lookup/retired/works/`
   - move `studio/data/generated/catalogue-lookup/work_details/` to `studio/data/generated/catalogue-lookup/retired/work_details/`
   - move `studio/data/generated/catalogue-lookup/work_detail_search.json` to `studio/data/generated/catalogue-lookup/retired/work_detail_search.json`
   - verify the old generated runtime paths no longer exist
   - keep retained lookup files in place: `work_search.json`, `series_search.json`, and `series/{series_id}.json`

5. Add per-work detail-source schema support:
   - define `catalogue_source_work_detail_record_v1`
   - validate filename, `header.work_id`, top-level `work_id`, section IDs, and detail UIDs
   - reject repeated section metadata on detail records
   - reject detail records that repeat mismatched parent fields

6. Add deterministic serializers:
   - write one `{work_id}.json` file
   - preserve stable section ordering
   - preserve stable detail ordering using section `detail_sort`
   - omit empty optional fields consistently
   - delete the per-work file when its last section is deleted

7. Update write services:
   - section create/save/delete writes one per-work detail file
   - detail create/save/move/delete writes one per-work detail file
   - work delete removes the companion detail file
   - publication and build follow-through continue to receive affected work/detail IDs

8. Update import/export boundaries:
   - workbook import can continue to parse rows
   - import apply groups rows by `work_id`
   - validation reports row-level errors before writing grouped per-work files
   - any export that needs rows flattens from the per-work source loader

9. Update read models and publication:
   - work editor service reads only the requested per-work detail file
   - detail editor service derives `work_id` from `detail_uid` and reads only that per-work detail file
   - replace generated Studio per-work/per-detail lookup files with service-only read payloads
   - remove runtime/static config paths for retired generated lookup files
   - public work page JSON generation consumes the matching nested per-work source while writing the same public output contract
   - global search generation consumes generated/public records or flattened helper output

10. Update delete, cleanup, and media workflows:
   - detail delete resolves parent work from `detail_uid` and reads the matching per-work file
   - section delete edits the parent work-detail file
   - cleanup still targets existing generated detail artifacts by `detail_uid`
   - media build still resolves `project_folder`, `details_subfolder`, and `project_filename`

11. Update tests and docs:
    - source validation tests
    - retained lookup generation tests
    - work editor section create/save/delete tests
    - service work/detail read tests
    - retired generated lookup path isolation tests
    - workbook import tests
    - delete-plan and cleanup tests
    - stable source model documentation

12. Verify retired-source isolation:
    - verify `studio/data/canonical/catalogue/work_details.json` does not exist
    - verify no runtime code path opens `studio/data/canonical/catalogue/retired/work_details.flat.v2.json`
    - allow retired-source reads only in migration verification or fixture helpers
    - verify retained Studio lookup output matches expected contracts
    - verify retired generated lookup runtime paths no longer exist
    - verify no runtime code path opens `studio/data/generated/catalogue-lookup/retired/`
    - verify regenerated public work JSON matches the current public output for representative works, including multi-section works

## Decisions And Decision Points

- Works with no detail sections have no per-work detail-source file.
- Empty sections are not allowed in the target source model.
- The initial migration should not add a generated manifest; add one later only if needed.
- Public site output is not changing. Generators target the same public JSON contracts as today.
- The migration should not add dual-running source readers, fallback compatibility, or aliases.
- The old global source file should be moved immediately to `studio/data/canonical/catalogue/retired/work_details.flat.v2.json` after per-work files are generated.
- Runtime loaders must not read from `retired/`; that folder is only for inspection and migration verification.
- Generated Studio lookup keeps only `work_search.json`, `series_search.json`, and `series/{series_id}.json` as runtime files.
- Generated Studio `works/{work_id}.json` and `work_details/{detail_uid}.json` are retired and replaced by service-only targeted read payloads.
- Generated Studio `work_detail_search.json` is retired without replacement unless a future explicit global detail search workflow is added.
- UI behavior should not change unless a specific UI change is accepted as an explicit migration decision point.
