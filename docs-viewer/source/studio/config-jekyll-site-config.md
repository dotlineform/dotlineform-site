---
doc_id: config-jekyll-site-config
title: Jekyll Site Config
added_date: 2026-03-31
last_updated: 2026-06-12
parent_id: architecture
viewable: false
---
# Jekyll Site Config

Retired: `_config.yml` was removed during the static public-site build migration.

Config file:

- `_config.yml`

## Scope

`_config.yml` was the repo’s site-wide Jekyll config before the static public-site build migration.

Former responsibilities included:

- site identity and canonical URLs
- collection definitions and permalink structure
- default layouts
- public media and thumbnail origins used by Liquid templates
- selected shell/runtime flags such as `enable_details_hash_scroll`
- Jekyll build exclusions

Former exclusions included local operational and non-site inputs such as:

- `var`
- `logs`
- `studio/tests`
- mutable Studio activity and catalogue source/lookup data that local Studio reads through localhost services
- Docs Viewer local service files under `docs-viewer/bin/`, `docs-viewer/services/`, and `docs-viewer/shell/`
- Docs Viewer source/config inputs that are not browser-safe public route assets
- Docs Viewer local/manage-only runtime modules, HTML import modules, management CSS, report CSS, and the full local route registry; public Jekyll routes publish the public read-only runtime, basic viewer CSS, and `docs-viewer/config/routes/docs-viewer-public-routes.json`

## What calls it

Former direct readers:

- Jekyll itself during `bundle exec jekyll serve` and `bundle exec jekyll build`
- Liquid templates through `site.*` values such as:
  - `_layouts/work.html`
  - `_layouts/work_details.html`
  - `_layouts/moment.html`
  - `_layouts/series.html`
  - `_layouts/about.html`
  - `series/index.md`
  - `studio/analytics/series-tag-editor/index.md`
  - `_includes/work_index_item.html`
- `docs-viewer/build/build_docs.py`, which read `media_base` when resolving docs media tokens

Current public-site config lives in `public-site/config/public-site.json`. Current repo-root detection uses that file.

## When it is read

- no current runtime path should read `_config.yml`

## Current boundaries

Formerly here:

- public site URL and media-origin settings
- collection/permalink/default-layout behavior
- site-shell booleans used by Liquid-rendered pages

Still elsewhere:

- local filesystem roots and media-generation env var names
  those live in **[Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)**
- Studio/search browser text and JSON path settings
  those live in **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
- dedicated `/catalogue/search/` runtime policy
  that lives in **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**
