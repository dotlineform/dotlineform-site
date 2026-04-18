---
doc_id: studio-runtime
title: Studio Runtime
last_updated: 2026-04-17
parent_id: studio
sort_order: 10
---

# Studio Runtime

This document describes the current Studio route shell, shared runtime modules, and the way Studio pages connect into the scoped Docs Viewer.

## Route Shell

All Studio pages use:

- `layout: studio`
- `_layouts/studio.html`

The Studio layout is a thin shell. It renders:

- the page title
- the page body content
- an optional `i` link when `page.studio_page_doc` is present

That `i` link is the page-to-doc bridge for Studio. Each page now points to a scoped Docs Viewer URL in the form:

```text
/docs/?scope=studio&doc=<doc_id>
```

This keeps Studio implementation notes in the shared `/docs/` module rather than on page-local routes.

## Studio Pages

Current route inventory:

- `studio/index.md`
- `studio/build-activity/index.md`
- `studio/catalogue-new-work/index.md`
- `studio/catalogue-work/index.md`
- `studio/catalogue-new-work-detail/index.md`
- `studio/catalogue-work-detail/index.md`
- `studio/catalogue-series/index.md`
- `studio/catalogue-new-series/index.md`
- `studio/tag-groups/index.md`
- `studio/tag-registry/index.md`
- `studio/tag-aliases/index.md`
- `studio/series-tags/index.md`
- `studio/series-tag-editor/index.md`
- `studio/studio-works/index.md`

Current page-level doc links:

- Tag Groups -> `/docs/?scope=studio&doc=tag-groups`
- Build Activity -> `/docs/?scope=studio&doc=build-activity`
- Catalogue Work Editor -> `/docs/?scope=studio&doc=catalogue-work-editor`
- New Catalogue Work -> `/docs/?scope=studio&doc=catalogue-new-work-editor`
- Catalogue Work Detail Editor -> `/docs/?scope=studio&doc=catalogue-work-detail-editor`
- New Catalogue Work Detail -> `/docs/?scope=studio&doc=catalogue-new-work-detail-editor`
- Catalogue Series Editor -> `/docs/?scope=studio&doc=catalogue-series-editor`
- New Catalogue Series -> `/docs/?scope=studio&doc=catalogue-new-series-editor`
- Tag Registry -> `/docs/?scope=studio&doc=tag-registry`
- Tag Aliases -> `/docs/?scope=studio&doc=tag-aliases`
- Series Tags -> `/docs/?scope=studio&doc=series-tags`
- Series Tag Editor -> `/docs/?scope=studio&doc=tag-editor`
- Studio Works -> `/docs/?scope=studio&doc=studio-works`

## Shared Runtime Modules

Shared Studio runtime and wiring currently live in:

- `assets/studio/js/studio-config.js`
  loads `assets/studio/data/studio_config.json`, merges defaults, and resolves root-relative paths against the current site base path
- `assets/studio/js/studio-data.js`
  provides shared JSON loading and common shaping helpers for Studio pages
- `assets/studio/js/studio-transport.js`
  provides local-write endpoint definitions, health probing, and shared JSON POST transport

Current page controllers:

- `assets/studio/js/build-activity.js`
- `assets/studio/js/catalogue-new-work-editor.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-new-work-detail-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-new-series-editor.js`
- `assets/studio/js/tag-groups.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/studio-works.js`

Controller splits that are already live:

- Tag Editor:
  - `tag-studio.js`
  - `tag-studio-domain.js`
  - `tag-studio-save.js`
- Tag Registry:
  - `tag-registry.js`
  - `tag-registry-domain.js`
  - `tag-registry-save.js`
  - `tag-registry-service.js`
- Tag Aliases:
  - `tag-aliases.js`
  - `tag-aliases-domain.js`
  - `tag-aliases-save.js`
  - `tag-aliases-service.js`

## Relation to `/docs/`

Studio no longer owns a separate documentation route. Its docs are served by the shared Docs Viewer, which also serves other docs scopes.

Current Studio usage of the Docs Viewer:

- Studio section docs live in `_docs_src/`
- `scripts/build_docs.rb` builds the Studio docs payload into the Studio docs scope
- `/docs/?scope=studio&doc=<doc_id>` opens those docs in the shared Docs Viewer shell
- Studio page `i` links use those scoped URLs directly

This means Studio documentation changes must stay aligned with the shared Docs Viewer behavior documented in **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** and **[Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)**.

## Local Development Boundary

`bin/dev-studio` is the current Studio route runner.

What it starts:

- `bundle exec ruby scripts/build_docs.rb --write`
- `bundle exec jekyll serve --host 127.0.0.1 --port 4000`
- `scripts/studio/tag_write_server.py`

What it does not start:

- docs-search builders
- catalogue/search regeneration scripts
- any separate Studio-only frontend server

Current local generated Studio feed surfaced through this runtime:

- `assets/studio/data/build_activity.json`
- `assets/studio/data/catalogue_activity.json`

The runner is therefore sufficient for route-shell and write-flow testing, but not a full content-generation pipeline.
