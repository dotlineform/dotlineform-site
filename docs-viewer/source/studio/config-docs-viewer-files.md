---
doc_id: config-docs-viewer-files
title: Docs Viewer Config Files
added_date: 2026-06-02
last_updated: 2026-06-03
parent_id: studio
viewable: true
---
# Docs Viewer Config Files

Config files:

- `docs-viewer/config/scopes/docs_scopes.json`
- `docs-viewer/config/scopes/docs_scope_manifest.json`
- `docs-viewer/config/routes/docs-viewer-routes.json`
- `docs-viewer/config/routes/docs-viewer-public-routes.json`
- `docs-viewer/config/defaults/docs-viewer-config.json`
- `docs-viewer/config/defaults/docs-viewer-public-config.json`
- `docs-viewer/config/defaults/docs-viewer-service.json`
- `docs-viewer/config/ui-text/ui-text.json`
- `docs-viewer/config/reports/reports.json`
- `docs-viewer/config/schema/docs-viewer-service.schema.json`

## Contract Role

Docs Viewer config is split by responsibility:

- scope config defines source roots, generated output paths, route defaults, media prefixes, search output paths, and scope UI policy
- route config defines how a browser route maps to a scope, access mode, generated payload URLs, config URLs, panel defaults, and hosted views
- default browser config gives the runtime a concrete scope list and display policy
- service config defines standalone local service defaults, endpoint paths, environment variable names, capability defaults, and local state directories
- UI text config owns visible Docs Viewer copy
- report config owns source report metadata; route config and the browser runtime consume the generated browser-visible report projection
- schema files validate infrastructure config shape

## What Reads Them

The docs/search builders read `docs-viewer/config/scopes/docs_scopes.json` to produce generated docs payloads, generated search payloads, and default browser config files.

The browser runtime reads route config through the route-config resolver.
Public routes use the public route registry and public browser default config.
The local management route uses the management route registry and local browser default config.

`docs-viewer/services/docs_viewer_service.py` reads service defaults and injects local service base URLs and capabilities for the management route.

Docs Viewer UI modules read `docs-viewer/config/ui-text/ui-text.json` for visible text.

## Edit Class

Scope, route, report, and UI text configs are maintainer-editable app config.
Service defaults and schemas are code infrastructure.
Generated default browser configs are source-controlled outputs from the Docs Viewer config/build pipeline; edit the source scope or route config first unless the change is explicitly about generated default output.

## Cleanup Review

The cleanup review should keep these boundaries strict:

- do not move Docs Viewer scope policy back into Local Studio config
- keep public and manage route registries distinct
- keep management-only capabilities absent from public route config
- keep source scope config separate from generated default browser config
- update builder tests when a source scope config change should regenerate defaults
- keep report source metadata in `docs-viewer/config/reports/reports.json`; `assets/data/docs/reports.json` is the browser-visible projection
- the 2026-06-03 cleanup review found no active owner docs that still describe Docs Viewer status, scope, or UI text config as living in Studio config; historical request docs remain historical context
