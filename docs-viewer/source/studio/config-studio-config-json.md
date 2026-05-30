---
doc_id: config-studio-config-json
title: Studio Config JSON
added_date: 2026-04-24
last_updated: 2026-05-30
parent_id: config
viewable: true
---
# Studio Config JSON

Config file:

- `assets/studio/data/studio_config.json`

## Scope

`studio_config.json` is the shared browser-facing bootstrap manifest for Studio pages.
It is published into the local Studio runtime config; it is not a shared manifest for Analytics or public Docs Viewer scopes.

Current responsibilities include:

- route paths used by Studio UI
- JSON data paths used by Studio loaders
- shared Docs Viewer settings used by `/docs/` and `/library/`
- scope-specific Docs Viewer UI status emoji definitions
- the route and feed path for the current Studio activity page
- route and data paths for catalogue status, unified activity, project-state reporting, and catalogue editor pages
- scoped Studio UI-text bundle paths under `paths.data.ui_text`; Docs Viewer copy belongs to `docs-viewer/config/ui-text/ui-text.json`
- the Studio Audits route path and scoped UI-text bundle path
- catalogue UI options such as the Studio series-type dropdown values

The file is the root browser manifest.
It does not own visible UI text directly; Studio UI copy belongs in scoped payloads under `assets/studio/data/ui_text/`, while Docs Viewer copy belongs under `docs-viewer/config/ui-text/ui-text.json`.
Domain behavior should live with the domain runtime that uses the config.
Analytics app config now owns Analytics/Data Sharing route, UI-text, scoring, and endpoint paths.
For example, Analytics scoring code lives in `analytics-app/app/frontend/js/analysis-tag-scoring.js`; `studio_config.json` no longer supplies that runtime's policy values or `/analysis/` public route/search paths.

## What calls it

This file is fetched through **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**.

Current direct consumers of that loader include:

- `assets/studio/js/studio-works.js`
- `assets/studio/js/activity.js`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/activity.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/project-state.js`
- `assets/studio/js/studio-audits.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `docs-viewer/runtime/js/docs-viewer.js`

It also feeds shared path resolution used by:

- `assets/studio/js/studio-data.js`

Analytics/Data Sharing app config lives at `analytics-app/app/frontend/config/analytics-config.json`.
The active Data Sharing domain list and capability status come from `data-sharing/config/adapters.json`.
Per-domain export configs and import apply contracts still live in the owning workflow docs and service code.

## When it is read

- once per page load on Studio pages that call `loadStudioConfig()`
- then reused from the loader module’s cached promise for the rest of that page session

## Current boundaries

What stays here:

- route and data-path lookup used by browser-side modules
- shared Docs Viewer UI settings such as `docs_viewer.recently_added_limit`
- shared Docs Viewer status emoji config under `docs_viewer.ui_statuses_by_scope`
- catalogue UI option lists such as `catalogue.series_type_options`, currently used by the series editor as a client-side dropdown while the write server remains permissive
- lookup paths for scoped Studio UI-text payloads

Visible Studio UI copy must use scoped payloads under `assets/studio/data/ui_text/`.
Current bundles:

- `activity-log.json`
- `bulk-add-work.json`
- `catalogue-field-registry-review.json`
- `catalogue-work-editor.json`
- `catalogue-work-detail-editor.json`
- `catalogue-series-editor.json`
- `catalogue-moment-editor.json`
- `catalogue-status.json`
- `docs-viewer.json`
- `library-documents.json`
- `project-state.json`
- `site-series-index.json`
- `studio-audits.json`
- `studio-works.json`

Do not add domain workflows, service endpoint contracts, generated payload schemas, or scoring implementations to `studio_config.json`.
If a domain needs behavior, place that behavior in the owning runtime module and keep this file to paths, policy values, options, and scoped payload lookup.

## Data Sharing Pages

Data Sharing prepare/review pages no longer read `studio_config.json`.
They are owned by the standalone Local Analytics app and read `analytics-app/app/frontend/config/analytics-config.json`, route-scoped UI text under `analytics-app/app/frontend/config/ui-text/`, same-origin services under `/analytics/api/data-sharing/...`, and adapter config under `data-sharing/config/`.
Do not restore Data Sharing route keys, endpoint keys, or scoped UI-text paths to `studio_config.json`.
Returned-package parsing rules, sharing-profile matching, output formats, and source-write validation belong in the Data Sharing adapters and local service.

Retired Studio routes should not keep active route keys or UI text. For example, series create copy belongs in `assets/studio/data/ui_text/catalogue-series-editor.json` because create mode now lives at `/studio/catalogue-series/?mode=new`.

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

Related status-pill labels and save-state messages live in `docs-viewer/config/ui-text/ui-text.json`, loaded through `paths.data.ui_text.docs_viewer`, including:

- `draft_toggle_label`
- `draft_toggle_aria_label`
- `metadata_status_draft_option`
- `status_pill_set_label`
- `status_pill_clear_label`
- `status_pill_readonly_label`
- `status_pill_saving`
- `status_pill_saved`
- `status_pill_failed`

The status config is scope-aware, while the shared Docs Viewer now fetches its visible copy from the scoped Docs Viewer UI-text payload.

What does not stay here:

- the code that normalizes, caches, and exposes these values
  that lives in **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**
- Jekyll render-time design selections for static Studio pages such as landing-page panel background images
  those should live in Jekyll data files such as `_data/studio_panel_images.json`, because page templates can read `site.data` directly at build time
  that data may define a page-level default width plus per-panel width overrides, and should document the filename pattern used to derive each asset path
- dedicated `/search/` runtime policy values such as debounce and result batching
  those live in **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**
- dedicated `/search/` labels, messages, back links, and scope-owned index paths
  those also live in **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)** so public search can boot without the Studio manifest
- local write-service endpoint URLs
  those currently live in `assets/studio/js/studio-transport.js`

For the Studio runtime that uses this config, see **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)**.
