---
draft: false
doc_id: d-20260607-222033-fc3fe4
title: Rebuild And Audit Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-11-18"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Rebuild And Audit Endpoints

These local endpoints operate on the configured Working workspace. [Management route owner](../../docs-viewer/services/docs_management_routes.py)

| Action | Request | Completed effect |
| --- | --- | --- |
| Exact document Rebuild | `POST /docs/rebuild-document` with `{doc_id}` or `{collection, doc_id}` | Read the saved source, generate the selected document and its Links effects, and prepare eligible publication changes. [External edits and rebuilds](../reference/Source_Organisation.md#explicit-external-edit-and-media-rebuilds) |
| Refresh Search and Recent | `POST /docs/refresh-discovery` with `{}` | Build and save Working Search and Recent and queue changed discovery files. [Working rebuild](Builder.md#working-rebuild) |
| Broken Links Refresh | `POST /docs/broken-links` with `{}` | Scan current Working inputs and save the private audit. `GET /docs/broken-links` reads that saved result. [Saved local report](Broken_Links_Script.md#saved-local-report) |

Full Working rebuild is an explicit maintenance CLI operation. Publish has its own queue-only endpoint. [Working rebuild](Builder.md#working-rebuild) · [Publish transfer boundary](Builder.md#preview-and-deployment-boundary)
