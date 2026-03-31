---
doc_id: config-pipeline-json
title: Pipeline Config JSON
last_updated: 2026-03-31
parent_id: config
sort_order: 20
---

# Pipeline Config JSON

Config file:

- `_data/pipeline.json`

## Scope

`_data/pipeline.json` stores shared defaults for the current [pipeline](/docs/?scope=studio&doc=scripts-main-pipeline) and the Liquid-rendered media/runtime surfaces that depend on the same variant and path conventions.

Current responsibilities include:

- env var names used by Python helpers
- relative source-root and media subpaths
- image variant widths, suffixes, and output subdirs
- encoding defaults

## What calls it

Current Python callers load it through `scripts/pipeline_config.py`:

- `scripts/generate_work_pages.py`
- `scripts/build_catalogue.py`
- `scripts/make_srcset_images.py`
- `scripts/copy_draft_media_files.py`
- `scripts/audit_site_consistency.py`

Current Jekyll/Liquid callers read it as `site.data.pipeline`:

- `_layouts/work.html`
- `_layouts/work_details.html`
- `_layouts/moment.html`
- `_layouts/series.html`
- `series/index.md`
- `studio/series-tag-editor/index.md`
- `_includes/work_index_item.html`

## When it is read

- at Python script startup when a script imports and loads shared pipeline config
- during Jekyll page rendering for layouts and includes that read `site.data.pipeline`

## Current boundaries

What stays here:

- shared defaults that need to be available to both scripts and Liquid templates
- relative path policy for generated media and source roots
- image-variant policy that the current templates assume

What does not stay here:

- absolute local machine paths
  those remain in environment variables referenced by this file
- public site/media origin URLs
  those stay in **[Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)**
- browser-side Studio/search path and text config
  those stay in **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
