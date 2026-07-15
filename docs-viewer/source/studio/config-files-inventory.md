---
doc_id: config-files-inventory
title: Configuration Map
added_date: 2026-06-02
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Configuration Map

## Find The Owner

| Concern | Configuration owner | Contract |
| --- | --- | --- |
| Studio routes and browser-safe data paths | `studio/app/frontend/config/studio-config.json` | [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json) |
| Catalogue field-to-artifact dependencies | `studio/data/config/catalogue/catalogue-field-registry.json` | [Studio Domain Config](/docs/?scope=studio&doc=config-studio-data-configs) |
| Activity grouping/display contract | `studio/data/config/runtime/activity-contract.json` | [Studio Domain Config](/docs/?scope=studio&doc=config-studio-data-configs) |
| Catalogue media/source pipeline | `_data/pipeline.json` | [Catalogue Media Pipeline Config](/docs/?scope=studio&doc=config-pipeline-json) |
| Admin routes and browser shell | `admin-app/app/frontend/config/admin-config.json` | [Admin Config JSON](/docs/?scope=studio&doc=config-admin-config-json) |
| Analytics routes and browser data | `analytics-app/app/frontend/config/analytics-config.json` | [Analytics Config JSON](/docs/?scope=studio&doc=config-analytics-config-json) |
| Docs Viewer scopes, routes, defaults, reports, and service schema | `docs-viewer/config/` plus the public route subset in `site/docs-viewer/config/` | [Docs Viewer Configuration](/docs/?scope=studio&doc=config-docs-viewer) |
| Data Sharing adapters and capabilities | `data-sharing/config/adapters.json` | [Data Sharing Adapter Registry](/docs/?scope=studio&doc=config-data-sharing-adapters) |
| Documents prepare profiles | `data-sharing/adapters/documents/config/prepare-profiles.json` | [Documents Prepare Profiles](/docs/?scope=studio&doc=data-sharing-documents-prepare-profiles) |
| Public-site validation and shared settings | `site-tools/config/site-tools.json` | source file and consumers |
| Catalogue search build/runtime policy | `studio/services/catalogue/search/build_config.json` and `site/assets/data/search/policy.json` | focused search config docs |
| Projection-boundary audit | `admin-app/checks/projection_contract.json` | [Projection Contract](/docs/?scope=studio&doc=data-models-projection-contract) |

## Classification

- **Source configuration** is checked policy edited by maintainers or users.
- **Schema configuration** validates another config contract.
- **Runtime projection** is assembled by a server from checked config plus environment and should not be edited as source.
- **Generated data** may be consumed at runtime but is not configuration.
- **Environment** owns machine-specific bindings, roots, and secrets; `.env.local` is not checked in.

## Change Method

1. Start from the concern, not from a similarly named JSON file.
2. Confirm its loader and active consumers.
3. Change the owning config and its focused validation/tests.
4. Update the focused contract page only when ownership, extension method, or a durable rule changes.
5. Do not add the same key to a second app config for convenience; project it at the server boundary when another app needs a safe subset.

This page is a map, not an exhaustive file registry. Exact file families belong in their focused contract docs or source tree, where they can be verified against code without making every feature change update a central list.
