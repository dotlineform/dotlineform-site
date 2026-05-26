---
doc_id: scripts-catalogue-source
title: Catalogue Source Utilities
added_date: 2026-04-18
last_updated: "2026-05-09 21:28"
parent_id: catalogue
sort_order: 10000
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
$HOME/miniconda3/bin/python3 studio/services/catalogue/validate_catalogue_source.py
```

Validation checks the source JSON for core relationship errors:

- malformed work, detail, and series IDs
- source fields that are not part of the canonical source schema
- source map keys that do not match normalized record IDs
- work `series_ids` references to unknown series
- series `primary_work_id` references to unknown works
- series `primary_work_id` values that are not members of that series
- work details that reference unknown works when actionable

Use the target media-section schema check for the current migrated source shape:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/validate_catalogue_source.py --target-media-section-schema
```

The target check requires detail `section_id` and `section_title`, accepts `details_subfolder`, validates `sort_order`, and rejects legacy detail `project_subfolder`.

## Media Section Migration

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/migrate_catalogue_media_sections.py
```

This previews the work-detail source migration from legacy `project_subfolder` to separated source-folder and public-section metadata:

- `details_subfolder`
- `section_id`
- `section_title`

The command is dry-run by default. It reports changed record counts, generated section ids, persisted source-folder metadata, and any blocking validation errors.

Apply the migration only when the preview is accepted:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/migrate_catalogue_media_sections.py --write
```

Write mode creates a backup under `var/studio/catalogue/backups/` before updating `assets/studio/data/catalogue/work_details.json`. After the migration has been applied, dry-run output should report `Legacy records: 0`, `Already migrated records: 2681`, and `Result: no changes`.

The migration does not move external source image files. Public runtime artifacts under `assets/works/index/` must be regenerated separately by the catalogue build/generator path.

## Project State Report

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py --write
```

The project-state report compares `$DOTLINEFORM_PROJECTS_BASE_DIR/projects` with primary work image references in `studio/data/canonical/catalogue/works.json`, then writes `var/studio/reports/project-state.md`.

Use this when you need to find source project folders or primary-image candidates that have not yet been represented in `works.json`. By default it scans only direct project folders; pass `--include-subfolders` when the review should include nested source folders too.

## Shared Module

Shared source loading, normalization, and validation logic lives in:

```text
studio/services/catalogue/catalogue_source.py
```

This module is the shared source-data helper for current JSON source records. Workbook parsing helpers live beside the only retained Excel flow in `studio/services/catalogue/catalogue_workbook_import.py`.

## Source Field Ownership

`studio/services/catalogue/catalogue_source.py` owns source field order, shared catalogue id-list and detail-uid normalization, source normalization, and omit-empty serialization for work, work-detail, and series records.

The field registry at `assets/studio/data/catalogue_field_registry.json` owns changed-field dependency planning for public build work and Studio lookup refresh selection. It does not drive source serialization.

When adding a source field:

1. add it to the relevant source field list in `studio/services/catalogue/catalogue_source.py`, or to the moment metadata field list in `studio/services/catalogue/moment_sources.py`
2. decide whether it is identity, derived, or editable metadata
3. add a matching registry rule when it is editable metadata
4. run `$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py`

Optional persisted fields currently omitted when empty:

- work `project_subfolder`
- detail `details_subfolder`
- detail `sort_order`

Required fields such as detail `section_id` and `section_title` must not be added to the omit-empty set. The field-registry verifier checks these source serialization boundaries.

## Related References

- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
