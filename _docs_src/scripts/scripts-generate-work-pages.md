---
doc_id: scripts-generate-work-pages
title: Generate Work Pages
last_updated: 2026-04-01
parent_id: scripts
sort_order: 50
---

# Generate Work Pages

Script:

```bash
./scripts/generate_work_pages.py
```

Common runs:

```bash
./scripts/generate_work_pages.py
./scripts/generate_work_pages.py --write
./scripts/generate_work_pages.py --work-ids 00456 --write
./scripts/generate_work_pages.py --work-ids-file /tmp/work_ids.txt --write
./scripts/generate_work_pages.py --series-ids curve-poems,dots --write
./scripts/generate_work_pages.py --only moments --moment-ids blue-sky --write
```

Before any writes begin, the generator now runs the same shared catalogue workbook preflight used by `build_catalogue.py`. Blocking workbook errors are aggregated and reported together before file writes or workbook status updates start.

Generator log output also shortens local absolute paths for workbook, source, staged-media, and generated-file messages so routine runs no longer echo machine-specific roots.

## Useful Flags

- `--write`: persist file and workbook changes
- `--force`: regenerate even when checksums match
- `--work-ids`, `--work-ids-file`
- `--series-ids`, `--series-ids-file`
- `--moment-ids`, `--moment-ids-file`
- `--work-files-sheet` with default `WorkFiles`
- `--work-links-sheet` with default `WorkLinks`
- `--moments-sheet` with default `Moments`
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
  - used for canonical work prose, work-detail and work-file sources, moment source files, and series prose source files
  - refreshes work primary-image dimensions only when `work-json` is selected directly or indirectly via `work-pages`
- `--media-base-dir`
  - defaults from `DOTLINEFORM_MEDIA_BASE_DIR`
  - stages downloadable files to `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/`
- `--series-index-json-path` with default `assets/data/series_index.json`
- `--works-index-json-path` with default `assets/data/works_index.json`
- `--series-json-dir` with default `assets/series/index`
  - writes per-series JSON payloads at `assets/series/index/<series_id>.json`
  - resolves canonical series prose from `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<primary_work_project_folder>/<paths.source_subdirs.prose>/<series_prose_file>`
  - still writes JSON when `Series.series_prose_file` is empty, but omits `content_html`

Work prose source path:

- canonical Markdown lives at `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<project_folder>/<paths.source_subdirs.prose>/<work_prose_file>`
- default `paths.source_subdirs.prose` value is `site text`
- if `Works.work_prose_file` is empty, cannot be resolved, or points at a missing Markdown file, work page and work JSON generation still continue
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
- `work-json`
  writes `assets/works/index/<work_id>.json` with full `work`, `sections[].details[]`, and rendered `content_html` when work prose exists

There is no separate `works-prose` artifact; use `work-json` for prose-only refreshes.

## Workbook Preflight

The shared preflight currently stops the run when actionable catalogue rows contain blocking workbook errors such as:

- malformed `work_id`, `detail_id`, `series_id`, or `moment_id` values
- `Works.series_ids` values that are not slug-safe or do not exist in `Series`
- missing `Series.primary_work_id`
- `Series.primary_work_id` values that do not resolve to a `Works` row
- `Series.primary_work_id` values whose `Works.series_ids` do not include that series
- `WorkDetails.work_id` values that do not resolve to `Works`

This preflight runs before generated files or workbook status/date updates are written, so those failures no longer appear after a partially written run.

## Runtime Canonical Data Flow

- `/series/` reads `assets/data/series_index.json` and `assets/data/moments_index.json` for the merged works and moments catalogue
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
