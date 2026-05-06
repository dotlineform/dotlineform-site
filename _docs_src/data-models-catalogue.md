---
doc_id: data-models-catalogue
title: Catalogue Scope
added_date: 2026-04-01
last_updated: "2026-05-06 20:49"
parent_id: catalogue
sort_order: 20
---
# Catalogue Scope

This document covers the current data model for the public catalogue: works, series, moments, detail pages, and catalogue search.

## Scope Boundary

Current checked-in catalogue model families:

- canonical source records:
  - `assets/studio/data/catalogue/works.json`
  - `assets/studio/data/catalogue/series.json`
  - `assets/studio/data/catalogue/work_details.json`
  - `assets/studio/data/catalogue/moments.json`
  - `assets/studio/data/catalogue/meta.json`
- canonical prose sources:
  - `_docs_src_catalogue/works/<work_id>.md`
  - `_docs_src_catalogue/series/<series_id>.md`
  - `_docs_src_catalogue/moments/<moment_id>.md`
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
  - `assets/studio/data/catalogue_field_registry.json`

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
- work prose is ID-derived from `_docs_src_catalogue/works/<work_id>.md`; source records no longer carry a prose filename override field.
- source-only fields such as `notes` and `provenance` stay out of public projections unless an explicit runtime contract includes them.

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
- series prose is ID-derived from `_docs_src_catalogue/series/<series_id>.md`; source records no longer carry a prose filename override field.

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

### `assets/studio/data/catalogue_field_registry.json`

Purpose:

- source of truth for field-aware catalogue build scoping rules
- reviewable registry for the future Studio field-registry page
- bridge between the Task 1 dependency inventory and later executable build-planning implementation

Location:

- exposed through `assets/studio/data/studio_config.json` at `paths.data.studio.catalogue_field_registry`

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

- `./scripts/verify_catalogue_field_registry.py` checks representative target rules, fallback defaults, duplicate field ownership, source/registry field coverage, and optional omit-empty source serialization against the live registry

Notes:

- the registry is JSON so Studio can display it directly
- current and target rules stay separate so review surfaces can compare historical broad behavior with active narrowed behavior
- the registry should be updated before adding a new active catalogue source field
- the registry does not own source field order, normalization, or omit-empty behavior; those live in `scripts/catalogue_source.py` and `scripts/moment_sources.py`

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
- canonical moment prose comes from `_docs_src_catalogue/moments/<moment_id>.md`
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

### `_docs_src_catalogue/moments/<moment_id>.md`

Purpose:

- canonical body-only moment prose source

Notes:

- files are ID-derived by `moment_id`
- files do not own canonical metadata front matter
- existing `<pre class="moment-text">...</pre>` wrappers remain accepted during migration

## Shared Catalogue Indexes

### `assets/data/series_index.json`

Purpose:

- canonical lookup map for series-level list and membership data

Current content families:

- series identity and publishing state
- list-card display metadata
- ordered work membership
- `primary_work_id`
- sort metadata used elsewhere in the catalogue and Studio

Current consumers:

- `/series/` in works mode
- `/series/<series_id>/`
- `/works/<work_id>/` when series context is needed for prev/next navigation
- Studio pages that need canonical series membership context

Why it exists separately:

- series list and membership data is needed in multiple places
- pages should not fetch every per-series record just to build a grid or navigation context

### `assets/data/works_index.json`

Purpose:

- lightweight lookup map for works used by grids, titles, and cross-scope references

Current content families:

- work identity
- title and year display
- series membership

Current consumers:

- `/series/<series_id>/` for work cards
- Studio pages that need fast work lookup without loading every work record

Why it stays lightweight:

- the work page’s full detail/prose payload is much larger
- series grids need fast bulk access to many works at once

### `assets/data/recent_index.json`

Purpose:

- snapshot ledger for the public `/recent/` page

Current content families:

- recent publication entry kind: `series` or `work`
- target id for route resolution
- snapshot title and caption text
- publication date
- thumbnail indirection via `thumb_id`
- lightweight write-order metadata for stable same-day ordering

Current consumers:

- `/recent/`

Why it is a separate derived artifact:

- the page needs publish-event history, not just current catalogue state
- snapshot titles and captions intentionally do not track later title edits or work-to-series moves
- deleted or unpublished targets can be pruned centrally by the generator when the catalogue rebuilds

### `assets/data/moments_index.json`

Purpose:

- lightweight lookup map for moments in the merged catalogue

Current content families:

- moment identity
- title and date display
- thumbnail indirection via `thumb_id`

Current consumers:

- `/series/` in moments mode

Why it is separate from the per-moment record:

- the merged catalogue only needs card metadata
- loading prose and image metadata for every moment card would be unnecessary

## Per-Record Catalogue Payloads

### `assets/series/index/<series_id>.json`

Purpose:

- page-local payload for one series page

Current content families:

- page-local series metadata
- rendered prose as `content_html`

Membership and thumbnail selection do not live in this payload. Public list and
grid contexts should read `assets/data/series_index.json` instead.

Current site mapping:

- `/series/<series_id>/`

Why it exists:

- the page needs prose and enough series metadata to update the local header
- shared membership and card context belong in the aggregate index so consumers do not fetch every per-series record

### `assets/works/index/<work_id>.json`

Purpose:

- page-local payload for one work and its detail structure

Current content families:

- canonical work metadata
- rendered prose as optional `content_html`
- `sections[]`
- ordered detail records grouped by section; nested detail records carry detail identity, title, and dimensions only, not route layout metadata

Current site mapping:

- `/works/<work_id>/`
- `/work_details/<detail_uid>/`

Why it is the most important catalogue record:

- the work page needs richer metadata than the index provides
- the detail page derives its canonical title, ordering, and back-link context from the parent work record
- avoiding a separate global detail index reduces duplication and keeps detail ordering local to the work that owns it
- work prose is optional, so the record still exists even when `_docs_src_catalogue/works/<work_id>.md` is missing

### `assets/moments/index/<moment_id>.json`

Purpose:

- page-local payload for one moment

Current content families:

- generated runtime moment metadata
- rendered prose as `content_html`
- image list and dimensions

Current site mapping:

- `/moments/<moment_id>/`

Why it exists:

- the moment page needs prose and image metadata, but the merged catalogue list does not

## Catalogue Search Model

### `assets/data/search/catalogue/index.json`

Purpose:

- search-owned flat index for `works`, `series`, and `moments`

Current content families:

- one `entries[]` array across all three catalogue kinds
- per-entry display metadata and route href
- normalized search terms and combined `search_text`
- selected structured fields such as series relationships, work medium type from per-work JSON, and Studio-derived tag data where available
- work-only search enrichment terms such as `medium_caption` folded into derived search fields from per-work JSON

Current site mapping:

- `/search/?scope=catalogue`

Why it is separate from the main indexes:

- search needs a flattened, text-oriented shape
- list/runtime pages need lookup-oriented shapes
- keeping those concerns separate avoids bloating the runtime indexes used by ordinary pages

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
