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
| `works.<work_id>.status` | Draft/published workflow state. |
| `works.<work_id>.published_date` | Publish transition bookkeeping. |
| `works.<work_id>.series_ids` | Work-to-series membership source. |
| `works.<work_id>.project_folder` | Source media path input for primary work media and parent folder input for detail media. |
| `works.<work_id>.project_filename` | Source media path input for primary work media. |
| `works.<work_id>.title` | Core work display and ordering metadata. |
| `works.<work_id>.year` | Core work date and ordering metadata. |
| `works.<work_id>.year_display` | Core work display date metadata. |
| `works.<work_id>.medium_type` | Focused work metadata. |
| `works.<work_id>.medium_caption` | Focused work metadata. |
| `works.<work_id>.duration` | Focused work metadata. |
| `works.<work_id>.artist` | Focused work metadata. |
| `works.<work_id>.storage_location` | Source field for runtime `storage` and Studio storage lookup. |
| `works.<work_id>.width_cm` | Physical dimension metadata. |
| `works.<work_id>.height_cm` | Physical dimension metadata. |
| `works.<work_id>.depth_cm` | Physical dimension metadata. |
| `works.<work_id>.width_px` | Image dimension metadata. |
| `works.<work_id>.height_px` | Image dimension metadata. |
| `works.<work_id>.downloads[]` | Work-owned file metadata. |
| `works.<work_id>.links[]` | Work-owned link metadata. |
| `works.<work_id>.notes` | Source/editor field; current public consumers are limited or reserved. |
| `works.<work_id>.provenance` | Source/editor field; current public consumers are limited or reserved. |
| `works.<work_id>.series_title` | Source/editor field; generated runtime derives current series title from series records. |
| `works.<work_id>.work_prose_file` | Source/editor field; current generator resolves prose by `work_id`. |
| `work_details.<detail_uid>.work_id` | Detail parent relation. |
| `work_details.<detail_uid>.detail_id` | Detail-local identity. |
| `work_details.<detail_uid>.detail_uid` | Detail identity and source map key consistency. |
| `work_details.<detail_uid>.status` | Detail workflow state. |
| `work_details.<detail_uid>.published_date` | Detail publish bookkeeping. |
| `work_details.<detail_uid>.project_subfolder` | Detail section grouping. |
| `work_details.<detail_uid>.project_filename` | Detail source media path input; `project_subfolder` plus `project_filename` resolves the source media path under the parent work folder. |
| `work_details.<detail_uid>.title` | Detail display metadata. |
| `work_details.<detail_uid>.width_px` | Detail image dimension metadata. |
| `work_details.<detail_uid>.height_px` | Detail image dimension metadata. |
| `series.<series_id>.series_id` | Series identity and source map key consistency. |
| `series.<series_id>.title` | Core series display metadata. |
| `series.<series_id>.series_type` | Core series metadata. |
| `series.<series_id>.year` | Core series date metadata. |
| `series.<series_id>.year_display` | Core series display date metadata. |
| `series.<series_id>.notes` | Core series metadata. |
| `series.<series_id>.status` | Series workflow state. |
| `series.<series_id>.published_date` | Series publish transition bookkeeping. |
| `series.<series_id>.primary_work_id` | Source of public primary-work context in aggregate series data. |
| `series.<series_id>.sort_fields` | Work ordering rules for generated series membership. |
| `series.<series_id>.series_prose_file` | Source/editor field; current generator resolves prose by `series_id`. |
| `moments.<moment_id>.moment_id` | Moment identity and source map key consistency. |
| `moments.<moment_id>.title` | Moment display and search metadata. |
| `moments.<moment_id>.date` | Moment date and search metadata. |
| `moments.<moment_id>.date_display` | Moment display date and search metadata. |
| `moments.<moment_id>.status` | Moment workflow state. |
| `moments.<moment_id>.published_date` | Moment publish bookkeeping. |
| `moments.<moment_id>.source_image_file` | Moment image source metadata. |
| `moments.<moment_id>.image_alt` | Moment public image alt metadata. |

## `studio-lookup` Fields

| Artifact field | Purpose |
|---|---|
| `meta.work_count` | Fast Studio work count and source sanity context. |
| `meta.detail_count` | Fast Studio detail count and source sanity context. |
| `meta.series_count` | Fast Studio series count and source sanity context. |
| `work_search.items[].work_id` | Work editor search/open identity. |
| `work_search.items[].title` | Work editor search/open display text. |
| `work_search.items[].year_display` | Work editor search/open display metadata. |
| `work_search.items[].status` | Work editor search/open workflow state. |
| `work_search.items[].series_ids` | Work editor search/open membership context. |
| `series_search.items[].series_id` | Series editor search/open identity. |
| `series_search.items[].title` | Series editor search/open display text. |
| `series_search.items[].status` | Series editor search/open workflow state. |
| `series_search.items[].primary_work_id` | Series editor search/open primary work context. |
| `work_detail_search.items[].detail_uid` | Detail editor search/open identity. |
| `work_detail_search.items[].work_id` | Detail editor search/open parent work identity. |
| `work_detail_search.items[].detail_id` | Detail editor search/open local detail identity. |
| `work_detail_search.items[].title` | Detail editor search/open display text. |
| `work_detail_search.items[].status` | Detail editor search/open workflow state. |
| `works.<work_id>.work` | Full canonical source work record for editing. |
| `works.<work_id>.detail_sections[].project_subfolder` | Work editor detail summary grouping. |
| `works.<work_id>.detail_sections[].details[].detail_uid` | Work editor detail summary identity. |
| `works.<work_id>.detail_sections[].details[].detail_id` | Work editor detail summary local detail identity. |
| `works.<work_id>.detail_sections[].details[].title` | Work editor detail summary display text. |
| `works.<work_id>.detail_sections[].details[].status` | Work editor detail summary workflow state. |
| `works.<work_id>.downloads[]` | Work-owned file editing context. |
| `works.<work_id>.links[]` | Work-owned link editing context. |
| `works.<work_id>.series_summary[].series_id` | Work editor series membership identity. |
| `works.<work_id>.series_summary[].title` | Work editor series membership display text. |
| `work_details.<detail_uid>.work_detail` | Full canonical source detail record for editing. |
| `work_details.<detail_uid>.work_summary.work_id` | Detail editor parent work identity. |
| `work_details.<detail_uid>.work_summary.title` | Detail editor parent work display text. |
| `series.<series_id>.series` | Full canonical source series record for editing. |
| `series.<series_id>.member_works[].work_id` | Series editor member-work identity. |
| `series.<series_id>.member_works[].title` | Series editor member-work display text. |
| `series.<series_id>.member_works[].year_display` | Series editor member-work display metadata. |
| `series.<series_id>.member_works[].status` | Series editor member-work workflow state. |
| `series.<series_id>.member_works[].series_ids` | Series editor member-work membership context. |

## `work-page` Fields

| Artifact field | Purpose |
|---|---|
| `filename_stem` | Route identity for `/works/<work_id>/`; layout comes from `_config.yml` collection defaults. |

## `work-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.work_id` | Payload identity. |
| `header.count` | Published detail count. |
| `work.work_id` | Main public work identity. |
| `work.title` | Main public work display metadata. |
| `work.year` | Main public work date metadata. |
| `work.year_display` | Main public work display date metadata. |
| `work.series_ids` | Public membership context and search/tag relation input. |
| `work.storage` | Public/Studio runtime storage metadata derived from `storage_location`. |
| `work.medium_type` | Focused work metadata and search enrichment. |
| `work.medium_caption` | Focused work metadata and search enrichment. |
| `work.duration` | Focused work metadata. |
| `work.artist` | Focused work metadata. |
| `work.height_cm` | Physical dimension. |
| `work.width_cm` | Physical dimension. |
| `work.depth_cm` | Physical dimension. |
| `work.width_px` | Image dimension. |
| `work.height_px` | Image dimension. |
| `work.downloads[]` | Work-owned files. |
| `work.links[]` | Work-owned links. |
| `sections[].project_subfolder` | Detail section grouping. |
| `sections[].details[].detail_uid` | Published detail summary identity. |
| `sections[].details[].work_id` | Published detail summary parent work identity. |
| `sections[].details[].detail_id` | Published detail summary local detail identity. |
| `sections[].details[].title` | Published detail summary display text. |
| `sections[].details[].project_subfolder` | Published detail summary section context. |
| `sections[].details[].width_px` | Published detail summary image dimension. |
| `sections[].details[].height_px` | Published detail summary image dimension. |
| `content_html` | Rendered work prose from `_docs_src_catalogue/works/<work_id>.md`. |

## `work-details-page` Fields

| Artifact field | Purpose |
|---|---|
| `filename_stem` | Detail route identity for `/work_details/<detail_uid>/`; parent work id is derived from the detail uid prefix and layout comes from `_config.yml` collection defaults. |

## `works-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.count` | Work count. |
| `works.<work_id>.work_id` | Work identity and map key consistency. |
| `works.<work_id>.title` | Public index/card/search display title. |
| `works.<work_id>.year` | Public date and search metadata. |
| `works.<work_id>.year_display` | Public display date and search metadata. |
| `works.<work_id>.series_ids` | Public series membership relation and search/tag relation input. |

## `work-storage-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.count` | Storage record count. |
| `works.<work_id>.storage` | Studio storage lookup derived from source `storage_location`. |

## `series-page` Fields

| Artifact field | Purpose |
|---|---|
| `filename_stem` | Route identity for `/series/<series_id>/`; layout comes from `_config.yml` collection defaults. |

## `series-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.series_id` | Payload identity. |
| `header.count` | Published work count. |
| `series.series_id` | Focused public series identity. |
| `series.status` | Focused public series workflow state. |
| `series.published_date` | Focused public series publication metadata. |
| `series.title` | Focused public series display metadata. |
| `series.series_type` | Focused public series metadata. |
| `series.year` | Focused public series date metadata. |
| `series.year_display` | Focused public series display date metadata. |
| `series.notes` | Focused public series metadata. |
| `series.sort_fields` | Public ordering context. |
| `series.project_folders[]` | Derived member-work project folders for Studio/public context. |
| `content_html` | Rendered series prose from `_docs_src_catalogue/series/<series_id>.md`. |

## `series-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.count` | Series count. |
| `series.<series_id>.series_id` | Series identity and map key consistency. |
| `series.<series_id>.status` | Series publication state. |
| `series.<series_id>.published_date` | Series publication metadata. |
| `series.<series_id>.title` | Public aggregate series display metadata and search source data. |
| `series.<series_id>.series_type` | Public aggregate series metadata and search source data. |
| `series.<series_id>.year` | Public aggregate series date metadata and search source data. |
| `series.<series_id>.year_display` | Public aggregate series display date metadata and search source data. |
| `series.<series_id>.notes` | Public aggregate series metadata. |
| `series.<series_id>.primary_work_id` | Series primary thumbnail/work context. |
| `series.<series_id>.sort_fields` | Ordering rule summary. |
| `series.<series_id>.project_folders[]` | Derived from member work `project_folder` values. |
| `series.<series_id>.works[]` | Ordered published member work ids derived from work `series_ids`, work `status`, and series `sort_fields`. |

## `recent-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.count` | Recent item count. |
| `entries[].kind` | Recent item type. |
| `entries[].target_id` | Recent item target identity. |
| `entries[].title` | Recent item display title from work or series metadata. |
| `entries[].caption` | Derived series/work publication caption. |
| `entries[].published_date` | Recent ordering and publication date context. |
| `entries[].recorded_at_utc` | Recent ordering and publication session context. |
| `entries[].session_order` | Recent ordering and publication session context. |
| `entries[].thumb_id` | Thumbnail target, usually work id or series primary work id. |

## `moment-page` Fields

| Artifact field | Purpose |
|---|---|
| `filename_stem` | Route identity for `/moments/<moment_id>/`; layout comes from `_config.yml` collection defaults. |

## `moment-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.moment_id` | Payload identity. |
| `moment.moment_id` | Public moment identity. |
| `moment.title` | Public moment display metadata. |
| `moment.date` | Public moment date metadata. |
| `moment.date_display` | Public moment display date metadata. |
| `moment.images[].file` | Public moment image filename derived from source image availability. |
| `moment.images[].alt` | Public moment image alt metadata. |
| `moment.width_px` | Source image dimension when available. |
| `moment.height_px` | Source image dimension when available. |
| `content_html` | Rendered moment prose from `_docs_src_catalogue/moments/<moment_id>.md`. |

## `moments-index-json` Fields

| Artifact field | Purpose |
|---|---|
| `header.schema` | Payload contract identifier. |
| `header.version` | Payload cache/change detection. |
| `header.generated_at_utc` | Payload generation timestamp. |
| `header.count` | Moment count. |
| `moments.<moment_id>.moment_id` | Moment identity and map key consistency. |
| `moments.<moment_id>.title` | Public index/card/search display title. |
| `moments.<moment_id>.date` | Public date and search metadata. |
| `moments.<moment_id>.date_display` | Public display date and search metadata. |
| `moments.<moment_id>.thumb_id` | Thumbnail availability marker, emitted only when image metadata exists. |

## `catalogue-search` Fields

| Artifact field | Purpose |
|---|---|
| `entries[].kind` | Search result type. |
| `entries[].id` | Search result identity. |
| `entries[].href` | Search result destination. |
| `entries[].title` | Search display title from works, series, or moments indexes. |
| `entries[].year` | Work/series search date value. |
| `entries[].date` | Moment search date value. |
| `entries[].display_meta` | Work `year_display`, series `year_display`, or moment `date_display` fallback. |
| `entries[].series_ids` | Work-to-series relation from `works-index-json`. |
| `entries[].series_titles` | Work series title labels from `series-index-json`. |
| `entries[].medium_type` | Work search enrichment from focused `work-json`. |
| `entries[].medium_caption` | Work search enrichment from focused `work-json`. |
| `entries[].series_type` | Series search enrichment from `series-index-json`. |
| `entries[].tag_ids` | Tag enrichment from Studio tag assignment data. |
| `entries[].tag_labels` | Tag enrichment from Studio tag registry data. |
| `entries[].search_terms` | Derived broad-match tokens from id, title, display metadata, dates, series data, medium data, and series type. |
| `entries[].search_text` | Derived broad-match text from id, title, display metadata, dates, series data, medium data, and series type. |

## `local-media` Fields

This section is a reference for the separate image-media workflow. It is not part of the field-aware JSON artifact dependency analysis.

Current Studio behavior keeps explicit image refresh separate from JSON rebuild scoping: the media readiness action calls `POST /catalogue/build-apply` with `media_only: true`, so it stages source images, regenerates local derivatives, and copies thumbnails without regenerating page JSON or catalogue search.

Replacing a source image with the same filename does not change catalogue source JSON. In the Studio save path, no source JSON change means no public JSON rebuild is requested. If a user changes metadata and an image is also pending, the normal scoped build may run media planning before JSON generation, but the JSON generation is caused by the source JSON change, not by the image replacement itself.

For Task 2, treat image media as out of scope for JSON artifact dependency rules. Keep `downloads` and `links` in scope because they are work-owned source JSON metadata, not image media.

| Artifact field | Purpose |
|---|---|
| `work.work_id` | Names staged source, primary derivatives, and thumbnail derivatives. |
| `work.project_folder` | Work source media path input. |
| `work.project_filename` | `project_folder` plus `project_filename` resolves the primary work source media path. |
| `work.source_mtime` | Compared with staged source and derivative mtimes to decide whether media is current or pending. |
| `work_detail.detail_uid` | Names staged source, primary derivatives, and thumbnail derivatives. |
| `work_detail.work_id` | Parent work identity used to find the parent work folder. |
| `work_detail.detail_id` | Contributes to `detail_uid`, which names staged source and derivative outputs. |
| `work_detail.parent_project_folder` | Parent work folder input for resolving the detail source media path. |
| `work_detail.project_subfolder` | Detail section folder input. |
| `work_detail.project_filename` | Parent folder plus `project_subfolder` plus `project_filename` resolves the detail source media path. |
| `work_detail.source_mtime` | Compared with staged source and derivative mtimes to decide whether media is current or pending. |
| `moment.moment_id` | Names staged source, primary derivatives, and thumbnail derivatives. |
| `moment.source_image_file` | Resolves the moment source media path under the configured moments image root. |
| `moment.source_mtime` | Compared with staged source and derivative mtimes to decide whether media is current or pending. |

## Local Media Field Summary

These are the current media-affecting field sets.

| Record family | Media-affecting source field | Why |
|---|---|---|
| work | `work_id` | Names primary work media derivative outputs. |
| work | `project_folder` | Resolves the primary work source media path. |
| work | `project_filename` | Resolves the primary work source media path. |
| work detail | `detail_uid` | Names detail media derivative outputs. |
| work detail | `work_id` | Resolves the parent work folder for detail source media. |
| work detail | `detail_id` | Contributes to `detail_uid`, which names detail media derivative outputs. |
| work detail | parent work `project_folder` | Resolves the parent work folder for detail source media. |
| work detail | `project_subfolder` | Resolves the detail source media path under the parent work folder. |
| work detail | `project_filename` | Resolves the detail source media path under the parent work folder and subfolder. |
| moment | `moment_id` | Names moment media derivative outputs. |
| moment | `source_image_file` | Resolves the moment source media path. |

Metadata-only source JSON changes should not be treated as image-media changes.

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

- Confirm whether route page artifacts should be selected only for create/delete/identity operations now that stubs are metadata-free.
- Confirm whether `work_prose_file` and `series_prose_file` are obsolete retained fields or future path overrides.
- Confirm whether any source field outside the media-affecting summary can change media manifests, copy lists, or media readiness output.
- Confirm whether `notes` and `provenance` are intentionally source/editor-only for works.
- Confirm whether `published_date` should remain transition/bookkeeping-only for works and moments or become public metadata.
- Confirm whether targeted catalogue search can safely update existing records in the future; current targeted catalogue policy is additive-only.
