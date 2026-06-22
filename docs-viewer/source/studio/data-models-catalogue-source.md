---
doc_id: data-models-catalogue-source
title: Catalogue Source Model
added_date: 2026-05-19
last_updated: 2026-06-16
parent_id: studio
viewable: true
---
# Catalogue Source Model

## Scope Boundary

Current checked-in catalogue model families:

- canonical source records:
  - `site/assets/studio/data/catalogue/works.json`
  - `site/assets/studio/data/catalogue/series.json`
  - `site/assets/studio/data/catalogue/work_details.json`
  - `site/assets/studio/data/catalogue/moments.json`
- canonical prose sources:
  - `_docs_catalogue/works/<work_id>.md`
  - `_docs_catalogue/series/<series_id>.md`
  - `_docs_catalogue/moments/<moment_id>.md`
- fixed public route shells:
  - `works/index.md`
  - `series/index.md`
  - `work-details/index.md`
  - `moments/index.md`
- shared indexes:
  - `site/assets/data/series_index.json`
  - `site/assets/data/works_index.json`
  - `site/assets/data/recent_index.json`
  - `site/assets/data/moments_index.json`
- per-record payloads:
  - `site/assets/series/index/<series_id>.json`
  - `site/assets/works/index/<work_id>.json`
  - `site/assets/moments/index/<moment_id>.json`
- scope search:
  - `site/assets/data/search/catalogue/index.json`
- Studio planning/support data:
  - `studio/data/config/catalogue/catalogue-field-registry.json`

Primary writers:

- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json) for the live rebuild path that refreshes shared indexes and per-record catalogue payloads
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture) for `site/assets/data/search/catalogue/index.json`

Primary validator:

- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)

## Source Record Shape

### Source File Headers

Catalogue source JSON files use a deterministic top-level header plus one primary map.

Typical shape:

```json
{
  "header": {
    "schema": "catalogue_source_works_v1",
    "count": 0
  },
  "works": {}
}
```

Header fields:

- `schema`: stable schema identifier for the source file family
- `count`: number of records in the primary map, where the file owns record rows

Source headers avoid volatile timestamps so ordinary source edits produce focused Git diffs. Write timestamps belong in Studio activity artifacts and JSONL logs, not canonical catalogue source records.

### Work Source Records

Work records in `site/assets/studio/data/catalogue/works.json` own the primary work source-image path:

- `project_folder`
- optional `project_subfolder`
- `project_filename`

`project_subfolder` is persisted only when non-empty. Public runtime work images still resolve generated media by `work_id`; the source path fields are for Studio editing, local media readiness, and generator/source media lookup.

Other work source-model notes:

- `work_id` is duplicated inside each record for readability and import/export compatibility.
- `series_ids` is an ordered array; the first item is the primary series for work-level context.
- `width_px` and `height_px` are source metadata once measured, but they are generator/media-maintained rather than normal user-editable metadata.
- work prose is ID-derived from `_docs_catalogue/works/<work_id>.md`; source records no longer carry a prose filename override field.
- source-only fields such as `provenance` stay out of public projections unless an explicit runtime contract includes them.
- retired `notes` fields are no longer part of the work or series source schema; use `_docs_catalogue/works/` and `_docs_catalogue/series/` Markdown prose for catalogue narrative text.

### Work Detail Source Records

Work-detail source in `studio/data/canonical/catalogue/work_details.json` is split into section records and detail records.

`work_detail_sections` owns section metadata:

- `section_id`: stable generated public-section key, such as `00001-1`
- `work_id`: parent work id
- `details_subfolder`: optional source-image folder under the parent work's `project_folder`
- `section_title`: public section label
- `section_order`: optional section ordering value
- `detail_sort`: optional section-level detail ordering mode (`detail_id` or `title`)

`work_details` owns individual detail metadata:

- `detail_uid`
- `work_id`
- `detail_id`
- `section_id`
- `project_filename`
- `title`
- generated/media-maintained dimensions such as `width_px` and `height_px`

Detail records do not repeat `details_subfolder`, `section_title`, or section ordering metadata. Detail records no longer use legacy `project_subfolder`.
Detail records do not own `status` or `published_date`; parent work publication controls whether detail records appear in public output.

### Series Source Records

Series records in `site/assets/studio/data/catalogue/series.json` own series metadata and publication state.

Current source-model notes:

- `sort_fields` is the current JSON-source replacement for the retired workbook `SeriesSort` table.
- `primary_work_id` must reference a work whose `series_ids` includes the series before the series can be published; draft series may temporarily omit it.
- `series_type` remains explicit because Studio distinguishes primary series from other holdings or curated groups.
- series prose is ID-derived from `_docs_catalogue/series/<series_id>.md`; source records no longer carry a prose filename override field.

### Per-Work Runtime JSON

`site/assets/works/index/<work_id>.json` groups published detail records under `sections[]`.

Each section owns:

- `section_id`
- `section_title`
- optional `section_order`
- optional `detail_sort`
- `details[]`

Nested `details[]` records do not repeat section-level metadata. Detail records within a section are generated in section `detail_sort` order, defaulting to `detail_id`.

## Catalogue Field Registry

### `studio/data/config/catalogue/catalogue-field-registry.json`

Purpose:

- source of truth for field-aware catalogue build scoping rules
- reviewable registry for the Studio field-registry page
- bridge between the Task 1 dependency inventory and later executable build-planning implementation

Location:

- exposed through `studio/app/frontend/config/studio-config.json` at `paths.data.studio.catalogue_field_registry`

Current content families:

- `artifact_families` labels the artifact family vocabulary used by the planner
- `rules[]` groups fields by record family, operation, current behavior, and target behavior
- `rules[].current` describes broad behavior currently selected by the planner, lookup invalidation, or media workflow
- `rules[].target` describes the narrower behavior used by save-time write-server planning and by later preview/dry-run tasks
- `defaults` defines fallback behavior for unknown fields and mixed dependency classes
- `defaults.*.target.artifacts_by_record_family` owns fallback artifact sets for `work`, `work_detail`, `series`, and `moment`
- `retired_fields[]` records fields intentionally removed from active source rules

Planner output:

- `field_plan.explanations[]` is derived from the registry rather than stored in the registry file
- each explanation row includes `artifact`, `fields`, `rule_ids`, `fallback`, `fallback_reason`, `reason`, and the artifact-family `description` when one is available
- fallback plans derive broad artifact selection and explanation rows from registry defaults instead of Python-only fallback tables

Verification:

- `$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py` checks representative target rules, fallback defaults, duplicate field ownership, source/registry field coverage, and optional omit-empty source serialization against the live registry

Notes:

- the registry is JSON so Studio can display it directly
- current and target rules stay separate so review surfaces can compare historical broad behavior with active narrowed behavior
- the registry should be updated before adding a new active catalogue source field
- the registry does not own source field order, normalization, or omit-empty behavior; those live in `studio/services/catalogue/catalogue_source.py` and `studio/services/catalogue/moment_sources.py`

## Work-Owned Files And Links

Files and links are now work-owned metadata in `site/assets/studio/data/catalogue/works.json`.

The current source fields are:

- `downloads`
  optional array of `{ "filename": "...", "label": "..." }`
- `links`
  optional array of `{ "url": "...", "label": "..." }`

Empty arrays are omitted from source records.

Retired standalone file/link source files are no longer canonical source, and live source records no longer expose derived file/link compatibility maps. Workbook import helpers may still read legacy file/link sheets only to fold those rows into work-owned `downloads` and `links`.

## Fixed Route Shells

The public catalogue shells are:

- `/works/`, with selected state in `?work=<work_id>`
- `/series/`, with selected state in `?series=<series_id>`
- `/work-details/`, with selected state in `?detail=<detail_uid>`
- `/moments/`, with selected state in `?moment=<moment_id>`

The canonical work, series, and moment runtime payloads live under `site/assets/works/index/`, `site/assets/series/index/`, and `site/assets/moments/index/`.
Work-detail pages resolve through the parent work payload so sibling ordering, section grouping, and detail metadata stay consistent with the owning work.

## Canonical Moment Source

### `site/assets/studio/data/catalogue/moments.json`

Purpose:

- canonical source records for moment metadata

Current content families:

- `moment_id`
- `title`
- `status`
- `published_date`
- `date`
- optional `date_display`
- optional `source_image_file`
- optional `image_alt`

Notes:

- this file is the metadata source of truth for moments
- generated runtime payloads under `site/assets/moments/index/` are not canonical source
- source images remain a separate media concern

### `_docs_catalogue/moments/<moment_id>.md`

Purpose:

- canonical body-only moment prose source

Notes:

- files are ID-derived by `moment_id`
- files do not own canonical metadata front matter
- existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration
