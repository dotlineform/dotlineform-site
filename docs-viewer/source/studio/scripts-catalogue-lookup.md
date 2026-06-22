---
doc_id: scripts-catalogue-lookup
title: Catalogue Lookup Export
added_date: 2026-04-17
last_updated: 2026-06-22
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
- focused per-record reads for series routes

Work and work-detail focused reads are service projections from canonical source, not generated lookup files.
Lookup payloads do not include full-source `record_hash` values. Studio save endpoints apply submitted changes to the current source record and return the normalized saved record.

Canonical write ownership remains with:

- `studio/data/canonical/catalogue/works.json`
- `studio/data/canonical/catalogue/work_details/<work_id>.json`
- `studio/data/canonical/catalogue/series.json`

## Optional Flags

- `--source-dir studio/data/canonical/catalogue`: canonical source input directory
- `--lookup-dir studio/data/generated/catalogue-lookup`: derived lookup output directory
- `--write`: write the lookup files

Without `--write`, the script prints the export plan only.

## Outputs

Root lookup files:

- `site/assets/studio/data/catalogue_lookup/work_search.json`
- `site/assets/studio/data/catalogue_lookup/series_search.json`

Focused record lookup files:

- `site/assets/studio/data/catalogue_lookup/series/<series_id>.json`

Retired lookup outputs live under `studio/data/generated/catalogue-lookup/retired/` only for migration comparison.
Runtime code must not read generated `works/<work_id>.json`, `work_details/<detail_uid>.json`, or `work_detail_search.json`.

## Runtime Use

The catalogue editors use these files as follows:

- work editor:
  - search from `work_search.json`
  - focused record load from `GET /studio/api/catalogue/read?key=catalogue_work_record&record_id=<work_id>`
- series editor:
  - search from `series_search.json`
  - focused record load from `series/<series_id>.json`
  - add-work validation from `work_search.json`

## Refresh Flow

The catalogue write server refreshes these lookup payloads after canonical catalogue source writes.
Run the export script manually when a full derived lookup refresh is needed outside a write flow.
