---
doc_id: scripts-catalogue-source
title: "Catalogue Source Utilities"
added_date: 2026-04-18
last_updated: 2026-05-01
parent_id: scripts
sort_order: 60
---
# Catalogue Source Utilities

These utilities validate and inspect the canonical catalogue source JSON.

They do not write runtime-critical public catalogue artifacts. They work against canonical source JSON under:

```text
assets/studio/data/catalogue/
```

The Phase 0 workbook export fixture is now retired. Canonical source JSON is maintained directly through Studio and the configured bulk-import flow.

## Validate

```bash
./scripts/validate_catalogue_source.py
```

Validation checks the source JSON for core relationship errors:

- malformed work, detail, and series IDs
- source map keys that do not match normalized record IDs
- work `series_ids` references to unknown series
- series `primary_work_id` references to unknown works
- series `primary_work_id` values that are not members of that series
- work details that reference unknown works when actionable

## Project State Report

```bash
./scripts/project_state_report.py --write
```

The project-state report compares `$DOTLINEFORM_PROJECTS_BASE_DIR/projects` with primary work image references in `assets/studio/data/catalogue/works.json`, then writes `_docs_src/project-state.md`.

Use this when you need to find source project folders or primary-image candidates that have not yet been represented in `works.json`. By default it scans only direct project folders; pass `--include-subfolders` when the review should include nested source folders too.

## Shared Module

Shared source loading, normalization, and validation logic lives in:

```text
scripts/catalogue_source.py
```

This module is the shared source-data helper for current JSON source records. Workbook parsing helpers live beside the only retained Excel flow in `scripts/catalogue_workbook_import.py`.

## Related References

- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)
- [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
