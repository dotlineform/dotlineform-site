---
doc_id: scripts-catalogue-write-server
title: Catalogue Write Services
added_date: 2026-04-22
last_updated: 2026-05-19
parent_id: servers
---
# Catalogue Write Services

Status:

- the standalone `studio/services/catalogue/catalogue_write_server.py` HTTP wrapper is retired
- Local Studio serves active catalogue APIs through `studio/app/server/studio/studio_app_server.py`
- catalogue write behavior lives in focused modules behind `studio/services/catalogue/catalogue_write_service.py`

The retired wrapper used to bind a separate local-only catalogue write process.
That separate process is no longer a supported fallback/debug path.
Use Local Studio app routes under `/studio/api/catalogue/...` for browser-facing catalogue writes.

## Current Behavior

The Local Studio catalogue service can:

- serve allowlisted catalogue source and lookup payloads for Studio
- create draft work, work-detail, and series records
- save existing work, work-detail, series, and moment records in canonical catalogue source JSON
- bulk-save existing work/work-detail records
- import new work/work-detail records from the configured bulk-import workbook
- import staged work, series, and moment prose Markdown into repo-local catalogue prose source files
- run scoped JSON-source rebuilds for work, series, and moment scopes
- apply shared publication preview/apply actions for works, work details, series, and moments
- write the local project-state report

## Module Boundary

- `studio/app/server/studio/studio_catalogue_api.py` owns the Local Studio `/studio/api/catalogue/...` adapter.
- `studio/services/catalogue/catalogue_write_service.py` owns service route dispatch.
- focused modules such as `catalogue_bulk_service.py`, `catalogue_work_service.py`, `catalogue_work_detail_service.py`, `catalogue_series_service.py`, `catalogue_build_service.py`, `catalogue_delete_service.py`, `catalogue_moment_service.py`, `catalogue_publication_service.py`, and `catalogue_prose_import_service.py` own workflow behavior.
- `studio/services/catalogue/catalogue_routes.py` remains the stable catalogue route constant inventory for activity profiles and request-contract documentation.

## Child References

- [Endpoint Reference](/docs/?scope=studio&doc=scripts-catalogue-write-server-endpoints) lists read, save, create, delete, publication, prose import, workbook import, series, and build endpoint request contracts.
- [Build And Lookup](/docs/?scope=studio&doc=scripts-catalogue-write-server-build-lookup) covers scoped build media, moment import behavior, derived lookup refresh, and field-aware build planning.
- [Operations](/docs/?scope=studio&doc=scripts-catalogue-write-server-operations) covers module ownership, validation, security, `bin/local-studio` integration, artifacts, and related references.
- [Catalogue Write Service Extraction](/docs/?scope=studio&doc=scripts-catalogue-write-service-extraction) records the handler-to-service extraction and wrapper retirement.
