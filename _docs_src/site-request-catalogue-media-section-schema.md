---
doc_id: site-request-catalogue-media-section-schema
title: Catalogue Media And Detail Section Schema Request
added_date: 2026-04-30
last_updated: 2026-05-02
parent_id: change-requests
sort_order: 105
---
# Catalogue Media And Detail Section Schema Request

Status:

- proposed

## Summary

This change request describes a catalogue schema migration that separates source-media filesystem paths from public catalogue structure.

The current work-detail model uses `project_subfolder` for two unrelated concepts:

- resolving the source image path for a work detail
- naming and grouping public detail sections in the generated work JSON and on the site

The second role already behaves like section metadata. Work and work-detail JSON effectively carry the public section label today as `project_subfolder`, commonly with values such as `details`.

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

This means the existing JSON already contains the future section-title concept, but under a misleading filesystem-oriented field name.

## Problem

The current model binds public catalogue structure to the physical source-folder layout.

This creates several non-obvious constraints:

- a work primary image cannot cleanly live in a nested folder without introducing ambiguity with detail folders
- a detail source image path cannot change independently from the public section grouping
- a public detail section label cannot change independently from a folder rename
- the schema name `project_subfolder` hides that the value is also user-facing catalogue structure
- field-aware build planning has to treat `project_subfolder` as both media-affecting and work JSON-affecting

The result is operationally tolerable for existing records, but it is conceptually fragile and blocks legitimate folder organization.

Important distinction: source media path fields are still persisted source metadata for Studio. They are not required for public runtime display after media artifacts are generated, because public work image srcsets resolve by `work_id` and public thumbnails/index images resolve from generated media paths. Studio still needs the source folder metadata so editors can view and update the external source image path used by media generation.

## Goals

- let source media paths describe file location only
- let detail section fields describe public catalogue grouping and labels only
- allow work source images and detail source images to use nested paths inside a work source folder
- make detail section names editable metadata rather than filesystem operations
- migrate existing source JSON automatically so the new schema works without manually editing every existing record
- remove the long-term need for generator and editor code to understand legacy path/grouping coupling

## Non-Goals

- do not move source image files on disk as part of the schema migration
- do not introduce standalone public detail JSON unless a separate request establishes that need
- do not make section records more complex than needed for current work-detail grouping

## Target Schema Direction

### Project folder

- Works should keep `project_folder` as the root folder for the work's source media and prose-adjacent project files.
- Works should include an optional `project_subfolder` field that can point to a subfolder inside `project_folder`. `project_subfolder` should allow a nested folder e.g. `[subfolder_1]/[subfolder_2]`

### Work Details folder

Work details should replace the path/grouping overload with separate fields:

- `details_subfolder`
- `section_id`
- `section_title`
- `sort_order`

`details_subfolder` should be an optional relative path under the parent work's `project_folder`. It should allow nested folders, e.g. `[subfolder_1]/[subfolder_2]`

`details_subfolder` can be null, empty, or absent. If it is empty or absent, the detail source image path resolves to the parent work's `project_folder`. Non-empty `details_subfolder` values are persisted in source JSON so Studio can reconstruct the external source image path. Empty `details_subfolder` values should not be written to source JSON.

`section_id` should be a stable logical grouping key for generated work JSON. The key is automatically generated on creation by combining parent `work_id` with an incremented 1-digit number using a hyphen. e.g. `[work_id]-1`, `[work_id]-2`...
`section_id` is read-only on the UI and is not user-editable.

`sort_order` is an optional numeric field and is not written to JSON if value is null. If completed it determines the order of the sections displayed on the public work page. Sections are ordered by `sort_order` and then `section_id`. So if `sort_order` is missing, the sections are sorted by `section_id` which is effectively the order in which they were created (this matches current behaviour). Detail records within a section remain sorted by `detail_id`.

`section_title` should be the display label for the public section. This is a required field and will be entered by user in the UI. `section_title` does not need to be unique within a work because `section_id` is the unique section key.

For existing records, the section migration is mostly a semantic rename and propagation:

- existing generated `project_subfolder` section values become `section_title`
- records can keep the same visible section labels after migration
- Studio can then treat the value as editable `section_title` metadata

### Example

`assets/studio/data/catalogue_lookup/works/00001.json`

**current** work fields

```json
{
  "project_folder": "a poem divided into 4 parts",
  "project_filename": "a poem divided into 4 parts - 1.jpg"
}
```

**target** work fields:

```json
{
  "project_folder": "a poem divided into 4 parts",
  "project_subfolder": "sub-folder",
  "project_filename": "a poem divided into 4 parts - 1.jpg"
}
```

**current** "detail_sections" fields:

```json
{
  "project_subfolder": "details"
}
```

**target** "detail_sections" fields:

```json
{
  "section_id": "00001-1",
  "section_title": "details",
  "details_subfolder": "sub-folder"
}
```

`project_subfolder` and `details_subfolder` are persisted when non-empty so Studio can show and edit the external source image path. They may be empty, and then they are not included in the JSON.

The separate source folder field becomes essential when source image organization diverges from the old rule that detail images live under a folder named by the public section.

## Automatic Migration

The legacy fields should map onto the new schema in a one-time source migration, not remain as permanent fallback behavior.

Work migration: none required, because new field `project_subfolder` is optional and default = null.

Work detail migration:

| Existing field | New field |
|---|---|
| `project_subfolder` | `details_subfolder` |
| `project_subfolder` | `section_title` |

- `project_subfolder` is effectively a field rename to `details_subfolder`
- and a data copy from `project_subfolder` to the new field `section_title`

The migration should write normalized source JSON so existing records immediately use the new schema without hand edits.

No compatibility logic is needed because the old fields map exactly to the new fields and current data is already validated.

The migration keeps all existing source files in their current locations. Later edits can then move source images into arbitrary nested paths by editing the `details_subfolder` without changing the public section title `section_title`.

## Build-Scoping Implications

After migration, field-aware planning becomes clearer:

| Field | Affected family |
|---|---|
| work `project_subfolder` | persisted source metadata for Studio source-image editing; local-media readiness input; not public runtime display after media generation |
| detail `details_subfolder` | persisted source metadata for Studio source-image editing; local-media readiness input; not public runtime display after media generation |
| detail `section_id` | `work-json`; not on public display or search. internal ID only. |
| detail `section_title` | `work-json`; public display; possibly catalogue search if section context becomes indexed |
| detail `sort_order` | `work-json`; not on public display but needed to sort sections on the public work page. not included in search. |

Changing source folder metadata or section metadata should **not** imply:
- public section regrouping.
- local media regeneration unless the user explicitly requests media refresh.

## Implementation Notes

The implementation should update:

- canonical source JSON schemas and validation
- bulk import work/work details (the bulk import file `data/works_bulk_import.xlsx` will be updated to align with the new fields)
- import/export helpers
- Studio work and work-detail editors
- Studio lookup payloads and media readiness summaries
- `scripts/catalogue_json_build.py` media source resolution
- `scripts/generate_work_pages.py` detail section generation
- docs for catalogue data models, scoped builds, and field-aware inventory

The implementation should include a dry-run migration command or preview mode before writing source JSON.

## Locked Decisions

These source-schema decisions are locked for the first implementation:

- Work source media continues to use `project_folder`, optional `project_subfolder`, and the existing source-image filename flow. The implementation does not add a new combined source image path field. Non-empty `project_subfolder` values are persisted in source JSON so Studio can reconstruct the external source image path used by media generation; public runtime image display still resolves generated srcset files by `work_id`.
- Detail source media follows the same principle as work media. It uses `details_subfolder` plus `project_filename` for source path resolution and does not add a new combined source image path field. Non-empty `details_subfolder` values are persisted in source JSON for Studio editing.
- `details_subfolder` is optional. It can be null, empty, or absent. Empty values are not written to source JSON. When `details_subfolder` is missing, the resolved source path for a detail image is the parent work's `project_folder`.
- `section_id` is generated automatically by combining the parent `work_id` with an incremented one-digit suffix using a hyphen, such as `[work_id]-1`, `[work_id]-2`, and so on. It is read-only in Studio and is not user-editable.
- `section_title` does not need to be unique within a work. No uniqueness validation is needed because `section_id` is the unique key.
- `sort_order` applies to sections only. It does not order detail records within a section. Detail records continue to sort by `detail_id`.

## Task List

### Task 1. Lock The Source Schema Contract

Status:

- locked

The source schema contract is now locked for the first implementation.

Locked decisions:

- keep the current work source-image filename flow used for srcset generation
- do not add a new combined source image path field for works or details
- persist non-empty `project_subfolder` and `details_subfolder` values so Studio can reconstruct external source image paths
- make `details_subfolder` optional and omit empty values from source JSON
- generate `section_id` from parent `work_id` plus a hyphen and incremented suffix
- allow duplicate `section_title` values within a work
- apply `sort_order` to sections only, while detail records continue to sort by `detail_id`

Acceptance checks:

- source-field names are consistent across prose, schema docs, validators, and planned UI labels
- the migration can be described as deterministic before any source JSON is written
- unresolved compatibility decisions are documented as follow-up risks rather than hidden implementation assumptions

### Task 2. Add A Dry-Run Migration

Status:

- implemented

Add a migration path that previews and then writes the canonical source JSON changes.

Expected behavior:

- work records keep existing `project_folder` and `project_filename`
- non-empty work `project_subfolder` values are persisted
- absent or empty work `project_subfolder` values are omitted from source JSON
- detail records copy legacy `project_subfolder` into `details_subfolder`
- detail records copy legacy `project_subfolder` into `section_title`
- detail records receive deterministic `section_id` values grouped by parent `work_id`
- legacy `project_subfolder` is removed from detail records after the write migration
- output ordering and formatting stay stable

Acceptance checks:

- dry-run reports record counts, changed fields, generated section ids, and any duplicate section-title cases
- dry-run reports whether non-empty `project_subfolder` and `details_subfolder` source metadata will be persisted
- write mode creates a backup before modifying canonical catalogue JSON
- repeated dry-runs after migration report no additional writes
- migration rejects ambiguous or invalid legacy records before write mode

Implemented:

- added `./scripts/migrate_catalogue_media_sections.py`
- dry-run is the default; `--write` is required to update source JSON
- write mode backs up `assets/studio/data/catalogue/work_details.json` under `var/studio/catalogue/backups/`
- section ids are assigned deterministically per parent work and first-seen legacy section title, using ids such as `00001-1`
- focused checks live in `tests/python/test_catalogue_media_section_migration.py`
- the field registry and canonical source field order were pre-aligned so later source writes can preserve `project_subfolder`, `details_subfolder`, `section_id`, `section_title`, and `sort_order`
- follow-on source/registry drift verification is tracked separately in [Catalogue Source And Registry Drift Verification Request](/docs/?scope=studio&doc=site-request-catalogue-source-registry-drift-verification)

Initial dry-run result:

- 2,681 legacy detail records would change
- 163 section ids would be generated
- no empty legacy detail `project_subfolder` values were found
- no duplicate section-title conflicts were found; duplicate section titles remain allowed because `section_id` is the unique key

### Task 3. Update Source Schemas And Validators

Status:

- implemented

Update every source validation and payload-shaping path to understand the new fields.

Expected changes:

- canonical catalogue schema rules accept work `project_subfolder` where applicable
- detail schema rules require `section_title` and `section_id`
- detail schema rules accept `details_subfolder` as the source-folder field
- source writers persist non-empty `project_subfolder` and `details_subfolder`
- source writers omit empty `project_subfolder` and `details_subfolder`
- create/save endpoints reject legacy detail `project_subfolder`
- import/export helpers use the new field names
- field-aware dependency rules classify source folder metadata fields separately from public section metadata

Acceptance checks:

- validation errors name the new user-facing fields
- no new compatibility fallback silently preserves legacy detail `project_subfolder`

Implementation notes:

- `scripts/catalogue_source.py` now defines the target work-detail source field order, validates required `section_id` and `section_title`, accepts optional `details_subfolder`, and rejects legacy detail `project_subfolder` when target media-section validation is requested.
- Default whole-source validation remains legacy-readable until the dry-run migration is written, while `./scripts/validate_catalogue_source.py --target-media-section-schema` verifies the migrated target shape.
- Studio write-server work-detail create/save and bulk-save validation reject incoming legacy `project_subfolder`; create generates `section_id` server-side as `[work_id]-1`, `[work_id]-2`, and so on.
- Bulk-import work-detail rows now use `details_subfolder` and `section_title`; non-empty legacy `project_subfolder` cells are blocked instead of silently mapped.
- Studio source-image path fields round-trip through source JSON when non-empty
- source edits can distinguish media-path changes from public section changes
- syntax checks pass for changed Python scripts

### Task 4. Update Build And Lookup Consumers

Status:

- not started

Move generated-output and readiness consumers to the separated media-path and section fields.

Expected changes:

- `scripts/catalogue_json_build.py` resolves primary work media with the locked work source-path contract
- detail source media resolution uses `details_subfolder` plus `project_filename`
- `scripts/generate_work_pages.py` groups detail output by `section_id` and displays `section_title`
- generated work JSON orders sections by `sort_order` and then `section_id`
- lookup payloads and media readiness summaries report the new source fields
- generated lookup payloads retain non-empty `project_subfolder` and `details_subfolder` for Studio editing
- local media generation only follows source media fields, not public section metadata

Acceptance checks:

- generated public work JSON keeps existing visible section labels after migration
- changing only `section_title` does not imply media regeneration
- changing only `details_subfolder` does not rename the public section
- public runtime image display still resolves generated media by work/detail ids rather than by the persisted source subfolder fields
- existing generated output changes are explainable and limited to the schema migration

### Task 5. Update Studio Editing And Import Surfaces

Status:

- not started

Update Studio UI and workbook-led import flows to expose the new contract without reintroducing the old overloaded field.

Expected changes:

- work editor exposes optional work `project_subfolder` only if that remains the locked schema
- work-detail editor exposes `details_subfolder`, read-only `section_id`, `section_title`, and `sort_order`
- new-detail create flow generates `section_id` and requires `section_title`
- UI copy and labels live in `assets/studio/data/studio_config.json`
- bulk import work-detail columns align with the new fields
- import previews call out generated section ids and section-title grouping

Acceptance checks:

- Studio cannot save legacy detail `project_subfolder`
- new detail creation produces a stable `section_id`
- section title edits are clear as public catalogue metadata, not folder changes
- existing parent-work detail navigation still works after the schema migration

### Task 6. Update Documentation And Field Inventory

Status:

- not started

Update stable reference docs once the implementation contract is final.

Expected docs:

- data-model docs for work and work-detail source records
- catalogue build and generator docs for media path resolution
- Studio work and work-detail editor docs
- field-aware build-scoping docs and registry notes
- relevant site or Studio change-log entries if public generated payload behavior changes

Acceptance checks:

- published docs link with `/docs/?scope=studio&doc=<doc_id>` where cross-references are needed
- Studio docs payloads are rebuilt with `./scripts/build_docs.rb --scope studio --write`
- Studio search is rebuilt if changed docs need search output to stay current
- docs avoid machine-specific paths or local credentials

### Task 7. Verify Migration And Runtime Behavior

Status:

- not started

Run a focused verification pass that proves the migration and public output are stable.

Required checks:

- dry-run migration before write mode
- post-migration dry-run showing no remaining changes
- catalogue build preview or dry-run for representative changed works and details
- targeted generated-output comparison for at least one work with multiple detail sections
- source validation for migrated records
- Studio smoke check for work-detail create/edit if UI surfaces changed
- Jekyll build to a separate destination when a serve process is already running

Acceptance checks:

- no unresolved legacy `project_subfolder` detail assumptions remain in active code
- public work pages preserve existing section labels unless explicitly changed
- media readiness uses the new source-folder fields
- changed files pass sanitization checks before close-out

## Benefits

- clearer schema boundaries between file storage and public catalogue structure
- more flexible source-media organization inside work folders
- editable public detail section names without filesystem moves
- simpler field-aware build-scoping rules
- less historical knowledge required to work safely with detail records

## Risks

- existing records are numerous, so migration needs validation and deterministic output
- all source consumers must move together or stale legacy assumptions will produce path or grouping errors
- section ordering and duplicate section labels need explicit policy
- any workbook import/export compatibility path must avoid reintroducing the old overloaded fields
