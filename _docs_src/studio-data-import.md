---
doc_id: studio-data-import
title: "Studio Data Import"
added_date: 2026-05-06
last_updated: "2026-05-06 12:30"
parent_id: studio
sort_order: 48
---

# Studio Data Import

Route:

- `/studio/import/`

This route is the shared Studio import shell for scoped staged-data workflows.
It defaults to the Library data domain and can expose Catalogue and Analytics as named workflow scopes when those adapters are present in `assets/studio/data/export_import_adapters.json`.

The route owns:

- scope selection
- staged-file selection
- local docs-management service probing
- route-ready and busy-state attributes
- preview command lifecycle
- preview-list selection
- result-modal rendering and reopen behavior
- shared UI copy under `ui_text.data_import`

The Library documents adapter still owns the implemented staged-file parser, preview Markdown renderer, summary apply, hierarchy apply, backups, and source rebuild/search refresh behavior.
Those domain contracts remain documented in [Library Import v1](/docs/?scope=studio&doc=library-import) and [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2).

## Runtime

The page shell loads:

- `assets/studio/js/data-import.js`
- `assets/studio/data/export_import_adapters.json`

Import file discovery, preview generation, and apply actions run through the docs-management endpoints:

- `GET /docs/import/files`
- `POST /docs/import/preview`
- `POST /docs/import/apply`

The browser sends `data_domain` so the local service can dispatch through the configured adapter boundary.

## Current Domains

- `library`: active documents adapter
- `catalogue`: named stub until catalogue staging, preview, and apply contracts exist
- `analytics`: named stub until analytics staging, preview, and apply contracts exist

## Verification

The retained smoke entry point is `tests/smoke/data_import.py`.
It checks route readiness, unavailable-service behavior, future-adapter disabled states, mocked preview list rendering, result reopen behavior, and mocked summary/hierarchy apply confirmation flows.
