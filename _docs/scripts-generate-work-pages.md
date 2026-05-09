---
doc_id: scripts-generate-work-pages
title: "Generate Work Pages"
added_date: 2026-04-19
last_updated: "2026-05-09 19:09"
parent_id: archive
sort_order: 50
---

# Deprecated: Generate Work Pages

Status:

- deprecated direct entrypoint
- retained for historical context only

This document describes the retired direct `generate_work_pages.py` command surface. The live catalogue workflow now uses `catalogue_json_build.py`, which calls the generator internally for scoped JSON builds.

Script:

```bash
./scripts/generate_work_pages.py
```

Common runs:

```bash
./scripts/generate_work_pages.py
./scripts/generate_work_pages.py --write
./scripts/catalogue_json_build.py --work-id 00456
./scripts/catalogue_json_build.py --work-id 00456 --write
./scripts/catalogue_json_build.py --moment-file keys.md
./scripts/catalogue_json_build.py --moment-file keys.md --write
```

Before any writes begin, the generator validates canonical source records and moment-source inputs before file writes or canonical source updates start.

Generator log output also shortens local absolute paths for source, staged-media, and generated-file messages so routine runs no longer echo machine-specific roots.

When `--write` is used, the generator writes mutable catalogue/source state back into canonical JSON rather than into a workbook.

Current helper ownership:

- `scripts/catalogue_generation_records.py` owns pure public work, series, detail, and moment record projection helpers
- `scripts/catalogue_generation_indexes.py` owns pure series/work aggregate contexts plus series, works, and Studio storage index payload builders
- `scripts/catalogue_generation_recent.py` owns pure recent-publications entry normalization, merge rules, published-target filtering, sorting, and `recent_index_v1` payload construction
- `scripts/generate_work_pages.py` remains the internal CLI/path/write orchestration layer for source loading, rendering, generated-file decisions, source write-back, and run summaries

Moment canonical source model:

- metadata source: `assets/studio/data/catalogue/moments.json`
- source prose file: `_docs_catalogue/moments/<moment_id>.md`
- canonical `moment_id`: filename stem
- required metadata:
  - `title`
  - `status`
  - `published_date`
  - `date`
- optional metadata:
  - `date_display`
  - `source_image_file`
  - `image_alt`
- default source image path:
  - `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/images/<moment_id>.jpg`
- when `source_image_file` is present:
  - source image lookup uses that filename instead
- public/generated moment image stem remains `<moment_id>`
- moment prose Markdown is body-only; the generator no longer writes moment source front matter

## Useful Flags

- `--internal-json-source-run`
  - internal-only flag used by `catalogue_json_build.py`
  - direct manual use is not part of the supported workflow
- `--write`: persist generated file changes plus canonical-source work/work-detail/series updates
- `--source-dir` with default `assets/studio/data/catalogue`
  - canonical source JSON directory for the internal run
- `--force`: force rewrites even when generated content would otherwise match
  - for route-anchor collection stubs, this is also the explicit way to normalize an existing older metadata-bearing stub to the current empty-front-matter shape
- `--refresh-published`
  - internal narrow refresh mode used by `catalogue_json_build.py`
  - lets selected published records be processed for prose/runtime payload recomputation without forcing unchanged aggregate JSON or catalogue search rewrites
  - does not refresh `published_date` for already-published records
- `--work-ids`, `--work-ids-file`
- `--series-ids`, `--series-ids-file`
  - accepts numeric series IDs and current legacy slug-style series IDs during transition
- `--moment-ids`, `--moment-ids-file`
- `--moments-output-dir` with default `_moments`
- `--moments-json-dir` with default `assets/moments/index`
  - writes per-moment JSON payloads at `assets/moments/index/<moment_id>.json`
  - renders canonical moment prose from `_docs_catalogue/moments/<moment_id>.md` using the local Jekyll markdown stack
  - generated together with `_moments/<moment_id>.md` when `moments` is selected
  - JSON is now the canonical runtime source for moment date, image, and prose content
  - generated `_moments/<moment_id>.md` files are metadata-free route-anchor stubs
- `--moments-index-json-path` with default `assets/data/moments_index.json`
  - writes a lightweight moments index object keyed by `moment_id`
  - rebuilt on every pipeline run as a full index and not scoped by `--moment-ids`
- `--projects-base-dir`
  - defaults from `DOTLINEFORM_PROJECTS_BASE_DIR` in `var/local/site.env` for local runs
  - used for work-detail sources plus source media dimension lookups
  - refreshes work primary-image dimensions only when `work-json` is selected directly or indirectly via `work-pages`
- `--series-index-json-path` with default `assets/data/series_index.json`
- `--works-index-json-path` with default `assets/data/works_index.json`
- `--recent-index-json-path` with default `assets/data/recent_index.json`
  - writes a capped recent-publications ledger for `/recent/`
  - snapshots only first-time `draft -> published` transitions for series and works
  - groups multiple newly published works in the same existing series into one work entry anchored to the first published work in that run
  - prunes entries whose target series or work no longer exists or is no longer published in the current catalogue
  - the old workbook-history backfill script has been removed; current updates come from scoped JSON-source publish runs
- `--series-json-dir` with default `assets/series/index`
  - writes per-series JSON payloads at `assets/series/index/<series_id>.json`
  - resolves canonical series prose from `_docs_catalogue/series/<series_id>.md`
  - still writes JSON when the ID-derived prose source file is missing, but leaves `content_html` blank

Work prose source path:

- canonical Markdown lives at `_docs_catalogue/works/<work_id>.md`
- source filenames are ID-derived and do not depend on `Works.work_prose_file`
- if the ID-derived source file is missing, work page and work JSON generation still continue
- in that case the work record is written without prose content and `content_html` is omitted or empty at runtime

## `--only` Artifacts

`--only` limits generation to selected artifacts, but aggregate index JSON artifacts for `series`, `works`, and `moments` are always rebuilt on every run.

Allowed values:

- `work-pages`
- `series-pages`
- `series-index-json`
- `work-details-pages`
- `work-json`
- `works-index-json`
- `moments`
- `moments-index-json`

Artifact behavior:

- `work-pages`
  writes `_works/<work_id>.md` as metadata-free route-anchor stubs
- `series-pages`
  writes `_series/<series_id>.md` metadata-free route-anchor stubs plus `assets/series/index/<series_id>.json` for published series only; per-series JSON carries page-local metadata and prose, while membership stays canonical in `assets/data/series_index.json`
- `work-details-pages`
  writes `_work_details/<detail_uid>.md` metadata-free route-anchor stubs
- `moments`
  writes both `_moments/<moment_id>.md` route-anchor stubs and `assets/moments/index/<moment_id>.json`
- `moments-index-json`
  writes `assets/data/moments_index.json` as a lightweight full index keyed by `moment_id`
- `series-index-json`
  writes `assets/data/series_index.json` as a full rebuild
- `works-index-json`
  writes `assets/data/works_index.json` as a lightweight full rebuild keyed by `work_id`
  for shared card and lookup metadata
  and writes `assets/studio/data/work_storage_index.json` as a Studio-only companion lookup for curator storage values
- `recent-index-json`
  writes `assets/data/recent_index.json` as a capped recent-publications ledger for `/recent/`; retained entries must still point at currently published series or works
- `work-json`
  writes `assets/works/index/<work_id>.json` with full `work`, section-level detail grouping, and rendered `content_html` when work prose exists. Sections carry `section_id`, `section_title`, optional `sort_order`, and `details[]`; nested detail records do not repeat section-level metadata.

There is no separate `works-prose` artifact; use `work-json` for prose-only refreshes.

Scoped refresh behavior:

- selected published records are processed when `--refresh-published` or `--force` is present
- existing route-anchor stubs are skipped unless `--force` is present; missing stubs are still created
- draft series are not actionable generator records and are excluded from public series pages and series index payloads
- unchanged generated artifacts still skip under `--refresh-published` when their content version matches
- `published_date` updates are reserved for first-time `draft -> published` transitions
- `--force` remains the explicit stronger mode for full rewrites and timestamp refreshes in generated payload headers

## Source Validation

The internal generator currently stops the run when actionable canonical source records contain blocking structural errors such as:

- malformed `work_id`, `detail_id`, `series_id`, or `moment_id` values
- `works.series_ids` values that do not normalize to a valid series ID or do not exist in `series`
- missing `series.primary_work_id`
- `series.primary_work_id` values that do not resolve to a `works` record
- `series.primary_work_id` values whose `works.series_ids` do not include that series
- `work_details.work_id` values that do not resolve to `works`
- work-detail section metadata that is missing or malformed under the migrated source schema
- non-slug-safe moment ids in `assets/studio/data/catalogue/moments.json`

This validation runs before generated files or canonical source status/date updates are written, so those failures no longer appear after a partially written run.

## Runtime Canonical Data Flow

- `/series/` reads `assets/data/series_index.json` and `assets/data/moments_index.json` for the merged works and moments catalogue
- `/recent/` reads `assets/data/recent_index.json`
- `/series/<series_id>/` reads `assets/data/series_index.json`
- `/series/<series_id>/` also reads `assets/data/works_index.json` for card metadata
- `/series/<series_id>/` reads `assets/series/index/<series_id>.json` for series prose HTML
- `/works/<work_id>/` reads `assets/works/index/<work_id>.json` for metadata, prose HTML, and detail sections; series nav state also reads `assets/data/series_index.json`
- `/work_details/<detail_uid>/` derives `work_id` from the `detail_uid` route prefix and then fetches `assets/works/index/<work_id>.json`
- `/moments/<moment_id>/` reads `assets/moments/index/<moment_id>.json`
- `/search/` reads `assets/data/search/catalogue/index.json`
- `/studio/studio-works/` reads `assets/studio/data/work_storage_index.json` for curator-only storage values

Catalogue search note:

- `generate_work_pages.py` no longer writes `assets/data/search/catalogue/index.json`
- catalogue search is now rebuilt separately by [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) from the generated repo JSON artifacts above plus Studio tag metadata

## Generator Module Ownership

`generate_work_pages.py` remains the internal orchestration entrypoint for the catalogue JSON build pipeline.
Pure generated-record shaping lives in `scripts/catalogue_generation_records.py`.
Pure series/work aggregate context and index payload construction lives in `scripts/catalogue_generation_indexes.py`, including series sort context, published series membership, primary-work validation, `assets/data/series_index.json`, `assets/data/works_index.json`, and `assets/studio/data/work_storage_index.json` payload construction.
The generator still owns CLI parsing, path binding, Markdown rendering, existing-version comparisons, dry-run/write reporting, file writes, source write-back, and event logging.

## Internal JSON Source Mode

`--internal-json-source-run` is the internal generator mode used by `catalogue_json_build.py`.

Current behavior:

- reads canonical source JSON from `assets/studio/data/catalogue/`
- builds work, series, work-detail, and moment artifacts from canonical source records rather than workbook-shaped row projections
- resolves work source media from `project_folder`, optional `project_subfolder`, and `project_filename`
- resolves work-detail source media from the parent work's `project_folder`, optional detail `details_subfolder`, and detail `project_filename`
- writes per-work runtime detail sections with section-level `section_id`, `section_title`, and optional `sort_order`; nested detail records do not repeat those section fields and do not carry route `layout`
- writes the runtime artifacts selected by the scoped JSON build flow
- when `--write` is used, mutates generator-updated mutable fields directly on canonical source records before source JSON write-back:
  - work `status`, `published_date`, `width_px`, `height_px`
  - work-detail `status`, `published_date`, `width_px`, `height_px`

Work-owned `downloads` and `links` remain on the canonical work record and are not processed as separate artifacts.

Validation note:

- JSON source records are validated before generation and again before source write-back
- use [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source) for direct JSON source validation

## Works Download Files

If `Works.downloads` contains entries for a work, generation stages those files and exposes them as `work.downloads` in per-work JSON.

- source path:
  - `[projects-base-dir]/projects/[project_folder]/[filename]`
- destination path:
  - `var/catalogue/media/works/files/[work_id]-[url-safe-filename.ext]`
  - staged filenames preserve the extension and normalize the basename for URLs
- work page link:
  - label is `download` or `downloads`
  - link text comes from `downloads[].label`
  - rendered before `cat. <work_id>`

## Works Published Links

If `Works.links` contains entries for a work, generation exposes them as `work.links` in per-work JSON.

- source fields:
  - `links[].url`
  - `links[].label`
- work page row:
  - caption stays `published on`
  - links render as a comma-delimited list using `links[].label`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
