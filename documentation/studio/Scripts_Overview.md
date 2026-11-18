---
draft: false
doc_id: d-20260607-222033-2a494e
title: Scripts Overview
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-15"
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Management Script Overview

Use this map to trace a Manage change from its HTTP boundary to its workflow and generated effects. The [endpoint overview](Endpoint_Overview.md) owns route names. [Local Runners](Local_Runners.md) owns launch commands, environment settings and addresses.

## Runtime And Dispatch

- [Docs Viewer service](../../docs-viewer/services/docs_viewer_service.py) owns HTTP serving, local capabilities, origin checks and static routing.
- [Management route allowlist](../../docs-viewer/services/docs_management_routes.py) owns the accepted paths. [Management dispatcher](../../docs-viewer/services/docs_management_service.py) delegates POSTs to focused workflow owners. Review uses its own [package-rooted endpoints](Docs_Review_Endpoints.md).

## Read And Config Helpers

- [Workspace configuration](Configuration_And_Extension_Points.md#workspace-and-target-contracts) resolves Working and publication owners.
- [Read dispatcher](../../docs-viewer/services/docs_management_read_service.py) dispatches exact GET targets. [Generated Read Endpoints](Generated_Read_Endpoints.md) describes the saved reader artifacts. [Health And Capabilities](Health_And_Capabilities_Endpoints.md) explains service availability and action gating.

## Write Workflows

- [Management Operations](Management_Operations.md) covers local write authority, Draft, Position, deletion and follow-through. [Source Mutation Scripts](Source_Mutation_Scripts.md) maps the exact service modules.
- [Source Editor Scripts](Source_Editor_Scripts.md) traces the complete source session and Save. [Docs Import](Docs_Import.md) and [Create And Import Endpoints](Create_And_Import_Endpoints.md) cover the import variants and their boundaries.
- [Exact document Rebuild](../../docs-viewer/services/docs_document_rebuild.py) and [discovery refresh](../../docs-viewer/services/docs_discovery_refresh.py) own separate completion paths. [Builder](Builder.md#working-rebuild) covers the explicit full maintenance workflow.
- [Broken Links Script](Broken_Links_Script.md) owns saved audit refresh and its CLI. [Publish](../../docs-viewer/services/docs_publish.py) consumes selections completed by Working generation and Catalogue operations.

## Ownership Rule

HTTP dispatch normalizes the request and calls the workflow with its exact target. The workflow carries validation, persistence and required follow-through. Builders own the generated artifacts, and the browser owns selection, draft form state and display completion. Follow the code and focused references above for exact contracts.
