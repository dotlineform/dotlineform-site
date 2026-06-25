---
doc_id: scripts-docs-management-endpoints-source-config
title: Source Config Endpoints
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: scripts-docs-management-endpoints
---
# Docs Viewer Source Config Endpoints

## `GET /docs/source-config`

Query parameters: none.

Returned data: a read-only source-config report containing:

- configured docs scopes from `docs-viewer/config/scopes/docs_scopes.json`
- browser config projections
- generated output paths
- generated viewer options
- per-scope warnings
- repo-relative paths only

Used for:

- Docs Viewer manage-mode configuration reports
- comparing source config with generated output
- diagnosing stale or missing generated artifacts

This endpoint reads known config and generated files only. It does not write source config or generated output.

## `GET /docs/source-config-settings`

Query parameters:

```text
scope=<scope>  optional; when omitted, returns all configured scopes
```

Returned data:

```json
{
  "ok": true,
  "schema_version": "docs_source_config_settings_v1",
  "source_config_path": "docs-viewer/config/scopes/docs_scopes.json",
  "editable_scope_fields": [],
  "blocked_scope_fields": [],
  "deferred_global_fields": [],
  "scopes": []
}
```

Used for:

- rendering settings controls that are safe to expose in manage mode
- explaining why install-time fields such as roots, route bases, output paths, and media prefixes are blocked
- returning an empty editable-field list when no scope settings are currently exposed

## `POST /docs/source-config-settings`

No scope fields are currently editable through this endpoint. When a future field is allowlisted, expected data will use this shape:

```json
{
  "scope": "studio",
  "changes": {}
}
```

Actions:

- validates `scope` against configured docs scopes
- validates every submitted field against the settings allowlist
- writes only allowlisted values to `docs-viewer/config/scopes/docs_scopes.json`
- rebuilds generated docs output for the affected scope when a saved setting requires it
- logs a `docs_source_config_settings` event when a real write occurs

Returned data includes validation results, rejected fields, warnings, `changed`, `requires_rebuild`, changed field values, the source config path, rebuild diagnostics when a rebuild ran, and `dry_run`.

Rejected data:

- empty changes
- unsupported fields
- blocked install-time fields
- deferred global fields
- wrong JSON types
- missing or unsupported scopes
