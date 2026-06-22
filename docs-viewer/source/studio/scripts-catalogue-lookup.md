---
doc_id: scripts-catalogue-lookup
title: Catalogue Lookup Export
added_date: 2026-04-17
last_updated: 2026-06-16
parent_id: studio
viewable: true
---
# Catalogue Lookup Export

Script:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/export_catalogue_lookup.py
```

## Purpose

This script builds the derived Studio lookup payloads used by the catalogue editors in Phase 8.

The lookup payloads are explicitly non-canonical. They exist to support:

- lightweight work search
- lightweight series search
- lightweight detail search
- focused per-record reads for work, transitional detail lookup consumers, and series routes

Lookup payloads do not include full-source `record_hash` values. Studio save endpoints apply submitted changes to the current source record and return the normalized saved record.

Canonical write ownership remains with:

- `site/assets/studio/data/catalogue/works.json`
- `site/assets/studio/data/catalogue/work_details.json`
- `site/assets/studio/data/catalogue/series.json`

## Optional Flags

- `--source-dir assets/studio/data/catalogue`: canonical source input directory
- `--lookup-dir assets/studio/data/catalogue_lookup`: derived lookup output directory
- `--write`: write the lookup files

Without `--write`, the script prints the export plan only.

## Outputs

Root lookup files:

- `site/assets/studio/data/catalogue_lookup/work_search.json`
- `site/assets/studio/data/catalogue_lookup/series_search.json`
- `site/assets/studio/data/catalogue_lookup/work_detail_search.json`

Focused record lookup files:

- `site/assets/studio/data/catalogue_lookup/works/<work_id>.json`
- `site/assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`
- `site/assets/studio/data/catalogue_lookup/series/<series_id>.json`

Work lookup `detail_sections` joins `work_detail_sections` with detail records. Each section projects `section_id`, `details_subfolder`, `section_title`, `section_order`, `detail_sort`, `count`, and `details[]`.

Nested work lookup detail summaries contain detail-owned fields only: `detail_uid`, `detail_id`, `title`, and `project_filename`. They do not repeat `section_id`, `section_title`, `details_subfolder`, `section_order`, or `detail_sort`.

Lookup export expects the v2 work-detail source shape. Focused detail lookup records still join section metadata onto the detail record for transitional consumers, but the standalone Studio work-detail editor route is retired.

## Runtime Use

The catalogue editors use these files as follows:

- work editor:
  - search from `work_search.json`
  - focused record load from `works/<work_id>.json`
- transitional detail lookup consumers:
  - search from `work_detail_search.json`
  - focused record load from `work_details/<detail_uid>.json`
- series editor:
  - search from `series_search.json`
  - focused record load from `series/<series_id>.json`
  - add-work validation from `work_search.json`

## Refresh Flow

The catalogue write server refreshes these lookup payloads after canonical catalogue source writes.
Run the export script manually when a full derived lookup refresh is needed outside a write flow.
