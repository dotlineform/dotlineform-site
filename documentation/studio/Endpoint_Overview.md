---
draft: false
doc_id: d-20260607-222033-647b52
title: Endpoint Overview
added_date: "2026-06-07 22:20:33"
last_updated: "2026-09-26 16:53:52"
parent_id: d-20260424-000000-04d75e
---
# Docs Viewer Endpoint Overview

Docs Viewer local endpoints are JSON APIs served by the Docs Viewer service. Canonical management endpoint constants live in `docs-viewer/services/docs_management_routes.py`; integrated document-package constants live in `docs-viewer/services/docs_document_package_routes.py`; independently gated Docs Review constants live in `docs-viewer/services/docs_review_routes.py`.

## GET Endpoints

| Endpoint | Child doc | Purpose |
| --- | --- | --- |
| `GET /health` | [Health And Capabilities](Health_And_Capabilities_Endpoints.md) | Probe service availability. |
| `GET /capabilities` | [Health And Capabilities](Health_And_Capabilities_Endpoints.md) | Report enabled management features and per-scope availability. |
| `GET /docs/index-tree` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return generated scope tree JSON. |
| `GET /docs/recent` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return the route-configured Recent JSON. |
| `GET /docs/doc` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return one generated document payload. |
| `GET /docs/media-files` | [Media And Asset Handling](Media_And_Asset_Handling.md) | List files for an exact Working media owner without document associations. |
| `GET /docs/media-references` | [Media And Asset Handling](Media_And_Asset_Handling.md) | Read source media references and exact document/collection-host identities for an exact Working media owner. |
| `GET /docs/search` | [Generated Read Endpoints](Generated_Read_Endpoints.md) | Return generated docs-search JSON. |
| `GET /docs/source-config-settings` | [Source Config Endpoints](Source_Config_Endpoints.md) | Return the settings edit contract. |
| `GET /docs/source` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Return Markdown body text and a revision token for one source doc. |
| `GET /docs/staged-media-files` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | List staged image or opaque-file choices for source-editor insertion. |
| `GET /docs/import-source-files` | [Create And Import Endpoints](Create_And_Import_Endpoints.md) | Project the body-free global Import candidate inventory and retained compatibility file list. |
| `GET /docs/publish/status` | [Public Scopes](Public_Scopes.md) | Report pending public-scope local-to-public changes. |

## Document Package GET Endpoints

These management-only endpoints support **Prepare package** and the selected
Import-row Docs Review handoff:

| Endpoint | Purpose |
| --- | --- |
| `GET /docs/packages/config` | Return fixed package profiles, scopes, actions, and external-workspace availability. |
| `GET /docs/packages/documents?scope=<scope>` | Return selectable source documents for Prepare. |
| `GET /docs/packages/returned?scope=<scope>` | List trusted reviewable packages for the active scope and its configured children, plus blocked and unassigned evidence. |
| `GET /docs/packages/returned?scope=<scope>&sub_scope=<sub-scope>` | Validate one explicitly return-Import-enabled child collection and list only complete trusted import-capable packages for that exact target. |

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
| `POST /docs/source-config-settings` | [Source Config Endpoints](Source_Config_Endpoints.md) | Apply allowlisted source-config settings and rebuild docs output when needed. |
| `POST /docs/source/rebuild` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Replace one source doc body, preserving front matter, then rebuild affected outputs. |
| `POST /docs/staged-media-preview` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Preview logical media identity and new/unchanged/replace collision state without writing. |
| `POST /docs/staged-media-apply` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Publish verified staged media and return Markdown for insertion into the active buffer. |
| `POST /docs/open-source` | [Source Editor Endpoints](Source_Editor_Endpoints.md) | Open one source Markdown file in a local editor. |
| `POST /docs/open-local-target` | [Management Services](Management_Services.md) | Revalidate one canonical base-relative target, then open or reveal the existing contained file or folder. |
| `POST /docs/create` | [Create And Import Endpoints](Create_And_Import_Endpoints.md) | Create a new source Markdown doc. |
| `POST /docs/import-source` | [Create And Import Endpoints](Create_And_Import_Endpoints.md) | Preview or apply one ordinary staged source or one trusted complete collection. |
| `POST /docs/rebuild` | [Rebuild And Audit Endpoints](Rebuild_And_Audit_Endpoints.md) | Rebuild generated docs and docs-search for one scope. |
| `POST /docs/broken-links` | [Rebuild And Audit Endpoints](Rebuild_And_Audit_Endpoints.md) | Run a missing-target audit for one docs scope. |
| `POST /docs/update-metadata` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Update supported front matter fields for one source doc. |
| `POST /docs/set-publishable` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Set publication intent for an exact selection of ordinary Analysis Working documents through one atomic rebuild. |
| `POST /docs/set-draft` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Set one Analysis Working document's draft readiness, including sub-scope documents, with a source revision and awaited rebuild. |
| `POST /docs/move` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Change one doc's parent without moving the source file. |
| `POST /docs/delete-preview` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Preview the exact source set plus any current public-cleanup impact. |
| `POST /docs/delete-apply` | [Source Mutation Endpoints](Source_Mutation_Endpoints.md) | Delete the confirmed exact set, clean its public projection, and apply any matched private lineage follow-through. |
| `POST /docs/scopes/create-preview` | [Scope Lifecycle Endpoints](Scope_Lifecycle_Endpoints.md) | Preview files and config changes for a new scope. |
| `POST /docs/scopes/create-apply` | [Scope Lifecycle Endpoints](Scope_Lifecycle_Endpoints.md) | Create a new manifest-owned scope after confirmation. |
| `POST /docs/scopes/delete-preview` | [Scope Lifecycle Endpoints](Scope_Lifecycle_Endpoints.md) | Preview deletion of a manifest-owned scope. |
| `POST /docs/scopes/delete-apply` | [Scope Lifecycle Endpoints](Scope_Lifecycle_Endpoints.md) | Delete a manifest-owned scope after confirmation. |
| `POST /docs/publish/confirm` | [Public Scopes](Public_Scopes.md) | Confirm the local-to-site-asset diff for one public scope without writing. |
| `POST /docs/publish/apply` | [Public Scopes](Public_Scopes.md) | Copy local published docs/search to public route site assets after `confirm: true`, then set or clear exact private editorial-lineage public URLs. |

`POST /docs/update-metadata` rejects publication fields. `POST /docs/set-publishable` owns durable publication intent for ordinary Working scope documents; `POST /docs/set-draft` owns independent readiness for all Working documents. Neither operation publishes documents. Visual `ui_status` has no workflow role: it is free text for ordinary documents, including the text `draft`, and is omitted from metadata for named collection targets.

## Document Package POST Endpoints

| Endpoint | Action |
| --- | --- |
| `POST /docs/packages/prepare` | Validate or write one JSON/JSONL package for an explicit source-document set. |
| `POST /docs/packages/returned/review` | Materialize the complete validated content package for read-only Docs Review. |

[Prepare Package](Package_Prepare.md)
documents its checked-document Action on `GET /docs/`.
`POST /docs/packages/returned/review` is invoked only by **Open in Docs
Review** for the exact selected app-level Import candidate. The retired
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
