---
doc_id: studio-runtime
title: "Studio Runtime"
added_date: 2026-04-24
last_updated: 2026-04-29
parent_id: studio
sort_order: 10
---

# Studio Runtime

This document describes the current Studio route shell, shared runtime modules, and the way Studio pages connect into the scoped Docs Viewer.

## Route Shell

All Studio pages use:

- `layout: studio`
- `_layouts/studio.html`

The Studio route shell now provides the shared admin-facing navigation model. On Studio and Studio Docs routes, `_layouts/default.html` switches the top header nav to:

- `Catalogue`
- `Library`
- `Analytics`
- `Search`
- `Docs`

The Studio page layout then renders:

- the page title
- the page body content
- an optional `i` link when `page.studio_page_doc` is present

The public site uses the user-facing `Works` / `Library` header nav. The only intended crossover points are:

- the site title at top left, which returns to the public site
- the footer `studio` link, which enters `/studio/`

Studio-originated Library viewer links open `/library/` with `mode=manage` so local management controls are available during admin workflows.

The `i` link is the page-to-doc bridge for Studio. Each page now points to a scoped Docs Viewer URL in the form:

```text
/docs/?scope=studio&doc=<doc_id>
```

This keeps Studio implementation notes in the shared `/docs/` module rather than on page-local routes.

## Studio Pages

Current route inventory:

- `studio/index.md`
- `studio/catalogue/index.md`
- `studio/library/index.md`
- `studio/analytics/index.md`
- `studio/search/index.md`
- `studio/catalogue-status/index.md`
- `studio/catalogue-activity/index.md`
- `studio/build-activity/index.md`
- `studio/docs-broken-links/index.md`
- `studio/docs-import/index.md`
- `studio/bulk-add-work/index.md`
- `studio/catalogue-moment/index.md`
- `studio/catalogue-moment-import/index.md` compatibility bridge to `/studio/catalogue-moment/`
- `studio/catalogue-work/index.md`
- `studio/catalogue-work-detail/index.md`
- `studio/catalogue-series/index.md`
- `studio/tag-groups/index.md`
- `studio/tag-registry/index.md`
- `studio/tag-aliases/index.md`
- `studio/series-tags/index.md`
- `studio/series-tag-editor/index.md`
- `studio/studio-works/index.md`

Current page-level doc links:

- Tag Groups -> `/docs/?scope=studio&doc=tag-groups`
- Build Activity -> `/docs/?scope=studio&doc=build-activity`
- Docs Broken Links -> `/docs/?scope=studio&doc=docs-broken-links`
- Docs HTML Import -> `/docs/?scope=studio&doc=user-guide-docs-html-import`
- Bulk Add Work -> `/docs/?scope=studio&doc=bulk-add-work`
- Catalogue Moment Editor -> `/docs/?scope=studio&doc=catalogue-moment-editor`
- Catalogue Moment Import -> `/docs/?scope=studio&doc=catalogue-moment-import` compatibility route note
- Catalogue Work Editor -> `/docs/?scope=studio&doc=catalogue-work-editor`
- Catalogue Work Detail Editor -> `/docs/?scope=studio&doc=catalogue-work-detail-editor`
- Catalogue Series Editor -> `/docs/?scope=studio&doc=catalogue-series-editor`
- Tag Registry -> `/docs/?scope=studio&doc=tag-registry`
- Tag Aliases -> `/docs/?scope=studio&doc=tag-aliases`
- Series Tags -> `/docs/?scope=studio&doc=series-tags`
- Series Tag Editor -> `/docs/?scope=studio&doc=tag-editor`
- Studio Works -> `/docs/?scope=studio&doc=studio-works`
- Studio landing and dashboards -> phased-plan and domain-plan docs
- Library Import -> `/docs/?scope=studio&doc=user-guide-docs-html-import`

## Shared Runtime Modules

Shared Studio runtime and wiring currently live in:

- `assets/studio/js/studio-config.js`
  loads `assets/studio/data/studio_config.json`, merges defaults, and resolves root-relative paths against the current site base path
- `assets/studio/js/studio-data.js`
  provides shared JSON loading and common shaping helpers for Studio pages
- `assets/studio/js/studio-transport.js`
  provides local-write endpoint definitions, health probing, and shared JSON POST transport
- `assets/studio/js/studio-dashboard.js`
  hydrates lightweight dashboard metrics for the new domain landing pages
- `assets/studio/js/docs-rebuild-button.js`
  wires the docs rebuild action beside the Studio docs search input
- `assets/studio/js/catalogue-work-fields.js`
  provides shared work-editor field metadata, id normalization, series parsing, draft shaping, and source-record payload helpers for work create/edit surfaces

Current page controllers:

- `assets/studio/js/build-activity.js`
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/js/bulk-add-work.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/catalogue-activity.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/tag-groups.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/studio-works.js`

Retired catalogue create routes:

- `/studio/catalogue-new-work/`, `/studio/catalogue-new-work-detail/`, and `/studio/catalogue-new-series/` are no longer published Studio pages.
- The old standalone controllers `assets/studio/js/catalogue-new-work-editor.js`, `assets/studio/js/catalogue-new-work-detail-editor.js`, and `assets/studio/js/catalogue-new-series-editor.js` have been removed.
- Active create behavior now lives in `assets/studio/js/catalogue-work-editor.js`, `assets/studio/js/catalogue-work-detail-editor.js`, and `assets/studio/js/catalogue-series-editor.js`.

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
- the Studio docs page uses the same top header nav and also renders a `Rebuild docs` action beside the docs search input

This means Studio documentation changes must stay aligned with the shared Docs Viewer behavior documented in **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** and **[Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)**.

## Local Development Boundary

`bin/dev-studio` is the current Studio route runner.

What it runs before starting long-lived services:

- required port preflight for Jekyll and the local write services
- optional docs/docs-search rebuilds for scopes listed in `DOCS_STARTUP_REBUILD_SCOPES`
- `./scripts/export_catalogue_lookup.py --write`

What it starts:

- `bundle exec jekyll serve --host 127.0.0.1 --port 4000`
- `scripts/studio/tag_write_server.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/docs/docs_management_server.py`
- `scripts/docs/docs_live_rebuild_watcher.py`

What it does not start:

- catalogue/search regeneration scripts
- any separate Studio-only frontend server

Current local generated Studio feed surfaced through this runtime:

- `assets/studio/data/build_activity.json`
- `assets/studio/data/catalogue_activity.json`

Current localhost docs-maintenance integration surfaced through this runtime:

- `POST /docs/broken-links`
- `POST /docs/rebuild`

The runner is therefore sufficient for route-shell and write-flow testing, but not a full content-generation pipeline.

## Current Catalogue UI Baseline

After Phase 3, the current Catalogue shell conventions are:

- Catalogue-domain pages no longer render a persistent page-link strip above the editor content
- work, series, and detail editors now use the right-hand summary rail for readiness state as well as current-record context
- work and detail editors now place compact media previews at the top of that summary rail
- work detail rows on the work editor now use thumbnail-led navigation rather than text-only rows
- the Catalogue dashboard uses grouped directional link lists rather than card panels
- metadata editors use a shared single-column row layout with labels on the left
- Catalogue Drafts is a sortable draft-record list and links directly into work, series, detail, and moment editors
- work-owned downloads and links are edited from the work editor rather than standalone child-record pages

After Phase 4, the current operational reporting conventions are:

- `Catalogue Activity` is the source-side activity surface for saves, creates, deletes, imports, and validation failures
- `Build Activity` is the rebuild/run surface for scoped and wider catalogue builds
- both pages now use sortable operational lists rather than expandable narrative cards
