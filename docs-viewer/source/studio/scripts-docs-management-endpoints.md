---
doc_id: scripts-docs-management-endpoints
title: Endpoint Overview
added_date: 2026-06-07
last_updated: 2026-06-10
parent_id: scripts-docs-management-server
---
# Docs Viewer Management Endpoint Overview

Docs Viewer management endpoints are local-only JSON APIs served by the standalone Docs Viewer service. Endpoint constants live in `docs-viewer/services/docs_management_routes.py`.

## GET Endpoints

| Endpoint | Child doc | Purpose |
| --- | --- | --- |
| `GET /health` | [Health And Capabilities](/docs/?scope=studio&doc=scripts-docs-management-endpoints-health-capabilities) | Probe service availability. |
| `GET /capabilities` | [Health And Capabilities](/docs/?scope=studio&doc=scripts-docs-management-endpoints-health-capabilities) | Report enabled management features and per-scope availability. |
| `GET /docs/index-tree` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Return generated scope tree JSON. |
| `GET /docs/generated/index-tree` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Explicit generated-data alias for scope tree JSON. |
| `GET /docs/recently-added` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Return generated recently-added JSON. |
| `GET /docs/generated/recently-added` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Explicit generated-data alias for recently-added JSON. |
| `GET /docs/doc` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Return one generated document payload. |
| `GET /docs/generated/payload` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Explicit generated-data alias for one document payload. |
| `GET /docs/search` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Return generated docs-search JSON. |
| `GET /docs/generated/search` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Explicit generated-data alias for docs-search JSON. |
| `GET /docs/references` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Return generated semantic-reference index JSON. |
| `GET /docs/generated/references` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Explicit generated-data alias for semantic-reference index JSON. |
| `GET /docs/reference-target` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Return generated semantic-reference target JSON. |
| `GET /docs/generated/reference-target` | [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | Explicit generated-data alias for semantic-reference target JSON. |
| `GET /docs/source-config` | [Source Config Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-config) | Return the Docs Viewer source-config report. |
| `GET /docs/source-config-settings` | [Source Config Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-config) | Return the settings edit contract. |
| `GET /docs/source` | [Source Editor Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-editor) | Return Markdown body text and a revision token for one source doc. |
| `GET /docs/import-source-files` | [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import) | List staged files that can be imported into docs source. |
| `GET /docs/import-html-files` | [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import) | Compatibility alias for staged import listing. |
| `GET /docs/publish/status` | [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes) | Report pending public-scope working-to-published changes. |

## POST Endpoints

| Endpoint | Child doc | Action |
| --- | --- | --- |
| `POST /docs/source-config-settings` | [Source Config Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-config) | Apply allowlisted source-config settings and rebuild docs output when needed. |
| `POST /docs/source/rebuild` | [Source Editor Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-editor) | Replace one source doc body, preserving front matter, then rebuild affected outputs. |
| `POST /docs/open-source` | [Source Editor Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-editor) | Open one source Markdown file in a local editor. |
| `POST /docs/create` | [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import) | Create a new source Markdown doc. |
| `POST /docs/import-source` | [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import) | Import a staged file into docs source. |
| `POST /docs/import-html` | [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import) | Compatibility alias for source import. |
| `POST /docs/rebuild` | [Rebuild And Audit Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-rebuild-audit) | Rebuild generated docs and docs-search for one scope. |
| `POST /docs/broken-links` | [Rebuild And Audit Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-rebuild-audit) | Run a missing-target audit for one docs scope. |
| `POST /docs/update-metadata` | [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) | Update supported front matter fields for one source doc. |
| `POST /docs/update-viewability` | [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) | Update `viewable` for one source doc. |
| `POST /docs/update-viewability-bulk` | [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) | Update `viewable` for multiple source docs. |
| `POST /docs/move` | [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) | Change one doc's parent without moving the source file. |
| `POST /docs/delete-preview` | [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) | Preview blockers and warnings before deleting one source doc. |
| `POST /docs/delete-apply` | [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) | Delete one source Markdown file after confirmation and validation. |
| `POST /docs/scopes/create-preview` | [Scope Lifecycle Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-scope-lifecycle) | Preview files and config changes for a new scope. |
| `POST /docs/scopes/create-apply` | [Scope Lifecycle Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-scope-lifecycle) | Create a new manifest-owned scope after confirmation. |
| `POST /docs/scopes/delete-preview` | [Scope Lifecycle Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-scope-lifecycle) | Preview deletion of a manifest-owned scope. |
| `POST /docs/scopes/delete-apply` | [Scope Lifecycle Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-scope-lifecycle) | Delete a manifest-owned scope after confirmation. |
| `POST /docs/publish/confirm` | [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes) | Confirm the working-to-published diff for one public scope without writing. |
| `POST /docs/publish/apply` | [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes) | Sync working docs/search to public snapshots after `confirm: true`. |

All JSON responses are sent with `Cache-Control: no-store`.
