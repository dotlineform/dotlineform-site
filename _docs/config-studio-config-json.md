---
doc_id: config-studio-config-json
title: Studio Config JSON
added_date: 2026-04-24
last_updated: "2026-05-10 19:05"
parent_id: studio
sort_order: 90
---
# Studio Config JSON

Config file:

- `assets/studio/data/studio_config.json`

## Scope

`studio_config.json` is the shared browser-facing bootstrap manifest for Studio pages.

Current responsibilities include:

- route paths used by Studio UI
- JSON data paths used by Studio loaders
- shared Docs Viewer settings used by `/docs/` and `/library/`
- scope-specific Docs Viewer UI status emoji definitions
- the route and feed path for the current Studio activity page
- route and data paths for catalogue status, unified activity, project-state reporting, and catalogue editor pages
- route and data paths for the shared Studio data export/import pages
- scoped UI-text bundle paths under `paths.data.ui_text`
- the Studio Audits route path and scoped UI-text bundle path
- catalogue UI options such as the Studio series-type dropdown values
- Studio analysis group and RAG settings

The file is the root browser manifest.
It does not own visible UI text directly; Studio UI copy belongs in scoped payloads under `assets/studio/data/ui_text/`.
Domain behavior should live with the domain runtime that uses the config.
For example, Studio analysis scoring code lives in `assets/studio/js/analysis-tag-scoring.js`; `studio_config.json` only supplies the current scoring policy values.

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
- `assets/studio/js/activity.js`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/activity.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/project-state.js`
- `assets/studio/js/studio-audits.js`
- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/js/docs-viewer.js`

It also feeds shared path resolution used by:

- `assets/studio/js/studio-data.js`

The active data-domain list and capability status come from `assets/studio/data/export_import_adapters.json`.
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
- shared Studio analysis policy values used by the analytics scoring runtime
- the lookup path for generated docs indexes used by Studio pages, such as the Library export selector
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
- `data-import.json`
- `data-export.json`
- `docs-broken-links.json`
- `docs-html-import.json`
- `docs-viewer.json`
- `library-documents.json`
- `project-state.json`
- `series-tag-editor.json`
- `series-tags.json`
- `site-series-index.json`
- `studio-audits.json`
- `studio-works.json`
- `tag-aliases.json`
- `tag-groups.json`
- `tag-registry.json`

Do not add domain workflows, service endpoint contracts, generated payload schemas, or scoring implementations to `studio_config.json`.
If a domain needs behavior, place that behavior in the owning runtime module and keep this file to paths, policy values, options, and scoped payload lookup.

## Data export page

The data export page reads:

- `paths.routes.data_export`
- `paths.data.studio.export_import_adapters`
- `paths.data.studio.library_export_configs`
- `paths.data.docs.scopes.library.index`
- `paths.data.ui_text.data_export`

The export config file owns export pattern definitions.
`studio_config.json` only owns browser-facing route, payload, and scoped UI-copy lookup for the Studio page.
The page runs exports through the fixed docs-management transport endpoint `POST /docs/export`, which is configured in `assets/studio/js/studio-transport.js` rather than in `studio_config.json`.
Adapter dispatch belongs in `assets/studio/data/export_import_adapters.json`.
Future-domain availability also belongs in that adapter registry; `studio_config.json` only provides fallback unavailable-state copy.
The scoped data-export payload keys `format_label`, `format_json`, `format_jsonl`, `format_required`, and `result_format_label` control output-format selector and result-modal copy.
The scoped data-export payload keys `filter_show_all`, `filter_no_content`, and `filter_not_viewable` control the list-filter pill labels.
The scoped data-export payload keys `result_title`, `result_close`, `result_files_label`, the `count_*` labels, `warnings_heading`, and `issues_heading` control the result modal copy shown after an export run.

Do not add export field mappings, output formats, or selection defaults to `studio_config.json`.
Those belong in `assets/studio/data/library_export_configs.json` so the CLI, service endpoint, and Studio UI all run the same pattern.

## Data import page

The data import page reads:

- `paths.routes.data_import`
- `paths.data.studio.export_import_adapters`
- `paths.data.ui_text.data_import`

The scoped data-import payload owns browser-facing labels, status messages, selection copy, preview/apply result modal titles and count labels, the preview `results` reopen button, summary-apply confirmation modal copy, and hierarchy-apply confirmation modal copy.
The fixed docs-management transport endpoints for staged-file listing, preview generation, and apply live in `assets/studio/js/studio-transport.js`.
Adapter dispatch belongs in `assets/studio/data/export_import_adapters.json`.
Future-domain availability also belongs in that adapter registry; `studio_config.json` only provides fallback unavailable-state copy.
Import parsing rules, export-pattern matching, output formats, and source-write validation do not belong in `studio_config.json`; they belong in the docs import/export scripts and docs-management service.

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

Related status-pill labels and save-state messages live in `assets/studio/data/ui_text/docs-viewer.json`, loaded through `paths.data.ui_text.docs_viewer`, including:

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
