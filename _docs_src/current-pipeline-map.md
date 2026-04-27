---
doc_id: new-pipeline-current-pipeline-map
title: "Current Pipeline Map"
added_date: 2026-04-17
last_updated: 2026-04-27
parent_id: new-pipeline
sort_order: 10
---

# Current Pipeline Map

This document maps the current workbook-led catalogue pipeline to the responsibilities a web-based Studio system must replace or preserve.

## Current Source Boundary

Current canonical catalogue source:

- `data/works.xlsx`
  - `Works`
  - `Series`
  - `SeriesSort`
  - `WorkDetails`
  - `WorkFiles`
  - `WorkLinks`
- canonical source media and legacy prose under `DOTLINEFORM_PROJECTS_BASE_DIR`
  - work primary images
  - work detail images
- current media source images
- repo-local catalogue prose under `_docs_src_catalogue/`
  - work prose Markdown
  - series prose Markdown
  - moment prose Markdown
- moment metadata records under `assets/studio/data/catalogue/moments.json`

The workbook is currently both an editing interface and a source database. The generator also writes operational state back into the workbook, including `status`, `published_date`, and image dimensions.

## Current Orchestrator

Current entrypoint:

```bash
./scripts/build_catalogue.py
```

Primary responsibilities:

- load `data/works.xlsx`
- fingerprint workbook rows for works, series, work details, work files, and work links
- fingerprint moment metadata and repo-local moment prose sources
- fingerprint source media and prose files
- compare those fingerprints with `var/build_catalogue_state.json`
- infer affected work IDs, detail UIDs, series IDs, and moment IDs
- preflight workbook/source validity
- run media copy and srcset scripts for affected media records
- call `generate_work_pages.py` with scoped ID manifests and `--only` artifact flags
- clean stale generated files and local media for removed source rows
- migrate or prune Studio tag assignments when series IDs or works are removed
- rebuild catalogue search with `build_search.rb --scope catalogue`
- update build activity feeds
- update planner state after successful write runs

The key design point is that `build_catalogue.py` is a planner and orchestrator. It is not the main transformation layer from source metadata to public JSON.

## Current Generator

Current generator:

```bash
./scripts/generate_work_pages.py
```

Primary responsibilities:

- read workbook sheets
- normalize IDs, dates, lists, text, dimensions, and status values
- validate workbook/source references with the shared preflight
- build canonical in-memory records for works, work details, series, files, and links
- render work, series, and moment prose through the local Jekyll stack
- write minimal route stubs:
  - `_works/*.md`
  - `_series/*.md`
  - `_work_details/*.md`
  - `_moments/*.md`
- write existing runtime JSON artifacts:
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/data/recent_index.json`
  - `assets/data/moments_index.json`
  - `assets/series/index/<series_id>.json`
  - `assets/works/index/<work_id>.json`
  - `assets/moments/index/<moment_id>.json`
- write the Studio-only storage companion:
  - `assets/studio/data/work_storage_index.json`
- update workbook-backed publication state:
  - `status`
  - `published_date`
  - `width_px`
  - `height_px`
- stage work download files from `WorkFiles`
- sync missing series rows into `assets/studio/data/tag_assignments.json`

The generator is the main source-to-runtime transformation layer. The new system should preserve most transformation logic while replacing its workbook reader/writer with a JSON source adapter.

## Current Workbook Sheet Mapping

### `Works`

Role:

- one source row per work
- primary key is `work_id`
- controls public work metadata, series membership, source image lookup, source prose lookup, and curator storage metadata

Important current fields:

- `work_id`
- `status`
- `published_date`
- `series_ids`
- `project_folder`
- `project_filename`
- `title`
- `width_cm`
- `height_cm`
- `depth_cm`
- `year`
- `year_display`
- `medium_type`
- `medium_caption`
- `storage_location`
- `work_prose_file`
- `notes`
- `duration`
- `width_px`
- `height_px`
- `provenance`
- `artist`

Current generated outputs:

- `_works/<work_id>.md`
- `assets/works/index/<work_id>.json`
- `assets/data/works_index.json`
- `assets/studio/data/work_storage_index.json`
- `assets/data/recent_index.json` when a work is newly published
- `assets/data/search/catalogue/index.json` after search rebuild

### `WorkDetails`

Role:

- one source row per additional image/detail for a work
- composite identity is `<work_id>-<detail_id>`
- grouped into sections by `project_subfolder`

Important current fields:

- `work_id`
- `detail_id`
- `project_subfolder`
- `project_filename`
- `title`
- `status`
- `published_date`
- `width_px`
- `height_px`

Current generated outputs:

- `_work_details/<work_id>-<detail_id>.md`
- detail sections inside `assets/works/index/<work_id>.json`
- search rebuild after generation

### `Series`

Role:

- one source row per series
- primary key is `series_id`
- controls series metadata, series prose lookup, primary thumbnail work, and the series page route

Important current fields:

- `series_id`
- `title`
- `series_type`
- `status`
- `published_date`
- `year`
- `year_display`
- `primary_work_id`
- `series_prose_file`
- `notes`

Current generated outputs:

- `_series/<series_id>.md`
- `assets/series/index/<series_id>.json`
- `assets/data/series_index.json`
- `assets/data/recent_index.json` when a series is newly published
- `assets/studio/data/tag_assignments.json` missing-row sync
- search rebuild after generation

### `SeriesSort`

Role:

- optional per-series sort rules
- primary key is `series_id`
- currently feeds `series_sort` and ordered membership calculations

Important current fields:

- `series_id`
- `sort_fields`

Replacement note:

- this should become a `sort_fields` property on the canonical series JSON record unless keeping it separate materially improves editing or import behavior

### `WorkFiles`

Role:

- optional downloadable files for a work
- sourced from the work project folder
- staged under media storage during generation

Important current fields:

- `work_id`
- `filename`
- `label`
- `status`
- `published_date`

Current generated outputs:

- staged files under `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/`
- `work.downloads` inside `assets/works/index/<work_id>.json`

### `WorkLinks`

Role:

- optional published links for a work

Important current fields:

- `work_id`
- `URL`
- `label`
- `status`
- `published_date`

Current generated outputs:

- `work.links` inside `assets/works/index/<work_id>.json`

## Current Runtime-Critical Artifacts

The new pipeline should avoid schema changes to these files unless a later requirement explicitly needs them:

- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/data/recent_index.json`
- `assets/data/moments_index.json`
- `assets/series/index/<series_id>.json`
- `assets/works/index/<work_id>.json`
- `assets/moments/index/<moment_id>.json`
- `assets/data/search/catalogue/index.json`
- `_works/*.md`
- `_series/*.md`
- `_work_details/*.md`
- `_moments/*.md`

These files are generated public/runtime artifacts. They should not become the editing source of truth because they already contain derived values, rendered prose HTML, aggregate indexes, and runtime-oriented projections.

## Replacement Mapping

| Current responsibility | Current owner | New owner |
| --- | --- | --- |
| edit work metadata | Excel workbook | Studio work editor writing canonical source JSON |
| edit work-detail metadata | Excel workbook | Studio work-detail editor writing canonical source JSON |
| edit series metadata | Excel workbook | Studio series editor writing canonical source JSON |
| edit series membership | `Works.series_ids` cells | Studio work editor and series editor writing canonical source JSON |
| add a series | `Series` row | Studio new-series flow writing canonical source JSON |
| bulk metadata edits | Excel filtering/fill | Studio bulk edit preview/apply flow |
| import new works/details | Excel workbook | optional workbook/CSV import into source JSON |
| source validation | generator preflight | shared JSON source validator used by Studio and generator |
| publish state updates | generator writes workbook | generator or write service updates source JSON |
| dimension updates | generator writes workbook | generator or media probe updates source JSON |
| public route and JSON generation | `generate_work_pages.py` | refactored generator using JSON source adapter |
| media copy/srcset | `copy_draft_media_files.py`, `make_srcset_images.sh`, orchestrated by `build_catalogue.py` | scoped JSON build stages work/detail source images under `var/catalogue/media/`, generates srcset derivatives there, copies thumbnails into `assets/`, and leaves primary derivatives staged for remote publishing |
| catalogue search rebuild | `build_catalogue.py` tail | explicit local build action after source/generation changes |
| planner state | `var/build_catalogue_state.json` based on workbook fingerprints | new planner state based on canonical source JSON fingerprints |

## Logic To Preserve

The new system should preserve the following current logic unless a later phase intentionally changes it:

- ID normalization:
  - work IDs remain five-digit strings
  - detail IDs remain three-digit strings within a work
  - detail UIDs remain `<work_id>-<detail_id>`
  - series IDs use existing `normalize_series_id` behavior
- status gating:
  - source records with blank or unknown status are not generated
  - `draft` records are actionable
  - `published` records are included in indexes and regenerated when selected or forced
- publish transition semantics:
  - first publication sets `published_date`
  - `/recent/` entries are snapshots, not always-live title mirrors
- series membership:
  - works can belong to more than one series
  - the first series ID is the primary series
  - `Series.primary_work_id` must belong to the series
- prose resolution:
  - work prose is resolved from `project_folder` plus `work_prose_file`
  - series prose is resolved from `primary_work_id` project folder plus `series_prose_file`
- work detail grouping:
  - `project_subfolder` defines detail sections
  - details sort by `detail_id` inside a section
- generated output determinism:
  - stable ordering
  - stable checksums/versions
  - compact JSON objects where the current generator compacts them
- stale cleanup:
  - removed works, work details, series, and moments require generated-artifact cleanup
  - removed works and series require tag assignment cleanup

## Logic To Retire Or Isolate

The new system should retire or isolate these workbook-specific behaviors:

- treating `data/works.xlsx` as canonical
- writing publication state and dimensions back to `data/works.xlsx`
- reading formula cache values from Excel
- relying on worksheet names and column positions at runtime
- using Excel as the normal way to edit existing published records

The workbook can remain useful as an import format, an export/reporting format, or a bulk-add staging surface. It should not be a second source of truth for currently published records.
