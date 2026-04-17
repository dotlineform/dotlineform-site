---
doc_id: new-pipeline-web-system-spec
title: Web System Specification
last_updated: 2026-04-17
parent_id: new-pipeline
sort_order: 30
---

# Web System Specification

This document specifies the Studio web system that replaces workbook-led catalogue maintenance.

## Product Goal

Studio should become the normal local interface for catalogue source maintenance.

The first useful version is deliberately small:

- search for a work by `work_id`
- open one work
- edit core work metadata
- save to canonical source JSON through a local write service
- regenerate the existing runtime artifacts without changing their public contract

Later versions add work details, series, adds/deletes, bulk edits, and workbook import/export.

## System Boundary

The new system has four layers:

1. Studio pages
   - browser UI under `/studio/`
   - fetches source JSON and existing generated indexes
   - sends mutations to localhost write endpoints
2. local catalogue write service
   - localhost-only Python service
   - validates requests
   - writes only allowlisted source JSON files and backup/log paths
   - optionally invokes build/generation commands
3. source/generation library
   - shared Python code that loads canonical JSON source records
   - exposes the same normalized records the current generator builds from workbook rows
   - runs shared validation
4. existing runtime artifacts
   - route stubs and public JSON remain generated outputs
   - public pages continue to consume current runtime files

## Studio Routes

Recommended route progression:

- `/studio/catalogue/`
  - catalogue maintenance hub
  - search by work ID
  - search by series title
  - links to work, series, bulk edit, import, and build actions
- `/studio/catalogue/work/?work=<work_id>`
  - work metadata editor
  - first implementation target
- `/studio/catalogue/work-detail/?detail=<detail_uid>`
  - work detail metadata editor
  - can also be opened from the work editor
- `/studio/catalogue/series/?series=<series_id>`
  - series metadata and membership editor
- `/studio/catalogue/new-series/`
  - add-series flow
- `/studio/catalogue/bulk-edit/`
  - preview/apply bulk metadata edits
- `/studio/catalogue/import/`
  - optional workbook/CSV import preview/apply

The exact route names can change during implementation, but route ownership should stay within the Studio section.

## Search And Selection

Required search behavior:

- works are searched by `work_id`
- series are searched by `series_title`

Recommended first implementation:

- work search accepts exact or partial work ID text
- work search normalizes numeric input to five-digit work IDs when possible
- series search uses case-insensitive title matching
- series search displays `series_id`, title, status, and work count
- result rows link to the relevant editor page

Data needed for search:

- source `works.json` for authoritative work metadata
- source `series.json` for authoritative series metadata
- generated `assets/data/series_index.json` for current membership/work counts until source-side membership helpers exist

Series titles are not guaranteed unique. The UI should display the `series_id` in results and route by `series_id`.

## Work Metadata Editor

First-page scope:

- load one work by `work_id`
- display canonical source fields
- edit scalar metadata fields
- edit ordered `series_ids`
- save through local write service
- show validation errors inline
- show unsaved changes state
- show last saved timestamp

Initial editable fields:

- `status`
- `published_date`
- `series_ids`
- `project_folder`
- `project_filename`
- `title`
- `year`
- `year_display`
- `medium_type`
- `medium_caption`
- `duration`
- `height_cm`
- `width_cm`
- `depth_cm`
- `storage_location`
- `work_prose_file`
- `notes`
- `provenance`
- `artist`

Read-only or generated fields in v1:

- `work_id`
- `width_px`
- `height_px`

The editor can display pixel dimensions, but changes should initially come from the generator/media probe path to avoid accidental manual drift.

Save behavior:

- `Save` writes only source JSON.
- `Save and rebuild` can be added after the generator consumes JSON.
- Save payload includes the previous record version or hash so the server can reject stale writes.
- After save, the client reloads the source record or updates its baseline from the server response.

## Work Detail Editor

Second-page scope:

- open detail editor from a work page
- search/open by `detail_uid`
- edit one detail record
- save source JSON

Initial editable fields:

- `status`
- `published_date`
- `project_subfolder`
- `project_filename`
- `title`

Read-only or generated fields in v1:

- `detail_uid`
- `work_id`
- `detail_id`
- `width_px`
- `height_px`

The work editor should list details for the current work and link to each detail editor.

## Series Editor

Third-page scope:

- search/open by series title
- edit one series record
- edit membership through work `series_ids`
- change a work's series from either the work editor or series editor

Initial editable fields:

- `title`
- `series_type`
- `status`
- `published_date`
- `year`
- `year_display`
- `primary_work_id`
- `series_prose_file`
- `notes`
- `sort_fields`

Membership behavior:

- canonical membership lives on works as ordered `series_ids`
- series editor can present member works by scanning source works
- adding a work to a series updates that work's `series_ids`
- removing a work from a series updates that work's `series_ids`
- changing primary series reorders a work's `series_ids`
- changing `primary_work_id` validates that the work belongs to the series

This keeps one membership source of truth and avoids maintaining duplicate membership arrays in both work and series source records.

## New Series Flow

Required behavior:

- create a new `series_id`
- enter required metadata
- optionally select member works
- choose `primary_work_id`
- save to `series.json` and affected work `series_ids`

Validation:

- `series_id` must normalize to a valid series ID and not already exist
- `title` must be present
- `status` must be allowed
- `primary_work_id` must exist if provided
- `primary_work_id` must belong to the series when the series is publishable

Recommended ID behavior:

- let the user enter the ID explicitly in v1
- add a suggested next-ID helper later

## Delete Flow

Delete must be preview/apply, not a direct button.

Delete preview for works should show:

- work source record
- work details, files, and links that would be removed or orphaned
- series membership impact
- series whose `primary_work_id` would become invalid
- generated route and JSON artifacts to delete
- local media derivatives to delete, if available
- tag assignment overrides to remove
- search rebuild requirement

Delete preview for series should show:

- source series record
- affected work `series_ids`
- affected `primary_work_id`
- tag assignments row to remove
- generated route and JSON artifacts to delete
- search rebuild requirement

Apply behavior:

- write source JSON changes
- write backup bundle first
- run generation/stale cleanup as a separate explicit step or as `Delete and rebuild`

## Bulk Edit Flow

Required behavior:

- apply a metadata field change to a range or selected set of works/details
- preview all changes before writing
- reject invalid changes before apply

Initial target types:

- works by ID range
- works by explicit IDs
- works in a series
- work details by parent work
- work details by explicit UIDs

Initial operations:

- set scalar field
- clear scalar field
- add series to works
- remove series from works
- replace primary series
- set status for draft records

Bulk edit preview should show:

- selected record count
- changed record count
- unchanged record count
- per-record old and new values
- validation warnings and blockers
- downstream generation scope

Bulk edit apply should:

- write one backup bundle
- write all affected source files atomically where practical
- return changed IDs for optional generation

## Local Write Service

Recommended implementation:

- add `scripts/studio/catalogue_write_server.py`
- keep it separate from `tag_write_server.py` initially to preserve a clear write allowlist and reduce regression risk
- optionally extract shared localhost server utilities after both services stabilize

Security constraints:

- bind to `127.0.0.1` only
- allow CORS only for `http://localhost:*` and `http://127.0.0.1:*`
- write only allowlisted paths under:
  - `assets/studio/data/catalogue/*.json`
  - `var/studio/catalogue/backups/*`
  - `var/studio/catalogue/logs/*`
- never write source media or prose files from metadata editor endpoints
- keep request and event logs minimal
- never log full payloads by default

Recommended endpoints:

- `GET /health`
- `POST /catalogue/work/save`
- `POST /catalogue/work-detail/save`
- `POST /catalogue/series/save`
- `POST /catalogue/series/create`
- `POST /catalogue/delete-preview`
- `POST /catalogue/delete-apply`
- `POST /catalogue/bulk-preview`
- `POST /catalogue/bulk-apply`
- `POST /catalogue/import-preview`
- `POST /catalogue/import-apply`
- `POST /catalogue/build-preview`
- `POST /catalogue/build-apply`

Build endpoints can be added later. The first editor can save source JSON without invoking generation.

## Validation

Validation must be shared by:

- Studio client-side form feedback
- local write server
- generator
- import preview
- bulk edit preview

Server-side validation is authoritative.

Core blockers:

- malformed `work_id`
- duplicate IDs
- malformed `detail_id` or `detail_uid`
- detail references unknown work
- work references unknown series
- series has missing title
- series `primary_work_id` does not exist
- series `primary_work_id` is not a member
- invalid status
- invalid date string
- invalid numeric fields
- file/link records reference unknown work
- publishable work has missing required public metadata

Warnings:

- missing source image
- missing prose file
- missing dimensions
- blank optional display fields
- series has zero works
- work has no series
- published source record changed without rebuild

## Generator Changes

The generator should be refactored around a source adapter:

- `ExcelCatalogueSource`
  - existing workbook reader, kept for import comparison and fallback during migration
- `JsonCatalogueSource`
  - new canonical source reader
- normalized source records
  - shared shape used by artifact writers

First target:

- make JSON source generation produce byte-for-byte equivalent generated artifacts for unchanged data, except for expected timestamp/version changes.

Generator CLI should gain a source mode:

```bash
./scripts/generate_work_pages.py --source json --write
./scripts/generate_work_pages.py --source xlsx data/works.xlsx --write
```

After migration, JSON should become the default.

## Build Flow

The current `build_catalogue.py` couples source-change planning, media copy/srcset, generation, stale cleanup, search rebuild, and build activity.

New target flow:

1. Studio writes source JSON.
2. A build preview computes affected IDs from source JSON changes and media/prose fingerprints.
3. The user explicitly runs generation/search for the affected scope.
4. Media copy/srcset remains available as separate explicit actions.

Media behavior:

- `copy_draft_media_files.py` remains functionally the same.
- `make_srcset_images.sh` remains functionally the same.
- The new pipeline should not require `build_catalogue.py` to orchestrate media.
- Studio can display commands or expose local build endpoints that call those scripts explicitly.

Search behavior:

- after generation, run `build_search.rb --scope catalogue --write`
- no source JSON editor should directly edit search artifacts

## Versioning And Backups

Every write endpoint should:

- load current source files
- validate the incoming mutation
- write timestamped backups before writing source JSON
- write temp files then atomic replace where practical
- return changed IDs and source file paths
- append a minimal event log

Backups should be grouped per write operation:

```text
var/studio/catalogue/backups/<timestamp>-<operation>/
```

Log path:

```text
var/studio/catalogue/logs/catalogue_write_server.log
```

Log event fields:

- timestamp
- endpoint
- operation
- target family
- IDs changed
- status
- error class/message when failed

Do not log full record payloads unless a temporary debug mode is explicitly enabled.
