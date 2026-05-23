---
doc_id: data-models-catalogue-maintenance
title: Catalogue Model Maintenance
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: catalogue
sort_order: 18000
viewable: true
---
# Catalogue Model Maintenance

## Dependencies And Enforcement

Important dependencies:

- `_work_details/*.md` depends on the parent work record for canonical detail data
- `works_index.json` depends on valid `series_ids` membership
- `series_index.json` depends on ordered work membership and stable `sort_fields`
- catalogue search depends on series/work/moment data plus Studio tag data from:
  - `assets/studio/data/tag_assignments.json`
  - `assets/studio/data/tag_registry.json`

Current enforcement visible in code:

- the generator writes and hashes the shared catalogue indexes and per-record catalogue payloads
- the search builder writes the catalogue search artifact from those generated JSON families plus Studio tag data
- the generator keeps `_moments`, `_series`, and `_works` stubs minimal and current
- the audit script checks:
  - `detail_uid` and `work_id` consistency
  - `series_index` membership integrity
  - `works_index` `series_ids`
  - JSON header and root-shape expectations
  - `tag_assignments` references back into series/work membership

## Performance Notes

The catalogue model is optimized for the current static-site runtime:

- `/series/` reads only shared indexes
- `/recent/` reads only the recent-publications index
- `/series/<series_id>/` reads one per-series record, not one record per work
- `/works/<work_id>/` reads one work-local payload that already contains all detail sections
- `/work_details/<detail_uid>/` reuses the work-local payload instead of requiring a second fetch family
- `/search/` reads one search-optimized catalogue artifact rather than scanning several unrelated indexes in the browser

This is the main reason the catalogue model looks more normalized than a single-page-site JSON dump.

## Practical Update Rule

If a change affects:

- list/grid cards or cross-page lookup
  update the relevant shared index model here
- page-local prose, detail sections, or page hydration
  update the relevant per-record model here
- search-visible structured fields
  update this doc and the relevant search docs together
