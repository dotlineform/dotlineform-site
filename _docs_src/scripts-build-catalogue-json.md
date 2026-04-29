---
doc_id: scripts-build-catalogue-json
title: "Scoped JSON Catalogue Build"
added_date: 2026-04-18
last_updated: 2026-04-29
parent_id: scripts
sort_order: 70
---
# Scoped JSON Catalogue Build

Script:

```bash
./scripts/catalogue_json_build.py --work-id 00001
```

This helper is the Phase 5 JSON-source rebuild entrypoint for focused work, series, and moment scopes.

It also supports a focused moment scope used by the first Studio moments import page.

## Common Runs

Preview the scoped build:

```bash
./scripts/catalogue_json_build.py --work-id 00001
```

Preview output includes local media counts for the scoped work/detail media plan.

Run the scoped build:

```bash
./scripts/catalogue_json_build.py --work-id 00001 --write
```

Refresh only local image derivatives for a work:

```bash
./scripts/catalogue_json_build.py --work-id 00001 --media-only --force --write
```

Refresh only local image derivatives for one work detail:

```bash
./scripts/catalogue_json_build.py --work-id 00001 --detail-uid 00001-003 --media-only --force --write
```

Include an additional series when membership changed and the previous series page also needs rebuild:

```bash
./scripts/catalogue_json_build.py --work-id 00001 --extra-series-ids 004 --write
```

Preview a scoped series build:

```bash
./scripts/catalogue_json_build.py --series-id 004
```

Run a scoped series build:

```bash
./scripts/catalogue_json_build.py --series-id 004 --write
```

Preview a single moment import scope:

```bash
./scripts/catalogue_json_build.py --moment-file keys.md
```

Run the moment import scope:

```bash
./scripts/catalogue_json_build.py --moment-file keys.md --write
```

Refresh only local image derivatives for one moment:

```bash
./scripts/catalogue_json_build.py --moment-file keys.md --media-only --force --write
```

## Current Behavior

The helper:

- reads canonical JSON source from `assets/studio/data/catalogue/`
- resolves the current work record and its current published series ids
- unions any `--extra-series-ids`
- requires every series in the build scope to have `status: published`
- requires a series primary work to exist, belong to the series, and have `status: published`
- lets the generator render optional work and series prose from `_docs_src_catalogue/works/<work_id>.md` and `_docs_src_catalogue/series/<series_id>.md`
- stages in-scope work and work-detail source images under `var/catalogue/media/`
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
- then runs `build_search.rb --scope catalogue`

For `--moment-file`, the helper:

- resolves moment metadata from `assets/studio/data/catalogue/moments.json`
- resolves moment prose from `_docs_src_catalogue/moments/<moment_id>.md`
- validates the moment filename, metadata, and required prose source
- stages the configured moment source image under `var/catalogue/media/moments/`
- generates local moment primary and thumbnail srcset derivatives under `var/catalogue/media/moments/`
- copies generated moment thumbnails into `assets/moments/img/`
- runs the internal `generate_work_pages.py` engine with `--only moments --moment-ids <moment_id> --refresh-published`
- then runs `build_search.rb --scope catalogue`

Force behavior:

- normal scoped builds do not pass `--force`; unchanged generated payloads and aggregate indexes are skipped by content version
- `--force` remains available for intentional full rewrites, passes force through to catalogue search, and forces local media derivative regeneration
- already-published records do not get a refreshed `published_date` unless they transition from `draft` to `published`
- `--media-only` stops after source-image staging and local image derivative generation; it does not regenerate page/json payloads or catalogue search

The helper does not:

- upload primary images to R2 or another remote media store
- rebuild unrelated works
- scan the moments folder for changes

## Local Image Outputs

Work, work-detail, and moment image generation uses the source-image metadata in canonical catalogue JSON:

- works resolve from `DOTLINEFORM_PROJECTS_BASE_DIR/projects/<project_folder>/<project_filename>`
- work details resolve from the parent work project folder plus `<project_subfolder>/<project_filename>`
- moments resolve from `DOTLINEFORM_PROJECTS_BASE_DIR/moments/images/<source_image_file>`
- renamed source images are copied to `var/catalogue/media/works/make_srcset_images/<work_id>.<ext>`, `var/catalogue/media/work_details/make_srcset_images/<work_id>-<detail_id>.<ext>`, or `var/catalogue/media/moments/make_srcset_images/<moment_id>.<ext>`
- primary derivatives are staged under `var/catalogue/media/<kind>/srcset_images/primary/`
- thumbnail derivatives are staged under `var/catalogue/media/<kind>/srcset_images/thumb/`
- thumbnail derivatives are also copied into the repo-owned public asset folders:
  - `assets/works/img/`
  - `assets/work_details/img/`
  - `assets/moments/img/`

The staged primary derivatives are the local handoff point for the remote media publishing step. The scoped helper does not upload or mutate remote R2 media.

## Purpose

This is the command-path companion to the Studio `Save + Rebuild` action on `/studio/catalogue-work/`, `/studio/catalogue-series/`, `/studio/catalogue-moment/`, and the file-driven moments import flow on `/studio/catalogue-moment-import/`.

Work and series scopes require published source records before runtime build/apply. Draft source saves remain source-only and are recovered through Catalogue Status rather than public rebuild paths.

It keeps Phase 5 narrow:

- source save remains separate from rebuild
- rebuild scope is explicit
- canonical source JSON stays the only write target for metadata edits

## Related References

- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Build Activity](/docs/?scope=studio&doc=build-activity)
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
