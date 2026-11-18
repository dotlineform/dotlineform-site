---
draft: false
doc_id: d-20260607-222033-5d82a6
title: Health And Capabilities Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-15"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Health And Capabilities Endpoints

These are local service endpoints. The public reader gets its read capabilities from public route and browser configuration. [Public execution path](Docs_Viewer_Runtime.md#public-execution-path)

## `GET /health`

The standalone service responds with `ok`, `service: "docs_viewer"`, `management_enabled`, `generated_reads_enabled` and `review_enabled`. Use it to distinguish a reachable process from an enabled capability. [Service owner](../../docs-viewer/services/docs_viewer_service.py) · [Local runners](Local_Runners.md)

## `GET /capabilities`

The service builds the capability response for the configured Working workspace and applies its process-level flags. When management is disabled, the response disables authoring, import and Publish. When generated reads are disabled, it disables document and Search reads through the service. Review has its own package boundary. Use the response to gate controls and leave exact target, path and request validation with the called service. [Endpoint overview](Endpoint_Overview.md) · [Docs Review endpoints](Docs_Review_Endpoints.md)
