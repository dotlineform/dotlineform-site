---
doc_id: scripts-generate-work-pages
title: "Generate Work Pages"
added_date: 2026-04-19
last_updated: 2026-04-27
parent_id: _archive
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

Before any writes begin, the generator validates canonical source records and moment-source inputs before file writes or canonical source status/date updates start.

Generator log output also shortens local absolute paths for source, staged-media, and generated-file messages so routine runs no longer echo machine-specific roots.

When `--write` is used, the generator writes mutable catalogue/source state back into canonical JSON and moment source front matter rather than into a workbook.

Moment canonical source model:

- source prose file: `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md`
- canonical `moment_id`: filename stem
- required front matter:
  - `title`
  - `status`
  - `published_date`
  - `date`
- optional front matter:
  - `date_display`
  - `image_file`
- default source image path:
  - `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/images/<moment_id>.jpg`
- when `image_file` is present:
  - source image lookup uses that filename instead
- public/generated moment image stem remains `<moment_id>`

## Useful Flags

- `--internal-json-source-run`
  - internal-only flag used by `catalogue_json_build.py`
  - direct manual use is not part of the supported workflow
- `--write`: persist generated file changes plus canonical-source work/work-detail/link/series updates
- `--source-dir` with default `assets/studio/data/catalogue`
  - canonical source JSON directory for the internal run
- `--force`: force rewrites even when checksums or content versions match
- `--refresh-published`
  - internal narrow refresh mode used by `catalogue_json_build.py`
  - lets selected published records be processed for prose/runtime payload recomputation without forcing unchanged aggregate JSON or catalogue search rewrites
  - does not refresh `published_date` for already-published records
- `--work-ids`, `--work-ids-file`
- `--series-ids`, `--series-ids-file`
  - accepts numeric series IDs and current legacy slug-style series IDs during transition
- `--moment-ids`, `--moment-ids-file`
- `--work-files-sheet` with default `WorkFiles`
- `--work-links-sheet` with default `WorkLinks`
- `--moments-output-dir` with default `_moments`
- `--moments-json-dir` with default `assets/moments/index`
  - writes per-moment JSON payloads at `assets/moments/index/<moment_id>.json`
  - renders canonical moment prose from `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md` using the local Jekyll markdown stack
  - generated together with `_moments/<moment_id>.md` when `moments` is selected
  - JSON is now the canonical runtime source for moment date, image, and prose content
  - generated `_moments/<moment_id>.md` files are minimal stubs with `moment_id`, `title`, `layout`, and `checksum`
- `--moments-index-json-path` with default `assets/data/moments_index.json`
  - writes a lightweight moments index object keyed by `moment_id`
  - rebuilt on every pipeline run as a full index and not scoped by `--moment-ids`
- `--projects-base-dir`
  - defaults from `DOTLINEFORM_PROJECTS_BASE_DIR`
  - used for work-detail and work-file sources, moment source files, and source media dimension lookups
  - refreshes work primary-image dimensions only when `work-json` is selected directly or indirectly via `work-pages`
- `--media-base-dir`
  - defaults from `DOTLINEFORM_MEDIA_BASE_DIR`
  - stages downloadable files to `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/`
- `--series-index-json-path` with default `assets/data/series_index.json`
- `--works-index-json-path` with default `assets/data/works_index.json`
- `--recent-index-json-path` with default `assets/data/recent_index.json`
  - writes a capped recent-publications ledger for `/recent/`
  - snapshots only first-time `draft -> published` transitions for series and works
  - groups multiple newly published works in the same existing series into one work entry anchored to the first published work in that run
  - prunes entries whose target series or work no longer exists in the current catalogue
  - existing ledgers can be seeded once from workbook git history with `scripts/backfill_recent_index_from_git_history.py`
- `--series-json-dir` with default `assets/series/index`
  - writes per-series JSON payloads at `assets/series/index/<series_id>.json`
  - resolves canonical series prose from `_docs_src_catalogue/series/<series_id>.md`
  - still writes JSON when the ID-derived prose source file is missing, but leaves `content_html` blank

Work prose source path:

- canonical Markdown lives at `_docs_src_catalogue/works/<work_id>.md`
- source filenames are ID-derived and do not depend on `Works.work_prose_file`
- if the ID-derived source file is missing, work page and work JSON generation still continue
- in that case the work record is written without prose content and `content_html` is omitted or empty at runtime

## `--only` Artifacts

`--only` limits generation to selected artifacts, but aggregate index JSON artifacts for `series`, `works`, and `moments` are always rebuilt on every run.

Allowed values:

- `work-pages`
- `work-files`
- `work-links`
- `series-pages`
- `series-index-json`
- `work-details-pages`
- `work-json`
- `works-index-json`
- `moments`
- `moments-index-json`

Artifact behavior:

- `work-pages`
  writes `_works/<work_id>.md` as lightweight stubs with `work_id`, `title`, `layout`, and `checksum`
- `work-files`
  stages `WorkFiles` rows for in-scope works into `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/` and updates `WorkFiles.status` and `published_date` on `--write`
- `work-links`
  updates `WorkLinks.status` and `published_date` for in-scope works on `--write`
- `series-pages`
  writes `_series/<series_id>.md` lightweight stubs plus `assets/series/index/<series_id>.json`
- `work-details-pages`
  writes `_work_details/<detail_uid>.md` lightweight stubs
- `moments`
  writes both `_moments/<moment_id>.md` stubs and `assets/moments/index/<moment_id>.json`
- `moments-index-json`
  writes `assets/data/moments_index.json` as a lightweight full index keyed by `moment_id`
- `series-index-json`
  writes `assets/data/series_index.json` as a full rebuild
- `works-index-json`
  writes `assets/data/works_index.json` as a lightweight full rebuild keyed by `work_id`
  for shared card and lookup metadata
  and writes `assets/studio/data/work_storage_index.json` as a Studio-only companion lookup for curator storage values
- `recent-index-json`
  writes `assets/data/recent_index.json` as a capped recent-publications ledger for `/recent/`
- `work-json`
  writes `assets/works/index/<work_id>.json` with full `work`, `sections[].details[]`, and rendered `content_html` when work prose exists

There is no separate `works-prose` artifact; use `work-json` for prose-only refreshes.

Scoped refresh behavior:

- selected published records are processed when `--refresh-published` or `--force` is present
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
- non-slug-safe moment source filenames under `moments/*.md`

This validation runs before generated files or canonical source status/date updates are written, so those failures no longer appear after a partially written run.

## Runtime Canonical Data Flow

- `/series/` reads `assets/data/series_index.json` and `assets/data/moments_index.json` for the merged works and moments catalogue
- `/recent/` reads `assets/data/recent_index.json`
- `/series/<series_id>/` reads `assets/data/series_index.json`
- `/series/<series_id>/` also reads `assets/data/works_index.json` for card metadata
- `/series/<series_id>/` reads `assets/series/index/<series_id>.json` for series prose HTML
- `/works/<work_id>/` reads `assets/works/index/<work_id>.json` for metadata, prose HTML, and detail sections; series nav state also reads `assets/data/series_index.json`
- `/work_details/<detail_uid>/` reads stub front matter for `work_id` and then fetches `assets/works/index/<work_id>.json`
- `/moments/<moment_id>/` reads `assets/moments/index/<moment_id>.json`
- `/search/` reads `assets/data/search/catalogue/index.json`
- `/studio/studio-works/` reads `assets/studio/data/work_storage_index.json` for curator-only storage values

Catalogue search note:

- `generate_work_pages.py` no longer writes `assets/data/search/catalogue/index.json`
- catalogue search is now rebuilt separately by [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) from the generated repo JSON artifacts above plus Studio tag metadata

## JSON Source Mode

`--source json` is the Phase 1 bridge from workbook-led generation to JSON-led generation.

Current behavior:

- reads canonical source JSON from `assets/studio/data/catalogue/`
- materializes those records into a temporary workbook with the current worksheet names and columns
- runs the existing generation logic against that temporary workbook
- writes the same runtime artifacts as workbook mode
- when `--write` is used, syncs generator-updated mutable fields back into source JSON:
  - work `status`, `published_date`, `width_px`, `height_px`
  - work-detail `status`, `published_date`, `width_px`, `height_px`
  - series `status`, `published_date`
  - work-file and work-link `status`, `published_date`

This keeps the public runtime JSON contracts stable while the generator is being refactored toward a native JSON source adapter.

Validation note:

- JSON source mode still passes through the current workbook/source preflight after materialization
- use [Catalogue Source Export](/docs/?scope=studio&doc=scripts-catalogue-source) for direct JSON source validation and workbook-vs-JSON comparison

## Works Download Files

If `WorkFiles` contains rows for a work, generation stages those files and exposes them as `work.downloads` in per-work JSON.

- source path:
  - `[projects-base-dir]/projects/[project_folder]/[filename]`
- destination path:
  - `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/[work_id]-[url-safe-filename.ext]`
  - staged filenames preserve the extension and normalize the basename for URLs
- work page link:
  - label is `download` or `downloads`
  - link text comes from `WorkFiles.label`
  - rendered before `cat. <work_id>`

## Works Published Links

If `WorkLinks` contains rows for a work, generation exposes them as `work.links` in per-work JSON.

- source fields:
  - `WorkLinks.URL`
  - `WorkLinks.label`
- work page row:
  - caption stays `published on`
  - links render as a comma-delimited list using `WorkLinks.label`

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
