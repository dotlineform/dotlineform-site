---
doc_id: config-pipeline-json
title: Pipeline Config JSON
added_date: 2026-03-31
last_updated: 2026-07-13
parent_id: studio
viewable: true
---
# Pipeline Config JSON

Config file:

- `_data/pipeline.json`

## Scope

`_data/pipeline.json` stores shared defaults for the current JSON-led catalogue workflow and the media/runtime surfaces that depend on the same variant and path conventions.

Current responsibilities include:

- env var names used by Python helpers
- the fixed `catalogue/media` workspace subpath beneath `DOTLINEFORM_PROJECTS_BASE_DIR`
- relative source-root and media-kind subpaths
- image variant widths, suffixes, and output subdirs
- encoding defaults

## What calls it

Current Python callers load it through `studio/shared/python/pipeline_config.py`:

- `studio/services/catalogue/generate_work_pages.py`
- `studio/services/catalogue/catalogue_build_media.py`
- `studio/services/media/make_srcset_images.py`
- `studio/services/media/publish_media_to_r2.py`
- `admin-app/checks/audit_site_consistency.py`

## When it is read

- at Python script startup when a script imports and loads shared pipeline config
- [anything else?]

## Current boundaries

What stays here:

- shared defaults that need to be available to scripts
- relative path policy for generated media and source roots
- `catalogue/media` is resolved by the shared external-workspace resolver and has no repo-local fallback
- image-variant policy that the current templates assume

## Current Thumbnail Policy

Public catalogue index thumbnails use a single configured thumbnail variant:

- size: `96`
- suffix: `thumb`
- format: `webp`
- quality: `62`

The public works, work-detail, and moments index grid layouts read this policy through `site.data.pipeline`, so they emit only the configured thumbnail candidate instead of allowing browsers to choose a larger `192w` thumbnail for retina displays. Catalogue-wide thumbnail regeneration is handled through:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --thumbnail-only --force --write
```
