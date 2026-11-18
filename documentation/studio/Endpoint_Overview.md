---
draft: false
doc_id: d-20260607-222033-647b52
title: Endpoint Overview
added_date: "2026-06-07 22:20:33"
last_updated: "2026-11-18"
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Endpoint Overview

Docs Viewer local endpoints are JSON APIs served by the Docs Viewer service. Canonical management endpoint constants live in `docs-viewer/services/docs_management_routes.py`; integrated document-package constants live in `docs-viewer/services/docs_document_package_routes.py`; independently gated Docs Review constants live in `docs-viewer/services/docs_review_routes.py`.

## GET Endpoints

| Endpoint | Child doc | Purpose |
| --- | --- | --- |
| `GET /health` | [Health And Capabilities](Health_And_Capabilities_Endpoints.md) | Probe service availability. |
| `GET /capabilities` | [Health And Capabilities](Health_And_Capabilities_Endpoints.md) | Report enabled management features and per-scope availability. |
| `GET /docs/index-tree` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return the generated Working Index tree. |
| `GET /docs/recent` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return the route-configured Recent JSON. |
| `GET /docs/doc` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return one generated document payload. |
| `GET /docs/media-files` | [Media And Asset Handling](Media_And_Asset_Handling.md) | List files for an exact Working media owner without document associations. |
| `GET /docs/media-references` | [Media And Asset Handling](Media_And_Asset_Handling.md) | Read source media references and exact document/collection-host identities for an exact Working media owner. |
| `GET /docs/search` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return generated docs-search JSON. |
| `GET /docs/source` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Return the complete Markdown buffer for one exact Working document. |
| `GET /docs/import-source-files` | [Docs Import](Docs_Import.md#choose-the-source-folder) | List document candidates in the accepted source folder. |

## Document Package GET Endpoints

These management-only endpoints support the selected Import-row Docs Review handoff. Prepare options uses the single POST below; the separate config/documents GET routes are retired without aliases.

| Endpoint | Purpose |
| --- | --- |
| `GET /docs/packages/returned` | List trusted reviewable packages for the configured workspace, plus blocked and unassigned evidence. |
| `GET /docs/packages/returned?collection=<collection>` | Resolve one explicitly return-Import-enabled collection and list complete trusted import-capable packages for that exact target. |

## Docs Review GET Endpoints

The complete independently gated contract lives in [Docs Review Endpoints](Docs_Review_Endpoints.md).

| Endpoint | Purpose |
| --- | --- |
| `GET /docs-review/capabilities` | Report review workspace availability and review-only authority. |
| `GET /docs-review/packages` | List validated packages and rejected-package diagnostics. |
| `GET /docs-review/packages/manifest` | Read one trusted validated manifest. |
| `GET /docs-review/packages/assets` | Read optional package inventories. |
| `GET /docs-review/packages/assets-content/<package>/<path>` | Serve one safe inventoried package asset. |
| `GET /docs-review/packages/index-tree` | Read one package-local generated tree. |
| `GET /docs-review/packages/payload` | Read one package-local generated document payload. |

## POST Endpoints

| Endpoint | Child doc | Action |
| --- | --- | --- |
| `POST /docs/source/save` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Save the complete Markdown buffer and selected media, then generate the exact Working result. |
| `POST /docs/source/media` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Resolve the selected media filename to a Working identity for the Source session. |
| `POST /docs/open-source` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Open one source Markdown file in a local editor. |
| `POST /docs/open-local-target` | [Local Folder Links](Management_Operations.md#local-folder-links) | Revalidate one canonical base-relative target, then open or reveal the existing contained file or folder. |
| `POST /docs/create` | [Create And Import Endpoints](Create_And_Import_Endpoints.md) | Create a new source Markdown doc. |
| `POST /docs/import-source` | [Create And Import Endpoints](Create_And_Import_Endpoints.md) | Preview or apply one ordinary staged source or one trusted complete collection. |
| `POST /docs/import-doc` | [Create And Import Endpoints](Create_And_Import_Endpoints.md) | Import one native-selected document through the exact Working owner. |
| `POST /docs/rebuild-document` | [Rebuild And Audit Endpoints](Rebuild_And_Audit_Endpoints.md) | Regenerate one exact saved Working document and its Links effects. |
| `POST /docs/refresh-discovery` | [Rebuild And Audit Endpoints](Rebuild_And_Audit_Endpoints.md) | Regenerate Working Search and Recent and queue changed discovery files. |
| `POST /docs/broken-links` | [Broken Links Script](Broken_Links_Script.md#saved-local-report) | Run and save the private Working missing-target audit. |
| `POST /docs/set-draft` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Persist one exact Working document's intended boolean and await generation from prepared source. |
| `POST /docs/set-selected` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Star/Unstar exact Working Selected membership; Unstar needs no source read. |
| `POST /docs/move` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Position an ordinary subtree and project navigation/parent metadata without source rendering. |
| `POST /docs/delete` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Delete a confirmed ordinary subtree or singular flat collection target and await exact generated/Links removal. |
| `POST /docs/publish` | [Publish transfer boundary](Builder.md#preview-and-deployment-boundary) | Apply completed Docs and Catalogue queue selections to Preview and configured destinations. |

Draft and the ordinary exclusion policy feed eligibility during Working generation. Publish consumes the completed selections. [Source Organisation](Source_Organisation.md#operations)

## Document Package POST Endpoints

| Endpoint | Action |
| --- | --- |
| `POST /docs/packages/prepare-options` | Require a configured collection; return profiles, workspace availability and metadata for only its checked IDs without rendering. |
| `POST /docs/packages/prepare` | Require a configured collection; produce one JSON/JSONL package from final explicit IDs/formats without reapplying UI filters. |
| `POST /docs/packages/returned/review` | Materialize the complete validated content package for read-only Docs Review. |

[Prepare Package](Package_Prepare.md)
documents its checked-document Action on `GET /docs/`.
`POST /docs/packages/returned/review` is invoked only by **Open in Docs
Review** for the exact selected, destination-matching Collection Import docs candidate. The retired
scope-level **Review package** action has no compatibility owner. There is no
separate package browser route or inspect endpoint. Requests reject generic
adapter fields and `record_indices`; the returned workflow has no
partial-record contract. Canonical returned-package mutation uses the normal
`POST /docs/import-source` whole-package plan and confirmation.

## Docs Review POST Endpoints

| Endpoint | Child doc | Action |
| --- | --- | --- |
| `POST /docs-review/packages/build` | [Docs Review Endpoints](Docs_Review_Endpoints.md) | Explicitly regenerate the complete retained projection for one validated package. |
| `POST /docs-review/packages/open-source` | [Docs Review Endpoints](Docs_Review_Endpoints.md) | Open one exact package-local source member in VS Code. |

All JSON responses are sent with `Cache-Control: no-store`.
