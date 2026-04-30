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

The tables use artifact-family names rather than individual file paths when a family has one file per record.

Important distinction:

- "appears in" means the field is serialized into, rendered by, or directly used to build an artifact
- "controls" means the field can include, exclude, sort, name, or otherwise change an artifact without necessarily being serialized into it
- "media-affecting" means the field can change local media source resolution, generated derivative filenames, or derivative freshness checks
- "metadata-only candidate" means the field should be able to skip local media generation if no media-affecting field changed

## Artifact Families

| Artifact family | Outputs | Current builder | Notes |
|---|---|---|---|
| `source-json` | `assets/studio/data/catalogue/*.json` | `catalogue_source.py`, write server | Canonical Studio metadata source. Excluded from Jekyll build/watch. |
| `studio-lookup` | `assets/studio/data/catalogue_lookup/**` and `/catalogue/read` payloads | `catalogue_lookup.py`, write server | Studio read model for editor search, focused records, summaries, hashes, details, downloads, and links. |
| `work-page` | `_works/<work_id>.md` | `generate_work_pages.py` | Minimal front matter: `work_id`, `title`, `layout`, `checksum`. Checksum currently derives from the canonical work record, so broad metadata changes can still rewrite the page shell. |
| `work-json` | `assets/works/index/<work_id>.json` | `generate_work_pages.py` | Focused public work payload. Includes canonical work metadata, published detail sections, and rendered work prose. |
| `work-details-page` | `_work_details/<detail_uid>.md` | `generate_work_pages.py` | Minimal detail route page with identifiers and title. |
| `works-index-json` | `assets/data/works_index.json` | `generate_work_pages.py` | Lightweight aggregate work index used by public pages and catalogue search. |
| `work-storage-index-json` | `assets/studio/data/work_storage_index.json` | `generate_work_pages.py` | Studio-only storage index derived from `storage_location` via the runtime `storage` key. |
| `series-page` | `_series/<series_id>.md` | `generate_work_pages.py` | Minimal front matter: `series_id`, `title`, `layout`, `checksum`. |
| `series-json` | `assets/series/index/<series_id>.json` | `generate_work_pages.py` | Focused public series payload and rendered series prose. Does not currently serialize `primary_work_id`. |
| `series-index-json` | `assets/data/series_index.json` | `generate_work_pages.py` | Aggregate series index. Owns series membership, ordering, `primary_work_id`, project folders, and public series summary data. |
| `recent-index-json` | `assets/data/recent_index.json` | `generate_work_pages.py` | Transition-driven recent-publications index. Mostly affected by publish transitions and current work/series membership data. |
| `moment-page` | `_moments/<moment_id>.md` | `generate_work_pages.py` | Minimal front matter: `moment_id`, `title`, `layout`, `checksum`. |
| `moment-json` | `assets/moments/index/<moment_id>.json` | `generate_work_pages.py` | Focused public moment payload and rendered moment prose. |
| `moments-index-json` | `assets/data/moments_index.json` | `generate_work_pages.py` | Lightweight aggregate moment index used by public pages and catalogue search. |
| `catalogue-search` | `assets/data/search/catalogue/index.json` | `build_search.rb` | Reads `series_index`, `works_index`, `moments_index`, per-work JSON metadata, tag assignments, and tag registry. |
| `local-media` | `var/catalogue/media/**`, copied thumbnail assets under `assets/**/img/` | `catalogue_json_build.py` | Resolves source image paths and derivative outputs for works, work details, and moments. |

## Works Fields

| Source field | Artifact families | Current role | Media-affecting | Notes |
|---|---|---|---|---|
| `work_id` | all work families, `series-index-json`, `catalogue-search`, `local-media` | Record identity, route filename, JSON key, media output stem, series membership target. | yes | Treat changes as structural create/delete, not metadata updates. |
| `status` | `studio-lookup`, `work-page`, `work-json`, `work-details-page`, indexes, `recent-index-json`, `catalogue-search` | Controls whether draft/published rows are actionable and publish transition behavior. | no | Publish transitions can update `published_date` and recent index. |
| `published_date` | `studio-lookup`, `recent-index-json` | Used for publish transition records and source metadata. | no | Not currently part of the public work index row. |
| `series_ids` | `studio-lookup`, `work-page`, `work-json`, `works-index-json`, `series-index-json`, `catalogue-search`, `recent-index-json` | Drives work membership, primary series fallback, series summaries, search series titles, and work tag inheritance. | no | Requires old and new related series when changed. |
| `series_title` | `studio-lookup` | Retained source field; generated runtime derives current series title from series records. | no | Should be treated as source-only unless a current consumer is found. |
| `project_folder` | `studio-lookup`, `series-index-json`, `local-media` | Resolves work primary media and detail media through parent work folder; contributes aggregate series `project_folders`. | yes | Metadata-only saves should not include this in the skip-media set. |
| `project_filename` | `studio-lookup`, `local-media` | Resolves work primary source media and dimension refresh. | yes | Does not currently serialize into public work JSON. |
| `title` | `studio-lookup`, `work-page`, `work-json`, `works-index-json`, `series-index-json`, `recent-index-json`, `catalogue-search` | Visible title, work index title, search title, recent title, optional series ordering when `sort_fields` uses title. | no | Can require series index refresh when a series sorts by title. |
| `year` | `studio-lookup`, `work-page`, `work-json`, `works-index-json`, `series-index-json`, `catalogue-search` | Work date metadata, search year, optional series ordering when `sort_fields` uses year. | no | Can require series index refresh when used by series sort rules. |
| `year_display` | `studio-lookup`, `work-page`, `work-json`, `works-index-json`, `series-index-json`, `catalogue-search` | Display date metadata, work index display meta, series member display context. | no | Usually work/index/search, plus series index if member display changes. |
| `medium_type` | `studio-lookup`, `work-page`, `work-json`, `catalogue-search` | Work metadata and search structured field. | no | Search reads this from per-work JSON, not `works_index`. |
| `medium_caption` | `studio-lookup`, `work-page`, `work-json`, `catalogue-search` | Work metadata and search enrichment. | no | Search reads this from per-work JSON. |
| `storage_location` | `studio-lookup`, `work-page`, `work-json`, `work-storage-index-json` | Source key is emitted as runtime `storage`. | no | Studio-only storage index should be selected when this changes. |
| `width_cm`, `height_cm`, `depth_cm` | `studio-lookup`, `work-page`, `work-json`, `series-index-json` when used by `sort_fields` | Physical dimensions and optional series sorting inputs. | no | Metadata-only candidates unless used by a series sort rule. |
| `width_px`, `height_px` | `studio-lookup`, `work-page`, `work-json` | Primary image dimensions, often refreshed from source media. | no | Output of media/dimension lookup, but changing only stored dimensions should not regenerate derivatives. |
| `duration` | `studio-lookup`, `work-page`, `work-json` | Work metadata. | no | Metadata-only candidate. |
| `notes` | `studio-lookup` | Source/editor note field. | no | No public generator consumer found in the current runtime payload path. |
| `provenance` | `studio-lookup` | Source/editor provenance field. | no | No public generator consumer found in the current runtime payload path. |
| `artist` | `studio-lookup`, `work-page`, `work-json` | Work metadata. | no | Metadata-only candidate. |
| `downloads` | `studio-lookup`, `work-page`, `work-json` | Work-owned files exposed in the focused work payload/editor model. | no | Should not require series artifacts unless another consumer is added. |
| `links` | `studio-lookup`, `work-page`, `work-json` | Work-owned links exposed in the focused work payload/editor model. | no | Should not require series artifacts unless another consumer is added. |
| `work_prose_file` | `studio-lookup` | Retained source field. | no | Current generator resolves work prose by `work_id` under `_docs_src_catalogue/works/`; confirm whether this field is obsolete or reserved. |

## Work Detail Fields

| Source field | Artifact families | Current role | Media-affecting | Notes |
|---|---|---|---|---|
| `detail_uid` | `studio-lookup`, `work-details-page`, `work-json`, `local-media` | Record identity and detail route/media output stem. | yes | Derived from `work_id` and `detail_id`; structural if it changes. |
| `work_id` | `studio-lookup`, `work-details-page`, parent `work-json`, `local-media` | Parent relation, page route prefix, detail grouping under parent work. | yes | Requires parent work refresh and may change media source folder resolution. |
| `detail_id` | `studio-lookup`, `work-details-page`, parent `work-json`, `local-media` | Detail route suffix, detail ordering within sections, media output stem. | yes | Structural if changed. |
| `title` | `studio-lookup`, `work-details-page`, parent `work-json` | Detail display title in route page and parent work detail sections. | no | Metadata-only candidate. |
| `status` | `studio-lookup`, `work-details-page`, parent `work-json` | Controls whether the detail page is generated and whether published details are included in parent work JSON. | no | Publish transitions can set `published_date`. |
| `published_date` | `studio-lookup` | Source metadata and publish transition bookkeeping. | no | No public detail date artifact found. |
| `project_subfolder` | `studio-lookup`, parent `work-json`, `local-media` | Groups detail sections and resolves detail media path. | yes | Changing it can move a detail between public sections and change source media path. |
| `project_filename` | `studio-lookup`, `local-media` | Resolves detail source media and dimension refresh. | yes | Does not currently serialize into parent work JSON. |
| `width_px`, `height_px` | `studio-lookup`, parent `work-json` | Detail image dimensions in parent work sections. | no | Output of dimension lookup; changing only stored dimensions should not regenerate derivatives. |

## Series Fields

| Source field | Artifact families | Current role | Media-affecting | Notes |
|---|---|---|---|---|
| `series_id` | all series families, work membership lookups, `catalogue-search`, tags | Record identity, route filename, JSON key, membership target, tag-assignment key. | no | Treat changes as structural create/delete. |
| `title` | `studio-lookup`, `series-page`, `series-json`, `series-index-json`, `work-json`, `catalogue-search`, `recent-index-json` | Visible series title, search title, work lookup summary title, recent title. | no | Work lookup/search may need refresh when a related series title changes. |
| `status` | `studio-lookup`, `series-page`, `series-json`, `series-index-json`, `recent-index-json`, `catalogue-search` | Controls series publication, series artifact generation, and membership visibility. | no | Publish transitions can affect attached draft works in write-server flows. |
| `published_date` | `studio-lookup`, `series-json`, `series-index-json`, `recent-index-json` | Series publication date and recent ordering context. | no | Usually series/index/recent. |
| `series_type` | `studio-lookup`, `series-json`, `series-index-json`, `catalogue-search` | Public series metadata and search structured field. | no | Metadata-only candidate. |
| `year` | `studio-lookup`, `series-json`, `series-index-json`, `catalogue-search` | Series date metadata and search year. | no | Metadata-only candidate. |
| `year_display` | `studio-lookup`, `series-json`, `series-index-json`, `catalogue-search` | Series display date/search display meta. | no | Metadata-only candidate. |
| `primary_work_id` | `studio-lookup`, `series-index-json`, `recent-index-json` | Primary thumbnail/work context for series aggregate data. | no | Removed from focused per-series JSON; still required for published series index/recent behavior. |
| `sort_fields` | `studio-lookup`, `series-json`, `series-index-json` | Defines work ordering inputs for each series. | no | May require related work fields used by the sort to select series index refresh. |
| `notes` | `studio-lookup`, `series-json`, `series-index-json` | Public/source series notes. | no | Metadata-only candidate. |
| `series_prose_file` | `studio-lookup` | Retained source field. | no | Current generator resolves series prose by `series_id` under `_docs_src_catalogue/series/`; confirm whether this field is obsolete or reserved. |
| computed `project_folders` | `series-json`, `series-index-json` | Derived from member works' `project_folder` values. | yes via work `project_folder` | Not a source field, but work `project_folder` changes can affect series outputs. |
| computed `works` | `series-index-json`, `recent-index-json` | Derived published member work list. | no | Affected by work `series_ids`, work `status`, and series sort rules. |

## Moment Fields

| Source field | Artifact families | Current role | Media-affecting | Notes |
|---|---|---|---|---|
| `moment_id` | all moment families, `catalogue-search`, `local-media` | Record identity, route filename, JSON key, media output stem. | yes | Treat changes as structural create/delete. |
| `title` | `studio-lookup`, `moment-page`, `moment-json`, `moments-index-json`, `catalogue-search` | Visible moment title, search title, image-alt fallback when `image_alt` is absent. | no | Public JSON/index/search, but no derivative regeneration required by itself. |
| `status` | `studio-lookup`, `moment-page`, `moment-json`, `moments-index-json`, `catalogue-search` | Controls whether moment artifacts are generated. | no | Publish transitions can affect generated scope and search. |
| `published_date` | `studio-lookup` | Source metadata and publish workflow state. | no | No direct public moment date artifact found beyond generation control. |
| `date` | `studio-lookup`, `moment-json`, `moments-index-json`, `catalogue-search` | Moment date metadata and search date. | no | Metadata-only candidate. |
| `date_display` | `studio-lookup`, `moment-json`, `moments-index-json`, `catalogue-search` | Moment display date/search display meta. | no | Metadata-only candidate. |
| `source_image_file` | `studio-lookup`, `moment-json`, `moments-index-json`, `local-media` | Resolves moment source media and controls whether `images`/`thumb_id` are emitted. | yes | Changing it must select media readiness/generation. |
| `image_alt` | `studio-lookup`, `moment-json` | Public image alt metadata. | no | Metadata-only candidate for media, but still requires moment JSON refresh. |
| `width_px`, `height_px` | `moment-json` | Moment image dimensions refreshed from source media when possible. | no | Generated/derived dimensions, not a media trigger by themselves. |
| prose body | `moment-json` | Rendered into `content_html`. | no | Prose changes require moment JSON/page checks and search only if search starts indexing body text later. |

## Search Field Sources

Catalogue search currently combines aggregate indexes, per-work JSON metadata, and tags.

| Search field | Source fields | Source family |
|---|---|---|
| `kind`, `id`, `href` | artifact identity | `catalogue_indexes` |
| `title` | work `title`, series `title`, moment `title` | `catalogue_indexes` |
| `year` | work `year`, series `year` | `catalogue_indexes` |
| `date` | moment `date` | `catalogue_indexes` |
| `display_meta` | work `year_display`, series `year_display`, moment `date_display` fallback to `date` | `catalogue_indexes` |
| `series_ids` | work `series_ids` | `catalogue_indexes` |
| `series_titles` | titles for work `series_ids` from `series-index-json` | `catalogue_indexes` |
| `medium_type` | work `medium_type` from per-work JSON | `catalogue_work_payloads` |
| `medium_caption` | work `medium_caption` from per-work JSON | `catalogue_work_payloads` |
| `series_type` | series `series_type` | `catalogue_indexes` |
| `tag_ids`, `tag_labels` | tag assignment and registry data | tag source families |
| `search_terms`, `search_text` | derived from ids, titles, display meta, dates, series data, medium fields, and series type | derived |

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

