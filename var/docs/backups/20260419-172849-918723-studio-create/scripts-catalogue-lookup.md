---
doc_id: scripts-catalogue-lookup
title: Catalogue Lookup Export
last_updated: 2026-04-17
parent_id: scripts
sort_order: 72
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
