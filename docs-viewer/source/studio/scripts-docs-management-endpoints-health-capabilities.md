---
doc_id: scripts-docs-management-endpoints-health-capabilities
title: Docs Viewer Health And Capabilities Endpoints
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: scripts-docs-management-endpoints
---
# Docs Viewer Health And Capabilities Endpoints

## `GET /health`

Query parameters: none.

Returned data:

```json
{
  "ok": true,
  "service": "docs_management",
  "dry_run": false
}
```

Used for:

- confirming that the standalone Docs Viewer service is reachable
- distinguishing a running management service from static generated-data fallback
- reporting dry-run mode when the service is launched with dry-run behavior

No source files, generated files, or logs are written.

## `GET /capabilities`

Query parameters: none.

Returned data:

```json
{
  "ok": true,
  "capabilities": {
    "docs_management": true,
    "generated_data_reads": true,
    "source_config_reads": true,
    "source_config_settings_reads": true,
    "source_config_settings_writes": true,
    "source_editor": true,
    "html_import": true,
    "docs_export": true,
    "library_import": true,
    "scope_lifecycle": {
      "manifest": true,
      "create_preview": true,
      "create_apply": true,
      "delete_preview": true,
      "delete_apply": true,
      "publishing_modes": ["public_readonly", "local_committed", "local_uncommitted"],
      "manifest_path": "docs-viewer/config/scopes/docs_scope_manifest.json"
    },
    "scopes": {
      "studio": {
        "available": true,
        "root": "docs-viewer/source/studio",
        "generated_data_reads": true,
        "generated_search_reads": true,
        "count": 0,
        "scope_lifecycle": {
          "manifest_recorded": true,
          "owner": "system",
          "created_by_tool": false,
          "delete_eligible": false
        }
      }
    }
  }
}
```

The `scopes` object is keyed by configured scope id. `count` is the number of loadable source docs found for that scope.

Used for:

- deciding whether manage mode should enable editing, import, source-config, and scope lifecycle controls
- showing per-scope generated-data availability
- disabling lifecycle deletion for system-owned or unmanifested scopes

No source files, generated files, or logs are written.
