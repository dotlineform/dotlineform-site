---
draft: false
doc_id: d-20260602-234732-ea94b3
title: Configuration Map
added_date: "2026-06-02 23:47:32"
last_updated: "2026-10-10 22:37:48"
parent_id: d-20260419-000000-d2e47b

---
# Configuration Map

## Find The Owner

| Concern | Configuration owner | Contract |
| --- | --- | --- |
| Studio routes and browser-safe data paths | `studio/app/frontend/config/studio-config.json` | [Studio Config JSON](Studio_Config_JSON.md) |
| Catalogue field-to-artifact dependencies | `studio/data/config/catalogue/catalogue-field-registry.json` | [Studio Domain Config](Studio_Domain_Config.md) |
| Tag group order and coverage/RAG policy | `studio/data/config/tags/tag-management.json` | [Tag Source Data](Tag_Source_Data.md) |
| Catalogue media/source pipeline | `_data/pipeline.json` | [Catalogue Media Pipeline Config](Catalogue_Media_Pipeline_Config.md) |
| Docs Viewer scopes, routes, defaults, reports, and service schema | `docs-viewer/config/` plus the public route subset in `site/docs-viewer/config/` | [Docs Viewer Configuration](Configuration_And_Extension_Points.md) |
| Docs Viewer document-action restrictions | `docs-viewer/config/management/document-actions.json` | [Runtime: Document Action Policy](Docs_Viewer_Runtime.md#document-action-policy) |
| Integrated document-package profiles | `docs-viewer/config/document-packages/profiles.json` | [Documents Prepare Profiles](Package_Prepare_Profiles.md) |
| Public-site validation and shared settings | `site-tools/config/site-tools.json` | source file and consumers |
| Catalogue search build/runtime policy | `studio/services/catalogue/search/build_config.json` and `site/assets/data/search/policy.json` | focused search config docs |
| Projection-boundary audit | `tests/contracts/projection_contract.json` | [Projection Contract](Projection_Contract.md) |

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
