---
doc_id: scripts-catalogue-lookup
title: "Catalogue Lookup Export"
added_date: 2026-04-17
last_updated: 2026-05-02
parent_id: scripts
sort_order: 110
---
# Catalogue Lookup Export

Script:

```bash
python3 ./scripts/export_catalogue_lookup.py
```

## Purpose

This script builds the derived Studio lookup payloads used by the catalogue editors in Phase 8.

The lookup payloads are explicitly non-canonical. They exist to support:

- lightweight work search
- lightweight series search
- lightweight detail search
- focused per-record editor reads for work, detail, and series routes

Lookup payloads do not include full-source `record_hash` values. Studio save endpoints apply submitted changes to the current source record and return the normalized saved record.

Canonical write ownership remains with:

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`
- `assets/studio/data/catalogue/series.json`

## Optional Flags

- `--source-dir assets/studio/data/catalogue`: canonical source input directory
- `--lookup-dir assets/studio/data/catalogue_lookup`: derived lookup output directory
- `--write`: write the lookup files

Without `--write`, the script prints the export plan only.

## Outputs

Root lookup files:

- `assets/studio/data/catalogue_lookup/meta.json`
- `assets/studio/data/catalogue_lookup/work_search.json`
- `assets/studio/data/catalogue_lookup/series_search.json`
- `assets/studio/data/catalogue_lookup/work_detail_search.json`

Focused record lookup files:

- `assets/studio/data/catalogue_lookup/works/<work_id>.json`
- `assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`
- `assets/studio/data/catalogue_lookup/series/<series_id>.json`

Work lookup `detail_sections` group details by `section_id`, display `section_title`, and preserve section `sort_order`. Detail summaries include `details_subfolder` and `project_filename` so Studio can reconstruct source-image edit paths without treating public section labels as media paths.

Until the media-section source migration is written, lookup export derives the same section ids the migration would write. Legacy detail rows with `project_subfolder: "details"` are exposed to Studio as generated ids such as `00001-1`, with `section_title` and `details_subfolder` set from the legacy value. Focused detail lookup records omit legacy detail `project_subfolder`; that field remains only in canonical source JSON until the write migration removes it.

## Runtime Use

The catalogue editors use these files as follows:

- work editor:
  - search from `work_search.json`
  - focused record load from `works/<work_id>.json`
- work detail editor:
  - search from `work_detail_search.json`
  - focused record load from `work_details/<detail_uid>.json`
- series editor:
  - search from `series_search.json`
  - focused record load from `series/<series_id>.json`
  - add-work validation from `work_search.json`

## Dev Studio

`bin/dev-studio` now runs this export before starting Jekyll and the local write services.

The catalogue write server also refreshes these lookup payloads after canonical catalogue source writes.
