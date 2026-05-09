---
doc_id: new-pipeline-source-model
title: "Source Model"
added_date: 2026-04-17
last_updated: 2026-05-02
parent_id: archive
sort_order: 20
---

# Source Model

Archived: current catalogue source-model details now live in [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue), with script behavior documented under [Scripts](/docs/?scope=studio&doc=scripts).

This document specifies the proposed JSON source model for the web-based catalogue pipeline.

## Design Principles

- JSON source files become canonical for catalogue metadata.
- Existing public/runtime JSON files remain generated artifacts.
- Runtime-critical JSON schemas should remain unchanged in the first migration.
- The source JSON should mirror the current workbook concepts closely enough to reduce migration risk.
- Source files should be easy for Studio to fetch and for the local write service to update with backups.
- The source model should support small targeted writes, deterministic diffs, validation, and bulk edits.
- Excel import/export can exist, but it must be a controlled import path into JSON, not a parallel editing source.

## Proposed File Location

Recommended source root:

```text
assets/studio/data/catalogue/
```

Recommended files:

```text
assets/studio/data/catalogue/works.json
assets/studio/data/catalogue/work_details.json
assets/studio/data/catalogue/series.json
assets/studio/data/catalogue/meta.json
```

Why this location:

- Studio can fetch these files from the local Jekyll server without a custom read endpoint.
- The existing local-write pattern already treats `assets/studio/data/` as Studio-owned data.
- The files are not public catalogue runtime artifacts, even though they are locally served during development.
- The write service can enforce a narrow allowlist for only this source-data directory.

Alternative:

- Store source files under `data/catalogue/` and expose read-only generated mirrors under `assets/studio/data/catalogue/`.

That gives a cleaner source-data root but adds another sync layer. For this project, the simpler `assets/studio/data/catalogue/` path is likely the better first implementation.

## File Granularity

Use one file per current workbook table rather than one monolithic file.

Benefits:

- smaller diffs
- safer write allowlists
- simpler bulk edit targeting
- easier import previews
- fewer merge conflicts if unrelated sections are edited manually
- page code can load only the families it needs

Tradeoff:

- validation must join across files for referential checks
- save operations that touch multiple families need atomic write behavior or a backup bundle

## Shared Header

Each source file should use a common top-level shape:

```json
{
  "header": {
    "schema": "catalogue_source_works_v1",
    "count": 0
  },
  "works": {}
}
```

Header requirements:

- `schema`: stable schema identifier
- `count`: number of records in the primary map

Source headers should avoid volatile timestamps so small source edits produce focused Git diffs. Write timestamps belong in activity artifacts and JSONL logs.

Optional future header fields:

- `source_exported_from`: for one-time workbook migration metadata
- `last_import_id`: for workbook/CSV imports
- `source_version`: deterministic content hash if planner behavior needs it

## `works.json`

Primary map:

```json
{
  "header": {
    "schema": "catalogue_source_works_v1",
    "count": 1
  },
  "works": {
    "00456": {
      "work_id": "00456",
      "status": "published",
      "published_date": "2026-04-17",
      "series_ids": ["001"],
      "project_folder": "example-project",
      "project_filename": "example.jpg",
      "title": "example title",
      "width_cm": 20,
      "height_cm": 30,
      "depth_cm": null,
      "year": 2026,
      "year_display": "2026",
      "medium_type": "drawing",
      "medium_caption": "ink on paper",
      "duration": null,
      "storage_location": "box 1",
      "notes": "",
      "provenance": "",
      "artist": "Michael Davies",
      "width_px": 1200,
      "height_px": 1600
    }
  }
}
```

Field notes:

- Keep `work_id` duplicated inside the record for readability and export compatibility.
- Keep `series_ids` as an ordered array.
- The first `series_ids` item remains the primary series.
- `width_px` and `height_px` remain source metadata once measured; they are no longer written back to the workbook.
- Work prose uses the ID-derived source path `_docs_catalogue/works/<work_id>.md`; there is no source filename override field.
- Series titles are derived from the related series records rather than stored redundantly on work records.
- Internal fields such as `storage_location`, `notes`, and `provenance` can remain in source JSON, but only approved projections should reach runtime public JSON.

## `work_details.json`

Primary map:

```json
{
  "header": {
    "schema": "catalogue_source_work_details_v1",
    "count": 1
  },
  "work_details": {
    "00456-001": {
      "detail_uid": "00456-001",
      "work_id": "00456",
      "detail_id": "001",
      "details_subfolder": "details",
      "section_id": "00456-1",
      "section_title": "details",
      "project_filename": "detail.jpg",
      "title": "detail",
      "status": "published",
      "published_date": "2026-04-17",
      "width_px": 1200,
      "height_px": 900
    }
  }
}
```

Field notes:

- The map key is `detail_uid`.
- `detail_uid` is derived from `work_id` and `detail_id`, but it should be stored in the record to keep import/export and preview output clear.
- `work_id` must reference an existing work.
- `details_subfolder` is optional source-image path metadata under the parent work's `project_folder`. Empty values are omitted.
- `section_id` is the stable generated logical section key for public work JSON, using `<work_id>-<number>`.
- `section_title` is the public section label and is required.
- `sort_order` is optional section ordering metadata. It applies to sections, not to detail ordering within a section.
- Detail records no longer use legacy `project_subfolder`; source image paths and public section labels are separate fields.

## `series.json`

Primary map:

```json
{
  "header": {
    "schema": "catalogue_source_series_v1",
    "count": 1
  },
  "series": {
    "001": {
      "series_id": "001",
      "title": "example series",
      "series_type": "primary",
      "status": "published",
      "published_date": "2026-04-17",
      "year": 2026,
      "year_display": "2026",
      "primary_work_id": "00456",
      "notes": "",
      "sort_fields": "work_id"
    }
  }
}
```

Field notes:

- `sort_fields` replaces the separate `SeriesSort` table for the JSON-first model.
- `primary_work_id` must reference a work whose `series_ids` includes this series when the series is publishable; draft source records may omit it temporarily.
- `series_type` should remain explicit because Studio currently distinguishes primary series from other holdings/curated groups.
- Series prose uses the ID-derived source path `_docs_catalogue/series/<series_id>.md`; there is no source filename override field.

## Work-Owned Files And Links

Files and links are work-owned metadata in `works.json`, not separate source files.

```json
{
  "downloads": [
    {
      "filename": "example.pdf",
      "label": "PDF"
    }
  ],
  "links": [
    {
      "url": "https://example.com",
      "label": "publisher"
    }
  ]
}
```

Field notes:

- empty `downloads` and `links` arrays may be omitted
- file/link `status` and `published_date` are retired because publishing is owned by the parent work record
- external file storage is unchanged; the source model stores metadata references only

## `meta.json`

Purpose:

- record source schema metadata that does not belong to one table
- record next-ID helper state only if it cannot be derived safely

Shape:

```json
{
  "header": {
    "schema": "catalogue_source_meta_v1"
  },
  "source": {
    "canonical": "json"
  },
  "id_policy": {
    "work_id_width": 5,
    "detail_id_width": 3
  }
}
```

Avoid storing mutable counters unless needed. For work IDs and detail IDs, deriving the next available ID from source records is less fragile than maintaining a counter.

## Activity Artifacts

Studio should have a small activity summary artifact for catalogue source and build events:

```text
var/studio/activity/activity_log.json
```

Recommended shape:

```json
{
  "header": {
    "schema": "activity_log_v1",
    "updated_at_utc": "2026-04-17T00:00:00Z",
    "count": 1
  },
  "entries": [
    {
      "id": "2026-04-17T00:00:00Z-catalogue-work-save",
      "time_utc": "2026-04-17T00:00:00Z",
      "kind": "source_save",
      "operation": "work.save",
      "status": "completed",
      "summary": "Saved 1 work source record.",
      "affected": {
        "works": ["00456"],
        "series": [],
        "work_details": []
      },
      "log_ref": "var/studio/catalogue/logs/catalogue_write_server.log"
    }
  ]
}
```

Purpose:

- give Studio a fast read model for recent catalogue data changes
- avoid parsing raw JSONL logs in the browser
- let the activity UI start small while preserving links to fuller logs

The local service should still keep append-only JSONL logs under:

```text
var/studio/catalogue/logs/
```

The summary artifact is a UI convenience. It is not canonical catalogue data.

## Canonical Versus Derived Fields

Canonical source fields:

- user-entered metadata from the current workbook tables
- publication state
- measured pixel dimensions once accepted into source
- stable row IDs for files and links
- series sort fields

Derived runtime fields:

- generated payload headers and content hashes
- `generated_at_utc`
- rendered `content_html`
- series work membership lists inside `assets/data/series_index.json`
- `project_folders` aggregates
- detail `sections`
- `work.downloads` URL-safe filenames
- `work.links` public projection
- catalogue search records
- recent index grouping/snapshot behavior

The source JSON should not try to store every generated field. Keeping source and generated projections separate reduces drift and keeps the public runtime contracts stable.

## Deletion Model

For the first implementation, use hard deletes from source JSON only after a preview confirms impact.

Delete preview should report:

- source records to remove
- generated route stubs to remove
- per-record JSON artifacts to remove
- local media derivatives that would become stale
- tag assignment rows or overrides affected
- search rebuild requirement
- recent index pruning impact

Optional future soft-delete:

- add `status: "deleted"` or an `archived` source area if accidental deletion becomes a real risk.

For v1, backups and preview/apply are probably enough.

## Bulk Edit Model

Bulk edits should be structured operations, not raw JSON patches.

Recommended operation shape:

```json
{
  "target": "works",
  "selector": {
    "work_ids": ["00456", "00457"],
    "range": null
  },
  "operation": {
    "field": "medium_type",
    "value": "drawing",
    "mode": "set"
  }
}
```

Supported initial selectors:

- explicit `work_ids`
- inclusive work ID range
- works in one series
- explicit `detail_uids`
- detail UIDs under one work

Supported initial operations:

- set scalar field
- clear scalar field
- append series ID to `series_ids`
- remove series ID from `series_ids`
- replace primary series by reordering `series_ids`

Bulk edit must always have preview and apply steps. The preview should list changed records, old values, new values, validation errors, and downstream build scope.

## Workbook Import Model

Workbook import should be additive or explicitly mapped, never silently authoritative over currently published records.

Recommended import modes:

- `add-new-only`
  - add records whose IDs do not already exist
  - reject existing IDs

Initial implemented workbook import scope:

- configured workbook source from `_data/pipeline.json`, currently `data/works_bulk_import.xlsx`
- one Studio route with two modes:
  - new `Works`
  - new `WorkDetails`
- imported records default to `draft`
- workbook `status` fields are ignored
- no workbook writeback
- existing JSON records are reported as duplicates and skipped
- works import requires referenced series to already exist
- work-details import requires the parent work to already exist

Import preview should report:

- new works
- new work details
- duplicate existing IDs
- unknown series references
- orphaned details
- IDs that need normalization

This keeps Excel useful for bulk additions without letting it overwrite the canonical JSON source by accident.
