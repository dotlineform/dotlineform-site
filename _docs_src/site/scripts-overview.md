---
doc_id: scripts-overview
title: Scripts Overview
last_updated: 2026-03-30
parent_id: site
sort_order: 20
---

# Scripts Overview

Use this command prefix for all script commands:

```bash
./
```

All commands below assume you are in `dotlineform-site/`.

For the centralized local install/setup guide, see [Local Setup](/docs/?doc=local-setup).

Docs viewer data:

```bash
./scripts/build_docs_data.rb --write
```

Use this after doc-source edits in `_docs_src/`.
`bin/dev-studio` also runs it once before starting Jekyll.

### Docs Viewer Data

Source location:

- `_docs_src/`

Published viewer route:

- `/docs/`

Generated outputs:

- `assets/data/docs/index.json`
- `assets/data/docs/by-id/<doc_id>.json`

What the builder does:

- reads Markdown source docs from `_docs_src/`
- reads front matter metadata such as `doc_id`, `title`, `last_updated`, `parent_id`, optional `sort_order`, and optional `published`
- renders each Markdown body to HTML using the local Jekyll Markdown stack
- rewrites doc-to-doc links onto the single viewer route
- writes one index payload plus one per-doc payload

Publishing rules:

- every `.md` file under `_docs_src/` is published by default
- add front matter with `published: false` to keep a Markdown file in `_docs_src/` without publishing it to `/docs/`
- if front matter is omitted, the builder falls back to:
  - `doc_id`: filename stem
  - `title`: first Markdown `#` heading, or a humanized filename

Common front matter fields:

- `doc_id`
  stable ID used by `/docs/?doc=<doc_id>`
- `title`
  label used in the viewer index and page title
- `last_updated`
  display metadata for the viewer
- `parent_id`
  empty string for a top-level doc
- `sort_order`
  optional integer for stable ordering inside the index tree
- `published`
  optional boolean; set `false` to exclude the file from published docs output

Internal doc links:

- preferred public link format: `/docs/?doc=<doc_id>`
- optional anchors should use the normal hash suffix: `/docs/?doc=<doc_id>#section-anchor`
- this is the recommended authoring format because it does not depend on `_docs_src/` folder layout
- the builder still rewrites legacy `/docs/.../` links and relative `.md` links, but treat that as compatibility behavior rather than the preferred convention

Default command:

```bash
./scripts/build_docs_data.rb --write
```

Dry run:

```bash
./scripts/build_docs_data.rb
```

Flags:

- `--source PATH`
  docs source directory
  default: `_docs_src`
- `--output PATH`
  output directory for generated JSON payloads
  default: `assets/data/docs`
- `--viewer-base-url URL`
  viewer route base used when generating `viewer_url` values and rewritten internal doc links
  default: `/docs/`
- `--write`
  persist generated files; if omitted, the script prints a dry-run summary only

Notes:

- `bin/dev-studio` runs this builder once before starting Jekyll
- if you edit `_docs_src/` while the dev runner is already running, re-run `./scripts/build_docs_data.rb --write`
- changing only the docs data does not require any separate asset pipeline

Jekyll verification builds:

- if `jekyll serve` or `bin/dev-studio` is already running, avoid building into the default `_site/` destination at the same time
- concurrent writes to the same `_site/` tree can produce transient static-file copy failures even when the source asset is valid
- for a one-off verification build while the dev server is active, use a separate destination:

```bash
bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build
```

Local environment variables (required for media/generation scripts):

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/path/to/dotlineform"
export DOTLINEFORM_MEDIA_BASE_DIR="/path/to/dotlineform-icloud"
```

Pipeline policy config:

- Shared pipeline defaults live in `_data/pipeline.json`.
- That config stores env var names and relative media subpaths.
- The default env var names remain `DOTLINEFORM_PROJECTS_BASE_DIR`, `DOTLINEFORM_MEDIA_BASE_DIR`, and `MAKE_SRCSET_JOBS`.
- Srcset manifest env var names also live there; defaults remain `MAKE_SRCSET_WORK_IDS_FILE` and `MAKE_SRCSET_SUCCESS_IDS_FILE`.
- CLI flags still override config-derived defaults.

Sorting behavior and consistency contract:

- [Sorting Architecture](/docs/?doc=sorting-architecture)

Deferred improvements and follow-up items:

- [CSS Audit Spec](/docs/?doc=css-audit-spec)
- [CSS Audit Latest](/docs/?doc=css-audit-latest)

## Main Pipeline

Run everything (copy -> srcset -> page generation):

```bash
./scripts/run_draft_pipeline.py --dry-run
./scripts/run_draft_pipeline.py
```

Useful flags:

- `--dry-run`: preview only (no workbook writes/deletes)
- `--force-generate`: pass `--force` through to `generate_work_pages.py`
- `--jobs N`: srcset parallel jobs (default: `4`, or `MAKE_SRCSET_JOBS` env var)
- `--mode work|work_details|moment`: run only selected flow(s). Repeat flag to run multiple.
- `--work-ids`, `--work-ids-file`: limit work + work_details scope
- `--series-ids`, `--series-ids-file`: pass series scope to generation
- `--moment-ids`, `--moment-ids-file`: limit moment scope
- `--xlsx PATH`: workbook path override
- `--input-dir`, `--output-dir`: works source/derivative dirs
- `--detail-input-dir`, `--detail-output-dir`: work_details source/derivative dirs
- `--moment-input-dir`, `--moment-output-dir`: moments source/derivative dirs

Mode examples:

```bash
./scripts/run_draft_pipeline.py --mode moment --dry-run
./scripts/run_draft_pipeline.py --mode work --mode work_details --dry-run
./scripts/run_draft_pipeline.py --mode moment --moment-ids blue-sky,compiled --dry-run
./scripts/run_draft_pipeline.py --mode work --work-ids 00456 --dry-run
```

Note: when `--mode work` is used and no `--series-ids*` are provided, draft series are auto-included in generation.

## Individual Scripts

### 1) Copy draft source images from workbook

Unified script with mode flags:

```bash
./scripts/copy_draft_media_files.py --mode work --ids-file /tmp/work_ids.txt --copied-ids-file /tmp/copied_work_ids.txt --write
./scripts/copy_draft_media_files.py --mode work_details --ids-file /tmp/detail_uids.txt --copied-ids-file /tmp/copied_detail_uids.txt --write
./scripts/copy_draft_media_files.py --mode moment --ids-file /tmp/moment_ids.txt --copied-ids-file /tmp/copied_moment_ids.txt --write
```

Flags:

- `--mode work|work_details|moment`
- `--ids-file`: optional filter manifest (one ID per line)
- `--copied-ids-file`: optional output manifest of successfully copied IDs
- `--write`: perform copy (omit for dry-run)
- `--keep-ext` / `--no-ext`: keep/remove source extension in copied filename

### 2) Build srcset derivatives

The stable shell entrypoint remains `scripts/make_srcset_images.sh`, but it now delegates to the shared config-driven Python implementation.

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_work_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/work_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/srcset_images" \
  4
```

Moments example:

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_moment_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/moment_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/srcset_images" \
  4
```

Moment source discovery uses the configured moments images directory plus a fixed source filename of `<moment_id>.jpg`.
If that source file is missing, the copy step skips it.

### 3) Generate Jekyll pages from workbook

```bash
./scripts/generate_work_pages.py
./scripts/generate_work_pages.py --write
```

Common scoped runs:

```bash
./scripts/generate_work_pages.py --work-ids 00456 --write
./scripts/generate_work_pages.py --work-ids-file /tmp/work_ids.txt --write
./scripts/generate_work_pages.py --series-ids curve-poems,dots --write
./scripts/generate_work_pages.py --only moments --moment-ids blue-sky --write
./scripts/generate_work_pages.py --only search-index-json --write
```

Useful flags:

- `--write`: persist file/workbook changes
- `--force`: regenerate even when checksums match
- `--work-ids`, `--work-ids-file`
- `--series-ids`, `--series-ids-file`
- `--moment-ids`, `--moment-ids-file`
- `--work-files-sheet` (default `WorkFiles`)
- `--work-links-sheet` (default `WorkLinks`)
- `--moments-sheet` (default `Moments`)
- `--moments-output-dir` (default `_moments`)
- `--moments-json-dir` (default `assets/moments/index`)
  - writes per-moment JSON payloads at `assets/moments/index/<moment_id>.json`
  - renders canonical moment prose from `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md` using the local Jekyll markdown stack
  - generated together with `_moments/<moment_id>.md` when `moments` is selected
  - JSON is now the canonical source for moment date/image/prose content at runtime
  - generated `_moments/<moment_id>.md` files are minimal stubs with `moment_id`, `title`, `layout`, and `checksum`
- `--moments-index-json-path` (default `assets/data/moments_index.json`)
  - writes a lightweight moments index object keyed by `moment_id`
  - used by `/moments/` for title/date/thumb metadata
  - rebuilt on every pipeline run as a full index and not scoped by `--moment-ids`
- work prose source path:
  - canonical markdown lives at `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<project_folder>/<paths.source_subdirs.prose>/<work_prose_file>`
  - default `paths.source_subdirs.prose` value is `site text`
  - if `Works.work_prose_file` is empty or the resolved markdown file is missing, the pipeline warns and skips that work
- `--projects-base-dir`: base path used for source-image dimension reads
  - default is taken from `DOTLINEFORM_PROJECTS_BASE_DIR`
  - used for canonical work prose source files, work detail and work file sources, moment source files, and series prose source files
  - work primary image dimension refresh only runs when `work-json` is selected directly or indirectly via `work-pages`
  - when source files are found, `Works.width_px`/`height_px` and detail/moment dimension columns are refreshed on `--write`
- `--media-base-dir`: base path used for staged media outputs
  - default is taken from `DOTLINEFORM_MEDIA_BASE_DIR`
  - `work-files` stages downloadable files to `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/`
- `--series-index-json-path` (default `assets/data/series_index.json`)
- `--search-index-json-path` (default `assets/data/search/catalogue/index.json`)
  - writes a flat search artifact spanning works, series, and moments
  - used first by `/search/?scope=catalogue`
  - rebuilt on every pipeline run as a full index and not scoped by `--work-ids`, `--series-ids`, or `--moment-ids`
- `--series-json-dir` (default `assets/series/index`)
  - writes per-series JSON payloads at `assets/series/index/<series_id>.json`
  - resolves canonical series prose from `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<primary_work_project_folder>/<paths.source_subdirs.prose>/<series_prose_file>`
  - `primary_work_project_folder` is derived from `Series.primary_work_id -> Works.project_folder`
  - generated together with `_series/<series_id>.md` when `series-pages` is selected
  - if `Series.series_prose_file` is empty, the JSON payload is still generated without `content_html`
  - if `Series.series_prose_file` is populated but the resolved markdown file is missing, the pipeline warns and omits `content_html`
- `--works-index-json-path` (default `assets/data/works_index.json`)
- `--only`: limit generation to selected artifacts
  - aggregate index JSON artifacts for `series`, `works`, `search`, and `moments` are always rebuilt on every run, regardless of `--only`
  - allowed: `work-pages`, `work-files`, `work-links`, `series-pages`, `series-index-json`, `work-details-pages`, `work-json`, `works-index-json`, `search-index-json`, `moments`, `moments-index-json`
  - there is no separate `works-prose` artifact; use `work-json` for prose-only refreshes
  - `work-pages`: writes `_works/<work_id>.md` as lightweight stubs (`work_id`, `title`, `layout`, `checksum`)
    - selecting `work-pages` also rebuilds the per-work JSON payload because runtime prose now depends on it
  - `work-files`: stages `WorkFiles` rows for in-scope works into `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/` and updates `WorkFiles.status` / `published_date` on `--write`
  - `work-links`: updates `WorkLinks.status` / `published_date` for in-scope works on `--write`
  - `series-pages`: writes `_series/<series_id>.md` as lightweight stubs (`series_id`, `title`, `layout`, `checksum`) and `assets/series/index/<series_id>.json`
    - per-series JSON stores full public `series` metadata plus rendered `content_html`
    - renders canonical series prose from the external projects tree using the local Jekyll markdown stack when `Series.series_prose_file` is populated
    - if `Series.series_prose_file` is blank, the series JSON is still written and the runtime prose section stays hidden
  - `work-details-pages`: writes `_work_details/<detail_uid>.md` as lightweight stubs (`work_id`, `detail_id`, `detail_uid`, `title`)
  - `moments`: writes both `_moments/<moment_id>.md` stubs and `assets/moments/index/<moment_id>.json`
    - stub front matter keeps only `moment_id`, `title`, `layout`, and a checksum derived from canonical moment metadata
    - JSON stores the canonical moment metadata (`title`, `date`, `date_display`, `images`, `width_px`, `height_px`) plus rendered `content_html`
  - `moments-index-json`: writes `assets/data/moments_index.json` as a lightweight object keyed by `moment_id`
    - each moment stores lightweight card metadata only (`title`, `date`, `date_display`, `thumb_id`)
    - always rebuilt as a full index (not scoped by `--moment-ids` and not gated by `--only`)
  - `series-index-json`: writes `assets/data/series_index.json` (full rebuild) with:
    - header: `schema`, deterministic content `version`, `generated_at_utc`, `count`
    - series map keyed by `series_id`
    - full series metadata used by generated series pages (`layout`, `status`, `published_date`, `title`, `sort_fields`, `series_type`, `year`, `year_display`, `primary_work_id`, `notes`, `project_folders`)
    - optional empty fields are omitted from JSON rather than written as `null`
    - ordered `works` (in canonical series sort order derived from `sort_fields`)
    - always rebuilt as a full index and not gated by `--only`
  - `works-index-json`: writes `assets/data/works_index.json` as a lightweight object keyed by `work_id`
    - each work stores canonical `series_ids` only; series membership is derived from that ordered array
    - optional empty fields are omitted from JSON rather than written as `null`
    - always rebuilt as a full index and not gated by `--only`
    - runtime thumb paths are derived from `work_id`, so no media/thumb payload is persisted here
    - rebuilding this index alone does not probe work source images; it uses the current workbook metadata
    - always rebuilt as a full index (not scoped by `--work-ids`)
  - `search-index-json`: writes `assets/data/search/catalogue/index.json` as a flat array of catalogue search entries
    - entries span `work`, `series`, and `moment`
    - each entry includes canonical `id`, title, route href, compact display metadata, and build-time normalized `search_terms` / `search_text`
    - work entries also include compact metadata such as `series_titles`, `medium_type`, and `storage`
    - tag-derived fields are carried for future ranking/filter expansion, but sparse tag coverage means they are not yet the primary ranking signal
    - always rebuilt as a full index and not gated by `--only`
  - `work-json`: writes `assets/works/index/<work_id>.json` with `header` (`schema`, deterministic content `version`, `generated_at_utc`, `work_id`, `count`), full `work`, full `sections[].details[]`, and rendered `content_html`
    - `work.series_ids` preserves the full ordered membership list from the workbook
    - optional empty fields are omitted from JSON rather than written as `null`
    - work-page primary-series label/link is derived at runtime from `series_index.json`, using `work.series_ids[0]`
    - work-driven: emits one file per selected work_id (uses `sections: []` when a work has no details)
    - renders canonical work prose from the external projects tree using the local Jekyll markdown stack
    - this is the prose-only refresh path for works when `_works/*.md` stubs do not need to change

Runtime canonical data flow:

- `/series/` reads `assets/data/series_index.json` and `assets/data/moments_index.json` for the merged works/moments catalogue.
- `/series/<series_id>/` reads `assets/data/series_index.json`.
- `/series/<series_id>/` also reads `assets/data/works_index.json` for card metadata.
- `/series/<series_id>/` reads `assets/series/index/<series_id>.json` for series prose HTML.
- `/works/<work_id>/` reads `assets/works/index/<work_id>.json` for metadata, prose HTML, and detail sections; series nav/counter/link visibility also read `assets/data/series_index.json`.
- `/work_details/<detail_uid>/` reads stub front matter for `work_id` and then fetches `assets/works/index/<work_id>.json`.
- `/moments/<moment_id>/` reads `assets/moments/index/<moment_id>.json`.
- `/search/` reads `assets/data/search/catalogue/index.json`.

### 3a) Delete a single work from generated artifacts

Run:

```bash
./scripts/delete_work.py --work-id 00123
./scripts/delete_work.py --work-id 00123 --write
```

Behavior:

- dry-run by default; pass `--write` to apply changes
- requires exactly one `--work-id`
- only proceeds when `data/works.xlsx` worksheet `Works` has `status=delete` for that work
- on successful `--write`, updates `Works.status` to `deleted`
- deletes:
  - `_works/<work_id>.md`
  - `_work_details/<work_id>-*.md`
  - `assets/works/index/<work_id>.json`
  - removes the work from `assets/data/series_index.json`
  - removes the work from `assets/data/works_index.json`
  - removes per-work overrides from `assets/studio/data/tag_assignments.json`
- if a deleted work is referenced by a series `primary_work_id`, that field is set to `null`
- intentionally leaves these untouched:
  - `assets/work_details/img/*`
  - canonical work prose under `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<project_folder>/<paths.source_subdirs.prose>/<work_prose_file>`
  - staged media under `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/<work_id>-*`

Backups:

- `--write` creates timestamped backups under `var/delete_work/backups/YYYYMMDD-HHMMSS/`
- backups preserve repo-relative paths for modified/deleted files so they can be restored manually if needed

### 3b) Tag Studio local save server

Run:

```bash
./scripts/studio/tag_write_server.py
```

Optional flags:

- `--port 8787`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection (`_config.yml` parent search)
- `--dry-run`: validate and return response without writing files

Behavior:

- Exposes:
  - `GET /health`
  - `POST /save-tags`
  - `POST /import-tag-registry`
  - `POST /import-tag-aliases`
  - `POST /delete-tag-alias`
  - `POST /mutate-tag-alias-preview`
  - `POST /mutate-tag-alias`
  - `POST /promote-tag-alias-preview`
  - `POST /promote-tag-alias`
  - `POST /import-tag-assignments-preview`
  - `POST /import-tag-assignments`
  - `POST /demote-tag-preview`
  - `POST /demote-tag`
  - `POST /mutate-tag-preview`
  - `POST /mutate-tag`
  - Tag Studio page probes `/health` and shows:
  - `Save mode: Local server` when available
  - `Save mode: Offline session` when unavailable or when a staged local row already exists for the current series
  - `POST /save-tags` expects assignment objects in `tags`:
    - series save payload: `{ "series_id": "<series>", "tags": [...] }`
    - work override save payload: `{ "series_id": "<series>", "work_id": "<work_id>", "keep_work": true|false, "tags": [...] }`
    - `{ "tag_id": "<group>:<slug>", "w_manual": 0.3|0.6|0.9, "alias"?: "<alias>" }`
    - `alias` is optional historical data only; it records that the tag was chosen from an alias match and is not treated as canonical
  - save writes `assets/studio/data/tag_assignments.json` with object-only tag rows (no string tags)
  - save is diff-based in the Series Tag Editor: the UI compares current series/work state against the last loaded/saved baseline and sends one `/save-tags` request for the series row when needed plus one request per changed work row
  - when multiple work pills are selected in the Series Tag Editor, the active work's current override set is used as the persisted state for all selected work pills
  - work override saves strip tags already inherited from `series[*].tags`
  - `keep_work: false` plus empty tags deletes `series[*].works[work_id]`
  - `keep_work: true` allows an explicit work row with `tags: []`
  - offline-session staging stores full normalized series rows in browser `localStorage`, including optional historical `alias`
  - Series Tags page can export that session as JSON or preview/apply it through the local server
  - assignment import preview/apply compares full normalized rows, including `alias`, and resolves conflicts per series via `overwrite` or `skip`
- Tag Registry page probes `/health` and shows:
  - `Import mode: Local server` when available
  - `Import mode: Patch` when unavailable (fallback to manual patch copy)
  - tag edit/delete requires local server mode
  - `New tag` button opens create modal:
    - group selected via group pills; slug + optional description entry
    - live duplicate check blocks existing `<group>:<slug>`
    - local mode uses `POST /import-tag-registry` with `mode: add` and a single tag payload
    - patch mode emits add-tag row snippet
- Import modes supported by endpoint:
  - `add` (no overwrite)
  - `merge` (add + overwrite)
  - `replace` (replace entire registry)
  - successful import responses include `summary_text` (same format used by Tag Registry UI and server log)
  - import request may include `import_filename`; server logs basename only (no client path)
  - tag mutation endpoint behavior (`POST /mutate-tag`):
    - `action: edit`: update canonical tag `description` (tag id/name remains fixed in UI flow)
    - `action: delete`: remove tag
    - delete cascades update `tag_assignments.json` and `tag_aliases.json`
    - aliases that become 1:1 self-maps (`alias == target slug`) are removed automatically
  - preview endpoint (`POST /mutate-tag-preview`) returns the same impact stats without writing files
  - tag demotion behavior:
    - trigger via tag pill `<-` action in registry list
    - preview via `POST /demote-tag-preview` is required before confirm
    - apply via `POST /demote-tag`
    - demotion removes canonical tag from registry, creates alias (`<slug>` -> chosen canonical targets), and rewrites assignments/alias target refs
    - patch fallback emits ordered manual steps only
- Tag Aliases page probes `/health` and shows:
  - `Import mode: Local server` when available
  - `Import mode: Patch` when unavailable (fallback to manual patch copy)
  - alias pill `×` delete:
    - local mode uses `POST /delete-tag-alias`
    - patch mode generates manual snippet with `aliases_to_remove`
  - alias text click opens edit modal:
    - live alias-name uniqueness validation
    - editable description + selected tags
    - selected tags must be canonical and satisfy: max 4 tags, max 1 per group
    - local mode uses `POST /mutate-tag-alias`
    - patch mode emits ordered `set_alias`/`remove_alias_key` steps
  - `New alias` button opens create modal:
    - same alias/tag validation and tag-picker behavior as edit modal
    - local mode uses `POST /import-tag-aliases` with `mode: add` and a single alias payload
    - patch mode emits add-alias fragment snippet
  - alias pill `→` promote:
    - user chooses target group at action time
    - preview via `POST /promote-tag-alias-preview` is required before confirm
    - apply via `POST /promote-tag-alias`
    - canonical tag id is `<group>:<alias-slug>`; label auto-derived from slug
    - if canonical already exists, alias key is removed only
    - patch fallback emits ordered manual steps only
  - Import modes supported by endpoint:
    - `add` (no overwrite)
    - `merge` (add + overwrite)
    - `replace` (replace entire aliases)
  - successful import responses include `summary_text` and `import_filename` (basename only)

Security constraints:

- Binds to loopback interface only (local machine only)
- CORS allows loopback origins only
- Write target is allowlisted to these files only:
  - `assets/studio/data/tag_assignments.json`
  - `assets/studio/data/tag_registry.json`
  - `assets/studio/data/tag_aliases.json`
  - timestamped backups are created in `var/studio/backups/`:
    - `tag_assignments.json.bak-YYYYMMDD-HHMMSS`
    - `tag_registry.json.bak-YYYYMMDD-HHMMSS`
    - `tag_aliases.json.bak-YYYYMMDD-HHMMSS`

Script logging:

- Per-script logs are written to repo-root log directories (auto-created).
- Current pipeline/logged scripts include:
  - `scripts/run_draft_pipeline.py` -> `logs/run_draft_pipeline.log`
  - `scripts/generate_work_pages.py` -> `logs/generate_work_pages.log`
  - `scripts/delete_work.py` -> `logs/delete_work.log`
  - `scripts/studio/tag_write_server.py` -> `var/studio/logs/tag_write_server.log`
- Log format is JSON Lines (one JSON object per line).
- Retention policy:
  - keep entries from the last 30 days
  - if no entries fall inside the last 30 days, keep the latest 1 day's worth (based on newest entry)

### 3c) CSS token audit

Run:

```bash
./scripts/css_token_audit.py
```

Optional flags:

- `--md-out _docs_src/css-audit-latest.md`: override Markdown output path
- `assets/css/main.css assets/studio/css/studio.css`: optional file list override

Behavior:

- scans CSS for `font-size` declarations and color literals
- reports repeated raw typography values and direct color literals
- writes the current snapshot to `_docs_src/css-audit-latest.md`

### 4) Audit site consistency (read-only)

Run an audit across generated pages and JSON:

```bash
./scripts/audit_site_consistency.py --strict
```

Scope and output options:

```bash
./scripts/audit_site_consistency.py \
  --checks cross_refs,schema,json_schema,links,media,orphans \
  --series-ids collected-1989-1998 \
  --json-out /tmp/site-audit.json \
  --md-out _docs_src/audit-latest.md \
  --strict
```

Run a single check with the convenience alias:

```bash
./scripts/audit_site_consistency.py \
  --check-only schema \
  --max-samples 10
```

Or run multiple checks with repeated `--check-only`:

```bash
./scripts/audit_site_consistency.py \
  --check-only cross_refs \
  --check-only json_schema \
  --series-ids collected-1989-1998
```

Current checks:

- `cross_refs`: validates key references across `_works`, `_series`, `_work_details`, `assets/data/series_index.json`, and `assets/works/index/*.json` (including duplicate IDs)
- `schema`: validates required front matter fields by collection and format/consistency checks (`work_id`, `detail_uid`, slug-safe IDs, `sort_fields` token rules with `work_id` last sourced from canonical `series_index.json` with `_series` fallback, optional `_works.series_id` slug format, and `detail_uid` prefix matching `work_id`)
- `json_schema`: validates generated JSON structure/count consistency for:
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/works/index/*.json`
- `links`: validates sitemap source/URL targets and query-parameter contract sanity across generated pages
- `media`: validates expected local thumbs for published `_works` and `_work_details` (primaries and download files are treated as remote/staged and are not asserted locally)
- `orphans`: reports orphan pages/JSON; optionally include orphan media files with `--orphans-media`

`--strict` behavior and value:

- `--strict` exits non-zero when audit errors are found (`errors > 0`), so scripts/CI can fail fast.
- Warnings do not fail the run under `--strict`.
- Without `--strict`, the audit is informational and exits zero.

Query contract map used by `links` check:

| flow | produced query keys | destination accepts |
| --- | --- | --- |
| `series -> work` | `series`, `series_page` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |
| `works index -> work` | `from`, `return_sort`, `return_dir`, `return_series` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |
| `work -> work_details index` | `from_work`, `from_work_title`, `section`, `section_label`, `series`, `series_page` | `sort`, `dir`, `from_work`, `from_work_title`, `section`, `section_label`, `series`, `series_page` |
| `work -> work_details page` | `from_work`, `from_work_title`, `section`, `details_section`, `details_page`, `series`, `series_page` | `from_work`, `from_work_title`, `section`, `series`, `series_page`, `details_section`, `details_page`, `section_label` |
| `work_details page -> work` | `series`, `series_page`, `details_section`, `details_page` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |

Orphan media scan (optional):

```bash
./scripts/audit_site_consistency.py \
  --check-only orphans \
  --orphans-media
```

Markdown report is written by default to `_docs_src/audit-latest.md` (overwrites each run).

To write to a different path:

```bash
./scripts/audit_site_consistency.py \
  --md-out /tmp/site-audit.md
```

Known limits:

- `media` assumes primaries and work download files are remote/staged and checks local thumbs only.
- `json_schema` validates structure/counts, not recomputed payload hash integrity.
- `links` query-contract checks are static sanity checks; they do not execute browser flows.
- Orphan checks currently focus on works/series/work_details artifacts.

Warning policy:

- Treat schema warnings as backlog by default.

### 5) Legacy autofix for numeric `title_sort` on works front matter

Generated site JSON no longer persists `title_sort`. This helper remains only for older or hand-authored `_works` front matter that still uses that field.

Dry-run:

```bash
./scripts/fix_missing_title_sort.py
```

Write changes:

```bash
./scripts/fix_missing_title_sort.py --write
```

Scope to selected IDs/ranges:

```bash
./scripts/fix_missing_title_sort.py \
  --work-ids 66-74,38,40 \
  --write
```

### Works download files

If `WorkFiles` contains rows for a work, generation stages those files and exposes them as `work.downloads` in per-work JSON.

- Source path:
  - `[projects-base-dir]/projects/[project_folder]/[filename]`
- Destination path:
  - `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/[work_id]-[url-safe-filename.ext]`
  - staged filenames preserve the extension and normalize the basename for URLs (for example spaces become `-`)
- Work page link:
  - Label: `download` or `downloads`
  - Link text: `WorkFiles.label`
  - Rendered before `cat. <work_id>`

### Works published links

If `WorkLinks` contains rows for a work, generation exposes them as `work.links` in per-work JSON.

- Source fields:
  - `WorkLinks.URL`
  - `WorkLinks.label`
- Work page row:
  - Caption stays `published on`
  - Links render as a comma-delimited list using `WorkLinks.label`
