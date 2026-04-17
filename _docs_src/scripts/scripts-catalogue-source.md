---
doc_id: scripts-catalogue-source
title: Catalogue Source Export
last_updated: 2026-04-17
parent_id: scripts
sort_order: 55
---

# Catalogue Source Export

These scripts implement Phase 0 of the JSON-led catalogue pipeline.

They do not write runtime-critical public catalogue artifacts. They only export and check canonical source JSON under:

```text
assets/studio/data/catalogue/
```

## Export

Dry-run:

```bash
./scripts/export_catalogue_source.py
```

Write source JSON:

```bash
./scripts/export_catalogue_source.py --write
```

Default input:

- `data/works.xlsx`

Default outputs:

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`
- `assets/studio/data/catalogue/series.json`
- `assets/studio/data/catalogue/work_files.json`
- `assets/studio/data/catalogue/work_links.json`
- `assets/studio/data/catalogue/meta.json`

The source JSON headers are deterministic and avoid volatile timestamps. Activity timestamps belong in future catalogue activity artifacts and JSONL logs, not in canonical source files.

## Validate

```bash
./scripts/validate_catalogue_source.py
```

Validation checks the exported JSON source for the same core relationship errors covered by the current workbook preflight:

- malformed work, detail, and series IDs
- source map keys that do not match normalized record IDs
- work `series_ids` references to unknown series
- series `primary_work_id` references to unknown works
- series `primary_work_id` values that are not members of that series
- work details, files, and links that reference unknown works when actionable

## Compare

```bash
./scripts/compare_catalogue_sources.py
```

The comparison loads:

- workbook-normalized records from `data/works.xlsx`
- JSON-normalized records from `assets/studio/data/catalogue/`

It reports count mismatches, missing IDs, extra IDs, and record differences.

For a successful Phase 0 export, comparison should pass with no differences.

## Shared Module

Shared source loading, normalization, validation, and comparison logic lives in:

```text
scripts/catalogue_source.py
```

This module is a migration fixture and compatibility adapter. It is not yet the final native generator data layer.

Phase 1 reuse:

- `generate_work_pages.py --source json` now uses this module to materialize canonical source JSON into a temporary workbook adapter
- direct source validation and workbook-vs-JSON comparison remain owned by the scripts on this page

## Related References

- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
