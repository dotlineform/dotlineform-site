---
doc_id: config-studio-config-json
title: "Studio Config JSON"
added_date: 2026-04-24
last_updated: 2026-04-29
parent_id: config
sort_order: 30
---

# Studio Config JSON

Config file:

- `assets/studio/data/studio_config.json`

## Scope

`studio_config.json` is the shared browser-facing config payload for Studio pages and the dedicated public search page.

Current responsibilities include:

- route paths used by Studio and search UI
- JSON data paths used by Studio and search loaders
- shared Docs Viewer settings used by `/docs/` and `/library/`
- scope-specific Docs Viewer UI status emoji definitions
- the route and feed path for the current Studio build-activity page
- route and data paths for catalogue status, catalogue activity, project-state reporting, and catalogue editor pages
- catalogue UI options such as the Studio series-type dropdown values
- Studio analysis group and RAG settings
- Studio-owned UI text, including search-shell text that is shared through the same loader

## What calls it

This file is fetched through **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**.

Current direct consumers of that loader include:

- `assets/studio/js/tag-studio.js`
- `assets/studio/js/tag-studio-index.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/tag-groups.js`
- `assets/studio/js/studio-works.js`
- `assets/studio/js/build-activity.js`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/catalogue-activity.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/project-state.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/js/search/search-page.js`
- `assets/js/docs-viewer.js`

It also feeds shared path resolution used by:

- `assets/studio/js/studio-data.js`

## When it is read

- once per page load on Studio pages that call `loadStudioConfig()`
- once per page load on `/search/`, before the dedicated search page loads its policy and scope-owned search index
- then reused from the loader module’s cached promise for the rest of that page session

## Current boundaries

What stays here:

- route and data-path lookup used by browser-side modules
- shared Docs Viewer UI settings such as `docs_viewer.recently_added_limit`
- shared Docs Viewer status emoji config under `docs_viewer.ui_statuses_by_scope`
- catalogue UI option lists such as `catalogue.series_type_options`, currently used by the series editor as a client-side dropdown while the write server remains permissive
- shared Studio UI text
- shared Studio analysis policy used by current tag metrics/RAG helpers
- the lookup path for dedicated search policy and scope-owned search indexes

Retired Studio routes should not keep active route keys or UI text. For example, series create copy belongs under `ui_text.catalogue_series_editor` because create mode now lives at `/studio/catalogue-series/?mode=new`.

## Docs Viewer status emoji

`docs_viewer.ui_statuses_by_scope` defines the status values that the shared Docs Viewer may expose for each docs scope.

The current shape is:

```json
{
  "docs_viewer": {
    "ui_statuses_by_scope": {
      "studio": [
        {
          "ui_status": "done",
          "label": "Done",
          "emoji": "✅"
        }
      ],
      "library": [],
      "analysis": []
    }
  }
}
```

Contract:

- scope keys are docs-viewer scope ids such as `studio`, `library`, and `analysis`
- each scope value must be an array
- each status entry uses `ui_status`, `label`, and `emoji`
- `ui_status` is the stable front-matter value
- `label` is UI copy for controls and accessible labels
- `emoji` is the compact visual marker for index and status-pill UI
- malformed, duplicate, blank, or overlong entries are ignored by the viewer rather than treated as build failures

Related status-pill labels and save-state messages live under `ui_text.docs_viewer`, including:

- `status_pill_set_label`
- `status_pill_clear_label`
- `status_pill_readonly_label`
- `status_pill_saving`
- `status_pill_saved`
- `status_pill_failed`

The config is scope-aware even while the shared Docs Viewer continues to fetch `studio_config.json` as its single browser-facing config payload.

What does not stay here:

- the code that normalizes, caches, and exposes these values
  that lives in **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**
- Jekyll render-time design selections for static Studio pages such as landing-page panel background images
  those should live in Jekyll data files such as `_data/studio_panel_images.json`, because page templates can read `site.data` directly at build time
  that data may define a page-level default width plus per-panel width overrides, and should document the filename pattern used to derive each asset path
- dedicated `/search/` runtime policy values such as debounce and result batching
  those live in **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**
- local write-service endpoint URLs
  those currently live in `assets/studio/js/studio-transport.js`

For the Studio runtime that uses this config, see **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)**.
