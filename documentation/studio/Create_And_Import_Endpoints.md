---
draft: false
doc_id: d-20260607-222033-78a47c
title: Create And Import Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-20"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Create And Import Endpoints

These local Manage routes use the configured Working workspace. An ordinary target supplies no collection; a named target supplies its exact collection ID. [Document and collection identity](Source_Organisation.md#document-and-collection-identity)

| Route | Current purpose |
| --- | --- |
| `POST /docs/create` | Create one draft ordinary or collection document. The ordinary workflow persists its Index placement. Catalogue Work documents belong to Regenerate. |
| `GET /docs/import-source-directories` and `GET /docs/import-source-files` | List approved staged source folders and candidate files through confined Projects-backed import discovery. |
| `POST /docs/import-doc` | Import one native-selected supported document and open it on completion. |
| `POST /docs/import-source` | Preview or apply an ordinary staged source or validated complete trusted collection. A preview does not persist source. |

Read the [current dispatcher](../../docs-viewer/services/docs_management_service.py) and owning workflows for request shapes. [Source Mutation Scripts](Source_Mutation_Scripts.md) covers New and [Docs Import](Docs_Import.md) covers import selection, media and failure recovery. [Docs Review Endpoints](Docs_Review_Endpoints.md) covers the independent package inspection surface.

General document-transfer and scope-lifecycle endpoints were retired. The current Book copy and ordering operations have their own owners. [Book curation](Sub_Scope_Index_Architecture.md#book-curation-in-manage) · [Endpoint overview](Endpoint_Overview.md)
