---
doc_id: site-request-field-aware-build-scoping-inventory
title: Field-Aware Build Scoping Inventory
added_date: 2026-04-30
last_updated: 2026-04-30
parent_id: site-request-field-aware-build-scoping
sort_order: 10
---
# Field-Aware Build Scoping Inventory

Status:

- initial inventory populated

## Purpose

This document is the Task 1 evidence inventory for [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping).

It maps catalogue source fields to the generated or Studio-facing artifact families that currently consume them. It is intentionally descriptive, not prescriptive: Task 2 should turn this inventory into field-to-artifact planning rules.

## How To Read This Inventory

The field tables are organized by artifact family because the planner selects output families, not source record families.

Important distinction:

- "artifact field" means a serialized field path, front matter key, route identity, derived field, or media path input inside that artifact family
- "purpose" describes why that field matters for that artifact family
- "controls" means the field can include, exclude, sort, name, or otherwise change an artifact without necessarily being serialized into it
- "media-affecting" means the field can change local media source resolution, generated derivative filenames, or derivative freshness checks

## Artifact Families

| Family | Outputs | Purpose |
|---|---|---|
| `source-json` | `assets/studio/data/catalogue/works.json`; `assets/studio/data/catalogue/work_details.json`; `assets/studio/data/catalogue/series.json`; `assets/studio/data/catalogue/moments.json`; `assets/studio/data/catalogue/meta.json` | Canonical local Studio metadata source. Excluded from Jekyll build/watch. |
| `studio-lookup` | `assets/studio/data/catalogue_lookup/meta.json`; `assets/studio/data/catalogue_lookup/work_search.json`; `assets/studio/data/catalogue_lookup/series_search.json`; `assets/studio/data/catalogue_lookup/work_detail_search.json`; `assets/studio/data/catalogue_lookup/works/<work_id>.json`; `assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`; `assets/studio/data/catalogue_lookup/series/<series_id>.json`; equivalent `/catalogue/read` payloads | Fast editor read model for search, focused records, summaries, hashes, details, downloads, and links. |
| `work-page` | `_works/<work_id>.md` | Public Jekyll route shell for a work. Runtime data comes from focused JSON. |
| `work-json` | `assets/works/index/<work_id>.json` | Main public metadata/prose/detail payload for one work. |
| `work-details-page` | `_work_details/<detail_uid>.md` | Public Jekyll route shell for a work detail. Runtime context is loaded client-side. |
| `works-index-json` | `assets/data/works_index.json` | Lightweight public work index for index loading, series pages, and catalogue search. |
| `work-storage-index-json` | `assets/studio/data/work_storage_index.json` | Studio-only storage lookup derived from work storage metadata. |
| `series-page` | `_series/<series_id>.md` | Public Jekyll route shell for a series. Runtime data comes from aggregate indexes and focused JSON. |
| `series-json` | `assets/series/index/<series_id>.json` | Focused public metadata/prose payload for one series. |
| `series-index-json` | `assets/data/series_index.json` | Lightweight public series index for index loading, series membership, ordering, thumbnails, and catalogue search. |
| `recent-index-json` | `assets/data/recent_index.json` | Public recent-publications index generated from publish transitions and current membership context. |
| `moment-page` | `_moments/<moment_id>.md` | Public Jekyll route shell for a moment. Runtime data comes from focused JSON. |
| `moment-json` | `assets/moments/index/<moment_id>.json` | Main public metadata/prose/image payload for one moment. |
| `moments-index-json` | `assets/data/moments_index.json` | Lightweight public moment index for index loading and catalogue search. |
| `catalogue-search` | `assets/data/search/catalogue/index.json` | Combined public search index for works, series, moments, and tags. |
| `local-media` | `var/catalogue/media/works/make_srcset_images/<work_id>.<ext>`; `var/catalogue/media/works/srcset_images/thumb/<work_id>-thumb-96.webp`; `var/catalogue/media/works/srcset_images/thumb/<work_id>-thumb-192.webp`; `var/catalogue/media/works/srcset_images/primary/<work_id>-primary-800.webp`; `var/catalogue/media/works/srcset_images/primary/<work_id>-primary-1200.webp`; `var/catalogue/media/works/srcset_images/primary/<work_id>-primary-1600.webp`; `assets/works/img/<work_id>-thumb-96.webp`; `assets/works/img/<work_id>-thumb-192.webp`; the same staged source, thumb, primary, and public thumb patterns under `var/catalogue/media/work_details/` and `assets/work_details/img/` using `<detail_uid>`; the same staged source, thumb, primary, and public thumb patterns under `var/catalogue/media/moments/` and `assets/moments/img/` using `<moment_id>` | Local source-media staging, derivative generation, and public thumbnail copy outputs. |

## Builders

| Builder | Families |
|---|---|
| `scripts/catalogue_source.py` | `source-json` import/export helpers for works, work details, and series. |
| `scripts/moment_sources.py` | `source-json` moment metadata helpers. |
| `scripts/studio/catalogue_write_server.py` | `source-json` writes, service-backed `studio-lookup` reads, build preview/apply orchestration. |
| `scripts/catalogue_lookup.py` | `studio-lookup` payload construction. |
| `scripts/export_catalogue_lookup.py` | `studio-lookup` file export. |
| `scripts/generate_work_pages.py` | `work-page`, `work-json`, `work-details-page`, `works-index-json`, `work-storage-index-json`, `series-page`, `series-json`, `series-index-json`, `recent-index-json`, `moment-page`, `moment-json`, `moments-index-json`. |
| `scripts/catalogue_json_build.py` | Scoped build planning/apply orchestration and `local-media`. |
| `scripts/build_search.rb` | `catalogue-search`. |

## `source-json` Fields

| Artifact field | Purpose |
|---|---|
| `works.<work_id>.work_id` | Work identity and source map key consistency. |
| `works.<work_id>.status`, `published_date` | Draft/published workflow state and publish transition bookkeeping. |
| `works.<work_id>.series_ids` | Work-to-series membership source. |
| `works.<work_id>.project_folder`, `project_filename` | Source media path inputs for primary work media and detail media folder resolution. |
| `works.<work_id>.title`, `year`, `year_display` | Core work display and ordering metadata. |
| `works.<work_id>.medium_type`, `medium_caption`, `duration`, `artist` | Focused work metadata. |
| `works.<work_id>.storage_location` | Source field for runtime `storage` and Studio storage lookup. |
| `works.<work_id>.width_cm`, `height_cm`, `depth_cm`, `width_px`, `height_px` | Physical and image dimension metadata. |
| `works.<work_id>.downloads[]`, `links[]` | Work-owned file/link metadata. |
| `works.<work_id>.notes`, `provenance`, `series_title`, `work_prose_file` | Source/editor fields; current public consumers are limited or reserved. |
| `work_details.<detail_uid>.work_id`, `detail_id`, `detail_uid` | Detail identity and parent relation. |
| `work_details.<detail_uid>.status`, `published_date` | Detail workflow state and publish bookkeeping. |
| `work_details.<detail_uid>.project_subfolder`, `project_filename` | Detail section grouping and source media path inputs. |
| `work_details.<detail_uid>.title`, `width_px`, `height_px` | Detail display and image dimension metadata. |
| `series.<series_id>.series_id` | Series identity and source map key consistency. |
| `series.<series_id>.title`, `series_type`, `year`, `year_display`, `notes` | Core series metadata. |
| `series.<series_id>.status`, `published_date` | Series workflow state and publish transition bookkeeping. |
| `series.<series_id>.primary_work_id` | Source of public primary-work context in aggregate series data. |
| `series.<series_id>.sort_fields` | Work ordering rules for generated series membership. |
| `series.<series_id>.series_prose_file` | Source/editor field; current generator resolves prose by `series_id`. |
| `moments.<moment_id>.moment_id` | Moment identity and source map key consistency. |
| `moments.<moment_id>.title`, `date`, `date_display` | Moment display and search metadata. |
| `moments.<moment_id>.status`, `published_date` | Moment workflow state and publish bookkeeping. |
| `moments.<moment_id>.source_image_file`, `image_alt` | Moment image source and public alt metadata. |

## `studio-lookup` Fields

| Artifact field | Purpose |
|---|---|
| `meta.work_count`, `detail_count`, `series_count` | Fast Studio counts and source sanity context. |
| `work_search.items[].work_id`, `title`, `year_display`, `status`, `series_ids`, `record_hash` | Work editor search/open list and stale-write baseline. |
| `series_search.items[].series_id`, `title`, `status`, `primary_work_id`, `record_hash` | Series editor search/open list and stale-write baseline. |
| `work_detail_search.items[].detail_uid`, `work_id`, `detail_id`, `title`, `status` | Detail editor search/open list. |
| `works.<work_id>.work` | Full canonical source work record for editing. |
| `works.<work_id>.record_hash` | Stale-write protection for focused work edits. |
| `works.<work_id>.detail_sections[].project_subfolder`, `details[].detail_uid`, `detail_id`, `title`, `status` | Work editor detail summary grouped by section. |
| `works.<work_id>.downloads[]`, `links[]` | Work-owned file/link editing context. |
| `works.<work_id>.series_summary[].series_id`, `title` | Work editor series membership display. |
| `work_details.<detail_uid>.work_detail` | Full canonical source detail record for editing. |
| `work_details.<detail_uid>.record_hash` | Stale-write protection for focused detail edits. |
| `work_details.<detail_uid>.work_summary.work_id`, `title` | Detail editor parent work context. |
| `series.<series_id>.series` | Full canonical source series record for editing. |
| `series.<series_id>.record_hash` | Stale-write protection for focused series edits. |
| `series.<series_id>.member_works[].work_id`, `title`, `year_display`, `status`, `series_ids`, `record_hash` | Series editor member-work list and member baseline. |

## `work-page` Fields

| Artifact field | Purpose |
|---|---|
| `front_matter.work_id` | Route identity for `/works/<work_id>/`. |
| `front_matter.title` | Jekyll/page fallback title. |
| `front_matter.layout` | Selects the public work layout. |
| `front_matter.checksum` | Change detector; currently derived from the broader canonical work record. |

## `work-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `work_id`, `count` | Payload contract, cache/change detection, identity, and detail count. |
| `work.work_id`, `title`, `year`, `year_display` | Main public work identity and display metadata. |
| `work.series_ids` | Public membership context and search/tag relation input. |
| `work.storage` | Public/Studio runtime storage metadata derived from `storage_location`. |
| `work.medium_type`, `medium_caption`, `duration`, `artist` | Focused work metadata and search enrichment. |
| `work.height_cm`, `width_cm`, `depth_cm`, `width_px`, `height_px` | Physical and image dimensions. |
| `work.downloads[]`, `links[]` | Work-owned files and links. |
| `sections[].project_subfolder` | Detail section grouping. |
| `sections[].details[].detail_uid`, `work_id`, `detail_id`, `title`, `project_subfolder`, `width_px`, `height_px` | Published detail summary records shown from the parent work payload. |
| `content_html` | Rendered work prose from `_docs_src_catalogue/works/<work_id>.md`. |

## `work-details-page` Fields

| Artifact field | Purpose |
|---|---|
| `front_matter.work_id` | Parent work identity. |
| `front_matter.detail_id` | Detail-local identity. |
| `front_matter.detail_uid` | Detail route identity for `/work_details/<detail_uid>/`. |
| `front_matter.title` | Detail page fallback title. |

## `works-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `count` | Payload contract, cache/change detection, and count. |
| `works.<work_id>.work_id` | Work identity and map key consistency. |
| `works.<work_id>.title` | Public index/card/search display title. |
| `works.<work_id>.year`, `year_display` | Public display date and search metadata. |
| `works.<work_id>.series_ids` | Public series membership relation and search/tag relation input. |

## `work-storage-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `count` | Payload contract, cache/change detection, and count. |
| `works.<work_id>.storage` | Studio storage lookup derived from source `storage_location`. |

## `series-page` Fields

| Artifact field | Purpose |
|---|---|
| `front_matter.series_id` | Route identity for `/series/<series_id>/`. |
| `front_matter.title` | Jekyll/page fallback title. |
| `front_matter.layout` | Selects the public series layout. |
| `front_matter.checksum` | Change detector for the series page shell. |

## `series-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `series_id`, `count` | Payload contract, cache/change detection, identity, and published work count. |
| `series.series_id`, `status`, `published_date` | Focused public series identity and workflow/publication metadata. |
| `series.title`, `series_type`, `year`, `year_display`, `notes` | Focused public series metadata. |
| `series.sort_fields` | Public ordering context. |
| `series.project_folders[]` | Derived member-work project folders for Studio/public context. |
| `content_html` | Rendered series prose from `_docs_src_catalogue/series/<series_id>.md`. |

## `series-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `count` | Payload contract, cache/change detection, and count. |
| `series.<series_id>.series_id`, `status`, `published_date` | Series identity and publication state. |
| `series.<series_id>.title`, `series_type`, `year`, `year_display`, `notes` | Public aggregate series metadata and search source data. |
| `series.<series_id>.primary_work_id` | Series primary thumbnail/work context. |
| `series.<series_id>.sort_fields` | Ordering rule summary. |
| `series.<series_id>.project_folders[]` | Derived from member work `project_folder` values. |
| `series.<series_id>.works[]` | Ordered published member work ids derived from work `series_ids`, work `status`, and series `sort_fields`. |

## `recent-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `count` | Payload contract, cache/change detection, and count. |
| `entries[].kind`, `target_id` | Recent item identity. |
| `entries[].title` | Recent item display title from work or series metadata. |
| `entries[].caption` | Derived series/work publication caption. |
| `entries[].published_date`, `recorded_at_utc`, `session_order` | Recent ordering and publication session context. |
| `entries[].thumb_id` | Thumbnail target, usually work id or series primary work id. |

## `moment-page` Fields

| Artifact field | Purpose |
|---|---|
| `front_matter.moment_id` | Route identity for `/moments/<moment_id>/`. |
| `front_matter.title` | Jekyll/page fallback title. |
| `front_matter.layout` | Selects the public moment layout. |
| `front_matter.checksum` | Change detector for the moment page shell. |

## `moment-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `moment_id` | Payload contract, cache/change detection, and identity. |
| `moment.moment_id`, `title`, `date`, `date_display` | Public moment identity and display metadata. |
| `moment.images[].file`, `alt` | Public moment image metadata derived from source image availability and `image_alt`. |
| `moment.width_px`, `height_px` | Source image dimensions when available. |
| `content_html` | Rendered moment prose from `_docs_src_catalogue/moments/<moment_id>.md`. |

## `moments-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema`, `version`, `generated_at_utc`, `count` | Payload contract, cache/change detection, and count. |
| `moments.<moment_id>.moment_id` | Moment identity and map key consistency. |
| `moments.<moment_id>.title` | Public index/card/search display title. |
| `moments.<moment_id>.date`, `date_display` | Public display date and search metadata. |
| `moments.<moment_id>.thumb_id` | Thumbnail availability marker, emitted only when image metadata exists. |

## `catalogue-search` Fields

| Artifact field | Purpose |
|---|---|
| `entries[].kind`, `id`, `href` | Search result identity and destination. |
| `entries[].title` | Search display title from works, series, or moments indexes. |
| `entries[].year` | Work/series search date value. |
| `entries[].date` | Moment search date value. |
| `entries[].display_meta` | Work `year_display`, series `year_display`, or moment `date_display` fallback. |
| `entries[].series_ids` | Work-to-series relation from `works-index-json`. |
| `entries[].series_titles` | Work series title labels from `series-index-json`. |
| `entries[].medium_type`, `medium_caption` | Work search enrichment from focused `work-json`. |
| `entries[].series_type` | Series search enrichment from `series-index-json`. |
| `entries[].tag_ids`, `tag_labels` | Tag enrichment from Studio tag assignment and registry data. |
| `entries[].search_terms`, `search_text` | Derived broad-match tokens from id, title, display metadata, dates, series data, medium data, and series type. |

## `local-media` Fields

| Artifact field | Purpose |
|---|---|
| `work.source_path = works.<work_id>.project_folder + project_filename` | Resolves primary work source media. |
| `work.output_stem = work_id` | Names staged source, primary derivatives, and thumbnail derivatives. |
| `work_detail.source_path = works.<work_id>.project_folder + work_details.<detail_uid>.project_subfolder + project_filename` | Resolves detail source media. |
| `work_detail.output_stem = detail_uid` | Names staged source, primary derivatives, and thumbnail derivatives. |
| `moment.source_path = moments.<moment_id>.source_image_file` under configured moments image root | Resolves moment source media. |
| `moment.output_stem = moment_id` | Names staged source, primary derivatives, and thumbnail derivatives. |
| `source_mtime` compared with staged source and derivative mtimes | Decides whether media is current, pending, or blocked. |

## Local Media Field Summary

These are the current media-affecting field sets.

| Record family | Media-affecting source fields | Why |
|---|---|---|
| work | `work_id`, `project_folder`, `project_filename` | Resolve source path and output derivative names for primary work media. |
| work detail | `detail_uid`, `work_id`, `detail_id`, parent work `project_folder`, `project_subfolder`, `project_filename` | Resolve source path and output derivative names for detail media. |
| moment | `moment_id`, `source_image_file` | Resolve source path and output derivative names for moment media. |

Metadata-only changes should be able to skip local media generation when none of the fields above changed and the user did not explicitly request a media refresh.

Examples of metadata-only candidates:

- work `title`, `year`, `year_display`, `medium_type`, `medium_caption`, dimensions, downloads, links, notes, provenance, artist
- work detail `title`, `status`, `published_date`, `width_px`, `height_px`
- series `title`, `year`, `year_display`, `series_type`, `notes`, `primary_work_id`, `sort_fields`
- moment `title`, `date`, `date_display`, `image_alt`

## Structural Operations

Create, delete, and identity changes should keep conservative fallback until they have explicit rules.

Examples:

- work create/delete or `work_id` change
- detail create/delete or `detail_uid` change
- series create/delete or `series_id` change
- moment create/delete or `moment_id` change
- bulk saves that mix multiple record families
- unknown fields added to source records before the registry is updated

## Inventory Gaps

These items should be confirmed before Task 2 turns this into executable rules.

- Decide whether `work-page`, `series-page`, and `moment-page` should continue selecting page artifacts when only checksum-only metadata changed.
- Confirm whether `work_prose_file` and `series_prose_file` are obsolete retained fields or future path overrides.
- Confirm whether any source field outside the media-affecting summary can change media manifests, copy lists, or media readiness output.
- Confirm whether `notes` and `provenance` are intentionally source/editor-only for works.
- Confirm whether `published_date` should remain transition/bookkeeping-only for works and moments or become public metadata.
- Confirm whether targeted catalogue search can safely update existing records in the future; current targeted catalogue policy is additive-only.
