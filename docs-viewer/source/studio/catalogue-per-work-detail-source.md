---
doc_id: catalogue-per-work-detail-source
title: Catalogue Per-Work Detail Source
added_date: 2026-06-22
last_updated: 2026-06-22
parent_id: studio
viewable: true
---
# Catalogue Per-Work Detail Source

## Implementation Note

Implemented on 2026-06-22.

- Migrated `studio/data/canonical/catalogue/work_details.json` into per-work files under `studio/data/canonical/catalogue/work_details/`.
- Moved the retired flat source to `studio/data/canonical/catalogue/retired/work_details.flat.v2.json`.
- Moved retired generated Studio lookup artifacts under `studio/data/generated/catalogue-lookup/retired/`.
- Kept retained generated lookup runtime files to `work_search.json`, `series_search.json`, and `series/{series_id}.json`.
- Replaced work and work-detail focused generated lookup reads with service projections for `catalogue_work_record` and `catalogue_work_detail_record`.
- Updated source loading, validation, write transactions, workbook import apply, delete plans, bulk/detail-section writes, frontend config, and tests for the per-work detail source model.

## Summary

Canonical work-detail source data is held in one nested canonical work-detail file per `work_id`.

The model treats detail sections and details as a work-owned aggregate:

- `works.json` remains the canonical source for primary work metadata.
- each detailed work gets one canonical detail-source file keyed by `work_id`.
- generated Studio search/list lookup and public JSON keep their current output contracts.
- targeted work and work-detail editor reads become service projections over canonical source rather than generated per-record lookup files.

This keeps canonical authoring data aligned with the current work editor, where detail sections and detail images are browsed, created, edited, deleted, and rebuilt through the parent work.

## Source Ownership

Canonical detail source is a directory of per-work records:

```text
studio/data/canonical/catalogue/work_details/
  00001.json
  00158.json
  00782.json
```

Only works with detail sections need a file. A work with no detail sections has no detail-source file.

Empty sections are not allowed in the target source model. A detail section should exist only when it owns at least one detail record, matching the current UI rule that section creation starts from one or more selected image files.

## JSON Structures

### `works.json`

Primary work metadata is in `studio/data/canonical/catalogue/works.json`.

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

## Lookup And Read Model

For targeted work-editor and work-detail-editor operations, the service should read only the relevant source records:

```text
studio/data/canonical/catalogue/works.json
studio/data/canonical/catalogue/series.json
studio/data/canonical/catalogue/work_details/{work_id}.json
```

A request for `detail_uid` can derive `work_id` from the UID prefix, load `work_details/{work_id}.json`, and find the child detail inside that one aggregate. That path does not require a global detail index.

The frontend should still avoid direct canonical-file reads. It should request a service projection such as "work editor payload for `work_id`" or "detail editor payload for `detail_uid`". The server/helper boundary should own schema validation, parent/child resolution, and any derived fields the UI needs.

### Studio Lookup File Contract

Generated lookup files:

| Runtime path | Schema | Decision |
| --- | --- | --- |
| `studio/data/generated/catalogue-lookup/work_search.json` | `studio_catalogue_lookup_work_search_v1` | Keep unchanged. Work search does not need detail records. |
| `studio/data/generated/catalogue-lookup/series_search.json` | `studio_catalogue_lookup_series_search_v1` | Keep unchanged. |
| `studio/data/generated/catalogue-lookup/series/{series_id}.json` | `studio_catalogue_lookup_series_record_v1` | Keep unchanged. |

Lookup JSON shapes:

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

### Service Read Payloads

Per-record lookup reads have been replaced with service-only read payloads. These are API contracts, not generated files.

Work editor read:

```text
GET /studio/api/catalogue/read?key=catalogue_work_record&record_id={work_id}
```

JSON:

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

JSON:

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

## Helper API Boundary

Catalogue code depends on helper functions that hide canonical storage shape.

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