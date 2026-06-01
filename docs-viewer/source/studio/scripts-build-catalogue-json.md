---
doc_id: scripts-build-catalogue-json
title: Scoped JSON Catalogue Build
added_date: 2026-04-18
last_updated: "2026-06-01"
parent_id: catalogue
---
# Scoped JSON Catalogue Build

Script:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001
```

This helper is the current JSON-source rebuild entrypoint for focused work, series, and moment scopes.

It also supports a focused moment scope used by the first Studio moments import page.
Scope planning rules for work, series, and moment builds live in `studio/services/catalogue/catalogue_build_scopes.py`; media readiness and local derivative work live in `studio/services/catalogue/catalogue_build_media.py`; field-aware build narrowing lives in `studio/services/catalogue/catalogue_build_field_plan.py`; generator/search command shapes and step result shaping live in `studio/services/catalogue/catalogue_build_commands.py`.
`studio/services/catalogue/catalogue_json_build.py` remains the supported CLI and Studio-callable orchestration entrypoint.

## Common Runs

Preview the scoped build:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001
```

Preview output includes local media counts for the scoped work/detail media plan.

Preview a field-aware work metadata scope:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --changed-fields duration
```

The registry path is resolved from `studio/app/frontend/config/studio-config.json` key `paths.data.studio.catalogue_field_registry`.

Field-aware preview output shows the selected planner mode, rule ids, artifact families, generator `--only` values, catalogue-search selection, and local-media selection. For example, a focused work metadata field can preview `work-json` only, while editor-only fields can produce no public build commands.

Run the scoped build:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --write
```

Refresh only local image derivatives for a work:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --media-only --force --write
```

Refresh only local image derivatives for one work detail:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --detail-uid 00001-003 --media-only --force --write
```

Preview catalogue-wide public thumbnail regeneration for works, work details, and moments:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --thumbnail-only --force
```

Regenerate only public thumbnails for all works, work details, and moments:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --thumbnail-only --force --write
```

Include an additional series when membership changed and the previous series page also needs rebuild:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00001 --extra-series-ids 004 --write
```

Preview a scoped series build:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --series-id 004
```

Run a scoped series build:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --series-id 004 --write
```

Preview a single moment import scope:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --moment-file keys.md
```

Run the moment import scope:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --moment-file keys.md --write
```

Refresh only local image derivatives for one moment:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --moment-file keys.md --media-only --force --write
```

## Current Behavior

The helper:

- reads canonical JSON source from `studio/data/canonical/catalogue/`
- optionally reads field-aware planning rules from the registry path exposed by `studio_config.json`
- resolves the current work record and its current published series ids
- unions any `--extra-series-ids`
- requires every series in the build scope to have `status: published`
- requires a series primary work to exist, belong to the series, and have `status: published`
- lets the generator render optional work and series prose from `studio/data/canonical/catalogue-markdown/works/<work_id>.md` and `studio/data/canonical/catalogue-markdown/series/<series_id>.md`
- stages in-scope source images under `var/catalogue/media/`
  - work source media resolves through `project_folder`, optional `project_subfolder`, and `project_filename`
  - work-detail source media resolves through the parent work's `project_folder`, optional detail `details_subfolder`, and detail `project_filename`
- generates local primary and thumbnail srcset derivatives under `var/catalogue/media/`
- copies generated thumbnail derivatives into `assets/works/img/` or `assets/work_details/img/`
- passes the generator's narrow `--refresh-published` mode so selected published records can be recomputed without forcing unchanged writes
- runs the internal `generate_work_pages.py` JSON engine with a narrow `--only` selection:
  - `work-pages`
  - `work-json`
  - `series-pages`
  - `series-index-json`
  - `works-index-json`
  - `recent-index-json`
- then runs `build_search.py --scope catalogue`

The extracted build modules own selection and validation rules, media planning/execution, field-aware narrowing, command construction, and step-result shaping. The entrypoint owns CLI option binding, preview text, command sequencing, subprocess execution, and the response payload shape used by Studio.

When `--changed-fields` is supplied, the `--only` selection, catalogue-search step, and local-media plan are narrowed by the matching registry target rule. The preview prints `Field-aware reasons` lines that group selected artifact families by the changed fields and registry reason. Unknown fields and mixed rule classes use conservative fallback and explain the fallback selection.

Planner behavior is covered by `$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py`.

For work scopes, `work-json` writes `assets/works/index/<work_id>.json` with the work record, rendered prose HTML when present, and published detail records grouped under `sections[]`. Each section carries `section_id`, `section_title`, optional `sort_order`, and `details[]`; nested detail records do not repeat section-level metadata.

For `--moment-file`, the helper:

- resolves moment metadata from `studio/data/canonical/catalogue/moments.json`
- resolves moment prose from `studio/data/canonical/catalogue-markdown/moments/<moment_id>.md`
- validates the moment filename, metadata, and required prose source
- stages the configured moment source image under `var/catalogue/media/moments/`
- generates local moment primary and thumbnail srcset derivatives under `var/catalogue/media/moments/`
- copies generated moment thumbnails into `assets/moments/img/`
- runs the internal `generate_work_pages.py` engine with `--only moments --moment-ids <moment_id> --refresh-published`
- then runs `build_search.py --scope catalogue`

Force behavior:

- normal scoped builds do not pass `--force`; unchanged generated payloads and aggregate indexes are skipped by content version
- `--force` remains available for intentional full rewrites, passes force through to catalogue search, and forces local media derivative regeneration
- already-published records do not get a refreshed `published_date` unless they transition from `draft` to `published`
- `--media-only` stops after source-image staging and local image derivative generation; it does not regenerate page/json payloads or catalogue search
- `--thumbnail-only` is catalogue-wide for works, work details, and moments, writes only public thumbnail assets, does not stage source media, does not generate primary derivatives, does not regenerate page/json payloads, and does not rebuild catalogue search
- missing or unresolved work, work-detail, or moment source images are reported as skipped records in `--thumbnail-only`; they do not fail the command

The helper does not:

- upload primary images to R2 or another remote media store
- rebuild unrelated works
- scan the moments folder for changes

## Local Image Outputs

Work, work-detail, and moment image generation uses the source-image metadata in canonical catalogue JSON:

- works resolve from `DOTLINEFORM_PROJECTS_BASE_DIR/projects/<project_folder>/<project_subfolder>/<project_filename>` when `project_subfolder` is present, otherwise directly from `<project_folder>/<project_filename>`
- work details resolve from the parent work `project_folder` plus optional `details_subfolder` and `project_filename`
- moments resolve from `DOTLINEFORM_PROJECTS_BASE_DIR/moments/images/<source_image_file>`
- local runs read `DOTLINEFORM_PROJECTS_BASE_DIR` from `var/local/site.env`; cloud runs can provide the same key through process environment configuration
- renamed source images are copied to `var/catalogue/media/works/make_srcset_images/<work_id>.<ext>`, `var/catalogue/media/work_details/make_srcset_images/<work_id>-<detail_id>.<ext>`, or `var/catalogue/media/moments/make_srcset_images/<moment_id>.<ext>`
- primary derivatives are staged under `var/catalogue/media/<kind>/srcset_images/primary/`
- thumbnail derivatives are generated temporarily under `var/catalogue/media/<kind>/srcset_images/thumb/`
- thumbnail derivatives are copied into the repo-owned public asset folders and then removed from staging:
  - `assets/works/img/`
  - `assets/work_details/img/`
  - `assets/moments/img/`

## Thumbnail-Only Regeneration

`--thumbnail-only` is a focused migration/maintenance mode for the public catalogue grid thumbnails. It scans all work, work-detail, and moment source records from canonical JSON, resolves source image paths with the same `DOTLINEFORM_PROJECTS_BASE_DIR` rules as local media generation, and writes only the configured thumbnail variants directly into:

- `assets/works/img/`
- `assets/work_details/img/`
- `assets/moments/img/`

This mode intentionally skips:

- source-image staging under `var/catalogue/media/`
- primary derivative generation
- page/json generation
- catalogue search rebuilds

Use `--force` when the thumbnail encoding policy changed and existing thumbnail mtimes still look current. Records with missing metadata or missing source files are listed as skipped so existing thumbnails for those records can remain in place.

The staged primary derivatives are the local handoff point for the remote media publishing step.
Use [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2) to preview or upload those primary derivatives after local generation.
Staged thumbnail derivatives are not retained after they have been copied into the public asset folders.

## Purpose

This is the command-path companion to Studio public-update actions on `/studio/catalogue-work/`, `/studio/catalogue-series/`, and `/studio/catalogue-moment/`. The Moment editor also contains the file-driven draft import panel, but that import path stays source-only until the draft is published.

Work and series scopes require published source records before runtime build/apply. Draft source saves remain source-only and are recovered through Catalogue Drafts rather than public rebuild paths.

It keeps the current source/public-update boundary narrow:

- source save remains separate from rebuild
- rebuild scope is explicit
- canonical source JSON stays the only write target for metadata edits

## Related References

- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
