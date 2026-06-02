---
doc_id: data-models-catalogue-source
title: Catalogue Source Model
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: studio
viewable: true
---
# Catalogue Source Model

## Scope Boundary

Current checked-in catalogue model families:

- canonical source records:
  - `assets/studio/data/catalogue/works.json`
  - `assets/studio/data/catalogue/series.json`
  - `assets/studio/data/catalogue/work_details.json`
  - `assets/studio/data/catalogue/moments.json`
  - `assets/studio/data/catalogue/meta.json`
- canonical prose sources:
  - `_docs_catalogue/works/<work_id>.md`
  - `_docs_catalogue/series/<series_id>.md`
  - `_docs_catalogue/moments/<moment_id>.md`
- route stubs:
  - `_works/*.md`
  - `_series/*.md`
  - `_work_details/*.md`
  - `_moments/*.md`
- shared indexes:
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/data/recent_index.json`
  - `assets/data/moments_index.json`
- per-record payloads:
  - `assets/series/index/<series_id>.json`
  - `assets/works/index/<work_id>.json`
  - `assets/moments/index/<moment_id>.json`
- scope search:
  - `assets/data/search/catalogue/index.json`
- Studio planning/support data:
  - `studio/data/config/catalogue/catalogue-field-registry.json`

Primary writers:

- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json) for the live rebuild path that refreshes route stubs, shared indexes, and per-record catalogue payloads
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) for `assets/data/search/catalogue/index.json`

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

Work records in `assets/studio/data/catalogue/works.json` own the primary work source-image path:

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

Work-detail records in `assets/studio/data/catalogue/work_details.json` use the migrated media-section schema:

- `details_subfolder`: optional source-image folder under the parent work's `project_folder`
- `section_id`: stable generated public-section key, such as `00001-1`
- `section_title`: public section label
- `sort_order`: optional section ordering value
- `project_filename`: detail source-image filename

Detail records no longer use legacy `project_subfolder`. Empty `details_subfolder` values are omitted from source JSON; when absent, the detail source image resolves directly under the parent work's `project_folder`.

### Series Source Records

Series records in `assets/studio/data/catalogue/series.json` own series metadata and publication state.

Current source-model notes:

- `sort_fields` is the current JSON-source replacement for the retired workbook `SeriesSort` table.
- `primary_work_id` must reference a work whose `series_ids` includes the series before the series can be published; draft series may temporarily omit it.
- `series_type` remains explicit because Studio distinguishes primary series from other holdings or curated groups.
- series prose is ID-derived from `_docs_catalogue/series/<series_id>.md`; source records no longer carry a prose filename override field.

### Catalogue Source Metadata

`assets/studio/data/catalogue/meta.json` records source-level metadata that does not belong to a record family.

Current shape:

```json
{
  "header": {
    "schema": "catalogue_source_meta_v1"
  },
  "source": {
    "canonical": "json"
  },
  "id_policy": {
    "work_id_width": 5,
    "detail_id_width": 3
  }
}
```

Mutable counters are intentionally avoided. Work IDs, detail IDs, and suggested next IDs are derived from the current source records where practical, which is less fragile than storing counters in canonical metadata.

### Per-Work Runtime JSON

`assets/works/index/<work_id>.json` groups published detail records under `sections[]`.

Each section owns:

- `section_id`
- `section_title`
- optional `sort_order`
- `details[]`

Nested `details[]` records do not repeat section-level `section_id`, `section_title`, or `sort_order`. Detail records within a section remain sorted by `detail_id`.

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

Files and links are now work-owned metadata in `assets/studio/data/catalogue/works.json`.

The current source fields are:

- `downloads`
  optional array of `{ "filename": "...", "label": "..." }`
- `links`
  optional array of `{ "url": "...", "label": "..." }`

Empty arrays are omitted from source records.

Retired standalone file/link source files are no longer canonical source, and live source records no longer expose derived file/link compatibility maps. Workbook import helpers may still read legacy file/link sheets only to fold those rows into work-owned `downloads` and `links`.

## Why The Model Is Split This Way

The catalogue model is intentionally split between minimal route stubs and generated JSON.

Why:

- Jekyll still needs stable route pages for `/works/`, `/series/`, `/work_details/`, and `/moments/`
- list pages need lightweight indexes, not full per-item prose and detail payloads
- work and moment pages need richer page-local data such as `content_html`, dimensions, and detail sections
- detail pages are cheaper to resolve through the owning work record than through a separate global detail index

In practice this means the route stub gives the page an ID and fallback metadata, while the JSON record gives the page its canonical runtime content.

## Route Stubs

### `_works/*.md`

Purpose:

- provide the public work route
- carry route identity and a small fallback set of metadata

Design:

- intentionally minimal
- the canonical detail/prose payload lives in `assets/works/index/<work_id>.json`

### `_series/*.md`

Purpose:

- provide the public series route
- carry route identity and title fallback

Design:

- intentionally minimal
- series prose and canonical series metadata live in `assets/series/index/<series_id>.json`

### `_work_details/*.md`

Purpose:

- provide one public route per detail image
- identify the owning work and detail UID

Design:

- detail pages do not own a standalone detail JSON artifact
- the page resolves through the parent work record in `assets/works/index/<work_id>.json`

This keeps sibling ordering, section grouping, and detail metadata consistent with the owning work payload.

### `_moments/*.md`

Purpose:

- provide the public moment route
- carry route identity and title fallback

Design:

- canonical moment metadata comes from `assets/studio/data/catalogue/moments.json`
- canonical moment prose comes from `_docs_catalogue/moments/<moment_id>.md`
- runtime moment metadata and rendered prose are generated into `assets/moments/index/<moment_id>.json`
- the Markdown stub exists mainly for route generation and fallback text

## Canonical Moment Source

### `assets/studio/data/catalogue/moments.json`

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
- generated runtime payloads under `assets/moments/index/` are not canonical source
- source images remain a separate media concern

### `_docs_catalogue/moments/<moment_id>.md`

Purpose:

- canonical body-only moment prose source

Notes:

- files are ID-derived by `moment_id`
- files do not own canonical metadata front matter
- existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration
