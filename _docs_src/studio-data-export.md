---
doc_id: studio-data-export
title: Studio Data Export
added_date: 2026-05-06
last_updated: "2026-05-06 20:14"
parent_id: import-export
sort_order: 30
---
# Studio Data Export

Route:

- `/studio/export/`

This route is the shared Studio export shell for scoped data workflows.
It defaults to the Library data domain and can expose Catalogue and Analytics as named workflow scopes when those adapters are present in `assets/studio/data/export_import_adapters.json`.

The route owns:

- scope selection
- local docs-management service probing
- route-ready and busy-state attributes
- export command lifecycle
- result-modal rendering
- shared UI copy under `ui_text.data_export`

The Library documents adapter still owns the implemented export config set, source index, document tree selection, field mapping, and export output shape.
Those domain contracts remain documented in [Library Export v1](/docs/?scope=studio&doc=library-export) and [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs).

## Runtime

The page shell loads:

- `assets/studio/js/data-export.js`
- `assets/studio/data/export_import_adapters.json`
- `assets/studio/data/library_export_configs.json`
- generated docs-scope indexes such as `assets/data/docs/scopes/library/index.json`

Exports run through the docs-management endpoint `POST /docs/export`.
The browser sends `data_domain` so the local service can dispatch through the configured adapter boundary.

## Current Domains

- `library`: active documents adapter
- `catalogue`: named stub until catalogue export configs and source adapters exist
- `analytics`: named stub until analytics export configs and source adapters exist

## Verification

The retained smoke entry point is `tests/smoke/data_export.py`.
It checks route readiness, config loading, document-list rendering, list filters, output-format controls, and disabled command behavior when the local docs-management service is unavailable.
