---
doc_id: config-jekyll-site-config
title: "Jekyll Site Config"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: config
sort_order: 10
---

# Jekyll Site Config

Config file:

- `_config.yml`

## Scope

`_config.yml` is the repo’s site-wide Jekyll config.

Current responsibilities include:

- site identity and canonical URLs
- collection definitions and permalink structure
- default layouts
- public media and thumbnail origins used by Liquid templates
- selected shell/runtime flags such as `enable_details_hash_scroll`
- Jekyll build exclusions

## What calls it

Current direct readers:

- Jekyll itself during `bundle exec jekyll serve` and `bundle exec jekyll build`
- Liquid templates through `site.*` values such as:
  - `_layouts/work.html`
  - `_layouts/work_details.html`
  - `_layouts/moment.html`
  - `_layouts/series.html`
  - `_layouts/about.html`
  - `series/index.md`
  - `studio/series-tag-editor/index.md`
  - `_includes/work_index_item.html`
- `scripts/build_docs.rb`, which reads `media_base` when resolving docs media tokens

Some scripts also use `_config.yml` as a repo-root marker. In those cases they check for the file’s presence, but do not parse its fields.

## When it is read

- at Jekyll startup for site build and serve
- during template rendering whenever a page reads `site.*` values
- during docs-data builds when docs media URLs are normalized
- during some script startup flows when repo-root detection walks upward looking for `_config.yml`

## Current boundaries

What stays here:

- public site URL and media-origin settings
- collection/permalink/default-layout behavior
- site-shell booleans used by Liquid-rendered pages

What does not stay here:

- local filesystem roots and media-generation env var names
  those live in **[Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)**
- Studio/search browser text and JSON path settings
  those live in **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
- dedicated `/search/` runtime policy
  that lives in **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**
