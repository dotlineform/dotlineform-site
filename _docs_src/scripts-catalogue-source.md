---
doc_id: scripts-catalogue-source
title: "Catalogue Source Utilities"
last_updated: 2026-04-18
parent_id: scripts
sort_order: 60
---
# Catalogue Source Utilities

These utilities validate and compare the canonical catalogue source JSON.

They do not write runtime-critical public catalogue artifacts. They work against canonical source JSON under:

```text
assets/studio/data/catalogue/
```

The Phase 0 workbook export fixture is now retired. Canonical source JSON is maintained directly through Studio and the workbook import flow.

## Validate

```bash
python3 ./scripts/validate_catalogue_source.py
```

Validation checks the source JSON for the same core relationship errors covered by the current catalogue validations:

- malformed work, detail, and series IDs
- source map keys that do not match normalized record IDs
- work `series_ids` references to unknown series
- series `primary_work_id` references to unknown works
- series `primary_work_id` values that are not members of that series
- work details, files, and links that reference unknown works when actionable

## Compare

```bash
python3 ./scripts/compare_catalogue_sources.py
```

The comparison loads:

- workbook-normalized records from `data/works.xlsx`
- JSON-normalized records from `assets/studio/data/catalogue/`

It reports count mismatches, missing IDs, extra IDs, and record differences. During the transition away from workbook-led maintenance, intentional JSON-side edits may also appear here and should be inspected case by case.

## Shared Module

Shared source loading, normalization, validation, and comparison logic lives in:

```text
scripts/catalogue_source.py
```

This module is a migration fixture and compatibility adapter. It is not yet the final native generator data layer.

## Related References

- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
