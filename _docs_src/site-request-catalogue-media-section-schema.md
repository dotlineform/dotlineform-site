---
doc_id: site-request-catalogue-media-section-schema
title: Catalogue Media And Detail Section Schema Request
added_date: 2026-04-30
last_updated: 2026-04-30
parent_id: change-requests
sort_order: 105
---
# Catalogue Media And Detail Section Schema Request

Status:

- deferred

## Summary

This change request tracks a future catalogue schema migration that separates source-media filesystem paths from public catalogue structure.

The current detail model uses `project_subfolder` for two unrelated concepts:

- resolving the source image path for a work detail
- naming and grouping public detail sections in the generated work JSON and on the site

That coupling was a reasonable early simplification, but it now constrains both source-folder organization and public section naming. A detail section cannot be renamed without moving files on disk, and work source images cannot be organized freely into subfolders because subfolders already imply detail sections.

This request is intentionally not an implementation task for the current field-aware build-scoping work. It records the schema problem and a preferred migration direction for later.

## Current Model

Works currently use:

- `project_folder`
- `project_filename`

Work details currently use:

- `work_id`
- `detail_id`
- `detail_uid`
- `project_subfolder`
- `project_filename`

For a work, `project_folder` is effectively the root source folder for that work. `project_filename` points to the primary work image inside that root.

For a work detail, `project_subfolder` and `project_filename` together resolve the source image under the parent work folder. The same `project_subfolder` value also becomes the generated detail section grouping in `assets/works/index/<work_id>.json`.

## Problem

The current model binds public catalogue structure to the physical source-folder layout.

This creates several non-obvious constraints:

- a work primary image cannot cleanly live in a nested folder without introducing ambiguity with detail folders
- a detail source image path cannot change independently from the public section grouping
- a public detail section label cannot change independently from a folder rename
- the schema name `project_subfolder` hides that the value is also user-facing catalogue structure
- field-aware build planning has to treat `project_subfolder` as both media-affecting and work JSON-affecting

The result is operationally tolerable for existing records, but it is conceptually fragile and blocks legitimate folder organization.

## Goals

- let source media paths describe file location only
- let detail section fields describe public catalogue grouping and labels only
- allow work source images and detail source images to use nested paths inside a work source folder
- make detail section names editable metadata rather than filesystem operations
- migrate existing source JSON automatically so the new schema works without manually editing every existing record
- remove the long-term need for generator and editor code to understand legacy path/grouping coupling

## Non-Goals

- do not change this schema as part of the current field-aware build-scoping cleanup
- do not move source image files on disk as part of the schema migration
- do not introduce standalone public detail JSON unless a separate request establishes that need
- do not make section records more complex than needed for current work-detail grouping

## Target Schema Direction

Works should keep `project_folder` as the root folder for the work's source media and prose-adjacent project files.

Works should replace `project_filename` with a path field that can point anywhere inside `project_folder`:

- `source_image_path`

Work details should replace the path/grouping overload with separate fields:

- `source_image_path`
- `section_id`
- `section_title`

`source_image_path` should be a relative path under the parent work's `project_folder`.

`section_id` should be a stable logical grouping key for generated work JSON.

`section_title` should be the display label for the public section. It may initially equal `section_id`, but it should not be derived from the filesystem after migration.

## Automatic Migration

The legacy fields should map onto the new schema in a one-time source migration, not remain as permanent fallback behavior.

Work migration:

| Existing field | New field |
|---|---|
| `project_folder` | keep as `project_folder` |
| `project_filename` | `source_image_path` |

Work detail migration:

| Existing field | New field |
|---|---|
| `project_subfolder` + `project_filename` | `source_image_path` |
| `project_subfolder` | `section_id` |
| `project_subfolder` | `section_title` |

The migration should write normalized source JSON so existing records immediately use the new schema without hand edits.

Compatibility logic should live at the migration or source-normalization boundary only. Generator, lookup, editor, validation, and media code should move toward consuming the new fields directly.

## Build-Scoping Implications

After migration, field-aware planning becomes clearer:

| Field | Affected family |
|---|---|
| work `source_image_path` | `local-media`; Studio media readiness |
| detail `source_image_path` | `local-media`; Studio media readiness |
| detail `section_id` | `work-json`; possibly catalogue search if section context becomes indexed |
| detail `section_title` | `work-json`; public display; possibly catalogue search if section context becomes indexed |

Changing source image paths should not imply public section regrouping.

Changing section metadata should not imply local media regeneration unless the user explicitly requests media refresh.

## Implementation Notes

A later implementation should update:

- canonical source JSON schemas and validation
- import/export helpers
- Studio work and work-detail editors
- Studio lookup payloads and media readiness summaries
- `scripts/catalogue_json_build.py` media source resolution
- `scripts/generate_work_pages.py` detail section generation
- docs for catalogue data models, scoped builds, and field-aware inventory

The implementation should include a dry-run migration command or preview mode before writing source JSON.

## Benefits

- clearer schema boundaries between file storage and public catalogue structure
- more flexible source-media organization inside work folders
- editable public detail section names without filesystem moves
- simpler field-aware build-scoping rules
- less historical knowledge required to work safely with detail records

## Risks

- existing records are numerous, so migration needs careful validation and deterministic output
- all source consumers must move together or stale legacy assumptions will produce path or grouping errors
- section ordering and duplicate section labels need explicit policy
- any workbook import/export compatibility path must avoid reintroducing the old overloaded fields

## Open Questions

- Should `section_title` be optional when it matches `section_id`, or always written for clarity?
- Should section ordering be derived from first detail order, an explicit `section_sort`, or a future section registry?
- Should work primary source images use `source_image_path` only, or should details use a more explicit name such as `detail_source_image_path`?
- Should migration retain retired legacy fields temporarily for audit, or remove them immediately once generated outputs validate?
